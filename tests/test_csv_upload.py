
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_valid_csv():
    csv_content = (
        "name,age,city\n"
        "Aman,21,Satna\n"
        "Riya,,Rewa\n"
        "Aman,21,Satna\n"
        "Karan,22,Jabalpur\n"
    )

    response = client.post(
        "/upload-csv",
        files={
            "file": (
                "students.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "students.csv"
    assert data["row_count"] == 4
    assert data["column_count"] == 3
    assert data["missing_values"]["age"] == 1
    assert data["duplicate_rows"] == 1


def test_upload_invalid_extension():
    response = client.post(
        "/upload-csv",
        files={
            "file": (
                "notes.txt",
                "This is not a CSV file.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a CSV file."


def test_upload_empty_csv():
    response = client.post(
        "/upload-csv",
        files={
            "file": (
                "empty.csv",
                "",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400


def test_upload_oversized_csv():
    large_content = b"name,age,city\n" + (
        b"Aman,21,Satna\n" * (400_000)
    )

    response = client.post(
        "/upload-csv",
        files={
            "file": (
                "large.csv",
                large_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "File too large. Maximum upload size is 5 MB."
    )


def test_clean_csv_download():
    csv_content = (
        "name,age,city\n"
        "Aman,20,Satna\n"
        "Riya,,Rewa\n"
        "Aman,20,Satna\n"
        "Karan,40,Satna\n"
    )

    response = client.post(
        "/clean-csv",
        files={
            "file": (
                "students.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="cleaned_students.csv"' in (
        response.headers["content-disposition"]
    )

    cleaned_csv = response.text

    assert "Aman,20.0,Satna" in cleaned_csv
    assert cleaned_csv.count("Aman,20.0,Satna") == 1
    assert "Riya,30.0,Rewa" in cleaned_csv


def test_clean_csv_rejects_oversized_file():
    large_content = b"name,age,city\n" + (
        b"Aman,21,Satna\n" * 400_000
    )

    response = client.post(
        "/clean-csv",
        files={
            "file": (
                "large.csv",
                large_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "File too large. Maximum upload size is 5 MB."
    )


def test_clean_csv_rejects_invalid_extension():
    response = client.post(
        "/clean-csv",
        files={
            "file": (
                "notes.txt",
                "This is not a CSV file.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a CSV file."


def test_clean_csv_rejects_empty_csv():
    response = client.post(
        "/clean-csv",
        files={
            "file": (
                "empty.csv",
                "",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400


def test_cleaning_summary_endpoint():
    csv_content = (
        "name,age,city\n"
        "Aman,20,Satna\n"
        "Riya,,Rewa\n"
        "Aman,20,Satna\n"
        "Karan,40,Satna\n"
    )

    response = client.post(
        "/cleaning-summary",
        files={
            "file": (
                "students.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "students.csv"
    assert data["before_cleaning"]["row_count"] == 4
    assert data["before_cleaning"]["duplicate_rows"] == 1
    assert data["before_cleaning"]["missing_values"] == 1

    assert data["after_cleaning"]["row_count"] == 3
    assert data["after_cleaning"]["duplicate_rows"] == 0
    assert data["after_cleaning"]["missing_values"] == 0

    assert data["rows_removed"] == 1
    assert data["duplicates_removed"] == 1
    assert data["missing_values_filled"] == 1
