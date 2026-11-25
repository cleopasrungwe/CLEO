
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI-powered AI provider for CLEO."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured.")

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

        self.model = settings.OPENAI_MODEL

    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=messages,
        )

        return response.output_text

    async def close(self):
        await self.client.close()
