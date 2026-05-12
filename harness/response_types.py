from typing import Literal

from pydantic import BaseModel


class AskResponse(BaseModel):
    mode: Literal["ask"]
    answer: str
    sources: list[str]
    latency_ms: int


class DebugResponse(BaseModel):
    mode: Literal["debug"]
    url: str
    latency_ms: int

