from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    id: str
    organization_id: str
    sku: str
    asin: Optional[str] = None
    name: str
    description: Optional[str] = None
    expected_colour: Optional[str] = None
    expected_variant: Optional[str] = None
    expected_components: Optional[str] = None
    units_per_carton: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderLineResponse(BaseModel):
    id: str
    organization_id: str
    purchase_order_id: str
    product_id: Optional[str] = None
    sku: str
    expected_quantity: int
    expected_cartons: int
    expected_units_per_carton: int
    expected_colour: Optional[str] = None
    expected_variant: Optional[str] = None
    expected_components: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    id: str
    organization_id: str
    po_number: str
    supplier: Optional[str] = None
    status: str
    created_at: datetime
    lines: List[PurchaseOrderLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
