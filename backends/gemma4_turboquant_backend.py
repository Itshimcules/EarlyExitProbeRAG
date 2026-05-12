from pathlib import Path

from backends.hf_probe_backend import HuggingFaceProbeAwareBackend


class Gemma4TurboQuantBackend(HuggingFaceProbeAwareBackend):
    """Gemma 4 Transformers backend with optional TurboQuant KV-cache compression."""

    name = "gemma4_turboquant"

    def __init__(
        self,
        model: str = "google/gemma-4-E2B-it",
        device: str = "auto",
        torch_dtype: str = "auto",
        max_new_tokens: int = 128,
        temperature: float = 0.2,
        probe_layer: int = -1,
        probe_threshold: float = 0.72,
        probe_weights_path: str | Path | None = None,
        use_turboquant: bool = False,
        turboquant_bits: int = 4,
    ):
        super().__init__(
            model=model,
            device=device,
            torch_dtype=torch_dtype,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            probe_layer=probe_layer,
            probe_threshold=probe_threshold,
            probe_weights_path=probe_weights_path,
        )
        self.use_turboquant = use_turboquant
        self.turboquant_bits = turboquant_bits
        self.quantization = f"turboquant-{turboquant_bits}bit" if use_turboquant else "none"

    def _load_runtime(self):
        if self._runtime is not None:
            return self._runtime

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "Gemma4TurboQuantBackend requires optional Transformers dependencies. "
                "Install them with: pip install '.[turboquant]'"
            ) from exc

        dtype = self._resolve_torch_dtype(torch)
        processor = AutoProcessor.from_pretrained(self.model)
        model_kwargs = {"output_hidden_states": True}
        if dtype is None:
            model_kwargs["dtype"] = "auto"
        else:
            model_kwargs["torch_dtype"] = dtype
        if self.device == "auto":
            model_kwargs["device_map"] = "auto"

        model = AutoModelForCausalLM.from_pretrained(self.model, **model_kwargs)
        if self.device != "auto":
            model = model.to(self.device)
        model.eval()

        self._runtime = {"torch": torch, "tokenizer": processor, "model": model}
        return self._runtime

    def _generate_sync(self, prompt: str) -> str:
        runtime = self._load_runtime()
        processor = runtime["tokenizer"]
        model = runtime["model"]
        torch = runtime["torch"]

        text = prompt
        if hasattr(processor, "apply_chat_template"):
            text = processor.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )

        inputs = processor(text=text, return_tensors="pt").to(model.device)
        generate_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature > 0,
            "temperature": self.temperature if self.temperature > 0 else None,
            "pad_token_id": getattr(processor, "eos_token_id", None),
            "use_cache": True,
        }

        if self.use_turboquant:
            generate_kwargs["past_key_values"] = self._create_turboquant_cache()

        generate_kwargs = {key: value for key, value in generate_kwargs.items() if value is not None}
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generate_kwargs)

        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return processor.decode(new_tokens, skip_special_tokens=True).strip()

    def _create_turboquant_cache(self):
        try:
            from turboquant import TurboQuantCache
        except ImportError as exc:
            raise RuntimeError(
                "Gemma4TurboQuantBackend with use_turboquant=True requires the optional "
                "turboquant package. Install it with: pip install '.[turboquant]'"
            ) from exc

        return TurboQuantCache(bits=self.turboquant_bits)
