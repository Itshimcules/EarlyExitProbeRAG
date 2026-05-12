from abc import ABC, abstractmethod


class ModelBackend(ABC):
    name = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate model output from a fully rendered prompt."""

