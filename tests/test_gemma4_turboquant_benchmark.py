import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_gemma4_turboquant_benchmark_dry_run(tmp_path):
    results = tmp_path / "gemma4-results.csv"
    report = tmp_path / "gemma4-report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/benchmark_gemma4_turboquant_probe.py",
            "--mode",
            "dry-run",
            "--results",
            str(results),
            "--report",
            str(report),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "mode=dry_run" in completed.stdout
    assert results.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "Gemma 4 TurboQuant and Probe Benchmark Findings" in report_text
    assert "`turboquant_probe`" in report_text
