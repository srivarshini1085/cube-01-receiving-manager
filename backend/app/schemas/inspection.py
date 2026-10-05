from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class VerdictEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


class InspectionStatusEnum(str, Enum):
    capturing = "capturing"
    pending = "pending"
    processing = "processing"
    completed = "completed"
    pending_review = "pending_review"
    failed_permanent = "failed_permanent"


class ImageTypeEnum(str, Enum):
    carton_exterior = "carton_exterior"
    carton_label = "carton_label"
    product = "product"
    product_label = "product_label"
    components = "components"
    other = "other"


class CheckTypeEnum(str, Enum):
    SKU_IDENTITY = "SKU_IDENTITY"
    QUANTITY_MATCH = "QUANTITY_MATCH"
    CARTON_COUNT = "CARTON_COUNT"
    UNITS_PER_CARTON = "UNITS_PER_CARTON"
    CARTON_DAMAGE = "CARTON_DAMAGE"
    UNIT_DAMAGE = "UNIT_DAMAGE"
    VARIANT_MATCH = "VARIANT_MATCH"
    COMPONENTS_CHECK = "COMPONENTS_CHECK"
    QUALITY_FLAGS = "QUALITY_FLAGS"


# --- Check Details ---
class InspectionCheckBase(BaseModel):
    check_key: str
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    verdict: VerdictEnum
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    explanation: Optional[str] = None
    model_version: Optional[str] = None
    latency_ms: Optional[int] = None


class InspectionCheckResponse(InspectionCheckBase):
    id: str
    inspection_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Evidence Items & Requests ---
class EvidenceItemResponse(BaseModel):
    id: str
    evidence_type: str
    description: Optional[str] = None
    relevance: Optional[str] = None
    image_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceRequestResponse(BaseModel):
    id: str
    inspection_id: str
    check_id: Optional[str] = None
    reason: str
    missing_evidence: str
    recommended_photograph: Optional[str] = None
    priority: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Overrides ---
class OperatorOverrideCreate(BaseModel):
    check_id: Optional[str] = None
    new_verdict: VerdictEnum
    reason: str = Field(..., min_length=5, description="Mandatory justification for operator override")
    operator_id: str


class OperatorOverrideResponse(BaseModel):
    id: str
    inspection_id: str
    check_id: Optional[str] = None
    original_verdict: str
    new_verdict: str
    reason: str
    operator_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Images ---
class ReceivingImageResponse(BaseModel):
    id: str
    inspection_id: Optional[str] = None
    file_reference: str
    image_type: str
    checksum: Optional[str] = None
    storage_key: Optional[str] = None
    image_url: Optional[str] = None
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata_json: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Inspection Requests & Responses ---
class CreateInspectionRequest(BaseModel):
    purchase_order_id: str
    po_line_id: str
    operator_id: Optional[str] = "op_default"
    unit_id: Optional[str] = None
    operator_attested_cartons: Optional[int] = None
    operator_attested_units_per_carton: Optional[int] = None


class AnalyzeInspectionRequest(BaseModel):
    operator_attested_cartons: Optional[int] = None
    operator_attested_units_per_carton: Optional[int] = None
    simulate_model_failure: Optional[bool] = False  # For Rule 3 fail-open testing


class ReceivingInspectionSummary(BaseModel):
    id: str
    organization_id: str
    purchase_order_id: str
    po_line_id: str
    sku: str
    operator_id: Optional[str]
    unit_id: Optional[str]
    inspection_status: str
    overall_decision: Optional[str]
    disposition: Optional[str]
    evidence_hash: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ReceivingInspectionDetail(ReceivingInspectionSummary):
    checks: List[InspectionCheckResponse] = []
    images: List[ReceivingImageResponse] = []
    evidence_items: List[EvidenceItemResponse] = []
    evidence_requests: List[EvidenceRequestResponse] = []
    overrides: List[OperatorOverrideResponse] = []
    po_details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
