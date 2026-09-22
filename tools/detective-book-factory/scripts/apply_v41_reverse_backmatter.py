#!/usr/bin/env python3
"""Deterministically convert HMDA V4.1 Hint/Solution back matter into reverse entry.

This is a presentation-only post-process. It does not alter story, case logic,
spatial geometry, answers, owner-gated visual assets, or English freeze state.

Physical reading contract:
- enter from the back of the printed book,
- rotate the book 180 degrees,
- read Hint Vault Level 1 -> Level 2 -> Level 3,
- then read Solutions Case 01 -> Case 30.

The PDF remains 145 pages. Front matter and case pages 1-109 stay byte-order
stable as PDF pages; only pages 110-145 are reordered and marked Rotate=180.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

PAGE_COUNT = 145
BACKMATTER_START = 110
BACKMATTER_END = 145

HINT_KEYS = (
    "hints_level_1_cases_01_15",
    "hints_level_1_cases_16_30",
    "hints_level_2_cases_01_15",
    "hints_level_2_cases_16_30",
    "hints_level_3_cases_01_15",
    "hints_level_3_cases_16_30",
)


def _solution_key(case_number: int) -> str:
    return f"{case_number:02d}_solution"


def validate_source_index(index: dict) -> None:
    if index.get("page_count") != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT}-page source index")

    expected_hints = list(range(BACKMATTER_START, BACKMATTER_START + 6))
    actual_hints = [index.get(key) for key in HINT_KEYS]
    if actual_hints != expected_hints:
        raise ValueError(
            "V4.1 Hint Vault source layout changed; reverse-entry transform must be reviewed"
        )

    expected_solutions = list(range(BACKMATTER_START + 6, BACKMATTER_END + 1))
    actual_solutions = [index.get(_solution_key(n)) for n in range(1, 31)]
    if actual_solutions != expected_solutions:
        raise ValueError(
            "V4.1 Solution source layout changed; reverse-entry transform must be reviewed"
        )


def forward_source_page_sequence(index: dict) -> list[int]:
    """Return source pages in the order they must appear in the transformed PDF."""
    validate_source_index(index)

    sequence = list(range(1, BACKMATTER_START))

    # Physical reader moves backward from page 145. Therefore PDF-forward order
    # must be the reverse of the desired physical reading order.
    sequence.extend(index[_solution_key(n)] for n in range(30, 0, -1))
    sequence.extend(
        index[key]
        for key in (
            "hints_level_3_cases_16_30",
            "hints_level_3_cases_01_15",
            "hints_level_2_cases_16_30",
            "hints_level_2_cases_01_15",
            "hints_level_1_cases_16_30",
            "hints_level_1_cases_01_15",
        )
    )

    if len(sequence) != PAGE_COUNT or sorted(sequence) != list(range(1, PAGE_COUNT + 1)):
        raise ValueError("Reverse-entry sequence must be a lossless 145-page permutation")
    return sequence


def _label_source_page(index: dict, source_page: int) -> str:
    for key in HINT_KEYS:
        if index.get(key) == source_page:
            return key
    for n in range(1, 31):
        key = _solution_key(n)
        if index.get(key) == source_page:
            return key
    return f"page_{source_page:03d}"


def physical_back_to_front_labels(index: dict) -> list[str]:
    sequence = forward_source_page_sequence(index)
    tail = sequence[BACKMATTER_START - 1 :]
    return [_label_source_page(index, source_page) for source_page in reversed(tail)]


def remap_index(index: dict, sequence: list[int]) -> dict:
    source_to_target = {source: target for target, source in enumerate(sequence, 1)}
    remapped = {}
    for key, value in index.items():
        if key == "page_count":
            remapped[key] = value
        elif isinstance(value, int) and 1 <= value <= PAGE_COUNT:
            remapped[key] = source_to_target[value]
        else:
            remapped[key] = value
    return remapped


def apply_reverse_backmatter(
    input_pdf: Path,
    output_pdf: Path,
    source_index: dict,
) -> tuple[dict, dict]:
    sequence = forward_source_page_sequence(source_index)
    reader = PdfReader(str(input_pdf))
    if len(reader.pages) != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT} PDF pages, got {len(reader.pages)}")

    writer = PdfWriter()
    if reader.metadata:
        safe_meta = {str(k): str(v) for k, v in reader.metadata.items() if v is not None}
        if safe_meta:
            writer.add_metadata(safe_meta)

    for target_page, source_page in enumerate(sequence, 1):
        page = reader.pages[source_page - 1]
        if target_page >= BACKMATTER_START:
            page.rotate(180)
        writer.add_page(page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as fh:
        writer.write(fh)

    remapped = remap_index(source_index, sequence)
    labels = physical_back_to_front_labels(source_index)
    expected_labels = list(HINT_KEYS) + [_solution_key(n) for n in range(1, 31)]
    if labels != expected_labels:
        raise ValueError("Physical back-to-front reading order contract failed")

    contract = {
        "revision": "v4.1",
        "presentation_only": True,
        "english_frozen": False,
        "page_count": PAGE_COUNT,
        "front_section_unchanged_pages": [1, BACKMATTER_START - 1],
        "reverse_entry_pages": [BACKMATTER_START, BACKMATTER_END],
        "rotation_degrees": 180,
        "physical_entry": "back cover",
        "physical_reading_order": labels,
        "source_page_sequence": sequence,
        "output_pdf_sha256": hashlib.sha256(output_pdf.read_bytes()).hexdigest(),
    }
    return remapped, contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-pdf", required=True, type=Path)
    parser.add_argument("--output-pdf", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--output-index", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()

    source_index = json.loads(args.index.read_text(encoding="utf-8"))
    remapped, contract = apply_reverse_backmatter(
        args.input_pdf.resolve(), args.output_pdf.resolve(), source_index
    )
    args.output_index.write_text(json.dumps(remapped, indent=2), encoding="utf-8")
    args.contract.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    print("PASS: reverse-entry Hint Vault/Solutions architecture applied")
    print(f"PDF: {args.output_pdf.resolve()}")
    print(f"SHA256: {contract['output_pdf_sha256']}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
