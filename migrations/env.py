from alembic import context
from sqlalchemy import create_engine, pool

from bonghwajigi.common.config import Settings
from bonghwajigi.db import (
    analysis_models,  # noqa: F401
    app_models,  # noqa: F401
    delivery_models,  # noqa: F401
    policy_models,  # noqa: F401
)
from bonghwajigi.db.base import Base

settings = Settings()
if settings.database_url is None or not settings.database_url.get_secret_value().strip():
    raise RuntimeError("BONGHWA_DATABASE_URL을 설정해야 마이그레이션을 실행할 수 있습니다.")
url = settings.database_url.get_secret_value()

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
