#!/usr/bin/env python3
"""Validate the locked HMDA spatial-source selection against a native Shigai checkpoint.

This is the production gate between Shigai and the RSE Map Factory. It does
not infer clues from artwork. It reads the native checkpoint and proves that:

* the selected source title/page is the one declared in the lock file;
* the stored answer/coordinate matches Shigai's murderer/target index;
* source placements obey one-person-per-row and one-person-per-column;
* no person is placed on a non-occupiable source cell;
* the stored answer is the unique person sharing the source owner's room;
* the final RSE room/zone skin covers every source room index exactly once;
* every marked case has exactly one empty final ROOM, and its first letter
  produces CHECK THE OLD MAP in book order.

It is deliberately a structural validation layer. Shigai remains the source
logic engine for the raw clue solution; later RSE clue rewrites must receive a
second semantic/solver validation before publication.

Example:
    python scripts/validate_spatial_source_manifest.py \
      --manifest content/spatial_source_manifest_final.yml \
      --skin content/spatial_room_skin.yml \
      --checkpoint /path/to/HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cell(index: int, cols: int) -> str:
    row0, col0 = divmod(index, cols)
    if cols > 26:
        raise ValueError("This validator currently expects <=26 columns.")
    return f"{chr(65 + col0)}{row0 + 1}"


def source_board(checkpoint: dict[str, Any], scene_index: int) -> dict[str, Any]:
    pages = checkpoint.get("pages", [])
    if not 0 <= scene_index < len(pages):
        raise ValueError(f"scene_index {scene_index} outside checkpoint")
    page = pages[scene_index]
    if page.get("settings", {}).get("murdokuPagePart") != "scene":
        raise ValueError(f"checkpoint page {scene_index} is not a scene page")
    boards = page.get("preGeneratedBoards") or []
    if len(boards) != 1:
        raise ValueError(f"checkpoint page {scene_index} does not contain exactly one board")
    return boards[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--skin", required=True)
    ap.add_argument("--checkpoint", required=True)
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    skin_path = Path(args.skin)
    checkpoint_path = Path(args.checkpoint)

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    skin = yaml.safe_load(skin_path.read_text(encoding="utf-8"))
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    warnings: list[str] = []

    expected_hash = manifest.get("source", {}).get("checkpoint_sha256")
    actual_hash = sha256(checkpoint_path)
    if expected_hash and actual_hash != expected_hash:
        errors.append(f"checkpoint SHA256 mismatch: expected {expected_hash}, got {actual_hash}")

    skin_cases = skin.get("cases", {})
    letters: list[str] = []

    for case in manifest.get("cases", []):
        cid = case["id"]
        scene_index = int(case["checkpoint"]["scene_index"])
        try:
            board = source_board(checkpoint, scene_index)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{cid}: {exc}")
            continue

        if board.get("caseTitle") != case.get("raw_title"):
            errors.append(
                f"{cid}: raw title mismatch: manifest={case.get('raw_title')!r}, "
                f"checkpoint={board.get('caseTitle')!r}"
            )

        rows, cols = int(board["rows"]), int(board["cols"])
        declared_grid = str(case.get("grid", "")).lower().replace("×", "x")
        if declared_grid != f"{cols}x{rows}":
            errors.append(f"{cid}: grid mismatch: manifest={declared_grid}, checkpoint={cols}x{rows}")

        placements = board["placement"]
        characters = board["characters"]
        room_ids = board["rooms"]
        occupiable = board["occupiable"]

        coords = [cell(p, cols) for p in placements]
        row_values = [p // cols for p in placements]
        col_values = [p % cols for p in placements]
        if len(row_values) != len(set(row_values)):
            errors.append(f"{cid}: source placement violates one-person-per-row")
        if len(col_values) != len(set(col_values)):
            errors.append(f"{cid}: source placement violates one-person-per-column")
        for ch, p in zip(characters, placements):
            if not occupiable[p]:
                errors.append(f"{cid}: {ch['name']} is placed on blocked source cell {cell(p, cols)}")

        answer_index = int(board["murdererIndex"])
        victim_index = int(board["victimIndex"])
        answer_name = characters[answer_index]["name"]
        answer_coord = coords[answer_index]
        declared_answer = case.get("source_answer", {})
        if answer_name != declared_answer.get("name") or answer_coord != declared_answer.get("coordinate"):
            errors.append(
                f"{cid}: stored source answer mismatch: checkpoint={answer_name}@{answer_coord}, "
                f"manifest={declared_answer.get('name')}@{declared_answer.get('coordinate')}"
            )

        victim_room = room_ids[placements[victim_index]]
        companions = [
            i for i, p in enumerate(placements)
            if i != victim_index and room_ids[p] == victim_room
        ]
        if companions != [answer_index]:
            errors.append(
                f"{cid}: source owner's room does not contain exactly the source answer; "
                f"companions={[characters[i]['name'] for i in companions]}, expected={answer_name}"
            )

        declared_grade = str(case.get("grade", "")).lower()
        source_grade = str(board.get("gradeMetrics", {}).get("grade", "")).lower()
        if source_grade and not declared_grade.startswith(source_grade):
            errors.append(f"{cid}: grade mismatch: manifest={declared_grade!r}, checkpoint={source_grade!r}")

        room_skin = skin_cases.get(cid, {}).get("rooms")
        if not isinstance(room_skin, dict):
            errors.append(f"{cid}: missing room skin")
            continue
        normalized_skin = {int(k): v for k, v in room_skin.items()}
        expected_room_ids = set(range(len(board["roomNames"])))
        if set(normalized_skin) != expected_room_ids:
            errors.append(
                f"{cid}: room skin indexes {sorted(normalized_skin)} do not cover source room indexes "
                f"{sorted(expected_room_ids)}"
            )
            continue

        occupancy = {rid: 0 for rid in expected_room_ids}
        for p in placements:
            occupancy[room_ids[p]] += 1

        meta = case.get("meta")
        if meta:
            empty_rooms = [
                (rid, normalized_skin[rid])
                for rid in expected_room_ids
                if normalized_skin[rid].get("kind") == "room" and occupancy[rid] == 0
            ]
            if len(empty_rooms) != 1:
                errors.append(
                    f"{cid}: expected exactly one empty RSE ROOM, found "
                    f"{[(r, x.get('final_name')) for r, x in empty_rooms]}"
                )
            else:
                rid, meta_room = empty_rooms[0]
                letter = str(meta.get("letter", ""))
                declared_name = str(meta.get("room", ""))
                if meta_room.get("final_name") != declared_name:
                    errors.append(
                        f"{cid}: manifest meta room {declared_name!r} != skin meta room "
                        f"{meta_room.get('final_name')!r}"
                    )
                if not meta_room.get("meta_carrier"):
                    errors.append(f"{cid}: unique empty ROOM is not marked meta_carrier")
                if not str(meta_room.get("final_name", "")).upper().startswith(letter.upper()):
                    errors.append(
                        f"{cid}: meta room {meta_room.get('final_name')!r} does not start with {letter!r}"
                    )
                letters.append(letter)
        else:
            marked = [v for v in normalized_skin.values() if v.get("meta_carrier")]
            if marked:
                warnings.append(f"{cid}: non-meta case contains meta_carrier room skin")

    actual_message = "".join(letters)
    expected_message = str(manifest.get("meta_engine", {}).get("message", "")).replace(" ", "")
    if actual_message != expected_message:
        errors.append(f"meta message mismatch: {actual_message!r} != {expected_message!r}")

    if warnings:
        print("WARNINGS")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"PASS: {len(manifest.get('cases', []))} selected spatial modules match the locked checkpoint")
    print(f"PASS: meta message = {manifest['meta_engine']['message']}")
    print("PASS: source answer/coordinate, row-column uniqueness, occupiable cells, owner-answer relation, and ROOM/ZONE meta skin")


if __name__ == "__main__":
    main()
