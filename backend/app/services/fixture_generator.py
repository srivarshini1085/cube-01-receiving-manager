import os
import math
from PIL import Image, ImageDraw, ImageFont


def ensure_fixtures_dir(base_dir: str = "fixtures/receiving") -> str:
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def create_base_carton(width: int = 600, height: int = 450, color=(198, 156, 109)) -> Image.Image:
    """Creates a corrugated cardboard carton texture with seam and tape."""
    img = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(img)
    # Cardboard corrugation texture lines
    for y in range(0, height, 4):
        draw.line([(0, y), (width, y)], fill=(188, 146, 99), width=1)
    # Center packaging tape
    draw.rectangle([width // 2 - 25, 0, width // 2 + 25, height], fill=(160, 120, 80))
    # Carton outline
    draw.rectangle([10, 10, width - 10, height - 10], outline=(140, 100, 60), width=3)
    return img


def add_shipping_label(
    img: Image.Image,
    sku: str,
    asin: str,
    po: str,
    qty: int,
    coords=(50, 60, 280, 240),
    is_glared: bool = False,
) -> None:
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = coords
    # White label backing
    draw.rectangle([x1, y1, x2, y2], fill=(245, 245, 245), outline=(50, 50, 50), width=2)
    # Simulated barcode lines
    bx = x1 + 15
    by = y1 + 20
    bw = x2 - x1 - 30
    for i in range(bx, bx + bw, 4):
        bar_w = 2 if (i % 6 == 0 or i % 8 == 0) else 1
        draw.line([(i, by), (i, by + 45)], fill=(0, 0, 0), width=bar_w)

    # Label text
    draw.text((x1 + 15, y1 + 75), f"SKU: {sku}", fill=(10, 10, 10))
    draw.text((x1 + 15, y1 + 95), f"ASIN: {asin}", fill=(30, 30, 30))
    draw.text((x1 + 15, y1 + 115), f"PO: {po} | QTY: {qty}", fill=(30, 30, 30))
    draw.text((x1 + 15, y1 + 135), "CARRIER: INBOUND-EXP", fill=(60, 60, 60))

    if is_glared:
        # Overlay bright glare wash covering barcode
        for r in range(50, 0, -5):
            alpha_color = (255, 255, 255)
            draw.ellipse([x1 + 40 - r, by + 20 - r, x1 + 120 + r, by + 45 + r], fill=alpha_color)


def apply_crush_damage(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Buckled corner crease
    points = [(w - 180, 0), (w, 160), (w - 30, 190), (w - 200, 40)]
    draw.polygon(points, fill=(120, 85, 50))
    for p in range(5):
        draw.line([(w - 190 + p * 15, 0), (w - 20, 170 + p * 5)], fill=(60, 40, 20), width=3)
    draw.text((w - 150, 70), "CRUSH COLLAPSE", fill=(220, 40, 40))


def apply_water_damage(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    # Dark saturated wavy watermark stain
    stain_points = [
        (40, 280), (120, 260), (220, 290), (320, 270), (450, 310),
        (550, 350), (550, 440), (30, 440), (20, 350)
    ]
    draw.polygon(stain_points, fill=(110, 75, 45))
    # Tide line contour
    draw.line(stain_points[:6], fill=(70, 45, 25), width=3)
    draw.text((100, 350), "WATER PENETRATION / STAIN", fill=(200, 230, 255))


def apply_tear_damage(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    # Jagged puncture / rip in packaging tape
    tear_poly = [(270, 160), (290, 140), (330, 210), (310, 250), (260, 220)]
    draw.polygon(tear_poly, fill=(20, 15, 10))
    draw.line([(260, 130), (290, 140), (340, 215), (320, 260)], fill=(230, 210, 190), width=2)
    draw.text((220, 270), "TORN PACKAGING / FLAP PUNCTURE", fill=(255, 230, 100))


def create_product_unit_image(
    product_name: str,
    color_rgb=(30, 100, 220),
    color_name="blue",
    components=("tub", "scoop"),
) -> Image.Image:
    img = Image.new("RGB", (500, 400), (235, 235, 240))
    draw = ImageDraw.Draw(img)
    # Background shadow
    draw.ellipse([80, 310, 420, 360], fill=(200, 200, 205))
    # Main product body
    draw.rounded_rectangle([140, 100, 340, 320], radius=15, fill=color_rgb, outline=(20, 20, 20), width=2)
    draw.text((160, 180), product_name, fill=(255, 255, 255))
    draw.text((160, 210), f"Color: {color_name}", fill=(240, 240, 240))

    # Components
    if "scoop" in components:
        # Draw accessory scoop next to tub
        draw.ellipse([360, 220, 430, 260], fill=(220, 220, 220), outline=(50, 50, 50), width=2)
        draw.line([(395, 260), (430, 330)], fill=(220, 220, 220), width=8)
        draw.text((370, 335), "Scoop", fill=(50, 50, 50))

    if "lid" in components:
        draw.rectangle([130, 80, 350, 105], fill=(50, 50, 50), outline=(20, 20, 20), width=2)

    return img


def generate_all_scenario_fixtures(base_dir: str = "fixtures/receiving") -> dict:
    ensure_fixtures_dir(base_dir)
    generated = {}

    # 1. Correct shipment
    f_c1 = os.path.join(base_dir, "correct_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-TOWEL-BLU", "B0DUMMY600", "PO-7000", 24)
    img.save(f_c1)
    f_c2 = os.path.join(base_dir, "correct_unit_blue.jpg")
    create_product_unit_image("Cotton Bath Towel", (40, 100, 220), "blue", components=["towel"]).save(f_c2)
    generated["correct"] = [f_c1, f_c2]

    # 2. Short shipment
    f_s1 = os.path.join(base_dir, "short_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-BOTTLE-750", "B0DUMMY622", "PO-7002", 24)
    img.save(f_s1)
    generated["short"] = [f_s1]

    # 3. Extra units (Overage)
    f_e1 = os.path.join(base_dir, "extra_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-CANDLE-3", "B0DUMMY964", "PO-7000", 24)
    img.save(f_e1)
    generated["extra"] = [f_e1]

    # 4. Wrong SKU
    f_w1 = os.path.join(base_dir, "wrong_sku_label.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-WRONG-999", "B0DUMMY999", "PO-7000", 24)
    img.save(f_w1)
    generated["wrong_sku"] = [f_w1]

    # 5. Wrong variant
    f_v1 = os.path.join(base_dir, "wrong_variant_red.jpg")
    create_product_unit_image("Cotton Bath Towel", (220, 40, 40), "red", components=["towel"]).save(f_v1)
    generated["wrong_variant"] = [f_v1]

    # 6. Crushed carton
    f_cr1 = os.path.join(base_dir, "crushed_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-PUZZLE-500", "B0DUMMY729", "PO-7000", 48)
    apply_crush_damage(img)
    img.save(f_cr1)
    generated["crushed"] = [f_cr1]

    # 7. Water damaged carton
    f_wt1 = os.path.join(base_dir, "water_damaged_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-LEASH-6FT", "B0DUMMY205", "PO-7001", 12)
    apply_water_damage(img)
    img.save(f_wt1)
    generated["water"] = [f_wt1]

    # 8. Torn packaging
    f_tr1 = os.path.join(base_dir, "torn_carton.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-CABLE-USBC", "B0DUMMY261", "PO-7001", 48)
    apply_tear_damage(img)
    img.save(f_tr1)
    generated["tear"] = [f_tr1]

    # 9. Missing components (Whey Protein: missing scoop)
    f_mc1 = os.path.join(base_dir, "missing_comp_tub_only.jpg")
    create_product_unit_image("Whey Protein 1kg", (240, 230, 200), "vanilla", components=["tub"]).save(f_mc1)
    generated["missing_comp"] = [f_mc1]

    # 10. Ambiguous / Glared label
    f_amb1 = os.path.join(base_dir, "ambiguous_glare_label.jpg")
    img = create_base_carton()
    add_shipping_label(img, "SKU-PUZZLE-500", "B0DUMMY729", "PO-7002", 48, is_glared=True)
    img.save(f_amb1)
    generated["ambiguous"] = [f_amb1]

    return generated
