
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_validate_csv_detects_invalid_ages():
    csv_content = (
        "name,age\n"
        "Aman,21\n"
        "Riya,-5\n"
        "Karan,125\n"
        "Neha,30\n"
    )

    response = client.post(
        "/validate-csv",
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

    assert data["valid"] is False
    assert data["issue_count"] == 2
    assert data["issues"][0]["value"] == "-5"
    assert data["issues"][1]["value"] == "125"


def test_validate_csv_accepts_valid_ages():
    csv_content = (
        "name,age\n"
        "Aman,21\n"
        "Riya,30\n"
    )

    response = client.post(
        "/validate-csv",
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

    assert data["valid"] is True
    assert data["issue_count"] == 0
    assert data["issues"] == []


def test_validate_csv_rejects_invalid_extension():
    response = client.post(
        "/validate-csv",
        files={
            "file": (
                "students.txt",
                "name,age\nAman,21\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
