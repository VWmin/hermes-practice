from dataclasses import dataclass, field

class Session:
    _DIR = "sessions"

    def __init__(self, session_id: str = "", system_message: str = ""):
        self.session_id = session_id or self.new_session_id()
        self.state = _SessionState()
        self.state.conversation_history.append({"role": "system", "content": system_message})

    @property
    def conversation_history(self):
        return self.state.conversation_history

    def new_session_id(self) -> str:
        from datetime import datetime
        import uuid
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{stamp}_{uuid.uuid4().hex[:6]}"

    @classmethod
    def load_session(cls, session_id: str = "") -> "Session":
        if not session_id:
            # use latest

            return None
        else:
            # use specified
            return None

    def flush(self):
        with open(f"{self._DIR}/{self.session_id}.json", "w") as f:
            import json
            json.dump(self.state.__dict__, f, indent=4)



@dataclass
class _SessionState:

    # conversation related
    conversation_history: list[dict] = field(default_factory=list)

    # tools related
    invalid_tool_retries: int = 0
    tool_call_id_prefix: str = "tool_call_"
    tool_call_id_counter: int = 0
