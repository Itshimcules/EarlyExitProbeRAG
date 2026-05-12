from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    ASK = "ask"
    DEBUG = "debug"


@dataclass(frozen=True)
class ParsedCommand:
    command: CommandType
    query: str


def parse_command(user_input: str) -> ParsedCommand:
    cleaned = user_input.strip()

    if cleaned.startswith("/debug "):
        return ParsedCommand(
            command=CommandType.DEBUG,
            query=cleaned.replace("/debug ", "", 1).strip(),
        )

    if cleaned.startswith("/ask "):
        return ParsedCommand(
            command=CommandType.ASK,
            query=cleaned.replace("/ask ", "", 1).strip(),
        )

    return ParsedCommand(
        command=CommandType.ASK,
        query=cleaned,
    )

