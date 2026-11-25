
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.ai.base import AIProvider


class OllamaProvider(AIProvider):
    """Local AI provider powered by Ollama."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key="ollama",
            base_url=settings.OLLAMA_BASE_URL,
        )

        self.model = settings.OLLAMA_MODEL

    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    async def close(self):
        await self.client.close()
