import math
from collections import Counter
from pathlib import Path

from retrieval.keyword_search import KeywordWikiSearch, SearchResult, TOKEN_RE


class LightweightVectorSearch:
    """Optional no-dependency vector-like search for roadmap experiments.

    This is intentionally simple: it uses normalized token-count vectors and
    cosine similarity over synthetic markdown docs. It gives the project a
    working semantic-search seam without introducing an external vector DB.
    """

    def __init__(self, docs_path: Path):
        self.keyword_index = KeywordWikiSearch(docs_path)
        self.page_vectors = {
            page_id: self._vector(page.title + "\n" + page.body)
            for page_id, page in self.keyword_index.pages.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
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

    def _vector(self, text: str) -> Counter[str]:
        return Counter(TOKEN_RE.findall(text.lower()))

    def _cosine(self, left: Counter[str], right: Counter[str]) -> float:
        numerator = sum(left[token] * right[token] for token in left.keys() & right.keys())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

