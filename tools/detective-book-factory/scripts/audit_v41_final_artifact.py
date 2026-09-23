#!/usr/bin/env python3
"""Fail-closed structural audit for the complete 145-page HMDA V4.1 artifact.

This validator is intentionally independent of the owner-gated Case 03 / Book 2
artwork. It verifies the physical final PDF produced by
``build_owner_review_v41_final.py``: page count/trim, reverse-entry rotations and
reading order, remapped index integrity, Case 26 generated map references,
manifest hashes, visual-gate state, and the explicit non-freeze state.

It does not alter story, puzzle logic, spatial geometry, pagination, visual
selection, or English freeze state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader

import apply_v41_reverse_backmatter as rbm

LETTER_W = 612.0
LETTER_H = 792.0
TRIM_TOLERANCE = 0.5
SPATIAL_CASES_BEFORE_26 = (2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25)


class FinalArtifactAuditError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - surfaced as a bounded audit error
        raise FinalArtifactAuditError([f"{label} is not readable JSON: {exc}"]) from exc
    if not isinstance(data, dict):
        raise FinalArtifactAuditError([f"{label} must be a JSON object"])
    return data


def _expected_physical_labels() -> list[str]:
    return list(rbm.HINT_KEYS) + [f"{n:02d}_solution" for n in range(1, 31)]


def _expected_remapped_backmatter(sequence: list[int]) -> dict[str, int]:
    source_to_target = {source: target for target, source in enumerate(sequence, 1)}
    expected: dict[str, int] = {}
    for offset, key in enumerate(rbm.HINT_KEYS):
        expected[key] = source_to_target[rbm.BACKMATTER_START + offset]
    for n in range(1, 31):
        expected[f"{n:02d}_solution"] = source_to_target[rbm.BACKMATTER_START + 5 + n]
    return expected


def audit_final_artifact(
    pdf_path: Path,
    index_path: Path,
    manifest_path: Path,
    reverse_contract_path: Path,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Audit a fully rendered V4.1 artifact and return a durable report.

    All checks are presentation/packaging checks. Any mismatch fails closed so a
    malformed physical artifact cannot be mistaken for the owner-review final.
    """
    pdf_path = pdf_path.resolve()
    index_path = index_path.resolve()
    manifest_path = manifest_path.resolve()
    reverse_contract_path = reverse_contract_path.resolve()

    errors: list[str] = []
    for path, label in (
        (pdf_path, "PDF"),
        (index_path, "page index"),
        (manifest_path, "manifest"),
        (reverse_contract_path, "reverse-entry contract"),
    ):
        if not path.is_file():
            errors.append(f"{label} missing: {path}")
    if errors:
        raise FinalArtifactAuditError(errors)

    index = _load_json(index_path, "page index")
    manifest = _load_json(manifest_path, "manifest")
    contract = _load_json(reverse_contract_path, "reverse-entry contract")

    actual_sha = _sha256(pdf_path)
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        raise FinalArtifactAuditError([f"PDF cannot be opened: {exc}"]) from exc

    page_count = len(reader.pages)
    if page_count != rbm.PAGE_COUNT:
        errors.append(f"PDF page count {page_count} != {rbm.PAGE_COUNT}")

    for page_number, page in enumerate(reader.pages, 1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - LETTER_W) > TRIM_TOLERANCE or abs(height - LETTER_H) > TRIM_TOLERANCE:
            errors.append(
                f"page {page_number} trim {width:.2f}x{height:.2f} is not Letter 612x792 pt"
            )
        rotation = int(page.rotation or 0) % 360
        expected_rotation = 0 if page_number < rbm.BACKMATTER_START else 180
        if rotation != expected_rotation:
            errors.append(
                f"page {page_number} rotation {rotation} != expected {expected_rotation}"
            )

    if index.get("page_count") != rbm.PAGE_COUNT:
        errors.append("final page index does not declare 145 pages")
    if manifest.get("revision") != "v4.1":
        errors.append("manifest revision is not v4.1")
    if manifest.get("pages") != rbm.PAGE_COUNT:
        errors.append("manifest does not declare 145 pages")
    if manifest.get("english_frozen") is not False:
        errors.append("English freeze state must remain false")
    if manifest.get("pdf_sha256") != actual_sha:
        errors.append("manifest pdf_sha256 does not match final PDF")

    if contract.get("revision") != "v4.1":
        errors.append("reverse-entry contract revision is not v4.1")
    if contract.get("presentation_only") is not True:
        errors.append("reverse-entry contract must be presentation_only=true")
    if contract.get("english_frozen") is not False:
        errors.append("reverse-entry contract must keep english_frozen=false")
    if contract.get("page_count") != rbm.PAGE_COUNT:
        errors.append("reverse-entry contract does not declare 145 pages")
    if contract.get("front_section_unchanged_pages") != [1, rbm.BACKMATTER_START - 1]:
        errors.append("reverse-entry front-section boundary changed")
    if contract.get("reverse_entry_pages") != [rbm.BACKMATTER_START, rbm.BACKMATTER_END]:
        errors.append("reverse-entry page range changed")
    if contract.get("rotation_degrees") != 180:
        errors.append("reverse-entry rotation contract changed")
    if contract.get("physical_entry") != "back cover":
        errors.append("reverse-entry physical entry is not the back cover")
    if contract.get("physical_reading_order") != _expected_physical_labels():
        errors.append("reverse-entry physical reading order changed")
    if contract.get("output_pdf_sha256") != actual_sha:
        errors.append("reverse-entry contract hash does not match final PDF")

    sequence = contract.get("source_page_sequence")
    if not isinstance(sequence, list) or len(sequence) != rbm.PAGE_COUNT:
        errors.append("reverse-entry source_page_sequence is not a 145-page list")
        sequence = []
    elif sorted(sequence) != list(range(1, rbm.PAGE_COUNT + 1)):
        errors.append("reverse-entry source_page_sequence is not a lossless permutation")
    elif sequence[: rbm.BACKMATTER_START - 1] != list(range(1, rbm.BACKMATTER_START)):
        errors.append("pages 1-109 are not preserved in source order")

    if sequence:
        for key, expected_page in _expected_remapped_backmatter(sequence).items():
            if index.get(key) != expected_page:
                errors.append(
                    f"final page index mismatch for {key}: {index.get(key)!r} != {expected_page}"
                )

    reverse_manifest = manifest.get("reverse_entry")
    if not isinstance(reverse_manifest, dict) or reverse_manifest.get("integrated") is not True:
        errors.append("manifest does not record integrated reverse-entry architecture")
    else:
        for key in ("pages", "rotation_degrees", "physical_entry", "physical_reading_order"):
            contract_key = "reverse_entry_pages" if key == "pages" else key
            if reverse_manifest.get(key) != contract.get(contract_key):
                errors.append(f"manifest reverse_entry.{key} disagrees with reverse-entry contract")

    owner_gate = manifest.get("owner_visual_gate")
    if not isinstance(owner_gate, dict):
        errors.append("manifest owner_visual_gate is missing")
        owner_status = None
    else:
        owner_status = owner_gate.get("status")
        allowed_statuses = {"OWNER_GATE_PENDING", "OWNER_LOCKED_ASSETS_VALIDATED"}
        if owner_status not in allowed_statuses:
            errors.append(f"unexpected owner visual gate status: {owner_status!r}")
        if owner_status == "OWNER_GATE_PENDING" and owner_gate.get("integrated") is not False:
            errors.append("pending owner visual gate cannot be marked integrated")
        if owner_status == "OWNER_LOCKED_ASSETS_VALIDATED" and owner_gate.get("integrated") is not True:
            errors.append("validated owner visual gate must be marked integrated")

    case26 = manifest.get("case26_lookup")
    if not isinstance(case26, dict):
        errors.append("manifest case26_lookup is missing")
        refs: list[dict[str, Any]] = []
    else:
        if case26.get("scope") != "HINT_LEVEL_1_ONLY":
            errors.append("Case 26 lookup scope changed")
        if case26.get("generated_from_page_plan") is not True:
            errors.append("Case 26 lookup is not marked page-plan generated")
        if case26.get("logic_changed") is not False:
            errors.append("Case 26 lookup must remain presentation-only")
        if case26.get("spatial_case_count") != len(SPATIAL_CASES_BEFORE_26):
            errors.append("Case 26 lookup does not declare 14 earlier spatial maps")
        raw_refs = case26.get("references")
        refs = raw_refs if isinstance(raw_refs, list) else []
        if len(refs) != len(SPATIAL_CASES_BEFORE_26):
            errors.append("Case 26 lookup does not contain exactly 14 references")

    if refs:
        actual_cases = [item.get("case") for item in refs if isinstance(item, dict)]
        if actual_cases != list(SPATIAL_CASES_BEFORE_26):
            errors.append("Case 26 lookup case sequence changed")
        for item in refs:
            if not isinstance(item, dict):
                errors.append("Case 26 lookup contains a non-object reference")
                continue
            case_number = item.get("case")
            page_number = item.get("page")
            if case_number not in SPATIAL_CASES_BEFORE_26:
                continue
            map_key = f"{int(case_number):02d}_map"
            expected_page = index.get(map_key)
            if expected_page is None:
                errors.append(f"final page index missing {map_key} for Case 26 lookup")
            elif page_number != expected_page:
                errors.append(
                    f"Case 26 lookup page mismatch for Case {int(case_number):02d}: "
                    f"{page_number!r} != {expected_page}"
                )
            if isinstance(page_number, int) and page_number >= rbm.BACKMATTER_START:
                errors.append(f"Case 26 map reference for Case {int(case_number):02d} points into back matter")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "revision": "v4.1",
        "pdf": str(pdf_path),
        "pages": page_count,
        "pdf_sha256": actual_sha,
        "letter_trim_verified": not any("trim" in error for error in errors),
        "reverse_entry_verified": not any("reverse-entry" in error or "rotation" in error for error in errors),
        "case26_lookup_verified": not any("Case 26" in error for error in errors),
        "owner_visual_gate_status": owner_status,
        "english_frozen": manifest.get("english_frozen"),
        "errors": errors,
    }
    if report_path is not None:
        report_path = report_path.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if errors:
        raise FinalArtifactAuditError(errors)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--reverse-contract", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = audit_final_artifact(
            args.pdf,
            args.index,
            args.manifest,
            args.reverse_contract,
            args.report,
        )
    except FinalArtifactAuditError as exc:
        print("HMDA V4.1 FINAL ARTIFACT AUDIT: BLOCKED")
        for error in exc.errors:
            print(f"- {error}")
        return 2

    print("PASS: HMDA V4.1 final artifact structural audit")
    print(f"PDF: {report['pdf']}")
    print(f"PAGES: {report['pages']}")
    print(f"SHA256: {report['pdf_sha256']}")
    print(f"OWNER VISUAL GATE: {report['owner_visual_gate_status']}")
    print("English frozen: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
