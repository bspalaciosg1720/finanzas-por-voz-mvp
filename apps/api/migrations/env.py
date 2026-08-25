from logging.config import fileConfig

from alembic import context
from app.core.config import get_settings
from app.infrastructure.database import Base
from app.modules.auth import models as auth_models
from app.modules.budgets import models as budget_models
from app.modules.categories import models as category_models
from app.modules.debts import models as debt_models
from app.modules.emergency_fund import models as emergency_fund_models
from app.modules.financial_alerts import models as financial_alert_models
from app.modules.financial_calendar import models as financial_calendar_models
from app.modules.financial_health import models as financial_health_models
from app.modules.financial_strategies import models as financial_strategy_models
from app.modules.notifications import models as notification_models
from app.modules.reminders import models as reminder_models
from app.modules.savings import models as savings_models
from app.modules.transactions import models as transaction_models
from app.modules.users import models as user_models
from app.modules.voice import models as voice_models
from sqlalchemy import engine_from_config, pool

_loaded_models = (
    auth_models,
    budget_models,
    category_models,
    debt_models,
    emergency_fund_models,
    financial_alert_models,
    financial_calendar_models,
    financial_health_models,
    financial_strategy_models,
    notification_models,
    reminder_models,
    savings_models,
    transaction_models,
    user_models,
    voice_models,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
