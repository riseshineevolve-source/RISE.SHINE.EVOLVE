#!/usr/bin/env python3
"""Check that map relabeling preserves dark pixels in locked object-cell cores.

This is deliberately independent of label detection. It compares rendered map
rasters with the hash-locked source at identical square-crop coordinates. The
central half of every object cell protects recognizable clue furniture without
confusing source label replacement near a cell edge with object deletion.
Verified source-label footprints (which can overlap furniture in the original
art) are separately recorded and excluded. Solutions also exclude the known
person-marker area in occupied cells. This does not certify object edges,
walls, label readability, or puzzle logic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

import render_spatial_map_hybrid as source
import render_spatial_map_hybrid_hardened as labels


def coordinate(cell: str) -> tuple[int, int]:
    return ord(cell[0].upper()) - ord("A"), int(cell[1:]) - 1


def compare_core(original: np.ndarray, rendered: np.ndarray, bounds: tuple[int, int, int, int],
                 marker: tuple[float, float, float, float] | None = None,
                 label_erasures: list[tuple[int, int, int, int]] = ()) -> dict:
    x0, y0, x1, y1 = bounds
    before = original[y0:y1, x0:x1]
    after = rendered[y0:y1, x0:x1]
    mask = before < 145
    if marker is not None:
        cx, cy, cell_w, cell_h = marker
        yy, xx = np.mgrid[y0:y1, x0:x1]
        mask &= ((xx - cx) / cell_w) ** 2 + ((yy - cy) / cell_h) ** 2 > .25 ** 2
    for left, top, right, bottom in label_erasures:
        ix0, iy0, ix1, iy1 = max(x0, left), max(y0, top), min(x1, right), min(y1, bottom)
        if ix0 < ix1 and iy0 < iy1:
            mask[iy0-y0:iy1-y0, ix0-x0:ix1-x0] = False
    changed = mask & (after != before)
    missing = mask & (after >= 145)
    return {"protected_dark_pixels": int(mask.sum()), "changed_dark_pixels": int(changed.sum()),
            "missing_dark_pixels": int(missing.sum()), "bbox": list(bounds),
            "marker_area_excluded": marker is not None}


def verified_label_erasures(case: dict, original: np.ndarray) -> list[dict]:
    """Return detected/explicit source pills only, never safe layout anchors.

    Detector candidates centered on an object are rejected by the hardened
    assignment gate. The attached-label exceptions use explicit source-bound
    metadata. Persist every exemption for independent inspection.
    """
    height, width = original.shape
    primary, _ = labels.assign_room_label_boxes(case, source.detect_room_label_boxes(original), width, height)
    broader, _ = labels.assign_room_label_boxes(case, source.detect_room_label_boxes(original, broad=True), width, height)
    assigned = {rid: (box, "detected_source_pill") for rid, box in primary.items()}
    for rid, box in broader.items():
        assigned.setdefault(rid, (box, "broad_source_pill"))
    for rid, reference in labels.explicit_reference_rooms(case).items():
        if rid in assigned:
            continue
        box = tuple(round(value * scale) for value, scale in zip(
            reference["normalized_footprint"], (width, height, width, height)))
        best, overlap, margin, _ = labels._box_room_scores(case, box, width, height)
        if best == rid and overlap >= .95 and margin >= .80:
            assigned[rid] = (box, reference.get("evidence_mode", "explicit_reference"))
    return [{"source_room_id": rid, "source_box": list(box), "evidence": evidence,
             "erasure_bbox": [max(0, box[0]-4), max(0, box[1]-4),
                              min(width, box[0]+box[2]+5), min(height, box[1]+box[3]+5)]}
            for rid, (box, evidence) in sorted(assigned.items())]


def self_test() -> None:
    original = np.full((100, 100), 220, dtype=np.uint8)
    original[30:70, 30:70] = 35
    whitened = original.copy()
    whitened[whitened >= 185] = 255
    bounds = (25, 25, 75, 75)
    assert compare_core(original, whitened, bounds)["changed_dark_pixels"] == 0
    erased = whitened.copy()
    erased[40:50, 30:70] = 255
    result = compare_core(original, erased, bounds)
    assert result["missing_dark_pixels"] == 400, result
    erased[65:70, 30:70] = 255
    result = compare_core(original, erased, bounds, label_erasures=[(30, 65, 70, 70)])
    assert result["missing_dark_pixels"] == 400, "A label exception must not hide unrelated furniture loss"
    print("PASS: object-core comparison permits paper whitening and catches a deleted bench strip")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--maps", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if any(value is None for value in (args.source_pdf, args.runtime, args.maps, args.report)):
        parser.error("--source-pdf, --runtime, --maps and --report are required unless --self-test is selected")
    selection = source.load_yaml(source.TOOL_ROOT / "content/spatial_source_manifest_final.yml")
    actual_hash = source.sha256(args.source_pdf)
    if actual_hash != selection["source"]["source_pdf_sha256"]:
        raise SystemExit("BLOCKED: immutable source PDF hash mismatch")
    cases = {case["id"]: case for case in source.load_runtime(args.runtime)["cases"]}
    requested = set(args.case)
    if requested - set(cases):
        raise SystemExit(f"Unknown case IDs: {sorted(requested-set(cases))}")
    checks, failures, page_erasures, map_records = [], [], [], []
    with source.fitz.open(args.source_pdf) as pdf:
        for declaration in selection["cases"]:
            cid = declaration["id"]
            if requested and cid not in requested:
                continue
            case = cases[cid]
            rows, cols = case["grid"]["rows"], case["grid"]["columns"]
            occupied = {person["placement"] for person in case["characters"]}
            for role in ("puzzle", "solution"):
                path = args.maps / f"{cid}_{role}_original_shigai_relabelled.png"
                if not path.is_file():
                    failures.append({"case": cid, "role": role, "error": "missing rendered map", "path": str(path)})
                    continue
                image = source.extract_embedded_page_image(pdf, int(declaration["pdf"][role + "_page"]))
                left, top, right, bottom = source.detect_grid_bbox(np.asarray(image.convert("L")))
                original = np.asarray(image.crop((left, top, right + 1, bottom + 1)).convert("L"))
                with Image.open(path) as im:
                    rendered = np.asarray(im.convert("L"))
                map_records.append({"case": cid, "role": role, "path": str(path.resolve()),
                                    "sha256": source.sha256(path), "source_crop": [left, top, right, bottom]})
                if original.shape != rendered.shape:
                    failures.append({"case": cid, "role": role, "error": "crop dimensions differ",
                                     "source_shape": list(original.shape), "output_shape": list(rendered.shape)})
                    continue
                exclusions = verified_label_erasures(case, original)
                page_erasures.append({"case": cid, "role": role, "footprints": exclusions})
                erasure_boxes = [tuple(item["erasure_bbox"]) for item in exclusions]
                height, width = original.shape
                cw, ch = width / cols, height / rows
                checked, altered = 0, 0
                for obj in case["objects"]:
                    col, row = coordinate(obj["cell"])
                    bounds = (round((col + .25) * cw), round((row + .25) * ch),
                              round((col + .75) * cw), round((row + .75) * ch))
                    marker = ((col + .73) * cw, (row + .27) * ch, cw, ch) if role == "solution" and obj["cell"] in occupied else None
                    result = compare_core(original, rendered, bounds, marker, erasure_boxes)
                    record = {"case": cid, "role": role, "cell": obj["cell"], "object_type": obj["type"], **result}
                    checks.append(record)
                    checked += 1
                    if result["missing_dark_pixels"]:
                        failures.append(record)
                        altered += 1
                print(f"{cid} {role}: {checked} object cores checked; {altered} with lost protected ink", flush=True)
    report = {"status": "PASS" if not failures else "FAIL", "source_pdf_sha256": actual_hash,
              "runtime_sha256": source.sha256(args.runtime), "map_directory": str(args.maps.resolve()),
              "policy": {"core_fraction": .5, "source_dark_threshold": 145,
                         "comparison": "every protected source dark pixel remains dark (<145); tonal changes are recorded",
                         "source_label_exclusions": "actual detected/explicit source pills plus the renderer's 4-pixel erasure padding; never layout anchors",
                         "solution_exclusion": "occupied-cell marker circle center (.73,.27), radius .25 cell"},
              "object_core_count": len(checks), "protected_dark_pixels": sum(c["protected_dark_pixels"] for c in checks),
              "failures": failures, "checks": checks, "maps": map_records, "source_label_erasures": page_erasures,
              "limitations": "Protects object cores outside recorded source-label and marker footprints, not complete object outlines, source-label footprints, walls or visual readability."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {len(checks)} object cores; {len(failures)} failures; report {args.report}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
