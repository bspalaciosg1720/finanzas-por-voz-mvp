import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.notifications.schemas import PushDeviceCreate, PushDeviceResponse
from app.modules.notifications.service import list_devices, register_device, revoke_device

router = APIRouter(prefix="/push-devices", tags=["Push devices"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[PushDeviceResponse])
def get_devices(user: CurrentUser, db: DbSession) -> list[PushDeviceResponse]:
    return list_devices(db, user)


@router.post("", response_model=PushDeviceResponse, status_code=status.HTTP_201_CREATED)
def add_device(
    payload: PushDeviceCreate,
    user: CurrentUser,
    db: DbSession,
) -> PushDeviceResponse:
    return register_device(db, user, payload)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    revoke_device(db, user, device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
