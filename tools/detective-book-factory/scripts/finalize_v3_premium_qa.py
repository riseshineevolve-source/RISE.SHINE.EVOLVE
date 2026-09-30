#!/usr/bin/env python3
"""Bind the V3 premium interior's source, assets, print and layout checks."""
from __future__ import annotations

import argparse
import json
import itertools
from pathlib import Path

import pdfplumber
from pypdf import PdfReader
from pypdf.generic import ContentStream

from audit_pdf_grayscale import audit_pdf_grayscale
from audit_v3_premium_interior import audit as audit_regression, norm
from build_v3_final_text_contract import build_contract
from build_v3_premium_interior import DEFAULT_PDF, PRINT_DERIVATIVES, ROOT, sha, verify_assets


def check(pdf: Path) -> dict:
    prefix = pdf.with_suffix("")
    index_path = prefix.with_name(prefix.name + "_page_index.json")
    render = json.loads(prefix.with_name(prefix.name + "_QA.json").read_text(encoding="utf-8"))
    spatial = json.loads(prefix.with_name(prefix.name + "_spatial_logic.json").read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    source = build_contract()
    regression = audit_regression(pdf, index_path)
    grayscale = audit_pdf_grayscale(pdf)
    reader = PdfReader(str(pdf))
    errors: list[str] = []
    expected_title = "Happy Makers Detective Academy - The Mystery of Room Zero - Book 1"
    if str(reader.metadata.title or "") != expected_title:
        errors.append("PDF metadata title drift")

    if render["pdf_sha256"] != sha(pdf) or render["errors"]:
        errors.append("renderer result is stale or has overflow errors")
    if regression["status"] != "PASS":
        errors.extend(regression["errors"])
    if grayscale["status"] != "PASS":
        errors.extend(grayscale["errors"])
    if sorted(spatial["cases"]) != sorted(str(n) for n in (2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25, 29)):
        errors.append("spatial solution report has an unexpected case set")
    if any(v["status"] != "PASS" or v["solution_count"] != 1 for v in spatial["cases"].values()):
        errors.append("a locked spatial case does not have a unique verified solution")
    if verify_assets() != render["assets"]:
        errors.append("owner or map asset contract drift")
    derivatives = render.get("derived_print_assets", {})
    if len(derivatives) != 4:
        errors.append("expected four traceable print derivatives")
    for name, record in derivatives.items():
        if sha(ROOT / record["source"]) != record["source_sha256"] or \
                sha(PRINT_DERIVATIVES / name) != record["derivative_sha256"]:
            errors.append(f"print derivative hash drift: {name}")

    # ReportLab registers unused Helvetica as /F1. Inspect text-show operators so
    # the embedding gate applies to fonts actually used to print the book.
    used_font_names: set[str] = set()
    unembedded: set[str] = set()
    for page_number, page in enumerate(reader.pages, 1):
        if [float(page.mediabox.width), float(page.mediabox.height)] != [612.0, 792.0]:
            errors.append(f"page {page_number}: wrong physical size")
        fonts = page["/Resources"]["/Font"].get_object()
        current_font = None
        for operands, operator in ContentStream(page.get_contents(), reader).operations:
            if operator == b"Tf":
                current_font = str(operands[0])
            elif operator in (b"Tj", b"TJ", b"'", b'"') and current_font:
                font = fonts[current_font].get_object()
                name = str(font.get("/BaseFont"))
                used_font_names.add(name)
                descriptor_ref = font.get("/FontDescriptor")
                descriptor = descriptor_ref.get_object() if descriptor_ref else {}
                if not any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                    unembedded.add(name)
    if unembedded:
        errors.append(f"text drawing uses unembedded fonts: {sorted(unembedded)}")

    # Letter pages are no-bleed. Check every glyph and embedded picture against
    # the 30 pt horizontal / 18 pt vertical trim inset.
    unsafe_glyphs: list[dict] = []
    unsafe_images: list[dict] = []
    image_dpi: list[dict] = []
    thin_vector_strokes: list[dict] = []
    with pdfplumber.open(pdf) as document:
        for page_number, page in enumerate(document.pages, 1):
            for glyph in page.chars:
                if glyph["x0"] < 30 or glyph["x1"] > 582 or glyph["top"] < 18 or glyph["bottom"] > 774:
                    unsafe_glyphs.append({"page": page_number, "text": glyph["text"]})
            for picture in page.images:
                if picture["x0"] < 30 or picture["x1"] > 582 or picture["top"] < 18 or picture["bottom"] > 774:
                    unsafe_images.append({"page": page_number, "bbox": [picture[k] for k in ("x0", "top", "x1", "bottom")]})
                src_w, src_h = picture["srcsize"]
                dpi = min(src_w * 72 / picture["width"], src_h * 72 / picture["height"])
                image_dpi.append({"page": page_number, "effective_dpi": round(dpi, 1)})
                if dpi < 300:
                    errors.append(f"page {page_number}: embedded picture is {dpi:.1f} effective DPI")
            for shape in page.lines + page.rects + page.curves:
                width = float(shape.get("linewidth") or 0)
                if 0 < width < 0.849:
                    thin_vector_strokes.append({"page": page_number, "width_pt": width})
    if unsafe_glyphs or unsafe_images:
        errors.append(f"trim inset exceeded: {len(unsafe_glyphs)} glyphs, {len(unsafe_images)} images")
    if thin_vector_strokes:
        errors.append(f"{len(thin_vector_strokes)} vector strokes thinner than 0.85 pt")
    if len(reader.pages) % 2:
        errors.append("odd manuscript page count would create an uncontrolled KDP blank")

    cases = source["main_cases"]
    index_text = norm(reader.pages[9].extract_text())
    title_matches = 0
    for case in cases:
        number = case["number"]
        title = norm(case["title"])
        main_page = next(i["physical_page"] for i in index if i["family"] == "case brief" and i["case"] == number)
        solution_page = next(i["physical_page"] for i in index if i["family"] == "solution" and i["case"] == number)
        if not all(title in text for text in (
            index_text,
            norm(reader.pages[main_page - 1].extract_text()),
            norm(reader.pages[solution_page - 1].extract_text()),
        )):
            errors.append(f"Case {number:02d}: title differs across index, brief, or solution")
        else:
            title_matches += 1

    photo_b = next(i["physical_page"] for i in index if i["family"] == "photo B")
    tracker_count = reader.pages[photo_b - 1].extract_text().count("?")
    if tracker_count != 10:
        errors.append(f"Case 03 tracker has {tracker_count} question marks instead of ten")
    symbols = ("BALL", "STAR", "BOLT", "HEART", "KEY", "MOON")
    six_symbol_solutions = [row for row in itertools.permutations(symbols)
                            if row.index("BOLT") == row.index("STAR") + 1
                            and row.index("BALL") < row.index("STAR")
                            and row.index("HEART") > row.index("BOLT")
                            and row.index("KEY") not in (0, 5)
                            and row.index("MOON") > row.index("KEY")
                            and row.index("MOON") == row.index("HEART") + 2]
    if six_symbol_solutions != [symbols]:
        errors.append("Case 05 printed six-symbol clues no longer have the locked unique answer")
    runtime = json.loads((ROOT / "dist/hmda_spatial_runtime_v4.json").read_text(encoding="utf-8"))
    answers = {int(case["id"].split("_")[1]): case["source_answer"]["display_name"] for case in runtime["cases"]}
    answer_witnesses = 0
    for item in index:
        if item["family"] != "witness board":
            continue
        if norm(answers[item["case"]]) not in norm(reader.pages[item["physical_page"] - 1].extract_text()):
            errors.append(f"Case {item['case']:02d}: answer witness absent from Witness Board")
        else:
            answer_witnesses += 1

    stop_page = next(item["physical_page"] for item in index if item["family"] == "stop divider")
    back_pages = list(range(stop_page + 1, len(reader.pages) + 1))
    bad_orientation = []
    for page_number in back_pages:
        page = reader.pages[page_number - 1]
        whole_page_turn = any(
            operator == b"cm" and [float(value) for value in operands] == [-1, 0, 0, -1, 612, 792]
            for operands, operator in ContentStream(page.get_contents(), reader).operations
        )
        if int(page.get("/Rotate", 0)) % 360 or whole_page_turn or index[page_number-1]["side"] != "upright":
            bad_orientation.append(page_number)
    if bad_orientation:
        errors.append(f"back matter pages are not physically upright: {bad_orientation[:10]}")
    if any(item["physical_side"] != ("verso / left" if item["physical_page"] % 2 == 0 else "recto / right") for item in index):
        errors.append("page-index physical side mismatch")

    return {
        "status": "PASS" if not errors else "BLOCKED",
        "pdf_sha256": sha(pdf),
        "page_count": len(reader.pages),
        "page_size_pt": [612, 792],
        "source_commit": source["authority"]["source_commit"],
        "source_blob_sha1": source["authority"]["blob_sha1"],
        "exact_assets": render["assets"],
        "derived_print_assets": derivatives,
        "print_images": {"count": len(image_dpi), "minimum_effective_dpi": min(v["effective_dpi"] for v in image_dpi),
                         "under_300_dpi": [v for v in image_dpi if v["effective_dpi"] < 300],
                         "source_detail_note": "Lanczos derivatives increase effective print DPI but add no source detail."},
        "vector_lines": {"minimum_required_pt": 0.85, "thin_strokes": thin_vector_strokes[:30]},
        "effective_kdp_page_count": len(reader.pages),
        "used_embedded_fonts": sorted(used_font_names),
        "unused_unembedded_default_font": "/Helvetica" if "/Helvetica" not in used_font_names else None,
        "grayscale": {"status": grayscale["status"], "vector_operators": grayscale["vector_color_operators_checked"], "images": grayscale["embedded_images_checked"]},
        "trim_safety": {"status": "PASS" if not unsafe_glyphs and not unsafe_images else "BLOCKED", "glyphs_outside_inset": len(unsafe_glyphs), "images_outside_inset": len(unsafe_images), "inset_pt": {"horizontal": 30, "vertical": 18}},
        "renderer_overflow_errors": render["errors"],
        "spatial_parity": {"boards_even_left_maps_following_odd_right": regression["status"] == "PASS", "spread_count": 15},
        "spatial_logic": {"status": "PASS" if all(v["status"] == "PASS" and v["solution_count"] == 1 for v in spatial["cases"].values()) else "BLOCKED", "unique_solution_cases": len(spatial["cases"])},
        "case03_tracker_count": tracker_count,
        "case05_unique_six_symbol_answer": list(six_symbol_solutions[0]) if len(six_symbol_solutions) == 1 else None,
        "case05_solution_count": len(six_symbol_solutions),
        "title_matches_index_brief_solution": title_matches,
        "answer_witnesses_on_boards": answer_witnesses,
        "reader_fragments_checked": regression["reader_fragments_checked"],
        "reader_fragments_missing": regression["missing_reader_fragment_count"],
        "upright_back_matter_pages": len(back_pages) - len(bad_orientation),
        "back_matter_page_count": len(back_pages),
        "errors": errors,
        "english_frozen": False,
        "kdp_publication_authorized": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    pdf = parser.parse_args().pdf.resolve()
    report = check(pdf)
    path = pdf.with_name(pdf.stem + "_final_QA.json")
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{report['status']}: {report['page_count']} pages, {report['title_matches_index_brief_solution']} matched titles, {report['case03_tracker_count']} tracker marks")
    for error in report["errors"]:
        print("ISSUE:", error)
    raise SystemExit(0 if report["status"] == "PASS" else 1)
