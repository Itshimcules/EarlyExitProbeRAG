from pathlib import Path

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

