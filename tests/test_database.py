from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Conversation, Message


# Create an isolated in-memory SQLite database
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable SQLite foreign keys
from sqlalchemy import event


@event.listens_for(test_engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def setup_function():
    Base.metadata.create_all(bind=test_engine)


def teardown_function():
    Base.metadata.drop_all(bind=test_engine)


def test_database_tables_are_created():
    inspector = inspect(test_engine)

    tables = inspector.get_table_names()

    assert "conversations" in tables
    assert "messages" in tables


def test_create_conversation():
    db = TestingSessionLocal()

    try:
        conversation = Conversation(
            title="My first CLEO conversation"
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.id is not None
        assert conversation.title == "My first CLEO conversation"

    finally:
        db.close()


def test_save_messages_to_conversation():
    db = TestingSessionLocal()

    try:
        conversation = Conversation(
            title="CLEO database test"
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hello CLEO",
        )

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Hello! How can I help you?",
        )

        db.add_all([user_message, assistant_message])
        db.commit()

        saved_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id
            )
            .order_by(Message.id)
            .all()
        )

        assert len(saved_messages) == 2
        assert saved_messages[0].role == "user"
        assert saved_messages[1].role == "assistant"

    finally:
        db.close()


def test_conversation_relationship():
    db = TestingSessionLocal()

    try:
        conversation = Conversation(
            title="Relationship test"
        )

        conversation.messages.append(
            Message(
                role="user",
                content="Testing relationship",
            )
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == (
            "Testing relationship"
        )

    finally:
        db.close()


def test_deleting_conversation_deletes_messages():
    db = TestingSessionLocal()

    try:
        conversation = Conversation(
            title="Deletion test"
        )

        conversation.messages.append(
            Message(
                role="user",
                content="This message should be deleted",
            )
        )

        db.add(conversation)
        db.commit()

        conversation_id = conversation.id

        db.delete(conversation)
        db.commit()

        remaining_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .count()
        )

        assert remaining_messages == 0

    finally:
        db.close()