
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    application: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str | None
