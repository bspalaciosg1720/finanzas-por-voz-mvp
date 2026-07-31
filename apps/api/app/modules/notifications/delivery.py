from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PushMessage:
    token: str
    title: str
    body: str
    data: dict[str, str]


class PushSender(Protocol):
    enabled: bool

    async def send(self, message: PushMessage) -> None: ...


class DisabledPushSender:
    enabled = False

    async def send(self, message: PushMessage) -> None:
        return None


class FakePushSender:
    enabled = True

    def __init__(self) -> None:
        self.sent: list[PushMessage] = []

    async def send(self, message: PushMessage) -> None:
        self.sent.append(message)


def get_push_sender() -> PushSender:
    return DisabledPushSender()
