#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from recover_v4_embedded_spatial_assets import pixel_digest, recover


def make_image(path: Path, seed: int, size: int = 640) -> None:
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)
    step = 40
    for i in range(0, size, step):
        draw.line((i, 0, i, size), fill="black", width=2)
        draw.line((0, i, size, i), fill="black", width=2)
    draw.rectangle((70 + seed, 90, 260 + seed, 250), outline="black", width=8)
    draw.ellipse((330, 320 + seed, 530, 520 + seed), outline="black", width=7)
    draw.text((35, 35), f"MAP-{seed}", fill="black")
    image.save(path, format="PNG")


def image_pixel_sha(path: Path) -> str:
    return pixel_digest(path.read_bytes())[0]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hmda-v4-recovery-test-") as tmp:
        root = Path(tmp)
        originals = root / "originals"
        originals.mkdir()
        specs = [
            ("HMDA_02", "puzzle", 1, 1),
            ("HMDA_04", "puzzle", 2, 2),
            ("HMDA_02", "solution", 3, 3),
            ("HMDA_04", "solution", 4, 4),
        ]
        source_images: dict[tuple[str, str], Path] = {}
        for source_id, mode, _page, seed in specs:
            path = originals / f"{source_id}_{mode}.png"
            make_image(path, seed)
            source_images[(source_id, mode)] = path

        logo = originals / "tiny_logo.png"
        Image.new("RGB", (64, 64), "black").save(logo, format="PNG")

        pdf = root / "v4-fixture.pdf"
        c = canvas.Canvas(str(pdf), pagesize=(612, 792), pageCompression=1)
        for source_id, mode, page, _seed in specs:
            c.drawString(36, 756, f"{source_id} {mode.upper()} PAGE {page}")
            c.drawImage(ImageReader(str(logo)), 510, 700, width=48, height=48)
            c.drawImage(
                ImageReader(str(source_images[(source_id, mode)])),
                56,
                120,
                width=500,
                height=500,
                preserveAspectRatio=True,
                mask="auto",
            )
            c.showPage()
        c.save()

        master = root / "master.yml"
        master.write_text(
            yaml.safe_dump(
                {
                    "missions": [
                        {"number": 2, "spatial_source_id": "HMDA_02"},
                        {"number": 4, "spatial_source_id": "HMDA_04"},
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        index = root / "page_index.json"
        index.write_text(
            '{\n'
            '  "02_map": 1,\n'
            '  "04_map": 2,\n'
            '  "02_solution": 3,\n'
            '  "04_solution": 4,\n'
            '  "page_count": 4\n'
            '}\n',
            encoding="utf-8",
        )
        expected_pdf_sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        out = root / "recovered"
        manifest = recover(
            pdf_path=pdf,
            master_path=master,
            page_index_path=index,
            output_dir=out,
            expected_pdf_sha256=expected_pdf_sha,
            require_count=2,
            require_page_count=4,
            min_dimension=500,
        )
        assert manifest["recovered_raster_count"] == 4
        assert manifest["method"] == "extract_embedded_png_xobject_no_page_render_no_crop_no_geometry_rebuild"
        for source_id, mode, _page, _seed in specs:
            recovered = out / f"{source_id}_{mode}_original_shigai_relabelled.png"
            assert recovered.is_file()
            assert image_pixel_sha(recovered) == image_pixel_sha(source_images[(source_id, mode)])

        try:
            recover(
                pdf_path=pdf,
                master_path=master,
                page_index_path=index,
                output_dir=root / "wrong-sha",
                expected_pdf_sha256="0" * 64,
                require_count=2,
                require_page_count=4,
                min_dimension=500,
            )
        except ValueError as exc:
            assert "PDF SHA mismatch" in str(exc)
        else:
            raise AssertionError("Recovery must fail closed on wrong source PDF SHA")

    print("PASS: exact embedded V4 spatial recovery contract")


if __name__ == "__main__":
    main()
