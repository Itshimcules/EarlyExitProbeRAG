import json
import importlib.util
from pathlib import Path

import httpx
import pytest

from backends.hf_probe_backend import HuggingFaceProbeAwareBackend
from backends.gemma4_turboquant_backend import Gemma4TurboQuantBackend
from backends.llama_cpp_backend import LlamaCppBackend
from backends.openai_compatible_backend import OpenAICompatibleBackend
from harness.local_harness import create_default_harness
from retrieval.vector_search import PersistentVectorWikiSearch


@pytest.mark.anyio
async def test_openai_compatible_backend_calls_chat_completions():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-token"
        payload = json.loads(request.content)
        assert payload["model"] == "local-test-model"
        assert payload["messages"][0]["content"] == "hello"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": " routed answer "}}]},
        )

    backend = OpenAICompatibleBackend(
        model="local-test-model",
        base_url="http://gateway.test/v1",
        api_key="test-token",
        transport=httpx.MockTransport(handler),
    )

    assert await backend.generate("hello") == "routed answer"


def test_llama_cpp_backend_reports_missing_model_file(tmp_path):
    backend = LlamaCppBackend(tmp_path / "missing.gguf")

    with pytest.raises(FileNotFoundError):
        backend._load_model()


def test_hf_probe_math_without_loading_transformers():
    backend = HuggingFaceProbeAwareBackend(probe_layer=-1)

    assert backend._normalize_layer_index(-1, 4) == 3
    confidence = backend._score_linear_probe([1.0, 1.0], {"weights": [2.0, 2.0], "bias": 0})
    assert confidence > 0.98


def test_gemma4_turboquant_backend_reports_missing_turboquant():
    if importlib.util.find_spec("turboquant") is not None:
        pytest.skip("turboquant is installed in this environment")
    backend = Gemma4TurboQuantBackend(use_turboquant=True)

    with pytest.raises(RuntimeError, match="turboquant"):
        backend._create_turboquant_cache()


def test_factory_wires_vector_retrieval_and_openai_backend(monkeypatch, tmp_path):
    docs_path = Path(__file__).resolve().parents[1] / "mcp_servers" / "fake_wiki_docs"
    monkeypatch.setenv("MODEL_BACKEND", "openai_compatible")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "local-test-model")
    monkeypatch.setenv("RETRIEVAL_MODE", "vector")
    monkeypatch.setenv("WIKI_DOCS_PATH", str(docs_path))
    monkeypatch.setenv("VECTOR_INDEX_PATH", str(tmp_path / "vector-index.json"))
    monkeypatch.setenv("RESULTS_PATH", str(tmp_path / "results.csv"))

    harness = create_default_harness()

    assert isinstance(harness.search, PersistentVectorWikiSearch)
    assert harness.backend.name == "openai_compatible"
    assert harness.backend.model == "local-test-model"
