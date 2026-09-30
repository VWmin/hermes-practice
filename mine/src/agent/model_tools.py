from dataclasses import dataclass
from typing import Callable, Any
import json
from agent.state import State
import importlib, pkgutil
import agent.tools



@dataclass
class ToolEntry:
    name: str
    tool_set: str
    schema: dict
    handler: Callable


ALL_TOOLS: dict[str, ToolEntry] = {}


def register(name: str, tool_set: str, schema: dict, handler: Callable):
    # 后来者覆盖前者，并记录警告
    ALL_TOOLS[name] = ToolEntry(name=name, tool_set=tool_set, schema=schema, handler=handler)


def get_tool(name: str) -> ToolEntry:
    return ALL_TOOLS.get(name)


def run_tool(name: str, args: str) -> str:
    entry: ToolEntry = get_tool(name)
    if entry is None:
        return f"Tool {name} not found."

    tool_function = entry.handler

    if not args or not isinstance(args, str):
        args = "{}"

    try:
        args = json.loads(args)
    except json.JSONDecodeError:
        return f"Tool {name} got invalid json format arguments: {args}"

    if not args or not isinstance(args, dict):
        args = {}

    schema = entry.schema or {}
    properties = schema.get("function", {}).get("parameters", {}).get("properties", {})
    if properties:
        for key, value in args.items():
            prop_schema = properties.get(key)
            if not prop_schema:
                continue
            expected = prop_schema.get("type")
            def _number(a):
                try:
                    f = float(a)
                    i = int(a)
                    return i if str(i) == a else f
                except ValueError:
                    return a
            def _integer(a):
                try:
                    return int(a)
                except ValueError:
                    return a
            def _boolean(a):
                try:
                    return bool(a)
                except ValueError:
                    return a
            def _json(a):
                try:
                    return json.loads(a)
                except (ValueError, TypeError):
                    return a

            try:
                if expected == "number":
                    args[key] = _number(value)
                elif expected == "integer":
                    args[key] = _integer(value)
                elif expected == "boolean":
                    args[key] = _boolean(value)
                elif expected in {"array", "object"}:
                    args[key] = _json(value)
            except TypeError:
                return f"Tool {name} got invalid argument, {key} expected to be {expected}, got {type(value).__name__}"

    try:
        result: Any = tool_function(**args)
        return f"Tool {name} returned: {result}"
    except Exception as e:
        return f"Tool {name} raised an exception: {e}"


def get_tool_definitions() -> list[dict]:
    for minfo in pkgutil.iter_modules(agent.tools.__path__):
        importlib.import_module(f"agent.tools.{minfo.name}")


def tools_schema():
    get_tool_definitions()
    return [tool.schema for tool in ALL_TOOLS.values()]
