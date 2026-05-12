from pathlib import Path

import pytest

from backends.base import ModelBackend
from backends.mock_backend import MockBackend
from harness.local_harness import LocalHarness
from retrieval.keyword_search import KeywordWikiSearch


DOCS_PATH = Path(__file__).resolve().parents[1] / "mcp_servers" / "fake_wiki_docs"


class BadDebugBackend(ModelBackend):
    name = "bad-debug"

    async def generate(self, prompt: str) -> str:
        if "Return ONLY the page_id" in prompt:
            return "wiki://totally-invented-page"
        return "Synthetic answer."


def test_keyword_search_ranks_gpu_doc():
    search = KeywordWikiSearch(DOCS_PATH)

    results = search.search("GPU tray reseat boot failure")

    assert results
    assert results[0].page_id == "gpu-tray-reseat"
    assert results[0].url == "wiki://gpu-tray-reseat"


@pytest.mark.anyio
async def test_debug_returns_validated_url():
    harness = LocalHarness(MockBackend(), KeywordWikiSearch(DOCS_PATH))

    response = await harness.handle("/debug GPU tray reseat boot failure")

    assert response.mode == "debug"
    assert response.url == "wiki://gpu-tray-reseat"


@pytest.mark.anyio
async def test_debug_falls_back_to_known_url_when_model_hallucinates():
    harness = LocalHarness(BadDebugBackend(), KeywordWikiSearch(DOCS_PATH))

    response = await harness.handle("/debug GPU tray reseat boot failure")

    assert response.mode == "debug"
    assert response.url == "wiki://gpu-tray-reseat"


@pytest.mark.anyio
async def test_ask_returns_answer_and_sources():
    harness = LocalHarness(MockBackend(), KeywordWikiSearch(DOCS_PATH))

    response = await harness.handle("/ask GPU tray reseat boot failure")

    assert response.mode == "ask"
    assert "GPU tray alignment" in response.answer
    assert "wiki://gpu-tray-reseat" in response.sources
    assert "wiki://psu-led-status" in response.sources
