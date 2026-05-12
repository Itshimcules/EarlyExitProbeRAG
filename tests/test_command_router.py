from harness.command_router import CommandType, parse_command


def test_parse_debug_command():
    parsed = parse_command("/debug server will not boot")

    assert parsed.command == CommandType.DEBUG
    assert parsed.query == "server will not boot"


def test_parse_ask_command():
    parsed = parse_command("/ask GPU tray reseat boot failure")

    assert parsed.command == CommandType.ASK
    assert parsed.query == "GPU tray reseat boot failure"


def test_default_command_is_ask():
    parsed = parse_command("GPU tray reseat boot failure")

    assert parsed.command == CommandType.ASK
    assert parsed.query == "GPU tray reseat boot failure"

