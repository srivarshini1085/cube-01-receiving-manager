"""initial_schema

Revision ID: dda3ddf387b4
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR, JSON

revision = "dda3ddf387b4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "users",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("auth_subject", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "auth_subject", name="uq_users_org_auth"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "catalog_products",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "id", name="uq_catalog_products_org_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "product_variants",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("product_id", CHAR(36), sa.ForeignKey("catalog_products.id"), nullable=False),
        sa.Column("sku", sa.String(255), nullable=False),
        sa.Column("colour", sa.String(255)),
        sa.Column("variant_label", sa.String(255)),
        sa.Column("components", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "sku", name="uq_product_variants_org_sku"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "product_identifiers",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("variant_id", CHAR(36), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("id_type", sa.String(50), nullable=False),
        sa.Column("id_value", sa.String(255), nullable=False),
        sa.UniqueConstraint("org_id", "id_type", "id_value", name="uq_product_identifiers_org_type_val"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("po_number", sa.String(255), nullable=False),
        sa.Column("supplier", sa.String(255)),
        sa.Column("source_version", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "po_number", name="uq_purchase_orders_org_po"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("po_id", CHAR(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("line_number", sa.String(50), nullable=False),
        sa.Column("variant_id", CHAR(36), sa.ForeignKey("product_variants.id")),
        sa.Column("ordered_cartons", sa.Integer, nullable=False),
        sa.Column("units_per_carton", sa.Integer, nullable=False),
        sa.Column("ordered_qty", sa.Integer, nullable=False),
        sa.UniqueConstraint("org_id", "po_id", "line_number", name="uq_po_lines_org_po_line"),
        sa.CheckConstraint("ordered_cartons >= 0", name="ck_po_lines_ordered_cartons"),
        sa.CheckConstraint("units_per_carton >= 0", name="ck_po_lines_units_per_carton"),
        sa.CheckConstraint("ordered_qty >= 0", name="ck_po_lines_ordered_qty"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "receiving_sessions",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("operator_id", CHAR(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "id", name="uq_receiving_sessions_org_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "receiving_records",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("session_id", CHAR(36), sa.ForeignKey("receiving_sessions.id"), nullable=False),
        sa.Column("po_line_id", CHAR(36), sa.ForeignKey("purchase_order_lines.id"), nullable=False),
        sa.Column("operator_id", CHAR(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("unit_id", sa.String(50)),
        sa.Column("cartons_received", sa.Integer),
        sa.Column("units_per_carton_counted", sa.Integer),
        sa.Column("qty_received", sa.Integer),
        sa.Column(
            "processing_state",
            sa.Enum(
                "capturing", "pending", "processing", "completed",
                "pending_review", "failed_permanent",
                name="processing_state",
            ),
            nullable=False,
            server_default="capturing",
        ),
        sa.Column(
            "overall_outcome",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="business_outcome"),
        ),
        sa.Column("idempotency_key", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "id", name="uq_receiving_records_org_id"),
        sa.UniqueConstraint("org_id", "idempotency_key", name="uq_receiving_records_org_idem"),
        sa.CheckConstraint("cartons_received IS NULL OR cartons_received >= 0", name="ck_rr_cartons"),
        sa.CheckConstraint("units_per_carton_counted IS NULL OR units_per_carton_counted >= 0", name="ck_rr_upc"),
        sa.CheckConstraint("qty_received IS NULL OR qty_received >= 0", name="ck_rr_qty"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "evidence_assets",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("media_type", sa.String(100)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("capture_role", sa.String(100)),
        sa.Column(
            "validation_status",
            sa.Enum("pending", "valid", "invalid", name="asset_validation_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("validation_error", sa.Text),
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("org_id", "id", name="uq_evidence_assets_org_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "analysis_jobs",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "claimed", "completed", "failed", name="job_status"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_detail", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_analysis_jobs_idem"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "vision_runs",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("job_id", CHAR(36), sa.ForeignKey("analysis_jobs.id"), nullable=False),
        sa.Column("provider", sa.String(100)),
        sa.Column("model_id", sa.String(255)),
        sa.Column("schema_version", sa.String(50)),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column(
            "status",
            sa.Enum("queued", "claimed", "completed", "failed", name="job_status"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("error_class", sa.String(100)),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "observations",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("run_id", CHAR(36), sa.ForeignKey("vision_runs.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("attribute", sa.String(100), nullable=False),
        sa.Column("value", sa.Text),
        sa.Column(
            "visibility",
            sa.Enum("observed", "not_visible", "ambiguous", name="visibility_state"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float),
        sa.Column("asset_refs", JSON),
        sa.Column("limitations", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "coverage_results",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column(
            "coverage_status",
            sa.Enum("sufficient", "missing", "ambiguous", name="coverage_status"),
            nullable=False,
        ),
        sa.Column("gap_reason", sa.Text),
        sa.Column("rule_version", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "evidence_requests",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("coverage_result_id", CHAR(36), sa.ForeignKey("coverage_results.id"), nullable=False),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column("instruction", sa.Text, nullable=False),
        sa.Column(
            "state",
            sa.Enum("open", "fulfilled", "cancelled", name="evidence_request_state"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("fulfilled_asset_id", CHAR(36), sa.ForeignKey("evidence_assets.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "check_results",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column(
            "outcome",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="business_outcome"),
            nullable=False,
        ),
        sa.Column("expected_value", sa.Text),
        sa.Column("expected_source", sa.String(255)),
        sa.Column("observed_value", sa.Text),
        sa.Column("observed_source", sa.String(100)),
        sa.Column("rationale", sa.Text),
        sa.Column("evidence_asset_ids", JSON),
        sa.Column("rule_version", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "decision_events",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum("machine_decision", "operator_override", name="decision_event_type"),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="business_outcome"),
            nullable=False,
        ),
        sa.Column(
            "prior_outcome",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="business_outcome"),
        ),
        sa.Column("policy_version", sa.String(50)),
        sa.Column("check_result_ids", JSON),
        sa.Column("actor_id", CHAR(36), sa.ForeignKey("users.id")),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "evidence_records",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("org_id", CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("record_id", CHAR(36), sa.ForeignKey("receiving_records.id"), nullable=False),
        sa.Column("schema_version", sa.String(50), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "evaluation_cases",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("unit_id", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "split",
            sa.Enum("dev", "held_out", name="eval_split"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "evaluation_labels",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("case_id", CHAR(36), sa.ForeignKey("evaluation_cases.id"), nullable=False),
        sa.Column("labeler", sa.String(255), nullable=False),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column(
            "label",
            sa.Enum("PASS", "FAIL", "UNCERTAIN", name="business_outcome"),
            nullable=False,
        ),
        sa.Column("adjudicated", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # Tenant-leading indexes for queue/history queries
    op.create_index("ix_receiving_records_org_state", "receiving_records", ["org_id", "processing_state"])
    op.create_index("ix_receiving_records_org_unit", "receiving_records", ["org_id", "unit_id"])
    op.create_index("ix_evidence_assets_org_record", "evidence_assets", ["org_id", "record_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status", "created_at"])
    op.create_index("ix_decision_events_org_record", "decision_events", ["org_id", "record_id"])
    op.create_index("ix_check_results_org_record", "check_results", ["org_id", "record_id"])


def downgrade() -> None:
    op.drop_index("ix_check_results_org_record", "check_results")
    op.drop_index("ix_decision_events_org_record", "decision_events")
    op.drop_index("ix_analysis_jobs_status", "analysis_jobs")
    op.drop_index("ix_evidence_assets_org_record", "evidence_assets")
    op.drop_index("ix_receiving_records_org_unit", "receiving_records")
    op.drop_index("ix_receiving_records_org_state", "receiving_records")

    op.drop_table("evaluation_labels")
    op.drop_table("evaluation_cases")
    op.drop_table("evidence_records")
    op.drop_table("decision_events")
    op.drop_table("check_results")
    op.drop_table("evidence_requests")
    op.drop_table("coverage_results")
    op.drop_table("observations")
    op.drop_table("vision_runs")
    op.drop_table("analysis_jobs")
    op.drop_table("evidence_assets")
    op.drop_table("receiving_records")
    op.drop_table("receiving_sessions")
    op.drop_table("purchase_order_lines")
    op.drop_table("purchase_orders")
    op.drop_table("product_identifiers")
    op.drop_table("product_variants")
    op.drop_table("catalog_products")
    op.drop_table("users")
    op.drop_table("organizations")
