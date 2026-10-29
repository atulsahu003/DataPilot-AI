
import pandas as pd

from app.services.data_cleaning import clean_dataframe


def test_clean_dataframe_removes_duplicates():
    df = pd.DataFrame({
        "name": ["Aman", "Riya", "Aman"],
        "age": [21, 22, 21],
    })

    cleaned_df = clean_dataframe(df)

    assert len(cleaned_df) == 2
    assert cleaned_df.duplicated().sum() == 0
    assert len(df) == 3


def test_clean_dataframe_fills_missing_values():
    df = pd.DataFrame({
        "age": [20.0, None, 40.0],
        "city": ["Satna", None, "Satna"],
    })

    cleaned_df = clean_dataframe(df)

    # Numeric missing value should be filled with median.
    assert cleaned_df.loc[1, "age"] == 30.0

    # Text missing value should be filled with mode.
    assert cleaned_df.loc[1, "city"] == "Satna"

    # Original DataFrame should remain unchanged.
    assert pd.isna(df.loc[1, "age"])
    assert pd.isna(df.loc[1, "city"])


def test_clean_dataframe_preserves_all_missing_column():
    df = pd.DataFrame({
        "age": [20.0, None, 40.0],
        "unknown": [None, None, None],
    })

    cleaned_df = clean_dataframe(df)

    # The numeric missing value should be filled with the median.
    assert cleaned_df.loc[1, "age"] == 30.0

    # A column with all values missing should remain unchanged.
    assert cleaned_df["unknown"].isna().all()

    # The original DataFrame should remain unchanged.
    assert df["age"].isna().sum() == 1
    assert df["unknown"].isna().all()


def test_clean_dataframe_removes_duplicates_and_fills_missing_values():
    df = pd.DataFrame({
        "name": ["Aman", "Riya", "Aman", "Karan"],
        "age": [21.0, None, 21.0, 22.0],
        "city": ["Satna", "Rewa", "Satna", "Jabalpur"],
    })

    cleaned_df = clean_dataframe(df)

    assert len(cleaned_df) == 3
    assert cleaned_df.duplicated().sum() == 0
    assert cleaned_df.isna().sum().sum() == 0
    assert cleaned_df.loc[
        cleaned_df["name"] == "Riya", "age"
    ].iloc[0] == 21.5

    # The source DataFrame must remain unchanged.
    assert len(df) == 4
    assert pd.isna(df.loc[1, "age"])
