
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)



def test_list_datasets_returns_dataset_metadata():
    datasets = [
        {
            "table_name": "csv_sample_sales_12345678",
            "original_filename": "sales.csv",
            "row_count": 10,
            "column_count": 2,
            "columns": [
                {"name": "city", "type": "text"},
                {"name": "quantity", "type": "bigint"},
            ],
        }
    ]

    with patch(
        "app.main.list_registered_datasets",
        return_value=datasets,
    ):
        response = client.get("/datasets")

    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 1
    assert data["datasets"][0]["table_name"] == "csv_sample_sales_12345678"
    assert data["datasets"][0]["original_filename"] == "sales.csv"
    assert data["datasets"][0]["column_count"] == 2
    assert data["datasets"][0]["row_count"] == 10



def test_query_data_rejects_unknown_dataset():
    schema = [
        {
            "table_name": "csv_sample_sales_12345678",
            "columns": [
                {"name": "city", "type": "text"},
            ],
        }
    ]

    with patch("app.main.get_table_schema", return_value=schema):
        response = client.post(
            "/query-data",
            json={
                "question": "Show all sales",
                "dataset_name": "csv_does_not_exist",
            },
        )

    assert response.status_code == 400
    assert "Selected dataset was not found" in response.json()["detail"]


def test_query_data_uses_only_selected_dataset():
    schema = [
        {
            "table_name": "csv_sales_12345678",
            "columns": [
                {"name": "city", "type": "text"},
            ],
        },
        {
            "table_name": "csv_customers_87654321",
            "columns": [
                {"name": "name", "type": "text"},
            ],
        },
    ]

    generated_sql = 'SELECT city FROM public."csv_sales_12345678" LIMIT 100'
    query_result = {
        "columns": ["city"],
        "rows": [["Satna"]],
        "row_count": 1,
    }

    with (
        patch("app.main.get_table_schema", return_value=schema),
                patch(
            "app.main.list_registered_datasets",
            return_value=[
                {
                    "table_name": "csv_sales_12345678",
                    "original_filename": "sales.csv",
                    "row_count": 10,
                    "column_count": 1,
                    "columns": [{"name": "city", "type": "text"}],
                },
                {
                    "table_name": "csv_customers_87654321",
                    "original_filename": "customers.csv",
                    "row_count": 5,
                    "column_count": 1,
                    "columns": [{"name": "name", "type": "text"}],
                },
            ],
        ),
        patch("app.main.generate_sql", return_value=generated_sql) as mock_generate,
        patch("app.main.validate_sql", return_value=generated_sql) as mock_validate,
        patch("app.main.execute_sql", return_value=query_result) as mock_execute,
    ):
        response = client.post(
            "/query-data",
            json={
                "question": "Show sales by city",
                "dataset_name": "csv_sales_12345678",
            },
        )

    assert response.status_code == 200
    assert response.json()["dataset_name"] == "csv_sales_12345678"
    assert response.json()["rows"] == [["Satna"]]

    mock_generate.assert_called_once_with(
        "Show sales by city",
        [schema[0]],
    )
    mock_validate.assert_called_once_with(
        generated_sql,
        {"csv_sales_12345678"},
    )
    mock_execute.assert_called_once_with(
        generated_sql,
        {"csv_sales_12345678"},
    )


def test_query_data_rejects_sql_referencing_another_dataset():
    schema = [
        {
            "table_name": "csv_sales_12345678",
            "columns": [
                {"name": "city", "type": "text"},
            ],
        }
    ]

    generated_sql = 'SELECT name FROM public."csv_customers_87654321" LIMIT 100'

    with (
        patch("app.main.get_table_schema", return_value=schema),
                patch(
            "app.main.list_registered_datasets",
            return_value=[
                {
                    "table_name": "csv_sales_12345678",
                    "original_filename": "sales.csv",
                    "row_count": 10,
                    "column_count": 1,
                    "columns": [{"name": "city", "type": "text"}],
                },
            ],
        ),
        patch("app.main.generate_sql", return_value=generated_sql),
        patch("app.main.validate_sql", return_value=generated_sql),
        patch("app.main.execute_sql") as mock_execute,
    ):
        response = client.post(
            "/query-data",
            json={
                "question": "Show all customers",
                "dataset_name": "csv_sales_12345678",
            },
        )

    assert response.status_code == 400
    assert "only the selected dataset" in response.json()["detail"]
    mock_execute.assert_not_called()
