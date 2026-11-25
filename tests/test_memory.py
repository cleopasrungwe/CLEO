
import pytest

from app.models import Memory
from app.services.memory.service import (
    save_memory,
    get_all_memories,
    delete_memory,
)


def test_save_memory(test_database):
    db = test_database()

    try:
        memory = save_memory(
            db,
            category="personal",
            content="My favourite programming language is Python.",
        )

        assert memory.id is not None
        assert memory.category == "personal"
        assert memory.content == (
            "My favourite programming language is Python."
        )

    finally:
        db.close()


def test_get_all_memories(test_database):
    db = test_database()

    try:
        save_memory(
            db,
            category="personal",
            content="I enjoy Python.",
        )

        memories = get_all_memories(db)

        assert len(memories) == 1
        assert memories[0].content == "I enjoy Python."

    finally:
        db.close()


def test_delete_memory(test_database):
    db = test_database()

    try:
        memory = save_memory(
            db,
            category="personal",
            content="I enjoy programming.",
        )

        result = delete_memory(db, memory.id)

        assert result is True
        assert db.query(Memory).count() == 0

    finally:
        db.close()


def test_delete_nonexistent_memory(test_database):
    db = test_database()

    try:
        result = delete_memory(db, 999)

        assert result is False

    finally:
        db.close()

from app.services.memory.service import (
    extract_explicit_memory_request,
)


def test_extract_explicit_memory_request():
    result = extract_explicit_memory_request(
        "Remember that I like Python."
    )

    assert result == "I like Python"


def test_extract_memory_request_with_please():
    result = extract_explicit_memory_request(
        "Please remember that I prefer short answers."
    )

    assert result == "I prefer short answers"


def test_ignore_normal_messages():
    result = extract_explicit_memory_request(
        "I like Python."
    )

    assert result is None


def test_ignore_questions_about_memory():
    result = extract_explicit_memory_request(
        "What do you remember about me?"
    )

    assert result is None