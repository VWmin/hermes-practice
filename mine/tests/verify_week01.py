"""Reproducible, offline checks for the week 1 agent loop.

Run from the repository root with: python mine/tests/verify_week01.py
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent.agent import Agent  # noqa: E402


class ScriptedClient:
    def __init__(self, responses: list[dict]):
        self.responses = iter(responses)
        self.requests: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> dict:
        self.requests.append(deepcopy(messages))
        try:
            return deepcopy(next(self.responses))
        except StopIteration as exc:
            raise AssertionError("Agent made an unexpected model call") from exc


def make_agent(responses: list[dict], max_iterations: int = 5) -> tuple[Agent, ScriptedClient]:
    client = ScriptedClient(responses)
    with patch("agent.agent.DeepseekClient", return_value=client):
        agent = Agent("You are a helpful assistant.")
    agent.MAX_ITERATIONS = max_iterations
    return agent, client


def tool_response(call_id: str, arguments: str, reasoning: str = "Use add") -> dict:
    return {
        "role": "assistant",
        "content": None,
        "reasoning_content": reasoning,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": "add", "arguments": arguments},
            }
        ],
    }


def final_response(content: str) -> dict:
    return {
        "role": "assistant",
        "content": content,
        "reasoning_content": "Answer from the result",
        "tool_calls": None,
    }


def trace(name: str, agent: Agent, client: ScriptedClient, stop_reason: str) -> dict:
    messages = agent.conversation_history
    return {
        "scenario": name,
        "model_calls": len(client.requests),
        "roles": [message["role"] for message in messages],
        "tool_calls": [
            {"name": call["function"]["name"], "id": call["id"]}
            for message in messages
            for call in message.get("tool_calls") or []
        ],
        "tool_results": [
            {"id": message["tool_call_id"], "content": message["content"]}
            for message in messages
            if message["role"] == "tool"
        ],
        "stop_reason": stop_reason,
    }


def verify_normal_completion() -> dict:
    agent, client = make_agent(
        [tool_response("call_ok", '{"a":7,"b":11}'), final_response("18")]
    )
    assert agent.run_conversation("Use add to calculate 7 + 11") == "18"
    assert len(client.requests) == 2
    assert [message["role"] for message in client.requests[1]] == [
        "system", "user", "assistant", "tool"
    ]
    assistant_call = client.requests[1][2]
    tool_result = client.requests[1][3]
    assert assistant_call["tool_calls"][0]["id"] == tool_result["tool_call_id"]
    assert assistant_call["reasoning_content"] == "Use add"
    assert tool_result["content"].startswith("Tool add returned:")
    assert float(tool_result["content"].split(":", 1)[1].strip()) == 18
    return trace("normal_completion", agent, client, "final_response")


def verify_budget_stop() -> dict:
    limit = 3
    responses = [
        tool_response(f"call_{number}", '{"a":1,"b":2}')
        for number in range(1, limit + 1)
    ]
    agent, client = make_agent(responses, max_iterations=limit)
    try:
        agent.run_conversation("Keep using add")
    except RuntimeError as exc:
        assert str(exc) == "Max iterations reached without a final response."
    else:
        raise AssertionError("Agent did not stop at the iteration limit")
    assert len(client.requests) == limit
    return trace("budget_stop", agent, client, "iteration_budget_exhausted")


def verify_tool_failure() -> dict:
    agent, client = make_agent(
        [tool_response("call_bad", '{"a":7,'), final_response("The tool arguments were invalid")]
    )
    assert agent.run_conversation("Try add with malformed arguments") == (
        "The tool arguments were invalid"
    )
    assert len(client.requests) == 2
    assistant_call = client.requests[1][2]
    tool_result = client.requests[1][3]
    assert assistant_call["tool_calls"][0]["id"] == tool_result["tool_call_id"]
    assert "invalid" in tool_result["content"].lower()
    assert "returned:" not in tool_result["content"]
    return trace("tool_failure", agent, client, "tool_error_then_final_response")


if __name__ == "__main__":
    for verification in (
        verify_normal_completion,
        verify_budget_stop,
        verify_tool_failure,
    ):
        print(json.dumps(verification(), ensure_ascii=False))
