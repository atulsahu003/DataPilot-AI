
import psycopg2

from app.core.config import settings


def get_db_connection():
    """Create and return a PostgreSQL database connection."""

    database_url = settings.database_url.replace(
        "postgresql+psycopg2://",
        "postgresql://",
        1,
    )

    return psycopg2.connect(
        database_url,
        connect_timeout=5,
    )
