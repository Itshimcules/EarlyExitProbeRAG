# Layer Probe Notes

This directory keeps the early-exit research separate from the stable wiki/RAG demo.

## Research Question

Can a local agent workflow reduce latency by detecting tool-call intent before a model finishes generating explanatory text or structured tool-call output?

## Hypothesis

For repeated technician workflows, the model may commit to a retrieval or routing action in intermediate hidden states before the final answer text is emitted. A lightweight classifier over selected layers could route the request early when confidence is high.

## Stable Demo Boundary

The FastAPI app, command router, keyword retrieval, MCP wiki wrapper, and backend abstraction are stable demo features. They do not require activation access.

## Experimental Boundary

Early-exit probing likely requires a backend that exposes hidden states, such as a custom Hugging Face Transformers inference wrapper. Ollama is useful for local RAG demos, but it is not the right first target for hidden-state probing because it does not expose the necessary layer activations through its standard generation API.

`backends/hf_probe_backend.py` now provides that wrapper boundary. It can:

- generate text through `transformers.AutoModelForCausalLM`
- inspect hidden-state metadata for a selected layer
- optionally return the selected last-token vector
- run a simple linear probe if a JSON weights file is provided

Run a smoke check with:

```bash
pip install '.[hf-probe]'
python experiments/hf_probe_smoke.py --model distilgpt2 --prompt "/debug GPU tray reseat boot failure"
```

Without trained probe weights, the backend exposes hidden states but returns an `untrained_probe` decision instead of pretending to classify tool intent.

## Metrics To Track

- baseline_tool_call_latency_ms
- probed_tool_call_latency_ms
- tokens_avoided
- false_positive_rate
- false_negative_rate
- layer_index
- confidence_threshold
- model_name
- quantization
- hardware

## Non-Claims

This scaffold does not claim that early-exit probing works. It only defines the measurement surface and keeps the future experiment modular enough to swap in a probe-aware backend.
