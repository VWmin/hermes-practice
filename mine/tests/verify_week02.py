"""Offline, reproducible verification of week 2 tool behavior.

Run from the repository root: python3 mine/tests/verify_week02.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


MINE_DIR = Path(__file__).resolve().parents[1]
DOCS_ROOT = MINE_DIR / "docs"
sys.path.insert(0, str(MINE_DIR / "src"))

from agent.agent import Agent  # noqa: E402
from agent.model_tools import get_tool  # noqa: E402


class ScriptedClient:
    def __init__(self, responses: list[dict]):
        self.responses = iter(responses)
        self.requests: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> dict:
        self.requests.append(deepcopy(messages))
        try:
            return deepcopy(next(self.responses))
        except StopIteration as exc:
            raise AssertionError("Unexpected model call") from exc


def make_agent(responses: list[dict]) -> tuple[Agent, ScriptedClient]:
    client = ScriptedClient(responses)
    with patch("agent.agent.DeepseekClient", return_value=client):
        agent = Agent("You are a helpful assistant.")
    return agent, client


def call(name: str, call_id: str, arguments: str) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }


def tool_reply(calls: list[dict]) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "reasoning_content": "Use the requested tools",
        "tool_calls": calls,
    }


def final_reply(content: str) -> dict:
    return {
        "role": "assistant",
        "content": content,
        "reasoning_content": "Answer from tool results",
        "tool_calls": None,
    }


@contextmanager
def count_handlers(*names: str):
    originals = {}
    calls = Counter()
    successes = Counter()
    for name in names:
        entry = get_tool(name)
        assert entry is not None, f"Tool {name} was not registered"
        original = entry.handler
        originals[name] = original

        def counted_handler(*args, _name=name, _original=original, **kwargs):
            calls[_name] += 1
            result = _original(*args, **kwargs)
            successes[_name] += 1
            return result

        entry.handler = counted_handler
    try:
        yield calls, successes
    finally:
        for name, original in originals.items():
            get_tool(name).handler = original


def trace(scenario: str, agent: Agent, client: ScriptedClient, calls: Counter, successes: Counter) -> dict:
    messages = agent.conversation_history
    tool_calls = [
        {"name": item["function"]["name"], "id": item["id"]}
        for message in messages
        for item in message.get("tool_calls") or []
    ]
    results = [message for message in messages if message["role"] == "tool"]
    return {
        "scenario": scenario,
        "model_calls": len(client.requests),
        "roles": [message["role"] for message in messages],
        "tool_calls": tool_calls,
        "result_ids": [message["tool_call_id"] for message in results],
        "result_kinds": [
            "success" if " returned:" in message["content"] else "error"
            for message in results
        ],
        "handler_calls": dict(calls),
        "successful_handlers": dict(successes),
        "stop_reason": "final_response",
    }


def verify_normal_batch() -> dict:
    batch = [
        call("add", "normal_add", '{"a":7,"b":11}'),
        call("read_docs", "normal_read", '{"path":"week-01/agent-loop.md"}'),
    ]
    agent, client = make_agent([tool_reply(batch), final_reply("Done")])
    with count_handlers("add", "read_docs") as (calls, successes):
        assert agent.run_conversation("Add numbers and read a note") == "Done"
    assert len(client.requests) == 2
    request = client.requests[1]
    assert [message["role"] for message in request] == ["system", "user", "assistant", "tool", "tool"]
    results = [message for message in request if message["role"] == "tool"]
    assert [message["tool_call_id"] for message in results] == ["normal_add", "normal_read"]
    assert results[0]["content"].startswith("Tool add returned:")
    assert float(results[0]["content"].split(":", 1)[1].strip()) == 18
    prefix = "Tool read_docs returned: "
    assert results[1]["content"].startswith(prefix)
    assert len(results[1]["content"][len(prefix):]) <= 1024
    assert calls == {"add": 1, "read_docs": 1}
    assert successes == calls
    return trace("normal_batch", agent, client, calls, successes)


def verify_mixed_errors() -> dict:
    batch = [
        call("missing", "unknown", "{}"),
        call("add", "bad_json", '{"a":7,'),
        call("add", "valid_add", '{"a":7,"b":11}'),
    ]
    agent, client = make_agent([tool_reply(batch), final_reply("Only the valid add ran")])
    with count_handlers("add") as (calls, successes):
        assert agent.run_conversation("Try three calls") == "Only the valid add ran"
    assert len(client.requests) == 2
    results = [message for message in client.requests[1] if message["role"] == "tool"]
    assert [message["tool_call_id"] for message in results] == ["unknown", "bad_json", "valid_add"]
    assert "not found" in results[0]["content"]
    assert "invalid" in results[1]["content"].lower()
    assert results[2]["content"].startswith("Tool add returned:")
    assert float(results[2]["content"].split(":", 1)[1].strip()) == 18
    assert calls == {"add": 1}
    assert successes == calls
    return trace("mixed_errors", agent, client, calls, successes)


def verify_directory_boundary() -> dict:
    outside = (MINE_DIR / "plan" / "WEEK_02.md").resolve()
    with tempfile.TemporaryDirectory(prefix=".week02_verify_", dir=DOCS_ROOT) as temp_dir:
        link = Path(temp_dir) / "outside.md"
        link.symlink_to(outside)
        link_path = str(link.relative_to(DOCS_ROOT))
        batch = [
            call("read_docs", "relative_escape", '{"path":"../plan/WEEK_02.md"}'),
            call("read_docs", "absolute_escape", json.dumps({"path": str(outside)})),
            call("read_docs", "symlink_escape", json.dumps({"path": link_path})),
        ]
        agent, client = make_agent([tool_reply(batch), final_reply("All three reads were rejected")])
        with count_handlers("read_docs") as (calls, successes):
            assert agent.run_conversation("Try paths outside the notes directory") == (
                "All three reads were rejected"
            )
        assert len(client.requests) == 2
        results = [message for message in client.requests[1] if message["role"] == "tool"]
        assert [message["tool_call_id"] for message in results] == [
            "relative_escape", "absolute_escape", "symlink_escape"
        ]
        assert all("raised an exception" in message["content"] for message in results)
        assert all(" returned:" not in message["content"] for message in results)
        assert calls == {"read_docs": 3}
        assert successes == {}
        return trace("directory_boundary", agent, client, calls, successes)


if __name__ == "__main__":
    for verification in (verify_normal_batch, verify_mixed_errors, verify_directory_boundary):
        print(json.dumps(verification(), ensure_ascii=False))
