from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator


# Initialise CLEO
app = FastAPI(
    title="CLEO",
    description="Cognitive Logic & Executive Operator",
    version="0.1.0",
)


# Chat request model
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The message sent to CLEO",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty or whitespace.")

        return value


# Chat response model
class ChatResponse(BaseModel):
    assistant: str
    received_message: str
    response: str


@app.get("/")
async def home():
    return {
        "assistant": "CLEO",
        "message": "Hello, CLEO is online",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "assistant": "CLEO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return ChatResponse(
        assistant="CLEO",
        received_message=request.message,
        response=(
            "I have received your instruction. "
            "My AI engine is not connected yet."
        ),
    )
