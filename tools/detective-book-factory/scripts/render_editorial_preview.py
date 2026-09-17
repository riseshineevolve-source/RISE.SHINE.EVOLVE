#!/usr/bin/env python3
"""Render the HMDA editorial preview without pretending pending map art exists.

The Book 1 branch is intentionally between two spatial-map systems: the old
prototype raster assets are no longer the source of truth, while final RSE
maps are still being rebuilt from the locked Shigai source bank. The regular
renderer already knows how to display an explicit ASSET MISSING placeholder,
but its crop preprocessor used to fail before reaching that fallback.

This wrapper is for CI/editorial preview only. It leaves the production
renderer strict, records every missing spatial raster in a status report, and
lets the rest of the book build so pagination/editorial regressions remain
visible while final map work proceeds.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

import render_book as rb


STRICT_PREPROCESS = rb.preprocess_crop


def editorial_preprocess_crop(src: Path, crop, dst: Path) -> None:
    """Use the normal crop path when art exists; otherwise keep an explicit
    missing-asset placeholder instead of crashing the whole editorial build."""
    if src.exists():
        STRICT_PREPROCESS(src, crop, dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    print(f"EDITORIAL PREVIEW: pending spatial asset -> {src}")


def spatial_asset_report(content_path: Path) -> list[str]:
    data = yaml.safe_load(content_path.read_text(encoding="utf-8"))
    tool_root = content_path.parent.parent
    lines = [
        "HMDA EDITORIAL PREVIEW - SPATIAL ASSET STATUS",
        "Final spatial maps are a separate production gate.",
        "Missing entries below are rendered as explicit placeholders and are NOT release-ready.",
        "",
    ]
    missing: list[str] = []
    for mission in data.get("missions", []):
        if mission.get("type") != "spatial":
            continue
        spatial = mission["spatial"]
        for label, key in (("puzzle", "source_page_asset"), ("solution", "solution_asset")):
            rel = spatial.get(key)
            if not rel:
                missing.append(f"CASE {mission['number']:02d} {label}: NO PATH DECLARED")
                continue
            path = tool_root / rel
            state = "PRESENT" if path.exists() else "PENDING FINAL MAP REPLACEMENT"
            lines.append(f"CASE {mission['number']:02d} {label}: {rel} -> {state}")
            if not path.exists():
                missing.append(f"CASE {mission['number']:02d} {label}: {rel}")
    lines.extend(["", f"Pending spatial raster count: {len(missing)}"])
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="content/book1_en_production.yml")
    parser.add_argument("--output", default="dist/HMDA_Book1_Editorial_Preview.pdf")
    parser.add_argument("--status-report", default="dist/spatial_asset_status.txt")
    args = parser.parse_args()

    content = Path(args.content).resolve()
    output = Path(args.output).resolve()
    report = Path(args.status_report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(spatial_asset_report(content)) + "\n", encoding="utf-8")

    rb.preprocess_crop = editorial_preprocess_crop
    pages = rb.render(content, output)
    print(f"Built editorial preview {output} ({pages} pages)")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
