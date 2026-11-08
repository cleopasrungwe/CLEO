from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, unexpected_exception_handler

client = TestClient(app)


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


def test_chat_endpoint():
    response = client.post(
        "/chat",
        json={"message": "Hello CLEO"},
    )

    assert response.status_code == 200
    assert response.json()["assistant"] == "CLEO"
    assert response.json()["received_message"] == "Hello CLEO"


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