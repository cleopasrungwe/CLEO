from datetime import datetime

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

import pytest


from app.main import app, unexpected_exception_handler

AI_REQUESTS = []

class FakeAIProvider:
    """Fake AI provider for automated tests."""

    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        AI_REQUESTS.append([
            message.copy() for message in messages
        ])

        latest_message = messages[-1]["content"]
        return f"CLEO test response to: {latest_message}"
    
    async def close(self):
        pass



@pytest.fixture(autouse=True)
def mock_ai_provider(monkeypatch):
    """Replace the real AI provider during every test."""

    monkeypatch.setattr(
        "app.main.create_ai_provider",
        lambda: FakeAIProvider(),
    )


client = TestClient(app)


from app.core.prompts import CLEO_SYSTEM_PROMPT
from app.models import Conversation, Message, Memory



def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "assistant": "CLEO",
        "message": "Hello, CLEO is online",
        "version": "0.1.0",
    }



def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "operational"
    assert data["assistant"] == "CLEO"
    assert datetime.fromisoformat(data["timestamp"])



def test_chat_endpoint(test_database):
    response = client.post(
        "/chat",
        json={"message": "Hello CLEO"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assistant"] == "CLEO"
    assert data["received_message"] == "Hello CLEO"
    assert data["conversation_id"] is not None

def test_chat_messages_are_saved_to_database(test_database):
    response = client.post(
        "/chat",
        json={"message": "Remember this message"},
    )

    assert response.status_code == 200

    conversation_id = response.json()["conversation_id"]

    db = test_database()

    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.id).all()

        assert conversation is not None
        assert conversation.title == "Remember this message"

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Remember this message"
        assert messages[1].role == "assistant"

    finally:
        db.close()


def test_chat_can_continue_existing_conversation(test_database):
    first_response = client.post(
        "/chat",
        json={"message": "Hello CLEO"},
    )

    conversation_id = first_response.json()["conversation_id"]

    second_response = client.post(
        "/chat",
        json={
            "message": "How are you?",
            "conversation_id": conversation_id,
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conversation_id

    db = test_database()

    try:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.id).all()

        assert len(messages) == 4
        assert messages[0].content == "Hello CLEO"
        assert messages[2].content == "How are you?"

    finally:
        db.close()

def test_chat_rejects_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""},
    )

    assert response.status_code == 422



def test_chat_returns_structured_validation_error():
    response = client.post(
        "/chat",
        json={"message": ""},
    )

    assert response.status_code == 422
    assert response.json() == {
        "assistant": "CLEO",
        "error": "validation_error",
        "message": (
            "Request validation failed. Check your input and try again."
        ),
    }



