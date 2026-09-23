#!/usr/bin/env python3
"""Prepare and validate cell-confined modern-prop overlays for HMDA maps.

This module is intentionally presentation-only. It never mutates runtime puzzle
semantics and it does not erase or replace source Shigai pixels by itself.
Instead it resolves exact catalog mappings, validates an asset pack, computes
strict per-cell safe boxes, and can render an isolated transparent overlay.
A later integration step may composite that overlay only after a before/after
footprint validator proves that no pixels outside the approved object boxes
changed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

import yaml
from PIL import Image, ImageDraw

TOOL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = TOOL_ROOT / "content" / "modern_prop_catalog.template.yml"
DEFAULT_ASSETS = TOOL_ROOT / "content" / "modern_prop_assets.template.yml"

SAFE_BOXES = {
    "cell_core": (0.16, 0.16, 0.84, 0.84),
    "cell_center_safe": (0.24, 0.24, 0.76, 0.76),
}


class PresentationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PresentationError(f"{path} must contain a JSON object")
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PresentationError(f"{path} must contain a YAML mapping")
    return data


def variant_key(value: Any) -> str:
    if value is None:
        return "__none__"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def resolve_mapping(catalog: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    types = catalog.get("types")
    if not isinstance(types, dict):
        raise PresentationError("catalog types must be a mapping")
    source_type = obj.get("type")
    mapping = types.get(source_type)
    if not isinstance(mapping, dict):
        raise PresentationError(f"no modern-prop mapping for source type {source_type!r}")
    variants = mapping.get("variants") or {}
    if not isinstance(variants, dict):
        raise PresentationError(f"catalog variants for {source_type!r} must be a mapping")
    override = variants.get(variant_key(obj.get("variant")))
    if override is None:
        resolved = dict(mapping)
        resolved.pop("variants", None)
        return resolved
    if not isinstance(override, dict):
        raise PresentationError(
            f"variant override {source_type!r}/{variant_key(obj.get('variant'))!r} must be a mapping"
        )
    resolved = dict(mapping)
    resolved.pop("variants", None)
    resolved.update(override)
    return resolved


def parse_cell(cell: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", str(cell).strip().upper())
    if not match:
        raise PresentationError(f"invalid cell {cell!r}")
    col = 0
    for ch in match.group(1):
        col = col * 26 + ord(ch) - ord("A") + 1
    return col - 1, int(match.group(2)) - 1


def semantic_record(case_id: str, obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "cell": obj.get("cell"),
        "type": obj.get("type"),
        "variant": obj.get("variant"),
        "occupiable": obj.get("occupiable"),
        "blocked": obj.get("blocked"),
    }


def semantic_fingerprint(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        sorted(
            records,
            key=lambda r: (
                str(r["case_id"]),
                str(r["cell"]),
                str(r["type"]),
                variant_key(r["variant"]),
            ),
        ),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def safe_asset_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PresentationError("asset path must be a non-empty relative POSIX path")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or value.startswith("~"):
        raise PresentationError(f"unsafe asset path {value!r}")
    if p.suffix.lower() != ".png":
        raise PresentationError(f"modern-prop asset must be PNG: {value!r}")
    return p.as_posix()


def asset_entry(manifest: dict[str, Any], key: str) -> dict[str, Any]:
    if manifest.get("mode") != "presentation_only":
        raise PresentationError("asset manifest mode must be 'presentation_only'")
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        raise PresentationError("asset manifest assets must be a mapping")
    entry = assets.get(key)
    if not isinstance(entry, dict):
        raise PresentationError(f"missing modern-prop asset entry {key!r}")
    path = safe_asset_path(entry.get("path"))
    sha = entry.get("sha256")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise PresentationError(f"asset {key!r} must declare lowercase sha256")
    return {**entry, "path": path}


def normalized_box(render_box: str) -> tuple[float, float, float, float]:
    try:
        return SAFE_BOXES[render_box]
    except KeyError as exc:
        raise PresentationError(f"unsupported render_box {render_box!r}") from exc


def box_pixels(
    col: int,
    row: int,
    cell_w: float,
    cell_h: float,
    render_box: str,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = normalized_box(render_box)
    left = round((col + x0) * cell_w)
    top = round((row + y0) * cell_h)
    right = round((col + x1) * cell_w)
    bottom = round((row + y1) * cell_h)
    if right <= left or bottom <= top:
        raise PresentationError("computed modern-prop box is empty")
    return left, top, right, bottom


def fit_sprite(sprite: Image.Image, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        raise PresentationError("sprite target box must be positive")
    sprite = sprite.convert("RGBA")
    bbox = sprite.getbbox()
    if bbox is None:
        raise PresentationError("modern-prop sprite is fully transparent")
    sprite = sprite.crop(bbox)
    sprite.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    x = (width - sprite.width) // 2
    y = (height - sprite.height) // 2
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def validate_sprite_bytes(key: str, entry: dict[str, Any], raw: bytes) -> Image.Image:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != entry["sha256"]:
        raise PresentationError(f"asset {key!r} sha256 mismatch")
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:
        raise PresentationError(f"asset {key!r} is not a readable PNG") from exc
    if image.format != "PNG":
        raise PresentationError(f"asset {key!r} is not a PNG")
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getbbox() is None:
        raise PresentationError(f"asset {key!r} is fully transparent")
    min_alpha, max_alpha = alpha.getextrema()
    if min_alpha > 0 or max_alpha == 0:
        raise PresentationError(
            f"asset {key!r} must contain transparent background and visible ink"
        )
    return rgba


def build_plan(
    runtime: dict[str, Any],
    catalog: dict[str, Any],
    assets: dict[str, Any],
) -> dict[str, Any]:
    if runtime.get("format") != "hmda-shigai-runtime":
        raise PresentationError("runtime format must be 'hmda-shigai-runtime'")
    if catalog.get("mode") != "presentation_only":
        raise PresentationError("catalog mode must be 'presentation_only'")
    cases = runtime.get("cases")
    if not isinstance(cases, list) or not cases:
        raise PresentationError("runtime cases must be a non-empty list")

    records: list[dict[str, Any]] = []
    planned_cases: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise PresentationError("invalid runtime case")
        cid = case["id"]
        grid = case.get("grid") or {}
        rows, cols = int(grid.get("rows", 0)), int(grid.get("columns", 0))
        if rows <= 0 or cols <= 0:
            raise PresentationError(f"{cid}: invalid grid")
        planned: list[dict[str, Any]] = []
        seen_cells: set[str] = set()
        for obj in case.get("objects") or []:
            if not isinstance(obj, dict):
                raise PresentationError(f"{cid}: invalid object record")
            for field in ("cell", "type", "occupiable", "blocked"):
                if field not in obj:
                    raise PresentationError(f"{cid}: object missing {field}")
            if not isinstance(obj["occupiable"], bool) or not isinstance(obj["blocked"], bool):
                raise PresentationError(
                    f"{cid}/{obj['cell']}: invalid blocked/occupiable flags"
                )
            if obj["blocked"] == obj["occupiable"]:
                raise PresentationError(
                    f"{cid}/{obj['cell']}: blocked must be inverse of occupiable"
                )
            cell = str(obj["cell"]).upper()
            if cell in seen_cells:
                raise PresentationError(f"{cid}: duplicate object cell {cell}")
            seen_cells.add(cell)
            col, row = parse_cell(cell)
            if not (0 <= col < cols and 0 <= row < rows):
                raise PresentationError(f"{cid}/{cell}: object outside grid")
            mapping = resolve_mapping(catalog, obj)
            key = mapping.get("presentation_key")
            if not isinstance(key, str) or not key:
                raise PresentationError(f"{cid}/{cell}: mapping has no presentation_key")
            allowed = mapping.get("allowed_occupiable")
            if not isinstance(allowed, list) or obj["occupiable"] not in allowed:
                raise PresentationError(
                    f"{cid}/{cell}: mapping {key!r} rejects "
                    f"occupiable={obj['occupiable']}"
                )
            render_box = mapping.get("render_box")
            normalized_box(str(render_box))
            entry = asset_entry(assets, key)
            records.append(semantic_record(cid, obj))
            planned.append(
                {
                    "cell": cell,
                    "source_type": obj["type"],
                    "source_variant": obj.get("variant"),
                    "occupiable": obj["occupiable"],
                    "blocked": obj["blocked"],
                    "presentation_key": key,
                    "render_box": render_box,
                    "asset_path": entry["path"],
                    "asset_sha256": entry["sha256"],
                }
            )
        planned_cases.append(
            {"id": cid, "grid": {"rows": rows, "columns": cols}, "objects": planned}
        )

    return {
        "format": "hmda-modern-prop-plan",
        "version": 1,
        "mode": "presentation_only",
        "source_runtime_version": runtime.get("version"),
        "object_semantics_sha256": semantic_fingerprint(records),
        "case_count": len(planned_cases),
        "object_count": len(records),
        "cases": planned_cases,
    }


def render_isolated_overlay(
    case_plan: dict[str, Any],
    asset_root: Path,
    asset_bytes: dict[str, bytes] | None = None,
    *,
    cell_px: int = 128,
) -> Image.Image:
    rows = int(case_plan["grid"]["rows"])
    cols = int(case_plan["grid"]["columns"])
    canvas = Image.new(
        "RGBA", (cols * cell_px, rows * cell_px), (255, 255, 255, 0)
    )
    for obj in case_plan["objects"]:
        col, row = parse_cell(obj["cell"])
        left, top, right, bottom = box_pixels(
            col, row, cell_px, cell_px, obj["render_box"]
        )
        path = obj["asset_path"]
        raw = asset_bytes[path] if asset_bytes is not None else (asset_root / path).read_bytes()
        entry = {"sha256": obj["asset_sha256"]}
        sprite = validate_sprite_bytes(obj["presentation_key"], entry, raw)
        fitted = fit_sprite(sprite, right - left, bottom - top)
        canvas.alpha_composite(fitted, (left, top))
    return canvas


def _png_bytes(size: int = 96) -> bytes:
    im = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(
        (18, 22, size - 18, size - 22),
        radius=10,
        outline=(0, 0, 0, 255),
        width=5,
    )
    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()


def self_test() -> None:
    raw = _png_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    catalog = {
        "version": 1,
        "mode": "presentation_only",
        "types": {
            "seat": {
                "presentation_key": "modern_seat",
                "allowed_occupiable": [True],
                "render_box": "cell_center_safe",
            },
            "locker": {
                "presentation_key": "modern_locker",
                "allowed_occupiable": [False],
                "render_box": "cell_core",
            },
        },
    }
    assets = {
        "version": 1,
        "mode": "presentation_only",
        "assets": {
            "modern_seat": {
                "path": "modern_props/seat.png",
                "sha256": digest,
            },
            "modern_locker": {
                "path": "modern_props/locker.png",
                "sha256": digest,
            },
        },
    }
    runtime = {"format": "hmda-shigai-runtime", "version": 1, "cases": []}
    for n, cid in ((6, "HMDA_6"), (7, "HMDA_7"), (9, "HMDA_9")):
        runtime["cases"].append(
            {
                "id": cid,
                "grid": {"rows": n, "columns": n},
                "objects": [
                    {
                        "cell": "B2",
                        "type": "seat",
                        "variant": None,
                        "occupiable": True,
                        "blocked": False,
                    },
                    {
                        "cell": f"{chr(64 + n)}{n}",
                        "type": "locker",
                        "variant": "closed",
                        "occupiable": False,
                        "blocked": True,
                    },
                ],
            }
        )
    plan = build_plan(runtime, catalog, assets)
    assert plan["case_count"] == 3 and plan["object_count"] == 6
    baseline = plan["object_semantics_sha256"]
    catalog["types"]["seat"]["presentation_key"] = "modern_seat"
    assert build_plan(runtime, catalog, assets)["object_semantics_sha256"] == baseline

    data = {"modern_props/seat.png": raw, "modern_props/locker.png": raw}
    for case in plan["cases"]:
        overlay = render_isolated_overlay(case, Path("."), data, cell_px=80)
        alpha = overlay.getchannel("A")
        px = alpha.load()
        rows = case["grid"]["rows"]
        cols = case["grid"]["columns"]
        allowed = set()
        for obj in case["objects"]:
            col, row = parse_cell(obj["cell"])
            left, top, right, bottom = box_pixels(
                col, row, 80, 80, obj["render_box"]
            )
            allowed.update(
                (x, y)
                for y in range(top, bottom)
                for x in range(left, right)
            )
        actual = {
            (x, y)
            for y in range(rows * 80)
            for x in range(cols * 80)
            if px[x, y] > 0
        }
        assert actual and actual <= allowed, (
            f"{case['id']}: overlay escaped approved cell box"
        )

    bad_assets = json.loads(json.dumps(assets))
    bad_assets["assets"]["modern_seat"]["path"] = "../escape.png"
    try:
        build_plan(runtime, catalog, bad_assets)
    except PresentationError:
        pass
    else:
        raise AssertionError("path traversal must fail closed")

    broken = json.loads(json.dumps(runtime))
    broken["cases"][0]["objects"][0]["blocked"] = True
    try:
        build_plan(broken, catalog, assets)
    except PresentationError:
        pass
    else:
        raise AssertionError("semantic drift must fail closed")

    missing = json.loads(json.dumps(assets))
    del missing["assets"]["modern_locker"]
    try:
        build_plan(runtime, catalog, missing)
    except PresentationError:
        pass
    else:
        raise AssertionError("missing asset must fail closed")

    print(
        "PASS: modern-prop overlay planning is cell-confined for "
        "6x6/7x7/9x9 and preserves semantics"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime", type=Path)
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.runtime is None or args.plan is None:
        ap.error("--runtime and --plan are required unless --self-test is selected")
    try:
        runtime = load_json(args.runtime.expanduser().resolve())
        catalog = load_yaml(args.catalog.expanduser().resolve())
        assets = load_yaml(args.assets.expanduser().resolve())
        plan = build_plan(runtime, catalog, assets)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
        PresentationError,
    ) as exc:
        print(f"HMDA MODERN PROP PRESENTATION: BLOCKED - {exc}", file=sys.stderr)
        return 2
    target = args.plan.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"PASS: planned {plan['object_count']} presentation-only modern props "
        f"across {plan['case_count']} cases"
    )
    print(f"PASS: object semantics sha256 = {plan['object_semantics_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
