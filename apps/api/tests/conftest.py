from collections.abc import Generator

import pytest
from app.infrastructure.database import Base, get_db
from app.infrastructure.email import EmailMessage, EmailSender, get_email_sender
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_factory() -> Generator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def mailbox() -> list[EmailMessage]:
    return []


@pytest.fixture
def client(
    db_factory: sessionmaker[Session],
    mailbox: list[EmailMessage],
) -> Generator[TestClient]:
    application = create_app()

    def override_db() -> Generator[Session]:
        with db_factory() as session:
            yield session

    class CapturingEmailSender(EmailSender):
        def send(self, message: EmailMessage) -> None:
            mailbox.append(message)

    sender = CapturingEmailSender()

    def override_email_sender() -> EmailSender:
        return sender

    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_email_sender] = override_email_sender
    with TestClient(application) as test_client:
        yield test_client
