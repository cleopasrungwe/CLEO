
from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.openai_provider import OpenAIProvider


def create_ai_provider() -> AIProvider:
    """Create the AI provider configured for CLEO."""

    if settings.AI_PROVIDER == "local":
        return OllamaProvider()

    if settings.AI_PROVIDER == "openai":
        return OpenAIProvider()

    raise ValueError(
        f"Unsupported AI provider: {settings.AI_PROVIDER}"
    )
