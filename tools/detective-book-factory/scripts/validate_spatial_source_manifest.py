#!/usr/bin/env python3
"""Validate the final HMDA spatial source manifest.

This is a structural gate, not a replacement for the Shigai logic engine.
It proves that the selected source modules still preserve:
- one person per row and column
- no person on a blocked cell
- the stored source answer sharing the owner's room uniquely
- the expected answer coordinate
- the Room Zero meta carrier: exactly one empty RSE ROOM whose initial
  matches CHECK THE OLD MAP in the fourteen marked cases

Run:
    python scripts/validate_spatial_source_manifest.py \
      --manifest content/spatial_source_manifest_final.yml
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import yaml

CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def col_num(label: str) -> int:
    n = 0
    for ch in label:
        n = n * 26 + ord(ch) - 64
    return n


def parse_cell(cell: str) -> tuple[int, int]:
    m = CELL_RE.fullmatch(cell)
    if not m:
        raise ValueError(f"Invalid cell: {cell}")
    return col_num(m.group(1)), int(m.group(2))


def validate_case(case: dict) -> list[str]:
    errors: list[str] = []
    cid = case["id"]
    rows = int(case["grid"]["rows"])
    cols = int(case["grid"]["columns"])
    people = case["people"]
    rooms = case["rooms"]
    objects = case.get("objects", [])

    room_for_cell: dict[str, str] = {}
    for room in rooms:
        for cell in room["cells"]:
            if cell in room_for_cell:
                errors.append(f"{cid}: overlapping room topology at {cell}")
            room_for_cell[cell] = room["id"]

    expected = {
        f"{chr(64 + c)}{r}"
        for r in range(1, rows + 1)
        for c in range(1, cols + 1)
    }
    if set(room_for_cell) != expected:
        errors.append(f"{cid}: rooms do not partition the full {cols}x{rows} grid")

    blocked = {obj["cell"] for obj in objects if obj.get("blocked") is True}
    coords = [p["coordinate"] for p in people]
    if len(coords) != len(set(coords)):
        errors.append(f"{cid}: duplicate person coordinate")

    row_values = [parse_cell(c)[1] for c in coords]
    col_values = [parse_cell(c)[0] for c in coords]
    if len(row_values) != len(set(row_values)):
        errors.append(f"{cid}: source placement violates one-person-per-row")
    if len(col_values) != len(set(col_values)):
        errors.append(f"{cid}: source placement violates one-person-per-column")

    for p in people:
        c, r = parse_cell(p["coordinate"])
        if not 1 <= c <= cols or not 1 <= r <= rows:
            errors.append(f"{cid}: {p['source_name']} outside grid at {p['coordinate']}")
        if p["coordinate"] in blocked:
            errors.append(f"{cid}: {p['source_name']} placed on blocked cell {p['coordinate']}")

    owner = next((p for p in people if p.get("is_owner")), None)
    answer = next((p for p in people if p.get("is_answer")), None)
    if owner is None or answer is None:
        errors.append(f"{cid}: missing owner or answer marker")
        return errors

    if answer["source_name"] != case["answer"]["source_name"]:
        errors.append(f"{cid}: answer identity mismatch")
    if answer["coordinate"] != case["answer"]["coordinate"]:
        errors.append(f"{cid}: answer coordinate mismatch")

    owner_room = room_for_cell[owner["coordinate"]]
    companions = [
        p for p in people
        if p is not owner and room_for_cell[p["coordinate"]] == owner_room
    ]
    if len(companions) != 1 or companions[0]["source_name"] != answer["source_name"]:
        errors.append(
            f"{cid}: owner room does not contain exactly the stored source answer "
            f"(companions={[p['source_name'] for p in companions]})"
        )

    if case.get("meta_letter"):
        counts = Counter(room_for_cell[p["coordinate"]] for p in people)
        empty_meta_rooms = [
            room for room in rooms
            if room.get("kind") == "room" and counts.get(room["id"], 0) == 0
        ]
        if len(empty_meta_rooms) != 1:
            errors.append(
                f"{cid}: expected exactly one empty ROOM for meta, found "
                f"{[r['final_name'] for r in empty_meta_rooms]}"
            )
        else:
            empty = empty_meta_rooms[0]
            if not empty.get("meta_carrier"):
                errors.append(f"{cid}: unique empty ROOM is not marked meta_carrier")
            if not empty["final_name"].upper().startswith(case["meta_letter"].upper()):
                errors.append(
                    f"{cid}: meta room {empty['final_name']!r} does not start with "
                    f"{case['meta_letter']!r}"
                )

    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    doc = yaml.safe_load(Path(args.manifest).read_text(encoding="utf-8"))
    errors: list[str] = []
    letters: list[str] = []

    for case in doc["cases"]:
        errors.extend(validate_case(case))
        if case.get("meta_letter"):
            letters.append(case["meta_letter"])

    message = "".join(letters)
    expected = doc["meta_engine"]["message"].replace(" ", "")
    if message != expected:
        errors.append(f"Meta letters {message!r} do not equal expected {expected!r}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"PASS: {len(doc['cases'])} selected spatial modules")
    print(f"PASS: meta message = {doc['meta_engine']['message']}")
    print("PASS: row/column placement, blocked-cell safety, owner-answer room relation, and meta-carrier checks")


if __name__ == "__main__":
    main()