def test_chat_returns_structured_error_for_whitespace():
    response = client.post(
        "/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422
    assert response.json()["assistant"] == "CLEO"
    assert response.json()["error"] == "validation_error"



def test_chat_rejects_whitespace_message():
    response = client.post(
        "/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422



def test_chat_rejects_message_over_2000_characters():
    response = client.post(
        "/chat",
        json={"message": "A" * 2001},
    )

    assert response.status_code == 422



def test_chat_rejects_missing_message():
    response = client.post("/chat", json={})

    assert response.status_code == 422



def test_chat_rejects_null_message():
    response = client.post(
        "/chat",
        json={"message": None},
    )

    assert response.status_code == 422



def test_home_response_schema():
    response = client.get("/openapi.json")
    schema = response.json()

    home_schema = (
        schema["paths"]["/"]["get"]["responses"]
        ["200"]["content"]["application/json"]["schema"]
    )

    assert home_schema["$ref"] == "#/components/schemas/HomeResponse"



def test_health_response_schema():
    response = client.get("/openapi.json")
    schema = response.json()

    health_schema = (
        schema["paths"]["/health"]["get"]["responses"]
        ["200"]["content"]["application/json"]["schema"]
    )

    assert health_schema["$ref"] == "#/components/schemas/HealthResponse"



def test_chat_response_schema():
    response = client.get("/openapi.json")
    schema = response.json()

    chat_schema = (
        schema["paths"]["/chat"]["post"]["responses"]
        ["200"]["content"]["application/json"]["schema"]
    )

    assert chat_schema["$ref"] == "#/components/schemas/ChatResponse"

    assert (
        schema["paths"]["/chat"]["post"]["responses"]
        ["422"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )

    assert (
        schema["paths"]["/chat"]["post"]["responses"]
        ["500"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )



def test_unexpected_errors_return_structured_response():
    test_app = FastAPI()

    test_app.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )

    @test_app.get("/test-error")
    async def trigger_error():
        raise RuntimeError("Sensitive internal details")

    test_client = TestClient(
        test_app,
        raise_server_exceptions=False,
    )

    response = test_client.get("/test-error")

    assert response.status_code == 500

    assert response.json() == {
        "assistant": "CLEO",
        "error": "internal_server_error",
        "message": (
            "An unexpected error occurred. Please try again later."
        ),
    }

    assert "Sensitive internal details" not in response.text

def test_responses_include_request_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_each_request_has_a_unique_request_id():
    first_response = client.get("/")
    second_response = client.get("/health")

    first_id = first_response.headers["X-Request-ID"]
    second_id = second_response.headers["X-Request-ID"]

    assert first_id != second_id


def test_requests_are_recorded_in_logs(caplog):
    with caplog.at_level(logging.INFO, logger="cleo"):
        response = client.get("/health")

    assert response.status_code == 200

    assert any(
        "Request completed" in record.message
        and "/health" in record.message
        and "Status: 200" in record.message
        for record in caplog.records
    )



def test_list_conversations(test_database):
    client.post(
        "/chat",
        json={"message": "First conversation"},
    )

    response = client.get("/conversations")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "First conversation"


def test_get_conversation_history(test_database):
    chat_response = client.post(
        "/chat",
        json={"message": "Hello CLEO"},
    )

    conversation_id = chat_response.json()["conversation_id"]

    response = client.get(
        f"/conversations/{conversation_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == conversation_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello CLEO"
    assert data["messages"][1]["role"] == "assistant"


def test_get_nonexistent_conversation(test_database):
    response = client.get("/conversations/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found."


def test_rename_conversation(test_database):
    # Create a conversation
    response = client.post(
        "/chat",
        json={"message": "Original conversation"},
    )

    conversation_id = response.json()["conversation_id"]

    # Rename the conversation
    rename_response = client.patch(
        f"/conversations/{conversation_id}",
        json={"title": "My New Conversation"},
    )

    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "My New Conversation"


def test_rename_nonexistent_conversation(test_database):
    response = client.patch(
        "/conversations/99999",
        json={"title": "New Title"},
    )

    assert response.status_code == 404


def test_rename_conversation_rejects_blank_title(test_database):
    chat_response = client.post(
        "/chat",
        json={"message": "Test conversation"},
    )

    conversation_id = chat_response.json()["conversation_id"]

    response = client.patch(
        f"/conversations/{conversation_id}",
        json={"title": "   "},
    )

    assert response.status_code == 422



def test_delete_conversation(test_database):
    chat_response = client.post(
        "/chat",
        json={"message": "Conversation to delete"},
    )

    conversation_id = chat_response.json()["conversation_id"]

    response = client.delete(
        f"/conversations/{conversation_id}"
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == conversation_id

    history_response = client.get(
        f"/conversations/{conversation_id}"
    )

    assert history_response.status_code == 404


def test_delete_nonexistent_conversation(test_database):
    response = client.delete("/conversations/99999")

    assert response.status_code == 404


def test_delete_conversation_also_deletes_messages(test_database):
    chat_response = client.post(
        "/chat",
        json={"message": "Delete my messages too"},
    )

    conversation_id = chat_response.json()["conversation_id"]

    response = client.delete(
        f"/conversations/{conversation_id}"
    )

    assert response.status_code == 200

    db = test_database()

    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()

        assert conversation is None
        assert messages == []

    finally:
        db.close()



def test_chat_ai_failure_rolls_back_new_conversation(
    test_database,
    monkeypatch,
):
    """A failed AI request must not leave an empty conversation."""

    class FailingAIProvider:
        async def generate_response(self, message: str) -> str:
            raise RuntimeError("Simulated AI service failure")

        async def close(self):
            pass

    monkeypatch.setattr(
        "app.main.create_ai_provider",
        lambda: FailingAIProvider(),
    )

    response = client.post(
        "/chat",
        json={"message": "Test AI failure"},
    )

    # CLEO should report that its AI service is unavailable.
    assert response.status_code == 503

    # The failed request should not leave a conversation in the database.
    with test_database() as db:
        assert db.query(Conversation).count() == 0

def test_chat_includes_system_prompt_and_conversation_history(
    test_database,
):
    AI_REQUESTS.clear()

    # Start a new conversation
    first_response = client.post(
        "/chat",
        json={"message": "My name is Alex."},
    )

    assert first_response.status_code == 200

    conversation_id = first_response.json()["conversation_id"]

    # Continue the same conversation
    second_response = client.post(
        "/chat",
        json={
            "message": "What is my name?",
            "conversation_id": conversation_id,
        },
    )

    assert second_response.status_code == 200

    # Inspect the messages sent during the second request
    messages = AI_REQUESTS[-1]

    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == CLEO_SYSTEM_PROMPT

    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "My name is Alex."

    assert messages[2]["role"] == "assistant"

    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "What is my name?"

def test_chat_saves_explicit_memory(test_database):
    AI_REQUESTS.clear()

    response = client.post(
        "/chat",
        json={
            "message": "Remember that I like Python."
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert "I'll remember that: I like Python" in (
        response_data["response"]
    )

    # Verify that the memory was saved in the database
    db = test_database()

    try:
        memories = db.query(Memory).all()

        assert len(memories) == 1
        assert memories[0].category == "general"
        assert memories[0].content == "I like Python"

    finally:
        db.close()

    # Verify that CLEO did not call the AI provider
    assert len(AI_REQUESTS) == 0

def test_chat_includes_saved_memories_in_ai_context(test_database):
    from app.services.memory.service import save_memory

    # Save a memory before starting a new conversation
    db = test_database()

    try:
        save_memory(
            db=db,
            category="general",
            content="I like Python.",
        )
    finally:
        db.close()

    AI_REQUESTS.clear()

    # Start a new conversation
    response = client.post(
        "/chat",
        json={
            "message": "What programming language do I like?"
        },
    )

    assert response.status_code == 200

    # Inspect the context sent to the AI provider
    messages = AI_REQUESTS[-1]

    memory_messages = [
        message
        for message in messages
        if message["role"] == "system"
        and "USER-APPROVED MEMORIES" in message["content"]
    ]

    assert len(memory_messages) == 1
    assert "I like Python." in memory_messages[0]["content"]

def test_list_memories(test_database):
    from app.services.memory.service import save_memory

    db = test_database()

    try:
        save_memory(
            db=db,
            category="personal",
            content="I like Python.",
        )

        save_memory(
            db=db,
            category="education",
            content="I studied Information Technology.",
        )
    finally:
        db.close()

    response = client.get("/memories")

    assert response.status_code == 200

    memories = response.json()

    assert len(memories) == 2
    assert memories[0]["content"] == (
        "I studied Information Technology."
    )
    assert memories[1]["content"] == "I like Python."

    assert memories[0]["category"] == "education"
    assert memories[1]["category"] == "personal"

def test_delete_memory_endpoint(test_database):
    from app.services.memory.service import save_memory

    db = test_database()

    try:
        memory = save_memory(
            db=db,
            category="personal",
            content="I like Python.",
        )

        memory_id = memory.id

    finally:
        db.close()

    response = client.delete(
        f"/memories/{memory_id}"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["assistant"] == "CLEO"
    assert response_data["message"] == (
        "Memory deleted successfully."
    )
    assert response_data["memory_id"] == memory_id

    # Verify that the memory was actually deleted
    response = client.get("/memories")

    assert response.status_code == 200
    assert response.json() == []


def test_delete_nonexistent_memory_endpoint():
    response = client.delete("/memories/99999")

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Memory not found."
    )