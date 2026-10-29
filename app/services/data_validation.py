
import pandas as pd


def validate_dataframe(df: pd.DataFrame) -> dict:
    """
    Validate a DataFrame and report suspicious age values.

    This function reports validation issues without modifying
    the original DataFrame.
    """

    issues = []

    # Check whether an age column exists.
    age_column = next(
        (
            column
            for column in df.columns
            if str(column).strip().lower() == "age"
        ),
        None,
    )

    if age_column is not None:
        numeric_ages = pd.to_numeric(
            df[age_column],
            errors="coerce",
        )
                # Report missing age values.
        missing_age_rows = df.index[
            df[age_column].isnull()
        ].tolist()

        for row_index in missing_age_rows:
            issues.append(
                {
                    "column": str(age_column),
                    "row": int(row_index) + 2,
                    "value": "",
                    "issue": "Age is missing.",
                }
            )

        # Report non-numeric age values.
        non_numeric_rows = df.index[
            df[age_column].notnull() & numeric_ages.isnull()
        ].tolist()

        for row_index in non_numeric_rows:
            issues.append(
                {
                    "column": str(age_column),
                    "row": int(row_index) + 2,
                    "value": str(df.loc[row_index, age_column]),
                    "issue": "Age must be a numeric value.",
                }
            )

        # Report negative ages.
        negative_age_rows = (
            numeric_ages[numeric_ages < 0].index.tolist()
        )

        for row_index in negative_age_rows:
            issues.append(
                {
                    "column": str(age_column),
                    "row": int(row_index) + 2,
                    "value": str(df.loc[row_index, age_column]),
                    "issue": "Age cannot be negative.",
                }
            )

        # Report unusually high ages.
        high_age_rows = (
            numeric_ages[numeric_ages > 120].index.tolist()
        )

        for row_index in high_age_rows:
            issues.append(
                {
                    "column": str(age_column),
                    "row": int(row_index) + 2,
                    "value": str(df.loc[row_index, age_column]),
                    "issue": "Age exceeds 120 and should be reviewed.",
                }
            )

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }
