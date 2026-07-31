import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from app.modules.categories.service import create_category, deactivate_category, update_category

router = APIRouter(prefix="/categories", tags=["Categories"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CategoryResponse])
def list_categories(user: CurrentUser, db: DbSession) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .where(
                Category.is_active.is_(True),
                or_(Category.user_id.is_(None), Category.user_id == user.id),
            )
            .order_by(Category.is_system.desc(), Category.name)
        )
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def add_category(
    payload: CategoryCreate,
    user: CurrentUser,
    db: DbSession,
) -> Category:
    return create_category(db, user, payload)


@router.patch("/{category_id}", response_model=CategoryResponse)
def edit_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    user: CurrentUser,
    db: DbSession,
) -> Category:
    return update_category(db, user, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    deactivate_category(db, user, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
