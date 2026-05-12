# Probe-Aware Tool Harness

A backend-agnostic Python harness for local AI workflows that routes commands, calls MCP wiki tools, retrieves technician documentation, and benchmarks normal tool-call generation against early-exit routing strategies.

This project explores local/private AI tooling for technician and operations workflows. It uses synthetic wiki/SOP documents to demonstrate safe internal knowledge retrieval, command-based output modes, and measurable local model performance.

This demo uses synthetic technician-style documentation and does not contain proprietary company data.

## What It Is

Probe-Aware Tool Harness is a FastAPI and Pydantic project for internal wiki workflows where loose chatbot behavior is not acceptable. It routes user commands through a Python harness, retrieves known technician-style pages, calls a model backend through an adapter, and returns strict response contracts.

The stable demo focuses on:

- `/ask` for context-grounded wiki answers with sources.
- `/debug` for exact validated wiki URL routing.
- MCP-style wiki tools over local markdown documents.
- Mock, Ollama, llama.cpp, OpenAI-compatible, and Hugging Face probe-aware backends behind one interface.
- Benchmark logging for latency and future probe experiments.

## Why It Exists

Technician workflows often depend on internal wiki pages, SOPs, and troubleshooting documents. Generic chatbots are too loose for this environment because they may invent procedures or hallucinate URLs.

This project demonstrates a stricter local AI workflow:

- command-based behavior
- known wiki page IDs
- validated URL returns
- local/private model support
- benchmarkable latency
- optional RAG retrieval

## Architecture

```txt
User Input
  ↓
FastAPI endpoint
  ↓
Python command router
  ↓
Local AI harness
  ↓
MCP wiki tool and/or retrieval layer
  ↓
ModelBackend interface
  ↓
MockBackend / OllamaBackend / LlamaCppBackend / OpenAICompatibleBackend / HuggingFaceProbeAwareBackend
  ↓
Response contract returned to API client
```

The app is intentionally not hardwired to Ollama:

```txt
App
  → Custom Python Harness
          → ModelBackend
              → MockBackend
              → OllamaBackend
              → LlamaCppBackend
              → OpenAICompatibleBackend
              → HuggingFaceProbeAwareBackend
              → Future VLLMBackend
```

## Features

- FastAPI endpoint: `POST /api/command`
- Pydantic response contracts for `/ask` and `/debug`
- Deterministic mock backend for tests and demos
- Ollama backend adapter for local model runs
- llama.cpp adapter for GGUF models through `llama-cpp-python`
- OpenAI-compatible adapter for local gateways such as LM Studio, LocalAI, or vLLM-compatible endpoints
- Hugging Face probe-aware backend that can expose hidden states for early-exit experiments
- Keyword search over synthetic markdown wiki pages
- Persistent no-dependency vector index over synthetic markdown docs
- MCP-style wiki server exposing `search_wiki` and `get_wiki_page`
- Latency and benchmark CSV logging
- Repeatable benchmark fixtures for RAG and debug-routing trials
- Early-exit probe experiment scaffolding

## Command Modes

### `/ask`

Use `/ask` for a grounded wiki answer:

```txt
/ask server will not boot after GPU tray reseat
```

Example response:

```json
{
  "mode": "ask",
  "answer": "Check the GPU tray alignment first...",
  "sources": ["wiki://gpu-tray-reseat", "wiki://psu-led-status"],
  "latency_ms": 42
}
```

### `/debug`

Use `/debug` when the client needs the best troubleshooting page URL:

```txt
/debug server will not boot after GPU tray reseat
```

The model is prompted to return a `page_id`, not a URL. The harness validates that page ID and maps it to a known `wiki://` URL.

Example response:

```json
{
  "mode": "debug",
  "url": "wiki://gpu-tray-reseat",
  "latency_ms": 18
}
```

## MCP Wiki Server

The local wiki access layer lives in `mcp_servers/wiki_server.py` and exposes:

- `search_wiki(query: str, top_k: int = 5)`
- `get_wiki_page(page_id: str)`

The MCP package is optional for the core API. If installed, run:

```bash
python mcp_servers/wiki_server.py
```

Without the optional MCP runtime, the same module still provides importable Python functions for the harness and tests.

## Model Backend Abstraction

All model calls go through `backends/base.py`:

```python
class ModelBackend(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        ...
```

Set the backend with `MODEL_BACKEND`:

```bash
MODEL_BACKEND=mock uvicorn app.main:app --reload
MODEL_BACKEND=ollama OLLAMA_MODEL=llama3.1:8b uvicorn app.main:app --reload
MODEL_BACKEND=llama_cpp LLAMA_CPP_MODEL_PATH=/models/local.gguf uvicorn app.main:app --reload
MODEL_BACKEND=openai_compatible OPENAI_COMPAT_BASE_URL=http://localhost:1234/v1 uvicorn app.main:app --reload
```

