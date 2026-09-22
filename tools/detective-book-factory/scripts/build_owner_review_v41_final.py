#!/usr/bin/env python3
"""Build the complete HMDA Book 1 V4.1 owner-review artifact.

This is the canonical V4.1 render wrapper. It runs the bounded V4.1 builder
first, then applies the already-validated reverse-entry Hint Vault / Solutions
architecture to the freshly rendered 145-page PDF. It does not change story,
puzzle logic, spatial geometry, owner-gated visual selections, or English
freeze state.

Case 03 and Book 2 art remain fail-closed in build_owner_review_v41.py unless an
explicit owner-locked visual manifest is supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

import apply_v41_reverse_backmatter as rbm

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
V41_BUILDER = SCRIPT_DIR / "build_owner_review_v41.py"
INDEX_NAME = "HMDA_Book1_EN_OwnerReview_v41_page_index.json"
MANIFEST_NAME = "HMDA_Book1_EN_OwnerReview_v41_manifest.json"
REVERSE_CONTRACT_NAME = "HMDA_Book1_EN_OwnerReview_v41_reverse_entry.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finalize_rendered_artifact(
    pre_reverse_pdf: Path,
    final_pdf: Path,
    index_path: Path,
    manifest_path: Path,
    reverse_contract_path: Path,
) -> dict:
    """Apply reverse-entry architecture and reconcile durable artifact metadata."""
    source_index = json.loads(index_path.read_text(encoding="utf-8"))
    if source_index.get("page_count") != rbm.PAGE_COUNT:
        raise ValueError("V4.1 finalization requires the locked 145-page index")

    pre_sha = sha256(pre_reverse_pdf)
    tmp_pdf = final_pdf.with_name(final_pdf.name + ".reverse.tmp")
    remapped_index, contract = rbm.apply_reverse_backmatter(
        pre_reverse_pdf, tmp_pdf, source_index
    )

    reader = PdfReader(str(tmp_pdf))
    if len(reader.pages) != rbm.PAGE_COUNT:
        raise ValueError("Reverse-entry final artifact lost the 145-page contract")

    tmp_pdf.replace(final_pdf)
    index_path.write_text(json.dumps(remapped_index, indent=2), encoding="utf-8")
    reverse_contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("revision") != "v4.1" or manifest.get("english_frozen") is not False:
        raise ValueError("Unexpected V4.1 manifest state; refusing finalization")
    if manifest.get("pages") != rbm.PAGE_COUNT:
        raise ValueError("Unexpected V4.1 manifest page count")

    manifest["pre_reverse_pdf_sha256"] = pre_sha
    manifest["pdf_sha256"] = contract["output_pdf_sha256"]
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

    cmd = [
        sys.executable,
        str(V41_BUILDER),
        "--master", str(args.master.resolve()),
        "--runtime", str(args.runtime.resolve()),
        "--maps", str(args.maps.resolve()),
        "--output", str(pre_reverse_pdf),
    ]
    if args.overrides:
        cmd.extend(["--overrides", str(args.overrides.resolve())])
    if args.aliases:
        cmd.extend(["--aliases", str(args.aliases.resolve())])
    if args.owner_visual_manifest:
        cmd.extend(["--owner-visual-manifest", str(args.owner_visual_manifest.resolve())])

    subprocess.run(cmd, check=True, cwd=ROOT)

    index_path = final_pdf.parent / INDEX_NAME
    manifest_path = final_pdf.parent / MANIFEST_NAME
    reverse_contract_path = final_pdf.parent / REVERSE_CONTRACT_NAME
    manifest = finalize_rendered_artifact(
        pre_reverse_pdf,
        final_pdf,
        index_path,
        manifest_path,
        reverse_contract_path,
    )
    pre_reverse_pdf.unlink(missing_ok=True)

    print("PASS: complete V4.1 owner-review artifact rendered")
    print(f"PDF: {final_pdf}")
    print(f"SHA256: {manifest['pdf_sha256']}")
    print(f"INDEX: {index_path}")
    print(f"REVERSE CONTRACT: {reverse_contract_path}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
