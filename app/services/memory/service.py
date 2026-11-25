

import re

from sqlalchemy.orm import Session

from app.models import Memory


def save_memory(
    db: Session,
    category: str,
    content: str,
) -> Memory:
    """Save a new user memory."""

    memory = Memory(
        category=category.strip().lower(),
        content=content.strip(),
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory

def extract_explicit_memory_request(
    message: str,
) -> str | None:
    """Extract information the user explicitly asks CLEO to remember."""

    pattern = r"^(?:please\s+)?remember that\s+(.+?)\s*[.!?]*$"

    match = re.match(
        pattern,
        message.strip(),
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    content = match.group(1).strip()

    if not content:
        return None

    return content

def get_all_memories(db: Session) -> list[Memory]:
    """Retrieve all saved memories."""

    return (
        db.query(Memory)
        .order_by(Memory.created_at.desc())
        .all()
    )


def delete_memory(
    db: Session,
    memory_id: int,
) -> bool:
    """Delete a memory by its ID."""

    memory = (
        db.query(Memory)
        .filter(Memory.id == memory_id)
        .first()
    )

    if memory is None:
        return False

    db.delete(memory)
    db.commit()

    return True
