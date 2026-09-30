#!/usr/bin/env python3
"""Make traceable print derivatives without changing locked owner originals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "assets/production/v3_owner_locked"
OUTPUT = ROOT / "dist/v3_print_derivatives"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        Path("C:/Windows/Fonts/georgiab.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    ):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("A Georgia or DejaVu Serif Bold font is required for the archive sign")


def archive_branding(source: Image.Image) -> Image.Image:
    """Replace only the two noncanonical nameplates in the approved photograph."""
    if source.size != (1086, 1448):
        raise ValueError("archive photograph source geometry drift")
    image = source.convert("RGB").copy()
    draw = ImageDraw.Draw(image)
    # Building sign: the original inscription occupied this existing nameplate.
    draw.rectangle((439, 267, 690, 325), fill=(70, 64, 58), outline=(38, 35, 32), width=2)
    draw.text((565, 296), "OLD ACADEMY", font=font(22), anchor="mm", fill=(206, 190, 165))
    # Handwritten footer signature: replace its name/date in the same corner.
    draw.rectangle((824, 1347, 1070, 1430), fill=(194, 179, 155), outline=(99, 87, 73), width=2)
    draw.text((947, 1388), "OLD ACADEMY", font=font(22), anchor="mm", fill=(57, 48, 43))
    return image


def prepare() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    specs = (
        (OWNER / "case03_photo_A.png", "case03_photo_A_print.png", 1.5),
        (OWNER / "case03_photo_B.png", "case03_photo_B_print.png", 1.5),
        (ROOT / "assets/production/squad-scanner.png", "squad_scanner_print.png", 1.1),
    )
    derivatives: dict[str, dict] = {}
    for source_path, output_name, factor in specs:
        with Image.open(source_path) as source:
            width, height = source.size
            image = source.convert("RGB").resize(
                (round(width * factor), round(height * factor)), Image.Resampling.LANCZOS
            )
        output_path = OUTPUT / output_name
        image.save(output_path, format="PNG", optimize=False)
        derivatives[output_name] = {
            "source": str(source_path.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": sha(source_path),
            "source_pixels": [width, height],
            "derivative_sha256": sha(output_path),
            "derivative_pixels": list(image.size),
            "method": f"Pillow Lanczos {factor:g}x; approved composition unchanged; no new source detail",
        }
    archive_source = OWNER / "book2_archive_photo.png"
    with Image.open(archive_source) as source:
        archive = archive_branding(source)
        archive_pixels = list(source.size)
    archive_output = OUTPUT / "book2_archive_photo_canon_print.png"
    archive.save(archive_output, format="PNG", optimize=False)
    derivatives[archive_output.name] = {
        "source": str(archive_source.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha(archive_source),
        "source_pixels": archive_pixels,
        "derivative_sha256": sha(archive_output),
        "derivative_pixels": list(archive.size),
        "method": "Two bounded nameplate replacements; all other owner pixels unchanged",
    }
    manifest = {"status": "PASS", "derivatives": derivatives}
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    result = prepare()
    print(json.dumps(result, indent=2))
