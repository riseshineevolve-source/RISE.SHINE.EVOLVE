#!/usr/bin/env python3
"""Compose and validate the canonical 30-mission HMDA Book 1 content graph."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
from typing import Any
import yaml

TOOL_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"number", "rank", "type", "title", "guides", "hook", "objective", "dialogue", "meta_reveal", "nudge", "solution_steps"}


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid YAML mapping: {path}")
    return data


def fail(msg: str) -> None:
    raise SystemExit(f"HMDA MASTER COMPOSE: FAIL - {msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=TOOL_ROOT / "content" / "book1_en_master.yml", type=Path)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    manifest_path = args.manifest.resolve()
    spec = load(manifest_path)
    comp = spec["composition"]

    base_path = TOOL_ROOT / comp["base"].replace("content/", "content/")
    base = load(base_path)
    result = {k: copy.deepcopy(v) for k, v in base.items() if k != "missions"}
    result["master"] = {
        "book_id": spec.get("book_id"),
        "status": spec.get("status"),
        "language": spec.get("language"),
        "composition_manifest": manifest_path.name,
    }

    missions: list[dict[str, Any]] = []
    seen: set[int] = set()
    for part in comp["mission_parts"]:
        part_path = TOOL_ROOT / part["path"].replace("content/", "content/")
        doc = load(part_path)
        nums = [int(m["number"]) for m in doc.get("missions", [])]
        expected = list(range(int(part["first"]), int(part["last"]) + 1))
        if nums != expected:
            fail(f"{part_path.name} mission range {nums} != {expected}")
        for mission in doc["missions"]:
            n = int(mission["number"])
            if n in seen:
                fail(f"duplicate mission {n}")
            seen.add(n)
            missions.append(copy.deepcopy(mission))

    expected_numbers = [int(n) for n in spec["expected"]["mission_numbers"]]
    actual_numbers = [int(m["number"]) for m in missions]
    if actual_numbers != expected_numbers:
        fail(f"mission order {actual_numbers} != {expected_numbers}")

    characters = result.get("characters", {})
    for m in missions:
        n = int(m["number"])
        missing = sorted(REQUIRED - set(m))
        if missing:
            fail(f"Case {n}: missing required keys {missing}")
        hints = m.get("hints")
        if not isinstance(hints, list) or len(hints) != int(spec["publication"]["hint_levels"]):
            fail(f"Case {n}: expected exactly {spec['publication']['hint_levels']} hint levels")
        if not m.get("solution_steps"):
            fail(f"Case {n}: no solution_steps")
        for d in m.get("dialogue", []):
            speaker = d.get("speaker")
            if speaker not in characters:
                fail(f"Case {n}: unknown Happy Maker speaker {speaker!r}")

    expected_spatial = {int(k): str(v) for k, v in spec["expected"]["spatial_cases"].items()}
    actual_spatial: dict[int, str] = {}
    for m in missions:
        if "spatial_source_id" in m:
            actual_spatial[int(m["number"])] = str(m["spatial_source_id"])
    if actual_spatial != expected_spatial:
        fail(f"spatial source mapping {actual_spatial} != {expected_spatial}")

    spatial_lock = load(TOOL_ROOT / "content" / "spatial_source_manifest_final.yml")
    locked_ids = [str(c["id"]) for c in spatial_lock.get("cases", [])]
    if list(expected_spatial.values()) != locked_ids:
        fail("master spatial mapping does not exactly match locked final 15-module order")

    expected_meta = str(spec["expected"]["meta_message"]).replace(" ", "")
    locked_meta = str(spatial_lock.get("meta_engine", {}).get("message", "")).replace(" ", "")
    if locked_meta != expected_meta:
        fail(f"locked meta {locked_meta!r} != {expected_meta!r}")

    result["missions"] = missions
    result["publication"] = copy.deepcopy(spec.get("publication", {}))
    result["source_parts"] = [p["path"] for p in comp["mission_parts"]]

    out = args.output.resolve() if args.output else TOOL_ROOT / comp["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")

    print(f"PASS: canonical HMDA master composed -> {out}")
    print("PASS: missions 01-30 complete")
    print("PASS: every mission has exactly 3 hint levels and solution steps")
    print("PASS: spatial source mapping matches the locked final 15-module bank")
    print(f"PASS: meta engine = {expected_meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
