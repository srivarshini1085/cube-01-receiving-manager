import os
import csv
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.models import (
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
)

logger = logging.getLogger(__name__)


def seed_database_from_csv(db: Session, csv_path: str = "data/receiving_sample.csv") -> dict:
    """
    Seeds organizations, products, and purchase orders from reference CSV.
    Guarantees both org_demo_alpha and org_demo_bravo exist with distinct data.
    """
    # 1. Create Organizations
    org_alpha = db.execute(
        select(Organization).where(Organization.organization_code == "org_demo_alpha")
    ).scalar_one_or_none()
    if not org_alpha:
        org_alpha = Organization(organization_code="org_demo_alpha", name="Alpha Logistics 3PL")
        db.add(org_alpha)

    org_bravo = db.execute(
        select(Organization).where(Organization.organization_code == "org_demo_bravo")
    ).scalar_one_or_none()
    if not org_bravo:
        org_bravo = Organization(organization_code="org_demo_bravo", name="Bravo Global Fulfillment")
        db.add(org_bravo)

    db.commit()
    db.refresh(org_alpha)
    db.refresh(org_bravo)

    org_map = {
        "org_demo_alpha": org_alpha.id,
        "org_demo_bravo": org_bravo.id,
    }

    # If CSV exists, parse unique products and POs
    products_created = 0
    pos_created = 0
    lines_created = 0

    if not os.path.exists(csv_path):
        # Fallback to standard location relative to backend if running from backend root
        alt_path = os.path.join("..", csv_path)
        if os.path.exists(alt_path):
            csv_path = alt_path

    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_org = row.get("org_id", "org_demo_alpha").strip()
                org_db_id = org_map.get(raw_org, org_alpha.id)

                sku = row.get("sku", "").strip()
                asin = row.get("asin", "").strip()
                title = row.get("product_title", sku).strip()
                colour = row.get("spec_colour", "").strip()
                variant = row.get("spec_variant", "").strip()
                components = row.get("spec_components", "").strip()
                upc = int(row.get("units_per_carton_ordered", 1) or 1)

                # Ensure product exists
                prod_stmt = select(Product).where(
                    and_(Product.organization_id == org_db_id, Product.sku == sku)
                )
                product = db.execute(prod_stmt).scalar_one_or_none()
                if not product:
                    product = Product(
                        organization_id=org_db_id,
                        sku=sku,
                        asin=asin,
                        name=title,
                        description=f"Standard catalogue entry for {title}",
                        expected_colour=colour,
                        expected_variant=variant,
                        expected_components=components,
                        units_per_carton=upc,
                        is_active=True,
                    )
                    db.add(product)
                    db.commit()
                    db.refresh(product)
                    products_created += 1

                # Ensure PO exists
                po_num = row.get("po_number", "PO-7000").strip()
                supplier = row.get("supplier", "Standard Supplier").strip()
                po_stmt = select(PurchaseOrder).where(
                    and_(PurchaseOrder.organization_id == org_db_id, PurchaseOrder.po_number == po_num)
                )
                po = db.execute(po_stmt).scalar_one_or_none()
                if not po:
                    po = PurchaseOrder(
                        organization_id=org_db_id,
                        po_number=po_num,
                        supplier=supplier,
                        status="open",
                    )
                    db.add(po)
                    db.commit()
                    db.refresh(po)
                    pos_created += 1

                # Ensure PO Line exists
                line_stmt = select(PurchaseOrderLine).where(
                    and_(
                        PurchaseOrderLine.organization_id == org_db_id,
                        PurchaseOrderLine.purchase_order_id == po.id,
                        PurchaseOrderLine.sku == sku,
                    )
                )
                po_line = db.execute(line_stmt).scalar_one_or_none()
                if not po_line:
                    qty = int(row.get("qty_ordered", 24) or 24)
                    cartons = int(row.get("cartons_ordered", 1) or 1)
                    po_line = PurchaseOrderLine(
                        organization_id=org_db_id,
                        purchase_order_id=po.id,
                        product_id=product.id,
                        sku=sku,
                        expected_quantity=qty,
                        expected_cartons=cartons,
                        expected_units_per_carton=upc,
                        expected_colour=colour,
                        expected_variant=variant,
                        expected_components=components,
                    )
                    db.add(po_line)
                    db.commit()
                    lines_created += 1

    return {
        "status": "success",
        "organizations": ["org_demo_alpha", "org_demo_bravo"],
        "products_created": products_created,
        "purchase_orders_created": pos_created,
        "po_lines_created": lines_created,
    }
