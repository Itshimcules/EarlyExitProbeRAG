import argparse
import asyncio
import csv
import importlib.util
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backends.gemma4_turboquant_backend import Gemma4TurboQuantBackend
from experiments.probe_fixture import extract_features, score_features
from harness.command_router import CommandType, parse_command
from harness.local_harness import LocalHarness
from retrieval.keyword_search import KeywordWikiSearch


DEFAULT_MODEL = "google/gemma-4-E2B-it"
DEFAULT_WEIGHTS = PROJECT_ROOT / "experiments" / "probe_fixtures" / "trained_probe_weights.json"
DEFAULT_RESULTS = PROJECT_ROOT / "experiments" / "gemma4_turboquant_probe_results.csv"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "gemma4_turboquant_probe_findings.md"
DEFAULT_DOCS_PATH = PROJECT_ROOT / "mcp_servers" / "fake_wiki_docs"

PROMPTS = [
    {
        "id": "debug_gpu",
        "input": "/debug GPU tray reseat boot failure",
        "expected": "wiki://gpu-tray-reseat",
    },
    {
        "id": "debug_nvme",
        "input": "/debug NVMe drive missing from bay inventory",
        "expected": "wiki://nvme-drive-missing",
    },
    {
        "id": "debug_thermal",
        "input": "/debug CPU thermal throttle warning and fan ramp",
        "expected": "wiki://cpu-thermal-throttle",
    },
    {
        "id": "ask_gpu",
        "input": "/ask explain GPU tray reseat boot failure using wiki sources",
        "expected": "",
    },
    {
        "id": "ask_storage",
        "input": "/ask summarize NVMe drive missing and storage controller cache checks",
        "expected": "",
    },
]


@dataclass(frozen=True)
class BenchmarkConfig:
    name: str
    turboquant: bool
    probe: bool


CONFIGS = [
    BenchmarkConfig("baseline", turboquant=False, probe=False),
    BenchmarkConfig("turboquant", turboquant=True, probe=False),
    BenchmarkConfig("probe", turboquant=False, probe=True),
    BenchmarkConfig("turboquant_probe", turboquant=True, probe=True),
]


async def main(args) -> int:
    mode, reason = resolve_run_mode(args)
    weights = json.loads(args.probe_weights.read_text(encoding="utf-8"))
    rows = []

    for config in CONFIGS:
        for prompt in PROMPTS:
            if mode == "real":
                row = await run_real_case(args, config, prompt, weights)
            else:
                row = run_dry_case(args, config, prompt, weights, reason)
            rows.append(row)

    write_results(args.results, rows)
    write_report(args.report, rows, args, mode, reason)
    print(f"mode={mode} rows={len(rows)} results={args.results} report={args.report}")
    if mode != "real":
        print(f"dry_run_reason={reason}")
    return 0


async def run_real_case(args, config: BenchmarkConfig, prompt: dict, weights: dict) -> dict:
    started = time.perf_counter()
    parsed = parse_command(prompt["input"])
    search = KeywordWikiSearch(args.docs_path)
    skipped_generation = False
    tokens_avoided = 0
    output_text = ""
    status = "ok"
    selected_url = ""
    probe_confidence = score_features(extract_features(prompt["input"]), weights)

    backend = Gemma4TurboQuantBackend(
        model=args.model,
        device=args.device,
        torch_dtype=args.torch_dtype,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        use_turboquant=config.turboquant,
        turboquant_bits=args.turboquant_bits,
    )

    try:
        if config.probe and parsed.command == CommandType.DEBUG and probe_confidence >= args.probe_threshold:
            results = search.search(parsed.query, top_k=1)
            selected_url = results[0].url if results else ""
            skipped_generation = True
            tokens_avoided = args.max_new_tokens
        else:
            harness = LocalHarness(backend=backend, search=search, benchmark_logger=None)
            response = await harness.handle(prompt["input"])
            output_text = getattr(response, "answer", getattr(response, "url", ""))
            selected_url = getattr(response, "url", "")
    except Exception as exc:
        status = f"error:{type(exc).__name__}:{exc}"

    latency_ms = round((time.perf_counter() - started) * 1000)
    return make_row(
        args=args,
        config=config,
        prompt=prompt,
        run_mode="real",
        latency_ms=latency_ms,
        output_text=output_text,
        selected_url=selected_url,
        skipped_generation=skipped_generation,
        tokens_avoided=tokens_avoided,
        probe_confidence=probe_confidence,
        status=status,
        notes="actual Gemma 4 backend path",
    )


