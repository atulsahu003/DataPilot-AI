
import pytest
from unittest.mock import MagicMock, patch

from langchain_google_genai.chat_models import GoogleAPIError

from app.services.sql_assistant import (
    validate_sql,
    execute_sql,
    generate_sql,
    generate_fallback_sql,
)


ALLOWED_TABLES = {"csv_sample_sales_6fa668f7"}


def test_allows_select_from_authorized_table():
    query = """
        SELECT city, quantity
        FROM public.csv_sample_sales_6fa668f7
    """

    result = validate_sql(query, ALLOWED_TABLES)

    assert "SELECT" in result.upper()
    assert "LIMIT 100" in result.upper()


def test_rejects_delete_query():
    with pytest.raises(ValueError):
        validate_sql(
            "DELETE FROM public.csv_sample_sales_6fa668f7",
            ALLOWED_TABLES,
        )


def test_rejects_update_query():
    with pytest.raises(ValueError):
        validate_sql(
            "UPDATE public.csv_sample_sales_6fa668f7 SET quantity = 0",
            ALLOWED_TABLES,
        )


def test_rejects_drop_query():
    with pytest.raises(ValueError):
        validate_sql(
            "DROP TABLE public.csv_sample_sales_6fa668f7",
            ALLOWED_TABLES,
        )


def test_rejects_multiple_statements():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT 1; SELECT 2",
            ALLOWED_TABLES,
        )


def test_rejects_unauthorized_table():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT * FROM public.customers",
            ALLOWED_TABLES,
        )


def test_rejects_unauthorized_schema():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT * FROM private.csv_sample_sales_6fa668f7",
            ALLOWED_TABLES,
        )


def test_rejects_select_into():
    with pytest.raises(ValueError):
        validate_sql(
            """
            SELECT *
            INTO public.new_table
            FROM public.csv_sample_sales_6fa668f7
            """,
            ALLOWED_TABLES,
        )


def test_rejects_locking_query():
    with pytest.raises(ValueError):
        validate_sql(
            "SELECT * FROM public.csv_sample_sales_6fa668f7 FOR UPDATE",
            ALLOWED_TABLES,
        )


def test_rejects_empty_query():
    with pytest.raises(ValueError):
        validate_sql("", ALLOWED_TABLES)


def test_adds_limit_to_unlimited_query():
    result = validate_sql(
        "SELECT city FROM public.csv_sample_sales_6fa668f7",
        ALLOWED_TABLES,
    )

    assert "LIMIT 100" in result.upper()


def test_preserves_existing_limit():
    result = validate_sql(
        "SELECT city FROM public.csv_sample_sales_6fa668f7 LIMIT 5",
        ALLOWED_TABLES,
    )

    assert "LIMIT 5" in result.upper()


def test_execute_sql_returns_columns_and_rows():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_cursor.description = [
        ("city",),
        ("total_sales",),
    ]
    mock_cursor.fetchmany.return_value = [
        ("Satna", 114000),
        ("Bhopal", 2500),
    ]

    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with (
        patch(
            "app.services.sql_assistant.validate_sql",
            return_value=(
                "SELECT city, total_sales "
                "FROM public.csv_sales LIMIT 100"
            ),
        ),
        patch(
            "app.services.sql_assistant.get_db_connection",
            return_value=mock_connection,
        ),
    ):
        result = execute_sql(
            "SELECT city, total_sales FROM public.csv_sales",
            {"csv_sales"},
        )

    assert result["columns"] == ["city", "total_sales"]
    assert result["rows"] == [
        ["Satna", 114000],
        ["Bhopal", 2500],
    ]
    assert result["row_count"] == 2

    mock_connection.set_session.assert_called_once_with(
        readonly=True,
        autocommit=False,
    )
    mock_connection.rollback.assert_called_once()
    mock_connection.close.assert_called_once()


def test_execute_sql_rejects_query_before_connecting():
    with (
        patch(
            "app.services.sql_assistant.validate_sql",
            side_effect=ValueError("Only SELECT queries are allowed."),
        ),
        patch("app.services.sql_assistant.get_db_connection") as mock_connect,
    ):
        with pytest.raises(ValueError):
            execute_sql(
                "DELETE FROM public.csv_sales",
                {"csv_sales"},
            )

    mock_connect.assert_not_called()


def test_generate_sql_handles_gemini_api_error():
    mock_model = MagicMock()
    mock_model.invoke.side_effect = GoogleAPIError(
        "Gemini request timed out",
        {"error": "deadline exceeded"},
    )
    with patch(
        "app.services.sql_assistant.ChatGoogleGenerativeAI",
        return_value=mock_model,
    ):
        
        result = generate_sql(
            "Show total sales by city",
            [
                {
                    "table_name": "csv_sample_sales_6fa668f7",
                    "columns": [
                        "city",
                        "quantity",
                        "unit_price",
                    ],
                }
            ],
        )

        assert "SUM(quantity * unit_price)" in result
        assert "GROUP BY city" in result
        assert "csv_sample_sales_6fa668f7" in result


def test_fallback_generates_sales_query_for_matching_table():
    schema = [
        {
            "table_name": "csv_sample_sales_6fa668f7",
            "columns": ["product", "category", "quantity", "unit_price", "city"],
        },
        {
            "table_name": "csv_test_26b4ea71_a6f3d98e",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Show total sales by city", schema)

    assert "SUM(quantity * unit_price)" in query
    assert 'public."csv_sample_sales_6fa668f7"' in query
    assert "GROUP BY city" in query


def test_fallback_rejects_unsupported_question():
    schema = [
        {
            "table_name": "csv_sample_sales_6fa668f7",
            "columns": ["product", "category", "quantity", "unit_price", "city"],
        },
    ]

    with pytest.raises(ValueError, match="not supported by the SQL fallback"):
        generate_fallback_sql("Explain quantum physics", schema)


def test_fallback_generates_show_all_query_for_selected_schema():
    schema = [
        {
            "table_name": "csv_students_12345678",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Show all records", schema)

    assert 'SELECT * FROM public."csv_students_12345678"' in query
    assert "LIMIT 100" in query

def test_fallback_generates_count_records_query():
    schema = [
        {
            "table_name": "csv_students_12345678",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Count total records", schema)

    assert "COUNT(*) AS total_records" in query
    assert 'FROM public."csv_students_12345678"' in query

def test_fallback_generates_average_age_query():
    schema = [
        {
            "table_name": "csv_students_12345678",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Show average age", schema)

    assert "AVG(age) AS average_age" in query
    assert 'FROM public."csv_students_12345678"' in query

def test_fallback_generates_maximum_age_query():
    schema = [
        {
            "table_name": "csv_students_12345678",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Show maximum age", schema)

    assert "MAX(age) AS maximum_age" in query
    assert 'FROM public."csv_students_12345678"' in query

def test_fallback_generates_minimum_age_query():
    schema = [
        {
            "table_name": "csv_students_12345678",
            "columns": ["name", "age", "city"],
        },
    ]

    query = generate_fallback_sql("Show minimum age", schema)

    assert "MIN(age) AS minimum_age" in query
    assert 'FROM public."csv_students_12345678"' in query

