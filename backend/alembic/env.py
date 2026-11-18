from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import ConfigurationError, load_settings
from app.modules.database.base import Base
from app.modules.database.models import (  # noqa: F401
    Address,
    Category,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Product,
    QueryRun,
    Review,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
MANAGED_SCHEMAS = {"ecommerce", "app_meta"}


def _get_migrator_url() -> str:
    settings = load_settings()
    if settings.database_migrator_url is None:
        raise ConfigurationError(
            "DATABASE_MIGRATOR_URL is required to run Alembic migrations. "
            "Configure it in the root .env file (see .env.example)."
        )
    return settings.database_migrator_url.get_secret_value()


def include_name(name: str | None, type_: str, parent_names: dict[str, object]) -> bool:
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_get_migrator_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema="app_meta",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(_get_migrator_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema="app_meta",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
