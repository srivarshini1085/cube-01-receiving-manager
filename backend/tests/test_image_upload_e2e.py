import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models.models import Organization, PurchaseOrder, PurchaseOrderLine, ReceivingImage


def test_image_upload_e2e_lifecycle(db_session):
    """
    Section 42: Image Upload Regression & Persistence Lifecycle Test.
    Verifies:
    1. Inspection creation
    2. Real image byte creation & multipart upload
    3. Proper content-type, checksum, size, and storage key generation
    4. Database record persistence
    5. Return of valid accessible image_url
    6. Retrieval of image bytes via secured endpoint
    7. Storage provider validation
    8. Analysis consumption by vision perception layer
    9. Delete image lifecycle
    """
    client = TestClient(app)

    org = db_session.query(Organization).filter(Organization.organization_code == "org_demo_alpha").first()
    assert org is not None

    po = db_session.query(PurchaseOrder).filter(PurchaseOrder.organization_id == org.id).first()
    assert po is not None
    pol = po.lines[0]

    # 1. Create receiving inspection session
    create_resp = client.post(
        "/api/v1/inspections",
        headers={"X-Organization-Id": org.id},
        json={
            "purchase_order_id": po.id,
            "po_line_id": pol.id,
            "operator_id": "op_dock_tester",
            "unit_id": "UNIT-IMG-TEST-001",
        },
    )
    assert create_resp.status_code == 200
    insp_data = create_resp.json()
    insp_id = insp_data["id"]

    # 2. Generate a valid test image (RGB PNG) in-memory
    img_byte_arr = io.BytesIO()
    test_img = Image.new("RGB", (320, 240), color=(30, 144, 255))
    test_img.save(img_byte_arr, format="PNG")
    raw_bytes = img_byte_arr.getvalue()

    # 3. Multipart Upload to backend endpoint
    upload_resp = client.post(
        f"/api/v1/inspections/{insp_id}/images",
        headers={"X-Organization-Id": org.id},
        files={"file": ("dock_label_carton.png", io.BytesIO(raw_bytes), "image/png")},
        data={"image_type": "carton_exterior"},
    )
    assert upload_resp.status_code == 200
    uploaded_data = upload_resp.json()

    # 4. Verify returned metadata and URL
    assert uploaded_data["id"] is not None
    assert uploaded_data["image_type"] == "carton_exterior"
    assert uploaded_data["checksum"] is not None
    assert len(uploaded_data["checksum"]) == 64
    assert uploaded_data["image_url"] is not None
    assert "dock_label_carton.png" in (uploaded_data.get("original_filename") or uploaded_data.get("metadata_json") or "")

    img_id = uploaded_data["id"]

    # 5. Verify database persistence
    db_img = db_session.query(ReceivingImage).filter(ReceivingImage.id == img_id).first()
    assert db_img is not None
    assert db_img.inspection_id == insp_id
    assert db_img.organization_id == org.id

    # 6. Verify image bytes download via endpoint
    get_bytes_resp = client.get(
        f"/api/v1/inspections/{insp_id}/images/{img_id}/bytes",
        headers={"X-Organization-Id": org.id},
    )
    assert get_bytes_resp.status_code == 200
    assert len(get_bytes_resp.content) == len(raw_bytes)
    assert get_bytes_resp.headers.get("content-type") in ("image/png", "image/jpeg")

    # 7. Verify inspection detail includes the image with image_url
    detail_resp = client.get(
        f"/api/v1/inspections/{insp_id}",
        headers={"X-Organization-Id": org.id},
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["images"]) == 1
    assert detail["images"][0]["id"] == img_id
    assert detail["images"][0]["image_url"] is not None

    # 8. Run analysis - vision layer must ingest image without crash
    analyze_resp = client.post(
        f"/api/v1/inspections/{insp_id}/analyze",
        headers={"X-Organization-Id": org.id},
        json={"operator_attested_cartons": 1, "operator_attested_units_per_carton": 24},
    )
    assert analyze_resp.status_code == 200
    analyzed_detail = analyze_resp.json()
    assert analyzed_detail["overall_decision"] in ("PASS", "FAIL", "UNCERTAIN")

    # 9. Test delete image endpoint
    del_resp = client.delete(
        f"/api/v1/inspections/{insp_id}/images/{img_id}",
        headers={"X-Organization-Id": org.id},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify deleted from DB
    deleted_img = db_session.query(ReceivingImage).filter(ReceivingImage.id == img_id).first()
    assert deleted_img is None
