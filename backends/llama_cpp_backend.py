import asyncio
from pathlib import Path

from backends.base import ModelBackend


class LlamaCppBackend(ModelBackend):
    """llama.cpp adapter using the optional llama-cpp-python package."""

    name = "llama_cpp"

    def __init__(
        self,
        model_path: str | Path,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
        temperature: float = 0.2,
        max_tokens: int = 512,
        stop: list[str] | None = None,
    ):
        self.model_path = str(model_path)
        self.model = Path(model_path).name
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stop = stop or []
        self._llm = None

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_sync, prompt)

    def _generate_sync(self, prompt: str) -> str:
        llm = self._load_model()
        result = llm(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=self.stop,
        )
        choices = result.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("text", "").strip()

    def _load_model(self):
        if self._llm is not None:
            return self._llm

        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                "LLAMA_CPP_MODEL_PATH does not point to a GGUF model file: "
                f"{self.model_path}"
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "LlamaCppBackend requires the optional llama-cpp-python package. "
                "Install it with: pip install '.[llama-cpp]'"
            ) from exc

        kwargs = {
            "model_path": self.model_path,
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "verbose": False,
        }
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads

        self._llm = Llama(**kwargs)
        return self._llm

