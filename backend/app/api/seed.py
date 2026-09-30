from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Organization
from app.services.seed_service import seed_database_from_csv

router = APIRouter(prefix="/api/v1", tags=["system_and_seed"])


@router.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    return seed_database_from_csv(db)


@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db)):
    orgs = db.execute(select(Organization)).scalars().all()
    return [{"id": o.id, "organization_code": o.organization_code, "name": o.name} for o in orgs]
