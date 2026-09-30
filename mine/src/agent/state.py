from dataclasses import dataclass

@dataclass
class State:

    # tools related
    invalid_tool_retries: int = 0
    tool_call_id_prefix: str = "tool_call_"
    tool_call_id_counter: int = 0