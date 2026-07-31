from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.reminders.models import ReminderDelivery, ReminderPreference
from app.modules.reminders.schemas import (
    ReminderCandidate,
    ReminderEvaluation,
    ReminderPreferencesResponse,
    ReminderPreferencesUpdate,
)
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def get_or_create_preferences(db: Session, user: User) -> ReminderPreference:
    preferences = db.get(ReminderPreference, user.id)
    if preferences is None:
        preferences = ReminderPreference(user_id=user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def public_preferences(
    preferences: ReminderPreference, user: User
) -> ReminderPreferencesResponse:
    return ReminderPreferencesResponse(
        daily_expense_enabled=preferences.daily_expense_enabled,
        weekly_income_enabled=preferences.weekly_income_enabled,
        budget_alerts_enabled=preferences.budget_alerts_enabled,
        local_hour=preferences.local_hour,
        local_minute=preferences.local_minute,
        timezone=user.timezone,
    )


def update_preferences(
    db: Session, user: User, payload: ReminderPreferencesUpdate
) -> ReminderPreferencesResponse:
    preferences = get_or_create_preferences(db, user)
    for field, value in payload.model_dump().items():
        setattr(preferences, field, value)
    db.commit()
    db.refresh(preferences)
    return public_preferences(preferences, user)


def _bounds(day: date, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(UTC)
    return start, end


def _has_movement(
    db: Session,
    user: User,
    movement_type: str,
    start: datetime,
    end: datetime,
) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(
            Transaction.user_id == user.id,
            Transaction.type == movement_type,
            Transaction.status == "confirmed",
            Transaction.deleted_at.is_(None),
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
    )
    return bool(count)


def evaluate_reminders(
    db: Session, user: User, *, now: datetime, include_pending: bool = False
) -> ReminderEvaluation:
    preferences = get_or_create_preferences(db, user)
    local_now = now.astimezone(ZoneInfo(user.timezone))
    scheduled = time(preferences.local_hour, preferences.local_minute)
    if local_now.time().replace(tzinfo=None) < scheduled:
        return ReminderEvaluation(candidates=[])

    candidates: list[ReminderCandidate] = []
    today = local_now.date()
    if preferences.daily_expense_enabled:
        start, end = _bounds(today, user.timezone)
        _add_if_due(
            db,
            user,
            candidates,
            kind="missing_daily_expense",
            period_key=today.isoformat(),
            has_movement=_has_movement(db, user, "expense", start, end),
            title="Registra tus gastos",
            body="No has registrado gastos hoy.",
            include_pending=include_pending,
        )

    if preferences.weekly_income_enabled and local_now.weekday() == 6:
        week_start = today - timedelta(days=6)
        start, _ = _bounds(week_start, user.timezone)
        _, end = _bounds(today, user.timezone)
        iso_year, iso_week, _ = today.isocalendar()
        _add_if_due(
            db,
            user,
            candidates,
            kind="missing_weekly_income",
            period_key=f"{iso_year}-W{iso_week:02d}",
            has_movement=_has_movement(db, user, "income", start, end),
            title="Revisa tus ingresos",
            body="No has registrado ingresos esta semana.",
            include_pending=include_pending,
        )
    db.commit()
    return ReminderEvaluation(candidates=candidates)


def _add_if_due(
    db: Session,
    user: User,
    candidates: list[ReminderCandidate],
    *,
    kind: str,
    period_key: str,
    has_movement: bool,
    title: str,
    body: str,
    include_pending: bool,
) -> None:
    if has_movement:
        return
    delivery = db.scalar(
        select(ReminderDelivery).where(
            ReminderDelivery.user_id == user.id,
            ReminderDelivery.kind == kind,
            ReminderDelivery.period_key == period_key,
        )
    )
    if delivery and (delivery.status == "delivered" or not include_pending):
        return
    if delivery is None:
        db.add(ReminderDelivery(user_id=user.id, kind=kind, period_key=period_key))
    candidates.append(
        ReminderCandidate(
            kind=kind, period_key=period_key, title=title, body=body
        )
    )
