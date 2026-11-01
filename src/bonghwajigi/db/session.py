from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bonghwajigi.common.config import Settings


def session_factory(settings: Settings):
    if not settings.database_url or not settings.database_url.get_secret_value().strip():
        raise RuntimeError("BONGHWA_DATABASE_URL이 필요합니다.")
    engine = create_engine(
        settings.database_url.get_secret_value(),
        pool_size=3,
        max_overflow=2,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
        hide_parameters=True,
    )
    return sessionmaker(engine, expire_on_commit=False)
