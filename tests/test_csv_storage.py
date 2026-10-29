
import uuid

import pandas as pd

from app.database.connection import get_db_connection
from app.database.csv_storage import store_dataframe


def test_store_dataframe_in_postgres():
    dataframe = pd.DataFrame(
        {
            "name": ["Aman", "Riya"],
            "age": [21, 22],
            "city": ["Satna", "Rewa"],
        }
    )

    result = store_dataframe(
        dataframe,
        f"test_{uuid.uuid4().hex[:8]}.csv",
        is_visible=False,
    )

    table_name = result["table_name"]
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT name, age, city FROM public."'
                + table_name
                + '" ORDER BY name'
            )
            rows = cursor.fetchall()

            assert rows == [
                ("Aman", 21, "Satna"),
                ("Riya", 22, "Rewa"),
            ]

            cursor.execute(
                """
                SELECT original_filename, row_count, column_count,
                       columns, is_visible
                FROM public.dataset_registry
                WHERE table_name = %s
                """,
                (table_name,),
            )
            registry_row = cursor.fetchone()

        assert result["schema"] == "public"
        assert result["row_count"] == 2
        assert result["column_count"] == 3
        assert result["columns"] == ["name", "age", "city"]

        assert registry_row is not None
        assert registry_row[0].startswith("test_")
        assert registry_row[1] == 2
        assert registry_row[2] == 3
        assert registry_row[3] == ["name", "age", "city"]
        assert registry_row[4] is False

    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.dataset_registry "
                    "WHERE table_name = %s",
                    (table_name,),
                )
                cursor.execute(
                    'DROP TABLE IF EXISTS public."'
                    + table_name
                    + '"'
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
