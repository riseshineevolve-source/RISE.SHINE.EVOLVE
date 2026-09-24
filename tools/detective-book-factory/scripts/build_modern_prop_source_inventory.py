#!/usr/bin/env python3
"""Build a deterministic modern-prop inventory directly from the locked Shigai checkpoint.

This is a read-only bridge for presentation work.  It never rewrites the
checkpoint or puzzle runtime.  The source manifest selects the production cases;
scene/clue page identity, raw title, grid and checkpoint SHA must all match before
any furniture record is emitted.

The output is evidence for modern-prop design only.  It preserves exact source
cell/type/variant/occupiable/blocked semantics and can optionally cross-check an
already generated HMDA runtime fingerprint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import extract_shigai_runtime as bridge
import validate_modern_prop_contract as contract

TOOL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = TOOL_ROOT / "content" / "spatial_source_manifest_final.yml"


class InventoryError(RuntimeError):
    pass


def _records_from_board(case_id: str, board: dict[str, Any], rows: int, cols: int) -> list[dict[str, Any]]:
    furniture = board.get("furniture") or []
    occupiable = board.get("occupiable") or []
    variants = board.get("furnitureVariants") or []
    if len(furniture) != rows * cols or len(occupiable) != rows * cols:
        raise InventoryError(f"{case_id}: furniture/occupiable vectors do not match {cols}x{rows}")
    if variants and len(variants) != rows * cols:
        raise InventoryError(f"{case_id}: furnitureVariants vector does not match {cols}x{rows}")

    result: list[dict[str, Any]] = []
    for index, item in enumerate(furniture):
        if item is None:
            continue
        if not isinstance(item, str) or not item.strip():
            raise InventoryError(f"{case_id}: invalid furniture type at source index {index}")
        can_occupy = bool(occupiable[index])
        result.append(
            {
                "case_id": case_id,
                "cell": bridge.coordinate(index, cols),
                "type": item,
                "variant": variants[index] if variants else None,
                "occupiable": can_occupy,
                "blocked": not can_occupy,
            }
        )
    return result


def build_inventory(checkpoint: dict[str, Any], manifest: dict[str, Any], checkpoint_hash: str) -> dict[str, Any]:
    declarations = manifest.get("cases")
    if not isinstance(declarations, list) or not declarations:
        raise InventoryError("selection manifest has no production cases")
    pages = checkpoint.get("pages")
    if not isinstance(pages, list):
        raise InventoryError("checkpoint has no pages list")

    expected_hash = str(manifest.get("source", {}).get("checkpoint_sha256", ""))
    if not expected_hash or checkpoint_hash != expected_hash:
        raise InventoryError(
            f"checkpoint SHA-256 mismatch: expected {expected_hash or '<missing>'}, got {checkpoint_hash}"
        )

    case_reports: dict[str, Any] = {}
    all_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for declaration in declarations:
        if not isinstance(declaration, dict):
            raise InventoryError("selection manifest contains a non-object case")
        case_id = declaration.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise InventoryError("selection manifest contains a case without id")
        if case_id in seen_ids:
            raise InventoryError(f"duplicate production case id {case_id}")
        seen_ids.add(case_id)

        checkpoint_ref = declaration.get("checkpoint") or {}
        scene = bridge.board_at(pages, checkpoint_ref.get("scene_index"), f"{case_id} scene")
        clues = bridge.board_at(pages, checkpoint_ref.get("clues_index"), f"{case_id} clues")
        if bridge.board_identity(scene) != bridge.board_identity(clues):
            raise InventoryError(f"{case_id}: scene and clues do not resolve to the same source board")

        rows, cols = scene.get("rows"), scene.get("cols")
        if not isinstance(rows, int) or not isinstance(cols, int) or rows <= 0 or cols <= 0:
            raise InventoryError(f"{case_id}: invalid source grid")
        declared_cols, declared_rows = bridge.parse_grid(declaration.get("grid"))
        if (cols, rows) != (declared_cols, declared_rows):
            raise InventoryError(
                f"{case_id}: source grid {cols}x{rows} != manifest {declared_cols}x{declared_rows}"
            )
        if scene.get("caseTitle") != declaration.get("raw_title"):
            raise InventoryError(
                f"{case_id}: raw title mismatch: {scene.get('caseTitle')!r} != {declaration.get('raw_title')!r}"
            )

        records = _records_from_board(case_id, scene, rows, cols)
        all_records.extend(records)
        type_counts: dict[str, int] = {}
        for rec in records:
            type_counts[rec["type"]] = type_counts.get(rec["type"], 0) + 1
        case_reports[case_id] = {
            "grid": f"{cols}x{rows}",
            "raw_title": scene.get("caseTitle"),
            "object_count": len(records),
            "type_counts": dict(sorted(type_counts.items())),
            "records": records,
        }

    types: dict[str, dict[str, Any]] = {}
    for rec in all_records:
        entry = types.setdefault(
            rec["type"],
            {"count": 0, "variants": set(), "occupiable_values": set(), "cells": []},
        )
        entry["count"] += 1
        entry["variants"].add(contract.variant_key(rec["variant"]))
        entry["occupiable_values"].add(rec["occupiable"])
        entry["cells"].append(f"{rec['case_id']}:{rec['cell']}")

    type_report = {
        key: {
            "count": value["count"],
            "variants": sorted(value["variants"]),
            "occupiable_values": sorted(value["occupiable_values"]),
            "cells": sorted(value["cells"]),
        }
        for key, value in sorted(types.items())
    }

    return {
        "status": "PASS",
        "mode": "locked_checkpoint_inventory",
        "checkpoint_sha256": checkpoint_hash,
        "production_case_count": len(case_reports),
        "object_count": len(all_records),
        "object_semantics_sha256": contract.fingerprint(all_records),
        "cases": case_reports,
        "types": type_report,
    }


def runtime_fingerprint(path: Path) -> tuple[str, int, int]:
    runtime = contract.load_json(path)
    records, errors, cases = contract.validate_runtime(runtime)
    if errors:
        raise InventoryError("runtime validation failed: " + "; ".join(errors))
    return contract.fingerprint(records), len(records), len(cases)


def self_test() -> None:
    def board(title: str, cols: int, rows: int, item: str, index: int, *, occupiable: bool) -> dict[str, Any]:
        size = cols * rows
        furniture: list[Any] = [None] * size
        variants: list[Any] = [None] * size
        occupied = [False] * size
        furniture[index] = item
        variants[index] = "illustrated-1"
        occupied[index] = occupiable
        return {
            "rows": rows,
            "cols": cols,
            "caseTitle": title,
            "roomNames": ["Room"],
            "rooms": [0] * size,
            "furniture": furniture,
            "furnitureVariants": variants,
            "occupiable": occupied,
            "placement": [],
            "characters": [],
        }

    a = board("Case A", 6, 6, "deskchair", 7, occupiable=True)
    b = board("Case B", 9, 9, "locker", 40, occupiable=False)
    checkpoint = {
        "format": "shigai-book",
        "pages": [
            {"preGeneratedBoards": [a]},
            {"preGeneratedBoards": [json.loads(json.dumps(a))]},
            {"preGeneratedBoards": [b]},
            {"preGeneratedBoards": [json.loads(json.dumps(b))]},
        ],
    }
    fake_hash = hashlib.sha256(b"locked-test-checkpoint").hexdigest()
    manifest = {
        "source": {"checkpoint_sha256": fake_hash},
        "cases": [
            {"id": "HMDA_A", "raw_title": "Case A", "grid": "6x6", "checkpoint": {"scene_index": 0, "clues_index": 1}},
            {"id": "HMDA_B", "raw_title": "Case B", "grid": "9x9", "checkpoint": {"scene_index": 2, "clues_index": 3}},
        ],
    }
    report = build_inventory(checkpoint, manifest, fake_hash)
    assert report["status"] == "PASS"
    assert report["production_case_count"] == 2 and report["object_count"] == 2
    assert report["cases"]["HMDA_A"]["records"][0] == {
        "case_id": "HMDA_A", "cell": "B2", "type": "deskchair", "variant": "illustrated-1",
        "occupiable": True, "blocked": False,
    }
    assert report["cases"]["HMDA_B"]["records"][0]["cell"] == "E5"

    drifted = json.loads(json.dumps(checkpoint))
    drifted["pages"][1]["preGeneratedBoards"][0]["furniture"][7] = "stool"
    try:
        build_inventory(drifted, manifest, fake_hash)
    except InventoryError as exc:
        assert "same source board" in str(exc)
    else:
        raise AssertionError("scene/clue semantic drift must fail closed")

    try:
        build_inventory(checkpoint, manifest, "0" * 64)
    except InventoryError as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("checkpoint hash drift must fail closed")

    print("PASS: checkpoint-bound modern-prop inventory preserves exact source semantics")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--runtime", type=Path, help="Optional generated runtime to cross-check semantic fingerprint.")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.checkpoint is None or args.report is None:
        ap.error("--checkpoint and --report are required unless --self-test is selected")

    try:
        checkpoint_path = args.checkpoint.expanduser().resolve()
        manifest = bridge.load_yaml(args.manifest.expanduser().resolve())
        checkpoint = bridge.load_checkpoint(checkpoint_path)
        checkpoint_hash = bridge.sha256(checkpoint_path)
        report = build_inventory(checkpoint, manifest, checkpoint_hash)
        if args.runtime is not None:
            fp, object_count, case_count = runtime_fingerprint(args.runtime.expanduser().resolve())
            report["runtime_crosscheck"] = {
                "runtime_object_semantics_sha256": fp,
                "runtime_object_count": object_count,
                "runtime_case_count": case_count,
                "matches": fp == report["object_semantics_sha256"],
            }
            if not report["runtime_crosscheck"]["matches"]:
                raise InventoryError(
                    "source inventory fingerprint does not match generated runtime fingerprint"
                )
        args.report.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        args.report.expanduser().resolve().write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, json.JSONDecodeError, bridge.BridgeError, InventoryError, contract.ContractError) as exc:
        print(f"HMDA MODERN PROP SOURCE INVENTORY: BLOCKED - {exc}", file=sys.stderr)
        return 2

    print(
        "PASS: locked checkpoint inventory: "
        f"{report['production_case_count']} cases, {report['object_count']} objects, "
        f"fingerprint {report['object_semantics_sha256']}"
    )
    if report.get("runtime_crosscheck"):
        print("PASS: generated runtime object fingerprint matches locked checkpoint inventory")
    print(f"PASS: report = {args.report.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
