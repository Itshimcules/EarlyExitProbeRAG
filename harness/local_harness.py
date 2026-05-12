import os
import re
import time
from pathlib import Path

from backends.base import ModelBackend
from backends.mock_backend import MockBackend
from backends.ollama_backend import OllamaBackend
from harness.benchmarks import BenchmarkLogger, BenchmarkRecord
from harness.command_router import CommandType, parse_command
from harness.prompts import build_ask_prompt, build_debug_prompt
from harness.response_types import AskResponse, DebugResponse
from retrieval.keyword_search import KeywordWikiSearch, SearchResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WIKI_PATH = PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs"
DEFAULT_RESULTS_PATH = PROJECT_ROOT / "experiments" / "results.csv"


class LocalHarness:
    def __init__(
        self,
        backend: ModelBackend,
        search: KeywordWikiSearch,
        benchmark_logger: BenchmarkLogger | None = None,
        top_k: int = 3,
    ):
        self.backend = backend
        self.search = search
        self.benchmark_logger = benchmark_logger
        self.top_k = top_k

    async def handle(self, user_input: str) -> AskResponse | DebugResponse:
        parsed = parse_command(user_input)
        if not parsed.query:
            raise ValueError("Command query cannot be empty.")

        if parsed.command == CommandType.DEBUG:
            return await self._debug(parsed.query)

        return await self._ask(parsed.query)

    async def _ask(self, query: str) -> AskResponse:
        started = time.perf_counter()
        results = self.search.search(query, top_k=self.top_k)
        page_ids = self._ask_page_ids(results)
        pages = [self.search.get_page(page_id) for page_id in page_ids]
        prompt = build_ask_prompt(query, [page for page in pages if page is not None])
        answer = await self.backend.generate(prompt)
        latency_ms = self._elapsed_ms(started)
        sources = [f"wiki://{page_id}" for page_id in page_ids]

        self._log(
            BenchmarkRecord(
                run_type="command",
                mode="ask",
                backend=self.backend.name,
                model_name=getattr(self.backend, "model", ""),
                query=query,
                latency_ms=latency_ms,
                sources=sources,
            )
        )

        return AskResponse(
            mode="ask",
            answer=answer,
            sources=sources,
            latency_ms=latency_ms,
        )

    def _ask_page_ids(self, results: list[SearchResult]) -> list[str]:
        if not results:
            return []

        ordered_ids = [results[0].page_id]
        top_page = self.search.get_page(results[0].page_id)
        related_ids = self.search.related_page_ids(top_page) if top_page else []

        if related_ids:
            for page_id in related_ids:
                if page_id not in ordered_ids:
                    ordered_ids.append(page_id)
                if len(ordered_ids) >= self.top_k:
                    break
            return ordered_ids

        for result in results[1:]:
            if result.page_id not in ordered_ids:
                ordered_ids.append(result.page_id)
            if len(ordered_ids) >= self.top_k:
                break

        return ordered_ids

    async def _debug(self, query: str) -> DebugResponse:
        started = time.perf_counter()
        results = self.search.search(query, top_k=self.top_k)
        if not results:
            raise ValueError("No matching wiki pages found for debug routing.")

        prompt = build_debug_prompt(query, results)
        model_output = await self.backend.generate(prompt)
        selected_page_id, model_output_valid = self._validated_page_id(model_output, results)
        selected_page = self.search.get_page(selected_page_id)
        if selected_page is None:
            selected_page = self.search.get_page(results[0].page_id)

        latency_ms = self._elapsed_ms(started)
        self._log(
            BenchmarkRecord(
                run_type="command",
                mode="debug",
                backend=self.backend.name,
                model_name=getattr(self.backend, "model", ""),
                query=query,
                latency_ms=latency_ms,
                selected_url=selected_page.url,
                notes=(
                    "model_output_validated"
                    if model_output_valid
                    else "fallback_to_top_keyword_result"
                ),
            )
        )

        return DebugResponse(
            mode="debug",
            url=selected_page.url,
            latency_ms=latency_ms,
        )

    def _validated_page_id(
        self, model_output: str, candidates: list[SearchResult]
    ) -> tuple[str, bool]:
        candidate_ids = {candidate.page_id for candidate in candidates}
        valid_ids = self.search.page_ids()
        cleaned = model_output.strip().strip("`").replace("wiki://", "")
        cleaned = re.split(r"\s+", cleaned)[0] if cleaned else ""

        if cleaned in candidate_ids:
            return cleaned, True

        mentioned_known_ids = [
            page_id for page_id in valid_ids if re.search(rf"\b{re.escape(page_id)}\b", model_output)
        ]
        for page_id in mentioned_known_ids:
            if page_id in candidate_ids:
                return page_id, True

        return candidates[0].page_id, False

    def _log(self, record: BenchmarkRecord) -> None:
        if self.benchmark_logger is not None:
            self.benchmark_logger.log(record)

    def _elapsed_ms(self, started: float) -> int:
        return max(0, round((time.perf_counter() - started) * 1000))


def create_default_harness() -> LocalHarness:
    docs_path = Path(os.getenv("WIKI_DOCS_PATH", DEFAULT_WIKI_PATH))
    backend_name = os.getenv("MODEL_BACKEND", "mock").strip().lower()

    if backend_name == "ollama":
        backend: ModelBackend = OllamaBackend(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    elif backend_name == "mock":
        backend = MockBackend()
    else:
        raise ValueError(f"Unsupported MODEL_BACKEND '{backend_name}'. Use 'mock' or 'ollama'.")

    return LocalHarness(
        backend=backend,
        search=KeywordWikiSearch(docs_path),
        benchmark_logger=BenchmarkLogger(Path(os.getenv("RESULTS_PATH", DEFAULT_RESULTS_PATH))),
    )
