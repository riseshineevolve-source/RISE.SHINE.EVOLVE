#!/usr/bin/env python3
"""Validate the HMDA modern-prop presentation contract without changing puzzle logic.

The locked Shigai-derived runtime remains authoritative for object identity,
cell, variant and blocked/occupiable semantics. This validator inventories those
objects, checks a presentation catalog for complete semantic-safe coverage and
emits a fingerprint that presentation work must not change.

Use --inventory-only before the real catalog is populated. Default mode fails
closed when any runtime object has no catalog entry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

TOOL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = TOOL_ROOT / "content" / "modern_prop_catalog.template.yml"


class ContractError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractError(f"{path} must contain a JSON object.")
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContractError(f"{path} must contain a YAML mapping.")
    return data


def parse_cell(cell: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", str(cell).strip().upper())
    if not match:
        raise ContractError(f"Invalid object cell {cell!r}.")
    col = 0
    for ch in match.group(1):
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(match.group(2)) - 1


def immutable_record(case_id: str, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "cell": str(obj.get("cell", "")),
        "type": obj.get("type"),
        "variant": obj.get("variant"),
        "occupiable": obj.get("occupiable"),
        "blocked": obj.get("blocked"),
    }


def fingerprint(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        sorted(
            records,
            key=lambda item: (
                str(item["case_id"]),
                str(item["cell"]),
                str(item["type"]),
                json.dumps(item["variant"], sort_keys=True, default=str),
            ),
        ),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def variant_key(value: Any) -> str:
    if value is None:
        return "__none__"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def resolve_mapping(catalog: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any] | None:
    source_type = obj.get("type")
    types = catalog.get("types", {})
    if not isinstance(types, dict) or source_type not in types:
        return None
    mapping = types[source_type]
    if not isinstance(mapping, dict):
        raise ContractError(f"Catalog type {source_type!r} must map to an object.")

    overrides = mapping.get("variants", {})
    if overrides is not None and not isinstance(overrides, dict):
        raise ContractError(f"Catalog variants for {source_type!r} must be a mapping.")
    override = (overrides or {}).get(variant_key(obj.get("variant")))
    if override is None:
        return mapping
    if not isinstance(override, dict):
        raise ContractError(
            f"Catalog variant override {source_type!r}/{variant_key(obj.get('variant'))!r} "
            "must be a mapping."
        )
    merged = dict(mapping)
    merged.pop("variants", None)
    merged.update(override)
    return merged


def validate_runtime(runtime: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    case_summary: dict[str, Any] = {}

    if runtime.get("format") != "hmda-shigai-runtime":
        errors.append("runtime format must be 'hmda-shigai-runtime'")

    cases = runtime.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("runtime must contain a non-empty cases list")
        return records, errors, case_summary

    seen_case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("runtime case entry is not an object")
            continue
        cid = case.get("id")
        if not isinstance(cid, str) or not cid:
            errors.append("runtime case has invalid id")
            continue
        if cid in seen_case_ids:
            errors.append(f"{cid}: duplicate case id")
            continue
        seen_case_ids.add(cid)

        grid = case.get("grid", {})
        try:
            rows = int(grid["rows"])
            cols = int(grid["columns"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{cid}: invalid grid")
            continue
        if rows <= 0 or cols <= 0:
            errors.append(f"{cid}: grid dimensions must be positive")
            continue

        objects = case.get("objects", [])
        if not isinstance(objects, list):
            errors.append(f"{cid}: objects must be a list")
            continue

        seen_cells: set[str] = set()
        type_counts: dict[str, int] = {}
        for index, obj in enumerate(objects):
            if not isinstance(obj, dict):
                errors.append(f"{cid}: object {index} is not an object")
                continue
            missing = [key for key in ("cell", "type", "occupiable", "blocked") if key not in obj]
            if missing:
                errors.append(f"{cid}: object {index} missing {', '.join(missing)}")
                continue
            cell = str(obj["cell"]).upper()
            if cell in seen_cells:
                errors.append(f"{cid}: multiple runtime objects occupy {cell}")
            seen_cells.add(cell)
            try:
                col, row = parse_cell(cell)
            except ContractError as exc:
                errors.append(f"{cid}: {exc}")
                continue
            if not (0 <= col < cols and 0 <= row < rows):
                errors.append(f"{cid}: object cell {cell} is outside {cols}x{rows}")
            if not isinstance(obj["occupiable"], bool) or not isinstance(obj["blocked"], bool):
                errors.append(f"{cid}/{cell}: occupiable and blocked must be booleans")
            elif obj["blocked"] == obj["occupiable"]:
                errors.append(
                    f"{cid}/{cell}: blocked must be the exact inverse of occupiable"
                )
            if not isinstance(obj["type"], str) or not obj["type"]:
                errors.append(f"{cid}/{cell}: object type must be a non-empty string")
            else:
                type_counts[obj["type"]] = type_counts.get(obj["type"], 0) + 1
            records.append(immutable_record(cid, obj))

        case_summary[cid] = {
            "grid": f"{cols}x{rows}",
            "object_count": len(objects),
            "type_counts": dict(sorted(type_counts.items())),
        }

    return records, errors, case_summary


def validate_catalog(
    records: list[dict[str, Any]],
    catalog: dict[str, Any],
    *,
    inventory_only: bool,
) -> tuple[list[str], list[dict[str, Any]], dict[str, int]]:
    errors: list[str] = []
    unmapped: list[dict[str, Any]] = []
    mapping_counts: dict[str, int] = {}

    if catalog.get("mode") != "presentation_only":
        errors.append("catalog mode must be 'presentation_only'")
    types = catalog.get("types", {})
    if not isinstance(types, dict):
        errors.append("catalog types must be a mapping")
        types = {}

    for rec in records:
        try:
            mapping = resolve_mapping(catalog, rec)
        except ContractError as exc:
            errors.append(str(exc))
            continue
        if mapping is None:
            unmapped.append(rec)
            continue

        key = mapping.get("presentation_key")
        if not isinstance(key, str) or not key.strip():
            errors.append(
                f"{rec['case_id']}/{rec['cell']}: catalog mapping for "
                f"{rec['type']!r} has no presentation_key"
            )
            continue

        allowed = mapping.get("allowed_occupiable")
        if not isinstance(allowed, list) or not allowed or any(not isinstance(v, bool) for v in allowed):
            errors.append(
                f"{rec['case_id']}/{rec['cell']}: {rec['type']!r} must declare "
                "non-empty boolean allowed_occupiable"
            )
            continue
        if rec["occupiable"] not in allowed:
            errors.append(
                f"{rec['case_id']}/{rec['cell']}: catalog {key!r} does not allow "
                f"occupiable={rec['occupiable']}"
            )
            continue

        render_box = mapping.get("render_box")
        if render_box not in {"cell_core", "cell_center_safe"}:
            errors.append(
                f"{rec['case_id']}/{rec['cell']}: {key!r} render_box must be "
                "'cell_core' or 'cell_center_safe'"
            )
            continue

        mapping_counts[key] = mapping_counts.get(key, 0) + 1

    if unmapped and not inventory_only:
        for rec in unmapped:
            errors.append(
                f"{rec['case_id']}/{rec['cell']}: no modern-prop mapping for "
                f"type={rec['type']!r} variant={rec['variant']!r}"
            )

    return errors, unmapped, dict(sorted(mapping_counts.items()))


def make_report(runtime: dict[str, Any], catalog: dict[str, Any], *, inventory_only: bool) -> dict[str, Any]:
    records, runtime_errors, cases = validate_runtime(runtime)
    catalog_errors, unmapped, mapping_counts = validate_catalog(
        records, catalog, inventory_only=inventory_only
    )
    errors = runtime_errors + catalog_errors

    by_type: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = str(rec["type"])
        info = by_type.setdefault(
            key,
            {
                "count": 0,
                "variants": set(),
                "occupiable_values": set(),
                "blocked_values": set(),
                "cells": [],
            },
        )
        info["count"] += 1
        info["variants"].add(variant_key(rec["variant"]))
        info["occupiable_values"].add(rec["occupiable"])
        info["blocked_values"].add(rec["blocked"])
        info["cells"].append(f"{rec['case_id']}:{rec['cell']}")

    serializable_types = {}
    for key, info in sorted(by_type.items()):
        serializable_types[key] = {
            "count": info["count"],
            "variants": sorted(info["variants"]),
            "occupiable_values": sorted(info["occupiable_values"]),
            "blocked_values": sorted(info["blocked_values"]),
            "cells": sorted(info["cells"]),
        }

    return {
        "status": "PASS" if not errors else "BLOCKED",
        "mode": "inventory_only" if inventory_only else "catalog_validation",
        "runtime_format": runtime.get("format"),
        "runtime_version": runtime.get("version"),
        "object_semantics_sha256": fingerprint(records),
        "object_count": len(records),
        "case_count": len(cases),
        "cases": cases,
        "types": serializable_types,
        "mapped_presentation_keys": mapping_counts,
        "unmapped_count": len(unmapped),
        "unmapped": unmapped,
        "errors": errors,
    }


def self_test() -> None:
    runtime = {
        "format": "hmda-shigai-runtime",
        "version": 1,
        "cases": [
            {
                "id": "HMDA_TEST",
                "grid": {"rows": 6, "columns": 6},
                "objects": [
                    {
                        "cell": "B2",
                        "type": "seat",
                        "variant": "a",
                        "occupiable": True,
                        "blocked": False,
                    },
                    {
                        "cell": "E4",
                        "type": "cabinet",
                        "variant": None,
                        "occupiable": False,
                        "blocked": True,
                    },
                ],
            }
        ],
    }
    catalog = {
        "version": 1,
        "mode": "presentation_only",
        "types": {
            "seat": {
                "presentation_key": "modern_seat",
                "allowed_occupiable": [True],
                "render_box": "cell_center_safe",
            },
            "cabinet": {
                "presentation_key": "modern_cabinet",
                "allowed_occupiable": [False],
                "render_box": "cell_core",
            },
        },
    }
    report = make_report(runtime, catalog, inventory_only=False)
    assert report["status"] == "PASS", report
    baseline = report["object_semantics_sha256"]

    # Presentation metadata may change; semantic fingerprint must not.
    catalog["types"]["seat"]["presentation_key"] = "modern_seat_v2"
    assert make_report(runtime, catalog, inventory_only=False)["object_semantics_sha256"] == baseline

    # Missing mapping fails in normal mode but inventory-only still reports it.
    missing = dict(catalog)
    missing["types"] = {"seat": catalog["types"]["seat"]}
    assert make_report(runtime, missing, inventory_only=False)["status"] == "BLOCKED"
    inv = make_report(runtime, missing, inventory_only=True)
    assert inv["status"] == "PASS" and inv["unmapped_count"] == 1, inv

    # Semantic drift fails even if the catalog is complete.
    broken = json.loads(json.dumps(runtime))
    broken["cases"][0]["objects"][0]["blocked"] = True
    assert make_report(broken, catalog, inventory_only=False)["status"] == "BLOCKED"

    print("PASS: modern-prop contract preserves immutable object semantics and fails closed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime", type=Path)
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--inventory-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.runtime is None:
        ap.error("--runtime is required unless --self-test is selected")

    try:
        runtime = load_json(args.runtime.expanduser().resolve())
        catalog = load_yaml(args.catalog.expanduser().resolve())
        report = make_report(runtime, catalog, inventory_only=args.inventory_only)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError, ContractError) as exc:
        print(f"HMDA MODERN PROP CONTRACT: BLOCKED - {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.report is not None:
        target = args.report.expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
