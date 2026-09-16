#!/usr/bin/env python3
"""Import raw geometry from a native Shigai checkpoint into the canonical
HMDA spatial-map manifest format.

This tool only moves MECHANICAL, verifiable facts out of a Shigai checkpoint
JSON: grid size, room partition, furniture footprints/types, blocked cells,
character placements, and victim/answer identity. It never invents or infers
clue logic. Normalized `constraints` (the reader-facing deduction rules) are
intentionally NOT generated here -- they must be hand-authored from the
checkpoint's own `characters[].clue` text and reviewed by a human, then
proven against the checkpoint's own verified placement by
`validate_spatial_map_pilot.py`. Automating that translation would risk
guessing puzzle logic, which this pipeline must never do.

Usage:
    python scripts/build_spatial_map_pilot_manifest.py \
        --checkpoint "<path to HMDA_checkpoint_11.shigai.json>" \
        --board-index 9 --case-id HMDA_10

Prints a YAML fragment (topology only) for one board to stdout. Review it,
then hand-merge it into content/spatial_map_pilots.yml and add the
constraints/source/solver/integrity sections.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]

import sys
sys.path.insert(0, str(HERE.parent))
from validate_spatial_map_pilot import column_label, format_cell  # noqa: E402

# Furniture types that fully occupy a cell (nobody can stand there). Derived
# directly from each checkpoint's own `occupiable` flags -- never assumed.
BLOCKING_BY_DEFAULT: set[str] = set()


def load_board(checkpoint_path: Path, board_index: int) -> dict[str, Any]:
    document = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    pages = document["pages"]
    if not (0 <= board_index < len(pages)):
        raise SystemExit(f"board-index {board_index} out of range (0..{len(pages) - 1})")
    boards = pages[board_index].get("preGeneratedBoards")
    if not boards:
        raise SystemExit(f"pages[{board_index}] has no preGeneratedBoards")
    return boards[0]


def cell_for_flat_index(index: int, cols: int) -> str:
    row0, col0 = divmod(index, cols)
    return format_cell(col0 + 1, row0 + 1)


def build_rooms(board: dict[str, Any]) -> list[dict[str, Any]]:
    room_names: list[str] = board["roomNames"]
    rooms_flat: list[int] = board["rooms"]
    cols = board["cols"]
    cells_by_room: dict[int, list[str]] = {i: [] for i in range(len(room_names))}
    for flat_index, room_index in enumerate(rooms_flat):
        cells_by_room[room_index].append(cell_for_flat_index(flat_index, cols))
    return [
        {"id": f"room_{i}", "name": room_names[i], "cells": cells_by_room[i]}
        for i in range(len(room_names))
    ]


def build_objects(board: dict[str, Any]) -> list[dict[str, Any]]:
    furniture: list[str | None] = board["furniture"]
    occupiable: list[bool] = board["occupiable"]
    cols = board["cols"]
    counters: dict[str, int] = {}
    objects: list[dict[str, Any]] = []
    for flat_index, kind in enumerate(furniture):
        if kind is None:
            continue
        counters[kind] = counters.get(kind, 0) + 1
        object_id = f"{kind}_{counters[kind]}"
        objects.append({
            "id": object_id,
            "type": kind,
            "cell": cell_for_flat_index(flat_index, cols),
            # occupiable=false means the furniture fills the whole cell.
            "blocked": occupiable[flat_index] is False,
        })
    return objects


def build_people(board: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    characters: list[dict[str, Any]] = board["characters"]
    placement: list[int] = board["placement"]
    cols = board["cols"]
    victim_index = board["victimIndex"]
    murderer_index = board["murdererIndex"]
    people = []
    for i, character in enumerate(characters):
        person_id = character["name"].strip().lower()
        people.append({
            "id": person_id,
            "display_name": character["name"],
            "placement": cell_for_flat_index(placement[i], cols),
            "raw_clue": character["clue"],
            "is_victim": i == victim_index,
        })
    answer = {
        "person_id": characters[murderer_index]["name"].strip().lower(),
        "coordinate": cell_for_flat_index(placement[murderer_index], cols),
        "source_identity": characters[murderer_index]["name"],
    }
    return people, answer


def build_topology(case_id: str, board: dict[str, Any]) -> dict[str, Any]:
    people, answer = build_people(board)
    return {
        "id": case_id,
        "raw_title": board["caseTitle"],
        "grid": {"rows": board["rows"], "columns": board["cols"]},
        "rooms": build_rooms(board),
        "objects": build_objects(board),
        "people": people,
        "answer": answer,
        "grade": board.get("gradeMetrics", {}).get("grade"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Path to the Shigai checkpoint JSON.")
    parser.add_argument("--board-index", type=int, required=True,
                         help="0-based index into the checkpoint's pages[] array.")
    parser.add_argument("--case-id", required=True, help="Canonical HMDA pilot case id, e.g. HMDA_10.")
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    board = load_board(checkpoint_path, args.board_index)
    topology = build_topology(args.case_id, board)
    print(yaml.safe_dump(topology, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
