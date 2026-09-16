#!/usr/bin/env python3
"""Validate a small HMDA spatial-map pilot without interpreting artwork.

The visual renderer consumes a canonical YAML map specification.  This checker
uses the same specification as the proof source for a map's topology,
coordinates, relationships, answer identity, and (when every raw constraint is
captured) unique solvability.  It deliberately does not OCR or infer logic
from a rendered image: that would make a production gate less deterministic,
not more.

Supported normalized constraint types are intentionally narrow.  Add a new
constraint type only when it is captured faithfully from verified source data;
never translate a prose clue into a guessed constraint just to make a solver
pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]
CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


class ValidationFailure(Exception):
    """Raised for a malformed canonical map specification."""


@dataclass(frozen=True)
class Cell:
    column: int
    row: int


@dataclass
class CaseModel:
    identifier: str
    raw: dict[str, Any]
    rows: int
    columns: int
    rooms: dict[str, dict[str, Any]]
    room_for_cell: dict[str, str]
    objects: dict[str, dict[str, Any]]
    people: dict[str, dict[str, Any]]
    blocked_cells: frozenset[str]
    constraints: list[dict[str, Any]]
    object_types: dict[str, list[str]]

    @property
    def cells(self) -> list[str]:
        return [format_cell(column, row) for row in range(1, self.rows + 1)
                for column in range(1, self.columns + 1)]

    @property
    def available_cells(self) -> list[str]:
        return [cell for cell in self.cells if cell not in self.blocked_cells]

    @property
    def solution(self) -> dict[str, str]:
        return {person_id: person["placement"] for person_id, person in self.people.items()}


@dataclass
class SolveResult:
    count: int
    solutions: list[dict[str, str]]
    nodes: int
    exhausted: bool


def as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationFailure(f"{label} must be a mapping.")
    return value


def as_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationFailure(f"{label} must be a list.")
    return value


def column_number(label: str) -> int:
    number = 0
    for character in label:
        if not ("A" <= character <= "Z"):
            raise ValidationFailure(f"Invalid coordinate column {label!r}.")
        number = number * 26 + (ord(character) - ord("A") + 1)
    return number


def column_label(number: int) -> str:
    if number < 1:
        raise ValidationFailure(f"Invalid coordinate column number {number}.")
    letters: list[str] = []
    while number:
        number, remainder = divmod(number - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def parse_cell(value: Any, rows: int, columns: int, label: str) -> Cell:
    if not isinstance(value, str):
        raise ValidationFailure(f"{label} must be a coordinate string.")
    match = CELL_RE.fullmatch(value.strip().upper())
    if not match:
        raise ValidationFailure(f"{label} has invalid coordinate {value!r}.")
    column = column_number(match.group(1))
    row = int(match.group(2))
    if column > columns or row > rows:
        raise ValidationFailure(
            f"{label} coordinate {value!r} is outside the {columns}x{rows} grid."
        )
    return Cell(column, row)


def format_cell(column: int, row: int) -> str:
    return f"{column_label(column)}{row}"


def normalized_cell(value: Any, rows: int, columns: int, label: str) -> str:
    cell = parse_cell(value, rows, columns, label)
    return format_cell(cell.column, cell.row)


def normalize_collection(value: Any, label: str) -> list[dict[str, Any]]:
    """Accept an id-keyed mapping or an ordered list with explicit ids."""
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        items = []
        for identifier, item in value.items():
            entry = dict(as_mapping(item, f"{label}.{identifier}"))
            entry.setdefault("id", identifier)
            items.append(entry)
    else:
        raise ValidationFailure(f"{label} must be a list or id-keyed mapping.")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        entry = dict(as_mapping(item, f"{label}[{index}]"))
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValidationFailure(f"{label}[{index}] needs a non-empty id.")
        entry["id"] = identifier.strip()
        normalized.append(entry)
    ids = [entry["id"] for entry in normalized]
    if len(ids) != len(set(ids)):
        raise ValidationFailure(f"{label} has duplicate ids.")
    return normalized


def constraint_type(constraint: dict[str, Any]) -> str:
    value = constraint.get("type")
    if not isinstance(value, str) or not value.strip():
        raise ValidationFailure("Every constraint needs a non-empty type.")
    return value.strip().lower().replace("-", "_")


SUPPORTED_CONSTRAINTS = {
    "exact",
    "exact_cell",
    "not_cell",
    "row",
    "not_row",
    "column",
    "not_column",
    "room",
    "not_room",
    "corner",
    "not_corner",
    "outer_wall",
    "not_outer_wall",
    "adjacent",
    "not_adjacent",
    "diagonal",
    "not_diagonal",
    "distance",
    "same_room",
    "different_room",
    "same_row",
    "different_row",
    "same_column",
    "different_column",
    "relative",
    "room_occupancy",
    "exclusive_companion",
    "on",
    "not_on",
    "one_of",
}


def build_model(raw_case: Any) -> CaseModel:
    case = dict(as_mapping(raw_case, "pilot case"))
    identifier = case.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValidationFailure("Each pilot case needs a non-empty id.")

    grid = as_mapping(case.get("grid"), f"{identifier}.grid")
    rows, columns = grid.get("rows"), grid.get("columns")
    if not isinstance(rows, int) or not isinstance(columns, int) or rows < 1 or columns < 1:
        raise ValidationFailure(f"{identifier}.grid needs positive integer rows and columns.")

    room_entries = normalize_collection(case.get("rooms"), f"{identifier}.rooms")
    rooms: dict[str, dict[str, Any]] = {}
    room_for_cell: dict[str, str] = {}
    for room in room_entries:
        name = room.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationFailure(f"{identifier}.rooms.{room['id']} needs a non-empty name.")
        cells = as_list(room.get("cells"), f"{identifier}.rooms.{room['id']}.cells")
        if not cells:
            raise ValidationFailure(f"{identifier}.rooms.{room['id']} has no cells.")
        normalized_cells = [
            normalized_cell(cell, rows, columns, f"{identifier}.rooms.{room['id']}.cells")
            for cell in cells
        ]
        if len(normalized_cells) != len(set(normalized_cells)):
            raise ValidationFailure(f"{identifier}.rooms.{room['id']} repeats a cell.")
        for cell in normalized_cells:
            if cell in room_for_cell:
                raise ValidationFailure(
                    f"{identifier} room topology overlaps at {cell}: "
                    f"{room_for_cell[cell]} and {room['id']}."
                )
            room_for_cell[cell] = room["id"]
        room["name"] = name.strip()
        room["cells"] = sorted(normalized_cells, key=cell_sort_key)
        rooms[room["id"]] = room

    expected_cells = {format_cell(column, row) for row in range(1, rows + 1)
                      for column in range(1, columns + 1)}
    if set(room_for_cell) != expected_cells:
        missing = sorted(expected_cells - set(room_for_cell), key=cell_sort_key)
        extra = sorted(set(room_for_cell) - expected_cells, key=cell_sort_key)
        parts: list[str] = []
        if missing:
            parts.append(f"missing room cells: {', '.join(missing)}")
        if extra:
            parts.append(f"out-of-grid room cells: {', '.join(extra)}")
        raise ValidationFailure(f"{identifier} rooms must partition the grid ({'; '.join(parts)}).")

    object_entries = normalize_collection(case.get("objects", []), f"{identifier}.objects")
    objects: dict[str, dict[str, Any]] = {}
    blocked_cells: set[str] = set()
    for obj in object_entries:
        footprint = obj.get("cells", obj.get("footprint"))
        if footprint is None:
            if "cell" not in obj:
                raise ValidationFailure(f"{identifier}.objects.{obj['id']} needs a cell or cells footprint.")
            footprint = [obj["cell"]]
        footprint = as_list(footprint, f"{identifier}.objects.{obj['id']}.cells")
        if not footprint:
            raise ValidationFailure(f"{identifier}.objects.{obj['id']} has an empty footprint.")
        obj["cells"] = sorted(
            [normalized_cell(cell, rows, columns, f"{identifier}.objects.{obj['id']}.cells")
             for cell in footprint],
            key=cell_sort_key,
        )
        if len(obj["cells"]) != len(set(obj["cells"])):
            raise ValidationFailure(f"{identifier}.objects.{obj['id']} repeats a footprint cell.")
        if "cell" in obj:
            obj["cell"] = normalized_cell(obj["cell"], rows, columns, f"{identifier}.objects.{obj['id']}.cell")
            if obj["cell"] not in obj["cells"]:
                raise ValidationFailure(
                    f"{identifier}.objects.{obj['id']}.cell must be inside its declared cells footprint."
                )
        else:
            obj["cell"] = obj["cells"][0]
        if obj.get("blocked") is True or obj.get("occupancy") == "blocked":
            blocked_cells.update(obj["cells"])
        objects[obj["id"]] = obj

    explicit_blocked_cells = as_list(case.get("blocked_cells", []), f"{identifier}.blocked_cells")
    blocked_cells.update(
        normalized_cell(cell, rows, columns, f"{identifier}.blocked_cells")
        for cell in explicit_blocked_cells
    )

    person_entries = normalize_collection(case.get("people"), f"{identifier}.people")
    if not person_entries:
        raise ValidationFailure(f"{identifier} needs at least one person.")
    people: dict[str, dict[str, Any]] = {}
    placements: set[str] = set()
    for person in person_entries:
        display_name = person.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            raise ValidationFailure(f"{identifier}.people.{person['id']} needs a display_name.")
        if "placement" not in person:
            raise ValidationFailure(f"{identifier}.people.{person['id']} needs a canonical placement.")
        person["display_name"] = display_name.strip()
        person["placement"] = normalized_cell(
            person["placement"], rows, columns, f"{identifier}.people.{person['id']}.placement"
        )
        if person["placement"] in placements:
            raise ValidationFailure(f"{identifier} places more than one person at {person['placement']}.")
        if person["placement"] in blocked_cells:
            raise ValidationFailure(
                f"{identifier} places {person['id']} on a canonical blocked cell {person['placement']}."
            )
        placements.add(person["placement"])
        people[person["id"]] = person

    constraints = [dict(as_mapping(item, f"{identifier}.constraints"))
                   for item in as_list(case.get("constraints", []), f"{identifier}.constraints")]
    unknown = sorted({constraint_type(constraint) for constraint in constraints} - SUPPORTED_CONSTRAINTS)
    if unknown:
        raise ValidationFailure(
            f"{identifier} has unsupported normalized constraint types: {', '.join(unknown)}. "
            "Do not claim solver uniqueness until they are implemented faithfully."
        )

    object_types: dict[str, list[str]] = {}
    for object_id, obj in objects.items():
        furniture_type = obj.get("type")
        if isinstance(furniture_type, str) and furniture_type.strip():
            object_types.setdefault(furniture_type.strip(), []).append(object_id)

    return CaseModel(
        identifier=identifier.strip(), raw=case, rows=rows, columns=columns,
        rooms=rooms, room_for_cell=room_for_cell, objects=objects, people=people,
        blocked_cells=frozenset(blocked_cells),
        constraints=constraints,
        object_types=object_types,
    )


def cell_sort_key(cell: str) -> tuple[int, int]:
    match = CELL_RE.fullmatch(cell)
    assert match is not None
    return int(match.group(2)), column_number(match.group(1))


def asset_paths(case: CaseModel) -> dict[str, str]:
    """Read renderer assets without locking the producer to one container key."""
    candidates: list[dict[str, Any]] = []
    for key in ("assets", "renderer"):
        value = case.raw.get(key)
        if isinstance(value, dict):
            candidates.append(value)
            nested = value.get("assets")
            if isinstance(nested, dict):
                candidates.append(nested)
    for candidate in candidates:
        puzzle = candidate.get("puzzle") or candidate.get("puzzle_asset")
        solution = candidate.get("solution") or candidate.get("solution_asset")
        if puzzle is not None or solution is not None:
            if not isinstance(puzzle, str) or not isinstance(solution, str):
                raise ValidationFailure(f"{case.identifier} needs both puzzle and solution renderer assets.")
            return {"puzzle": puzzle, "solution": solution}
    raise ValidationFailure(f"{case.identifier} is missing renderer asset paths.")


def check_asset_paths(case: CaseModel) -> list[str]:
    results: list[str] = []
    for kind, raw_path in asset_paths(case).items():
        path = (TOOL_ROOT / raw_path).resolve()
        try:
            path.relative_to(TOOL_ROOT.resolve())
        except ValueError as exc:
            raise ValidationFailure(f"{case.identifier} {kind} asset escapes the Book Factory: {raw_path}") from exc
        if not path.is_file() or path.stat().st_size == 0:
            raise ValidationFailure(f"{case.identifier} {kind} asset is missing or empty: {path}")
        results.append(f"{kind} asset exists: {path.relative_to(TOOL_ROOT)}")
    return results


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_hash_status(source: dict[str, Any], expected_checksum: str) -> str:
    """Verify a mounted raw PDF, but keep CI portable when private source is absent."""
    locator = source.get("local_path", source.get("source_path", source.get("locator")))
    if locator is None:
        return "raw-PDF checksum declared; source file is not mounted for local hash verification"
    if not isinstance(locator, str) or not locator.strip():
        raise ValidationFailure("source local_path/source_path/locator must be a non-empty string when supplied.")
    path = Path(locator)
    if not path.is_absolute():
        path = (TOOL_ROOT / path).resolve()
    if not path.is_file():
        return f"raw-PDF checksum declared; source file is not mounted at {path}"
    actual_checksum = sha256_file(path)
    if actual_checksum != expected_checksum:
        raise ValidationFailure(
            f"raw-PDF SHA-256 mismatch at {path}: expected {expected_checksum}, got {actual_checksum}."
        )
    return f"raw-PDF SHA-256 verified against mounted source: {actual_checksum}"


def check_source_identity(case: CaseModel) -> list[str]:
    source = as_mapping(case.raw.get("source"), f"{case.identifier}.source")
    source_reference = source.get("reference", source.get("pdf", source.get("file")))
    if not isinstance(source_reference, str) or not source_reference.strip():
        raise ValidationFailure(
            f"{case.identifier}.source needs a read-only raw-PDF reference for provenance."
        )
    source_checksum = source.get("sha256", source.get("pdf_sha256", source.get("checksum")))
    if not isinstance(source_checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", source_checksum):
        raise ValidationFailure(
            f"{case.identifier}.source needs the raw-PDF SHA-256 checksum used for extraction."
        )
    puzzle_page = source.get("puzzle_page", source.get("grid_page", source.get("source_page")))
    solution_page = source.get("solution_page")
    if not isinstance(puzzle_page, int) or puzzle_page < 1 or not isinstance(solution_page, int) or solution_page < 1:
        raise ValidationFailure(
            f"{case.identifier}.source needs integer puzzle_page and solution_page provenance."
        )
    raw_answer = source.get("verified_answer", source.get("raw_solution"))
    if not isinstance(raw_answer, str) or not raw_answer.strip():
        raise ValidationFailure(
            f"{case.identifier}.source needs verified_answer (or raw_solution) from the raw module."
        )
    answer = as_mapping(case.raw.get("answer"), f"{case.identifier}.answer")
    person_id = answer.get("person_id")
    coordinate = answer.get("coordinate")
    if person_id not in case.people:
        raise ValidationFailure(f"{case.identifier}.answer.person_id does not identify a canonical person.")
    normalized_coordinate = normalized_cell(
        coordinate, case.rows, case.columns, f"{case.identifier}.answer.coordinate"
    )
    if case.people[person_id]["placement"] != normalized_coordinate:
        raise ValidationFailure(
            f"{case.identifier} answer coordinate {normalized_coordinate} does not match "
            f"{person_id}'s canonical placement {case.people[person_id]['placement']}."
        )
    source_identity = answer.get("source_identity")
    if not isinstance(source_identity, str) or not source_identity.strip():
        source_identity = case.people[person_id].get("source_identity", case.people[person_id]["display_name"])
    if not isinstance(source_identity, str) or source_identity.casefold().strip() != raw_answer.casefold().strip():
        raise ValidationFailure(
            f"{case.identifier} answer identity drift: raw module says {raw_answer!r}, "
            f"canonical answer maps to {source_identity!r}."
        )
    raw_coordinate = source.get("verified_coordinate", source.get("raw_coordinate"))
    if raw_coordinate is not None:
        raw_coordinate = normalized_cell(raw_coordinate, case.rows, case.columns,
                                        f"{case.identifier}.source.verified_coordinate")
        if raw_coordinate != normalized_coordinate:
            raise ValidationFailure(
                f"{case.identifier} answer coordinate drift: raw module is {raw_coordinate}, "
                f"canonical answer is {normalized_coordinate}."
            )
    return [
        f"solution identity preserved: {raw_answer.upper()} at {normalized_coordinate} "
        f"(raw PDF pp. {puzzle_page}/{solution_page}, sha256 {source_checksum[:12]}... )",
        source_hash_status(source, source_checksum),
    ]


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    return value


def fingerprint(value: Any) -> str:
    serialized = json.dumps(canonicalize(value), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def fingerprints(case: CaseModel) -> dict[str, str]:
    topology = {
        "grid": {"rows": case.rows, "columns": case.columns},
        "rooms": [
            {"id": room_id, "name": case.rooms[room_id]["name"], "cells": case.rooms[room_id]["cells"]}
            for room_id in sorted(case.rooms)
        ],
        "objects": [
            {
                "id": object_id,
                "type": case.objects[object_id].get("type"),
                "cell": case.objects[object_id]["cell"],
                "cells": case.objects[object_id]["cells"],
                "blocked": case.objects[object_id].get("blocked") is True
                           or case.objects[object_id].get("occupancy") == "blocked",
            }
            for object_id in sorted(case.objects)
        ],
        "blocked_cells": sorted(case.blocked_cells, key=cell_sort_key),
        "constraints": case.constraints,
        "solver_rules": case.raw.get("solver"),
    }
    solution = {
        "people": [
            {
                "id": person_id,
                "source_identity": case.people[person_id].get(
                    "source_identity", case.people[person_id]["display_name"]
                ),
                "placement": case.people[person_id]["placement"],
            }
            for person_id in sorted(case.people)
        ],
        "answer": case.raw["answer"],
        "meta": case.raw.get("meta"),
    }
    return {"topology_sha256": fingerprint(topology), "solution_sha256": fingerprint(solution)}


def check_fingerprints(case: CaseModel) -> list[str]:
    expected = as_mapping(case.raw.get("integrity"), f"{case.identifier}.integrity")
    actual = fingerprints(case)
    for key, value in actual.items():
        recorded = expected.get(key)
        if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
            raise ValidationFailure(f"{case.identifier}.integrity.{key} must contain a pinned SHA-256 baseline.")
        if recorded != value:
            raise ValidationFailure(
                f"{case.identifier} {key} changed: expected {recorded}, got {value}."
            )
    return [f"{key}: {value}" for key, value in actual.items()]


def coordinates_for_reference(reference: Any, assignment: dict[str, str], case: CaseModel) -> list[str] | None:
    if not isinstance(reference, str):
        raise ValidationFailure(f"{case.identifier} constraint reference must be a string.")
    if reference in case.people:
        coordinate = assignment.get(reference)
        return [coordinate] if coordinate is not None else None
    if reference in case.objects:
        return list(case.objects[reference]["cells"])
    if reference.startswith("type:"):
        furniture_type = reference[len("type:"):]
        object_ids = case.object_types.get(furniture_type)
        if not object_ids:
            raise ValidationFailure(
                f"{case.identifier} constraint references unknown furniture type {furniture_type!r}."
            )
        cells: list[str] = []
        for object_id in object_ids:
            cells.extend(case.objects[object_id]["cells"])
        return cells
    raise ValidationFailure(f"{case.identifier} constraint references unknown person/object {reference!r}.")


def coord_for_reference(reference: Any, assignment: dict[str, str], case: CaseModel) -> str | None:
    coordinates = coordinates_for_reference(reference, assignment, case)
    if coordinates is None:
        return None
    if len(coordinates) != 1:
        raise ValidationFailure(
            f"{case.identifier} constraint needs one coordinate for {reference!r}; "
            "use a binary relation for a multi-cell object footprint."
        )
    return coordinates[0]


def reference_pair(constraint: dict[str, Any], case: CaseModel) -> tuple[Any, Any]:
    left = constraint.get("left", constraint.get("person", constraint.get("subject")))
    right = constraint.get("right", constraint.get("target", constraint.get("other")))
    if left is None or right is None:
        raise ValidationFailure(
            f"{case.identifier} {constraint_type(constraint)} constraint needs left/right "
            "(or person/target) references."
        )
    return left, right


def room_for_reference(reference: Any, assignment: dict[str, str], case: CaseModel) -> str | None:
    coordinates = coordinates_for_reference(reference, assignment, case)
    if coordinates is None:
        return None
    rooms = {case.room_for_cell[coordinate] for coordinate in coordinates}
    if len(rooms) != 1:
        raise ValidationFailure(
            f"{case.identifier} constraint reference {reference!r} spans multiple rooms."
        )
    return next(iter(rooms))


def integer_value(constraint: dict[str, Any], keys: Iterable[str], label: str) -> int:
    for key in keys:
        value = constraint.get(key)
        if isinstance(value, int):
            return value
    raise ValidationFailure(f"{label} needs an integer {'/'.join(keys)}.")


def string_value(constraint: dict[str, Any], keys: Iterable[str], label: str) -> str:
    for key in keys:
        value = constraint.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValidationFailure(f"{label} needs {'/'.join(keys)}.")


def evaluate_constraint(constraint: dict[str, Any], assignment: dict[str, str], case: CaseModel) -> bool | None:
    """Return None while a relationship cannot yet be evaluated in a partial solve."""
    kind = constraint_type(constraint)
    label = f"{case.identifier} {kind} constraint"

    if kind in {"exact", "exact_cell", "not_cell", "row", "not_row", "column", "not_column",
                "room", "not_room", "corner", "not_corner", "outer_wall", "not_outer_wall"}:
        person = constraint.get("person", constraint.get("subject"))
        coordinate = coord_for_reference(person, assignment, case)
        if coordinate is None:
            return None
        cell = parse_cell(coordinate, case.rows, case.columns, label)
        if kind in {"exact", "exact_cell", "not_cell"}:
            expected = normalized_cell(constraint.get("cell"), case.rows, case.columns, label)
            result = coordinate == expected
            return not result if kind == "not_cell" else result
        if kind in {"row", "not_row"}:
            expected = integer_value(constraint, ("value", "row"), label)
            result = cell.row == expected
            return not result if kind == "not_row" else result
        if kind in {"column", "not_column"}:
            expected = string_value(constraint, ("value", "column"), label).upper()
            result = cell.column == column_number(expected)
            return not result if kind == "not_column" else result
        if kind in {"room", "not_room"}:
            room_ids = constraint.get("room_ids")
            if room_ids is not None:
                room_ids = as_list(room_ids, f"{label}.room_ids")
                for room_id in room_ids:
                    if room_id not in case.rooms:
                        raise ValidationFailure(f"{label} references unknown room {room_id!r}.")
                result = case.room_for_cell[coordinate] in set(room_ids)
            else:
                expected = string_value(constraint, ("room_id", "value", "room"), label)
                if expected not in case.rooms:
                    raise ValidationFailure(f"{label} references unknown room {expected!r}.")
                result = case.room_for_cell[coordinate] == expected
            return not result if kind == "not_room" else result
        if kind in {"corner", "not_corner"}:
            result = cell.column in {1, case.columns} and cell.row in {1, case.rows}
            return not result if kind == "not_corner" else result
        result = cell.column in {1, case.columns} or cell.row in {1, case.rows}
        return not result if kind == "not_outer_wall" else result

    if kind in {"on", "not_on"}:
        person = constraint.get("person", constraint.get("subject"))
        coordinate = coord_for_reference(person, assignment, case)
        if coordinate is None:
            return None
        target = constraint.get("reference", constraint.get("object", constraint.get("target")))
        target_coordinates = coordinates_for_reference(target, assignment, case)
        if target_coordinates is None:
            return None
        result = coordinate in target_coordinates
        return not result if kind == "not_on" else result

    if kind == "one_of":
        person = constraint.get("person", constraint.get("subject"))
        coordinate = coord_for_reference(person, assignment, case)
        if coordinate is None:
            return None
        cells = [
            normalized_cell(cell, case.rows, case.columns, f"{label}.cells")
            for cell in as_list(constraint.get("cells"), f"{label}.cells")
        ]
        return coordinate in cells

    if kind in {"adjacent", "not_adjacent", "diagonal", "not_diagonal", "distance", "same_room",
                "different_room", "same_row", "different_row", "same_column", "different_column", "relative"}:
        left, right = reference_pair(constraint, case)
        left_coordinates = coordinates_for_reference(left, assignment, case)
        right_coordinates = coordinates_for_reference(right, assignment, case)
        if left_coordinates is None or right_coordinates is None:
            return None
        pairs = [
            (
                parse_cell(left_coordinate, case.rows, case.columns, label),
                parse_cell(right_coordinate, case.rows, case.columns, label),
                left_coordinate,
                right_coordinate,
            )
            for left_coordinate in left_coordinates for right_coordinate in right_coordinates
        ]
        if kind in {"adjacent", "not_adjacent"}:
            result = any(abs(left_cell.column - right_cell.column) + abs(left_cell.row - right_cell.row) == 1
                         for left_cell, right_cell, _, _ in pairs)
            return not result if kind == "not_adjacent" else result
        if kind in {"diagonal", "not_diagonal"}:
            result = any(abs(left_cell.column - right_cell.column) == 1
                         and abs(left_cell.row - right_cell.row) == 1
                         for left_cell, right_cell, _, _ in pairs)
            return not result if kind == "not_diagonal" else result
        if kind == "distance":
            metric = constraint.get("metric", "manhattan")
            expected = integer_value(constraint, ("value", "distance"), label)
            if metric == "manhattan":
                return any(abs(left_cell.column - right_cell.column) + abs(left_cell.row - right_cell.row) == expected
                           for left_cell, right_cell, _, _ in pairs)
            if metric in {"chebyshev", "king"}:
                return any(max(abs(left_cell.column - right_cell.column), abs(left_cell.row - right_cell.row)) == expected
                           for left_cell, right_cell, _, _ in pairs)
            raise ValidationFailure(f"{label} has unsupported metric {metric!r}.")
        if kind in {"same_room", "different_room"}:
            result = any(case.room_for_cell[left_coordinate] == case.room_for_cell[right_coordinate]
                         for _, _, left_coordinate, right_coordinate in pairs)
            return not result if kind == "different_room" else result
        if kind in {"same_row", "different_row"}:
            result = any(left_cell.row == right_cell.row for left_cell, right_cell, _, _ in pairs)
            return not result if kind == "different_row" else result
        if kind in {"same_column", "different_column"}:
            result = any(left_cell.column == right_cell.column for left_cell, right_cell, _, _ in pairs)
            return not result if kind == "different_column" else result
        direction = string_value(constraint, ("direction", "value"), label).lower().replace(" ", "_")
        def relation(left_cell: Cell, right_cell: Cell) -> bool:
            relations = {
                "left_of": left_cell.column < right_cell.column,
                "west_of": left_cell.column < right_cell.column,
                "right_of": left_cell.column > right_cell.column,
                "east_of": left_cell.column > right_cell.column,
                "above": left_cell.row < right_cell.row,
                "north_of": left_cell.row < right_cell.row,
                "below": left_cell.row > right_cell.row,
                "south_of": left_cell.row > right_cell.row,
                "northwest_of": left_cell.column < right_cell.column and left_cell.row < right_cell.row,
                "northeast_of": left_cell.column > right_cell.column and left_cell.row < right_cell.row,
                "southwest_of": left_cell.column < right_cell.column and left_cell.row > right_cell.row,
                "southeast_of": left_cell.column > right_cell.column and left_cell.row > right_cell.row,
            }
            if direction not in relations:
                raise ValidationFailure(f"{label} has unsupported direction {direction!r}.")
            return relations[direction]
        if not any(relation(left_cell, right_cell) for left_cell, right_cell, _, _ in pairs):
            return False
        row_distance = constraint.get("row_distance")
        if row_distance is not None:
            if not isinstance(row_distance, int) or row_distance < 0:
                raise ValidationFailure(f"{label} row_distance must be a non-negative integer.")
        column_distance = constraint.get("column_distance")
        if column_distance is not None:
            if not isinstance(column_distance, int) or column_distance < 0:
                raise ValidationFailure(f"{label} column_distance must be a non-negative integer.")
        return any(
            relation(left_cell, right_cell)
            and (row_distance is None or abs(left_cell.row - right_cell.row) == row_distance)
            and (column_distance is None or abs(left_cell.column - right_cell.column) == column_distance)
            for left_cell, right_cell, _, _ in pairs
        )

    if kind in {"room_occupancy", "exclusive_companion"}:
        anchor = constraint.get("anchor", constraint.get("owner", constraint.get("person")))
        room_id = room_for_reference(anchor, assignment, case)
        if room_id is None:
            return None
        assigned_in_room = sum(
            1 for coordinate in assignment.values() if case.room_for_cell[coordinate] == room_id
        )
        expected = integer_value(constraint, ("count",), label) if kind == "room_occupancy" else 2
        if assigned_in_room > expected:
            return False
        if len(assignment) != len(case.people):
            return None
        if assigned_in_room != expected:
            return False
        if kind == "exclusive_companion":
            companion = constraint.get("companion")
            companion_room = room_for_reference(companion, assignment, case)
            return companion_room == room_id
        return True

    raise ValidationFailure(f"{label} is not implemented.")


def check_solution_constraints(case: CaseModel) -> str:
    failures: list[str] = []
    for index, constraint in enumerate(case.constraints, 1):
        result = evaluate_constraint(constraint, case.solution, case)
        if result is not True:
            failures.append(f"constraint {index:02d} ({constraint_type(constraint)})")
    if failures:
        raise ValidationFailure(
            f"{case.identifier} canonical placement violates {', '.join(failures)}."
        )
    rules = distinct_position_rules(case)
    placements = [parse_cell(coordinate, case.rows, case.columns, case.identifier)
                  for coordinate in case.solution.values()]
    if rules["rows"] and len({cell.row for cell in placements}) != len(placements):
        raise ValidationFailure(f"{case.identifier} violates its source rule of one person per row.")
    if rules["columns"] and len({cell.column for cell in placements}) != len(placements):
        raise ValidationFailure(f"{case.identifier} violates its source rule of one person per column.")
    global_rules = []
    if rules["rows"]:
        global_rules.append("one person per row")
    if rules["columns"]:
        global_rules.append("one person per column")
    suffix = f"; {', '.join(global_rules)}" if global_rules else ""
    if case.constraints:
        return f"canonical placement satisfies {len(case.constraints)} normalized raw constraints{suffix}"
    if global_rules:
        return f"canonical placement satisfies source position rule(s): {', '.join(global_rules)}"
    return "no normalized raw constraints captured; solvability is intentionally not claimed"


def distinct_position_rules(case: CaseModel) -> dict[str, bool]:
    """Read only explicitly captured source rules; never infer them from grid size."""
    solver = case.raw.get("solver", {})
    if solver is None:
        solver = {}
    solver = as_mapping(solver, f"{case.identifier}.solver")
    return {
        "rows": any(solver.get(key) is True for key in (
            "one_person_per_row", "all_people_distinct_rows", "unique_rows"
        )),
        "columns": any(solver.get(key) is True for key in (
            "one_person_per_column", "all_people_distinct_columns", "unique_columns"
        )),
    }


def compatible_with_partial(case: CaseModel, assignment: dict[str, str]) -> bool:
    rules = distinct_position_rules(case)
    placements = [parse_cell(coordinate, case.rows, case.columns, case.identifier)
                  for coordinate in assignment.values()]
    if rules["rows"] and len({cell.row for cell in placements}) != len(placements):
        return False
    if rules["columns"] and len({cell.column for cell in placements}) != len(placements):
        return False
    return all(evaluate_constraint(constraint, assignment, case) is not False for constraint in case.constraints)


def solve(case: CaseModel, max_nodes: int) -> SolveResult:
    if max_nodes < 1:
        raise ValidationFailure(f"{case.identifier} solver max_nodes must be positive.")
    domains = {person_id: list(case.available_cells) for person_id in case.people}
    assignment: dict[str, str] = {}
    all_solutions: list[dict[str, str]] = []
    nodes = 0
    stopped = False

    def available(person_id: str) -> list[str]:
        used = set(assignment.values())
        choices: list[str] = []
        for coordinate in domains[person_id]:
            if coordinate in used:
                continue
            assignment[person_id] = coordinate
            if compatible_with_partial(case, assignment):
                choices.append(coordinate)
            del assignment[person_id]
        return choices

    def visit() -> None:
        nonlocal nodes, stopped
        if stopped:
            return
        if nodes >= max_nodes:
            stopped = True
            return
        if len(assignment) == len(case.people):
            nodes += 1
            if compatible_with_partial(case, assignment):
                all_solutions.append(dict(sorted(assignment.items())))
                if len(all_solutions) > 1:
                    # A second solution is enough to prove non-uniqueness.
                    stopped = True
            return
        options = [(len(candidates := available(person_id)), person_id, candidates)
                   for person_id in case.people if person_id not in assignment]
        _, person_id, candidates = min(options, key=lambda item: (item[0], item[1]))
        for coordinate in candidates:
            if stopped:
                return
            nodes += 1
            if nodes > max_nodes:
                stopped = True
                return
            assignment[person_id] = coordinate
            visit()
            del assignment[person_id]

    visit()
    return SolveResult(
        count=len(all_solutions), solutions=all_solutions, nodes=nodes, exhausted=not stopped
    )


def check_uniqueness(case: CaseModel) -> str:
    solver = case.raw.get("solver", {})
    if solver is None:
        return "solver deliberately disabled; source constraints are incomplete or unavailable"
    solver = as_mapping(solver, f"{case.identifier}.solver")
    expected = solver.get("expected_solution_count")
    if expected is None:
        return "solver intentionally not asserted; source constraints are incomplete or unavailable"
    if not isinstance(expected, int) or expected < 0:
        raise ValidationFailure(f"{case.identifier}.solver.expected_solution_count must be a non-negative integer or null.")
    max_nodes = solver.get("max_nodes", 1_000_000)
    if not isinstance(max_nodes, int):
        raise ValidationFailure(f"{case.identifier}.solver.max_nodes must be an integer.")
    result = solve(case, max_nodes)
    if result.count != expected:
        raise ValidationFailure(
            f"{case.identifier} solver found {result.count} solution(s); expected {expected} "
            f"after {result.nodes} search nodes."
        )
    if not result.exhausted and result.count <= expected:
        raise ValidationFailure(
            f"{case.identifier} solver hit its {max_nodes}-node limit before proving {expected} solution(s)."
        )
    if expected == 1:
        if not result.solutions or result.solutions[0] != dict(sorted(case.solution.items())):
            raise ValidationFailure(
                f"{case.identifier} solver's unique placement does not match the canonical solution placement."
            )
    return f"solver proved {expected} solution(s) in {result.nodes} search nodes"


def check_meta(case: CaseModel) -> str:
    meta = case.raw.get("meta")
    if meta is None:
        return "no meta-letter requirement for this pilot case"
    meta = as_mapping(meta, f"{case.identifier}.meta")
    room_id = meta.get("empty_room_id")
    letter = meta.get("letter")
    if room_id is None and letter is None:
        return "no meta-letter requirement for this pilot case"
    if room_id not in case.rooms:
        raise ValidationFailure(f"{case.identifier}.meta.empty_room_id must reference a canonical room.")
    if not isinstance(letter, str) or len(letter.strip()) != 1 or not letter.strip().isalpha():
        raise ValidationFailure(f"{case.identifier}.meta.letter must be exactly one alphabetic character.")
    occupancy = {identifier: 0 for identifier in case.rooms}
    for coordinate in case.solution.values():
        occupancy[case.room_for_cell[coordinate]] += 1
    empty = [identifier for identifier, count in occupancy.items() if count == 0]
    if empty != [room_id]:
        raise ValidationFailure(
            f"{case.identifier} meta topology drift: expected only {room_id} empty, got {empty or 'no empty rooms'}."
        )
    room_name = case.rooms[room_id]["name"]
    if room_name[0].casefold() != letter.strip().casefold():
        raise ValidationFailure(
            f"{case.identifier} meta letter drift: empty room {room_name!r} does not yield {letter!r}."
        )
    return f"unique empty room {room_id} ({room_name}) yields meta letter {letter.upper()}"


def validate_case(raw_case: Any) -> tuple[str, list[str]]:
    case = build_model(raw_case)
    messages = [
        f"topology partitions {case.columns}x{case.rows} grid across {len(case.rooms)} rooms",
        *check_source_identity(case),
        check_solution_constraints(case),
        check_meta(case),
        check_uniqueness(case),
        *check_asset_paths(case),
        *check_fingerprints(case),
    ]
    return case.identifier, messages


def emit_fingerprints(raw_cases: list[Any], requested: set[str]) -> str:
    entries: dict[str, dict[str, str]] = {}
    for raw_case in raw_cases:
        case = build_model(raw_case)
        if requested and case.identifier not in requested:
            continue
        entries[case.identifier] = fingerprints(case)
    return yaml.safe_dump(entries, sort_keys=True).rstrip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="content/spatial_map_pilots.yml",
                        help="Canonical pilot map manifest, relative to the Book Factory by default.")
    parser.add_argument("--case", action="append", default=[],
                        help="Pilot case id to validate; repeat for a small selected subset.")
    parser.add_argument("--report", help="Optional deterministic text report path.")
    parser.add_argument("--emit-fingerprints", action="store_true",
                        help="Print integrity baselines for the selected cases and exit.")
    args = parser.parse_args()

    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = (TOOL_ROOT / manifest).resolve()
    requested = set(args.case)
    lines: list[str] = ["HMDA SPATIAL MAP PILOT VALIDATION"]
    exit_code = 0
    try:
        document = as_mapping(yaml.safe_load(manifest.read_text(encoding="utf-8")), "pilot manifest")
        raw_cases = document.get("pilots", document.get("cases"))
        raw_cases = as_list(raw_cases, "pilot manifest pilots")
        if not raw_cases:
            raise ValidationFailure("Pilot manifest has no cases.")
        available = {as_mapping(item, "pilot case").get("id") for item in raw_cases}
        missing = sorted(requested - available)
        if missing:
            raise ValidationFailure(f"Requested pilot case(s) absent from manifest: {', '.join(missing)}.")
        selected = [item for item in raw_cases if not requested or as_mapping(item, "pilot case").get("id") in requested]
        if args.emit_fingerprints:
            print(emit_fingerprints(selected, requested))
            return
        for raw_case in selected:
            identifier = as_mapping(raw_case, "pilot case").get("id", "UNKNOWN")
            try:
                case_id, messages = validate_case(raw_case)
                lines.append(f"\nPASS {case_id}")
                lines.extend(f"  - {message}" for message in messages)
            except ValidationFailure as exc:
                exit_code = 1
                lines.append(f"\nFAIL {identifier}\n  - {exc}")
    except (OSError, yaml.YAMLError, ValidationFailure) as exc:
        exit_code = 1
        lines.append(f"\nFAIL\n  - {exc}")
    lines.append(f"\nOVERALL: {'PASS' if exit_code == 0 else 'FAIL'}")
    text = "\n".join(lines) + "\n"
    print(text, end="")
    if args.report:
        report = Path(args.report)
        if not report.is_absolute():
            report = (TOOL_ROOT / report).resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(text, encoding="utf-8")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
