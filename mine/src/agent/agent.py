from agent.model_tools import tools_schema, run_tool
from agent.client import Client, DeepseekClient
from agent.state import State
from typing import Any


class Agent:
    """暂时接deepseek"""
    MAX_ITERATIONS = 5

    def __init__(self, system_message: str):
        self.conversation_history = [{"role": "system", "content": system_message}]
        self.tools = tools_schema()
        self.client: Client = DeepseekClient(tools=self.tools)
        self.state = State()

    def append_message(self, role: str, content: str, extra=None):
        extra = extra or {}
        self.conversation_history.append({"role": role, "content": content, **extra})

    def api_call(self):
        response = self.client.chat(messages=self.conversation_history)
        return response

    def run_conversation(self, user_message: str) -> str:
        self.append_message("user", user_message)
        cur_iteration = 0
        while cur_iteration < self.MAX_ITERATIONS:
            response = self.api_call()
            tool_calls = response.get("tool_calls", [])
            # append assistant message
            self.conversation_history.append(response)

            if tool_calls:
                self.tool_calls(tool_calls)
            else:
                break

            cur_iteration += 1
        else:
            raise RuntimeError("Max iterations reached without a final response.")

        return self.last_message()

    def last_message(self) -> str:
        return self.conversation_history[-1]["content"] if self.conversation_history else ""

    def tool_calls(self, tool_calls: list[dict[str, Any]]):
        # ensure tool_call id
        repeat_id = set()
        for tool_call in tool_calls:
            if "id" not in tool_call or not tool_call["id"] or tool_call["id"] in repeat_id:
                while True:
                    next_id = f"{self.state.tool_call_id_prefix}{self.state.tool_call_id_counter}"
                    self.state.tool_call_id_counter += 1
                    if next_id not in repeat_id:
                        tool_call["id"] = next_id
                        break
            repeat_id.add(tool_call["id"])

        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            tool_name = tool_call["function"]["name"]
            tool_args: str = tool_call["function"]["arguments"]
            tool_message = run_tool(tool_name, tool_args)
            self.append_message("tool", tool_message, {"tool_call_id": tool_call_id})
