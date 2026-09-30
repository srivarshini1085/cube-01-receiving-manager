from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    status: str  # "ok" | "error"
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    database: DatabaseHealth
