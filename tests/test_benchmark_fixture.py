import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_fixture_script_runs(tmp_path):
    results_path = tmp_path / "fixture-results.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/run_benchmark_fixture.py",
            "--repeats",
            "1",
            "--results",
            str(results_path),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "passed=13/13" in completed.stdout
    assert results_path.exists()
    assert "fixture_debug" in results_path.read_text(encoding="utf-8")
