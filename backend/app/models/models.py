"""
INBOUNDSHIELD AI — Phase 3 domain models.
All org-owned tables carry organization_id. UTC timestamps throughout.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

InspectionStatus = Enum(
    "capturing", "pending", "processing", "completed", "pending_review", "failed_permanent",
    name="inspection_status",
)

Verdict = Enum("PASS", "FAIL", "UNCERTAIN", name="verdict")

POStatus = Enum("draft", "open", "closed", "cancelled", name="po_status")

ImageType = Enum(
    "carton_exterior", "carton_label", "product", "product_label", "components", "other",
    name="image_type",
)

EvidenceRequestStatus = Enum("open", "fulfilled", "cancelled", name="evidence_request_status")

EvidenceType = Enum(
    "visual_observation", "operator_count", "label_reading", "damage_record", "other",
    name="evidence_type",
)


# ---------------------------------------------------------------------------
# 1. Organizations
# ---------------------------------------------------------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="organization")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="organization"
    )
    inspections: Mapped[list["ReceivingInspection"]] = relationship(
        "ReceivingInspection", back_populates="organization"
    )


# ---------------------------------------------------------------------------
# 2. Products
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    asin: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    expected_colour: Mapped[str | None] = mapped_column(String(255))
    expected_variant: Mapped[str | None] = mapped_column(String(255))
    expected_components: Mapped[str | None] = mapped_column(Text)
    units_per_carton: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="products")
    po_lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="product"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),
        CheckConstraint("units_per_carton IS NULL OR units_per_carton > 0", name="ck_products_upc"),
        Index("ix_products_org_active", "organization_id", "is_active"),
    )


# ---------------------------------------------------------------------------
# 3. Purchase Orders
# ---------------------------------------------------------------------------

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    po_number: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(POStatus, nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="purchase_orders"
    )
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="purchase_order"
    )
    inspections: Mapped[list["ReceivingInspection"]] = relationship(
        "ReceivingInspection", back_populates="purchase_order"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "po_number", name="uq_po_org_number"),
        Index("ix_po_org_status", "organization_id", "status"),
    )


# ---------------------------------------------------------------------------
# 4. Purchase Order Lines
# ---------------------------------------------------------------------------

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    purchase_order_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("purchase_orders.id"), nullable=False
    )
    product_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("products.id"))
    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_cartons: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_units_per_carton: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_colour: Mapped[str | None] = mapped_column(String(255))
    expected_variant: Mapped[str | None] = mapped_column(String(255))
    expected_components: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    product: Mapped["Product | None"] = relationship("Product", back_populates="po_lines")
    inspections: Mapped[list["ReceivingInspection"]] = relationship(
        "ReceivingInspection", back_populates="po_line"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "purchase_order_id", "sku", name="uq_pol_org_po_sku"),
        CheckConstraint("expected_quantity > 0", name="ck_pol_qty"),
        CheckConstraint("expected_cartons > 0", name="ck_pol_cartons"),
        CheckConstraint("expected_units_per_carton > 0", name="ck_pol_upc"),
        Index("ix_pol_org_po", "organization_id", "purchase_order_id"),
    )


# ---------------------------------------------------------------------------
# 5. Receiving Inspections
# ---------------------------------------------------------------------------

class ReceivingInspection(Base):
    __tablename__ = "receiving_inspections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    purchase_order_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("purchase_orders.id"), nullable=False
    )
    po_line_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("purchase_order_lines.id"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    operator_id: Mapped[str | None] = mapped_column(String(255))
    unit_id: Mapped[str | None] = mapped_column(String(50))
    inspection_status: Mapped[str] = mapped_column(
        InspectionStatus, nullable=False, default="capturing"
    )
    overall_decision: Mapped[str | None] = mapped_column(Verdict)
    disposition: Mapped[str | None] = mapped_column(String(100))
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="inspections"
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="inspections"
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine", back_populates="inspections"
    )
    images: Mapped[list["ReceivingImage"]] = relationship(
        "ReceivingImage", back_populates="inspection"
    )
    checks: Mapped[list["InspectionCheck"]] = relationship(
        "InspectionCheck", back_populates="inspection"
    )
    evidence_requests: Mapped[list["EvidenceRequest"]] = relationship(
        "EvidenceRequest", back_populates="inspection"
    )
    overrides: Mapped[list["OperatorOverride"]] = relationship(
        "OperatorOverride", back_populates="inspection"
    )

    __table_args__ = (
        Index("ix_ri_org_status", "organization_id", "inspection_status"),
        Index("ix_ri_org_po", "organization_id", "purchase_order_id"),
        Index("ix_ri_org_unit", "organization_id", "unit_id"),
    )


# ---------------------------------------------------------------------------
# 6. Receiving Images
# ---------------------------------------------------------------------------

class ReceivingImage(Base):
    __tablename__ = "receiving_images"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    inspection_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("receiving_inspections.id"), nullable=False
    )
    file_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    image_type: Mapped[str] = mapped_column(ImageType, nullable=False, default="other")
    checksum: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    inspection: Mapped["ReceivingInspection"] = relationship(
        "ReceivingInspection", back_populates="images"
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem", back_populates="image"
    )

    __table_args__ = (
        Index("ix_ri_images_org_inspection", "organization_id", "inspection_id"),
    )


# ---------------------------------------------------------------------------
# 7. Inspection Checks
# ---------------------------------------------------------------------------

class InspectionCheck(Base):
    __tablename__ = "inspection_checks"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    inspection_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("receiving_inspections.id"), nullable=False
    )
    check_key: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_value: Mapped[str | None] = mapped_column(Text)
    observed_value: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(Verdict, nullable=False, default="UNCERTAIN")
    confidence: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    inspection: Mapped["ReceivingInspection"] = relationship(
        "ReceivingInspection", back_populates="checks"
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem", back_populates="check"
    )
    evidence_requests: Mapped[list["EvidenceRequest"]] = relationship(
        "EvidenceRequest", back_populates="check"
    )
    overrides: Mapped[list["OperatorOverride"]] = relationship(
        "OperatorOverride", back_populates="check"
    )

    __table_args__ = (
        UniqueConstraint("inspection_id", "check_key", name="uq_ic_inspection_key"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_ic_confidence",
        ),
        Index("ix_ic_org_inspection", "organization_id", "inspection_id"),
    )


# ---------------------------------------------------------------------------
# 8. Evidence Items
# ---------------------------------------------------------------------------

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    inspection_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("receiving_inspections.id"), nullable=False
    )
    check_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("inspection_checks.id"))
    image_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("receiving_images.id"))
    evidence_type: Mapped[str] = mapped_column(EvidenceType, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    relevance: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    inspection: Mapped["ReceivingInspection"] = relationship("ReceivingInspection")
    check: Mapped["InspectionCheck | None"] = relationship(
        "InspectionCheck", back_populates="evidence_items"
    )
    image: Mapped["ReceivingImage | None"] = relationship(
        "ReceivingImage", back_populates="evidence_items"
    )

    __table_args__ = (
        Index("ix_ei_org_inspection", "organization_id", "inspection_id"),
        Index("ix_ei_check", "check_id"),
    )


# ---------------------------------------------------------------------------
# 9. Evidence Requests
# ---------------------------------------------------------------------------

class EvidenceRequest(Base):
    __tablename__ = "evidence_requests"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    inspection_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("receiving_inspections.id"), nullable=False
    )
    check_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("inspection_checks.id"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    missing_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_photograph: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        EvidenceRequestStatus, nullable=False, default="open"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    inspection: Mapped["ReceivingInspection"] = relationship(
        "ReceivingInspection", back_populates="evidence_requests"
    )
    check: Mapped["InspectionCheck | None"] = relationship(
        "InspectionCheck", back_populates="evidence_requests"
    )

    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 5", name="ck_er_priority"),
        Index("ix_er_org_inspection", "organization_id", "inspection_id"),
        Index("ix_er_status", "organization_id", "status"),
    )


# ---------------------------------------------------------------------------
# 10. Operator Overrides  (append-only — never mutate original verdict)
# ---------------------------------------------------------------------------

class OperatorOverride(Base):
    __tablename__ = "operator_overrides"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("organizations.id"), nullable=False
    )
    inspection_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("receiving_inspections.id"), nullable=False
    )
    check_id: Mapped[str | None] = mapped_column(CHAR(36), ForeignKey("inspection_checks.id"))
    original_verdict: Mapped[str] = mapped_column(Verdict, nullable=False)
    new_verdict: Mapped[str] = mapped_column(Verdict, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    operator_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    inspection: Mapped["ReceivingInspection"] = relationship(
        "ReceivingInspection", back_populates="overrides"
    )
    check: Mapped["InspectionCheck | None"] = relationship(
        "InspectionCheck", back_populates="overrides"
    )

    __table_args__ = (
        Index("ix_oo_org_inspection", "organization_id", "inspection_id"),
    )
