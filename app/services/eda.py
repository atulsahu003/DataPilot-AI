
import pandas as pd


def generate_eda_summary(df: pd.DataFrame) -> dict:
    """
    Generate an Exploratory Data Analysis (EDA) summary.

    Mixed numeric/text columns are analyzed numerically when
    they contain at least one valid number. Invalid text values
    are reported separately.
    """

    if df.empty:
        raise ValueError("Cannot perform EDA on an empty dataset.")

    summary = {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
    }

    # 1. Identify numeric and mixed-type columns.
    numerical_summary = {}
    categorical_summary = {}
    invalid_values = {}
    numeric_columns = {}

    for column in df.columns:
        series = df[column]

        # Convert values to numbers where possible.
        converted = pd.to_numeric(series, errors="coerce")

        # Only treat a non-numeric dtype as a numeric candidate
        # if it contains at least one actual numeric value.
        is_originally_numeric = pd.api.types.is_numeric_dtype(
            series
        )
        has_numeric_values = converted.notna().any()

        if is_originally_numeric or has_numeric_values:
            numeric_columns[column] = converted

            valid_values = converted.dropna()

            numerical_summary[str(column)] = {
                "mean": (
                    float(valid_values.mean())
                    if not valid_values.empty else None
                ),
                "median": (
                    float(valid_values.median())
                    if not valid_values.empty else None
                ),
                "standard_deviation": (
                    float(valid_values.std())
                    if not valid_values.empty else None
                ),
                "minimum": (
                    float(valid_values.min())
                    if not valid_values.empty else None
                ),
                "maximum": (
                    float(valid_values.max())
                    if not valid_values.empty else None
                ),
            }

            # Report non-empty values that could not be converted.
            invalid_mask = series.notna() & converted.isna()

            if invalid_mask.any():
                invalid_values[str(column)] = {
                    str(value): int(count)
                    for value, count in (
                        series[invalid_mask]
                        .value_counts(dropna=False)
                        .items()
                    )
                }

        else:
            # Keep genuinely categorical columns categorical.
            frequencies = (
                series.value_counts(dropna=False).head(10)
            )

            categorical_summary[str(column)] = {
                str(value): int(count)
                for value, count in frequencies.items()
            }

    summary["numerical_summary"] = numerical_summary
    summary["categorical_summary"] = categorical_summary
    summary["invalid_values"] = invalid_values

    # 2. Missing values in the original dataset.
    summary["missing_values"] = {
        str(column): int(count)
        for column, count in df.isnull().sum().items()
    }

    # 3. Correlation matrix using numeric-convertible columns.
    numeric_df = pd.DataFrame(numeric_columns, index=df.index)
    correlation_df = numeric_df.corr()

    summary["correlation_matrix"] = {
        str(column): {
            str(other_column): (
                float(value) if pd.notna(value) else None
            )
            for other_column, value in row.items()
        }
        for column, row in correlation_df.iterrows()
    }

    return summary
