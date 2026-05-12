from fastapi import FastAPI

from app.api.command import router as command_router


app = FastAPI(
    title="Probe-Aware Tool Harness",
    version="0.1.0",
    description=(
        "Backend-agnostic local AI harness for technician wiki workflows, "
        "validated debug routing, and benchmarkable RAG experiments."
    ),
)

app.include_router(command_router, prefix="/api", tags=["commands"])


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}

