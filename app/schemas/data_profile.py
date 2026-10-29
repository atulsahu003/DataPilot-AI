
from pydantic import BaseModel


class DataProfileResponse(BaseModel):
    row_count: int
    column_count: int
    columns: list[str]
    data_types: dict[str, str]
    missing_values: dict[str, int]
    duplicate_rows: int
