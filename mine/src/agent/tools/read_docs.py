import os
from pathlib import Path
from agent.model_tools import register

LS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ls",
        "description": "List files in a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the directory."}
            },
            "required": []
        }
    }
}

READ_DOCS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_docs",
        "description": "Read the content of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file."}
            },
            "required": ["path"]
        }
    }
}

__HOME = Path("/Users/wenxin/PycharmProjects/hermes-practice/mine/docs")

def _real_path(path: str) -> Path:
    given = Path(path)
    if given.is_absolute():
        raise ValueError("Path must be relative to the home directory.")
    real_path = (__HOME / given).resolve(strict=True)
    if not real_path.is_relative_to(__HOME):
        raise ValueError("Path must be within the home directory.")
    if not real_path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    return real_path


def ls(path: str = "."):
    real_path = _real_path(path)
    return os.listdir(real_path)[:1024]  # Limit to first 1024 entries for safety

def read_docs(path: str):
    real_path = _real_path(path)
    if real_path.is_dir():
        raise IsADirectoryError(f"Path {path} is a directory, not a file.")
    with open(real_path, "r", encoding="utf-8") as f:
        return f.read(1024)  # Limit to first 1024 characters for safety

register(name="ls", tool_set="file_ops", schema=LS_SCHEMA, handler=ls)
register(name="read_docs", tool_set="file_ops", schema=READ_DOCS_SCHEMA, handler=read_docs)
