
import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate a basic profile of a pandas DataFrame."""

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "missing_values": {
            column: int(count)
            for column, count in df.isnull().sum().items()
        },
        "duplicate_rows": int(df.duplicated().sum()),
    }

def profile_csv(file_path: str) -> dict:
    """Read a CSV file and return its data profile."""

    df = pd.read_csv(file_path)

    return profile_dataframe(df)
