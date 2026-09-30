#!/usr/bin/env python3
"""Recover locked V4 spatial rasters and run the canonical V4.1 final build.

This is an orchestration-only bridge for the already-validated recovery and
finalization paths. It never renders/crops the source PDF, redraws geometry,
or chooses owner-gated Case 03 / Book 2 art.

The exact locked 145-page V4 PDF is SHA-checked by
recover_v4_embedded_spatial_assets.py before any raster is written. The V4 page
index used for extraction is regenerated deterministically from the current
master + locked V4 overrides, then the canonical V4.1 finalizer consumes the
recovered byte-identical PNG XObjects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

import build_owner_review_v4 as v4
import build_owner_review_v41_final as v41_final
import recover_v4_embedded_spatial_assets as recovery

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_OVERRIDES = ROOT / "content/book1_v4_overrides.yml"
FINALIZER = SCRIPT_DIR / "build_owner_review_v41_final.py"
RECOVERY_INDEX_NAME = "HMDA_Book1_EN_OwnerReview_v4_recovery_page_index.json"
RECOVERY_MASTER_NAME = "book1_en_master_v4_recovery_input.yml"
INTEGRATION_MANIFEST_NAME = "HMDA_V41_LOCKED_V4_RECOVERY_INTEGRATION.json"
FINAL_MANIFEST_NAME = "HMDA_Book1_EN_OwnerReview_v41_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_recovery_index(master: Path, overrides: Path, work_dir: Path) -> tuple[Path, Path, dict]:
    """Build the exact deterministic 145-page V4 index used by the locked PDF."""
    work_dir.mkdir(parents=True, exist_ok=True)
    recovery_master = work_dir / RECOVERY_MASTER_NAME

    # Reuse the same bounded overlay merge already used by the canonical V4.1
    # finalizer. The Case 26 navigation addition does not change pagination.
    v41_final.prepare_case26_lookup_master(master, overrides, recovery_master)
    data = yaml.safe_load(recovery_master.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("missions"), list):
        raise ValueError("Recovery master is missing the canonical mission list")

    index = v4.plan_pages(data["missions"], data)
    if index.get("page_count") != 145:
        raise ValueError(
            f"Locked V4 recovery requires the 145-page plan, got {index.get('page_count')}"
        )

    recovery_index = work_dir / RECOVERY_INDEX_NAME
    recovery_index.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return recovery_master, recovery_index, index


def run_finalizer(args: argparse.Namespace, recovered_maps: Path) -> None:
    cmd = [
        sys.executable,
        str(FINALIZER),
        "--master", str(args.master),
        "--runtime", str(args.runtime),
        "--maps", str(recovered_maps),
        "--overrides", str(args.overrides),
        "--output", str(args.output),
    ]
    if args.aliases:
        cmd.extend(["--aliases", str(args.aliases)])
    if args.owner_visual_manifest:
        cmd.extend(["--owner-visual-manifest", str(args.owner_visual_manifest)])
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--locked-v4-pdf", required=True, type=Path)
    parser.add_argument("--maps-out", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--aliases", type=Path)
    parser.add_argument("--owner-visual-manifest", type=Path)
    parser.add_argument(
        "--expected-v4-pdf-sha256",
        default=recovery.LOCKED_V4_PDF_SHA256,
        help="Fail-closed SHA-256 for the exact locked 145-page V4 owner-review PDF.",
    )
    args = parser.parse_args()

    args.master = args.master.resolve()
    args.runtime = args.runtime.resolve()
    args.locked_v4_pdf = args.locked_v4_pdf.resolve()
    args.maps_out = args.maps_out.resolve()
    args.output = args.output.resolve()
    args.overrides = args.overrides.resolve()
    if args.aliases:
        args.aliases = args.aliases.resolve()
    if args.owner_visual_manifest:
        args.owner_visual_manifest = args.owner_visual_manifest.resolve()

    for required in (args.master, args.runtime, args.locked_v4_pdf, args.overrides):
        if not required.is_file():
            raise FileNotFoundError(required)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.maps_out.mkdir(parents=True, exist_ok=True)
    work_dir = args.maps_out / "_locked_v4_recovery_contract"
    recovery_master, recovery_index, page_index = build_recovery_index(
        args.master, args.overrides, work_dir
    )

    recovery_manifest = recovery.recover(
        pdf_path=args.locked_v4_pdf,
        master_path=recovery_master,
        page_index_path=recovery_index,
        output_dir=args.maps_out,
        expected_pdf_sha256=args.expected_v4_pdf_sha256,
        require_count=15,
        require_page_count=145,
        min_dimension=500,
    )
    if recovery_manifest.get("recovered_raster_count") != 30:
        raise ValueError("Recovery did not produce the exact 30-raster spatial set")

    run_finalizer(args, args.maps_out)

    final_manifest_path = args.output.parent / FINAL_MANIFEST_NAME
    if not final_manifest_path.is_file():
        raise FileNotFoundError(final_manifest_path)
    final_manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
    if final_manifest.get("english_frozen") is not False:
        raise ValueError("V4.1 finalizer unexpectedly changed English freeze state")
    if final_manifest.get("pages") != 145:
        raise ValueError("V4.1 finalizer unexpectedly changed the 145-page contract")
    if final_manifest.get("pdf_sha256") != sha256(args.output):
        raise ValueError("Final PDF SHA does not match the canonical V4.1 manifest")

    integration = {
        "status": "PASS",
        "method": "locked_v4_embedded_png_recovery_then_canonical_v41_finalizer",
        "source_v4_pdf_sha256": sha256(args.locked_v4_pdf),
        "expected_source_v4_pdf_sha256": args.expected_v4_pdf_sha256,
        "recovery_page_count": page_index["page_count"],
        "recovered_raster_count": recovery_manifest["recovered_raster_count"],
        "recovery_manifest": str(args.maps_out / "HMDA_V4_EMBEDDED_SPATIAL_RECOVERY_MANIFEST.json"),
        "recovery_index": str(recovery_index),
        "final_pdf": str(args.output),
        "final_pdf_sha256": final_manifest["pdf_sha256"],
        "final_pages": final_manifest["pages"],
        "english_frozen": final_manifest["english_frozen"],
        "owner_visual_manifest_supplied": args.owner_visual_manifest is not None,
        "logic_changed": False,
        "geometry_redrawn": False,
        "pdf_page_render_or_crop_used": False,
    }
    integration_path = args.output.parent / INTEGRATION_MANIFEST_NAME
    integration_path.write_text(json.dumps(integration, indent=2) + "\n", encoding="utf-8")

    print("PASS: locked V4 spatial recovery + canonical V4.1 final build completed")
    print(f"RECOVERED RASTERS: {integration['recovered_raster_count']}")
    print(f"FINAL PDF: {args.output}")
    print(f"FINAL SHA256: {integration['final_pdf_sha256']}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
