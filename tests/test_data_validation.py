
import pandas as pd

from app.services.data_validation import validate_dataframe


def test_validate_dataframe_detects_invalid_ages():
    df = pd.DataFrame({
        "name": ["Aman", "Riya", "Karan", "Neha"],
        "age": [21, -5, 125, 30],
    })

    original_df = df.copy(deep=True)

    result = validate_dataframe(df)

    assert result["valid"] is False
    assert result["issue_count"] == 2

    assert result["issues"][0]["value"] == "-5"
    assert result["issues"][0]["issue"] == (
        "Age cannot be negative."
    )

    assert result["issues"][1]["value"] == "125"
    assert result["issues"][1]["issue"] == (
        "Age exceeds 120 and should be reviewed."
    )

    # Validation must not modify the original dataset.
    pd.testing.assert_frame_equal(df, original_df)


def test_validate_dataframe_accepts_normal_ages():
    df = pd.DataFrame({
        "name": ["Aman", "Riya"],
        "age": [21, 30],
    })

    result = validate_dataframe(df)

    assert result["valid"] is True
    assert result["issue_count"] == 0
    assert result["issues"] == []


def test_validate_dataframe_without_age_column():
    df = pd.DataFrame({
        "name": ["Aman", "Riya"],
        "city": ["Satna", "Rewa"],
    })

    result = validate_dataframe(df)

    assert result["valid"] is True
    assert result["issue_count"] == 0
    assert result["issues"] == []



def test_validate_dataframe_handles_missing_and_text_ages():
    df = pd.DataFrame({
        "name": ["Aman", "Riya", "Karan"],
        "age": [None, "unknown", 25],
    })

    result = validate_dataframe(df)

    assert result["valid"] is False
    assert result["issue_count"] == 2

    assert result["issues"][0]["issue"] == "Age is missing."
    assert result["issues"][1]["issue"] == (
        "Age must be a numeric value."
    )
