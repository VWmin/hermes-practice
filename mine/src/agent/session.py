from dataclasses import dataclass, field
import re
import os
import json
from pathlib import Path
from agent.utils import exit_error

class Session:
    _DIR = "sessions"

    def __init__(self, session_id: str = "", system_message: str = ""):
        os.makedirs(self._DIR, exist_ok=True)
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
        pattern = re.compile(r"^\d{8}_\d{6}_[0-9a-f]{6}\.json$")
        files = [p for p in Path(cls._DIR).iterdir() if p.is_file() and pattern.match(p.name)]

        # no session exists
        if not files:
            exit_error(f"No session files found in {cls._DIR}.")

        # use latest
        if not session_id:
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            return cls.load_session_from_file(latest_file)

        found = next((f for f in files if f.stem == session_id), None)
        if not found:
            exit_error(f"Session file {session_id}.json not found in {cls._DIR}.")

        return cls.load_session_from_file(found)


    @classmethod
    def load_session_from_file(cls, file_path: Path) -> "Session":
        with open(file_path, "r") as f:
            data = json.load(f)
        session = cls(session_id=file_path.stem)
        session.state = _SessionState(**data)
        return session


    def flush(self):
        with open(f"{self._DIR}/{self.session_id}.json", "w") as f:
            json.dump(self.state.__dict__, f, indent=4)


@dataclass
class _SessionState:

    # conversation related
    conversation_history: list[dict] = field(default_factory=list)

    # tools related
    invalid_tool_retries: int = 0
    tool_call_id_prefix: str = "tool_call_"
    tool_call_id_counter: int = 0
