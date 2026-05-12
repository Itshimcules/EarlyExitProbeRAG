import asyncio
import json
import math
from pathlib import Path
from typing import Sequence

from backends.base import HiddenStateSnapshot, ProbeAwareBackend, ToolIntentProbeResult


class HuggingFaceProbeAwareBackend(ProbeAwareBackend):
    """Transformers backend that can expose hidden states for probe experiments."""

    name = "hf_probe"

    def __init__(
        self,
        model: str = "distilgpt2",
        device: str = "auto",
        torch_dtype: str = "auto",
        max_new_tokens: int = 256,
        temperature: float = 0.2,
        probe_layer: int = -1,
        probe_threshold: float = 0.72,
        probe_weights_path: str | Path | None = None,
    ):
        self.model = model
        self.device = device
        self.torch_dtype = torch_dtype
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.probe_layer = probe_layer
        self.probe_threshold = probe_threshold
        self.probe_weights_path = Path(probe_weights_path) if probe_weights_path else None
        self._runtime = None
        self._probe_weights = None

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_sync, prompt)

    async def inspect_hidden_states(
        self,
        prompt: str,
        layer_index: int | None = None,
        include_vector: bool = False,
    ) -> HiddenStateSnapshot:
        return await asyncio.to_thread(
            self._inspect_hidden_states_sync,
            prompt,
            layer_index,
            include_vector,
        )

    async def probe_tool_intent(
        self,
        prompt: str,
        candidate_labels: Sequence[str] = (),
        layer_index: int | None = None,
        threshold: float | None = None,
    ) -> ToolIntentProbeResult:
        snapshot = await self.inspect_hidden_states(
            prompt,
            layer_index=layer_index,
            include_vector=True,
        )
        weights = self._load_probe_weights()
        confidence = 0.0
        label = "untrained_probe"
        selected_candidate = None
        notes = "Hidden states exposed; no linear probe weights configured."

        if weights and snapshot.vector is not None:
            confidence = self._score_linear_probe(snapshot.vector, weights)
            cutoff = threshold if threshold is not None else self.probe_threshold
            label = "tool_call" if confidence >= cutoff else "continue_generation"
            notes = "Linear probe weights applied to selected hidden-state vector."
            if confidence >= cutoff and candidate_labels:
                selected_candidate = candidate_labels[0]

        return ToolIntentProbeResult(
            should_route=label == "tool_call",
            confidence=confidence,
            label=label,
            layer_index=snapshot.layer_index,
            hidden_state_shape=snapshot.shape,
            selected_candidate=selected_candidate,
            notes=notes,
        )

    def _generate_sync(self, prompt: str) -> str:
        runtime = self._load_runtime()
        tokenizer = runtime["tokenizer"]
        model = runtime["model"]
        torch = runtime["torch"]

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        generate_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature > 0,
            "temperature": self.temperature if self.temperature > 0 else None,
            "pad_token_id": tokenizer.eos_token_id,
        }
        generate_kwargs = {key: value for key, value in generate_kwargs.items() if value is not None}
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generate_kwargs)

        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def _inspect_hidden_states_sync(
        self,
        prompt: str,
        layer_index: int | None,
        include_vector: bool,
    ) -> HiddenStateSnapshot:
        runtime = self._load_runtime()
        tokenizer = runtime["tokenizer"]
        model = runtime["model"]
        torch = runtime["torch"]

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True, use_cache=False)

        hidden_states = outputs.hidden_states
        selected_index = self._normalize_layer_index(
            layer_index if layer_index is not None else self.probe_layer,
            len(hidden_states),
        )
        selected = hidden_states[selected_index]
        last_token = selected[0, -1, :].detach().float().cpu()
        vector = last_token.tolist() if include_vector else None

        return HiddenStateSnapshot(
            layer_index=selected_index,
            layer_count=len(hidden_states),
            sequence_length=int(selected.shape[1]),
            hidden_size=int(selected.shape[2]),
            shape=tuple(int(part) for part in selected.shape),
            vector=vector,
        )

    def _load_runtime(self):
        if self._runtime is not None:
            return self._runtime

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "HuggingFaceProbeAwareBackend requires optional Transformers dependencies. "
                "Install them with: pip install '.[hf-probe]'"
            ) from exc

        dtype = self._resolve_torch_dtype(torch)
        tokenizer = AutoTokenizer.from_pretrained(self.model)
        model_kwargs = {"output_hidden_states": True}
        if dtype is not None:
            model_kwargs["torch_dtype"] = dtype
        if self.device == "auto":
            model_kwargs["device_map"] = "auto"

        model = AutoModelForCausalLM.from_pretrained(self.model, **model_kwargs)
        if self.device != "auto":
            model = model.to(self.device)
        model.eval()

        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        self._runtime = {"torch": torch, "tokenizer": tokenizer, "model": model}
        return self._runtime

    def _resolve_torch_dtype(self, torch):
        if self.torch_dtype == "auto":
            return None
        if self.torch_dtype in {"float16", "fp16"}:
            return torch.float16
        if self.torch_dtype in {"bfloat16", "bf16"}:
            return torch.bfloat16
        if self.torch_dtype in {"float32", "fp32"}:
            return torch.float32
        raise ValueError(f"Unsupported HF_PROBE_TORCH_DTYPE: {self.torch_dtype}")

    def _normalize_layer_index(self, layer_index: int, layer_count: int) -> int:
        normalized = layer_index if layer_index >= 0 else layer_count + layer_index
        if normalized < 0 or normalized >= layer_count:
            raise ValueError(
                f"layer_index {layer_index} is out of range for {layer_count} hidden-state layers"
            )
        return normalized

    def _load_probe_weights(self) -> dict | None:
        if self._probe_weights is not None:
            return self._probe_weights
        if self.probe_weights_path is None:
            return None
        data = json.loads(self.probe_weights_path.read_text(encoding="utf-8"))
        if "weights" not in data:
            raise ValueError("Probe weights JSON must contain a 'weights' array.")
        self._probe_weights = data
        return data

    def _score_linear_probe(self, vector: list[float], weights: dict) -> float:
        coefficients = weights["weights"]
        if len(coefficients) != len(vector):
            raise ValueError(
                "Probe weight length does not match selected hidden-state size: "
                f"{len(coefficients)} != {len(vector)}"
            )
        bias = float(weights.get("bias", 0.0))
        logit = sum(float(weight) * value for weight, value in zip(coefficients, vector)) + bias
        return 1.0 / (1.0 + math.exp(-logit))

