"""phase3_domain_model

Revision ID: 371cf5e48394
Revises: dda3ddf387b4
Create Date: 2024-01-01 00:00:01.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision = "371cf5e48394"
down_revision = "dda3ddf387b4"
branch_labels = None
depends_on = None

# Phase 2 tables to drop (in FK-safe order, children first)
_P2_TABLES = [
    "evaluation_labels",
    "evaluation_cases",
    "evidence_records",
    "decision_events",
    "check_results",
    "evidence_requests",
    "coverage_results",
    "observations",
    "vision_runs",
    "analysis_jobs",
    "evidence_assets",
    "receiving_records",
    "receiving_sessions",
    "purchase_order_lines",
    "purchase_orders",
    "product_identifiers",
    "product_variants",
    "catalog_products",
    "users",
    "organizations",
]


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Drop Phase 2 tables                                                  #
    # ------------------------------------------------------------------ #
    op.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in _P2_TABLES:
        op.execute(f"DROP TABLE IF EXISTS `{table}`")
    op.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Drop Phase 2 enums (MySQL stores them inline; dropping tables is enough,
    # but we drop the alembic_version row so we can track cleanly)

    # ------------------------------------------------------------------ #
    # Phase 3 tables                                                       #
    # ------------------------------------------------------------------ #

    op.create_table(
        "organizations",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_code", name="uq_org_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "products",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("sku", sa.String(255), nullable=False),
        sa.Column("asin", sa.String(20)),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("expected_colour", sa.String(255)),
        sa.Column("expected_variant", sa.String(255)),
        sa.Column("expected_components", sa.Text),
        sa.Column("units_per_carton", sa.Integer),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),
        sa.CheckConstraint("units_per_carton IS NULL OR units_per_carton > 0", name="ck_products_upc"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_products_org_active", "products", ["organization_id", "is_active"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("po_number", sa.String(255), nullable=False),
        sa.Column("supplier", sa.String(255)),
        sa.Column(
            "status",
            sa.Enum("draft", "open", "closed", "cancelled", name="po_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "po_number", name="uq_po_org_number"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_po_org_status", "purchase_orders", ["organization_id", "status"])

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("purchase_order_id", CHAR(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("product_id", CHAR(36), sa.ForeignKey("products.id")),
        sa.Column("sku", sa.String(255), nullable=False),
        sa.Column("expected_quantity", sa.Integer, nullable=False),
        sa.Column("expected_cartons", sa.Integer, nullable=False),
        sa.Column("expected_units_per_carton", sa.Integer, nullable=False),
        sa.Column("expected_colour", sa.String(255)),
        sa.Column("expected_variant", sa.String(255)),
        sa.Column("expected_components", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id", "purchase_order_id", "sku", name="uq_pol_org_po_sku"
        ),
        sa.CheckConstraint("expected_quantity > 0", name="ck_pol_qty"),
        sa.CheckConstraint("expected_cartons > 0", name="ck_pol_cartons"),
        sa.CheckConstraint("expected_units_per_carton > 0", name="ck_pol_upc"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_pol_org_po", "purchase_order_lines", ["organization_id", "purchase_order_id"])

    op.create_table(
        "receiving_inspections",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "purchase_order_id", CHAR(36), sa.ForeignKey("purchase_orders.id"), nullable=False
        ),
        sa.Column(
            "po_line_id", CHAR(36), sa.ForeignKey("purchase_order_lines.id"), nullable=False
        ),
        sa.Column("sku", sa.String(255), nullable=False),
        sa.Column("operator_id", sa.String(255)),
        sa.Column("unit_id", sa.String(50)),
        sa.Column(
            "inspection_status",
            sa.Enum(
                "capturing", "pending", "processing", "completed",
                "pending_review", "failed_permanent",
                name="inspection_status",
            ),
            nullable=False,
            server_default="capturing",
        ),
        sa.Column(
            "overall_decision",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="verdict"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_ri_org_status", "receiving_inspections", ["organization_id", "inspection_status"])
    op.create_index("ix_ri_org_po", "receiving_inspections", ["organization_id", "purchase_order_id"])
    op.create_index("ix_ri_org_unit", "receiving_inspections", ["organization_id", "unit_id"])

    op.create_table(
        "receiving_images",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "inspection_id", CHAR(36), sa.ForeignKey("receiving_inspections.id"), nullable=False
        ),
        sa.Column("file_reference", sa.String(500), nullable=False),
        sa.Column(
            "image_type",
            sa.Enum(
                "carton_exterior", "carton_label", "product",
                "product_label", "components", "other",
                name="image_type",
            ),
            nullable=False,
            server_default="other",
        ),
        sa.Column("checksum", sa.String(64)),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_ri_images_org_inspection", "receiving_images", ["organization_id", "inspection_id"])

    op.create_table(
        "inspection_checks",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "inspection_id", CHAR(36), sa.ForeignKey("receiving_inspections.id"), nullable=False
        ),
        sa.Column("check_key", sa.String(100), nullable=False),
        sa.Column("expected_value", sa.Text),
        sa.Column("observed_value", sa.Text),
        sa.Column(
            "verdict",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="verdict"),
            nullable=False,
            server_default="UNCERTAIN",
        ),
        sa.Column("confidence", sa.Float),
        sa.Column("explanation", sa.Text),
        sa.Column("model_version", sa.String(100)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("inspection_id", "check_key", name="uq_ic_inspection_key"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_ic_confidence",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_ic_org_inspection", "inspection_checks", ["organization_id", "inspection_id"])

    op.create_table(
        "evidence_items",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "inspection_id", CHAR(36), sa.ForeignKey("receiving_inspections.id"), nullable=False
        ),
        sa.Column("check_id", CHAR(36), sa.ForeignKey("inspection_checks.id")),
        sa.Column("image_id", CHAR(36), sa.ForeignKey("receiving_images.id")),
        sa.Column(
            "evidence_type",
            sa.Enum(
                "visual_observation", "operator_count", "label_reading",
                "damage_record", "other",
                name="evidence_type",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text),
        sa.Column("relevance", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_ei_org_inspection", "evidence_items", ["organization_id", "inspection_id"])
    op.create_index("ix_ei_check", "evidence_items", ["check_id"])

    op.create_table(
        "evidence_requests",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "inspection_id", CHAR(36), sa.ForeignKey("receiving_inspections.id"), nullable=False
        ),
        sa.Column("check_id", CHAR(36), sa.ForeignKey("inspection_checks.id")),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("missing_evidence", sa.Text, nullable=False),
        sa.Column("recommended_photograph", sa.Text),
        sa.Column("priority", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum("open", "fulfilled", "cancelled", name="evidence_request_status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("priority >= 1 AND priority <= 5", name="ck_er_priority"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_er_org_inspection", "evidence_requests", ["organization_id", "inspection_id"])
    op.create_index("ix_er_status", "evidence_requests", ["organization_id", "status"])

    op.create_table(
        "operator_overrides",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("organization_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column(
            "inspection_id", CHAR(36), sa.ForeignKey("receiving_inspections.id"), nullable=False
        ),
        sa.Column("check_id", CHAR(36), sa.ForeignKey("inspection_checks.id")),
        sa.Column(
            "original_verdict",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="verdict"),
            nullable=False,
        ),
        sa.Column(
            "new_verdict",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="verdict"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("operator_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_oo_org_inspection", "operator_overrides", ["organization_id", "inspection_id"])


def downgrade() -> None:
    op.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in [
        "operator_overrides", "evidence_requests", "evidence_items",
        "inspection_checks", "receiving_images", "receiving_inspections",
        "purchase_order_lines", "purchase_orders", "products", "organizations",
    ]:
        op.execute(f"DROP TABLE IF EXISTS `{table}`")
    op.execute("SET FOREIGN_KEY_CHECKS = 1")
