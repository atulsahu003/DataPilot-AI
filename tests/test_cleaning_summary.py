
import pandas as pd

from app.services.cleaning_summary import generate_cleaning_summary


def test_generate_cleaning_summary():
    df = pd.DataFrame({
        "name": ["Aman", "Riya", "Aman", "Karan"],
        "age": [20.0, None, 20.0, 40.0],
        "city": ["Satna", "Rewa", "Satna", "Satna"],
    })

    summary = generate_cleaning_summary(df)

    assert summary["before_cleaning"]["row_count"] == 4
    assert summary["before_cleaning"]["column_count"] == 3
    assert summary["before_cleaning"]["duplicate_rows"] == 1
    assert summary["before_cleaning"]["missing_values"] == 1

    assert summary["after_cleaning"]["row_count"] == 3
    assert summary["after_cleaning"]["column_count"] == 3
    assert summary["after_cleaning"]["duplicate_rows"] == 0
    assert summary["after_cleaning"]["missing_values"] == 0

    assert summary["rows_removed"] == 1
    assert summary["duplicates_removed"] == 1
    assert summary["missing_values_filled"] == 1

    # The original DataFrame should remain unchanged.
    assert len(df) == 4
    assert df["age"].isna().sum() == 1
