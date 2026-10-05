from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.models import (
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
    ReceivingInspection,
    ReceivingImage,
    InspectionCheck,
    EvidenceItem,
    EvidenceRequest,
    OperatorOverride,
)


class ReceivingRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Tenant / Organization Management
    # -------------------------------------------------------------------------
    def get_organization_by_code(self, org_code: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.organization_code == org_code)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_organization(self, org_code: str, name: str) -> Organization:
        org = self.get_organization_by_code(org_code)
        if not org:
            org = Organization(organization_code=org_code, name=name)
            self.db.add(org)
            self.db.commit()
            self.db.refresh(org)
        return org

    # -------------------------------------------------------------------------
    # Products & Catalog
    # -------------------------------------------------------------------------
    def list_products(self, org_id: str) -> List[Product]:
        stmt = select(Product).where(Product.organization_id == org_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_product(self, org_id: str, product_id: str) -> Optional[Product]:
        stmt = select(Product).where(
            and_(Product.id == product_id, Product.organization_id == org_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_product_by_sku(self, org_id: str, sku: str) -> Optional[Product]:
        stmt = select(Product).where(
            and_(Product.sku == sku, Product.organization_id == org_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Purchase Orders & Lines
    # -------------------------------------------------------------------------
    def list_purchase_orders(self, org_id: str) -> List[PurchaseOrder]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.organization_id == org_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_purchase_order(self, org_id: str, po_id: str) -> Optional[PurchaseOrder]:
        stmt = select(PurchaseOrder).where(
            and_(PurchaseOrder.id == po_id, PurchaseOrder.organization_id == org_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_po_line(self, org_id: str, po_line_id: str) -> Optional[PurchaseOrderLine]:
        stmt = select(PurchaseOrderLine).where(
            and_(PurchaseOrderLine.id == po_line_id, PurchaseOrderLine.organization_id == org_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Inspections (strictly tenant isolated)
    # -------------------------------------------------------------------------
    def create_inspection(
        self,
        org_id: str,
        purchase_order_id: str,
        po_line_id: str,
        sku: str,
        operator_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> ReceivingInspection:
        inspection = ReceivingInspection(
            organization_id=org_id,
            purchase_order_id=purchase_order_id,
            po_line_id=po_line_id,
            sku=sku,
            operator_id=operator_id,
            unit_id=unit_id,
            inspection_status="capturing",
        )
        self.db.add(inspection)
        self.db.commit()
        self.db.refresh(inspection)
        return inspection

    def get_inspection(self, org_id: str, inspection_id: str) -> Optional[ReceivingInspection]:
        stmt = select(ReceivingInspection).where(
            and_(
                ReceivingInspection.id == inspection_id,
                ReceivingInspection.organization_id == org_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_inspections(
        self, org_id: str, status: Optional[str] = None
    ) -> List[ReceivingInspection]:
        conditions = [ReceivingInspection.organization_id == org_id]
        if status:
            conditions.append(ReceivingInspection.inspection_status == status)
        stmt = select(ReceivingInspection).where(and_(*conditions)).order_by(ReceivingInspection.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    # -------------------------------------------------------------------------
    # Receiving Images
    # -------------------------------------------------------------------------
    def add_image(
        self,
        org_id: str,
        inspection_id: str,
        file_reference: str,
        image_type: str = "other",
        checksum: Optional[str] = None,
        metadata_json: Optional[str] = None,
        storage_key: Optional[str] = None,
        image_url: Optional[str] = None,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
    ) -> ReceivingImage:
        image = ReceivingImage(
            organization_id=org_id,
            inspection_id=inspection_id,
            file_reference=file_reference,
            image_type=image_type,
            checksum=checksum,
            metadata_json=metadata_json,
            storage_key=storage_key,
            image_url=image_url,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def get_image(self, org_id: str, image_id: str) -> Optional[ReceivingImage]:
        stmt = select(ReceivingImage).where(
            and_(ReceivingImage.id == image_id, ReceivingImage.organization_id == org_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Checks & Evidence
    # -------------------------------------------------------------------------
    def save_or_update_check(
        self,
        org_id: str,
        inspection_id: str,
        check_key: str,
        expected_value: Optional[str],
        observed_value: Optional[str],
        verdict: str,
        confidence: Optional[float] = None,
        explanation: Optional[str] = None,
        model_version: Optional[str] = None,
        latency_ms: Optional[int] = None,
    ) -> InspectionCheck:
        stmt = select(InspectionCheck).where(
            and_(
                InspectionCheck.inspection_id == inspection_id,
                InspectionCheck.check_key == check_key,
                InspectionCheck.organization_id == org_id,
            )
        )
        check = self.db.execute(stmt).scalar_one_or_none()
        if check:
            check.expected_value = expected_value
            check.observed_value = observed_value
            check.verdict = verdict
            check.confidence = confidence
            check.explanation = explanation
            check.model_version = model_version
            check.latency_ms = latency_ms
        else:
            check = InspectionCheck(
                organization_id=org_id,
                inspection_id=inspection_id,
                check_key=check_key,
                expected_value=expected_value,
                observed_value=observed_value,
                verdict=verdict,
                confidence=confidence,
                explanation=explanation,
                model_version=model_version,
                latency_ms=latency_ms,
            )
            self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check

    def add_evidence_item(
        self,
        org_id: str,
        inspection_id: str,
        evidence_type: str,
        check_id: Optional[str] = None,
        image_id: Optional[str] = None,
        description: Optional[str] = None,
        relevance: Optional[str] = None,
    ) -> EvidenceItem:
        item = EvidenceItem(
            organization_id=org_id,
            inspection_id=inspection_id,
            check_id=check_id,
            image_id=image_id,
            evidence_type=evidence_type,
            description=description,
            relevance=relevance,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def add_evidence_request(
        self,
        org_id: str,
        inspection_id: str,
        reason: str,
        missing_evidence: str,
        recommended_photograph: Optional[str] = None,
        priority: int = 1,
        check_id: Optional[str] = None,
    ) -> EvidenceRequest:
        req = EvidenceRequest(
            organization_id=org_id,
            inspection_id=inspection_id,
            check_id=check_id,
            reason=reason,
            missing_evidence=missing_evidence,
            recommended_photograph=recommended_photograph,
            priority=priority,
            status="open",
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def record_override(
        self,
        org_id: str,
        inspection_id: str,
        original_verdict: str,
        new_verdict: str,
        reason: str,
        operator_id: str,
        check_id: Optional[str] = None,
    ) -> OperatorOverride:
        override = OperatorOverride(
            organization_id=org_id,
            inspection_id=inspection_id,
            check_id=check_id,
            original_verdict=original_verdict,
            new_verdict=new_verdict,
            reason=reason,
            operator_id=operator_id,
        )
        self.db.add(override)
        self.db.commit()
        self.db.refresh(override)
        return override

    def update_inspection_status_and_decision(
        self,
        org_id: str,
        inspection_id: str,
        status: str,
        overall_decision: Optional[str] = None,
        disposition: Optional[str] = None,
        evidence_hash: Optional[str] = None,
    ) -> Optional[ReceivingInspection]:
        inspection = self.get_inspection(org_id, inspection_id)
        if not inspection:
            return None
        inspection.inspection_status = status
        if overall_decision:
            inspection.overall_decision = overall_decision
        if disposition:
            inspection.disposition = disposition
        if evidence_hash:
            inspection.evidence_hash = evidence_hash
        if status in ("completed", "pending_review", "failed_permanent"):
            inspection.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(inspection)
        return inspection
