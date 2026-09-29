#!/usr/bin/env python3
"""Fail-closed structural and reader-copy audit for the V3 premium interior."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from build_v3_final_text_contract import build_contract
from build_v3_premium_interior import DEFAULT_PDF, paragraphs, plain, sha, split_case


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", plain(value)).lower()
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def substantive_lines(markdown: str) -> list[str]:
    return [value for kind, value in paragraphs(markdown)
            if kind != "heading" and len(norm(value).split()) >= 7]


def audit(pdf: Path, index_path: Path) -> dict:
    source = build_contract()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    reader = PdfReader(str(pdf))
    errors: list[str] = []
    if len(reader.pages) != len(index):
        errors.append("page-index length differs from PDF")
    for i, page in enumerate(reader.pages, 1):
        if tuple(float(v) for v in page.mediabox.upper_right) != (612.0,792.0):
            errors.append(f"page {i} is not 8.5 x 11 in")
        if index[i-1]["physical_page"] != i:
            errors.append(f"page-index physical sequence drift at {i}")
    families = Counter(item["family"] for item in index)
    if families["witness board"] != 15 or families["live case map"] != 15:
        errors.append("missing spatial spread family")
    for item in index:
        if item["family"] == "witness board":
            n = item["physical_page"]
            if n % 2 != 0 or index[n]["family"] != "live case map" or index[n]["case"] != item["case"]:
                errors.append(f"Case {item['case']:02d}: Witness Board/map adjacency or parity failed")
    photos = {item["family"]: item["physical_page"] for item in index if item["family"] in ("photo A", "photo B")}
    if photos.get("photo A", 1) % 2 or photos.get("photo B") != photos.get("photo A", 0)+1:
        errors.append("Case 03 photographs are not adjacent facing left/right pages")
    if len([item for item in index if item["family"] == "solution map"]) != 15:
        errors.append("missing spatial solution maps")
    if len([item for item in index if item["family"] == "solution"]) != 30:
        errors.append("missing Solution Files")
    if len([item for item in index if item["family"] == "front matter"]) != 10:
        errors.append("front matter physical page count drift")
    reverse = [item for item in index if item["side"] == "reverse"]
    if not reverse or any(item["side"] != "reverse" for item in index[reverse[0]["physical_page"]-1:]):
        errors.append("reverse back matter is discontinuous")
    if index[reverse[0]["physical_page"]-2]["family"] != "stop divider":
        errors.append("missing upright STOP divider before reverse back matter")

    page_text = [page.extract_text() or "" for page in reader.pages]
    if any("**" in text for text in page_text):
        errors.append("unrendered Markdown emphasis markers appear in reader PDF")
    all_text = norm(" ".join(page_text))
    checks: list[tuple[str,str]] = []
    for front in source["front_pages"]:
        checks += [(f"front {front['number']:02d}", p) for p in substantive_lines(front["markdown"])]
    for block in source["main_flow"]:
        if block["kind"] == "section":
            checks += [(block["title"], p) for p in substantive_lines(block["markdown"])]
        else:
            number = block["number"]
            _opening, sections = split_case(block["markdown"])
            for name, content in sections.items():
                if name == "PUZZLE / EVIDENCE SURFACE":
                    continue
                checks += [(f"case {number:02d} / {name}", p) for p in substantive_lines(content)]
    for level in ("1", "2", "3"):
        checks += [(f"hint intro {level}", p) for p in substantive_lines(source["hint_intros"][level])]
        for case in source["hint_levels"][level]:
            checks += [(f"hint {level} case {case['number']:02d}", p) for p in substantive_lines(case["markdown"])]
    checks += [("solutions intro", p) for p in substantive_lines(source["solutions_intro"])]
    for case in source["solution_files"]:
        checks += [(f"solution case {case['number']:02d}", p) for p in substantive_lines(case["markdown"])]
    missing = [(label, value[:150]) for label, value in checks if norm(value) not in all_text]
    if missing:
        errors.append(f"{len(missing)} reader-copy fragments not found in PDF extraction")

    required = {
        "page2 welcome": "WE HAVE SAVED A COZY SPOT JUST FOR YOU.",
        "Case01 alias QUILL": "QUILL",
        "Case01 alias MORSE": "MORSE",
        "Case01 alias PIP": "PIP",
        "Case01 alias KNOX": "KNOX",
        "Case05 six symbols": "BALL STAR BOLT HEART KEY MOON",
        "Case21 message": "THE ANSWER IS IN WHAT YOU LEAVE EMPTY",
        "Case26 message": "CHECK THE OLD MAP",
        "Rule Zero": "ZERO ASSUMPTIONS NOTICE FIRST THEORIZE SECOND",
        "Room Zero access": "D3",
        "Book2 heading": "ARCHIVE FILE 001 STILL OPEN",
    }
    for label, phrase in required.items():
        if norm(phrase) not in all_text:
            errors.append(f"missing locked printed invariant: {label}")
    forbidden = ("FOUR SYMBOL", "CASE 001 STILL OPEN", "ONE TINY MISMATCH WILL MATTER LATER")
    for phrase in forbidden:
        if norm(phrase) in all_text:
            errors.append(f"superseded phrase printed: {phrase}")

    report = {
        "status": "PASS" if not errors else "BLOCKED",
        "pdf_sha256": sha(pdf),
        "source_blob_sha1": source["authority"]["blob_sha1"],
        "physical_pages": len(reader.pages),
        "page_families": dict(families),
        "reader_fragments_checked": len(checks),
        "missing_reader_fragments": missing[:100],
        "missing_reader_fragment_count": len(missing),
        "errors": errors,
        "english_frozen": False,
        "kdp_publication_authorized": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    pdf = args.pdf.resolve()
    index = args.index or pdf.with_name(pdf.stem+"_page_index.json")
    report_path = args.report or pdf.with_name(pdf.stem+"_regression.json")
    result = audit(pdf, index)
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"{result['status']}: {result['physical_pages']} pages; "
          f"{result['reader_fragments_checked']} reader fragments; "
          f"{result['missing_reader_fragment_count']} missing")
    for issue in result["errors"]:
        print("ISSUE:", issue)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
