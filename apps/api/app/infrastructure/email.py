import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as SmtpMessage
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    text: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class FileEmailSender:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or Path("tmp/mailbox")

    def send(self, message: EmailMessage) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        safe_recipient = "".join(
            char if char.isalnum() or char in "._-" else "_" for char in message.recipient
        )
        target = self.directory / f"{safe_recipient}.txt"
        target.write_text(
            f"To: {message.recipient}\nSubject: {message.subject}\n\n{message.text}\n",
            encoding="utf-8",
        )


class SmtpEmailSender:
    def send(self, message: EmailMessage) -> None:
        settings = get_settings()
        if not settings.smtp_host:
            raise RuntimeError("SMTP host is not configured")
        email = SmtpMessage()
        email["From"] = settings.email_from
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email.set_content(message.text)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_use_tls:
                client.starttls()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(email)


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.email_delivery_mode == "smtp":
        return SmtpEmailSender()
    return FileEmailSender()
