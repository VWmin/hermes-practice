"""Run one bounded, paid DeepSeek read_docs check with a redacted trace."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path


MINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINE_DIR / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(MINE_DIR / "src" / ".env", override=True)

from agent.agent import Agent  # noqa: E402
from agent.model_tools import get_tool  # noqa: E402


FIXTURE_PATH = "week-02/live-fixture.md"


def main() -> int:
    try:
        agent = Agent(
            "You are a helpful assistant. This is a synthetic tool test. "
            "Call read_docs only for week-02/live-fixture.md. "
            "Do not request any other path or guess the file contents."
        )
    except Exception as exc:
        print(json.dumps({"scenario": "live_read_docs", "stop_reason": "setup_error", "error_type": type(exc).__name__}))
        return 1

    agent.MAX_ITERATIONS = 5
    read_entry = get_tool("read_docs")
    if read_entry is None:
        print(json.dumps({"scenario": "live_read_docs", "stop_reason": "read_docs_unavailable"}))
        return 1
    original_handler = read_entry.handler

    def fixture_only_read_docs(path: str):
        if path != FIXTURE_PATH:
            raise ValueError("Only the synthetic verification fixture is allowed")
        return original_handler(path)

    read_entry.handler = fixture_only_read_docs
    agent.tools = [
        schema for schema in agent.tools
        if schema.get("function", {}).get("name") == "read_docs"
    ]
    agent.client.tools = agent.tools
    agent.client.openai_client = agent.client.openai_client.with_options(
        timeout=30.0, max_retries=0
    )
    requests: list[list[dict]] = []
    original_chat = agent.client.chat

    def tracked_chat(*, messages):
        requests.append(deepcopy(messages))
        return original_chat(messages=messages)

    agent.client.chat = tracked_chat
    try:
        answer = agent.run_conversation(
            "请调用 read_docs 读取合成测试文件 week-02/live-fixture.md，"
            "只回答文件的第一个一级标题代码。"
        )
        stop_reason = "final_response"
        error_type = None
        http_status = None
    except Exception as exc:
        answer = None
        stop_reason = (
            "iteration_budget_exhausted"
            if isinstance(exc, RuntimeError)
            and str(exc) == "Max iterations reached without a final response."
            else "error"
        )
        error_type = type(exc).__name__
        http_status = getattr(exc, "status_code", None)

    messages = agent.conversation_history
    calls = [
        {"name": call["function"]["name"], "id": call["id"]}
        for message in messages
        for call in message.get("tool_calls") or []
    ]
    results = [message for message in messages if message["role"] == "tool"]
    result_ids = [message["tool_call_id"] for message in results]
    read_results = [
        message for message in results
        if message["tool_call_id"] in {
            call["id"] for call in calls if call["name"] == "read_docs"
        }
    ]
    success_prefix = "Tool read_docs returned: "
    trace = {
        "scenario": "live_read_docs",
        "model_calls": len(requests),
        "iteration_limit": agent.MAX_ITERATIONS,
        "roles": [message["role"] for message in messages],
        "tool_calls": calls,
        "result_ids": result_ids,
        "read_result_success": [
            message["content"].startswith(success_prefix) for message in read_results
        ],
        "read_result_chars": [
            len(message["content"][len(success_prefix):])
            if message["content"].startswith(success_prefix) else 0
            for message in read_results
        ],
        "assistant_reasoning_present": [
            bool(message.get("reasoning_content"))
            for message in messages if message["role"] == "assistant"
        ],
        "next_request_contains_tool_result": any(
            any(message["role"] == "tool" for message in request)
            for request in requests[1:]
        ),
        "answer_mentions_fixture": "w2fixture" in (answer or "").lower(),
        "stop_reason": stop_reason,
    }
    if error_type:
        trace.update(error_type=error_type, http_status=http_status)
    print(json.dumps(trace, ensure_ascii=False))

    read_ids = [call["id"] for call in calls if call["name"] == "read_docs"]
    valid = (
        stop_reason == "final_response"
        and 1 <= len(requests) <= agent.MAX_ITERATIONS
        and read_ids
        and all(call_id in result_ids for call_id in read_ids)
        and all(trace["read_result_success"])
        and all(length <= 1024 for length in trace["read_result_chars"])
        and trace["next_request_contains_tool_result"]
        and trace["answer_mentions_fixture"]
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
