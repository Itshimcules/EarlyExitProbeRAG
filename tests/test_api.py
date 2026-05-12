import httpx
import pytest

from app.api.command import get_harness
from app.main import app


@pytest.fixture(autouse=True)
def clear_harness_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_BACKEND", "mock")
    monkeypatch.setenv("RESULTS_PATH", str(tmp_path / "results.csv"))
    get_harness.cache_clear()
    yield
    get_harness.cache_clear()


@pytest.mark.anyio
async def test_command_endpoint_debug():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/command",
            json={"input": "/debug GPU tray reseat boot failure"},
        )

    assert response.status_code == 200
    assert response.json()["url"] == "wiki://gpu-tray-reseat"


@pytest.mark.anyio
async def test_command_endpoint_ask():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/command",
            json={"input": "/ask GPU tray reseat boot failure"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "ask"
    assert "wiki://gpu-tray-reseat" in payload["sources"]
