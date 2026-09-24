#!/usr/bin/env python3
"""Recover exact embedded V4 spatial rasters without redrawing geometry.

This utility is intentionally narrow. It accepts the canonical V4 owner-review
PDF only when its SHA-256 matches the supplied lock, locates the spatial map
pages from the deterministic V4 page index, extracts the largest embedded PNG
XObject on each map/solution page, and writes the raster bytes unchanged.

It never renders/crops PDF pages and never reconstructs Shigai geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import fitz  # PyMuPDF
import yaml
from PIL import Image

LOCKED_V4_PDF_SHA256 = "1b2b908763e76b42321035fb1faf91056bd2a8a1301ea0a2f84944c91287e1cb"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def pixel_digest(data: bytes) -> tuple[str, int, int]:
    with Image.open(io.BytesIO(data)) as image:
        normalized = image.convert("RGB")
        payload = (
            f"RGB:{normalized.width}x{normalized.height}:".encode("ascii")
            + normalized.tobytes()
        )
        return sha256_bytes(payload), normalized.width, normalized.height


def load_master(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    missions = data.get("missions", []) if isinstance(data, dict) else []
    spatial = [m for m in missions if m.get("spatial_source_id")]
    if not spatial:
        raise ValueError("No spatial missions found in master")
    return spatial


def load_page_index(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Page index must be a JSON object")
    return data


def extract_largest_embedded_png(doc: fitz.Document, page_number: int) -> dict:
    if page_number < 1 or page_number > doc.page_count:
        raise ValueError(f"Page {page_number} outside PDF range 1..{doc.page_count}")
    page = doc[page_number - 1]
    seen: set[int] = set()
    candidates: list[dict] = []
    for entry in page.get_images(full=True):
        xref = int(entry[0])
        if xref in seen:
            continue
        seen.add(xref)
        extracted = doc.extract_image(xref)
        data = extracted.get("image", b"")
        ext = str(extracted.get("ext", "")).lower()
        if not data:
            continue
        try:
            pixel_sha, width, height = pixel_digest(data)
        except Exception:
            continue
        candidates.append(
            {
                "xref": xref,
                "ext": ext,
                "bytes": data,
                "byte_sha256": sha256_bytes(data),
                "pixel_sha256": pixel_sha,
                "width": width,
                "height": height,
                "area": width * height,
            }
        )
    if not candidates:
        raise ValueError(f"No embedded image XObjects found on page {page_number}")
    candidates.sort(key=lambda item: (-item["area"], item["xref"]))
    largest = candidates[0]
    same_area = [item for item in candidates if item["area"] == largest["area"]]
    if len(same_area) != 1:
        raise ValueError(
            f"Ambiguous largest embedded image on page {page_number}: "
            f"{[(c['xref'], c['width'], c['height']) for c in same_area]}"
        )
    if largest["ext"] != "png":
        raise ValueError(
            f"Largest embedded image on page {page_number} is {largest['ext']!r}, not PNG; "
            "refusing conversion because recovery must preserve embedded raster bytes"
        )
    if largest["width"] < 500 or largest["height"] < 500:
        raise ValueError(
            f"Largest embedded image on page {page_number} is only "
            f"{largest['width']}x{largest['height']}; refusing likely non-map asset"
        )
    return largest


def recover(
    pdf_path: Path,
    master_path: Path,
    page_index_path: Path,
    output_dir: Path,
    expected_pdf_sha256: str,
    require_count: int = 15,
    require_page_count: int = 145,
    min_dimension: int = 500,
) -> dict:
    pdf_path = pdf_path.resolve()
    master_path = master_path.resolve()
    page_index_path = page_index_path.resolve()
    output_dir = output_dir.resolve()

    actual_pdf_sha = sha256_file(pdf_path)
    if actual_pdf_sha != expected_pdf_sha256:
        raise ValueError(
            f"V4 PDF SHA mismatch: expected {expected_pdf_sha256}, got {actual_pdf_sha}"
        )

    missions = load_master(master_path)
    if len(missions) != require_count:
        raise ValueError(f"Expected {require_count} spatial missions, found {len(missions)}")
    page_index = load_page_index(page_index_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    try:
        if doc.page_count != require_page_count:
            raise ValueError(
                f"Expected {require_page_count} V4 pages, found {doc.page_count}"
            )
        recovered: list[dict] = []
        seen_outputs: set[str] = set()
        for mission in missions:
            number = int(mission["number"])
            source_id = str(mission["spatial_source_id"])
            for mode, index_key in (
                ("puzzle", f"{number:02d}_map"),
                ("solution", f"{number:02d}_solution"),
            ):
                if index_key not in page_index:
                    raise ValueError(f"Missing page-index key {index_key}")
                page_number = int(page_index[index_key])
                item = extract_largest_embedded_png(doc, page_number)
                if item["width"] < min_dimension or item["height"] < min_dimension:
                    raise ValueError(
                        f"Recovered {source_id} {mode} raster is too small: "
                        f"{item['width']}x{item['height']}"
                    )
                filename = f"{source_id}_{mode}_original_shigai_relabelled.png"
                if filename in seen_outputs:
                    raise ValueError(f"Duplicate recovery output {filename}")
                seen_outputs.add(filename)
                target = output_dir / filename
                target.write_bytes(item["bytes"])
                recovered.append(
                    {
                        "case_number": number,
                        "source_id": source_id,
                        "mode": mode,
                        "page": page_number,
                        "page_index_key": index_key,
                        "xref": item["xref"],
                        "width": item["width"],
                        "height": item["height"],
                        "byte_sha256": item["byte_sha256"],
                        "pixel_sha256": item["pixel_sha256"],
                        "output": filename,
                    }
                )
    finally:
        doc.close()

    manifest = {
        "status": "RECOVERED_FROM_EXACT_EMBEDDED_V4_PNG_XOBJECTS",
        "method": "extract_embedded_png_xobject_no_page_render_no_crop_no_geometry_rebuild",
        "source_pdf": str(pdf_path),
        "source_pdf_sha256": actual_pdf_sha,
        "master_sha256": sha256_file(master_path),
        "page_index_sha256": sha256_file(page_index_path),
        "spatial_mission_count": len(missions),
        "recovered_raster_count": len(recovered),
        "expected_raster_count": require_count * 2,
        "recovered": recovered,
    }
    if len(recovered) != require_count * 2:
        raise ValueError(
            f"Expected {require_count * 2} recovered rasters, got {len(recovered)}"
        )
    manifest_path = output_dir / "HMDA_V4_EMBEDDED_SPATIAL_RECOVERY_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--page-index", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--expected-pdf-sha256",
        default=LOCKED_V4_PDF_SHA256,
        help="Fail-closed SHA lock for the exact V4 owner-review PDF",
    )
    parser.add_argument("--require-count", type=int, default=15)
    parser.add_argument("--require-page-count", type=int, default=145)
    parser.add_argument("--min-dimension", type=int, default=500)
    args = parser.parse_args()

    manifest = recover(
        pdf_path=args.pdf,
        master_path=args.master,
        page_index_path=args.page_index,
        output_dir=args.output_dir,
        expected_pdf_sha256=args.expected_pdf_sha256,
        require_count=args.require_count,
        require_page_count=args.require_page_count,
        min_dimension=args.min_dimension,
    )
    print(
        "PASS: recovered "
        f"{manifest['recovered_raster_count']} exact embedded V4 spatial PNGs from locked PDF"
    )


if __name__ == "__main__":
    main()