`mock` is the default so the showcase runs without pulling a model. Heavy local runtimes are optional extras:

```bash
pip install '.[llama-cpp]'
pip install '.[hf-probe]'
```

`LlamaCppBackend` expects a local GGUF model file. `OpenAICompatibleBackend` expects a local or private gateway with `/v1/chat/completions`.

## Retrieval Modes

Keyword retrieval is the default:

```bash
RETRIEVAL_MODE=keyword uvicorn app.main:app --reload
```

Persistent vector retrieval uses a JSON token-vector index:

```bash
RETRIEVAL_MODE=vector VECTOR_INDEX_PATH=.cache/wiki-vector-index.json uvicorn app.main:app --reload
```

The vector index is intentionally dependency-free. It is not a replacement for a production vector database, but it gives larger synthetic corpora a reusable retrieval path for benchmark runs.

## Synthetic Wiki Docs

The demo wiki pages are in `mcp_servers/fake_wiki_docs/`:

- `gpu-tray-reseat.md`
- `psu-led-status.md`
- `network-boot-failure.md`
- `bmc-reset-procedure.md`
- `memory-training-failure.md`

They are deliberately fake technician-style documents. Do not replace them with real company wiki content, real SOPs, proprietary URLs, internal screenshots, or customer/server data.

## Running Locally

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Start the API with the mock backend:

```bash
MODEL_BACKEND=mock uvicorn app.main:app --reload
```

Open the health endpoint:

```bash
curl http://localhost:8000/health
```

## Example Requests

Ask mode:

```bash
curl -s http://localhost:8000/api/command \
  -H 'Content-Type: application/json' \
  -d '{"input": "/ask GPU tray reseat boot failure"}' | python -m json.tool
```

Debug mode:

```bash
curl -s http://localhost:8000/api/command \
  -H 'Content-Type: application/json' \
  -d '{"input": "/debug GPU tray reseat boot failure"}' | python -m json.tool
```

See `docs/api_examples.md` for captured responses and screenshots from a running local mock-backend demo.

## Benchmark Logging

Command runs write benchmark rows to `experiments/results.csv`. Query text is hashed before logging so the CSV can track latency without storing full user prompts.

Run the baseline script:

```bash
python experiments/baseline_tool_call.py
```

Run the synthetic probe scaffold:

```bash
python experiments/probed_tool_call.py
```

Run repeated fixture trials:

```bash
python experiments/run_benchmark_fixture.py --repeats 5 --retrieval-mode keyword
python experiments/run_benchmark_fixture.py --repeats 5 --retrieval-mode vector
```

## Experimental Early-Exit Probing

This repo includes experimental scaffolding and notes for detecting tool-call intent before full generation completes. The goal is to measure whether early routing can reduce unnecessary output tokens and latency in local agent workflows.

This is experimental and separated from the stable MCP/wiki demo.

The likely research stack is:

```txt
FastAPI App
  ↓
Custom Python Harness
  ↓
Probe-aware model backend
  ↓
Hidden-state / activation access
  ↓
Tool-call intent classifier
  ↓
Model runtime
```

Ollama is useful for the stable RAG/MCP demo, but hidden-state probing needs a runtime that exposes intermediate activations. `HuggingFaceProbeAwareBackend` provides that boundary through Transformers:

```bash
pip install '.[hf-probe]'
python experiments/hf_probe_smoke.py --model distilgpt2 --prompt "/debug GPU tray reseat boot failure"
```

Without trained probe weights, the backend exposes hidden states and returns an `untrained_probe` decision. With a JSON linear-probe weights file, it can score the selected hidden-state vector against a confidence threshold.

## Limitations

- The bundled wiki is synthetic and intentionally small.
- Keyword search is the stable v1 retrieval mode.
- The persistent vector index is lightweight and dependency-free, not a production vector database.
- The Hugging Face probe backend exposes hidden states, but a useful early-exit classifier still requires trained probe weights and validation.
- `/debug` optimizes for safe known URL routing, not open-ended explanation.

## Completed Roadmap

- Real `LlamaCppBackend`.
- OpenAI-compatible local gateway backend.
- Persistent vector index for larger synthetic corpora.
- Benchmark fixtures for repeated RAG and debug-routing trials.
- Hugging Face probe-aware backend that can expose hidden states.
- Screenshots and API examples from a running local demo.

## Next Roadmap

- Add a trained probe fixture and evaluation report.
- Add a real vector database adapter behind the same retrieval interface.
- Add a vLLM-specific backend configuration example.
- Expand the synthetic technician corpus for stress testing.
