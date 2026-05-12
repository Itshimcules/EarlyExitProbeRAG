from pathlib import Path
from types import SimpleNamespace

from retrieval.chroma_search import ChromaWikiSearch, HashingEmbeddingFunction
from retrieval.vector_search import PersistentVectorWikiSearch


DOCS_PATH = Path(__file__).resolve().parents[1] / "mcp_servers" / "fake_wiki_docs"


def test_persistent_vector_index_builds_and_reloads(tmp_path):
    index_path = tmp_path / "wiki-vector-index.json"
    search = PersistentVectorWikiSearch(DOCS_PATH, index_path)

    results = search.search("GPU tray reseat boot failure", top_k=2)

    assert index_path.exists()
    assert results
    assert results[0].page_id == "gpu-tray-reseat"

    reloaded = PersistentVectorWikiSearch(DOCS_PATH, index_path)
    reloaded_results = reloaded.search("GPU tray reseat boot failure", top_k=2)

    assert reloaded_results[0].page_id == "gpu-tray-reseat"


def test_hashing_embedding_function_is_deterministic_and_normalized():
    embedder = HashingEmbeddingFunction(dimensions=16)

    first = embedder.embed("GPU tray reseat")
    second = embedder.embed("GPU tray reseat")

    assert first == second
    assert len(first) == 16
    assert abs(sum(value * value for value in first) - 1.0) < 0.0001


def test_chroma_adapter_uses_collection_interface(monkeypatch, tmp_path):
    class FakeCollection:
        def __init__(self):
            self.ids = []
            self.documents = []

        def count(self):
            return len(self.ids)

        def add(self, ids, documents, metadatas):
            self.ids = ids
            self.documents = documents

        def query(self, query_texts, n_results, include):
            terms = set(query_texts[0].lower().split())
            scored = []
            for page_id, document in zip(self.ids, self.documents):
                score = sum(1 for term in terms if term in document.lower())
                scored.append((score, page_id))
            ranked = [page_id for _, page_id in sorted(scored, key=lambda item: item[0], reverse=True)[:n_results]]
            return {"ids": [ranked], "distances": [[0.1 for _ in ranked]]}

    class FakeClient:
        def __init__(self, path):
            self.collection = FakeCollection()

        def delete_collection(self, name):
            self.collection = FakeCollection()

        def get_or_create_collection(self, name, embedding_function, metadata):
            return self.collection

    monkeypatch.setitem(
        __import__("sys").modules,
        "chromadb",
        SimpleNamespace(PersistentClient=FakeClient),
    )
    search = ChromaWikiSearch(DOCS_PATH, tmp_path / "chroma")

    results = search.search("GPU tray reseat", top_k=1)

    assert results[0].page_id == "gpu-tray-reseat"
