from fastapi import APIRouter

from app.modules.auth.router import profile_router
from app.modules.auth.router import router as auth_router
from app.modules.budgets.router import router as budgets_router
from app.modules.categories.router import router as categories_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.health.router import router as health_router
from app.modules.notifications.router import router as notifications_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reports.router import router as reports_router
from app.modules.savings.router import router as savings_router
from app.modules.transaction_suggestions.router import router as suggestions_router
from app.modules.transactions.router import router as transactions_router
from app.modules.voice.router import router as voice_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(reminders_router)
api_router.include_router(savings_router)
api_router.include_router(auth_router)
api_router.include_router(budgets_router)
api_router.include_router(profile_router)
api_router.include_router(categories_router)
api_router.include_router(transactions_router)
api_router.include_router(suggestions_router)
api_router.include_router(dashboard_router)
api_router.include_router(voice_router)
