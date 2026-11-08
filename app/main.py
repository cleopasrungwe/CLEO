
import logging
import time
import uuid

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


# CLEO logging configuration
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("cleo")


# CLEO application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CLEO backend starting up")

    yield

    logger.info("CLEO backend shutting down")


# CLEO application
app = FastAPI(
    title="CLEO",
    description="Cognitive Logic & Executive Operator",
    version="0.1.0",
    lifespan=lifespan,
)


# HTTP request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration = time.perf_counter() - start_time

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed | ID: %s | Method: %s | "
            "Path: %s | Status: %s | Duration: %.4f seconds",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response

    except Exception:
        duration = time.perf_counter() - start_time

        logger.error(
            "Request processing failed | ID: %s | Method: %s | "
            "Path: %s | Duration: %.4f seconds",
            request_id,
            request.method,
            request.url.path,
            duration,
        )

        raise


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


# Response models
class HomeResponse(BaseModel):
    assistant: str
    message: str
    version: str


class HealthResponse(BaseModel):
    status: str
    assistant: str
    timestamp: datetime


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
    logger.warning(
        "Request validation failed | Request ID: %s",
        getattr(request.state, "request_id", "unknown"),
    )

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
    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    logger.exception(
        "Unhandled application exception | Request ID: %s",
        request_id,
    )

    error_response = ErrorResponse(
        assistant="CLEO",
        error="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
        headers={
            "X-Request-ID": request_id,
        },
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
