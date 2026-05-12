import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.probe_fixture import load_examples, train_linear_probe


DEFAULT_TRAIN_PATH = PROJECT_ROOT / "experiments" / "probe_fixtures" / "tool_intent_train.jsonl"
DEFAULT_WEIGHTS_PATH = PROJECT_ROOT / "experiments" / "probe_fixtures" / "trained_probe_weights.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Train the synthetic tool-intent probe fixture.")
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_WEIGHTS_PATH)
    parser.add_argument("--epochs", type=int, default=1800)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    weights = train_linear_probe(load_examples(args.train), epochs=args.epochs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(weights, indent=2), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

