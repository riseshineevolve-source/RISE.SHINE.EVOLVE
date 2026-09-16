#!/usr/bin/env python3
"""HYBRID HMDA Map Factory pilot: Shigai original art + HMDA book framing.

This does NOT redraw geometry, furniture, or room boundaries. It places the
original, verified Shigai puzzle/solution page image (extracted losslessly
from the source PDF, never re-generated or upscaled) as the hero visual, and
adds only HMDA branding chrome around it using the same palette/typography
helpers as render_book.py. This is an alternative to (not a replacement of)
scripts/render_spatial_map.py, the validated code-drawn fallback renderer.

Usage:
    python scripts/render_spatial_map_hybrid.py --manifest content/spatial_map_pilots.yml \
        --case HMDA_10 --case HMDA_17 --out dist/spatial_maps_hybrid
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz
import yaml
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as canvas_module
from PIL import Image

HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]
sys.path.insert(0, str(TOOL_ROOT))
import render_book as rb  # noqa: E402

# Exact source mapping, confirmed by content match against
# content/spatial_map_pilots.yml (rooms, furniture, placements, answer) --
# see the pilot's completion report for the page-by-page verification.
SOURCE_PDF = (r"C:\Users\danie\Desktop\Asia\KDP\detective adventure"
              r"\HMDA_RECOVERY_11_CANDIDATES\HMDA_SHIGAI_SOURCE_15_MODULES_FINAL.pdf")

SOURCE_PAGES = {
    "HMDA_10": {"puzzle": 12, "solution": 46},
    "HMDA_17": {"puzzle": 20, "solution": 50},
}


EXISTING_PILOT_CACHE = TOOL_ROOT / "dist" / "spatial_maps_hybrid" / "_source_cache"


def extract_source_images(cache_dir: Path) -> dict[str, dict[str, Path]]:
    """Reuse the already-extracted full-page source JPEGs; only pull from the
    31 MB source PDF again if a case/mode is missing from every known cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, dict[str, Path]] = {}
    missing: list[tuple[str, str]] = []
    for case_id, pages in SOURCE_PAGES.items():
        paths[case_id] = {}
        for mode in pages:
            existing = sorted(cache_dir.glob(f"{case_id}_{mode}_source.*"))
            if not existing:
                existing = sorted(EXISTING_PILOT_CACHE.glob(f"{case_id}_{mode}_source.*"))
            if existing:
                src = existing[0]
                dst = cache_dir / src.name
                if src != dst:
                    dst.write_bytes(src.read_bytes())
                paths[case_id][mode] = dst
            else:
                missing.append((case_id, mode))

    if missing:
        doc = fitz.open(SOURCE_PDF)
        for case_id, mode in missing:
            page_no = SOURCE_PAGES[case_id][mode]
            page = doc[page_no - 1]
            info = page.get_image_info(xrefs=True)
            if len(info) != 1:
                raise SystemExit(
                    f"Expected exactly one image on page {page_no} for {case_id} {mode}, found {len(info)}."
                )
            xref = info[0]["xref"]
            base = doc.extract_image(xref)
            out_path = cache_dir / f"{case_id}_{mode}_source.{base['ext']}"
            out_path.write_bytes(base["image"])
            paths[case_id][mode] = out_path
    return paths


