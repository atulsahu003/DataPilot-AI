
import pandas as pd

from app.services.data_cleaning import clean_dataframe


def generate_cleaning_summary(df: pd.DataFrame) -> dict:
    """
    Compare a DataFrame before and after cleaning.
    """

    # Profile the original dataset.
    original_rows = len(df)
    original_columns = len(df.columns)
    original_duplicates = int(df.duplicated().sum())
    original_missing = int(df.isnull().sum().sum())

    # Clean the dataset.
    cleaned_df = clean_dataframe(df)

    # Profile the cleaned dataset.
    cleaned_rows = len(cleaned_df)
    cleaned_columns = len(cleaned_df.columns)
    cleaned_duplicates = int(cleaned_df.duplicated().sum())
    cleaned_missing = int(cleaned_df.isnull().sum().sum())

    return {
        "before_cleaning": {
            "row_count": original_rows,
            "column_count": original_columns,
            "duplicate_rows": original_duplicates,
            "missing_values": original_missing,
        },
        "after_cleaning": {
            "row_count": cleaned_rows,
            "column_count": cleaned_columns,
            "duplicate_rows": cleaned_duplicates,
            "missing_values": cleaned_missing,
        },
        "rows_removed": original_rows - cleaned_rows,
        "duplicates_removed": original_duplicates - cleaned_duplicates,
        "missing_values_filled": original_missing - cleaned_missing,
    }
