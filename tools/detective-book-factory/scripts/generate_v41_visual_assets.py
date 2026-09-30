#!/usr/bin/env python3
"""Generate deterministic external visual assets for HMDA Book 1 V4.1.

This is deliberately not a generative-AI pipeline. Case 03 is a fair-play
spot-the-difference puzzle, so both "photos" are rendered from one shared base
and a hard pixel-delta contract allows only six explicit changes.

Outputs:
- case03_photo_A.png
- case03_photo_B.png
- book2_archive_photo.png
- manifest.json

English is NOT frozen by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _textured_gray(size: tuple[int, int], seed: int, mid: int = 238, noise: int = 7) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    image = Image.new("L", size, mid)
    px = image.load()
    for y in range(h):
        for x in range(w):
            vignette = int(
                10
                * (
                    (x - w / 2) ** 2 / (w / 2) ** 2
                    + (y - h / 2) ** 2 / (h / 2) ** 2
                )
                / 2
            )
            px[x, y] = max(200, min(250, mid + rng.randint(-noise, noise) - vignette))
    return image.filter(ImageFilter.GaussianBlur(0.32))


def _star(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float = 20) -> None:
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.42
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=(58, 58, 58, 255))


def _footprint(angle: float) -> Image.Image:
    image = Image.new("RGBA", (280, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((92, 115, 188, 300), radius=42, fill=(65, 65, 65, 235))
    for y in range(145, 280, 38):
        draw.rectangle((106, y, 174, y + 11), fill=(128, 128, 128, 180))
    for dx, dy, radius in [(-52, 72, 18), (-26, 48, 19), (0, 40, 20), (26, 48, 19), (52, 72, 18)]:
        draw.ellipse(
            (140 + dx - radius, dy - radius, 140 + dx + radius, dy + radius),
            fill=(58, 58, 58, 230),
        )
    return image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)


def _case03_base() -> Image.Image:
    width, height = 1600, 1100
    base = _textured_gray((width, height), 471, 241, 5).convert("RGBA")

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((95, 75, 1505, 1025), radius=38, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    base = Image.alpha_composite(base, shadow)

    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle(
        (75, 55, 1485, 1005), radius=34, fill=(238, 238, 238, 255),
        outline=(42, 42, 42, 255), width=6,
    )
    draw.line((105, 285, 1455, 285), fill=(95, 95, 95, 255), width=4)
    draw.rectangle((1370, 315, 1392, 920), fill=(45, 45, 45, 255))
    draw.rectangle((1398, 315, 1403, 920), fill=(130, 130, 130, 255))

    draw.rounded_rectangle(
        (120, 100, 460, 260), radius=16, fill=(248, 248, 248, 255),
        outline=(80, 80, 80, 255), width=4,
    )
    draw.rounded_rectangle(
        (540, 115, 1060, 245), radius=16, fill=(247, 247, 247, 255),
        outline=(100, 100, 100, 255), width=3,
    )

    parcel_shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    parcel_shadow_draw = ImageDraw.Draw(parcel_shadow)
    parcel_shadow_draw.rounded_rectangle((370, 385, 1090, 755), radius=28, fill=(0, 0, 0, 95))
    parcel_shadow = parcel_shadow.filter(ImageFilter.GaussianBlur(26))
    base = Image.alpha_composite(base, parcel_shadow)

    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle(
        (345, 360, 1065, 730), radius=26, fill=(214, 214, 214, 255),
        outline=(45, 45, 45, 255), width=6,
    )
    for y in range(390, 715, 44):
        draw.line((365, y, 1045, y + 6), fill=(196, 196, 196, 255), width=2)
    for x in range(390, 1035, 75):
        draw.line((x, 380, x + 8, 710), fill=(225, 225, 225, 255), width=1)

    draw.rounded_rectangle(
        (145, 785, 455, 935), radius=15, fill=(250, 250, 250, 255),
        outline=(42, 42, 42, 255), width=5,
    )
    draw.line((168, 830, 432, 830), fill=(120, 120, 120, 255), width=2)

    draw.ellipse((1125, 470, 1265, 610), fill=(246, 246, 246, 255), outline=(50, 50, 50, 255), width=5)
    draw.ellipse((1148, 493, 1242, 587), fill=(200, 200, 200, 255), outline=(82, 82, 82, 255), width=3)

    rng = random.Random(933)
    for _ in range(55):
        x = rng.randint(110, 1450)
        y = rng.randint(80, 990)
        radius = rng.choice([1, 1, 1, 2])
        value = rng.randint(180, 225)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(value, value, value, 255))
    return base


def _case03_variant(base: Image.Image, label: str) -> Image.Image:
    if label not in {"A", "B"}:
        raise ValueError(label)
    image = base.copy()
    draw = ImageDraw.Draw(image)

    # Three harmless decoys.
    star_count = 3 if label == "A" else 4
    for i in range(star_count):
        _star(draw, 185 + i * 70, 180)

    # Material difference 1: parcel knot position.
    knot_x = 500 if label == "A" else 900
    draw.line((345, 545, 1065, 545), fill=(82, 82, 82, 255), width=10)
    draw.line((knot_x, 360, knot_x, 730), fill=(82, 82, 82, 255), width=10)
    draw.arc((knot_x - 80, 505, knot_x + 5, 575), 15, 345, fill=(55, 55, 55, 255), width=8)
    draw.arc((knot_x - 5, 505, knot_x + 80, 575), 195, 165, fill=(55, 55, 55, 255), width=8)
    draw.line((knot_x, 540, knot_x - 48, 612), fill=(55, 55, 55, 255), width=7)
    draw.line((knot_x, 540, knot_x + 48, 612), fill=(55, 55, 55, 255), width=7)

    # Material difference 2: exact tag number.
    number = "0417" if label == "A" else "0471"
    draw.text((225, 850), number, font=_font(52, True), fill=(28, 28, 28, 255))

    # Material difference 3: muddy print points toward the door only in B.
    footprint = _footprint(90 if label == "B" else -90)
    image.alpha_composite(footprint, (1210 - footprint.width // 2, 810 - footprint.height // 2))
    draw = ImageDraw.Draw(image)

    # Harmless decoy: cup handle side.
    if label == "A":
        draw.arc((1245, 500, 1330, 580), 245, 115, fill=(46, 46, 46, 255), width=8)
    else:
        draw.arc((1060, 500, 1145, 580), 65, 295, fill=(46, 46, 46, 255), width=8)

    # Harmless decoy: pencil angle.
    if label == "A":
        draw.line((600, 860, 865, 815), fill=(38, 38, 38, 255), width=13)
        draw.polygon([(865, 815), (895, 808), (870, 835)], fill=(38, 38, 38, 255))
    else:
        draw.line((600, 815, 865, 860), fill=(38, 38, 38, 255), width=13)
        draw.polygon([(865, 860), (895, 867), (870, 840)], fill=(38, 38, 38, 255))
    return image.convert("L")


def _assert_case03_delta_contract(a: Image.Image, b: Image.Image) -> int:
    diff = ImageChops.difference(a, b)
    mask = diff.point(lambda value: 255 if value else 0)
    allowed = Image.new("L", a.size, 0)
    draw = ImageDraw.Draw(allowed)
    for box in [
        (110, 85, 475, 275),      # stars
        (335, 350, 1075, 740),    # parcel knot/twine
        (140, 780, 465, 945),     # tag number
        (1040, 470, 1340, 620),   # cup handle
        (560, 785, 920, 900),     # pencil
        (1020, 645, 1390, 980),   # footprint
    ]:
        draw.rectangle(box, fill=255)

    leak = ImageChops.multiply(mask, ImageOps.invert(allowed))
    if leak.getbbox() is not None:
        raise RuntimeError(f"Case03 uncontrolled pixel delta outside contract: {leak.getbbox()}")

    changed = mask.histogram()[255]
    if changed < 18000:
        raise RuntimeError(f"Case03 delta unexpectedly small: {changed} pixels")
    return changed


def _book2_archive_photo() -> Image.Image:
    width, height = 2000, 920
    art = _textured_gray((width, height), 1601, 236, 7).convert("RGBA")

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle((85, 70, 1915, 850), fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    art = Image.alpha_composite(art, shadow)

    draw = ImageDraw.Draw(art)
    draw.rectangle((60, 45, 1890, 825), fill=(226, 226, 226, 255), outline=(35, 35, 35, 255), width=8)
    draw.rectangle((88, 74, 1862, 795), fill=(188, 188, 188, 255), outline=(85, 85, 85, 255), width=4)
    draw.rounded_rectangle((640, 145, 1360, 735), radius=170, fill=(160, 160, 160, 255), outline=(73, 73, 73, 255), width=6)
    draw.rectangle((110, 605, 1840, 770), fill=(170, 170, 170, 255))
    for y in range(170, 610, 84):
        draw.line((130, y, 1820, y), fill=(148, 148, 148, 255), width=3)

    centers = [360, 650, 1000, 1350, 1640]
    for i, cx in enumerate(centers):
        if i == 2:
            draw.polygon(
                [(905, 245), (1095, 245), (1095, 665), (905, 665)],
                fill=(238, 238, 238, 255), outline=(50, 50, 50, 255),
            )
            for y in range(260, 650, 24):
                offset = 10 if (y // 24) % 2 else -7
                draw.line((905 + offset, y, 922, y + 13), fill=(80, 80, 80, 255), width=3)
                draw.line((1095 - offset, y, 1078, y + 13), fill=(80, 80, 80, 255), width=3)
            continue

        shade = 58 + 10 * (i % 3)
        draw.ellipse((cx - 62, 245, cx + 62, 370), fill=(shade, shade, shade, 255), outline=(40, 40, 40, 255), width=3)
        draw.rectangle((cx - 26, 350, cx + 26, 390), fill=(shade + 8, shade + 8, shade + 8, 255))
        draw.polygon(
            [(cx - 95, 385), (cx + 95, 385), (cx + 125, 650), (cx - 125, 650)],
            fill=(shade + 18, shade + 18, shade + 18, 255), outline=(42, 42, 42, 255),
        )
        draw.line((cx - 60, 395, cx, 495), fill=(130, 130, 130, 255), width=5)
        draw.line((cx + 60, 395, cx, 495), fill=(130, 130, 130, 255), width=5)
        draw.rectangle((cx - 78, 645, cx - 10, 735), fill=(shade + 4, shade + 4, shade + 4, 255))
        draw.rectangle((cx + 10, 645, cx + 78, 735), fill=(shade + 4, shade + 4, shade + 4, 255))
        draw.line((cx - 95, 425, cx - 155, 560), fill=(shade + 12, shade + 12, shade + 12, 255), width=22)
        draw.line((cx + 95, 425, cx + 155, 560), fill=(shade + 12, shade + 12, shade + 12, 255), width=22)
        if i % 2 == 0:
            draw.arc((cx - 62, 238, cx + 62, 360), 180, 355, fill=(25, 25, 25, 255), width=10)
        else:
            draw.line((cx - 58, 270, cx + 50, 255), fill=(25, 25, 25, 255), width=9)

    # Distinct Book 2 visual hook. Narrative text remains vector-rendered by the book builder.
    draw.polygon([(1535, 120), (1665, 355), (1405, 355)], outline=(28, 28, 28, 255), fill=None)
    draw.line((1460, 338, 1620, 145), fill=(35, 35, 35, 255), width=10)
    draw.rectangle((115, 700, 610, 760), fill=(228, 228, 228, 255), outline=(90, 90, 90, 255), width=2)

    rng = random.Random(77)
    for _ in range(130):
        x = rng.randint(95, 1870)
        y = rng.randint(80, 790)
        if rng.random() < 0.65:
            value = rng.choice([120, 140, 205, 218])
            draw.point((x, y), fill=(value, value, value, 255))
        else:
            value = rng.choice([125, 150, 205])
            draw.line(
                (x, y, x + rng.randint(-25, 25), y + rng.randint(8, 38)),
                fill=(value, value, value, 255), width=1,
            )
    return art.convert("L").filter(ImageFilter.GaussianBlur(0.28))


def generate(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    base = _case03_base()
    photo_a = _case03_variant(base, "A")
    photo_b = _case03_variant(base, "B")
    changed_pixels = _assert_case03_delta_contract(photo_a, photo_b)
    photo_a.save(output_dir / "case03_photo_A.png", optimize=True)
    photo_b.save(output_dir / "case03_photo_B.png", optimize=True)

    book2 = _book2_archive_photo()
    book2.save(output_dir / "book2_archive_photo.png", optimize=True)

    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.glob("*.png"))
    }
    manifest = {
        "version": "v4.1",
        "status": "DETERMINISTIC_EXTERNAL_VISUAL_ASSETS",
        "assets": hashes,
        "case03_controlled_differences": {
            "material": [
                "parcel knot position",
                "evidence tag 0417 -> 0471",
                "muddy footprint direction toward the door",
            ],
            "harmless_decoys": [
                "poster star count 3 -> 4",
                "cup handle side",
                "pencil angle",
            ],
            "changed_pixels": changed_pixels,
            "uncontrolled_pixel_deltas_allowed": False,
        },
        "book2_hook": [
            "vintage Academy group photo",
            "one physically cut-out central figure",
            "distinct triangular archival mark",
            "no baked-in narrative text",
        ],
        "english_frozen": False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "cache" / "v41_visual_assets",
    )
    args = parser.parse_args()
    manifest = generate(args.output_dir.resolve())
    print("PASS: deterministic V4.1 visual assets generated")
    for name, sha in manifest["assets"].items():
        print(f"{name}: {sha}")
    print(f"Case03 controlled changed pixels: {manifest['case03_controlled_differences']['changed_pixels']}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
