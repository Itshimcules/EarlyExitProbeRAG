import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from retrieval.keyword_search import KeywordWikiSearch, SearchResult, TOKEN_RE


class HashingEmbeddingFunction:
    """Deterministic local embedding function for Chroma demos.

    It avoids network calls and model downloads while still exercising a real
    vector database adapter. Production deployments can replace this with a
    sentence-transformer or service-backed embedding function.
    """

    def __init__(self, dimensions: int = 384):
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        return [self.embed(document) for document in input]

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class ChromaWikiSearch:
    """Chroma-backed persistent vector database adapter for wiki pages."""

    def __init__(
        self,
        docs_path: Path,
        persist_path: Path,
        collection_name: str = "synthetic_technician_wiki",
        embedding_dimensions: int = 384,
        rebuild: bool = False,
    ):
        self.docs_path = docs_path
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.keyword_index = KeywordWikiSearch(docs_path)
        self.embedding_function = HashingEmbeddingFunction(embedding_dimensions)
        self.manifest_path = persist_path / f"{collection_name}.manifest.json"
        self._client = None
        self._collection = None
        self.load_or_build(rebuild=rebuild)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        collection = self._get_collection()
        response = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["distances", "metadatas", "documents"],
        )
        ids = response.get("ids", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results = []

        for index, page_id in enumerate(ids):
            page = self.keyword_index.get_page(page_id)
            if page is None:
                continue
            distance = float(distances[index]) if index < len(distances) else 0.0
            results.append(
                SearchResult(
                    title=page.title,
                    page_id=page.page_id,
                    url=page.url,
                    snippet=self.keyword_index._snippet(page.body, TOKEN_RE.findall(query.lower())),
                    score=1.0 / (1.0 + max(distance, 0.0)),
                )
            )

        return results

    def get_page(self, page_id: str):
        return self.keyword_index.get_page(page_id)

    def page_ids(self) -> set[str]:
        return self.keyword_index.page_ids()

    def related_page_ids(self, page) -> list[str]:
        return self.keyword_index.related_page_ids(page)

    def load_or_build(self, rebuild: bool = False) -> None:
        self.persist_path.mkdir(parents=True, exist_ok=True)
        manifest = self._read_manifest()
        if rebuild or manifest.get("docs_fingerprint") != self._docs_fingerprint():
            self._rebuild_collection()
            return

        collection = self._get_collection()
        if collection.count() != len(self.keyword_index.pages):
            self._rebuild_collection()

    def _rebuild_collection(self) -> None:
        chromadb = self._load_chromadb()
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass

        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        pages = list(self.keyword_index.pages.values())
        self._collection.add(
            ids=[page.page_id for page in pages],
            documents=[page.title + "\n" + page.body for page in pages],
            metadatas=[
                {"title": page.title, "url": page.url, "page_id": page.page_id}
                for page in pages
            ],
        )
        self._write_manifest({"docs_fingerprint": self._docs_fingerprint()})

    def _get_client(self):
        if self._client is None:
            chromadb = self._load_chromadb()
            self._client = chromadb.PersistentClient(path=str(self.persist_path))
        return self._client

    def _get_collection(self):
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _load_chromadb(self):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "ChromaWikiSearch requires the optional chromadb package. "
                "Install it with: pip install '.[vector-db]'"
            ) from exc
        return chromadb

    def _docs_fingerprint(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(self.docs_path.glob("*.md")):
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def _read_manifest(self) -> dict:
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

