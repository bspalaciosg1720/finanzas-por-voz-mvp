import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    icon: str
    movement_scope: str
    is_system: bool


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    icon: str = Field(default="more", min_length=1, max_length=40)
    movement_scope: str = Field(default="expense", pattern=r"^(income|expense|both)$")


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=80)
    icon: str | None = Field(default=None, min_length=1, max_length=40)
    movement_scope: str | None = Field(
        default=None,
        pattern=r"^(income|expense|both)$",
    )
