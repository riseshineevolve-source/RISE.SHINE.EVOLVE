#!/usr/bin/env python3
"""Build a deterministic local HMDA runtime bundle from a locked Shigai checkpoint.

The native checkpoint stays outside Git history. This bridge verifies its SHA,
extracts only the 15 production-selected boards and overlays the RSE ROOM/ZONE
skin without changing source topology or placements.

The output is generated evidence, not an editable source file.
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


class BridgeError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BridgeError(f"{path} must contain a mapping.")
    return data


def load_checkpoint(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != "shigai-book":
        raise BridgeError("Checkpoint is not a recognized Shigai book JSON.")
    pages = data.get("pages")
    if not isinstance(pages, list):
        raise BridgeError("Checkpoint has no pages list.")
    return data


def board_at(pages: list[Any], index: int, label: str) -> dict[str, Any]:
    if not isinstance(index, int) or index < 0 or index >= len(pages):
        raise BridgeError(f"{label}: page index {index!r} is outside checkpoint.")
    page = pages[index]
    settings = page.get("settings", {}) if isinstance(page, dict) else {}
    boards = settings.get("preGeneratedBoards", [])
    if not isinstance(boards, list) or len(boards) != 1 or not isinstance(boards[0], dict):
        raise BridgeError(f"{label}: expected exactly one preGeneratedBoard at page index {index}.")
    return boards[0]


def board_identity(board: dict[str, Any]) -> dict[str, Any]:
    characters = board.get("characters") or []
    return {
        "rows": board.get("rows"),
        "cols": board.get("cols"),
        "caseTitle": board.get("caseTitle"),
        "roomNames": board.get("roomNames"),
        "rooms": board.get("rooms"),
        "furniture": board.get("furniture"),
        "occupiable": board.get("occupiable"),
        "placement": board.get("placement"),
        "characters": [
            {
                "name": c.get("name"),
                "clue": c.get("clue"),
                "isVictim": c.get("isVictim"),
            }
            for c in characters
            if isinstance(c, dict)
        ],
    }


def column_label(index: int) -> str:
    if index < 0:
        raise BridgeError("Negative column index.")
    label = ""
    value = index + 1
    while value:
        value, rem = divmod(value - 1, 26)
        label = chr(ord("A") + rem) + label
    return label


def coordinate(cell_index: int, cols: int) -> str:
    if not isinstance(cell_index, int) or cell_index < 0:
        raise BridgeError(f"Invalid placement cell index: {cell_index!r}")
    row, col = divmod(cell_index, cols)
    return f"{column_label(col)}{row + 1}"


def parse_grid(value: Any) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)x(\d+)\s*", str(value))
    if not match:
        raise BridgeError(f"Invalid grid declaration: {value!r}")
    return int(match.group(1)), int(match.group(2))


def canonical_room_skin(
    case_id: str,
    board: dict[str, Any],
    skin_doc: dict[str, Any],
    cols: int,
) -> list[dict[str, Any]]:
    cases = skin_doc.get("cases", {})
    case_skin = cases.get(case_id) if isinstance(cases, dict) else None
    if not isinstance(case_skin, dict) or not isinstance(case_skin.get("rooms"), dict):
        raise BridgeError(f"{case_id}: missing ROOM/ZONE skin.")
    skin_rooms = case_skin["rooms"]

    room_ids = sorted(set(board.get("rooms") or []))
    room_names = board.get("roomNames") or []
    result: list[dict[str, Any]] = []
    for room_id in room_ids:
        if not isinstance(room_id, int):
            raise BridgeError(f"{case_id}: non-integer source room id {room_id!r}.")
        skin = skin_rooms.get(room_id)
        if skin is None:
            skin = skin_rooms.get(str(room_id))
        if not isinstance(skin, dict):
            raise BridgeError(f"{case_id}: source room {room_id} has no final skin.")
        kind = skin.get("kind")
        final_name = skin.get("final_name")
        if kind not in {"room", "zone"} or not isinstance(final_name, str) or not final_name.strip():
            raise BridgeError(f"{case_id}: invalid skin for source room {room_id}.")
        source_name = room_names[room_id] if room_id < len(room_names) else f"room_{room_id}"
        cells = [
            coordinate(index, cols)
            for index, value in enumerate(board.get("rooms") or [])
            if value == room_id
        ]
        result.append(
            {
                "source_room_id": room_id,
                "source_name": source_name,
                "final_name": final_name,
                "kind": kind,
                "meta_carrier": bool(skin.get("meta_carrier", False)),
                "cells": cells,
            }
        )
    return result


def build_case(
    declaration: dict[str, Any],
    pages: list[Any],
    skin_doc: dict[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    case_id = declaration.get("id")
    if not isinstance(case_id, str):
        raise BridgeError("Spatial case without id.")

    checkpoint_ref = declaration.get("checkpoint") or {}
    scene_index = checkpoint_ref.get("scene_index")
    clues_index = checkpoint_ref.get("clues_index")
    scene = board_at(pages, scene_index, f"{case_id} scene")
    clues = board_at(pages, clues_index, f"{case_id} clues")

    if board_identity(scene) != board_identity(clues):
        raise BridgeError(f"{case_id}: scene and clues pages do not resolve to the same source board.")

    board = scene
    rows = board.get("rows")
    cols = board.get("cols")
    if not isinstance(rows, int) or not isinstance(cols, int):
        raise BridgeError(f"{case_id}: invalid board size.")

    declared_cols, declared_rows = parse_grid(declaration.get("grid"))
    if (cols, rows) != (declared_cols, declared_rows):
        raise BridgeError(
            f"{case_id}: source grid is {cols}x{rows}, manifest expects {declared_cols}x{declared_rows}."
        )

    if board.get("caseTitle") != declaration.get("raw_title"):
        raise BridgeError(
            f"{case_id}: raw title mismatch: {board.get('caseTitle')!r} != {declaration.get('raw_title')!r}."
        )

    characters = board.get("characters") or []
    placements = board.get("placement") or []
    if len(characters) != len(placements):
        raise BridgeError(f"{case_id}: characters/placement length mismatch.")

    runtime_characters: list[dict[str, Any]] = []
    placement_by_name: dict[str, int] = {}
    for char, cell in zip(characters, placements):
        if not isinstance(char, dict) or not isinstance(char.get("name"), str):
            raise BridgeError(f"{case_id}: invalid source character.")
        name = char["name"]
        if name in placement_by_name:
            raise BridgeError(f"{case_id}: duplicate source character {name!r}.")
        placement_by_name[name] = cell
        runtime_characters.append(
            {
                "source_name": name,
                "gender": char.get("gender"),
                "portrait_id": char.get("portraitId"),
                "is_owner": bool(char.get("isVictim", False)),
                "raw_clue": char.get("clue"),
                "placement": coordinate(cell, cols),
            }
        )

    expected_answer = declaration.get("source_answer") or {}
    answer_name = expected_answer.get("name")
    answer_coord = expected_answer.get("coordinate")
    if answer_name not in placement_by_name:
        raise BridgeError(f"{case_id}: manifest answer {answer_name!r} is absent from source board.")
    actual_answer_coord = coordinate(placement_by_name[answer_name], cols)
    if actual_answer_coord != answer_coord:
        raise BridgeError(
            f"{case_id}: answer coordinate mismatch for {answer_name}: "
            f"{actual_answer_coord} != {answer_coord}."
        )

    source_rooms = board.get("rooms") or []
    if len(source_rooms) != rows * cols:
        raise BridgeError(f"{case_id}: room partition length does not match grid.")

    final_rooms = canonical_room_skin(case_id, board, skin_doc, cols)

    occupied_room_ids = {
        source_rooms[cell]
        for cell in placements
        if isinstance(cell, int) and 0 <= cell < len(source_rooms)
    }
    empty_final_rooms = [
        room
        for room in final_rooms
        if room["kind"] == "room" and room["source_room_id"] not in occupied_room_ids
    ]

    meta = declaration.get("meta")
    meta_evidence = None
    if meta is not None:
        if len(empty_final_rooms) != 1:
            names = [r["final_name"] for r in empty_final_rooms]
            raise BridgeError(
                f"{case_id}: expected exactly one empty final ROOM, found {len(names)}: {names}."
            )
        empty_room = empty_final_rooms[0]
        expected_letter = str(meta.get("letter", "")).upper()
        expected_room = meta.get("room")
        if empty_room["final_name"] != expected_room:
            raise BridgeError(
                f"{case_id}: empty ROOM is {empty_room['final_name']!r}, expected {expected_room!r}."
            )
        if not empty_room["final_name"].upper().startswith(expected_letter):
            raise BridgeError(
                f"{case_id}: meta room {empty_room['final_name']!r} does not carry {expected_letter!r}."
            )
        if not empty_room["meta_carrier"]:
            raise BridgeError(f"{case_id}: empty meta ROOM is not flagged meta_carrier in skin.")
        meta_evidence = {
            "letter": expected_letter,
            "room": empty_room["final_name"],
            "source_room_id": empty_room["source_room_id"],
        }

    furniture = board.get("furniture") or []
    occupiable = board.get("occupiable") or []
    if len(furniture) != rows * cols or len(occupiable) != rows * cols:
        raise BridgeError(f"{case_id}: furniture/occupiable vectors do not match grid.")

    objects = []
    labels = board.get("furnitureLabels") or {}
    variants = board.get("furnitureVariants") or []
    for index, item in enumerate(furniture):
        if item is None:
            continue
        objects.append(
            {
                "cell": coordinate(index, cols),
                "type": item,
                "display_label": labels.get(item, item),
                "variant": variants[index] if index < len(variants) else None,
                "occupiable": bool(occupiable[index]),
                "blocked": not bool(occupiable[index]),
            }
        )

    return {
        "id": case_id,
        "final_title": declaration.get("final_title"),
        "tier": declaration.get("tier"),
        "provenance": {
            "checkpoint_sha256": source_hash,
            "scene_index": scene_index,
            "clues_index": clues_index,
            "raw_title": board.get("caseTitle"),
        },
        "grid": {"rows": rows, "columns": cols},
        "rooms": final_rooms,
        "doors": board.get("doors") or [],
        "objects": objects,
        "characters": runtime_characters,
        "source_answer": {
            "name": answer_name,
            "coordinate": actual_answer_coord,
        },
        "source_owner": next(
            (c["source_name"] for c in runtime_characters if c["is_owner"]),
            None,
        ),
        "difficulty": {
            "declared_grade": declaration.get("grade"),
            "metrics": board.get("gradeMetrics") or {},
        },
        "source_solve_hints": board.get("solveHints") or [],
        "source_explain_steps": board.get("explainSteps") or [],
        "source_explain_steps_detailed": board.get("explainStepsDetailed") or [],
        "meta": meta_evidence,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument(
        "--manifest",
        default=TOOL_ROOT / "content" / "spatial_source_manifest_final.yml",
        type=Path,
    )
    ap.add_argument(
        "--skin",
        default=TOOL_ROOT / "content" / "spatial_room_skin.yml",
        type=Path,
    )
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    checkpoint_path = args.checkpoint.expanduser().resolve()
    manifest_path = args.manifest.expanduser().resolve()
    skin_path = args.skin.expanduser().resolve()
    output_path = args.output.expanduser().resolve()

    if not checkpoint_path.is_file():
        raise SystemExit(f"Checkpoint not found: {checkpoint_path}")

    manifest = load_yaml(manifest_path)
    skin = load_yaml(skin_path)
    checkpoint = load_checkpoint(checkpoint_path)

    actual_hash = sha256(checkpoint_path)
    expected_hash = str(manifest.get("source", {}).get("checkpoint_sha256", ""))
    if actual_hash != expected_hash:
        raise SystemExit(
            "BLOCKED: Shigai checkpoint SHA-256 mismatch. "
            f"expected {expected_hash}, got {actual_hash}"
        )

    errors: list[str] = []
    runtime_cases: list[dict[str, Any]] = []
    for declaration in manifest.get("cases", []):
        try:
            runtime_cases.append(
                build_case(declaration, checkpoint["pages"], skin, actual_hash)
            )
        except BridgeError as error:
            errors.append(str(error))

    if errors:
        print("HMDA SHIGAI BRIDGE: BLOCKED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    meta_message = "".join(
        case["meta"]["letter"] for case in runtime_cases if case["meta"] is not None
    )
    expected_message = str(manifest.get("meta_engine", {}).get("message", "")).replace(" ", "")
    if meta_message != expected_message:
        print(
            f"HMDA SHIGAI BRIDGE: BLOCKED - meta {meta_message!r} != {expected_message!r}",
            file=sys.stderr,
        )
        return 3

    payload = {
        "format": "hmda-shigai-runtime",
        "version": 1,
        "generated_from": {
            "checkpoint_filename": checkpoint_path.name,
            "checkpoint_sha256": actual_hash,
            "selection_manifest": manifest_path.name,
            "room_skin": skin_path.name,
        },
        "production_case_count": len(runtime_cases),
        "meta_message": meta_message,
        "cases": runtime_cases,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: extracted {len(runtime_cases)} locked HMDA spatial modules")
    print(f"PASS: meta message = {meta_message}")
    print(f"PASS: runtime bundle = {output_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BridgeError as error:
        print(f"HMDA SHIGAI BRIDGE: BLOCKED - {error}", file=sys.stderr)
        sys.exit(2)
