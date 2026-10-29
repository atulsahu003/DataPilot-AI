
import json

from app.database.connection import get_db_connection



def initialize_dataset_registry() -> None:
    """Create the dataset registry table if it does not exist."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS public.dataset_registry (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    table_name VARCHAR(100) UNIQUE NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    row_count INTEGER NOT NULL CHECK (row_count >= 0),
                    column_count INTEGER NOT NULL CHECK (column_count > 0),
                    columns JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    is_visible BOOLEAN NOT NULL DEFAULT TRUE
                    
                    
                );
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def register_dataset(
    table_name: str,
    original_filename: str,
    row_count: int,
    column_count: int,
    columns: list[str],
) -> None:
    """Register a CSV dataset after it has been stored successfully."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.dataset_registry (
                    table_name,
                    original_filename,
                    row_count,
                    column_count,
                    columns
                )
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (table_name) DO NOTHING;
                """,
                (
                    table_name,
                    original_filename,
                    row_count,
                    column_count,
                    json.dumps(columns),
                ),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_registered_datasets() -> list[dict]:
    """Return datasets explicitly registered by the application."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name,
                    original_filename,
                    row_count,
                    column_count,
                    columns,
                    created_at
                FROM public.dataset_registry
                WHERE is_visible = TRUE
                ORDER BY created_at DESC, id DESC;
                """
            )

            rows = cursor.fetchall()

        return [
            {
                "table_name": row[0],
                "original_filename": row[1],
                "row_count": row[2],
                "column_count": row[3],
                "columns": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    finally:
        connection.close()
