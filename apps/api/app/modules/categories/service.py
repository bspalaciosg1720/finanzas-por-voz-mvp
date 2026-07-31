import re
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate
from app.modules.users.models import User


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def create_category(db: Session, user: User, payload: CategoryCreate) -> Category:
    category = Category(
        user_id=user.id,
        name=" ".join(payload.name.split()),
        slug=slugify(payload.name),
        icon=payload.icon,
        movement_scope=payload.movement_scope,
        is_system=False,
        is_active=True,
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise category_conflict() from exc
    return category


def update_category(
    db: Session,
    user: User,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> Category:
    category = get_owned_category(db, user, category_id)
    values = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "name" in values:
        category.name = " ".join(values["name"].split())
        category.slug = slugify(values["name"])
    if "icon" in values:
        category.icon = values["icon"]
    if "movement_scope" in values:
        category.movement_scope = values["movement_scope"]
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise category_conflict() from exc
    return category


def deactivate_category(
    db: Session,
    user: User,
    category_id: uuid.UUID,
) -> None:
    category = get_owned_category(db, user, category_id)
    category.is_active = False
    db.commit()


def get_owned_category(db: Session, user: User, category_id: uuid.UUID) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user.id,
            Category.is_system.is_(False),
        )
    )
    if category is None:
        raise AppError(
            status=404,
            title="Category not found",
            detail="The requested category does not exist.",
            error_type="category-not-found",
        )
    return category


def category_conflict() -> AppError:
    return AppError(
        status=409,
        title="Category already exists",
        detail="Use a different category name.",
        error_type="category-conflict",
    )
