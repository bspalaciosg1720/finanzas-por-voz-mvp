import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.notifications.models import PushDevice
from app.modules.notifications.schemas import PushDeviceCreate, PushDeviceResponse
from app.modules.users.models import User


def register_device(
    db: Session,
    user: User,
    payload: PushDeviceCreate,
) -> PushDeviceResponse:
    device = db.scalar(select(PushDevice).where(PushDevice.token == payload.token))
    if device is None:
        device = PushDevice(user_id=user.id, **payload.model_dump())
        db.add(device)
    else:
        device.user_id = user.id
        device.platform = payload.platform
        device.device_name = payload.device_name
        device.is_active = True
    db.commit()
    db.refresh(device)
    return public_device(device)


def list_devices(db: Session, user: User) -> list[PushDeviceResponse]:
    devices = db.scalars(
        select(PushDevice)
        .where(PushDevice.user_id == user.id, PushDevice.is_active.is_(True))
        .order_by(PushDevice.created_at.desc())
    )
    return [public_device(device) for device in devices]


def revoke_device(
    db: Session,
    user: User,
    device_id: uuid.UUID,
) -> None:
    device = db.scalar(
        select(PushDevice).where(
            PushDevice.id == device_id,
            PushDevice.user_id == user.id,
            PushDevice.is_active.is_(True),
        )
    )
    if device is None:
        raise AppError(
            status=404,
            title="Push device not found",
            detail="The requested push device does not exist.",
            error_type="push-device-not-found",
        )
    device.is_active = False
    db.commit()


def public_device(device: PushDevice) -> PushDeviceResponse:
    return PushDeviceResponse(
        id=device.id,
        platform=device.platform,
        device_name=device.device_name,
        is_active=device.is_active,
    )
