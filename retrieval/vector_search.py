import math
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from retrieval.keyword_search import KeywordWikiSearch, SearchResult, TOKEN_RE


INDEX_VERSION = 1


class PersistentVectorWikiSearch:
    """Persistent no-dependency vector index for larger synthetic corpora.

    It stores normalized token-count vectors as JSON so benchmark runs can reuse
    the same index without reparsing every document on every process start.
    """

    def __init__(self, docs_path: Path, index_path: Path, auto_build: bool = True):
        self.docs_path = docs_path
        self.index_path = index_path
        self.keyword_index = KeywordWikiSearch(docs_path)
        self.page_vectors: dict[str, Counter[str]] = {}
        if auto_build:
            self.load_or_build()

    def load_or_build(self, force: bool = False) -> None:
        if not force and self.index_path.exists():
            loaded = self._load()
            if loaded:
                return
        self.build()

    def build(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.page_vectors = {
            page_id: self._vector(page.title + "\n" + page.body)
            for page_id, page in self.keyword_index.pages.items()
        }
        payload = {
            "version": INDEX_VERSION,
            "docs_fingerprint": self._docs_fingerprint(),
            "pages": {
                page_id: {
                    "title": self.keyword_index.pages[page_id].title,
                    "url": self.keyword_index.pages[page_id].url,
                    "vector": dict(vector),
                }
                for page_id, vector in self.page_vectors.items()
            },
        }
        tmp_path = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.index_path)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not self.page_vectors:
            self.load_or_build()

        query_vector = self._vector(query)
        if not query_vector:
            return []

        results = []
        for page_id, page_vector in self.page_vectors.items():
            score = self._cosine(query_vector, page_vector)
            if score <= 0:
                continue
            page = self.keyword_index.get_page(page_id)
            if page is None:
                continue
            results.append(
                SearchResult(
                    title=page.title,
                    page_id=page.page_id,
                    url=page.url,
                    snippet=self.keyword_index._snippet(page.body, list(query_vector.keys())),
                    score=score,
                )
            )

        return sorted(results, key=lambda result: (-result.score, result.title))[:top_k]

    def get_page(self, page_id: str):
        return self.keyword_index.get_page(page_id)

    def page_ids(self) -> set[str]:
        return self.keyword_index.page_ids()

    def related_page_ids(self, page) -> list[str]:
        return self.keyword_index.related_page_ids(page)

    def _vector(self, text: str) -> Counter[str]:
        return Counter(TOKEN_RE.findall(text.lower()))

    def _cosine(self, left: Counter[str], right: Counter[str]) -> float:
        numerator = sum(left[token] * right[token] for token in left.keys() & right.keys())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _load(self) -> bool:
        try:
            payload: dict[str, Any] = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False

        if payload.get("version") != INDEX_VERSION:
            return False
        if payload.get("docs_fingerprint") != self._docs_fingerprint():
            return False

        pages = payload.get("pages", {})
        self.page_vectors = {
            page_id: Counter({token: int(count) for token, count in data["vector"].items()})
            for page_id, data in pages.items()
            if page_id in self.keyword_index.pages and "vector" in data
        }
        return bool(self.page_vectors)

    def _docs_fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.docs_path.glob("*.md")):
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()


class LightweightVectorSearch(PersistentVectorWikiSearch):
    """Backward-compatible in-memory constructor for the original vector scaffold."""

    def __init__(self, docs_path: Path):
        super().__init__(docs_path, index_path=Path(":memory:"), auto_build=False)
        self.page_vectors = {
            page_id: self._vector(page.title + "\n" + page.body)
            for page_id, page in self.keyword_index.pages.items()
        }
