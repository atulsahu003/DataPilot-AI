
import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a DataFrame by removing duplicate rows
    and handling missing values.
    """

    # Work on a copy to preserve the original DataFrame.
    cleaned_df = df.copy()

    # Step 1: Remove duplicate rows.
    cleaned_df = cleaned_df.drop_duplicates()

    # Step 2: Handle missing values in each column.
    for column in cleaned_df.columns:

        # Skip columns that have no missing values.
        if not cleaned_df[column].isnull().any():
            continue

        # Numeric columns: fill missing values with median.
        if pd.api.types.is_numeric_dtype(cleaned_df[column]):
            median_value = cleaned_df[column].median()

            # If every value is missing, leave it unchanged.
            if pd.notna(median_value):
                cleaned_df[column] = cleaned_df[column].fillna(
                    median_value
                )

        # Text and categorical columns: fill with mode.
        else:
            mode_values = cleaned_df[column].mode(dropna=True)

            # If a valid mode exists, use the most frequent value.
            if not mode_values.empty:
                cleaned_df[column] = cleaned_df[column].fillna(
                    mode_values.iloc[0]
                )

    return cleaned_df
