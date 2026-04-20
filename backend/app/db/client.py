from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


@contextmanager
def get_db_connection() -> Iterator[psycopg.Connection[dict]]:
    database_url = settings.resolved_database_url
    if database_url is None:
        raise RuntimeError(
            "DATABASE_URL/SUPABASE_DB_URL is not configured. Set one before using job endpoints."
        )

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        yield connection

