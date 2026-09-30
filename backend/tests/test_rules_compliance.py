import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import Organization, Product, PurchaseOrder, PurchaseOrderLine


@pytest.fixture(scope="module")
def setup_rules_test_data(db_session):
    org = db_session.query(Organization).filter(Organization.organization_code == "org_demo_alpha").first()
    assert org is not None

    po = db_session.query(PurchaseOrder).filter(PurchaseOrder.organization_id == org.id).first()
    assert po is not None

    pol = db_session.query(PurchaseOrderLine).filter(PurchaseOrderLine.purchase_order_id == po.id).first()
    assert pol is not None

    return {
        "org_id": org.id,
        "po_id": po.id,
        "pol_id": pol.id,
        "sku": pol.sku,
    }


def test_rule_2_batch_model_calls(setup_rules_test_data):
    """
    Engineering Rule 2: Make ONE call per unit carrying all checks, never one call per check.
    """
    client = TestClient(app)
    data = setup_rules_test_data

    # Create inspection
    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": data["org_id"]},
        json={
            "purchase_order_id": data["po_id"],
            "po_line_id": data["pol_id"],
            "operator_id": "op_test_01",
            "unit_id": "UNIT-BATCH-001",
        },
    )
    assert create_resp.status_code == 200
    insp_id = create_resp.json()["id"]

    # Mock VisionAgent.analyze_unit_batch to count invocations
    with patch("app.services.inspection_service.VisionAgent.analyze_unit_batch") as mock_vision:
        from app.agents.vision_agent import VisionObservation
        mock_vision.return_value = VisionObservation(
            detected_sku=data["sku"],
            detected_colour="blue",
            detected_variant="standard",
            estimated_cartons=1,
            estimated_units_per_carton=24,
            carton_damage_types=[],
            unit_damage_types=[],
        )

        analyze_resp = client.post(
            f"/api/v1/inspections/{insp_id}/analyze",
            headers={"X-Organization-Id": data["org_id"]},
            json={"operator_attested_cartons": 1, "operator_attested_units_per_carton": 24},
        )
        assert analyze_resp.status_code == 200

        # Verifies that vision analysis was called EXACTLY ONCE for all checks
        assert mock_vision.call_count == 1

        detail = analyze_resp.json()
        assert len(detail["checks"]) >= 7


def test_rule_3_fail_open(setup_rules_test_data):
    """
    Engineering Rule 3: Fail open. Model error or timeout still saves capture and produces a record, marked pending.
    Nothing blocks the operator.
    """
    client = TestClient(app)
    data = setup_rules_test_data

    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": data["org_id"]},
        json={
            "purchase_order_id": data["po_id"],
            "po_line_id": data["pol_id"],
            "operator_id": "op_test_02",
            "unit_id": "UNIT-FAILOPEN-002",
        },
    )
    insp_id = create_resp.json()["id"]

    # Trigger analysis with simulate_model_failure=True
    resp = client.post(
        f"/api/v1/inspections/{insp_id}/analyze",
        headers={"X-Organization-Id": data["org_id"]},
        json={"simulate_model_failure": True},
    )
    assert resp.status_code == 200
    res_data = resp.json()

    # Must be marked pending_review, overall_decision UNCERTAIN, with an open evidence request
    assert res_data["inspection_status"] == "pending_review"
    assert res_data["overall_decision"] == "UNCERTAIN"
    assert len(res_data["evidence_requests"]) >= 1


def test_rule_4_uncertain_verdict_and_evidence_requests(setup_rules_test_data):
    """
    Engineering Rule 4: UNCERTAIN is a valid verdict. It isn't a low-confidence PASS.
    Build it as a first-class outcome with targeted evidence requests.
    """
    client = TestClient(app)
    data = setup_rules_test_data

    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": data["org_id"]},
        json={
            "purchase_order_id": data["po_id"],
            "po_line_id": data["pol_id"],
            "operator_id": "op_test_03",
            "unit_id": "UNIT-UNCERTAIN-003",
        },
    )
    insp_id = create_resp.json()["id"]

    # Upload ambiguous glared image
    with open("fixtures/receiving/ambiguous_glare_label.jpg", "rb") as f:
        upload_resp = client.post(
            f"/api/v1/inspections/{insp_id}/images",
            headers={"X-Organization-Id": data["org_id"]},
            files={"file": ("ambiguous_glare_label.jpg", f, "image/jpeg")},
            data={"image_type": "carton_label"},
        )
    assert upload_resp.status_code == 200

    # Analyze
    resp = client.post(
        f"/api/v1/inspections/{insp_id}/analyze",
        headers={"X-Organization-Id": data["org_id"]},
        json={},
    )
    assert resp.status_code == 200
    res_data = resp.json()

    # Overall verdict must be UNCERTAIN
    assert res_data["overall_decision"] == "UNCERTAIN"
    assert res_data["disposition"] == "UNCERTAIN_PENDING_EVIDENCE"

    # Targeted evidence request must be generated
    assert len(res_data["evidence_requests"]) >= 1
    req = res_data["evidence_requests"][0]
    assert req["status"] == "open"


def test_rule_6_overrides_are_data(setup_rules_test_data):
    """
    Engineering Rule 6: Overrides are data.
    Capture original verdict, new verdict, reason, timestamp, and operator ID.
    Never discard or mutate silently.
    """
    client = TestClient(app)
    data = setup_rules_test_data

    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": data["org_id"]},
        json={
            "purchase_order_id": data["po_id"],
            "po_line_id": data["pol_id"],
            "operator_id": "op_dock_lead",
            "unit_id": "UNIT-OVERRIDE-004",
        },
    )
    insp_id = create_resp.json()["id"]

    # Initial analysis with fail open
    client.post(
        f"/api/v1/inspections/{insp_id}/analyze",
        headers={"X-Organization-Id": data["org_id"]},
        json={"simulate_model_failure": True},
    )

    detail_resp = client.get(f"/api/v1/inspections/{insp_id}", headers={"X-Organization-Id": data["org_id"]})
    checks = detail_resp.json()["checks"]
    check_id = checks[0]["id"] if checks else None

    # Operator overrides verdict to PASS with reason
    override_resp = client.post(
        f"/api/v1/inspections/{insp_id}/overrides",
        headers={"X-Organization-Id": data["org_id"]},
        json={
            "check_id": check_id,
            "new_verdict": "PASS",
            "reason": "Supervisor physically inspected package barcode with handheld terminal; verified genuine SKU.",
            "operator_id": "supervisor_sarah",
        },
    )
    assert override_resp.status_code == 200
    ov_data = override_resp.json()
    assert ov_data["original_verdict"] == "UNCERTAIN"
    assert ov_data["new_verdict"] == "PASS"
    assert "supervisor_sarah" in ov_data["operator_id"]
    assert "Supervisor physically inspected" in ov_data["reason"]

    # Verify that inspection details now contain the immutable override record
    final_detail = client.get(f"/api/v1/inspections/{insp_id}", headers={"X-Organization-Id": data["org_id"]}).json()
    assert len(final_detail["overrides"]) >= 1
    assert final_detail["overrides"][0]["operator_id"] == "supervisor_sarah"
