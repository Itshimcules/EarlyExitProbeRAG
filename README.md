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
- Mock and Ollama model backends behind one interface.
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
MockBackend / OllamaBackend / future backends
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
          → Future LlamaCppBackend
          → Future VLLMBackend
```

## Features

- FastAPI endpoint: `POST /api/command`
- Pydantic response contracts for `/ask` and `/debug`
- Deterministic mock backend for tests and demos
- Ollama backend adapter for local model runs
- Keyword search over synthetic markdown wiki pages
- Optional lightweight vector-like search module
- MCP-style wiki server exposing `search_wiki` and `get_wiki_page`
- Latency and benchmark CSV logging
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
```

`mock` is the default so the showcase runs without pulling a model. `ollama` is the first real local model adapter.

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

Ollama is useful for the stable RAG/MCP demo, but hidden-state probing probably needs a custom Hugging Face Transformers wrapper or another runtime that exposes intermediate activations.

## Limitations

- The bundled wiki is synthetic and intentionally small.
- Keyword search is the stable v1 retrieval mode.
- The vector search module is lightweight scaffolding, not a production vector database.
- The probe experiment is not a hidden-state implementation yet.
- `/debug` optimizes for safe known URL routing, not open-ended explanation.

## Roadmap

- Add a real `LlamaCppBackend`.
- Add an OpenAI-compatible local gateway backend.
- Add a persistent vector index for larger synthetic corpora.
- Add benchmark fixtures for repeated RAG and debug-routing trials.
- Implement a Hugging Face probe-aware backend that can expose hidden states.
- Add screenshots and API examples from a running local demo.

