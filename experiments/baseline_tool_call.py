import asyncio
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backends.mock_backend import MockBackend
from harness.benchmarks import BenchmarkLogger, BenchmarkRecord
from harness.local_harness import DEFAULT_RESULTS_PATH, LocalHarness
from retrieval.keyword_search import KeywordWikiSearch


PROMPTS = [
    "/debug GPU tray reseat boot failure",
    "/debug PSU amber power fault after service",
    "/debug PXE network boot timeout",
    "/debug BMC sensor data stale",
    "/debug memory training POST code",
]


async def main() -> None:
    harness = LocalHarness(
        backend=MockBackend(),
        search=KeywordWikiSearch(PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs"),
    )
    logger = BenchmarkLogger(Path(os.getenv("RESULTS_PATH", DEFAULT_RESULTS_PATH)))

    for prompt in PROMPTS:
        response = await harness.handle(prompt)
        logger.log(
            BenchmarkRecord(
                run_type="baseline_tool_call",
                mode=response.mode,
                backend="mock",
                model_name="mock-deterministic",
                query=prompt,
                baseline_tool_call_latency_ms=response.latency_ms,
                selected_url=response.url,
                notes="Full debug prompt rendered before route selection.",
            )
        )
        print(f"{prompt} -> {response.url} ({response.latency_ms} ms)")


if __name__ == "__main__":
    asyncio.run(main())
