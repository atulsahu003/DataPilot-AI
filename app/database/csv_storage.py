

import json
import re
import uuid

import pandas as pd
from psycopg2 import sql

from app.database.connection import get_db_connection



def _safe_table_name(filename: str) -> str:
    """Generate a predictable, safe PostgreSQL table name."""

    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    name = name.rsplit(".", 1)[0].lower()
    name = re.sub(r"[^a-z0-9_]+", "_", name).strip("_")
    name = name[:40] or "uploaded_data"

    # A suffix prevents accidental collisions with existing tables.
    return f"csv_{name}_{uuid.uuid4().hex[:8]}"


def _safe_column_names(columns) -> list[str]:
    """Normalize CSV column names and make them unique."""

    safe_names = []
    used_names = set()

    for index, column in enumerate(columns, start=1):
        name = str(column).strip().lower()
        name = re.sub(r"[^a-z0-9_]+", "_", name).strip("_")
        name = name or f"column_{index}"

        if name[0].isdigit():
            name = f"col_{name}"

        base_name = name[:50]
        name = base_name
        suffix = 2

        while name in used_names:
            ending = f"_{suffix}"
            name = f"{base_name[:63 - len(ending)]}{ending}"
            suffix += 1

        used_names.add(name)
        safe_names.append(name)

    return safe_names


def _postgres_type(series: pd.Series) -> str:
    """Choose a conservative PostgreSQL type for a CSV column."""

    if pd.api.types.is_bool_dtype(series.dtype):
        return "BOOLEAN"

    if pd.api.types.is_integer_dtype(series.dtype):
        return "BIGINT"

    if pd.api.types.is_float_dtype(series.dtype):
        return "DOUBLE PRECISION"

    return "TEXT"


def store_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
    is_visible: bool = True,
) -> dict:
    """Store a DataFrame in a new PostgreSQL table."""

    if dataframe.empty or len(dataframe.columns) == 0:
        raise ValueError("The CSV must contain columns and at least one row.")

    if len(dataframe.columns) > 200:
        raise ValueError("The CSV cannot contain more than 200 columns.")

    if len(dataframe) > 100_000:
        raise ValueError("The CSV cannot contain more than 100,000 rows.")

    table_name = _safe_table_name(filename)
    column_names = _safe_column_names(dataframe.columns)
    dataframe = dataframe.copy()
    dataframe.columns = column_names

    column_types = [
        _postgres_type(dataframe[column])
        for column in column_names
    ]

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            column_definitions = [
                sql.SQL("{} {}").format(
                    sql.Identifier(column),
                    sql.SQL(column_type),
                )
                for column, column_type in zip(
                    column_names,
                    column_types,
                )
            ]

            create_query = sql.SQL(
                "CREATE TABLE {} ({})"
            ).format(
                sql.Identifier("public", table_name),
                sql.SQL(", ").join(column_definitions),
            )

            cursor.execute(create_query)

            insert_query = sql.SQL(
                "INSERT INTO {} ({}) VALUES ({})"
            ).format(
                sql.Identifier("public", table_name),
                sql.SQL(", ").join(
                    sql.Identifier(column)
                    for column in column_names
                ),
                sql.SQL(", ").join(
                    sql.Placeholder() for _ in column_names
                ),
            )

            rows = [
                tuple(
                    None if pd.isna(value) else value
                    for value in row
                )
                for row in dataframe.itertuples(
                    index=False,
                    name=None,
                )
            ]

            
            cursor.executemany(insert_query, rows)

            
            # Register the dataset in the same database transaction.
            cursor.execute(
                """
                INSERT INTO public.dataset_registry (
                    table_name,
                    original_filename,
                    row_count,
                    column_count,
                    columns,
                    is_visible
                )
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    table_name,
                    filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
                    len(dataframe),
                    len(column_names),
                    json.dumps(column_names),
                    is_visible,
                ),
            )


        connection.commit()

        return {

            "table_name": table_name,
            "schema": "public",
            "row_count": len(dataframe),
            "column_count": len(column_names),
            "columns": column_names,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
