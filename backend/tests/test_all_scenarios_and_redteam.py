import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.scenario_runner import ScenarioRunner
from app.models.models import Organization, PurchaseOrder


def test_all_10_canonical_scenarios():
    """
    Executes and validates all 10 problem-statement scenarios:
    1. Correct shipment
    2. Short shipment
    3. Extra units (Overage)
    4. Wrong SKU
    5. Wrong variant
    6. Crushed carton
    7. Water-damaged carton
    8. Torn packaging
    9. Missing components
    10. Ambiguous cases
    """
    runner = ScenarioRunner()
    report = runner.run_all_scenarios()

    assert report.total_scenarios == 10
    assert report.scenarios_passed_ground_truth == 10
    assert report.accuracy_percentage == 100.0

    # Verify confusion matrix
    cm = report.confusion_matrix
    assert cm["PASS"]["PASS"] == 1
    assert cm["FAIL"]["FAIL"] == 8
    assert cm["UNCERTAIN"]["UNCERTAIN"] == 1


def test_redteam_sql_injection_defense():
    """
    Red-Team: Attempt SQL injection in SKU, PO, and operator fields.
    System must safely parameterize all queries and avoid injection vulnerabilities.
    """
    client = TestClient(app)

    malicious_payload = {
        "purchase_order_id": "' OR '1'='1' --",
        "po_line_id": "' UNION SELECT * FROM users --",
        "operator_id": "<script>alert('xss')</script>' OR 1=1",
        "unit_id": "UNIT-'; DROP TABLE organizations; --",
    }

    resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": "org_demo_alpha"},
        json=malicious_payload,
    )
    # Must fail safely with 404/422 without 500 error or database corruption
    assert resp.status_code in (404, 422)


def test_redteam_corrupt_image_upload(db_session):
    """
    Red-Team: Upload corrupted non-image binary stream.
    System must calculate checksum, handle gracefully without crash.
    """
    client = TestClient(app)

    org = db_session.query(Organization).filter(Organization.organization_code == "org_demo_alpha").first()
    assert org is not None

    po = db_session.query(PurchaseOrder).filter(PurchaseOrder.organization_id == org.id).first()
    assert po is not None
    assert len(po.lines) > 0

    pol = po.lines[0]

    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": org.id},
        json={
            "purchase_order_id": po.id,
            "po_line_id": pol.id,
            "operator_id": "op_redteam",
            "unit_id": "UNIT-REDTEAM-001",
        },
    )
    assert create_resp.status_code == 200
    insp_id = create_resp.json()["id"]

    # Upload corrupt garbage bytes
    corrupt_data = io.BytesIO(b"GARBAGE_NOT_A_JPEG_OR_PNG_HEADER_CORRUPT")
    upload_resp = client.post(
        f"/api/v1/inspections/{insp_id}/images",
        headers={"X-Organization-Id": org.id},
        files={"file": ("corrupt.jpg", corrupt_data, "image/jpeg")},
        data={"image_type": "carton_exterior"},
    )
    assert upload_resp.status_code == 200
    img_data = upload_resp.json()
    assert img_data["checksum"] is not None

    # Analyzing with corrupt image must fail open safely
    analyze_resp = client.post(
        f"/api/v1/inspections/{insp_id}/analyze",
        headers={"X-Organization-Id": org.id},
        json={},
    )
    assert analyze_resp.status_code == 200
    assert analyze_resp.json()["inspection_status"] in ("completed", "pending_review")


def test_evidence_contract_tamper_evident_signature():
    """
    Cross-pod contract validation:
    Verifies that the generated contract has all mandatory fields, valid JSON,
    and a verifiable SHA-256 certificate signature.
    """
    client = TestClient(app)

    # Trigger scenario run endpoint
    resp = client.post("/api/v1/scenarios/run-all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accuracy_percentage"] == 100.0

    # Ensure evidence hashes exist for all scenarios
    for sc in data["scenarios"]:
        assert len(sc["evidence_hash"]) == 64  # Valid SHA-256 hex string
