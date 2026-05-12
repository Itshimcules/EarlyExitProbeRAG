# vLLM Gateway Configuration

This project uses `OpenAICompatibleBackend` for vLLM instead of a separate hardwired backend. vLLM can expose an OpenAI-compatible HTTP server, so the harness only needs the gateway base URL and served model name.

Official vLLM references:

- [OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server/)
- [Docker deployment](https://docs.vllm.ai/en/stable/deployment/docker/)

## Local Environment

```bash
MODEL_BACKEND=openai_compatible
OPENAI_COMPAT_BASE_URL=http://localhost:8001/v1
OPENAI_COMPAT_MODEL=sideboard-tech-model
OPENAI_COMPAT_API_KEY=local-dev-token
```

Then run the harness API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## vLLM Docker Example

The companion `docker-compose.vllm.yml` starts a vLLM OpenAI-compatible server on port `8001`. It is a configuration example, not a default runtime dependency.

```bash
docker compose -f docker-compose.vllm.yml up
```

After vLLM is healthy, point the harness at it:

```bash
MODEL_BACKEND=openai_compatible \
OPENAI_COMPAT_BASE_URL=http://localhost:8001/v1 \
OPENAI_COMPAT_MODEL=sideboard-tech-model \
OPENAI_COMPAT_API_KEY=local-dev-token \
uvicorn app.main:app --reload
```

## Notes

- The `OPENAI_COMPAT_MODEL` value should match vLLM's served model name.
- The API key is optional in some local vLLM setups, but the example includes one because private gateways often use a bearer token.
- This config keeps vLLM behind the same backend abstraction as LM Studio, LocalAI, and other OpenAI-compatible local gateways.

