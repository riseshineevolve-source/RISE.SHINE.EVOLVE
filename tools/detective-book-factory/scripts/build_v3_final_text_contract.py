#!/usr/bin/env python3
"""Build a lossless machine-readable contract from the exact Detective V3 final text.

The contract is an integration seam, not a renderer and not an evidence generator.
It preserves exact Markdown blocks from the owner-authorized V3 source so a
production renderer can consume current reader copy without resurrecting
historical V4/V4.1 prose. Visual/evidence assets remain separate source-backed
inputs and are never reconstructed here.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import verify_v3_final_text_source as source_verify

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "DETECTIVE_ACADEMY_BOOK1_TEXT_GOLD_MASTER_V3.md"
DEFAULT_OUTPUT = ROOT / "dist" / "book1_v3_final_text_contract.json"


def _between(text: str, start: str, end: str | None) -> str:
    if start not in text:
        raise ValueError(f"missing start marker: {start}")
    value = text.split(start, 1)[1]
    if end is not None:
        if end not in value:
            raise ValueError(f"missing end marker after {start}: {end}")
        value = value.split(end, 1)[0]
    return value


def _blocks(section: str, pattern: str) -> list[dict]:
    matches = list(re.finditer(pattern, section, flags=re.MULTILINE))
    blocks: list[dict] = []
    for index, match in enumerate(matches):
        start = match.start()
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        blocks.append({
            "number": int(match.group("number")),
            "title": (match.groupdict().get("title") or "").strip(),
            "markdown": section[start:stop].rstrip() + "\n",
        })
    return blocks


def _front_pages(front: str) -> list[dict]:
    # Canonical V3 keeps production page labels only on the first three pages.
    # The remaining seven section titles are the reader-facing page markers.
    markers = (
        r"## PAGE 1 // TITLE + THE UNEXPLAINED SLOT",
        r"## PAGE 2 // PUBLICATION RECORD",
        r"## PAGE 3 // THE BLACK ENVELOPE",
        r"## YOUR SQUAD",
        r"## CLAIM YOUR RECRUIT CREDENTIAL",
        r"## WHAT YOU ARE ABOUT TO WALK INTO",
        r"## HOW EVERY CASE WORKS",
        r"## MAP CASES — READ THIS ONCE",
        r"## YOUR CASE WALL + HINT VAULT",
        r"## CASE INDEX",
    )
    matches = []
    for number, marker in enumerate(markers, 1):
        found = list(re.finditer(r"^" + re.escape(marker) + r"$", front, re.MULTILINE))
        if len(found) != 1:
            raise ValueError(f"V3 front page {number} marker missing or duplicated: {marker}")
        matches.append(found[0])
    if [match.start() for match in matches] != sorted(match.start() for match in matches):
        raise ValueError("V3 front page markers are out of order")
    if len(re.findall(r"^## ", front, re.MULTILINE)) != len(markers):
        raise ValueError("V3 front matter contains an unexpected page section")
    return [
        {
            "number": number,
            "title": marker[3:],
            "markdown": front[match.start():matches[number].start() if number < len(matches) else len(front)].rstrip() + "\n",
        }
        for number, (marker, match) in enumerate(zip(markers, matches), 1)
    ]


def _cases(main: str) -> list[dict]:
    blocks = _blocks(
        main,
        r"^## CASE (?P<number>\d{2}) // (?P<title>.+)$",
    )
    for block in blocks:
        raw = block["markdown"]
        status = re.search(r"^\*\*STATUS:\*\*\s*(.+?)\s*$", raw, flags=re.MULTILINE)
        rank = re.search(r"^\*\*RANK:\*\*\s*(.+?)\s*$", raw, flags=re.MULTILINE)
        block["status"] = status.group(1).strip() if status else None
        block["rank"] = rank.group(1).strip() if rank else None
        block["evidence_hydration_marker_present"] = "### PUZZLE / EVIDENCE SURFACE" in raw
    return blocks


def _support_cases(section: str) -> list[dict]:
    return _blocks(
        section,
        r"^## CASE (?P<number>\d{2})(?: // (?P<title>.+))?$",
    )


def _support_intro(section: str) -> str:
    match = re.search(r"^## CASE 01", section, flags=re.MULTILINE)
    if match is None:
        raise ValueError("support section lacks Case 01")
    return section[:match.start()].strip() + "\n"


def _ordered_main_flow(section: str) -> list[dict]:
    """Keep act gates, Room Zero threads and cases in their source order."""
    matches = list(re.finditer(r"^(?:# (?!#)(?P<section>.+)|## CASE (?P<number>\d{2}) // (?P<title>.+))$", section, re.MULTILINE))
    blocks = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        blocks.append({
            "kind": "case" if match.group("number") else "section",
            "number": int(match.group("number")) if match.group("number") else None,
            "title": match.group("title") or match.group("section"),
            "markdown": section[match.start():stop].rstrip() + "\n",
        })
    if [item["number"] for item in blocks if item["kind"] == "case"] != list(range(1, 31)):
        raise ValueError("ordered V3 main flow lost or reordered a case")
    return blocks


def build_contract() -> dict:
    verified = source_verify.verify()
    text = SOURCE.read_text(encoding="utf-8")

    front = _between(
        text,
        "# FRONT MATTER // LOCKED READER PAGES 1-10",
        "# ACT 1 // SOMETHING IS OFF",
    )
    main = "# ACT 1 // SOMETHING IS OFF" + _between(text, "# ACT 1 // SOMETHING IS OFF", "# HINT VAULT // LEVEL 1")
    level1 = _between(text, "# HINT VAULT // LEVEL 1", "# HINT VAULT // LEVEL 2")
    level2 = _between(text, "# HINT VAULT // LEVEL 2", "# HINT VAULT // LEVEL 3")
    level3 = _between(text, "# HINT VAULT // LEVEL 3", "# SOLUTION FILES")
    solutions = _between(text, "# SOLUTION FILES", "# EDITORIAL LOCKS // NOT PRINTED")

    front_pages = _front_pages(front)
    cases = _cases(main)
    main_flow = _ordered_main_flow(main)
    ordered_cases = {item["number"]: item for item in main_flow if item["kind"] == "case"}
    for case in cases:
        case["markdown"] = ordered_cases[case["number"]]["markdown"]
    hint_levels = {
        "1": _support_cases(level1),
        "2": _support_cases(level2),
        "3": _support_cases(level3),
    }
    solution_cases = _support_cases(solutions)

    expected_pages = list(range(1, 11))
    if [item["number"] for item in front_pages] != expected_pages:
        raise ValueError("V3 front matter must contain locked reader pages 1-10 exactly once")
    expected_cases = list(range(1, 31))
    if [item["number"] for item in cases] != expected_cases:
        raise ValueError("V3 main flow must contain Cases 01-30 exactly once")
    for level, items in hint_levels.items():
        if [item["number"] for item in items] != expected_cases:
            raise ValueError(f"V3 Hint Vault Level {level} must contain Cases 01-30 exactly once")
    if [item["number"] for item in solution_cases] != expected_cases:
        raise ValueError("V3 Solution Files must contain Cases 01-30 exactly once")

    return {
        "schema": "hmda-v3-final-text-contract-v1",
        "status": "FINAL_TEXT_SOURCE_PARSED_RENDERER_WIRING_PENDING",
        "authority": {
            "source_path": verified["source"],
            "source_commit": verified["source_commit"],
            "blob_sha1": verified["blob_sha1"],
            "version_family": "V3",
            "english_frozen": False,
        },
        "policy": {
            "reader_copy_authority": "exact_v3_markdown_blocks",
            "evidence_authority": "separate_locked_source_assets",
            "reconstruct_evidence_from_prose": False,
            "force_historical_page_count": False,
            "merge_main_authorized": False,
            "kdp_publication_authorized": False,
        },
        "front_pages": front_pages,
        "main_flow": main_flow,
        "main_cases": cases,
        "hint_levels": hint_levels,
        "hint_intros": {
            "1": _support_intro(level1),
            "2": _support_intro(level2),
            "3": _support_intro(level3),
        },
        "solutions_intro": _support_intro(solutions),
        "solution_files": solution_cases,
        "regression_contract": {
            "case01_reader_aliases": ["QUILL", "MORSE", "PIP", "KNOX"],
            "case03_difference_count": 10,
            "case05_answer": ["BALL", "STAR", "BOLT", "HEART", "KEY", "MOON"],
            "case21_message": "THE ANSWER IS IN WHAT YOU LEAVE EMPTY",
            "case26_spatial_cases": source_verify.EXPECTED_CASE26_MAPS,
            "case26_message": "CHECK THE OLD MAP",
            "case28_rule_zero": "ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.",
            "case29_access_coordinate": "D3",
            "book2_hook": "ARCHIVE FILE 001 // STILL OPEN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    contract = build_contract()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("PASS: exact V3 final-text integration contract built")
    print(f"OUTPUT: {output}")
    print(f"FRONT PAGES: {len(contract['front_pages'])}")
    print(f"MAIN CASES: {len(contract['main_cases'])}")
    print("HINTS: 30 x 3")
    print(f"SOLUTIONS: {len(contract['solution_files'])}")
    print("English frozen: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
