from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_org_id
from app.repositories.receiving_repository import ReceivingRepository
from app.schemas.purchase_order import (
    ProductResponse,
    PurchaseOrderResponse,
    PurchaseOrderLineResponse,
)

router = APIRouter(prefix="/api/v1", tags=["catalog_and_po"])


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    return repo.list_products(org_id=org_id)


@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    pos = repo.list_purchase_orders(org_id=org_id)
    return pos
