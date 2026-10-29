
import pandas as pd
import pytest

from app.services.eda import generate_eda_summary


def test_generate_eda_summary():
    df = pd.DataFrame({
        "age": [20, 30, 40],
        "salary": [20000, 30000, 40000],
        "city": ["Satna", "Bhopal", "Satna"],
    })

    result = generate_eda_summary(df)

    assert result["row_count"] == 3
    assert result["column_count"] == 3

    assert result["numerical_summary"]["age"]["mean"] == 30.0
    assert result["numerical_summary"]["age"]["median"] == 30.0

    assert result["missing_values"]["age"] == 0

    assert result["categorical_summary"]["city"]["Satna"] == 2

    assert result["correlation_matrix"]["age"]["salary"] == pytest.approx(1.0)


def test_generate_eda_summary_with_missing_values():
    df = pd.DataFrame({
        "age": [20, None, 40],
        "city": ["Satna", None, "Bhopal"],
    })

    result = generate_eda_summary(df)

    assert result["missing_values"]["age"] == 1
    assert result["missing_values"]["city"] == 1


def test_generate_eda_summary_rejects_empty_dataframe():
    df = pd.DataFrame()

    with pytest.raises(ValueError, match="empty dataset"):
        generate_eda_summary(df)


def test_generate_eda_summary_with_mixed_numeric_and_text_values():
    df = pd.DataFrame({
        "age": [20, "unknown", 40],
        "city": ["Satna", "Bhopal", "Satna"],
    })

    result = generate_eda_summary(df)

    assert result["row_count"] == 3
    assert result["column_count"] == 2

    # Valid numeric values should be analyzed.
    assert result["numerical_summary"]["age"]["mean"] == 30.0
    assert result["numerical_summary"]["age"]["median"] == 30.0
    assert result["numerical_summary"]["age"]["minimum"] == 20.0
    assert result["numerical_summary"]["age"]["maximum"] == 40.0

    # Invalid text values should be reported separately.
    assert result["invalid_values"]["age"]["unknown"] == 1

    # Genuine categorical columns should remain categorical.
    assert "age" not in result["categorical_summary"]
    assert result["categorical_summary"]["city"]["Satna"] == 2

    # Missing-value counts should remain unchanged.
    assert result["missing_values"]["age"] == 0
    assert result["missing_values"]["city"] == 0


def test_smart_eda_separates_missing_and_invalid_values():
    df = pd.DataFrame({
        "age": [20, "unknown", None, 40],
        "city": ["Satna", "Bhopal", "Satna", "Indore"],
    })

    result = generate_eda_summary(df)

    # Valid numbers only are used for numerical statistics.
    assert result["numerical_summary"]["age"]["mean"] == 30.0

    # Original missing values are counted separately.
    assert result["missing_values"]["age"] == 1

    # Invalid non-missing text is reported separately.
    assert result["invalid_values"]["age"] == {"unknown": 1}

    # Categorical data remains intact.
    assert result["categorical_summary"]["city"]["Satna"] == 2
