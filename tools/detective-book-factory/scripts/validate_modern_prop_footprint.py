#!/usr/bin/env python3
"""Fail-closed pixel-footprint guard for future HMDA modern-prop composites.

The modern-prop layer is presentation-only. This validator compares a locked
pre-composite map raster with a candidate post-composite raster and proves that
every changed pixel is confined to catalog-approved object boxes from an
`hmda-modern-prop-plan`. It deliberately does not decide which prop art is good;
it only protects the spatial puzzle surface from collateral pixel changes.

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


def approved_mask(
    case: dict[str, Any], width: int, height: int
) -> tuple[Image.Image, list[dict[str, Any]]]:
    grid = case.get("grid") or {}
    rows, cols = int(grid.get("rows", 0)), int(grid.get("columns", 0))
    if rows <= 0 or cols <= 0:
        raise FootprintError(f"{case.get('id')}: invalid grid")
    if width < cols or height < rows:
        raise FootprintError(f"{case.get('id')}: raster smaller than grid")

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
        draw.rectangle((left, top, right - 1, bottom - 1), fill=1)
        records.append(
            {
                "cell": cell,
                "source_type": obj["source_type"],
                "source_variant": obj.get("source_variant"),
                "occupiable": obj["occupiable"],
                "blocked": obj["blocked"],
                "render_box": obj["render_box"],
                "bbox": [left, top, right, bottom],
            }
        )

    return mask_image, records


def validate_images(
    before: Image.Image,
    after: Image.Image,
    case: dict[str, Any],
    *,
    require_changes: bool = False,
) -> dict[str, Any]:
    if before.size != after.size:
        raise FootprintError(
            f"raster size mismatch: before={before.size}, after={after.size}"
        )
    width, height = before.size
    allowed, object_records = approved_mask(case, width, height)
    changed = _changed_mask(before, after)
    changed_count = _pixel_count(changed)
    if require_changes and changed_count == 0:
        raise FootprintError("candidate composite made no pixel changes")
    outside = ImageChops.logical_and(changed, ImageChops.invert(allowed))
    outside_count = _pixel_count(outside)
    if outside_count:
        raise FootprintError(
            f"{case.get('id')}: {outside_count} changed pixels escaped approved object boxes; "
            f"outside_bbox={_bbox(outside)}"
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
        "image_size": [width, height],
        "changed_pixels": changed_count,
        "changed_bbox": _bbox(changed),
        "approved_pixels": _pixel_count(allowed),
        "outside_changed_pixels": 0,
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


def _grid_image(n: int, cell_px: int = 44) -> Image.Image:
    im = Image.new("RGBA", (n * cell_px, n * cell_px), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    for i in range(n + 1):
        p = i * cell_px
        draw.line((p, 0, p, n * cell_px - 1), fill=(30, 30, 30, 255), width=1)
        draw.line((0, p, n * cell_px - 1, p), fill=(30, 30, 30, 255), width=1)
    return im


def self_test() -> None:
    for n in (6, 7, 9):
        case = _synthetic_case(n)
        before = _grid_image(n)
        after = before.copy()
        draw = ImageDraw.Draw(after)
        for obj in case["objects"]:
            col, row = props.parse_cell(obj["cell"])
            box = props.box_pixels(col, row, 44, 44, obj["render_box"])
            draw.rounded_rectangle(
                (box[0] + 2, box[1] + 2, box[2] - 3, box[3] - 3),
                radius=3,
                outline=(0, 0, 0, 255),
                width=2,
            )
        report = validate_images(before, after, case, require_changes=True)
        assert report["outside_changed_pixels"] == 0
        assert report["changed_pixels"] > 0
        assert report["object_count"] == 2

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
        "PASS: modern-prop footprint guard confines all changes to approved "
        "object boxes for 6x6/7x7/9x9 and catches RGB/alpha pixel leaks"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", type=Path)
    ap.add_argument("--after", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--case-id")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--require-changes", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.before is None or args.after is None or args.plan is None:
        ap.error("--before, --after and --plan are required unless --self-test is selected")

    try:
        plan = load_plan(args.plan.expanduser().resolve())
        case = select_case(plan, args.case_id)
        with Image.open(args.before.expanduser().resolve()) as before_im:
            before = before_im.copy()
        with Image.open(args.after.expanduser().resolve()) as after_im:
            after = after_im.copy()
        report = validate_images(
            before, after, case, require_changes=args.require_changes
        )
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
    print(
        f"PASS: {report['case_id']} changed {report['changed_pixels']} pixels; "
        "all changes are confined to approved modern-prop object boxes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
