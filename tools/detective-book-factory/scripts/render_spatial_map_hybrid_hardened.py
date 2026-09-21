#!/usr/bin/env python3
"""Topology-aware hardened entry point for the HMDA hybrid Map Factory.

This wrapper preserves the existing production renderer and replaces only the
room-label assignment boundary. The locked runtime topology is authoritative;
image detection may identify a label footprint, but it may not redefine room
geometry.

The original center-point assignment can misclassify a pill that straddles an
irregular room boundary. This version scores the full detected pill footprint
against the verified room-cell topology, accepts only a dominant overlap, and
fails closed when the image evidence is ambiguous.

No case-specific pixel coordinates or source labels are stored here.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

import render_spatial_map_hybrid as base


MIN_ROOM_OVERLAP = 0.52
MIN_ROOM_MARGIN = 0.08
LABEL_METADATA = base.load_yaml(base.TOOL_ROOT / "content" / "spatial_source_label_metadata.yml")


def _parse_cell(cell: str) -> tuple[int, int]:
    letters = ""
    digits = ""
    for ch in cell.strip().upper():
        if ch.isalpha() and not digits:
            letters += ch
        elif ch.isdigit():
            digits += ch
        else:
            raise ValueError(f"Invalid runtime cell: {cell!r}")
    if not letters or not digits:
        raise ValueError(f"Invalid runtime cell: {cell!r}")
    col = 0
    for ch in letters:
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(digits) - 1


def _box_room_scores(
    case: dict[str, Any],
    box: tuple[int, int, int, int],
    grid_w: int,
    grid_h: int,
) -> tuple[int, float, float, dict[int, float]]:
    """Return dominant room, coverage, dominance margin, and raw overlap areas."""
    x, y, bw, bh = box
    rows = int(case["grid"]["rows"])
    cols = int(case["grid"]["columns"])
    if rows <= 0 or cols <= 0 or grid_w <= 0 or grid_h <= 0 or bw <= 0 or bh <= 0:
        raise ValueError("Invalid grid or label-box geometry")

    cell_w = grid_w / cols
    cell_h = grid_h / rows
    scores: dict[int, float] = {}
    for room in case["rooms"]:
        rid = int(room["source_room_id"])
        overlap = 0.0
        for cell in room.get("cells", []):
            col, row = _parse_cell(str(cell))
            if not (0 <= col < cols and 0 <= row < rows):
                raise ValueError(f"{case['id']}: runtime cell outside grid: {cell}")
            cx0, cy0 = col * cell_w, row * cell_h
            cx1, cy1 = (col + 1) * cell_w, (row + 1) * cell_h
            ix = max(0.0, min(x + bw, cx1) - max(x, cx0))
            iy = max(0.0, min(y + bh, cy1) - max(y, cy0))
            overlap += ix * iy
        scores[rid] = overlap

    if not scores:
        raise ValueError(f"{case['id']}: runtime contains no rooms")

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_rid, best_area = ranked[0]
    second_area = ranked[1][1] if len(ranked) > 1 else 0.0
    area = float(bw * bh)
    return best_rid, best_area / area, (best_area - second_area) / area, scores


def assign_room_label_boxes(
    case: dict[str, Any],
    boxes: list[tuple[int, int, int, int]],
    grid_w: int,
    grid_h: int,
    *,
    min_overlap: float = MIN_ROOM_OVERLAP,
    min_margin: float = MIN_ROOM_MARGIN,
) -> tuple[dict[int, tuple[int, int, int, int]], list[dict[str, Any]]]:
    """Assign detected pills to verified rooms using dominant footprint overlap.

    Ambiguous candidates are rejected. If more than one accepted candidate lands
    in a room, the strongest topology score wins with the original largest-box
    preference as the final deterministic tie-breaker.
    """
    accepted_by_room: dict[int, list[tuple[float, float, int, tuple[int, int, int, int]]]] = {}
    diagnostics: list[dict[str, Any]] = []

    for box in boxes:
        rid, overlap, margin, raw_scores = _box_room_scores(case, box, grid_w, grid_h)
        accepted = overlap >= min_overlap and margin >= min_margin
        diagnostics.append(
            {
                "box": box,
                "best_room": rid,
                "overlap": round(overlap, 4),
                "margin": round(margin, 4),
                "accepted": accepted,
                "scores": {key: round(value, 2) for key, value in raw_scores.items()},
            }
        )
        if not accepted:
            continue
        x, y, bw, bh = box
        accepted_by_room.setdefault(rid, []).append((overlap, margin, bw * bh, box))

    assigned: dict[int, tuple[int, int, int, int]] = {}
    for rid, candidates in accepted_by_room.items():
        candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        assigned[rid] = candidates[0][3]

    return assigned, diagnostics


def absent_verified_rooms(case: dict[str, Any]) -> set[int]:
    expected = str(base.load_yaml(base.TOOL_ROOT / "content" / "spatial_source_manifest_final.yml")["source"]["source_pdf_sha256"])
    if LABEL_METADATA.get("source_pdf_sha256") != expected:
        raise ValueError("Source-label metadata hash does not match the locked source PDF.")
    rooms = LABEL_METADATA.get("cases", {}).get(case["id"], {}).get("rooms", {})
    return {int(rid) for rid, data in rooms.items() if data.get("state") == "absent_verified"}


def explicit_reference_rooms(case: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Read hash-bound normalized source references, never pixel constants."""
    expected = str(base.load_yaml(base.TOOL_ROOT / "content" / "spatial_source_manifest_final.yml")["source"]["source_pdf_sha256"])
    if LABEL_METADATA.get("source_pdf_sha256") != expected:
        raise ValueError("Source-label metadata hash does not match the locked source PDF.")
    rooms = LABEL_METADATA.get("cases", {}).get(case["id"], {}).get("rooms", {})
    return {
        int(rid): data for rid, data in rooms.items()
        if data.get("state") == "explicit_reference"
    }


