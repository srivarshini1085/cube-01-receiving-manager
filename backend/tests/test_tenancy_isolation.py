import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import Organization, Product, PurchaseOrder, PurchaseOrderLine, ReceivingInspection, ReceivingImage


@pytest.fixture(scope="module")
def setup_tenancy_data(db_session):
    # Create Org Alpha and Org Bravo
    org_a = db_session.query(Organization).filter(Organization.organization_code == "org_demo_alpha").first()
    if not org_a:
        org_a = Organization(id="org_alpha_id", organization_code="org_demo_alpha", name="Alpha Logistics")
        db_session.add(org_a)
        db_session.commit()

    org_b = db_session.query(Organization).filter(Organization.organization_code == "org_demo_bravo").first()
    if not org_b:
        org_b = Organization(id="org_bravo_id", organization_code="org_demo_bravo", name="Bravo Fulfillment")
        db_session.add(org_b)
        db_session.commit()

    # Create an Alpha-only inspection
    prod_a = db_session.query(Product).filter(Product.organization_id == org_a.id).first()
    po_a = db_session.query(PurchaseOrder).filter(PurchaseOrder.organization_id == org_a.id).first()
    pol_a = db_session.query(PurchaseOrderLine).filter(PurchaseOrderLine.organization_id == org_a.id).first()

    insp_a = ReceivingInspection(
        id="insp_alpha_secret",
        organization_id=org_a.id,
        purchase_order_id=po_a.id if po_a else "po_a",
        po_line_id=pol_a.id if pol_a else "pol_a",
        sku="SKU-ALPHA-100",
        inspection_status="completed",
        overall_decision="PASS",
    )
    db_session.add(insp_a)
    db_session.commit()

    img_a = ReceivingImage(
        id="img_alpha_confidential",
        organization_id=org_a.id,
        inspection_id="insp_alpha_secret",
        file_reference="fixtures/receiving/correct_carton.jpg",
        image_type="carton_exterior",
        checksum="dummy_checksum_alpha",
    )
    db_session.add(img_a)
    db_session.commit()

    return {"org_a": org_a.id, "org_b": org_b.id}


def test_tenancy_isolation_inspections(setup_tenancy_data):
    """Rule 1: Org Bravo must not see Org Alpha's inspections."""
    client = TestClient(app)
    org_a_id = setup_tenancy_data["org_a"]
    org_b_id = setup_tenancy_data["org_b"]

    resp_a = client.get("/api/v1/inspections", headers={"X-Organization-Id": org_a_id})
    assert resp_a.status_code == 200
    alpha_ids = [i["id"] for i in resp_a.json()]
    assert "insp_alpha_secret" in alpha_ids

    # Org Bravo requests inspections -> sees ZERO rows for Alpha
    resp_b = client.get("/api/v1/inspections", headers={"X-Organization-Id": org_b_id})
    assert resp_b.status_code == 200
    bravo_ids = [i["id"] for i in resp_b.json()]
    assert "insp_alpha_secret" not in bravo_ids


def test_tenancy_isolation_direct_key_guessing_denied(setup_tenancy_data):
    """Rule 1: Org Bravo cannot view Org Alpha's inspection even by guessing the inspection_id."""
    client = TestClient(app)
    org_b_id = setup_tenancy_data["org_b"]

    resp = client.get(
        "/api/v1/inspections/insp_alpha_secret",
        headers={"X-Organization-Id": org_b_id},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_tenancy_isolation_image_asset_protection(setup_tenancy_data):
    """Rule 1: Org Bravo cannot download Org Alpha's photo asset even by guessing image_id."""
    client = TestClient(app)
    org_b_id = setup_tenancy_data["org_b"]

    resp = client.get(
        "/api/v1/inspections/insp_alpha_secret/images/img_alpha_confidential/bytes",
        headers={"X-Organization-Id": org_b_id},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower() or "access denied" in resp.json()["detail"].lower()
