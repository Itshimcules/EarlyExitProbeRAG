# Gemma 4 TurboQuant and Probe Benchmark Findings

- Model target: `google/gemma-4-E2B-it`
- Run mode: `dry_run`
- Environment: `macOS-26.4.1-arm64-arm-64bit`
- Reason: missing optional packages: torch, transformers, turboquant
- Results CSV: `experiments/gemma4_turboquant_probe_results.csv`

## Summary

| Configuration | Avg latency ms | Debug tokens avoided | Estimated peak memory MB | Skipped generations |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | 3518 | 0 | 11815 | 0 |
| `turboquant` | 3167 | 0 | 8507 | 0 |
| `probe` | 2202 | 42 | 11815 | 3 |
| `turboquant_probe` | 1986 | 42 | 8507 | 3 |

## Findings

- Probe routing produced the largest latency reduction in this harness because `/debug` requests can skip free-form generation once tool intent is confidently detected.
- TurboQuant is wired as an optional Gemma 4 KV-cache compression path. In dry-run mode it is modeled as reducing KV-cache memory and modestly improving generation latency.
- The local Codex machine has 8 GB RAM and no NVIDIA GPU, so this report does not claim measured Gemma 4 E2B runtime latency.
- To collect real numbers, install `.[turboquant]`, use a machine with enough accelerator memory, and run this script with `--mode real`.

## Real Run Command

```bash
pip install '.[turboquant]'
python experiments/benchmark_gemma4_turboquant_probe.py --mode real --model google/gemma-4-E2B-it
```

## References

- [Google Gemma 4 E2B model card](https://huggingface.co/google/gemma-4-E2B-it)
- [TurboQuant package](https://pypi.org/project/turboquant/)
