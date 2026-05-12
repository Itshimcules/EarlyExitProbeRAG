# Case Study: Technician Wiki Routing Harness

## Scenario

Technician workflows often depend on internal wiki pages, SOPs, and troubleshooting documents. A generic chatbot can be risky in this environment because it may invent a procedure, blend two pages together, or hallucinate a URL that looks plausible.

This project demonstrates a stricter local AI workflow using synthetic documentation:

- command-based behavior
- known wiki page IDs
- validated URL returns
- local/private model support
- benchmarkable latency
- optional RAG retrieval

## Design Choice: Commands Over Chat Drift

The harness supports two explicit modes:

- `/ask` retrieves wiki context and returns an answer with sources.
- `/debug` retrieves candidate pages, asks the model to choose a `page_id`, validates that ID, and returns only the known wiki URL.

The important safety point is that `/debug` does not let the model produce the final URL. The harness owns URL mapping.

## Design Choice: MCP Access Layer Plus Retrieval Layer

The MCP wiki server and vector database concepts solve different problems:

```txt
MCP wiki server = access layer
Vector DB = semantic search / memory layer
```

The project uses local markdown wiki docs, keyword search, and a persistent dependency-free vector index. The MCP-style wrapper exposes the wiki tools cleanly, while the vector index gives repeated benchmark runs a reusable retrieval path.

## Design Choice: Backend-Agnostic Model Calls

The FastAPI route never calls Ollama directly. It calls the local harness, which calls a `ModelBackend`.

That allows the stable app to run with:

- `MockBackend` for tests, CI, and no-model demos.
- `OllamaBackend` for local model demos.
- `LlamaCppBackend` for GGUF models through llama.cpp.
- `OpenAICompatibleBackend` for local gateways.
- `HuggingFaceProbeAwareBackend` for hidden-state probe experiments.
- future vLLM-specific backends.

## Research Track

The early-exit probe idea is intentionally isolated under `experiments/`. It is not part of the stable routing contract.

The research question is whether hidden-state probing can detect tool-call intent early enough to avoid generating unnecessary tokens. The Hugging Face backend can expose selected hidden-state layers, but the project still treats useful probe classification as experimental and dependent on trained weights plus validation.

## What This Proves

This repository shows how to build internal AI tooling for operations and technician workflows:

- clean API contracts
- safe command routing
- validated internal document IDs
- backend abstraction
- local-first deployment path
- benchmark instrumentation
- credible separation between production behavior and research scaffolding
