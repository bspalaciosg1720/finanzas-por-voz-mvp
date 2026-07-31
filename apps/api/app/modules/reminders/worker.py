import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.infrastructure.database import get_session_factory
from app.modules.budgets.models import Budget, BudgetAlert
from app.modules.categories.models import Category
from app.modules.notifications.delivery import PushMessage, PushSender, get_push_sender
from app.modules.notifications.models import PushDevice
from app.modules.reminders.models import ReminderDelivery, ReminderPreference
from app.modules.reminders.schemas import ReminderCandidate
from app.modules.reminders.service import evaluate_reminders
from app.modules.users.models import User


@dataclass
class ReminderBatchResult:
    users_evaluated: int = 0
    messages_sent: int = 0
    delivery_failures: int = 0


async def run_reminder_batch(
    db: Session, sender: PushSender, *, now: datetime
) -> ReminderBatchResult:
    result = ReminderBatchResult()
    users = db.scalars(
        select(User)
        .join(ReminderPreference, ReminderPreference.user_id == User.id)
        .where(
            or_(
                ReminderPreference.daily_expense_enabled.is_(True),
                ReminderPreference.weekly_income_enabled.is_(True),
                ReminderPreference.budget_alerts_enabled.is_(True),
            )
        )
    )
    for user in users:
        result.users_evaluated += 1
        evaluation = evaluate_reminders(db, user, now=now, include_pending=True)
        if db.get(ReminderPreference, user.id).budget_alerts_enabled:
            evaluation.candidates.extend(_budget_candidates(db, user))
        devices = list(
            db.scalars(
                select(PushDevice).where(
                    PushDevice.user_id == user.id,
                    PushDevice.is_active.is_(True),
                )
            )
        )
        if not sender.enabled or not devices:
            continue
        for candidate in evaluation.candidates:
            successful = True
            for device in devices:
                try:
                    await sender.send(
                        PushMessage(
                            token=device.token,
                            title=candidate.title,
                            body=candidate.body,
                            data={
                                "type": candidate.kind,
                                "period": candidate.period_key,
                            },
                        )
                    )
                    result.messages_sent += 1
                except Exception:
                    successful = False
                    result.delivery_failures += 1
            if successful:
                delivery = db.scalar(
                    select(ReminderDelivery).where(
                        ReminderDelivery.user_id == user.id,
                        ReminderDelivery.kind == candidate.kind,
                        ReminderDelivery.period_key == candidate.period_key,
                    )
                )
                if delivery:
                    delivery.status = "delivered"
                    delivery.delivered_at = now
                    db.commit()
    return result


def _budget_candidates(db: Session, user: User) -> list[ReminderCandidate]:
    candidates: list[ReminderCandidate] = []
    alerts = db.execute(
        select(BudgetAlert, Category.name)
        .join(Budget, Budget.id == BudgetAlert.budget_id)
        .join(Category, Category.id == Budget.category_id)
        .where(
            BudgetAlert.user_id == user.id,
            BudgetAlert.read_at.is_(None),
        )
    ).all()
    for alert, category_name in alerts:
        period_key = str(alert.id)
        delivery = db.scalar(
            select(ReminderDelivery).where(
                ReminderDelivery.user_id == user.id,
                ReminderDelivery.kind == f"budget_{alert.level}",
                ReminderDelivery.period_key == period_key,
            )
        )
        if delivery and delivery.status == "delivered":
            continue
        if delivery is None:
            db.add(
                ReminderDelivery(
                    user_id=user.id,
                    kind=f"budget_{alert.level}",
                    period_key=period_key,
                )
            )
            db.commit()
        candidates.append(
            ReminderCandidate(
                kind=f"budget_{alert.level}",
                period_key=period_key,
                title=(
                    "Presupuesto excedido"
                    if alert.level == "exceeded"
                    else "Presupuesto cerca del límite"
                ),
                body=f"Revisa tu presupuesto de {category_name}.",
            )
        )
    return candidates


def main() -> None:
    with get_session_factory()() as db:
        result = asyncio.run(
            run_reminder_batch(db, get_push_sender(), now=datetime.now(UTC))
        )
    print(
        f"users={result.users_evaluated} sent={result.messages_sent} "
        f"failures={result.delivery_failures}"
    )
