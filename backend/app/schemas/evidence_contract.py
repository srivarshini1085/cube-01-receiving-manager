from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContractCheckRecord(BaseModel):
    check_key: str
    expected: Optional[str] = None
    observed: Optional[str] = None
    verdict: str  # PASS, FAIL, UNCERTAIN
    confidence: Optional[float] = None
    explanation: Optional[str] = None


class ContractEvidenceHash(BaseModel):
    image_type: str
    filename: str
    sha256: str


class ContractOverride(BaseModel):
    check_key: Optional[str] = None
    original_verdict: str
    new_verdict: str
    reason: str
    operator_id: str
    timestamp: str


class CrossPodEvidenceContract(BaseModel):
    contract_version: str = "2.0.0"
    stage: str = "01_RECEIVING"
    record_id: str
    unit_id: str
    org_id: str
    operator_id: str
    captured_at: str
    completed_at: str
    
    # Authoritative PO context
    po_number: str
    po_line: int
    supplier: Optional[str] = None
    sku: str
    asin: Optional[str] = None
    product_title: Optional[str] = None
    spec_colour: Optional[str] = None
    spec_variant: Optional[str] = None
    spec_components: Optional[str] = None
    
    # Quantities
    cartons_ordered: int
    cartons_received: int
    units_per_carton_ordered: int
    units_per_carton_counted: int
    qty_ordered: int
    qty_received: int
    
    # Findings and Results
    overall_verdict: str  # PASS, FAIL, UNCERTAIN
    disposition: str      # ACCEPTED, EXCEPTION_SHORTAGE, EXCEPTION_DAMAGE, EXCEPTION_MISMATCH, etc.
    checks: List[ContractCheckRecord]
    
    # Evidence & Audit
    evidence_hashes: List[ContractEvidenceHash]
    overrides: List[ContractOverride] = []
    
    # Cryptographic integrity
    certificate_sha256: str
