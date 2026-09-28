
def add(a, b):
    """
    Adds two numbers.
    """
    return a + b


TOOL_FUNCTIONS = {
    "add": add,
}


def tools_schem():
    return [{
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
    }]
