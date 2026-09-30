from fastapi import APIRouter

from app.core.database import check_db_connection
from app.schemas.health import DatabaseHealth, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    db_ok = check_db_connection()
    db_health = DatabaseHealth(status="ok" if db_ok else "error")
    overall = "ok" if db_ok else "degraded"
    return HealthResponse(status=overall, database=db_health)
