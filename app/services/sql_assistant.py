
import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.database.connection import get_db_connection
from langchain_google_genai.chat_models import GoogleAPIError

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"
MAX_RESULT_ROWS = 100


def get_table_schema() -> list[dict]:
    """Return user-table names and column metadata from public schema."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name LIKE 'csv\\_%' ESCAPE '\\'
                ORDER BY table_name, ordinal_position;
                """
            )
            rows = cursor.fetchall()

        tables = {}

        for table_name, column_name, data_type in rows:
            tables.setdefault(table_name, []).append(
                {
                    "name": column_name,
                    "type": data_type,
                }
            )

        return [
            {"table_name": name, "columns": columns}
            for name, columns in tables.items()
        ]

    finally:
        connection.close()

def generate_fallback_sql(question: str, schema: list[dict]) -> str:
    """Generate safe SQL for a few recognized analytics questions."""
    normalized_question = question.lower().strip()

    for table in schema:
        columns = {
    column["name"].lower() if isinstance(column, dict) else column.lower()
    for column in table["columns"]
}
        table_name = table["table_name"]

        # Sales analysis: total sales by city
        if (
            {"city", "quantity", "unit_price"}.issubset(columns)
            and any(word in normalized_question for word in ["sales", "revenue"])
            and "city" in normalized_question
            and any(word in normalized_question for word in ["by", "each", "per", "city"])
        ):
            return (
                f'SELECT city, SUM(quantity * unit_price) AS total_sales ' 
                f'FROM public."{table_name}" '
                f'GROUP BY city ORDER BY total_sales DESC LIMIT 100'
            )
                # Count total records in a recognized table
        if (
            "count" in normalized_question
            or "number of records" in normalized_question
            or "total records" in normalized_question
            or "how many records" in normalized_question
        ):
            return f'SELECT COUNT(*) AS total_records FROM public."{table_name}"'

                # Calculate average age when the age column is available
        if (
            "age" in columns
            and "average age" in normalized_question
        ):
            return (
                f'SELECT AVG(age) AS average_age '
                f'FROM public."{table_name}"'
            )

            # Find the maximum age when the age column is available
        if (
            "age" in columns
            and "maximum age" in normalized_question
        ):
            return (
                f'SELECT MAX(age) AS maximum_age '
                f'FROM public."{table_name}"'
            )

        # Find the minimum age when the age column is available
        if (
            "age" in columns
            and "minimum age" in normalized_question
        ):
            return (
                f'SELECT MIN(age) AS minimum_age '
                f'FROM public."{table_name}"'
            )

        # Show the available rows for a recognized table question
        if (
            "show all" in normalized_question
            or "show records" in normalized_question
            or "show data" in normalized_question
        ):
            return f'SELECT * FROM public."{table_name}" LIMIT 100'

    raise ValueError(
        "Gemini is unavailable, and this question is not supported by the SQL fallback. Please try again later."
    )


def generate_sql(question: str, schema: list[dict]) -> str:
    """Ask Gemini to generate one read-only PostgreSQL SELECT query."""
    # Use local fallback for recognized simple questions first.
    try:
        return generate_fallback_sql(question, schema)
    except ValueError:
        pass

    if not settings.google_api_key.strip():
        raise ValueError("Google API key is not configured.")

    
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=settings.google_api_key,
        temperature=0,
        timeout=30,
        max_retries=0,
    )


    
    prompt = f"""
Generate one read-only PostgreSQL SELECT query for this analytics question.

Question: {question}

Schema: {schema}

Rules:
- Use only the listed tables and columns.
- Use fully qualified public table names.
- Return exactly one SELECT query, without Markdown or explanation.
- Never modify data or schema.
- Do not use SELECT INTO, locking clauses, or system catalogs.
- Limit results to {MAX_RESULT_ROWS} rows.
- If the question cannot be answered from the schema, return:
  SELECT 1 WHERE FALSE
"""


    
    try:
        response = model.invoke(prompt)
    except GoogleAPIError as exc:
        logger.warning(
            "Gemini API request failed (%s). Trying SQL fallback.",
            type(exc).__name__,
        )
        return generate_fallback_sql(question, schema)

    content = response.content

    if isinstance(content, str):
        sql_text = content.strip()
    elif isinstance(content, list):
        sql_text = "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ).strip()
    else:
        raise ValueError("Gemini returned an unsupported response format.")

    # Remove an optional Markdown code fence.
    sql_text = re.sub(r"^```(?:sql)?\s*", "", sql_text, flags=re.IGNORECASE)
    sql_text = re.sub(r"\s*```$", "", sql_text).strip()

    if not sql_text:
        raise ValueError("Gemini returned an empty SQL query.")

    return sql_text


from sqlglot import exp, parse
from sqlglot.errors import ParseError


def validate_sql(query: str, allowed_tables: set[str]) -> str:
    """Validate a single read-only PostgreSQL SELECT query."""

    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    if len(query) > 10_000:
        raise ValueError("SQL query is too long.")

    try:
        statements = parse(query, read="postgres")
    except ParseError as exc:
        raise ValueError("Invalid SQL syntax.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    statement = statements[0]

    if not isinstance(statement, exp.Query):
        raise ValueError("Only read-only SELECT queries are allowed.")

    # Reject SELECT INTO and locking clauses.
    if statement.find(exp.Into) is not None:
        raise ValueError("SELECT INTO is not allowed.")

    if statement.find(exp.Lock) is not None:
        raise ValueError("Locking clauses are not allowed.")

    # Only allow tables explicitly discovered from the uploaded CSV tables.
    for table in statement.find_all(exp.Table):
        if (
            table.db.lower() != "public"
            or table.catalog
            or table.name.lower() not in allowed_tables
        ):
            raise ValueError(
                f"Table is not allowed: {table.sql(dialect='postgres')}"
            )

    # Add a conservative upper bound to the outer query.
    if statement.args.get("limit") is None:
        statement = statement.limit(MAX_RESULT_ROWS)

    return statement.sql(dialect="postgres")


def execute_sql(
    query: str,
    allowed_tables: set[str],
) -> dict:
    """Execute a validated SELECT query in a read-only transaction."""

    validated_query = validate_sql(query, allowed_tables)
    connection = get_db_connection()

    try:
        connection.set_session(readonly=True, autocommit=False)

        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5000ms'")
            cursor.execute(validated_query)

            if cursor.description is None:
                raise ValueError("The query did not return tabular results.")

            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchmany(MAX_RESULT_ROWS)

            return {
                "columns": columns,
                "rows": [
                    [
                        value.isoformat() if hasattr(value, "isoformat") else value
                        for value in row
                    ]
                    for row in rows
                ],
                "row_count": len(rows),
            }

    finally:
        connection.rollback()
        connection.close()
