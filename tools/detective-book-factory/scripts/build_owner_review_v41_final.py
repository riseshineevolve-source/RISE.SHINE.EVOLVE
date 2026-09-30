#!/usr/bin/env python3
"""Build the complete HMDA Book 1 V4.1 owner-review artifact.

This is the canonical V4.1 render wrapper. It runs the bounded owner-audit V4.1
builder first, inserts one dedicated upright STOP / HINT VAULT divider after
locked main-content page 109, then applies the validated reverse-entry Hint
Vault / Solutions architecture. The source builder remains 145 pages; the
final physical artifact becomes 146 pages without moving any case/map page
1-109.

It does not change story, puzzle logic, spatial geometry, owner-gated visual
selections, or English freeze state.

Case 03 and Book 2 art remain fail-closed in build_owner_review_v41.py unless an
explicit owner-locked visual manifest is supplied.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import yaml

import apply_v41_reverse_backmatter as rbm
import audit_pdf_grayscale as grayscale_audit
import audit_v41_final_artifact as final_audit
import build_owner_review_v4 as v4

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
V41_BUILDER = SCRIPT_DIR / "build_owner_review_v41_owner_audit.py"
INDEX_NAME = "HMDA_Book1_EN_OwnerReview_v41_page_index.json"
MANIFEST_NAME = "HMDA_Book1_EN_OwnerReview_v41_manifest.json"
REVERSE_CONTRACT_NAME = "HMDA_Book1_EN_OwnerReview_v41_reverse_entry.json"
FINAL_AUDIT_NAME = "HMDA_Book1_EN_OwnerReview_v41_final_audit.json"
GRAYSCALE_AUDIT_NAME = "HMDA_Book1_EN_OwnerReview_v41_grayscale_audit.json"
DEFAULT_OVERRIDES = ROOT / "content/book1_v4_overrides.yml"
CASE26_LOOKUP_INPUT_NAME = "book1_en_master_v41_case26_lookup_input.yml"
BUILDER_PAGE_COUNT = 145


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def prepare_case26_lookup_master(
    master_path: Path,
    overrides_path: Path,
    output_path: Path,
) -> list[dict]:
    """Add generated map-page references to Case 26 Hint Level 1 only.

    Case 26 asks the reader to compare the fourteen completed spatial maps.
    The durable V4 contract intentionally keeps case numbers in the main
    ledger and adds physical page references only to Hint Level 1. Generate
    those references from the locked page plan so they cannot drift when
    parity/interlude placement changes.

    This is navigation-only presentation support: no hint logic, answers,
    spatial geometry or pagination is changed.
    """
    data = copy.deepcopy(_load_yaml(master_path))
    overrides = _load_yaml(overrides_path)

    data["v4"] = copy.deepcopy(overrides)
    if "story_spine" in overrides:
        data["story_spine"] = copy.deepcopy(overrides["story_spine"])

    cases_patch = overrides.get("cases", {})
    for mission in data.get("missions", []):
        number = int(mission["number"])
        patch = cases_patch.get(number, cases_patch.get(str(number), {}))
        if patch:
            mission.update(copy.deepcopy(patch))

    plan = v4.plan_pages(data["missions"], data)
    refs: list[dict] = []
    for mission in data["missions"]:
        number = int(mission["number"])
        if number >= 26:
            continue
        if mission.get("type") not in ("spatial", "boss-spatial"):
            continue
        key = f"{number:02d}_map"
        if key not in plan:
            raise ValueError(f"Case 26 lookup cannot resolve page for Case {number:02d}")
        refs.append({"case": number, "page": int(plan[key])})

    if len(refs) != 14:
        raise ValueError(
            f"Case 26 lookup contract requires 14 earlier spatial maps, found {len(refs)}"
        )

    case26 = next((m for m in data["missions"] if int(m["number"]) == 26), None)
    if case26 is None:
        raise ValueError("Case 26 missing from master")
    hints = case26.get("hints")
    if not isinstance(hints, list) or len(hints) < 1 or not str(hints[0]).strip():
        raise ValueError("Case 26 requires an existing Hint Level 1 entry")

    base_hint = str(hints[0]).split("\n\nMAP LOOKUP //", 1)[0].rstrip()
    lookup = " · ".join(f"Case {item['case']:02d} p. {item['page']}" for item in refs)
    hints[0] = f"{base_hint}\n\nMAP LOOKUP // {lookup}"

    data.setdefault("production_state", {})["case26_generated_map_lookup"] = refs
    data["production_state"]["case26_lookup_scope"] = "HINT_LEVEL_1_ONLY"
    data["production_state"]["case26_lookup_changes_logic"] = False

    output_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )
    return refs


def _render_support_divider(path: Path) -> None:
    """Render a strict grayscale physical boundary between cases and back-entry help."""
    width, height = letter
    c = canvas.Canvas(str(path), pagesize=letter, pageCompression=1)
    c.setFillGray(0)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    c.setFillGray(1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(54, height - 74, "DETECTIVE ACADEMY // SUPPORT BOUNDARY")

    c.setLineWidth(1.5)
    c.setStrokeGray(1)
    c.line(54, height - 92, width - 54, height - 92)

    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(width / 2, height - 186, "STOP")
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(width / 2, height - 230, "HINT VAULT // SOLUTIONS")

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width / 2, height - 310, "MAIN CASE FILE ENDS HERE")

    c.setFont("Helvetica", 13)
    lines = (
        "Need help? Keep your place in the case.",
        "Turn the whole book upside down.",
        "Open from the BACK cover and read forward from that direction.",
        "Take the smallest hint you need, then return to the case.",
    )
    y = height - 366
    for line in lines:
        c.drawCentredString(width / 2, y, line)
        y -= 31

    c.setLineWidth(1.2)
    c.line(86, 214, width - 86, 214)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(
        width / 2,
        184,
        "BACK ENTRY ORDER // HINT 1 → HINT 2 → HINT 3 → SOLUTIONS",
    )
    c.setFont("Helvetica", 10.5)
    c.drawCentredString(width / 2, 145, "PAGE 110 // KEEP THIS PAGE UPRIGHT")
    c.save()


def insert_support_divider(
    input_pdf: Path,
    output_pdf: Path,
    source_index: dict,
) -> dict:
    """Insert page 110 while preserving original pages 1-109 exactly in position."""
    if source_index.get("page_count") != BUILDER_PAGE_COUNT:
        raise ValueError("Support-divider insertion requires the 145-page builder index")

    reader = PdfReader(str(input_pdf))
    if len(reader.pages) != BUILDER_PAGE_COUNT:
        raise ValueError(
            f"Support-divider insertion requires {BUILDER_PAGE_COUNT} builder pages, "
            f"got {len(reader.pages)}"
        )

    divider_pdf = output_pdf.with_name(output_pdf.name + ".divider-page.tmp.pdf")
    _render_support_divider(divider_pdf)
    divider_reader = PdfReader(str(divider_pdf))
    if len(divider_reader.pages) != 1:
        raise ValueError("Support-divider renderer must produce exactly one page")

    writer = PdfWriter()
    if reader.metadata:
        safe_meta = {str(k): str(v) for k, v in reader.metadata.items() if v is not None}
        if safe_meta:
            writer.add_metadata(safe_meta)

    for page in reader.pages[: rbm.MAIN_CONTENT_END]:
        writer.add_page(page)
    writer.add_page(divider_reader.pages[0])
    for page in reader.pages[rbm.MAIN_CONTENT_END :]:
        writer.add_page(page)

    with output_pdf.open("wb") as fh:
        writer.write(fh)
    divider_pdf.unlink(missing_ok=True)

    shifted: dict = {}
    for key, value in source_index.items():
        if key == "page_count":
            shifted[key] = rbm.PAGE_COUNT
        elif isinstance(value, int) and rbm.SUPPORT_DIVIDER_PAGE <= value <= BUILDER_PAGE_COUNT:
            shifted[key] = value + 1
        else:
            shifted[key] = value
    shifted["support_divider"] = rbm.SUPPORT_DIVIDER_PAGE

    if shifted.get("page_count") != rbm.PAGE_COUNT:
        raise ValueError("Support-divider insertion failed to produce the 146-page index")
    if shifted.get(rbm.HINT_KEYS[0]) != rbm.BACKMATTER_START:
        raise ValueError("Support-divider insertion did not shift Hint Vault start to page 111")
    return shifted


def finalize_rendered_artifact(
    pre_reverse_pdf: Path,
    final_pdf: Path,
    index_path: Path,
    manifest_path: Path,
    reverse_contract_path: Path,
) -> dict:
    """Insert support boundary, apply reverse entry, and reconcile artifact metadata."""
    builder_index = json.loads(index_path.read_text(encoding="utf-8"))
    if builder_index.get("page_count") != BUILDER_PAGE_COUNT:
        raise ValueError("V4.1 finalization requires the locked 145-page builder index")

    pre_sha = sha256(pre_reverse_pdf)
    with_divider_pdf = final_pdf.with_name(final_pdf.name + ".divider.tmp")
    shifted_index = insert_support_divider(
        pre_reverse_pdf,
        with_divider_pdf,
        builder_index,
    )
    with_divider_sha = sha256(with_divider_pdf)

    tmp_pdf = final_pdf.with_name(final_pdf.name + ".reverse.tmp")
    remapped_index, contract = rbm.apply_reverse_backmatter(
        with_divider_pdf, tmp_pdf, shifted_index
    )

    reader = PdfReader(str(tmp_pdf))
    if len(reader.pages) != rbm.PAGE_COUNT:
        raise ValueError("Reverse-entry final artifact lost the 146-page contract")

    tmp_pdf.replace(final_pdf)
    with_divider_pdf.unlink(missing_ok=True)
    index_path.write_text(json.dumps(remapped_index, indent=2), encoding="utf-8")
    reverse_contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("revision") != "v4.1" or manifest.get("english_frozen") is not False:
        raise ValueError("Unexpected V4.1 manifest state; refusing finalization")
    if manifest.get("pages") != BUILDER_PAGE_COUNT:
        raise ValueError("Unexpected V4.1 builder manifest page count")

    manifest["builder_pages"] = BUILDER_PAGE_COUNT
    manifest["pages"] = rbm.PAGE_COUNT
    manifest["pre_reverse_pdf_sha256"] = pre_sha
    manifest["pre_reverse_with_divider_sha256"] = with_divider_sha
    manifest["pdf_sha256"] = contract["output_pdf_sha256"]
    manifest["support_divider"] = {
        "integrated": True,
        "page": rbm.SUPPORT_DIVIDER_PAGE,
        "title": "STOP / HINT VAULT / SOLUTIONS",
        "upright": True,
        "main_case_pages_unchanged": [1, rbm.MAIN_CONTENT_END],
        "adds_one_final_page": True,
        "logic_changed": False,
        "owner_gated_art_changed": False,
    }
    manifest["reverse_entry"] = {
        "integrated": True,
        "contract_file": reverse_contract_path.name,
        "pages": contract["reverse_entry_pages"],
        "rotation_degrees": contract["rotation_degrees"],
        "physical_entry": contract["physical_entry"],
        "physical_reading_order": contract["physical_reading_order"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--maps", required=True, type=Path)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--owner-visual-manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    final_pdf = args.output.resolve()
    final_pdf.parent.mkdir(parents=True, exist_ok=True)
    pre_reverse_pdf = final_pdf.with_name(final_pdf.stem + "_upright_backmatter.pdf")
    overrides_path = args.overrides.resolve() if args.overrides else DEFAULT_OVERRIDES.resolve()
    lookup_master = final_pdf.parent / CASE26_LOOKUP_INPUT_NAME

    case26_refs = prepare_case26_lookup_master(
        args.master.resolve(),
        overrides_path,
        lookup_master,
    )

    cmd = [
        sys.executable,
        str(V41_BUILDER),
        "--master", str(lookup_master),
        "--runtime", str(args.runtime.resolve()),
        "--maps", str(args.maps.resolve()),
        "--overrides", str(overrides_path),
        "--output", str(pre_reverse_pdf),
    ]
    if args.aliases:
        cmd.extend(["--aliases", str(args.aliases.resolve())])
    if args.owner_visual_manifest:
        cmd.extend(["--owner-visual-manifest", str(args.owner_visual_manifest.resolve())])

    subprocess.run(cmd, check=True, cwd=ROOT)

    index_path = final_pdf.parent / INDEX_NAME
    manifest_path = final_pdf.parent / MANIFEST_NAME
    reverse_contract_path = final_pdf.parent / REVERSE_CONTRACT_NAME
    audit_report_path = final_pdf.parent / FINAL_AUDIT_NAME
    grayscale_report_path = final_pdf.parent / GRAYSCALE_AUDIT_NAME

    manifest = finalize_rendered_artifact(
        pre_reverse_pdf,
        final_pdf,
        index_path,
        manifest_path,
        reverse_contract_path,
    )
    manifest["case26_lookup"] = {
        "scope": "HINT_LEVEL_1_ONLY",
        "generated_from_page_plan": True,
        "spatial_case_count": len(case26_refs),
        "references": case26_refs,
        "logic_changed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    grayscale_report = grayscale_audit.audit_pdf_grayscale(
        final_pdf,
        grayscale_report_path,
    )
    manifest["grayscale_audit"] = {
        "status": grayscale_report["status"],
        "report_file": grayscale_report_path.name,
        "vector_color_operators_checked": grayscale_report[
            "vector_color_operators_checked"
        ],
        "embedded_images_checked": grayscale_report["embedded_images_checked"],
        "grayscale_only": grayscale_report["grayscale_only"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Fail closed on the actual physical artifact, not merely on synthetic
    # transform contracts. This remains independent of owner-gated art choice.
    audit_report = final_audit.audit_final_artifact(
        final_pdf,
        index_path,
        manifest_path,
        reverse_contract_path,
        audit_report_path,
    )

    pre_reverse_pdf.unlink(missing_ok=True)
    lookup_master.unlink(missing_ok=True)

    print("PASS: complete V4.1 owner-review artifact rendered")
    print(f"PDF: {final_pdf}")
    print(f"SHA256: {manifest['pdf_sha256']}")
    print(f"PAGES: {manifest['pages']} // SUPPORT DIVIDER: {rbm.SUPPORT_DIVIDER_PAGE}")
    print(f"INDEX: {index_path}")
    print(f"REVERSE CONTRACT: {reverse_contract_path}")
    print(f"GRAYSCALE AUDIT: {grayscale_report_path} // {grayscale_report['status']}")
    print(f"FINAL AUDIT: {audit_report_path} // {audit_report['status']}")
    print(f"CASE 26 LOOKUP: {len(case26_refs)} generated map references")
    print("English frozen: false")


if __name__ == "__main__":
    main()
