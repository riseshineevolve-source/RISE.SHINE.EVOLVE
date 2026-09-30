#!/usr/bin/env python3
"""Fail-closed pixel-footprint guard for future HMDA modern-prop composites.

The modern-prop layer is presentation-only. This validator compares a locked
pre-composite map raster with a candidate post-composite raster and proves that
every changed pixel is confined to catalog-approved object boxes from an
`hmda-modern-prop-plan`.

When the locked Shigai runtime is supplied, the validator also binds the plan
back to the exact runtime object semantics. For solution-map surfaces it treats
all witness/person placement cells as protected: no modern-prop pixel change is
allowed in a cell occupied by a person marker. This keeps presentation work from
silently covering or moving solution witnesses while still permitting the same
prop to be modernized on the puzzle surface.

Production substitution remains disabled until this guard and representative
visual QA both pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from PIL import Image, ImageChops, ImageDraw

import modern_prop_presentation as props


class FootprintError(RuntimeError):
    pass


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FootprintError("modern-prop plan must be a JSON object")
    if data.get("format") != "hmda-modern-prop-plan":
        raise FootprintError("plan format must be 'hmda-modern-prop-plan'")
    if data.get("mode") != "presentation_only":
        raise FootprintError("plan mode must be 'presentation_only'")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FootprintError("plan cases must be a non-empty list")
    return data


def load_runtime(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FootprintError("runtime must be a JSON object")
    if data.get("format") != "hmda-shigai-runtime":
        raise FootprintError("runtime format must be 'hmda-shigai-runtime'")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FootprintError("runtime cases must be a non-empty list")
    return data


def select_case(plan: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    cases = plan["cases"]
    if case_id is None:
        if len(cases) != 1:
            raise FootprintError("--case-id is required when plan contains multiple cases")
        case = cases[0]
    else:
        matches = [case for case in cases if case.get("id") == case_id]
        if len(matches) != 1:
            raise FootprintError(f"case {case_id!r} not found exactly once in plan")
        case = matches[0]
    if not isinstance(case, dict) or not isinstance(case.get("id"), str):
        raise FootprintError("invalid case record in plan")
    return case


def select_runtime_case(runtime: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [case for case in runtime["cases"] if isinstance(case, dict) and case.get("id") == case_id]
    if len(matches) != 1:
        raise FootprintError(f"runtime case {case_id!r} not found exactly once")
    return matches[0]


def _bbox(mask: Image.Image) -> list[int] | None:
    box = mask.getbbox()
    return list(box) if box is not None else None


def _pixel_count(mask: Image.Image) -> int:
    return int(sum(mask.histogram()[1:]))


def _changed_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    diff = ImageChops.difference(before.convert("RGBA"), after.convert("RGBA"))
    bands = diff.split()
    combined = bands[0]
    for band in bands[1:]:
        combined = ImageChops.lighter(combined, band)
    return combined.point(lambda value: 255 if value else 0, mode="1")


def _runtime_records(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in runtime["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise FootprintError("runtime contains invalid case record")
        cid = case["id"]
        objects = case.get("objects")
        if not isinstance(objects, list):
            raise FootprintError(f"{cid}: runtime objects must be a list")
        for obj in objects:
            if not isinstance(obj, dict):
                raise FootprintError(f"{cid}: invalid runtime object record")
            for field in ("cell", "type", "occupiable", "blocked"):
                if field not in obj:
                    raise FootprintError(f"{cid}: runtime object missing {field}")
            records.append(props.semantic_record(cid, obj))
    return records


def _case_runtime_semantics(case: dict[str, Any]) -> list[dict[str, Any]]:
    cid = case.get("id")
    objects = case.get("objects")
    if not isinstance(cid, str) or not isinstance(objects, list):
        raise FootprintError("invalid runtime case semantics")
    records = []
    for obj in objects:
        if not isinstance(obj, dict):
            raise FootprintError(f"{cid}: invalid runtime object record")
        records.append(props.semantic_record(cid, obj))
    return sorted(
        records,
        key=lambda rec: (
            str(rec["cell"]),
            str(rec["type"]),
            props.variant_key(rec["variant"]),
        ),
    )


def _case_plan_semantics(case: dict[str, Any]) -> list[dict[str, Any]]:
    cid = case.get("id")
    objects = case.get("objects")
    if not isinstance(cid, str) or not isinstance(objects, list):
        raise FootprintError("invalid plan case semantics")
    records: list[dict[str, Any]] = []
    for obj in objects:
        if not isinstance(obj, dict):
            raise FootprintError(f"{cid}: invalid plan object record")
        for field in ("cell", "source_type", "occupiable", "blocked"):
            if field not in obj:
                raise FootprintError(f"{cid}: plan object missing {field}")
        records.append(
            {
                "case_id": cid,
                "cell": obj["cell"],
                "type": obj["source_type"],
                "variant": obj.get("source_variant"),
                "occupiable": obj["occupiable"],
                "blocked": obj["blocked"],
            }
        )
    return sorted(
        records,
        key=lambda rec: (
            str(rec["cell"]),
            str(rec["type"]),
            props.variant_key(rec["variant"]),
        ),
    )


def _grid_tuple(case: dict[str, Any], label: str) -> tuple[int, int]:
    grid = case.get("grid") or {}
    try:
        rows = int(grid["rows"])
        cols = int(grid["columns"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FootprintError(f"{label}: invalid grid") from exc
    if rows <= 0 or cols <= 0:
        raise FootprintError(f"{label}: invalid grid")
    return rows, cols


def _character_placements(runtime_case: dict[str, Any]) -> set[str]:
    cid = runtime_case.get("id")
    rows, cols = _grid_tuple(runtime_case, f"{cid} runtime")
    characters = runtime_case.get("characters")
    if characters is None:
        raise FootprintError(f"{cid}: solution-surface guard requires runtime characters")
    if not isinstance(characters, list):
        raise FootprintError(f"{cid}: runtime characters must be a list")

    placements: set[str] = set()
    for index, character in enumerate(characters):
        if not isinstance(character, dict) or "placement" not in character:
            raise FootprintError(f"{cid}: character {index} has no placement")
        cell = str(character["placement"]).upper()
        try:
            col, row = props.parse_cell(cell)
        except props.PresentationError as exc:
            raise FootprintError(str(exc)) from exc
        if not (0 <= col < cols and 0 <= row < rows):
            raise FootprintError(f"{cid}: character placement {cell} outside grid")
        if cell in placements:
            raise FootprintError(f"{cid}: duplicate character placement {cell}")
        placements.add(cell)
    return placements


def bind_plan_to_runtime(
    plan: dict[str, Any],
    plan_case: dict[str, Any],
    runtime: dict[str, Any],
    *,
    surface: str,
) -> tuple[dict[str, Any], set[str]]:
    """Prove the plan still describes the exact locked runtime semantics.

    The plan-level SHA guards the whole runtime inventory. The direct per-case
    comparison separately prevents a tampered plan from moving an allowed box
    while retaining an old top-level fingerprint.
    """
    if surface not in {"puzzle", "solution"}:
        raise FootprintError(f"unsupported map surface {surface!r}")

    runtime_records = _runtime_records(runtime)
    actual_sha = props.semantic_fingerprint(runtime_records)
    expected_sha = plan.get("object_semantics_sha256")
    if not isinstance(expected_sha, str) or expected_sha != actual_sha:
        raise FootprintError(
            "modern-prop plan semantic fingerprint does not match locked runtime"
        )

    cid = str(plan_case["id"])
    runtime_case = select_runtime_case(runtime, cid)
    plan_grid = _grid_tuple(plan_case, f"{cid} plan")
    runtime_grid = _grid_tuple(runtime_case, f"{cid} runtime")
    if plan_grid != runtime_grid:
        raise FootprintError(
            f"{cid}: plan/runtime grid mismatch plan={plan_grid} runtime={runtime_grid}"
        )
    if _case_plan_semantics(plan_case) != _case_runtime_semantics(runtime_case):
        raise FootprintError(f"{cid}: plan object semantics drift from locked runtime")

    protected = _character_placements(runtime_case) if surface == "solution" else set()
    return runtime_case, protected


def approved_mask(
    case: dict[str, Any],
    width: int,
    height: int,
    *,
    protected_cells: set[str] | None = None,
) -> tuple[Image.Image, list[dict[str, Any]]]:
    grid = case.get("grid") or {}
    rows, cols = int(grid.get("rows", 0)), int(grid.get("columns", 0))
    if rows <= 0 or cols <= 0:
        raise FootprintError(f"{case.get('id')}: invalid grid")
    if width < cols or height < rows:
        raise FootprintError(f"{case.get('id')}: raster smaller than grid")

    protected = {str(cell).upper() for cell in (protected_cells or set())}
    cell_w, cell_h = width / cols, height / rows
    mask_image = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(mask_image)
    records: list[dict[str, Any]] = []
    seen_cells: set[str] = set()

    objects = case.get("objects")
    if not isinstance(objects, list):
        raise FootprintError(f"{case.get('id')}: objects must be a list")
    for obj in objects:
        if not isinstance(obj, dict):
            raise FootprintError(f"{case.get('id')}: invalid object record")
        for field in ("cell", "render_box", "source_type", "occupiable", "blocked"):
            if field not in obj:
                raise FootprintError(f"{case.get('id')}: object missing {field}")
        if not isinstance(obj["occupiable"], bool) or not isinstance(obj["blocked"], bool):
            raise FootprintError(f"{case.get('id')}/{obj['cell']}: invalid semantic flags")
        if obj["blocked"] == obj["occupiable"]:
            raise FootprintError(
                f"{case.get('id')}/{obj['cell']}: blocked must be inverse of occupiable"
            )
        cell = str(obj["cell"]).upper()
        if cell in seen_cells:
            raise FootprintError(f"{case.get('id')}: duplicate object cell {cell}")
        seen_cells.add(cell)
        try:
            col, row = props.parse_cell(cell)
        except props.PresentationError as exc:
            raise FootprintError(str(exc)) from exc
        if not (0 <= col < cols and 0 <= row < rows):
            raise FootprintError(f"{case.get('id')}/{cell}: object outside grid")
        try:
            left, top, right, bottom = props.box_pixels(
                col, row, cell_w, cell_h, str(obj["render_box"])
            )
        except props.PresentationError as exc:
            raise FootprintError(str(exc)) from exc
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise FootprintError(f"{case.get('id')}/{cell}: approved box outside raster")

        is_protected = cell in protected
        if not is_protected:
            # Mode "1" must be painted with canonical 255 values. Pillow accepts
            # integer 1 but ImageChops.invert then yields 254, which is still
            # truthy for logical operations and would misclassify approved pixels.
            draw.rectangle((left, top, right - 1, bottom - 1), fill=255)
        records.append(
            {
                "cell": cell,
                "source_type": obj["source_type"],
                "source_variant": obj.get("source_variant"),
                "occupiable": obj["occupiable"],
                "blocked": obj["blocked"],
                "render_box": obj["render_box"],
                "bbox": [left, top, right, bottom],
                "protected_person_cell": is_protected,
            }
        )

    return mask_image, records


def validate_images(
    before: Image.Image,
    after: Image.Image,
    case: dict[str, Any],
    *,
    require_changes: bool = False,
    surface: str = "puzzle",
    protected_cells: set[str] | None = None,
) -> dict[str, Any]:
    if surface not in {"puzzle", "solution"}:
        raise FootprintError(f"unsupported map surface {surface!r}")
    if before.size != after.size:
        raise FootprintError(
            f"raster size mismatch: before={before.size}, after={after.size}"
        )
    width, height = before.size
    protected = {str(cell).upper() for cell in (protected_cells or set())}
    allowed, object_records = approved_mask(
        case, width, height, protected_cells=protected
    )
    changed = _changed_mask(before, after)
    changed_count = _pixel_count(changed)
    if require_changes and changed_count == 0:
        raise FootprintError("candidate composite made no pixel changes")
    outside = ImageChops.logical_and(changed, ImageChops.invert(allowed))
    outside_count = _pixel_count(outside)
    if outside_count:
        protected_changed = [
            record["cell"]
            for record in object_records
            if record["protected_person_cell"]
            and _pixel_count(changed.crop(tuple(record["bbox"]))) > 0
        ]
        detail = (
            f"; protected_person_cells_changed={sorted(protected_changed)}"
            if protected_changed
            else ""
        )
        raise FootprintError(
            f"{case.get('id')}: {outside_count} changed pixels escaped approved object boxes; "
            f"outside_bbox={_bbox(outside)}{detail}"
        )

    per_object: list[dict[str, Any]] = []
    for record in object_records:
        left, top, right, bottom = record["bbox"]
        per_object.append(
            {
                **record,
                "changed_pixels": _pixel_count(changed.crop((left, top, right, bottom))),
            }
        )

    return {
        "status": "PASS",
        "case_id": case.get("id"),
        "surface": surface,
        "image_size": [width, height],
        "changed_pixels": changed_count,
        "changed_bbox": _bbox(changed),
        "approved_pixels": _pixel_count(allowed),
        "outside_changed_pixels": 0,
        "protected_person_cells": sorted(protected),
        "object_count": len(object_records),
        "objects": per_object,
    }


def _synthetic_case(n: int) -> dict[str, Any]:
    last = f"{chr(64 + n)}{n}"
    return {
        "id": f"HMDA_{n}",
        "grid": {"rows": n, "columns": n},
        "objects": [
            {
                "cell": "B2",
                "source_type": "seat",
                "source_variant": None,
                "occupiable": True,
                "blocked": False,
                "presentation_key": "modern_seat",
                "render_box": "cell_center_safe",
                "asset_path": "modern_props/seat.png",
                "asset_sha256": "0" * 64,
            },
            {
                "cell": last,
                "source_type": "locker",
                "source_variant": "closed",
                "occupiable": False,
                "blocked": True,
                "presentation_key": "modern_locker",
                "render_box": "cell_core",
                "asset_path": "modern_props/locker.png",
                "asset_sha256": "1" * 64,
            },
        ],
    }


def _synthetic_runtime(case: dict[str, Any]) -> dict[str, Any]:
    objects = []
    for obj in case["objects"]:
        objects.append(
            {
                "cell": obj["cell"],
                "type": obj["source_type"],
                "variant": obj.get("source_variant"),
                "occupiable": obj["occupiable"],
                "blocked": obj["blocked"],
            }
        )
    return {
        "format": "hmda-shigai-runtime",
        "version": 1,
        "cases": [
            {
                "id": case["id"],
                "grid": dict(case["grid"]),
                "objects": objects,
                "characters": [
                    {"name": "Witness Alpha", "placement": "B2"},
                    {"name": "Witness Beta", "placement": "A1"},
                ],
            }
        ],
    }


def _synthetic_plan(case: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": "hmda-modern-prop-plan",
        "version": 1,
        "mode": "presentation_only",
        "object_semantics_sha256": props.semantic_fingerprint(_runtime_records(runtime)),
        "case_count": 1,
        "object_count": len(case["objects"]),
        "cases": [case],
    }


def _grid_image(n: int, cell_px: int = 44) -> Image.Image:
    im = Image.new("RGBA", (n * cell_px, n * cell_px), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    for i in range(n + 1):
        p = i * cell_px
        draw.line((p, 0, p, n * cell_px - 1), fill=(30, 30, 30, 255), width=1)
        draw.line((0, p, n * cell_px - 1, p), fill=(30, 30, 30, 255), width=1)
    return im


def _draw_object_change(after: Image.Image, obj: dict[str, Any], cell_px: int = 44) -> None:
    draw = ImageDraw.Draw(after)
    col, row = props.parse_cell(obj["cell"])
    box = props.box_pixels(col, row, cell_px, cell_px, obj["render_box"])
    draw.rounded_rectangle(
        (box[0] + 2, box[1] + 2, box[2] - 3, box[3] - 3),
        radius=3,
        outline=(0, 0, 0, 255),
        width=2,
    )


def self_test() -> None:
    for n in (6, 7, 9):
        case = _synthetic_case(n)
        runtime = _synthetic_runtime(case)
        plan = _synthetic_plan(case, runtime)

        _, puzzle_protected = bind_plan_to_runtime(
            plan, case, runtime, surface="puzzle"
        )
        assert puzzle_protected == set()
        _, solution_protected = bind_plan_to_runtime(
            plan, case, runtime, surface="solution"
        )
        assert solution_protected == {"A1", "B2"}

        before = _grid_image(n)
        after = before.copy()
        for obj in case["objects"]:
            _draw_object_change(after, obj)
        report = validate_images(
            before,
            after,
            case,
            require_changes=True,
            surface="puzzle",
            protected_cells=puzzle_protected,
        )
        assert report["outside_changed_pixels"] == 0
        assert report["changed_pixels"] > 0
        assert report["object_count"] == 2

        # The same composite must fail on the solution surface because B2 holds
        # a witness/person marker there.
        try:
            validate_images(
                before,
                after,
                case,
                require_changes=True,
                surface="solution",
                protected_cells=solution_protected,
            )
        except FootprintError as exc:
            assert "protected_person_cells_changed" in str(exc)
            assert "B2" in str(exc)
        else:
            raise AssertionError(f"{n}x{n}: solution prop may not cover person cell B2")

        # A change to the unoccupied locker cell remains allowed on solutions.
        solution_safe = before.copy()
        _draw_object_change(solution_safe, case["objects"][1])
        solution_report = validate_images(
            before,
            solution_safe,
            case,
            require_changes=True,
            surface="solution",
            protected_cells=solution_protected,
        )
        assert solution_report["outside_changed_pixels"] == 0
        assert "B2" in solution_report["protected_person_cells"]

        leaked = after.copy()
        leaked.putpixel((2, 2), (0, 0, 0, 255))
        try:
            validate_images(before, leaked, case, require_changes=True)
        except FootprintError as exc:
            assert "escaped approved object boxes" in str(exc)
        else:
            raise AssertionError(f"{n}x{n}: one-pixel leak must fail closed")

        try:
            validate_images(before, before.copy(), case, require_changes=True)
        except FootprintError as exc:
            assert "no pixel changes" in str(exc)
        else:
            raise AssertionError(f"{n}x{n}: require_changes must reject no-op composite")

        # Top-level SHA alone is not enough: direct case semantics must also bind.
        tampered_case = json.loads(json.dumps(case))
        tampered_case["objects"][0]["cell"] = "C3"
        tampered_plan = dict(plan)
        tampered_plan["cases"] = [tampered_case]
        try:
            bind_plan_to_runtime(tampered_plan, tampered_case, runtime, surface="puzzle")
        except FootprintError as exc:
            assert "plan object semantics drift" in str(exc)
        else:
            raise AssertionError(f"{n}x{n}: moved plan box must fail runtime binding")

        stale_runtime = json.loads(json.dumps(runtime))
        stale_runtime["cases"][0]["objects"][0]["blocked"] = True
        try:
            bind_plan_to_runtime(plan, case, stale_runtime, surface="puzzle")
        except FootprintError as exc:
            assert "semantic fingerprint" in str(exc)
        else:
            raise AssertionError(f"{n}x{n}: runtime semantic drift must fail SHA binding")

    alpha_before = Image.new("RGBA", (60, 60), (255, 255, 255, 255))
    alpha_after = alpha_before.copy()
    alpha_after.putpixel((2, 2), (255, 255, 255, 0))
    try:
        validate_images(alpha_before, alpha_after, _synthetic_case(6))
    except FootprintError as exc:
        assert "escaped approved object boxes" in str(exc)
    else:
        raise AssertionError("alpha-only leak must fail closed")

    try:
        validate_images(
            Image.new("RGBA", (100, 100), "white"),
            Image.new("RGBA", (101, 100), "white"),
            _synthetic_case(6),
        )
    except FootprintError as exc:
        assert "size mismatch" in str(exc)
    else:
        raise AssertionError("raster size mismatch must fail closed")

    invalid = _synthetic_case(6)
    invalid["objects"][0]["cell"] = "Z99"
    try:
        validate_images(_grid_image(6), _grid_image(6), invalid)
    except FootprintError as exc:
        assert "outside grid" in str(exc)
    else:
        raise AssertionError("out-of-grid approved object must fail closed")

    print(
        "PASS: modern-prop footprint guard binds to locked runtime semantics, "
        "confines 6x6/7x7/9x9 changes to approved boxes, protects solution "
        "person cells, and catches RGB/alpha leaks"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", type=Path)
    ap.add_argument("--after", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--runtime", type=Path)
    ap.add_argument("--case-id")
    ap.add_argument("--surface", choices=("puzzle", "solution"), default="puzzle")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--require-changes", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.before is None or args.after is None or args.plan is None:
        ap.error("--before, --after and --plan are required unless --self-test is selected")
    if args.surface == "solution" and args.runtime is None:
        ap.error("--runtime is required for --surface solution")

    try:
        plan = load_plan(args.plan.expanduser().resolve())
        case = select_case(plan, args.case_id)
        protected_cells: set[str] = set()
        runtime_bound = False
        if args.runtime is not None:
            runtime = load_runtime(args.runtime.expanduser().resolve())
            _, protected_cells = bind_plan_to_runtime(
                plan, case, runtime, surface=args.surface
            )
            runtime_bound = True
        with Image.open(args.before.expanduser().resolve()) as before_im:
            before = before_im.copy()
        with Image.open(args.after.expanduser().resolve()) as after_im:
            after = after_im.copy()
        report = validate_images(
            before,
            after,
            case,
            require_changes=args.require_changes,
            surface=args.surface,
            protected_cells=protected_cells,
        )
        report["runtime_bound"] = runtime_bound
        if args.surface == "solution" and not runtime_bound:
            raise FootprintError("solution surface must be bound to locked runtime")
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        FootprintError,
        props.PresentationError,
    ) as exc:
        print(f"HMDA MODERN PROP FOOTPRINT: BLOCKED - {exc}", file=sys.stderr)
        return 2

    if args.report is not None:
        target = args.report.expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    binding = "runtime-bound" if report["runtime_bound"] else "plan-only"
    print(
        f"PASS: {report['case_id']} {report['surface']} ({binding}) changed "
        f"{report['changed_pixels']} pixels; all changes are confined to approved "
        "modern-prop object boxes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
