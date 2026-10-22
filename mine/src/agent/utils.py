def exit_ok(msg: str = ""):
    if msg:
        print(msg)
    exit(0)

def exit_error(msg: str = ""):
    if msg:
        print(msg)
    exit(1)