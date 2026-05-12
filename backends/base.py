from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class HiddenStateSnapshot:
    layer_index: int
    layer_count: int
    sequence_length: int
    hidden_size: int
    shape: tuple[int, ...]
    vector: list[float] | None = None


@dataclass(frozen=True)
class ToolIntentProbeResult:
    should_route: bool
    confidence: float
    label: str
    layer_index: int
    hidden_state_shape: tuple[int, ...]
    selected_candidate: str | None = None
    notes: str = ""


class ModelBackend(ABC):
    name = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate model output from a fully rendered prompt."""


class ProbeAwareBackend(ModelBackend):
    @abstractmethod
    async def inspect_hidden_states(
        self,
        prompt: str,
        layer_index: int | None = None,
        include_vector: bool = False,
    ) -> HiddenStateSnapshot:
        """Return metadata, and optionally a vector, for a selected hidden-state layer."""

    @abstractmethod
    async def probe_tool_intent(
        self,
        prompt: str,
        candidate_labels: Sequence[str] = (),
        layer_index: int | None = None,
        threshold: float | None = None,
    ) -> ToolIntentProbeResult:
        """Classify whether tool routing should happen before full generation."""
