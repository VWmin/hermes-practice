"""Run one bounded, paid DeepSeek tool-call check and print a redacted trace."""

from __future__ import annotations

import json
import sys
from pathlib import Path


MINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINE_DIR / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(MINE_DIR / "src" / ".env", override=True)

from agent.agent import Agent  # noqa: E402


def main() -> int:
    try:
        agent = Agent(
            "You are a helpful assistant. When asked for arithmetic, "
            "use the add tool before answering."
        )
    except Exception as exc:
        print(json.dumps({"scenario": "live_add", "stop_reason": "setup_error", "error_type": type(exc).__name__}))
        return 1

    agent.MAX_ITERATIONS = 5
    agent.client.openai_client = agent.client.openai_client.with_options(
        timeout=30.0, max_retries=0
    )
    model_calls = 0
    original_chat = agent.client.chat

    def counted_chat(*args, **kwargs):
        nonlocal model_calls
        model_calls += 1
        return original_chat(*args, **kwargs)

    agent.client.chat = counted_chat
    try:
        answer = agent.run_conversation("请调用 add 工具计算 7 加 11，然后给出结果。")
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
    results = [
        {"id": message["tool_call_id"], "content": message["content"]}
        for message in messages
        if message["role"] == "tool"
    ]
    trace = {
        "scenario": "live_add",
        "model_calls": model_calls,
        "iteration_limit": agent.MAX_ITERATIONS,
        "roles": [message["role"] for message in messages],
        "tool_calls": calls,
        "tool_results": results,
        "assistant_reasoning_present": [
            bool(message.get("reasoning_content"))
            for message in messages
            if message["role"] == "assistant"
        ],
        "answer": answer,
        "stop_reason": stop_reason,
    }
    if error_type:
        trace.update(error_type=error_type, http_status=http_status)
    print(json.dumps(trace, ensure_ascii=False))

    ids = [call["id"] for call in calls]
    result_ids = [result["id"] for result in results]
    return 0 if stop_reason == "final_response" and ids and ids == result_ids and "18" in (answer or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
