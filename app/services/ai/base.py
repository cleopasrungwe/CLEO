
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base interface for all CLEO AI providers."""

    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """Generate a response using conversation history."""
        pass

    async def close(self):
        """Release resources used by the AI provider."""
        pass
