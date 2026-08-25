from fastapi import APIRouter

from app.modules.auth.router import profile_router
from app.modules.auth.router import router as auth_router
from app.modules.budgets.router import router as budgets_router
from app.modules.categories.router import router as categories_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.debts.router import router as debts_router
from app.modules.emergency_fund.router import router as emergency_fund_router
from app.modules.financial_alerts.router import router as financial_alerts_router
from app.modules.financial_assistant.router import router as financial_assistant_router
from app.modules.financial_calendar.router import router as financial_calendar_router
from app.modules.financial_health.router import router as financial_health_router
from app.modules.financial_strategies.router import router as financial_strategies_router
from app.modules.health.router import router as health_router
from app.modules.notifications.router import router as notifications_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reports.router import router as reports_router
from app.modules.savings.router import router as savings_router
from app.modules.simulations.router import router as simulations_router
from app.modules.transaction_suggestions.router import router as suggestions_router
from app.modules.transactions.router import router as transactions_router
from app.modules.voice.router import router as voice_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(debts_router)
api_router.include_router(emergency_fund_router)
api_router.include_router(financial_calendar_router)
api_router.include_router(financial_assistant_router)
api_router.include_router(financial_health_router)
api_router.include_router(financial_strategies_router)
api_router.include_router(financial_alerts_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(reminders_router)
api_router.include_router(savings_router)
api_router.include_router(simulations_router)
api_router.include_router(auth_router)
api_router.include_router(budgets_router)
api_router.include_router(profile_router)
api_router.include_router(categories_router)
api_router.include_router(transactions_router)
api_router.include_router(suggestions_router)
api_router.include_router(dashboard_router)
api_router.include_router(voice_router)
