
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

# Standard error response structure
class ErrorResponse(BaseModel):
    assistant: str
    error: str
    message: str


# Handle invalid requests
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    error_response = ErrorResponse(
        assistant="CLEO",
        error="validation_error",
        message="Request validation failed. Check your input and try again.",
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
    )

# Handle unexpected server errors
@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    error_response = ErrorResponse(
        assistant="CLEO",
        error="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )

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
@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Request validation failed",
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected server error",
        },
    },
)
async def chat(request: ChatRequest):
    return ChatResponse(
        assistant="CLEO",
        received_message=request.message,
        response=(
            "I have received your instruction. "
            "My AI engine is not connected yet."
        ),
    )
