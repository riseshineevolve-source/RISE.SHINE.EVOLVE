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
    ap.add_argument("--base", default=TOOL_ROOT / "content" / "book1_en_phase1.yml", type=Path)
    ap.add_argument("--phase2", default=TOOL_ROOT / "content" / "book1_en_phase2.yml", type=Path)
    ap.add_argument("--phase3", default=TOOL_ROOT / "content" / "book1_en_phase3.yml", type=Path)
    ap.add_argument("--story-spine", default=TOOL_ROOT / "content" / "book1_story_spine.yml", type=Path)
    ap.add_argument(
        "--spatial-assets",
        default=None,
        type=Path,
        help="Optional PRIVATE generated Map Factory asset manifest for release builds.",
    )
    ap.add_argument("--output", default=TOOL_ROOT / "dist" / "book1_en_master.yml", type=Path)
    args = ap.parse_args()

    base = load(args.base.resolve())
    phase2 = load(args.phase2.resolve())
    phase3 = load(args.phase3.resolve())
    story_spine = load(args.story_spine.resolve())

    base_missions = base.get("missions", [])
    base_nums = [int(m["number"]) for m in base_missions]
    if base_nums != [1, 2, 3, 4, 5]:
        raise SystemExit(f"phase1 source must contain Cases 01-05, got {base_nums}")

    validate_tranche("phase2", phase2, list(range(6, 17)))
    validate_tranche("phase3", phase3, list(range(17, 31)))

    master = copy.deepcopy(base)
    master["missions"] = (
        copy.deepcopy(base_missions)
        + copy.deepcopy(phase2["missions"])
        + copy.deepcopy(phase3["missions"])
    )
    master.pop("preview_end", None)
    master["story_spine"] = copy.deepcopy(story_spine)
    master.setdefault("book", {})["edition"] = "KDP Launch Candidate EN"
    master["production_state"] = {
        "format": "hmda-book1-master",
        "version": 1,
        "source_tranches": [
            "content/book1_en_phase1.yml#cases-01-05",
            "content/book1_en_phase2.yml#cases-06-16",
            "content/book1_en_phase3.yml#cases-17-30",
            "content/book1_story_spine.yml#big-case-interludes",
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

    expected_spatial = {
        2: "HMDA_02", 4: "HMDA_04", 6: "HMDA_06", 7: "HMDA_07", 10: "HMDA_10",
        12: "HMDA_12", 13: "HMDA_13", 15: "HMDA_15", 17: "HMDA_17", 19: "HMDA_19",
        20: "HMDA_20", 22: "HMDA_22", 23: "HMDA_23", 25: "HMDA_25", 29: "HMDA_29",
    }
    actual_spatial = {
        int(m["number"]): str(m["spatial_source_id"])
        for m in master["missions"] if m.get("spatial_source_id")
    }
    if actual_spatial != expected_spatial:
        raise SystemExit(f"master spatial mapping mismatch: {actual_spatial}")

    if args.spatial_assets is not None:
        asset_doc = load(args.spatial_assets.expanduser().resolve())
        asset_cases = asset_doc.get("cases", {})
        if not isinstance(asset_cases, dict):
            raise SystemExit("spatial asset manifest must contain a cases mapping")
        expected_ids = list(expected_spatial.values())
        if sorted(asset_cases) != sorted(expected_ids):
            raise SystemExit(
                "spatial asset manifest must contain exactly the locked 15 case IDs; "
                f"got {sorted(asset_cases)}"
            )
        by_id = {str(m.get("spatial_source_id")): m for m in master["missions"] if m.get("spatial_source_id")}
        for source_id in expected_ids:
            info = copy.deepcopy(asset_cases[source_id])
            for key in ("puzzle_asset", "solution_asset", "rows", "columns", "source_pdf_sha256"):
                if key not in info:
                    raise SystemExit(f"{source_id}: spatial asset manifest missing {key}")
            if str(info["source_pdf_sha256"]) != "6662c292642f3d66148e41eef180bb7d2b15a0975ca822981f4f33aa7153aada":
                raise SystemExit(f"{source_id}: unexpected source PDF SHA-256")
            info["asset_manifest"] = str(args.spatial_assets.expanduser().resolve())
            by_id[source_id]["spatial"] = info
        master["production_state"]["spatial_assets_attached"] = True
    else:
        master["production_state"]["spatial_assets_attached"] = False
    for mission in master["missions"]:
        hints = mission.get("hints")
        if not isinstance(hints, list) or len(hints) != 3:
            raise SystemExit(f"master case {mission['number']}: expected exactly 3 hint levels")

    beats = story_spine.get("beats", [])
    expected_beats = [5, 9, 16, 21, 25, 29]
    actual_beats = [int(b.get("after_case")) for b in beats]
    if actual_beats != expected_beats:
        raise SystemExit(f"story spine beats {actual_beats} != {expected_beats}")
    for beat in beats:
        squad = beat.get("squad") or []
        if not squad:
            raise SystemExit(f"story spine after Case {beat.get('after_case')} has no Happy Makers beat")
        for line in squad:
            if line.get("speaker") not in master.get("characters", {}):
                raise SystemExit(
                    f"story spine after Case {beat.get('after_case')}: unknown speaker {line.get('speaker')!r}"
                )

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
