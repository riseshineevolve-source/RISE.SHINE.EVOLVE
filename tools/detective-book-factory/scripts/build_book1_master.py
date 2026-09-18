#!/usr/bin/env python3
"""Assemble the durable 30-mission HMDA Book 1 master from locked source tranches."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
import yaml

TOOL_ROOT = Path(__file__).resolve().parents[1]
EXPECTED = list(range(1, 31))
REQUIRED = {
    "number", "rank", "type", "title", "guides", "hook", "objective",
    "dialogue", "meta_reveal", "nudge", "solution_steps",
}


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a YAML mapping")
    return data


def mission_numbers(doc: dict) -> list[int]:
    return [int(m["number"]) for m in doc.get("missions", [])]


def validate_tranche(name: str, doc: dict, expected: list[int]) -> None:
    nums = mission_numbers(doc)
    if nums != expected:
        raise SystemExit(f"{name}: expected missions {expected}, got {nums}")
    for mission in doc.get("missions", []):
        missing = sorted(REQUIRED - set(mission))
        if missing:
            raise SystemExit(f"{name} case {mission.get('number')}: missing keys {missing}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=TOOL_ROOT / "content" / "book1_en_production.yml", type=Path)
    ap.add_argument("--phase2", default=TOOL_ROOT / "content" / "book1_en_phase2.yml", type=Path)
    ap.add_argument("--phase3", default=TOOL_ROOT / "content" / "book1_en_phase3.yml", type=Path)
    ap.add_argument("--output", default=TOOL_ROOT / "dist" / "book1_en_master.yml", type=Path)
    args = ap.parse_args()

    base = load(args.base.resolve())
    phase2 = load(args.phase2.resolve())
    phase3 = load(args.phase3.resolve())

    base_missions = base.get("missions", [])
    base_nums = [int(m["number"]) for m in base_missions]
    if base_nums != [1, 2, 3, 4, 5]:
        raise SystemExit(f"base production source must contain Cases 01-05, got {base_nums}")

    validate_tranche("phase2", phase2, list(range(6, 17)))
    validate_tranche("phase3", phase3, list(range(17, 31)))

    master = copy.deepcopy(base)
    master["missions"] = (
        copy.deepcopy(base_missions)
        + copy.deepcopy(phase2["missions"])
        + copy.deepcopy(phase3["missions"])
    )
    master.pop("preview_end", None)
    master.setdefault("book", {})["edition"] = "KDP Launch Candidate EN"
    master["production_state"] = {
        "format": "hmda-book1-master",
        "version": 1,
        "source_tranches": [
            "content/book1_en_production.yml#cases-01-05",
            "content/book1_en_phase2.yml#cases-06-16",
            "content/book1_en_phase3.yml#cases-17-30",
        ],
        "spatial_truth": [
            "content/spatial_source_manifest_final.yml",
            "SPATIAL_SOURCE_LOCK.md",
            "content/spatial_room_skin.yml",
        ],
        "release_note": (
            "This master is reproducible from GitHub. Final KDP release remains blocked "
            "until all spatial cases use validated final Map Factory assets and strict preflight passes."
        ),
    }

    nums = mission_numbers(master)
    if nums != EXPECTED:
        raise SystemExit(f"master assembly failed: expected Cases 01-30, got {nums}")
    for mission in master["missions"]:
        missing = sorted(REQUIRED - set(mission))
        if missing:
            raise SystemExit(f"master case {mission['number']}: missing required keys {missing}")

    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(
        yaml.safe_dump(master, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )
    print(f"PASS: assembled canonical HMDA Book 1 master with {len(master['missions'])} missions")
    print(f"OUTPUT: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
