import json
import subprocess
import sys
from pathlib import Path

from experiments.probe_fixture import evaluate_probe, load_examples


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = PROJECT_ROOT / "experiments" / "probe_fixtures"


def test_trained_probe_fixture_scores_eval_set():
    weights = json.loads((FIXTURE_DIR / "trained_probe_weights.json").read_text(encoding="utf-8"))
    metrics = evaluate_probe(load_examples(FIXTURE_DIR / "tool_intent_eval.jsonl"), weights)

    assert metrics["accuracy"] == 1.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 0.0


def test_probe_fixture_report_script_runs(tmp_path):
    report_path = tmp_path / "probe-report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/evaluate_probe_fixture.py",
            "--report",
            str(report_path),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "accuracy=1.000" in completed.stdout
    assert "False positive rate: 0.000" in report_path.read_text(encoding="utf-8")
