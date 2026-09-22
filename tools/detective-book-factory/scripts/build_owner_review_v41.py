#!/usr/bin/env python3
"""Build HMDA Book 1 V4.1 from the locked V4 composition plus bounded polish.

This wrapper deliberately preserves V4 story, puzzle logic, spatial geometry,
reader premise and pagination.  It only integrates the deterministic V4.1
external visual assets into the two surfaces for which they were created:
Case 03's fair-play photo comparison and the Book 2 archival hook.

English is NOT frozen by this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

import yaml

import build_owner_review_v4 as v4
import generate_v41_visual_assets as v41_assets

ROOT = v4.ROOT
rb = v4.rb
ASSET_DIR = ROOT / "cache" / "v41_visual_assets"


def _prepare_assets() -> dict:
    """Generate and validate the deterministic V4.1 visual packet."""
    manifest = v41_assets.generate(ASSET_DIR)
    if manifest.get("version") != "v4.1":
        raise ValueError("V4.1 visual manifest version mismatch")
    if manifest.get("english_frozen") is not False:
        raise ValueError("V4.1 visual generation must never freeze English")

    expected = {
        "case03_photo_A.png",
        "case03_photo_B.png",
        "book2_archive_photo.png",
    }
    present = set(manifest.get("assets", {}))
    if present != expected:
        raise ValueError(f"V4.1 visual packet mismatch: expected {sorted(expected)}, got {sorted(present)}")

    case03 = manifest.get("case03_controlled_differences", {})
    if case03.get("uncontrolled_pixel_deltas_allowed") is not False:
        raise ValueError("Case 03 uncontrolled pixel deltas are forbidden")
    if case03.get("material") != [
        "parcel knot position",
        "evidence tag 0417 -> 0471",
        "muddy footprint direction toward the door",
    ]:
        raise ValueError("Case 03 material-difference contract changed")

    for name, expected_sha in manifest["assets"].items():
        path = ASSET_DIR / name
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise ValueError(f"V4.1 asset hash mismatch for {name}")
    return manifest


def case03_photo_page(c, data, mission, page, progress):
    """Render the deterministic photo pair without changing Case 03 logic."""
    rb.top_bar(c, "VISUAL EVIDENCE // PHOTO PAIR", page, progress)
    y = rb.PAGE_H - 64
    rb.para(c, "SAME TABLE. ONE MINUTE APART.", rb.M, y, rb.PAGE_W - 2 * rb.M, 38,
            size=19, font=rb.BOLD)
    y -= 52
    rule = mission.get("visual", {}).get(
        "relevance_rule",
        "A useful change affects the parcel, its tag, or its recorded route.",
    )
    rb.para(c, html.escape(rule), rb.M, y, rb.PAGE_W - 2 * rb.M, 42,
            size=11, font=rb.BOLD)
    y -= 55

    gap = 14
    panel_w = (rb.PAGE_W - 2 * rb.M - gap) / 2
    panel_h = 315
    for idx, label in enumerate(("A", "B")):
        x = rb.M + idx * (panel_w + gap)
        rb.box(c, x, y - panel_h, panel_w, panel_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=8)
        rb.label(c, f"PHOTO {label} // 15:{42 + idx:02d}", x + 10, y - 18, size=9.5)
        image = ASSET_DIR / f"case03_photo_{label}.png"
        rb.draw_image_fit(c, image, x + 10, y - 262, panel_w - 20, 224)
        rb.label(c, "EVIDENCE PHOTO // SAME CAMERA POSITION", x + 10, y - 282, size=8.4)
        rb.para(c, "Three evidence changes + three harmless decoys.",
                x + 10, y - 292, panel_w - 20, 20, size=8.8, align=1)

    y -= panel_h + 18
    rb.writing_card(c, "CIRCLE THE 3 CHANGES THAT ALTER THE EVIDENCE",
                    rb.M, y, rb.PAGE_W - 2 * rb.M, 72)
    v4.compact_signal_bar(c, mission)
    rb.footer(c, page)
    c.showPage()


def book2_scene_page(c, data, page):
    """Use the deterministic archival photograph in the existing V4 scene."""
    scene = data.get("book2_scene", {})
    rb.top_bar(c, "NEW FILE // AFTER CERTIFICATION", page, 1.0)
    y = rb.PAGE_H - 62
    rb.para(c, scene.get("heading", "CASE 001 // STILL OPEN"), rb.M, y,
            rb.PAGE_W - 2 * rb.M, 40, size=21, font=rb.BOLD)
    y -= 55

    folder_x = rb.M + 30
    folder_w = rb.PAGE_W - 2 * rb.M - 60
    rb.box(c, folder_x, y - 305, folder_w, 285,
           fill=rb.WHITE, stroke=rb.BLACK, radius=5, sw=1.4)
    rb.label(c, "ARCHIVE RELEASE // CASE 001", folder_x + 16, y - 47, size=10)

    photo = ASSET_DIR / "book2_archive_photo.png"
    rb.draw_image_fit(c, photo, folder_x + 22, y - 257, folder_w - 44, 190)
    rb.label(c, "ARCHIVE GROUP PHOTO // CENTRAL FIGURE PHYSICALLY REMOVED",
             folder_x + 22, y - 272, size=8.5)

    rb.box(c, folder_x + 68, y - 294, folder_w - 136, 38,
           fill=rb.BLACK, stroke=rb.BLACK, radius=2)
    rb.para(c, "RETURN BEFORE THE FIRST MEETING", folder_x + 76, y - 270,
            folder_w - 152, 24, size=11, font=rb.BOLD,
            color=rb.WHITE, align=1)

    y -= 330
    for beat in scene.get("beats", [])[:5]:
        h = rb.text_height(str(beat), rb.PAGE_W - 2 * rb.M - 24, 9.5)
        rb.para(c, "• " + html.escape(str(beat)), rb.M + 12, y,
                rb.PAGE_W - 2 * rb.M - 24, h + 1, size=9.5)
        y -= h + 5

    chat = scene.get("chat", [])
    if chat:
        rb.label(c, "HAPPY MAKERS CHAT", rb.M, y - 2, size=9.5)
        y -= 15
        for item in chat[:4]:
            text = f"<b>{data['characters'][item['speaker']]['name']}:</b> {html.escape(item['text'])}"
            h = rb.text_height(text, rb.PAGE_W - 2 * rb.M, 9.5)
            rb.para(c, text, rb.M, y, rb.PAGE_W - 2 * rb.M, h + 1, size=9.5)
            y -= h + 3

    rb.box(c, rb.M, 55, rb.PAGE_W - 2 * rb.M, 44,
           fill=rb.BLACK, stroke=rb.BLACK, radius=8)
    rb.para(c, scene.get("final_line", "NEXT FILE INCOMING."), rb.M + 12, 84,
            rb.PAGE_W - 2 * rb.M - 24, 22, size=12, font=rb.BOLD,
            color=rb.WHITE, align=1)
    rb.footer(c, page)
    c.showPage()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--maps", required=True, type=Path)
    parser.add_argument("--overrides", default=ROOT / "content/book1_v4_overrides.yml", type=Path)
    parser.add_argument("--aliases", default=ROOT / "content/spatial_character_aliases.yml", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = _prepare_assets()
    data, cases, _v4_master, runtime = v4.build_data(
        args.master.resolve(),
        args.runtime.resolve(),
        args.maps.resolve(),
        args.overrides.resolve(),
        args.aliases.resolve(),
        args.output.resolve(),
    )

    data.setdefault("production_state", {})["owner_review_revision"] = "4.1"
    data["production_state"]["v41_visual_manifest"] = "cache/v41_visual_assets/manifest.json"
    data["production_state"]["english_frozen"] = False
    v41_master = args.output.resolve().parent / "book1_en_master_owner_review_v41.yml"
    v41_master.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )

    # render_v4 resolves these module globals at runtime, so bounded patching
    # replaces only the two V4 surfaces approved for V4.1 asset integration.
    original_case03 = v4.case03_photo_page
    original_book2 = v4.book2_scene_page
    v4.case03_photo_page = case03_photo_page
    v4.book2_scene_page = book2_scene_page
    try:
        pages, _index = v4.render_v4(data, cases, v41_master, args.output.resolve())
    finally:
        v4.case03_photo_page = original_case03
        v4.book2_scene_page = original_book2

    v4_index = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v4_page_index.json"
    v41_index = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v41_page_index.json"
    if v4_index.is_file():
        shutil.copyfile(v4_index, v41_index)

    sha = hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    packet = {
        "revision": "v4.1",
        "pages": pages,
        "pdf_sha256": sha,
        "visual_manifest": manifest,
        "english_frozen": False,
    }
    packet_path = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v41_manifest.json"
    packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"PASS: V4.1 bounded owner review rendered, {pages} pages")
    print(f"MASTER: {v41_master}")
    print(f"RUNTIME: {runtime}")
    print(f"PDF: {args.output.resolve()}")
    print(f"SHA256: {sha}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
