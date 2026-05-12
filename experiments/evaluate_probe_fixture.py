import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.probe_fixture import evaluate_probe, load_examples, write_report


DEFAULT_EVAL_PATH = PROJECT_ROOT / "experiments" / "probe_fixtures" / "tool_intent_eval.jsonl"
DEFAULT_WEIGHTS_PATH = PROJECT_ROOT / "experiments" / "probe_fixtures" / "trained_probe_weights.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / "probe_evaluation_report.md"


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate the synthetic tool-intent probe fixture.")
    parser.add_argument("--eval", type=Path, default=DEFAULT_EVAL_PATH)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    weights = json.loads(args.weights.read_text(encoding="utf-8"))
    metrics = evaluate_probe(load_examples(args.eval), weights)
    write_report(metrics, args.report)
    print(
        f"accuracy={metrics['accuracy']:.3f} "
        f"fpr={metrics['false_positive_rate']:.3f} "
        f"fnr={metrics['false_negative_rate']:.3f} "
        f"report={args.report}"
    )
    return 0 if metrics["accuracy"] >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())

