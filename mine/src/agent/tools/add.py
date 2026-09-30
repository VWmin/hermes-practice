from agent.model_tools import register

SCHEMA = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Adds two numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "The first number."},
                "b": {"type": "number", "description": "The second number."}
            },
            "required": ["a", "b"]
        }
    }
}


def add(a, b):
    """
    Adds two numbers.
    """
    return a + b


register(name="add", tool_set="math", schema=SCHEMA, handler=add)
