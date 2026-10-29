
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_eda_endpoint_returns_summary():
    csv_content = (
        "age,salary,city\n"
        "20,20000,Satna\n"
        "30,30000,Bhopal\n"
        "40,40000,Satna\n"
    )

    response = client.post(
        "/eda",
        files={
            "file": (
                "sample.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["filename"] == "sample.csv"
    assert result["row_count"] == 3
    assert result["column_count"] == 3
    assert result["numerical_summary"]["age"]["mean"] == 30.0
    assert result["categorical_summary"]["city"]["Satna"] == 2
    assert result["message"] == "EDA summary generated successfully."


def test_eda_endpoint_rejects_invalid_extension():
    response = client.post(
        "/eda",
        files={
            "file": (
                "sample.txt",
                "age\n20\n30\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are allowed."


def test_eda_endpoint_rejects_empty_file():
    response = client.post(
        "/eda",
        files={
            "file": (
                "empty.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded CSV file is empty."


def test_eda_endpoint_rejects_csv_with_headers_only():
    csv_content = "age,salary,city\n"

    response = client.post(
        "/eda",
        files={
            "file": (
                "headers_only.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
