import json
import math
from dataclasses import dataclass
from pathlib import Path


FEATURE_NAMES = [
    "debug_command",
    "ask_command",
    "hardware_symptom",
    "routing_language",
    "question_language",
    "source_language",
    "exact_page_language",
    "general_help_language",
]

HARDWARE_TERMS = {
    "amber",
    "array",
    "bay",
    "bmc",
    "boot",
    "cache",
    "cpu",
    "degraded",
    "dimm",
    "drive",
    "fan",
    "firmware",
    "gpu",
    "memory",
    "network",
    "nvme",
    "post",
    "psu",
    "pxe",
    "raid",
    "rebuild",
    "thermal",
    "throttle",
}
ROUTING_TERMS = {"debug", "find", "open", "route", "troubleshooting", "page", "sop"}
QUESTION_TERMS = {"what", "why", "how", "explain", "summarize", "context", "mean"}
SOURCE_TERMS = {"cite", "source", "sources", "references"}
EXACT_TERMS = {"exact", "single", "url", "page_id", "page"}
GENERAL_HELP_TERMS = {"answer", "explain", "overview", "summary", "context"}


@dataclass(frozen=True)
class ProbeExample:
    id: str
    text: str
    label: int


def load_examples(path: Path) -> list[ProbeExample]:
    examples = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        data = json.loads(line)
        examples.append(
            ProbeExample(
                id=data.get("id", f"line_{line_number}"),
                text=data["text"],
                label=int(data["label"]),
            )
        )
    return examples


def extract_features(text: str) -> list[float]:
    lowered = text.lower()
    tokens = set(lowered.replace("/", " ").replace("-", " ").split())

    return [
        1.0 if lowered.strip().startswith("/debug") else 0.0,
        1.0 if lowered.strip().startswith("/ask") else 0.0,
        _term_score(tokens, HARDWARE_TERMS),
        _term_score(tokens, ROUTING_TERMS),
        _term_score(tokens, QUESTION_TERMS),
        _term_score(tokens, SOURCE_TERMS),
        _term_score(tokens, EXACT_TERMS),
        _term_score(tokens, GENERAL_HELP_TERMS),
    ]


def train_linear_probe(
    examples: list[ProbeExample],
    epochs: int = 1800,
    learning_rate: float = 0.25,
    l2: float = 0.002,
) -> dict:
    weights = [0.0] * len(FEATURE_NAMES)
    bias = 0.0
    rows = [(extract_features(example.text), example.label) for example in examples]

    for _ in range(epochs):
        for features, label in rows:
            prediction = sigmoid(dot(weights, features) + bias)
            error = prediction - label
            for index, value in enumerate(features):
                weights[index] -= learning_rate * (error * value + l2 * weights[index])
            bias -= learning_rate * error

    return {
        "feature_names": FEATURE_NAMES,
        "weights": [round(weight, 6) for weight in weights],
        "bias": round(bias, 6),
        "threshold": 0.72,
        "training_note": (
            "Synthetic text-feature logistic probe for evaluation plumbing; "
            "not a hidden-state classifier."
        ),
    }


def evaluate_probe(examples: list[ProbeExample], weights_payload: dict) -> dict:
    rows = []
    threshold = float(weights_payload.get("threshold", 0.72))
    for example in examples:
        features = extract_features(example.text)
        confidence = score_features(features, weights_payload)
        prediction = 1 if confidence >= threshold else 0
        rows.append(
            {
                "id": example.id,
                "label": example.label,
                "prediction": prediction,
                "confidence": confidence,
                "text": example.text,
            }
        )

    true_positive = sum(1 for row in rows if row["label"] == 1 and row["prediction"] == 1)
    true_negative = sum(1 for row in rows if row["label"] == 0 and row["prediction"] == 0)
    false_positive = sum(1 for row in rows if row["label"] == 0 and row["prediction"] == 1)
    false_negative = sum(1 for row in rows if row["label"] == 1 and row["prediction"] == 0)
    total = len(rows)

    return {
        "threshold": threshold,
        "total": total,
        "accuracy": (true_positive + true_negative) / total if total else 0.0,
        "false_positive_rate": false_positive / max(1, false_positive + true_negative),
        "false_negative_rate": false_negative / max(1, false_negative + true_positive),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "rows": rows,
    }


def score_features(features: list[float], weights_payload: dict) -> float:
    return sigmoid(dot(weights_payload["weights"], features) + float(weights_payload.get("bias", 0.0)))


def write_report(metrics: dict, output_path: Path) -> None:
    lines = [
        "# Probe Fixture Evaluation Report",
        "",
        "This report evaluates a trained synthetic text-feature probe fixture.",
        "It validates the early-exit measurement pipeline without claiming hidden-state performance.",
        "",
        "## Metrics",
        "",
        f"- Total examples: {metrics['total']}",
        f"- Accuracy: {metrics['accuracy']:.3f}",
        f"- False positive rate: {metrics['false_positive_rate']:.3f}",
        f"- False negative rate: {metrics['false_negative_rate']:.3f}",
        f"- Threshold: {metrics['threshold']:.2f}",
        "",
        "## Examples",
        "",
        "| ID | Label | Prediction | Confidence | Text |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in metrics["rows"]:
        text = row["text"].replace("|", "\\|")
        lines.append(
            f"| `{row['id']}` | {row['label']} | {row['prediction']} | "
            f"{row['confidence']:.3f} | {text} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The fixture is intentionally synthetic. It gives the repo a repeatable trained-probe artifact, "
            "but a production early-exit classifier still needs hidden-state features, held-out prompts, "
            "hardware-specific latency measurement, and false-route safety analysis.",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _term_score(tokens: set[str], terms: set[str]) -> float:
    matches = len(tokens & terms)
    return min(1.0, matches / 2.0)

