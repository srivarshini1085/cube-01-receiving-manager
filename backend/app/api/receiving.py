import os
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_org_id
from app.repositories.receiving_repository import ReceivingRepository
from app.services.inspection_service import InspectionService
from app.schemas.inspection import (
    CreateInspectionRequest,
    AnalyzeInspectionRequest,
    ReceivingInspectionSummary,
    ReceivingInspectionDetail,
    ReceivingImageResponse,
    OperatorOverrideCreate,
    OperatorOverrideResponse,
)
from app.schemas.evidence_contract import CrossPodEvidenceContract

router = APIRouter(prefix="/api/v1/inspections", tags=["inspections"])


@router.post("", response_model=ReceivingInspectionDetail)
def create_inspection(
    payload: CreateInspectionRequest,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    # Validate PO line belongs to tenant
    po_line = repo.get_po_line(org_id, payload.po_line_id)
    if not po_line:
        raise HTTPException(status_code=404, detail="Purchase order line not found for this tenant.")

    inspection = repo.create_inspection(
        org_id=org_id,
        purchase_order_id=payload.purchase_order_id,
        po_line_id=payload.po_line_id,
        sku=po_line.sku,
        operator_id=payload.operator_id,
        unit_id=payload.unit_id,
    )
    return inspection


@router.get("", response_model=List[ReceivingInspectionSummary])
def list_inspections(
    status: Optional[str] = Query(None),
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    return repo.list_inspections(org_id=org_id, status=status)


@router.get("/{inspection_id}", response_model=ReceivingInspectionDetail)
def get_inspection(
    inspection_id: str,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    inspection = repo.get_inspection(org_id=org_id, inspection_id=inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found for this tenant.")

    detail = ReceivingInspectionDetail.model_validate(inspection)
    po_line = inspection.po_line
    po = inspection.purchase_order
    detail.po_details = {
        "po_number": po.po_number if po else "N/A",
        "supplier": po.supplier if po else "N/A",
        "sku": po_line.sku if po_line else inspection.sku,
        "expected_quantity": po_line.expected_quantity if po_line else 0,
        "expected_cartons": po_line.expected_cartons if po_line else 0,
        "expected_units_per_carton": po_line.expected_units_per_carton if po_line else 0,
        "expected_colour": po_line.expected_colour if po_line else None,
        "expected_variant": po_line.expected_variant if po_line else None,
        "expected_components": po_line.expected_components if po_line else None,
    }
    return detail


@router.post("/{inspection_id}/images", response_model=ReceivingImageResponse)
async def upload_image(
    inspection_id: str,
    file: UploadFile = File(...),
    image_type: str = Form("other"),
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    inspection = repo.get_inspection(org_id=org_id, inspection_id=inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found for this tenant.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    org_upload_dir = os.path.join(settings.UPLOAD_DIR, org_id)
    os.makedirs(org_upload_dir, exist_ok=True)

    contents = await file.read()
    checksum = hashlib.sha256(contents).hexdigest()
    
    file_ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    safe_filename = f"{inspection_id}_{checksum[:12]}{file_ext}"
    target_path = os.path.join(org_upload_dir, safe_filename)

    with open(target_path, "wb") as f:
        f.write(contents)

    image_record = repo.add_image(
        org_id=org_id,
        inspection_id=inspection_id,
        file_reference=target_path,
        image_type=image_type,
        checksum=checksum,
        metadata_json=f'{{"filename": "{file.filename}", "size_bytes": {len(contents)}}}',
    )
    return image_record


@router.get("/{inspection_id}/images/{image_id}/bytes")
def get_image_file(
    inspection_id: str,
    image_id: str,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    """
    Securely serves image bytes strictly scoped to the requesting tenant.
    Engineering Rule 1: A second organization cannot fetch another org's image by guessing a key.
    """
    repo = ReceivingRepository(db)
    image = repo.get_image(org_id=org_id, image_id=image_id)
    if not image or image.inspection_id != inspection_id:
        raise HTTPException(status_code=404, detail="Image not found or access denied for this tenant.")

    if not os.path.exists(image.file_reference):
        raise HTTPException(status_code=404, detail="Physical image asset missing on disk.")

    return FileResponse(image.file_reference)


@router.post("/{inspection_id}/analyze", response_model=ReceivingInspectionDetail)
def analyze_inspection(
    inspection_id: str,
    payload: AnalyzeInspectionRequest = AnalyzeInspectionRequest(),
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    service = InspectionService(db)
    try:
        updated = service.run_inspection_analysis(
            org_id=org_id,
            inspection_id=inspection_id,
            operator_cartons=payload.operator_attested_cartons,
            operator_upc=payload.operator_attested_units_per_carton,
            simulate_failure=payload.simulate_model_failure or False,
        )
        return get_inspection(inspection_id=inspection_id, org_id=org_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{inspection_id}/overrides", response_model=OperatorOverrideResponse)
def record_override(
    inspection_id: str,
    payload: OperatorOverrideCreate,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    repo = ReceivingRepository(db)
    inspection = repo.get_inspection(org_id=org_id, inspection_id=inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    original_verdict = "UNCERTAIN"
    if payload.check_id:
        check = next((c for c in inspection.checks if c.id == payload.check_id), None)
        if check:
            original_verdict = check.verdict
            check.verdict = payload.new_verdict.value
            db.commit()

    override = repo.record_override(
        org_id=org_id,
        inspection_id=inspection_id,
        check_id=payload.check_id,
        original_verdict=original_verdict,
        new_verdict=payload.new_verdict.value,
        reason=payload.reason,
        operator_id=payload.operator_id,
    )
    return override


@router.get("/{inspection_id}/contract", response_model=CrossPodEvidenceContract)
def export_contract(
    inspection_id: str,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    service = InspectionService(db)
    try:
        contract = service.export_evidence_contract(org_id=org_id, inspection_id=inspection_id)
        return contract
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
