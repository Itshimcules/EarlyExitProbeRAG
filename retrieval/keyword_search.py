import re
from dataclasses import dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class WikiPage:
    page_id: str
    title: str
    url: str
    body: str
    path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "page_id": self.page_id,
            "url": self.url,
            "body": self.body,
        }


@dataclass(frozen=True)
class SearchResult:
    title: str
    page_id: str
    url: str
    snippet: str
    score: float

    def to_dict(self) -> dict[str, str | float]:
        return {
            "title": self.title,
            "page_id": self.page_id,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
        }


class KeywordWikiSearch:
    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self.pages = self._load_pages(docs_path)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scored: list[SearchResult] = []
        for page in self.pages.values():
            title_tokens = self._tokenize(page.title)
            body_tokens = self._tokenize(page.body)
            score = 0.0

            for term in query_terms:
                score += title_tokens.count(term) * 5.0
                score += body_tokens.count(term) * 1.0

            if score > 0:
                scored.append(
                    SearchResult(
                        title=page.title,
                        page_id=page.page_id,
                        url=page.url,
                        snippet=self._snippet(page.body, query_terms),
                        score=score,
                    )
                )

        return sorted(scored, key=lambda result: (-result.score, result.title))[:top_k]

    def get_page(self, page_id: str) -> WikiPage | None:
        return self.pages.get(page_id)

    def page_ids(self) -> set[str]:
        return set(self.pages.keys())

    def related_page_ids(self, page: WikiPage) -> list[str]:
        related_ids = []
        for page_id in re.findall(r"wiki://([a-z0-9-]+)", page.body):
            if page_id in self.pages and page_id not in related_ids:
                related_ids.append(page_id)
        return related_ids

    def _load_pages(self, docs_path: Path) -> dict[str, WikiPage]:
        if not docs_path.exists():
            raise FileNotFoundError(f"Wiki docs path does not exist: {docs_path}")

        pages = {}
        for path in sorted(docs_path.glob("*.md")):
            body = path.read_text(encoding="utf-8")
            page_id = path.stem
            title = self._extract_title(body) or page_id.replace("-", " ").title()
            pages[page_id] = WikiPage(
                page_id=page_id,
                title=title,
                url=f"wiki://{page_id}",
                body=body,
                path=path,
            )

        return pages

    def _extract_title(self, body: str) -> str | None:
        for line in body.splitlines():
            if line.startswith("# "):
                return line.replace("# ", "", 1).strip()
        return None

    def _tokenize(self, text: str) -> list[str]:
        return TOKEN_RE.findall(text.lower())

    def _snippet(self, body: str, terms: list[str], max_chars: int = 220) -> str:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
        for paragraph in paragraphs:
            lowered = paragraph.lower()
            if any(term in lowered for term in terms):
                cleaned = re.sub(r"\s+", " ", paragraph.replace("#", "")).strip()
                return cleaned[:max_chars]

        cleaned = re.sub(r"\s+", " ", body.replace("#", "")).strip()
        return cleaned[:max_chars]
