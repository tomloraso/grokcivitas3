from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from civitas.infrastructure.config.settings import get_settings


@lru_cache(maxsize=1)
def database_url() -> str:
    return get_settings().database.url


@lru_cache(maxsize=4)
def db_engine(database_url_value: str | None = None) -> Engine:
    resolved_database_url = database_url_value or database_url()
    return create_engine(resolved_database_url, future=True)