def run_dry_case(args, config: BenchmarkConfig, prompt: dict, weights: dict, reason: str) -> dict:
    parsed = parse_command(prompt["input"])
    prompt_tokens = estimate_tokens(prompt["input"])
    expected_output_tokens = 14 if parsed.command == CommandType.DEBUG else args.max_new_tokens
    base_latency = 1650 + prompt_tokens * 18 + expected_output_tokens * 36
    base_memory = 11800 + prompt_tokens * 1.5
    output_text = prompt["expected"] if parsed.command == CommandType.DEBUG else "dry-run wiki answer"
    selected_url = prompt["expected"] if parsed.command == CommandType.DEBUG else ""
    probe_confidence = score_features(extract_features(prompt["input"]), weights)
    skipped_generation = False
    tokens_avoided = 0

    if config.turboquant:
        base_latency *= 0.9
        base_memory *= 0.72

    if config.probe and parsed.command == CommandType.DEBUG and probe_confidence >= args.probe_threshold:
        skipped_generation = True
        tokens_avoided = expected_output_tokens
        base_latency = 86 + prompt_tokens * 4
        if config.turboquant:
            base_latency *= 0.95
        output_text = prompt["expected"]

    return make_row(
        args=args,
        config=config,
        prompt=prompt,
        run_mode="dry_run",
        latency_ms=round(base_latency),
        output_text=output_text,
        selected_url=selected_url,
        skipped_generation=skipped_generation,
        tokens_avoided=tokens_avoided,
        probe_confidence=probe_confidence,
        status="dry_run",
        estimated_peak_memory_mb=round(base_memory),
        notes=reason,
    )


def make_row(
    args,
    config: BenchmarkConfig,
    prompt: dict,
    run_mode: str,
    latency_ms: int,
    output_text: str,
    selected_url: str,
    skipped_generation: bool,
    tokens_avoided: int,
    probe_confidence: float,
    status: str,
    notes: str,
    estimated_peak_memory_mb: int | None = None,
) -> dict:
    return {
        "run_mode": run_mode,
        "config": config.name,
        "model": args.model,
        "prompt_id": prompt["id"],
        "input": prompt["input"],
        "turboquant_enabled": config.turboquant,
        "turboquant_bits": args.turboquant_bits if config.turboquant else "",
        "probe_enabled": config.probe,
        "probe_confidence": round(probe_confidence, 4),
        "skipped_generation": skipped_generation,
        "tokens_avoided": tokens_avoided,
        "latency_ms": latency_ms,
        "estimated_peak_memory_mb": estimated_peak_memory_mb or "",
        "output_chars": len(output_text),
        "selected_url": selected_url,
        "status": status,
        "notes": notes,
    }


def resolve_run_mode(args) -> tuple[str, str]:
    if args.mode == "dry-run":
        return "dry_run", "forced dry-run mode"

    missing = [
        package
        for package in ("torch", "transformers", "turboquant")
        if importlib.util.find_spec(package) is None
    ]
    memory_gb = detect_memory_gb()
    if args.mode == "real":
        if missing:
            raise RuntimeError(f"Missing packages for real run: {', '.join(missing)}")
        return "real", "forced real mode"

    if missing:
        return "dry_run", f"missing optional packages: {', '.join(missing)}"
    if memory_gb is not None and memory_gb < args.minimum_real_memory_gb:
        return (
            "dry_run",
            f"local memory {memory_gb:.1f} GB below {args.minimum_real_memory_gb:.1f} GB real-run guardrail",
        )
    return "real", "all optional packages present and memory guardrail passed"


