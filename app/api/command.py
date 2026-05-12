from functools import lru_cache
from typing import Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from harness.local_harness import create_default_harness
from harness.response_types import AskResponse, DebugResponse


router = APIRouter()
CommandResponse = Union[AskResponse, DebugResponse]


class CommandRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=1,
        examples=["/ask server will not boot after GPU tray reseat"],
    )


@lru_cache(maxsize=1)
def get_harness():
    return create_default_harness()


@router.post("/command", response_model=CommandResponse)
async def run_command(request: CommandRequest) -> CommandResponse:
    try:
        return await get_harness().handle(request.input)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