def _grid_image(source: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    left, top, right, bottom = bbox
    return source.crop((left, top, right + 1, bottom + 1)).convert("RGB")


def _label_assignments(case: dict[str, Any], grid: Image.Image, *, broad: bool) -> dict[int, tuple[int, int, int, int]]:
    boxes = base.detect_room_label_boxes(base.np.asarray(grid.convert("L")), broad=broad)
    assigned, _ = assign_room_label_boxes(case, boxes, grid.width, grid.height)
    return assigned


def _owned_boxes(case: dict[str, Any], grid: Image.Image) -> dict[int, list[tuple[int, int, int, int]]]:
    """Return all broad, topology-dominant source candidates by room."""
    owned: dict[int, list[tuple[int, int, int, int]]] = {}
    for box in base.detect_room_label_boxes(base.np.asarray(grid.convert("L")), broad=True):
        rid, overlap, margin, _ = _box_room_scores(case, box, grid.width, grid.height)
        if overlap >= MIN_ROOM_OVERLAP and margin >= MIN_ROOM_MARGIN:
            owned.setdefault(rid, []).append(box)
    return owned


def _paired_source_box(
    solution_box: tuple[int, int, int, int],
    puzzle_boxes: list[tuple[int, int, int, int]],
) -> tuple[int, int, int, int] | None:
    """Pair repeat footprints despite page-title vertical translation.

    Label width, height, and x position are invariant in the locked source;
    vertical position is deliberately not used, because the paired page headers
    have different heights.  This is source evidence, not a render placement.
    """
    sx, _, sw, sh = solution_box
    candidates = [
        box for box in puzzle_boxes
        if abs(box[0] - sx) <= 14 and abs(box[2] - sw) <= max(12, int(sw * 0.12)) and abs(box[3] - sh) <= 12
    ]
    if len(candidates) != 1:
        return None
    return candidates[0]


def _normalized(box: tuple[int, int, int, int], grid: Image.Image) -> list[float]:
    x, y, width, height = box
    return [round(x / grid.width, 6), round(y / grid.height, 6), round(width / grid.width, 6), round(height / grid.height, 6)]


def classify_two_page_evidence(
    case: dict[str, Any],
    puzzle: Image.Image,
    puzzle_bbox: tuple[int, int, int, int],
    solution: Image.Image,
    solution_bbox: tuple[int, int, int, int],
) -> dict[int, dict[str, Any]]:
    """Classify only evidence-complete missing labels from two locked pages.

    The classifier never reads label text and never invents pixels.  It asks
    whether a topology-owned label footprint exists in either page.  A broader
    deterministic text-like scan is used only as negative/secondary evidence.
    """
    puzzle_grid = _grid_image(puzzle, puzzle_bbox)
    solution_grid = _grid_image(solution, solution_bbox)
    puzzle_primary = _label_assignments(case, puzzle_grid, broad=False)
    puzzle_broad = _label_assignments(case, puzzle_grid, broad=True)
    solution_primary = _label_assignments(case, solution_grid, broad=False)
    solution_broad = _label_assignments(case, solution_grid, broad=True)
    puzzle_boxes = base.detect_room_label_boxes(base.np.asarray(puzzle_grid.convert("L")), broad=True)
    solution_owned = _owned_boxes(case, solution_grid)
    result: dict[int, dict[str, Any]] = {}

    for room in case["rooms"]:
        rid = int(room["source_room_id"])
        if rid in puzzle_primary:
            continue
        # A broader scan finds a real, topology-owned footprint that the
        # primary detector rejected.  Persist the normalized reference only
        # after it repeats on the paired source page.
        if rid in puzzle_broad and rid in solution_broad:
            pp = _normalized(puzzle_broad[rid], puzzle_grid)
            sp = _normalized(solution_broad[rid], solution_grid)
            max_delta = max(abs(a - b) for a, b in zip(pp, sp))
            if max_delta <= 0.035:
                result[rid] = {
                    "state": "explicit_reference",
                    "evidence_mode": "auto_two_page_reference",
                    "normalized_footprint": pp,
                    "confidence": {"normalized_max_delta": round(max_delta, 6), "puzzle_broad": True, "solution_broad": True},
                }
                continue

        # The paired solution page can supply a verified source reference
        # when its room-owned pill repeats as the same physical source pill on
        # the puzzle page, even if the puzzle page's geometry intentionally
        # maps that pill to another runtime room.  The final puzzle label is
        # still topology-anchored below; this reference is never used to erase
        # or relabel that other room's source art.
        solution_candidates = solution_owned.get(rid, [])
        if len(solution_candidates) == 1:
            paired = _paired_source_box(solution_candidates[0], puzzle_boxes)
            if paired is not None:
                result[rid] = {
                    "state": "explicit_reference",
                    "evidence_mode": "auto_two_page_reference",
                    "reference_page": "solution",
                    "normalized_footprint": _normalized(solution_candidates[0], solution_grid),
                    "confidence": {
                        "puzzle_primary": False,
                        "solution_topology_overlap": 1.0,
                        "paired_source_footprint": True,
                        "puzzle_reference_normalized": _normalized(paired, puzzle_grid),
                    },
                }
                continue

        # Absence is a stronger claim: neither primary nor broader text-like
        # evidence may locate a footprint owned by this room on either page,
        # and a topology-only anchor must exist before the claim is persisted.
        if rid not in puzzle_broad and rid not in solution_broad:
            anchor = topology_safe_anchor(case, rid, puzzle_grid.width, puzzle_grid.height)
            result[rid] = {
                "state": "absent_verified",
                "evidence_mode": "auto_two_page_absence",
                "confidence": {
                    "puzzle_primary": False,
                    "puzzle_broad_text_scan": False,
                    "solution_primary": False,
                    "solution_broad_text_scan": False,
                    "topology_safe_anchor": True,
                    "anchor_normalized": _normalized(anchor, puzzle_grid),
                },
            }
    return result


def persist_two_page_evidence(
    source: Path,
    runtime: Path,
    requested: list[str],
) -> None:
    """Persist deterministic auto-classifications before base rendering runs."""
    selection = base.load_yaml(base.TOOL_ROOT / "content" / "spatial_source_manifest_final.yml")
    expected_hash = str(selection["source"]["source_pdf_sha256"])
    if base.sha256(source) != expected_hash:
        raise SystemExit("BLOCKED: source PDF SHA mismatch before label classification.")
    if LABEL_METADATA.get("source_pdf_sha256") != expected_hash:
        raise SystemExit("BLOCKED: label metadata source hash does not match the locked source.")
    declarations = {item["id"]: item for item in selection["cases"]}
    runtime_cases = {item["id"]: item for item in base.load_runtime(runtime)["cases"]}
    doc = base.fitz.open(source)
    changed = False
    try:
        for cid in requested:
            if cid not in declarations or cid not in runtime_cases:
                continue
            decl, case = declarations[cid], runtime_cases[cid]
            puzzle = base.extract_embedded_page_image(doc, int(decl["pdf"]["puzzle_page"]))
            solution = base.extract_embedded_page_image(doc, int(decl["pdf"]["solution_page"]))
            discovered = classify_two_page_evidence(
                case, puzzle, base.detect_grid_bbox(base.np.asarray(puzzle.convert("L"))),
                solution, base.detect_grid_bbox(base.np.asarray(solution.convert("L"))),
            )
            case_meta = LABEL_METADATA.setdefault("cases", {}).setdefault(cid, {})
            case_meta.setdefault("puzzle_page", int(decl["pdf"]["puzzle_page"]))
            case_meta.setdefault("solution_page", int(decl["pdf"]["solution_page"]))
            rooms = case_meta.setdefault("rooms", {})
            for rid, evidence in discovered.items():
                key = int(rid)
                if key not in rooms:
                    rooms[key] = evidence
                    changed = True
    finally:
        doc.close()
    if changed:
        metadata_path = base.TOOL_ROOT / "content" / "spatial_source_label_metadata.yml"
        metadata_path.write_text(base.yaml.safe_dump(LABEL_METADATA, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print("PASS: persisted deterministic two-page source-label evidence")


def topology_safe_anchor(case: dict[str, Any], rid: int, grid_w: int, grid_h: int) -> tuple[int, int, int, int]:
    """Place an absent-verified label in a clear, topology-owned source cell."""
    rows, cols = int(case["grid"]["rows"]), int(case["grid"]["columns"])
    room = next(room for room in case["rooms"] if int(room["source_room_id"]) == rid)
    occupied = {obj["cell"] for obj in case.get("objects", [])}
    occupied |= {person["placement"] for person in case.get("characters", [])}
    candidates = []
    for cell in room["cells"]:
        if cell in occupied:
            continue
        col, row = _parse_cell(cell)
        cell_w, cell_h = grid_w / cols, grid_h / rows
        # Prefer cells surrounded by matching-room neighbours: a conservative
        # clear interior score derived exclusively from topology.
        neighbours = [(col-1,row),(col+1,row),(col,row-1),(col,row+1)]
        interior = sum(
            1 for nc,nr in neighbours
            if 0 <= nc < cols and 0 <= nr < rows and f"{chr(65+nc)}{nr+1}" in room["cells"]
        )
        candidates.append((interior, -row, -col, col, row, cell_w, cell_h))
    if not candidates:
        raise ValueError(f"{case['id']}: absent_verified room {rid} has no clear topology cell.")
    _, _, _, col, row, cell_w, cell_h = max(candidates)
    width, height = int(cell_w * 0.82), int(cell_h * 0.30)
    x = int(col * cell_w + (cell_w - width) / 2)
    y = int(row * cell_h + (cell_h - height) / 2)
    return x, y, width, height


def replace_room_labels_hardened(
    source: Image.Image,
    case: dict[str, Any],
    bbox: tuple[int, int, int, int],
    fallback_layout: dict[int, tuple[float, float, float, float]] | None = None,
) -> tuple[Image.Image, dict[int, tuple[float, float, float, float]]]:
    """Replace source room labels without letting image geometry override topology."""
    left, top, right, bottom = bbox
    grid = source.crop((left, top, right + 1, bottom + 1)).convert("RGB")
    gray = base.np.asarray(grid.convert("L"))
    boxes = base.detect_room_label_boxes(gray)
    assigned, diagnostics = assign_room_label_boxes(case, boxes, grid.width, grid.height)

    expected = {int(room["source_room_id"]) for room in case["rooms"]}
    missing = sorted(expected - set(assigned))

    for rid in list(missing):
        if rid in absent_verified_rooms(case):
            assigned[rid] = topology_safe_anchor(case, rid, grid.width, grid.height)
    for rid, reference in explicit_reference_rooms(case).items():
        if rid not in missing:
            continue
        normalized = reference.get("normalized_footprint")
        if not isinstance(normalized, list) or len(normalized) != 4:
            raise ValueError(f"{case['id']}: explicit reference for room {rid} is not a normalized footprint.")
        nx, ny, nw, nh = (float(value) for value in normalized)
        candidate = (int(round(nx * grid.width)), int(round(ny * grid.height)), int(round(nw * grid.width)), int(round(nh * grid.height)))
        best, overlap, margin, _ = _box_room_scores(case, candidate, grid.width, grid.height)
        # A same-page reference can safely replace its own footprint.  A
        # cross-page reference may describe a source pill whose visual
        # geometry intentionally differs between pages; preserve that art and
        # use the deterministic topology-safe anchor instead.
        if best == rid and overlap >= 0.95 and margin >= 0.80:
            assigned[rid] = candidate
        else:
            assigned[rid] = topology_safe_anchor(case, rid, grid.width, grid.height)
    missing = sorted(expected - set(assigned))

    # Existing production rule retained: only the solution page may borrow the
    # already-validated normalized puzzle layout for rooms not safely detected.
    if missing and fallback_layout:
        for rid in list(missing):
            if rid not in fallback_layout:
                continue
            nx, ny, nw, nh = fallback_layout[rid]
            assigned[rid] = (
                int(round(nx * grid.width)),
                int(round(ny * grid.height)),
                int(round(nw * grid.width)),
                int(round(nh * grid.height)),
            )
        missing = sorted(expected - set(assigned))

    if missing:
        summary = "; ".join(
            f"box={d['box']} best={d['best_room']} overlap={d['overlap']:.2f} margin={d['margin']:.2f} accepted={d['accepted']}"
            for d in diagnostics
        )
        raise SystemExit(
            f"{case['id']}: topology-aware label assignment could not safely resolve room ids {missing}. "
            f"Candidates: {summary}. Failing closed rather than guessing."
        )

    draw = ImageDraw.Draw(grid)
    for room in case["rooms"]:
        rid = int(room["source_room_id"])
        x, y, bw, bh = assigned[rid]
        final = str(room["final_name"]).upper()
        if room.get("kind") == "zone":
            final += " // ZONE"

        pad_x = max(8, int(bh * 0.20))
        x0 = max(0, x - pad_x)
        x1 = min(grid.width, x + bw + pad_x)
        y0 = max(0, y - int(bh * 0.10))
        y1 = min(grid.height, y + bh + int(bh * 0.10))

        # Detected/reference labels replace only their source footprint. An
        # absent_verified label is anchored wholly inside an empty topology cell.
        draw.rounded_rectangle(
            (x0, y0, x1, y1),
            radius=max(6, int(bh * 0.22)),
            fill="white",
            outline=(20, 20, 20),
            width=max(2, int(bh * 0.06)),
        )
        max_size = max(20, int(bh * 0.86))
        min_size = max(15, int(bh * 0.52))
        chosen = base.font(min_size)
        for size in range(max_size, min_size - 1, -1):
            candidate_font = base.font(size)
            tb = draw.textbbox((0, 0), final, font=candidate_font)
            if tb[2] - tb[0] <= (x1 - x0) - 14 and tb[3] - tb[1] <= (y1 - y0) - 8:
                chosen = candidate_font
                break
        tb = draw.textbbox((0, 0), final, font=chosen)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2 - 2), final, font=chosen, fill=(20, 20, 20))

    normalized = {
        rid: (x / grid.width, y / grid.height, bw / grid.width, bh / grid.height)
        for rid, (x, y, bw, bh) in assigned.items()
    }
    return grid, normalized


def _self_test() -> None:
    # Irregular topology: the rectangle center lands in room 1 (B1), while a
    # majority of its full footprint belongs to the L-shaped room 0. The old
    # center-point rule would select room 1; topology overlap must select room 0.
    case = {
        "id": "SYNTHETIC",
        "grid": {"columns": 3, "rows": 2},
        "rooms": [
            {"source_room_id": 0, "cells": ["A1", "A2", "B2", "C2"]},
            {"source_room_id": 1, "cells": ["B1", "C1"]},
        ],
    }
    dominant_box = (70, 40, 120, 100)
    assigned, diagnostics = assign_room_label_boxes(case, [dominant_box], 300, 200)
    assert assigned == {0: dominant_box}, diagnostics

    # Exact boundary ambiguity must fail closed rather than picking a room by
    # sort order or pixel-center coincidence.
    simple = {
        "id": "AMBIGUOUS",
        "grid": {"columns": 2, "rows": 1},
        "rooms": [
            {"source_room_id": 0, "cells": ["A1"]},
            {"source_room_id": 1, "cells": ["B1"]},
        ],
    }
    ambiguous_box = (35, 10, 30, 20)
    assigned, diagnostics = assign_room_label_boxes(simple, [ambiguous_box], 100, 50)
    assert assigned == {}, diagnostics

    # Fully contained candidates remain deterministic and map one-to-one.
    boxes = [(5, 10, 30, 20), (60, 10, 30, 20)]
    assigned, diagnostics = assign_room_label_boxes(simple, boxes, 100, 50)
    assert assigned == {0: boxes[0], 1: boxes[1]}, diagnostics


# Monkey-patch only the label-replacement seam. All source hashing, page
# extraction, grid detection, framing, solution rendering and CLI behavior stay
# in the previously approved renderer.
base.replace_room_labels = replace_room_labels_hardened


if __name__ == "__main__":
    preflight = argparse.ArgumentParser(add_help=False)
    preflight.add_argument("--source-pdf", required=True, type=Path)
    preflight.add_argument("--runtime", required=True, type=Path)
    preflight.add_argument("--case", action="append", default=[])
    preflight_args, _ = preflight.parse_known_args()
    selection = base.load_yaml(base.TOOL_ROOT / "content" / "spatial_source_manifest_final.yml")
    requested = preflight_args.case or [case["id"] for case in selection["cases"]]
    persist_two_page_evidence(
        preflight_args.source_pdf.expanduser().resolve(),
        preflight_args.runtime.expanduser().resolve(),
        requested,
    )
    base.main()
