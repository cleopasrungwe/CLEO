
import logging
import time
import uuid

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session


# CLEO logging configuration
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.models import Conversation, Message


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
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

    # Initialize database tables
    Base.metadata.create_all(bind=engine)

    logger.info("CLEO database initialized successfully")

    yield

    logger.info("CLEO backend shutting down")


# CLEO application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
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

    conversation_id: int | None = Field(
        default=None,
        gt=0,
        description="Existing conversation ID, if continuing a conversation",
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
    conversation_id: int
    received_message: str
    response: str


class ErrorResponse(BaseModel):
    assistant: str
    error: str
    message: str

class ConversationSummary(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageHistoryItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageHistoryItem]


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
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # Find an existing conversation or create a new one
    if request.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

    else:
        conversation = Conversation(
            title=request.message[:200],
        )

        db.add(conversation)
        db.flush()

    # Save the user's message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # Temporary assistant response until the AI engine is connected
    assistant_response = (
        "I have received your instruction. "
        "My AI engine is not connected yet."
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_response,
    )

    db.add_all([
        user_message,
        assistant_message,
    ])

    # Update the conversation's last activity time
    conversation.updated_at = datetime.now(timezone.utc)

    # Commit both messages to the database
    db.commit()

    return ChatResponse(
        assistant="CLEO",
        conversation_id=conversation.id,
        received_message=request.message,
        response=assistant_response,
    )


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

# List all saved conversations
@app.get(
    "/conversations",
    response_model=list[ConversationSummary],
)
async def list_conversations(
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return conversations


# Retrieve one conversation and its messages
@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistoryResponse,
)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
    }



