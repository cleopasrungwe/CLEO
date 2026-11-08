
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator


# CLEO application
app = FastAPI(
    title="CLEO",
    description="Cognitive Logic & Executive Operator",
    version="0.1.0",
)


# Incoming chat request structure
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


# Standard chat response structure
# Home response model
class HomeResponse(BaseModel):
    assistant: str
    message: str
    version: str


# Health response model
class HealthResponse(BaseModel):
    status: str
    assistant: str
    timestamp: datetime


# Chat response model
class ChatResponse(BaseModel):
    assistant: str
    received_message: str
    response: str


# Homepage
@app.get("/", response_model=HomeResponse)
async def home():
    return {
        "assistant": "CLEO",
        "message": "Hello, CLEO is online",
        "version": "0.1.0",
    }


# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "operational",
        "assistant": "CLEO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Chat endpoint
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
