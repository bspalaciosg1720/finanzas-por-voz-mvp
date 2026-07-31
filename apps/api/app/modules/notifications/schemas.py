import uuid

from pydantic import BaseModel, ConfigDict, Field


class PushDeviceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(
        min_length=20,
        max_length=220,
        pattern=r"^(Expo|Exponent)PushToken\[[A-Za-z0-9_-]+\]$",
    )
    platform: str = Field(pattern=r"^(ios|android)$")
    device_name: str = Field(min_length=1, max_length=80)


class PushDeviceResponse(BaseModel):
    id: uuid.UUID
    platform: str
    device_name: str
    is_active: bool