def autocrop_whitespace(img: Image.Image, pad_frac: float = 0.012, thresh: int = 245) -> Image.Image:
    """Trim blank page margin around the printed content only. Never touches
    a pixel inside the detected content box, so puzzle-relevant art, room
    labels, and the legend baked into the source page are preserved exactly."""
    mask = img.convert("L").point(lambda v: 255 if v < thresh else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    pad_x = int(img.width * pad_frac)
    pad_y = int(img.height * pad_frac)
    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(img.width, right + pad_x)
    bottom = min(img.height, bottom + pad_y)
    return img.crop((left, top, right, bottom))


def trim_source_images(images: dict[str, dict[str, Path]], cache_dir: Path) -> dict[str, dict[str, Path]]:
    """Derive whitespace-trimmed copies used for layout only; the extracted
    originals in the cache are left byte-for-byte untouched."""
    trimmed: dict[str, dict[str, Path]] = {}
    for case_id, modes in images.items():
        trimmed[case_id] = {}
        for mode, src_path in modes.items():
            out_path = cache_dir / f"{case_id}_{mode}_trimmed.png"
            with Image.open(src_path) as img:
                autocrop_whitespace(img).save(out_path)
            trimmed[case_id][mode] = out_path
    return trimmed


def name_legend(case: dict) -> list[tuple[str, str, bool]]:
    """Return (initial, full display name, is_answer) for each suspect."""
    entries = []
    for person in case["people"]:
        initial = person["display_name"][0].upper()
        is_answer = person["id"] == case["answer"]["person_id"]
        entries.append((initial, person["display_name"], is_answer))
    return entries


ROW_H = 0.32 * inch
GAP_IMG_TO_LEGEND = 0.22 * inch
GAP_LEGEND_TO_VERDICT = 0.20 * inch
VERDICT_H = 0.40 * inch
GAP_VERDICT_TO_FOOTER = 0.14 * inch


def hybrid_page(c, case: dict, image_path: Path, mode: str) -> None:
    M = rb.M
    is_solution = mode == "solution"
    # No production/debug label or raw case ID here -- the reader-facing
    # title and difficulty badge are already part of the original Shigai
    # page art being placed below, so the top bar only needs the section name.
    rb.top_bar(c, "SOLVED" if is_solution else "DEDUCTION GRID")
    y = rb.PAGE_H - 0.62 * inch

    img = Image.open(image_path)
    iw, ih = img.size
    aspect = iw / ih

    footer_reserve = 0.40 * inch
    legend_reserve = 0.0
    entries: list[tuple[str, str, bool]] = []
    if is_solution:
        entries = name_legend(case)
        rows = (len(entries) + 1) // 2
        legend_reserve = (GAP_IMG_TO_LEGEND + rows * ROW_H + GAP_LEGEND_TO_VERDICT
                           + VERDICT_H + GAP_VERDICT_TO_FOOTER)
    available_h = y - footer_reserve - legend_reserve
    available_w = rb.PAGE_W - 2 * M

    draw_w = available_w
    draw_h = draw_w / aspect
    if draw_h > available_h:
        draw_h = available_h
        draw_w = draw_h * aspect

    x = (rb.PAGE_W - draw_w) / 2
    top_of_image = y
    y_img = top_of_image - draw_h
    rb.box(c, x - 0.06 * inch, y_img - 0.06 * inch, draw_w + 0.12 * inch, draw_h + 0.12 * inch,
           fill=rb.WHITE, stroke=rb.LINE, radius=10)
    c.drawImage(str(image_path), x, y_img, width=draw_w, height=draw_h,
                preserveAspectRatio=True, anchor='c')

    if is_solution:
        ly = y_img - GAP_IMG_TO_LEGEND
        colw = (rb.PAGE_W - 2 * M) / 2
        c.setFont(rb.BOLD, 11.5)
        for i, (initial, name, is_answer) in enumerate(entries):
            col, row = i % 2, i // 2
            lx = M + col * colw
            top = ly - row * ROW_H
            c.setFillColor(rb.BLACK)
            label = f"{initial} = {name}"
            c.drawString(lx, top, label)
            if is_answer:
                label_w = rb.pdfmetrics.stringWidth(label, rb.BOLD, 11.5)
                rb.pill(c, "ANSWER", lx + label_w + 0.14 * inch, top - 3.2,
                        font_size=7.6, fill=rb.BLACK, text_color=rb.WHITE, pad_x=8, h=15)

        rows = (len(entries) + 1) // 2
        answer_name = case["answer"]["source_identity"]
        answer_coord = case["answer"]["coordinate"]
        verdict_top = ly - rows * ROW_H - GAP_LEGEND_TO_VERDICT
        rb.box(c, M, verdict_top - VERDICT_H, rb.PAGE_W - 2 * M, VERDICT_H,
               fill=rb.BLACK, stroke=rb.BLACK, radius=9)
        c.setFillColor(rb.WHITE)
        c.setFont(rb.BOLD, 12.5)
        c.drawCentredString(rb.PAGE_W / 2, verdict_top - VERDICT_H / 2 - 4.3,
                             f"VERDICT: {answer_name.upper()} — {answer_coord}")

    rb.footer(c)
    c.showPage()


def render_case(case: dict, images: dict[str, Path], out_dir: Path) -> Path:
    pdf_path = out_dir / f"{case['id']}_hybrid.pdf"
    c = canvas_module.Canvas(str(pdf_path), pagesize=(rb.PAGE_W, rb.PAGE_H))
    hybrid_page(c, case, images["puzzle"], "puzzle")
    hybrid_page(c, case, images["solution"], "solution")
    c.save()
    return pdf_path


def rasterize(pdf_path: Path, out_dir: Path, case_id: str, dpi: int = 300) -> tuple[Path, Path]:
    doc = fitz.open(pdf_path)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    names = (f"{case_id}_hybrid_puzzle.png", f"{case_id}_hybrid_solution.png")
    outputs = []
    for page, name in zip(doc, names):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = out_dir / name
        pix.save(out_path)
        outputs.append(out_path)
    return outputs[0], outputs[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="content/spatial_map_pilots.yml")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--out", default="dist/spatial_maps_hybrid_final")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = TOOL_ROOT / manifest_path
    document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in document["pilots"]}
    requested = args.case or [cid for cid in SOURCE_PAGES if cid in cases]

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = TOOL_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "_source_cache"

    all_images = extract_source_images(cache_dir)
    all_images = trim_source_images(all_images, cache_dir)

    for case_id in requested:
        if case_id not in SOURCE_PAGES:
            raise SystemExit(f"No confirmed source page mapping for {case_id}.")
        case = cases[case_id]
        pdf_path = render_case(case, all_images[case_id], out_dir)
        puzzle_png, solution_png = rasterize(pdf_path, out_dir, case_id, dpi=args.dpi)
        print(f"{case_id}: {pdf_path.relative_to(TOOL_ROOT)}, "
              f"{puzzle_png.relative_to(TOOL_ROOT)}, {solution_png.relative_to(TOOL_ROOT)}")


if __name__ == "__main__":
    main()
