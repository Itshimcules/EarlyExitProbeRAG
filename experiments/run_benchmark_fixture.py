import argparse
import asyncio
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backends.mock_backend import MockBackend
from harness.benchmarks import BenchmarkLogger, BenchmarkRecord
from harness.local_harness import DEFAULT_RESULTS_PATH, DEFAULT_VECTOR_INDEX_PATH, LocalHarness
from retrieval.chroma_search import ChromaWikiSearch
from retrieval.keyword_search import KeywordWikiSearch
from retrieval.vector_search import PersistentVectorWikiSearch


DEFAULT_FIXTURE_PATH = PROJECT_ROOT / "experiments" / "fixtures" / "wiki_command_trials.jsonl"
DEFAULT_DOCS_PATH = PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs"


def load_trials(path: Path) -> list[dict]:
    trials = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        trial = json.loads(line)
        if "input" not in trial:
            raise ValueError(f"Fixture line {line_number} is missing 'input'.")
        trials.append(trial)
    return trials


def build_search(
    retrieval_mode: str,
    docs_path: Path,
    vector_index_path: Path,
    chroma_path: Path,
):
    if retrieval_mode == "keyword":
        return KeywordWikiSearch(docs_path)
    if retrieval_mode == "vector":
        return PersistentVectorWikiSearch(docs_path, vector_index_path)
    if retrieval_mode == "chroma":
        return ChromaWikiSearch(docs_path, chroma_path)
    raise ValueError("retrieval_mode must be 'keyword', 'vector', or 'chroma'.")


def check_trial(trial: dict, response) -> bool:
    if response.mode == "debug":
        return response.url == trial.get("expected_url")

    expected_sources = set(trial.get("expected_sources", []))
    if not expected_sources:
        return True
    return expected_sources.issubset(set(response.sources))


async def run_fixture(args) -> int:
    trials = load_trials(args.fixture)
    logger = BenchmarkLogger(args.results)
    harness = LocalHarness(
        backend=MockBackend(),
        search=build_search(
            args.retrieval_mode,
            args.docs_path,
            args.vector_index_path,
            args.chroma_path,
        ),
        benchmark_logger=None,
    )
    passed = 0
    total = 0

    for repeat_index in range(args.repeats):
        for trial in trials:
            response = await harness.handle(trial["input"])
            total += 1
            ok = check_trial(trial, response)
            passed += int(ok)

            logger.log(
                BenchmarkRecord(
                    run_type=f"fixture_{trial.get('trial_type', response.mode)}",
                    mode=response.mode,
                    backend=harness.backend.name,
                    model_name="mock-deterministic",
                    query=trial["input"],
                    latency_ms=response.latency_ms,
                    selected_url=getattr(response, "url", ""),
                    sources=getattr(response, "sources", []),
                    notes=(
                        f"fixture_id={trial.get('id', 'unknown')}; "
                        f"repeat={repeat_index + 1}; "
                        f"retrieval_mode={args.retrieval_mode}; "
                        f"pass={str(ok).lower()}"
                    ),
                )
            )

    print(
        f"fixture={args.fixture} repeats={args.repeats} "
        f"retrieval_mode={args.retrieval_mode} passed={passed}/{total} "
        f"results={args.results}"
    )
    return 0 if passed == total else 1


def parse_args():
    parser = argparse.ArgumentParser(description="Run repeated wiki RAG/debug benchmark fixtures.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--docs-path", type=Path, default=DEFAULT_DOCS_PATH)
    parser.add_argument("--retrieval-mode", choices=["keyword", "vector", "chroma"], default="keyword")
    parser.add_argument("--vector-index-path", type=Path, default=DEFAULT_VECTOR_INDEX_PATH)
    parser.add_argument("--chroma-path", type=Path, default=PROJECT_ROOT / ".cache" / "chroma")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_fixture(parse_args())))
