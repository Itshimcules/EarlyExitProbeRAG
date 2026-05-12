import csv
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESULT_FIELDS = [
    "timestamp",
    "run_type",
    "mode",
    "backend",
    "model_name",
    "query_hash",
    "selected_url",
    "sources_json",
    "latency_ms",
    "baseline_tool_call_latency_ms",
    "probed_tool_call_latency_ms",
    "tokens_avoided",
    "false_positive_rate",
    "false_negative_rate",
    "layer_index",
    "confidence_threshold",
    "quantization",
    "hardware",
    "notes",
]


@dataclass
class BenchmarkRecord:
    run_type: str
    mode: str
    backend: str
    query: str
    latency_ms: int | None = None
    model_name: str = ""
    selected_url: str = ""
    sources: list[str] = field(default_factory=list)
    baseline_tool_call_latency_ms: int | None = None
    probed_tool_call_latency_ms: int | None = None
    tokens_avoided: int | None = None
    false_positive_rate: float | None = None
    false_negative_rate: float | None = None
    layer_index: int | None = None
    confidence_threshold: float | None = None
    quantization: str = ""
    hardware: str = ""
    notes: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_type": self.run_type,
            "mode": self.mode,
            "backend": self.backend,
            "model_name": self.model_name,
            "query_hash": hashlib.sha256(self.query.encode("utf-8")).hexdigest()[:16],
            "selected_url": self.selected_url,
            "sources_json": json.dumps(self.sources),
            "latency_ms": self.latency_ms if self.latency_ms is not None else "",
            "baseline_tool_call_latency_ms": (
                self.baseline_tool_call_latency_ms
                if self.baseline_tool_call_latency_ms is not None
                else ""
            ),
            "probed_tool_call_latency_ms": (
                self.probed_tool_call_latency_ms
                if self.probed_tool_call_latency_ms is not None
                else ""
            ),
            "tokens_avoided": self.tokens_avoided if self.tokens_avoided is not None else "",
            "false_positive_rate": (
                self.false_positive_rate if self.false_positive_rate is not None else ""
            ),
            "false_negative_rate": (
                self.false_negative_rate if self.false_negative_rate is not None else ""
            ),
            "layer_index": self.layer_index if self.layer_index is not None else "",
            "confidence_threshold": (
                self.confidence_threshold if self.confidence_threshold is not None else ""
            ),
            "quantization": self.quantization,
            "hardware": self.hardware,
            "notes": self.notes,
        }


class BenchmarkLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: BenchmarkRecord) -> None:
        should_write_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=RESULT_FIELDS)
            if should_write_header:
                writer.writeheader()
            writer.writerow(record.to_row())

