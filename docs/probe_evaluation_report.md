# Probe Fixture Evaluation Report

This report evaluates a trained synthetic text-feature probe fixture.
It validates the early-exit measurement pipeline without claiming hidden-state performance.

## Metrics

- Total examples: 8
- Accuracy: 1.000
- False positive rate: 0.000
- False negative rate: 0.000
- Threshold: 0.72

## Examples

| ID | Label | Prediction | Confidence | Text |
| --- | ---: | ---: | ---: | --- |
| `eval_debug_gpu` | 1 | 1 | 0.963 | /debug GPU tray reseat boot failure |
| `eval_debug_storage` | 1 | 1 | 0.885 | find exact page_id for storage controller cache warning |
| `eval_debug_nvme` | 1 | 1 | 0.987 | route to single troubleshooting page for NVMe bay missing |
| `eval_debug_thermal` | 1 | 1 | 0.963 | /debug CPU thermal throttle warning and fan ramp |
| `eval_ask_gpu` | 0 | 0 | 0.012 | /ask explain GPU tray reseat and PSU LED checks |
| `eval_ask_sources` | 0 | 0 | 0.006 | summarize sources for network boot failure context |
| `eval_ask_raid` | 0 | 0 | 0.016 | what does degraded RAID array mean during rebuild |
| `eval_ask_firmware` | 0 | 0 | 0.054 | give me an overview of firmware rollback risks |

## Interpretation

The fixture is intentionally synthetic. It gives the repo a repeatable trained-probe artifact, but a production early-exit classifier still needs hidden-state features, held-out prompts, hardware-specific latency measurement, and false-route safety analysis.