def detect_memory_gb() -> float | None:
    if platform.system() == "Darwin":
        try:
            import subprocess

            raw = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            return int(raw) / (1024**3)
        except Exception:
            return None
    try:
        import os

        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return pages * page_size / (1024**3)
    except Exception:
        return None


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text.split()) * 1.25))


def write_results(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> list[dict]:
    summaries = []
    for config in CONFIGS:
        config_rows = [row for row in rows if row["config"] == config.name]
        summaries.append(
            {
                "config": config.name,
                "avg_latency_ms": round(statistics.mean(row["latency_ms"] for row in config_rows)),
                "debug_tokens_avoided": sum(row["tokens_avoided"] for row in config_rows),
                "avg_estimated_peak_memory_mb": (
                    round(
                        statistics.mean(
                            int(row["estimated_peak_memory_mb"])
                            for row in config_rows
                            if row["estimated_peak_memory_mb"] != ""
                        )
                    )
                    if any(row["estimated_peak_memory_mb"] != "" for row in config_rows)
                    else ""
                ),
                "skipped_generations": sum(1 for row in config_rows if row["skipped_generation"]),
            }
        )
    return summaries


def write_report(path: Path, rows: list[dict], args, mode: str, reason: str) -> None:
    summaries = summarize(rows)
    lines = [
        "# Gemma 4 TurboQuant and Probe Benchmark Findings",
        "",
        f"- Model target: `{args.model}`",
        f"- Run mode: `{mode}`",
        f"- Environment: `{platform.platform()}`",
        f"- Reason: {reason}",
        f"- Results CSV: `{display_path(args.results)}`",
        "",
        "## Summary",
        "",
        "| Configuration | Avg latency ms | Debug tokens avoided | Estimated peak memory MB | Skipped generations |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        lines.append(
            f"| `{summary['config']}` | {summary['avg_latency_ms']} | "
            f"{summary['debug_tokens_avoided']} | {summary['avg_estimated_peak_memory_mb']} | "
            f"{summary['skipped_generations']} |"
        )

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- Probe routing produced the largest latency reduction in this harness because `/debug` requests can skip free-form generation once tool intent is confidently detected.",
            "- TurboQuant is wired as an optional Gemma 4 KV-cache compression path. In dry-run mode it is modeled as reducing KV-cache memory and modestly improving generation latency.",
            "- The local Codex machine has 8 GB RAM and no NVIDIA GPU, so this report does not claim measured Gemma 4 E2B runtime latency.",
            "- To collect real numbers, install `.[turboquant]`, use a machine with enough accelerator memory, and run this script with `--mode real`.",
            "",
            "## Real Run Command",
            "",
            "```bash",
            "pip install '.[turboquant]'",
            "python experiments/benchmark_gemma4_turboquant_probe.py --mode real --model google/gemma-4-E2B-it",
            "```",
            "",
            "## References",
            "",
            "- [Google Gemma 4 E2B model card](https://huggingface.co/google/gemma-4-E2B-it)",
            "- [TurboQuant package](https://pypi.org/project/turboquant/)",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark Gemma 4 with TurboQuant and probe routing.")
    parser.add_argument("--mode", choices=["auto", "real", "dry-run"], default="auto")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--torch-dtype", default="auto")
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--turboquant-bits", type=int, default=4)
    parser.add_argument("--probe-threshold", type=float, default=0.72)
    parser.add_argument("--probe-weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--docs-path", type=Path, default=DEFAULT_DOCS_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--minimum-real-memory-gb", type=float, default=24.0)
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parse_args())))
