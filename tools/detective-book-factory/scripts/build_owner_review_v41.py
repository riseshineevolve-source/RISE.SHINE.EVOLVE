#!/usr/bin/env python3
"""Build HMDA Book 1 V4.1 from the locked V4 composition plus bounded polish.

This wrapper deliberately preserves V4 story, puzzle logic, spatial geometry,
reader premise and pagination. Owner-gated Case 03 / Book 2 art is NEVER
generated or silently selected by this builder: it can be integrated only from
an explicit owner-locked visual manifest. All asset-independent V4.1 polish
continues normally while that gate is pending.

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

ROOT = v4.ROOT
rb = v4.rb
ACTIVE_ASSET_DIR: Path | None = None
EXPECTED_OWNER_ASSETS = {
    "case03_photo_A.png",
    "case03_photo_B.png",
    "book2_archive_photo.png",
}
OWNER_CASE03_SPEC_STATUS = "OWNER_APPROVED_EXACT_10_DIFFERENCE_CONTRACT"


# Thirty deterministic field-note lines guarantee that whichever spatial cases
# require parity correction receive case-specific rather than cloned filler copy.
# Only 11 are currently emitted by the locked V4 page plan.
INTERLUDE_QUIPS = (
    "A clue can look important and still be decorative. Rude, but legal.",
    "If the board looks too neat, the mystery is probably hiding under the neat part.",
    "Tiny detail, giant consequence. Detective work has terrible scale settings.",
    "Do not argue with the evidence. It has more free time than you do.",
    "Circle what changed, not what merely became dramatic.",
    "A confident guess is still a guess wearing a very nice coat.",
    "If two facts disagree, congratulations: the case just became interesting.",
    "The obvious clue would like applause. Make it earn some first.",
    "Write the weird thing down. Weird things hate being documented.",
    "A witness can be mistaken without being mysterious. Check the grid.",
    "If your theory needs seven excuses, it may actually be seven excuses.",
    "Keep one box for questions. Questions are evidence with unfinished paperwork.",
    "The loudest detail is not automatically the useful one. Classic loud-detail behavior.",
    "Before crossing anything out, make sure the rule actually crossed it out for you.",
    "When the pattern clicks, verify it once more. Victory laps come after checking.",
    "A good detective leaves room for the fact that future-them may be smarter.",
    "If a clue feels too convenient, inspect the inconvenient clue beside it.",
    "Facts first, theory second. Snacks may occur at any stage.",
    "A blank space on the board is not failure. It is reserved parking for a better idea.",
    "The case does not care how elegant your theory is. Very inconsiderate of it.",
    "One clean contradiction can beat a whole paragraph of vibes.",
    "If you cannot explain why, mark it as a hunch and keep moving.",
    "The map is allowed to be boring. Boring maps catch surprisingly exciting mistakes.",
    "Treat every arrow like it has to testify under oath.",
    "A clue that survives three checks has earned a place on the wall.",
    "Do not promote a coincidence to evidence without an interview first.",
    "The best next move is usually smaller than the dramatic one.",
    "If the answer appears instantly, test the route that got you there.",
    "A messy board can still hold a clean thought. Label the clean thought.",
    "Last case rule: confidence is useful; verification is better.",
)


def _load_owner_visual_packet(manifest_path: Path | None) -> dict:
    """Validate owner-gated visual slots without generating or choosing art.

    No manifest means the visual gate is intentionally pending. When a manifest
    is supplied, it must explicitly attest that the owner approved the exact
    ten-difference Case 03 contract and the Book 2 archival hook, and every
    referenced asset must match its locked SHA-256.
    """
    if manifest_path is None:
        return {
            "status": "OWNER_GATE_PENDING",
            "owner_locked": False,
            "integrated": False,
            "case03_difference_count_required": 10,
            "case03_spec_status_required": OWNER_CASE03_SPEC_STATUS,
            "assets": {},
        }

    if not manifest_path.is_file():
        raise FileNotFoundError(f"Owner visual manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Owner visual manifest must be a JSON object")
    if manifest.get("owner_locked") is not True:
        raise ValueError("Owner visual manifest is not owner-locked")
    if manifest.get("case03_difference_count") != 10:
        raise ValueError("Case 03 owner visual contract must contain exactly 10 differences")
    if manifest.get("case03_spec_status") != OWNER_CASE03_SPEC_STATUS:
        raise ValueError("Case 03 exact 10-difference specification is not owner-approved")
    if manifest.get("book2_visual_owner_locked") is not True:
        raise ValueError("Book 2 archival-hook visual is not owner-locked")

    assets = manifest.get("assets", {})
    if set(assets) != EXPECTED_OWNER_ASSETS:
        raise ValueError(
            f"Owner visual packet mismatch: expected {sorted(EXPECTED_OWNER_ASSETS)}, "
            f"got {sorted(assets)}"
        )
    asset_dir = manifest_path.parent
    for name, expected_sha in assets.items():
        path = asset_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Owner visual asset missing: {path}")
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise ValueError(f"Owner visual asset hash mismatch for {name}")

    result = dict(manifest)
    result["status"] = "OWNER_LOCKED_ASSETS_VALIDATED"
    result["integrated"] = True
    result["manifest_path"] = str(manifest_path)
    return result


def _owner_asset(name: str) -> Path:
    if ACTIVE_ASSET_DIR is None:
        raise RuntimeError("Owner-gated visual asset requested while visual gate is pending")
    if name not in EXPECTED_OWNER_ASSETS:
        raise ValueError(f"Unsupported owner visual asset: {name}")
    return ACTIVE_ASSET_DIR / name


def _interlude_note(data: dict, case_number: int) -> tuple[str, str]:
    """Return a deterministic Happy Makers voice + unique case-wall note."""
    if not 1 <= case_number <= len(INTERLUDE_QUIPS):
        raise ValueError(f"Unsupported V4.1 interlude case number: {case_number}")
    speaker_keys = ("mimi", "luli", "dilo", "alio", "nini")
    key = speaker_keys[(case_number - 1) % len(speaker_keys)]
    speaker = data.get("characters", {}).get(key, {}).get("name", key.upper())
    return speaker, INTERLUDE_QUIPS[case_number - 1]


def parity_pause_v41(c, data, mission, page):
    """Replace cloned parity filler with a usable, case-specific Case Wall.

    Pagination and case order remain untouched. The page exists only where V4
    already inserted a parity page before a spatial spread.
    """
    n = int(mission["number"])
    speaker, quip = _interlude_note(data, n)
    rb.top_bar(c, "CASE WALL // FIELD INTERLUDE", page)
    y = rb.PAGE_H - 64
    rb.para(c, f"CASE {n:02d} // CLEAR THE BOARD BEFORE THE MAP",
            rb.M, y, rb.PAGE_W - 2 * rb.M, 44, size=21, font=rb.BOLD)
    y -= 58
    rb.para(
        c,
        "Use this wall before the facing Witness Board + Live Case Map. "
        "Write only what the current file gives you; do not solve ahead.",
        rb.M, y, rb.PAGE_W - 2 * rb.M, 46, size=10.8,
    )
    y -= 58

    gap = 12
    panel_w = (rb.PAGE_W - 2 * rb.M - 2 * gap) / 3
    labels = (
        ("FACTS", "What is directly stated or visibly verified?"),
        ("SIGNALS", "What may matter, repeat, shift, or connect?"),
        ("QUESTIONS", "What still needs testing on the map?"),
    )
    panel_h = 330
    for idx, (label, prompt) in enumerate(labels):
        x = rb.M + idx * (panel_w + gap)
        rb.box(c, x, y - panel_h, panel_w, panel_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.1)
        rb.label(c, label, x + 12, y - 23, size=10)
        rb.para(c, prompt, x + 12, y - 42, panel_w - 24, 48,
                size=9.2, font=rb.BOLD)
        line_y = y - 108
        c.setStrokeColor(rb.LINE)
        c.setLineWidth(0.7)
        for _ in range(6):
            c.line(x + 12, line_y, x + panel_w - 12, line_y)
            line_y -= 32

    y -= panel_h + 18
    rb.box(c, rb.M, y - 92, rb.PAGE_W - 2 * rb.M, 92,
           fill=rb.BLACK, stroke=rb.BLACK, radius=9)
    rb.label(c, f"FIELD NOTE // {speaker}", rb.M + 14, y - 24,
             size=9.5, color=rb.WHITE)
    rb.para(c, html.escape(quip), rb.M + 14, y - 46,
            rb.PAGE_W - 2 * rb.M - 28, 38, size=11.2,
            font=rb.BOLD, color=rb.WHITE)

    rb.label(c, f"NEXT // WITNESS BOARD + LIVE CASE MAP // CASE {n:02d}",
             rb.M, 62, size=9.5)
    rb.footer(c, page)
    c.showPage()


def case03_photo_page(c, data, mission, page, progress):
    """Render only an explicitly owner-locked Case 03 photo pair."""
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
        image = _owner_asset(f"case03_photo_{label}.png")
        rb.draw_image_fit(c, image, x + 10, y - 262, panel_w - 20, 224)
        rb.label(c, "EVIDENCE PHOTO // SAME CAMERA POSITION", x + 10, y - 282, size=8.4)
        rb.para(c, "Find the 10 approved differences. Decide which ones change the evidence.",
                x + 10, y - 292, panel_w - 20, 20, size=8.8, align=1)

    y -= panel_h + 18
    rb.writing_card(c, "MARK THE DIFFERENCES THAT ALTER THE EVIDENCE",
                    rb.M, y, rb.PAGE_W - 2 * rb.M, 72)
    v4.compact_signal_bar(c, mission)
    rb.footer(c, page)
    c.showPage()


def book2_scene_page(c, data, page):
    """Render only an explicitly owner-locked Book 2 archival photograph."""
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

    photo = _owner_asset("book2_archive_photo.png")
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
    global ACTIVE_ASSET_DIR

    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--maps", required=True, type=Path)
    parser.add_argument("--overrides", default=ROOT / "content/book1_v4_overrides.yml", type=Path)
    parser.add_argument("--aliases", default=ROOT / "content/spatial_character_aliases.yml", type=Path)
    parser.add_argument("--owner-visual-manifest", type=Path,
                        help="Optional explicit owner-locked Case 03 + Book 2 asset manifest. "
                             "Without it, V4 baseline visuals remain and the owner visual gate stays pending.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    visual_manifest_path = args.owner_visual_manifest.resolve() if args.owner_visual_manifest else None
    manifest = _load_owner_visual_packet(visual_manifest_path)
    visuals_integrated = manifest.get("integrated") is True
    if visuals_integrated and visual_manifest_path is not None:
        ACTIVE_ASSET_DIR = visual_manifest_path.parent

    data, cases, _v4_master, runtime = v4.build_data(
        args.master.resolve(),
        args.runtime.resolve(),
        args.maps.resolve(),
        args.overrides.resolve(),
        args.aliases.resolve(),
        args.output.resolve(),
    )

    data.setdefault("production_state", {})["owner_review_revision"] = "4.1"
    data["production_state"]["english_frozen"] = False
    data["production_state"]["v41_owner_visual_gate"] = (
        "OWNER_LOCKED_ASSETS_INTEGRATED" if visuals_integrated
        else "PENDING_CASE03_EXACT_10_DIFFERENCE_AND_BOOK2_ART"
    )
    if visual_manifest_path is not None:
        data["production_state"]["v41_visual_manifest"] = str(visual_manifest_path)
    v41_master = args.output.resolve().parent / "book1_en_master_owner_review_v41.yml"
    v41_master.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )

    # render_v4 resolves these module globals at runtime. Asset-independent V4.1
    # polish is always applied; owner-gated visual surfaces are patched only when
    # an explicit owner-locked manifest passes the gate above.
    original_case03 = v4.case03_photo_page
    original_book2 = v4.book2_scene_page
    original_parity = v4.parity_pause
    if visuals_integrated:
        v4.case03_photo_page = case03_photo_page
        v4.book2_scene_page = book2_scene_page
    v4.parity_pause = parity_pause_v41
    try:
        pages, _index = v4.render_v4(data, cases, v41_master, args.output.resolve())
    finally:
        v4.case03_photo_page = original_case03
        v4.book2_scene_page = original_book2
        v4.parity_pause = original_parity
        ACTIVE_ASSET_DIR = None

    v4_index = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v4_page_index.json"
    v41_index = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v41_page_index.json"
    if v4_index.is_file():
        shutil.copyfile(v4_index, v41_index)

    sha = hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    packet = {
        "revision": "v4.1",
        "pages": pages,
        "pdf_sha256": sha,
        "owner_visual_gate": manifest,
        "premium_polish": {
            "parity_interludes": "unique case-specific Case Wall pages",
            "owner_gated_visuals_integrated": visuals_integrated,
            "logic_changed": False,
            "pagination_changed": False,
        },
        "english_frozen": False,
    }
    packet_path = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v41_manifest.json"
    packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"PASS: V4.1 bounded owner review rendered, {pages} pages")
    print(f"MASTER: {v41_master}")
    print(f"RUNTIME: {runtime}")
    print(f"PDF: {args.output.resolve()}")
    print(f"SHA256: {sha}")
    print(f"Owner visuals integrated: {str(visuals_integrated).lower()}")
    print("English frozen: false")


if __name__ == "__main__":
    main()
