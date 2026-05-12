from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.keyword_search import KeywordWikiSearch


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional dependency path
    FastMCP = None


DOCS_PATH = PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs"
SEARCH = KeywordWikiSearch(DOCS_PATH)


def search_wiki(query: str, top_k: int = 5) -> list[dict]:
    """Search synthetic wiki pages and return MCP-friendly result dicts."""
    return [result.to_dict() for result in SEARCH.search(query, top_k=top_k)]


def get_wiki_page(page_id: str) -> dict | None:
    """Return a validated synthetic wiki page by page_id."""
    page = SEARCH.get_page(page_id)
    return page.to_dict() if page else None


if FastMCP is not None:
    mcp = FastMCP("synthetic-technician-wiki")

    @mcp.tool()
    def mcp_search_wiki(query: str, top_k: int = 5) -> list[dict]:
        return search_wiki(query, top_k=top_k)

    @mcp.tool()
    def mcp_get_wiki_page(page_id: str) -> dict | None:
        return get_wiki_page(page_id)
else:
    mcp = None


if __name__ == "__main__":
    if mcp is None:
        raise SystemExit(
            "Install the optional 'mcp' package to run this as an MCP server: "
            "pip install 'mcp[cli]'"
        )
    mcp.run()

