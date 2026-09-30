from fastapi import Header, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Organization


def get_current_org_id(
    x_organization_id: Optional[str] = Header(
        default="org_demo_alpha",
        alias="X-Organization-Id",
        description="Tenant identifier for multi-tenant isolation (e.g. org_demo_alpha or org_demo_bravo)",
    ),
    db: Session = Depends(get_db),
) -> str:
    if not x_organization_id or not x_organization_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Missing required X-Organization-Id header for tenant isolation.",
        )
    val = x_organization_id.strip()
    org = db.execute(
        select(Organization).where(
            (Organization.id == val) | (Organization.organization_code == val)
        )
    ).scalar_one_or_none()
    if org:
        return org.id
    return val
