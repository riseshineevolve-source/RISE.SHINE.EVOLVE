#!/usr/bin/env python3
"""Fail-closed structural and reader-copy audit for the V3 premium interior."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from build_v3_final_text_contract import build_contract
from build_v3_premium_interior import (
    DEFAULT_PDF, paragraphs, plain, project_case_markdown, project_front_markdown,
    project_solution_markdown, sha, split_case,
)

WITNESS_COPY = Path(__file__).resolve().parents[1] / "content/v3_witness_board_copy.json"


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
    stops = [item for item in index if item["family"] == "stop divider"]
    if len(stops) != 1:
        errors.append("expected one STOP divider before the back matter")
    else:
        back_matter = index[stops[0]["physical_page"]:]
        if not back_matter or back_matter[0]["family"] != "hint vault level 1":
            errors.append("Hint Vault does not begin immediately after STOP divider")
        if any(item["side"] != "upright" for item in back_matter):
            errors.append("back matter page marked with non-upright orientation")
        if any(not item["family"].startswith(("hint vault level", "solution"))
               and item["family"] != "closing" for item in back_matter):
            errors.append("unexpected page family in Hint Vault or Solution Files")
        if any(families[f"hint vault level {level}"] < 1 for level in (1, 2, 3)):
            errors.append("one or more Hint Vault levels are missing")

    page_text = [page.extract_text() or "" for page in reader.pages]
    if any("\x00" in text for text in page_text):
        errors.append("missing-font glyph printed in reader PDF")
    if any("**" in text for text in page_text):
        errors.append("unrendered Markdown emphasis markers appear in reader PDF")
    all_text = norm(" ".join(page_text))
    if "story bridge continuation" in all_text:
        errors.append("internal story bridge continuation label printed")

    titles = {case["number"]: case["title"] for case in source["main_cases"]}
    for item in index:
        if item["family"] != "evidence grid interstitial":
            continue
        case_number = item["case"]
        text = norm(page_text[item["physical_page"] - 1])
        spread = "PHOTO A -> PHOTO B" if case_number == 3 else "WITNESS BOARD -> LIVE CASE MAP"
        if norm(titles[case_number]) not in text or norm(spread) not in text:
            errors.append(f"Case {case_number:02d}: interstitial title or spread label drift")
        if norm("FOLLOW THE EVIDENCE. DO NOT GUESS.") in text:
            errors.append(f"Case {case_number:02d}: parity-page filler printed")
        if case_number == 3 and norm("WITNESS BOARD") in text:
            errors.append("Case 03 interstitial still names a Witness Board")

    flow = source["main_flow"]
    meta_titles = (
        "ROOM ZERO THREAD // FOUR MATCHING MARKS",
        "ROOM ZERO THREAD // THE OLD CASES COME BACK",
        "ROOM ZERO // THE EXPLANATION",
    )
    for position, block in enumerate(flow):
        if block["title"] not in meta_titles:
            continue
        start = next((number for number, value in enumerate(page_text, 1)
                      if norm(block["title"]) in norm(value)), None)
        next_title = flow[position + 1]["title"]
        end = next((number for number in range(start + 1, len(page_text) + 1)
                    if norm(next_title) in norm(page_text[number - 1])), None) if start else None
        if start is None or end is None:
            errors.append(f"{block['title']}: section page range missing")
            continue
        region = " ".join(page_text[start - 1:end - 1])
        region_norm = norm(region)
        panel_count = region.count("HAPPY MAKERS // COMMS")
        expected_panels = (2, 3) if block["title"] == "ROOM ZERO // THE EXPLANATION" else (1, 1)
        if not expected_panels[0] <= panel_count <= expected_panels[1]:
            errors.append(f"{block['title']}: expected {expected_panels} COMMS panels, got {panel_count}")
        if norm("HAPPY MAKERS CHAT") in region_norm:
            errors.append(f"{block['title']}: raw chat heading printed")
        cursor = 0
        for kind, beat in paragraphs(block["markdown"]):
            if kind != "bullet":
                continue
            token = norm(beat)
            offset = region_norm.find(token, cursor)
            if offset < 0:
                errors.append(f"{block['title']}: dialogue missing or out of order: {beat[:60]}")
                break
            cursor = offset + len(token)

    case06_comms = [item for item in index if item["family"] == "comms transcript" and item["case"] == 6]
    if len(case06_comms) != 1:
        errors.append("Case 06 must have one intentional COMMS page")
    elif norm("HERITAGE GALLERY // LIVE COMMS") not in norm(page_text[case06_comms[0]["physical_page"] - 1]):
        errors.append("Case 06 COMMS page lacks its reader-facing heading")
    checks: list[tuple[str,str]] = []
    for front in source["front_pages"]:
        checks += [(f"front {front['number']:02d}", p) for p in
                   substantive_lines(project_front_markdown(front["number"], front["markdown"]))]
    for block in source["main_flow"]:
        if block["kind"] == "section":
            checks += [(block["title"], p) for p in substantive_lines(block["markdown"])]
        else:
            number = block["number"]
            _opening, sections = split_case(project_case_markdown(number, block["markdown"]))
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
        checks += [(f"solution case {case['number']:02d}", p) for p in
                   substantive_lines(project_solution_markdown(case["number"], case["markdown"]))]
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
        "Evidence Grid motif": "EVIDENCE GRID",
    }
    for label, phrase in required.items():
        if norm(phrase) not in all_text:
            errors.append(f"missing locked printed invariant: {label}")
    forbidden = (
        "FOUR SYMBOL",
        "CASE 001 STILL OPEN",
        "ONE TINY MISMATCH WILL MATTER LATER",
        "PREP THE EVIDENCE",
        "POSSIBLE LINKS",
    )
    for phrase in forbidden:
        if norm(phrase) in all_text:
            errors.append(f"superseded phrase printed: {phrase}")

    def evidence_text(number: int) -> str:
        return " ".join(page_text[item["physical_page"]-1] for item in index
                        if item["case"] == number and item["family"].startswith("puzzle evidence"))

    wall_text = norm(page_text[8])
    if any(norm(name) not in wall_text for name in
           ("MATCHING MARKS", "MESSAGES / RULES", "CODES / COORDINATES", "OPEN QUESTIONS")):
        errors.append("page 9 Case Wall zones missing")
    if norm("FALSE LEADS") in wall_text or norm("upside down") in wall_text:
        errors.append("page 9 still describes obsolete Case Wall or page orientation")
    intake_page = next(item["physical_page"] for item in index if item["family"] == "intake evidence")
    intake = norm(page_text[intake_page-1])
    if norm("HELPER ROSTER QUILL PIP MORSE KNOX") not in intake:
        errors.append("Case 01 four-candidate roster is missing")
    if intake.count("knox") != 1:
        errors.append("Case 01 must introduce Knox only on the roster")
    if norm("RECRUIT BADGE RECORD 0") not in intake:
        errors.append("Case 01 recruit badge 0 seed is missing")
    for case_number, record in ((2, "TROPHY HALL TAG 0"),
                                (4, "OPEN NIGHT EVIDENCE LABEL 0"),
                                (5, "OLD LOCKER ENVELOPE 0")):
        brief = next(item["physical_page"] for item in index
                     if item["family"] == "case brief" and item["case"] == case_number)
        if norm(record) not in norm(page_text[brief-1]):
            errors.append(f"Case {case_number:02d} pre-Case09 mark seed is missing")

    if "<br/>" in " ".join(page_text):
        errors.append("literal HTML line-break token printed")
    for token in ("zigzag-2", "notch-3", "curve-1"):
        if token in " ".join(page_text):
            errors.append(f"Case 21 renderer edge vocabulary printed: {token}")
    case09 = evidence_text(9)
    if any(norm(token) in norm(case09) for token in
           ("plain Academy", "no Academy mark", "striped circle", "ring with pointer")):
        errors.append("Case 09 symbol classification is printed instead of shown")
    if any(norm(name) not in norm(case09) for name in
           ("RECRUIT BADGE RECORD", "TROPHY HALL TAG", "OPEN NIGHT EVIDENCE LABEL",
            "OLD LOCKER ENVELOPE", "LOOK-TWICE ROUTING FILE", "POSTER DECORATION", "STAGE-LIGHT DIAL")):
        errors.append("Case 09 record labels missing")
    if norm("The 2008 candidate is therefore too late") in norm(evidence_text(16)):
        errors.append("Case 16 evidence reveals the year")
    case26 = evidence_text(26)
    ordered_cases = "02 04 06 07 10 12 13 15 17 19 20 22 23 25"
    if norm(ordered_cases) not in norm(case26):
        errors.append("Case 26 extraction case order missing")
    case27 = norm(evidence_text(27))
    if any(norm(token) not in case27 for token in
           ("OLD PLAN", "CURRENT PLAN", "TRAINING ROOM", "ARCHIVE WALL",
            "C1", "F3", "A5")):
        errors.append("Case 27 overlay visual labels or anchors missing")
    case28 = norm(evidence_text(28))
    if any(norm(token) not in case28 for token in
           ("CLAIM A", "CLAIM B", "CLAIM C", "CLAIM D", "CLAIM E", "CLAIM F",
            "FACT", "THEORY", "UNSUPPORTED ASSUMPTION")):
        errors.append("Case 28 claim cards or three sorting zones missing")
    case30 = norm(evidence_text(30))
    if norm("OFFICIAL CALL SIGN from your Recruit Credential") not in case30:
        errors.append("Case 30 DETECTIVE field does not request the official call sign")
    if norm("The reply is brief: the helper saw no courier") not in all_text:
        errors.append("Case 01 contact reply is not closed before Case 02")
    solution08 = next(item["physical_page"] for item in index
                      if item["family"] == "solution" and item["case"] == 8)
    brief08 = next(item["physical_page"] for item in index
                   if item["family"] == "case brief" and item["case"] == 8)
    case08 = norm(page_text[brief08-1] + evidence_text(8) + page_text[solution08-1])
    if any(norm(phrase) in case08 for phrase in
           ("passes through a wall", "Walls cannot be crossed", "line crosses a wall",
            "or a wall")):
        errors.append("Case 08 claims unsupported wall-crossing logic")
    if any(norm(phrase) not in case08 for phrase in
           ("Route A fails because the Paint Corridor is closed",
            "Route B fails because the Staff Stairs are locked",
            "Route C is the only valid shortcut")):
        errors.append("Case 08 visible restrictions or C verdict drift")
    case24 = norm(evidence_text(24))
    if any(norm(phrase) not in case24 for phrase in
           ("PRINT 1 EAST PATH", "PRINT 4 WEST GATE")):
        errors.append("Case 24 printed endpoint names are missing")
    solution24 = next(item["physical_page"] for item in index
                      if item["family"] == "solution" and item["case"] == 24)
    if norm("EAST PATH -> WEST GATE") not in norm(page_text[solution24-1]):
        errors.append("Case 24 locked answer drift")

    with pdfplumber.open(pdf) as visual_pdf:
        wall = visual_pdf.pages[8]
        wall_shapes = wall.rects + wall.curves
        zone_w = (522-19)/2
        def wall_shapes_of_size(width: float, height: float) -> int:
            return sum(1 for shape in wall_shapes
                       if abs(shape["width"]-width) < 1 and abs(shape["height"]-height) < 1)
        if any(wall_shapes_of_size(zone_w, height) != count for height, count in
               ((150, 1), (178, 1), (120, 2))):
            errors.append("page 9 four writable Case Wall zones are missing")
        if wall_shapes_of_size(29, 29) != 7:
            errors.append("page 9 mark space or six code slots are missing")
        writing_lines = sum(1 for line in wall.lines if abs(line["width"]-(zone_w-24)) < 1)
        if writing_lines < 13:
            errors.append("page 9 lacks the required writing lines")
        def sized_rectangles(number: int, width: float, height: float) -> int:
            pages = [item["physical_page"] for item in index
                     if item["case"] == number and item["family"].startswith("puzzle evidence")]
            return sum(1 for page in pages
                       for shape in visual_pdf.pages[page-1].rects + visual_pdf.pages[page-1].curves
                       if abs(shape["width"]-width) < 1 and abs(shape["height"]-height) < 1)
        if sized_rectangles(26, 40, 31) != 14:
            errors.append("Case 26 must provide exactly fourteen visible letter boxes")
        if sized_rectangles(28, (522-18)/3, 112) != 3:
            errors.append("Case 28 must provide three visible sort zones")
        if sized_rectangles(30, 55, 30) != 6:
            errors.append("Case 30 CODE must provide six visible slots")

    # Reader-facing Witness Boards must use the V3 presentation layer, never raw Shigai crime prose.
    witness_copy = json.loads(WITNESS_COPY.read_text(encoding="utf-8"))
    board_pages = {
        f"{item['case']:02d}": item["physical_page"]
        for item in index if item["family"] == "witness board"
    }
    for case_id, rows in witness_copy["cases"].items():
        board_page = board_pages.get(case_id)
        if board_page is None:
            errors.append(f"Case {case_id}: Witness Board page missing")
            continue
        board_text = norm(page_text[board_page - 1])
        for display_name, clue in rows:
            if norm(display_name) not in board_text:
                errors.append(f"Case {case_id}: Witness Board display name missing on page {board_page}: {display_name}")
            if norm(clue) not in board_text:
                errors.append(f"Case {case_id}: locked Witness Board clue missing on page {board_page}: {clue}")
        for phrase in witness_copy.get("forbidden_reader_words", []):
            if norm(phrase) in board_text:
                errors.append(f"Case {case_id}: raw-source crime wording on Witness Board page {board_page}: {phrase}")
    for phrase in witness_copy.get("forbidden_reader_words", []):
        if norm(phrase) in all_text:
            errors.append(f"raw-source crime wording leaked into reader PDF: {phrase}")

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
