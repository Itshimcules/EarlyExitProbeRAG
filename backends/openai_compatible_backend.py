import httpx

from backends.base import ModelBackend


class OpenAICompatibleBackend(ModelBackend):
    """Adapter for local gateways that expose an OpenAI-compatible API."""

    name = "openai_compatible"

    def __init__(
        self,
        model: str = "local-model",
        base_url: str = "http://localhost:1234/v1",
        api_key: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
        timeout_seconds: float = 60,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        if "content" in message:
            return str(message["content"]).strip()
        return str(choice.get("text", "")).strip()
