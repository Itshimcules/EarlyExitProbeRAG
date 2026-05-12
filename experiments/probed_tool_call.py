import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.benchmarks import BenchmarkLogger, BenchmarkRecord
from harness.local_harness import DEFAULT_RESULTS_PATH
from retrieval.keyword_search import KeywordWikiSearch


@dataclass(frozen=True)
class ProbeDecision:
    should_route: bool
    confidence: float
    page_id: str | None
    tokens_avoided: int


class SyntheticToolIntentProbe:
    """Placeholder for hidden-state probing experiments.

    A real implementation would read intermediate activations from a backend
    such as Hugging Face Transformers and classify tool-call intent at a chosen
    layer. This synthetic version only exercises the benchmark plumbing.
    """

    def __init__(self, threshold: float = 0.72):
        self.threshold = threshold

    def inspect(self, query: str, candidate_page_id: str) -> ProbeDecision:
        lowered = query.lower()
        confidence = 0.35
        if any(term in lowered for term in ["debug", "failure", "boot", "amber", "post"]):
            confidence += 0.4
        if candidate_page_id in lowered:
            confidence += 0.2
        confidence = min(confidence, 0.99)

        return ProbeDecision(
            should_route=confidence >= self.threshold,
            confidence=confidence,
            page_id=candidate_page_id if confidence >= self.threshold else None,
            tokens_avoided=48 if confidence >= self.threshold else 0,
        )


async def main() -> None:
    search = KeywordWikiSearch(PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs")
    probe = SyntheticToolIntentProbe()
    logger = BenchmarkLogger(Path(os.getenv("RESULTS_PATH", DEFAULT_RESULTS_PATH)))
    prompts = [
        "GPU tray reseat boot failure",
        "PSU amber power fault after service",
        "PXE network boot timeout",
        "BMC sensor data stale",
        "memory training POST code",
    ]

    for query in prompts:
        started = time.perf_counter()
        candidates = search.search(query, top_k=1)
        if not candidates:
            continue
        decision = probe.inspect(query, candidates[0].page_id)
        latency_ms = round((time.perf_counter() - started) * 1000)
        selected_url = candidates[0].url if decision.should_route else ""

        logger.log(
            BenchmarkRecord(
                run_type="probed_tool_call",
                mode="debug",
                backend="synthetic-probe",
                model_name="planned-hf-transformers-wrapper",
                query=query,
                selected_url=selected_url,
                probed_tool_call_latency_ms=latency_ms,
                tokens_avoided=decision.tokens_avoided,
                layer_index=12,
                confidence_threshold=probe.threshold,
                notes=(
                    f"confidence={decision.confidence:.2f}; "
                    "synthetic scaffold, not a hidden-state measurement"
                ),
            )
        )
        print(f"{query} -> should_route={decision.should_route} url={selected_url}")


if __name__ == "__main__":
    asyncio.run(main())
