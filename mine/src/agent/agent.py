import json
from typing import Any, Callable

from agent.tools import TOOL_FUNCTIONS, tools_schem
from agent.client import Client, DeepseekClient


class Agent:
    """暂时接deepseek"""
    MAX_ITERATIONS = 5

    def __init__(self, system_message: str):
        self.conversation_history = [{"role": "system", "content": system_message}]
        self.tools = tools_schem()
        self.client: Client = DeepseekClient(tools=self.tools)

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

    def tool_calls(self, tool_calls: list):
        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            self.run_tool(tool_name, tool_args, tool_call_id)

    def run_tool(self, tool_name: str, tool_args: str, tool_call_id: str):
        tool_function: Callable = TOOL_FUNCTIONS.get(tool_name)
        if tool_function is None:
            self.append_message("tool", f"Tool {tool_name} not found.", {"tool_call_id": tool_call_id})
            return
        try:
            result: Any = tool_function(**json.loads(tool_args))
            self.append_message("tool", f"Tool {tool_name} returned: {result}", {"tool_call_id": tool_call_id})
        except Exception as e:
            self.append_message("tool", f"Tool {tool_name} raised an exception: {e}", {"tool_call_id": tool_call_id})
