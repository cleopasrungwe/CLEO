from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


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
