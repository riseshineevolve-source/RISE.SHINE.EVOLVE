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

INTERLUDE_FAMILIES = (
    "TRIAGE_COLUMNS",
    "EVIDENCE_RAIL",
    "CASE_STRIPS",
    "CROSSCHECK_GRID",
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


def _interlude_family(case_number: int, page: int) -> str:
    """Choose a stable visual family without introducing render-order state."""
    return INTERLUDE_FAMILIES[(case_number * 7 + page * 3) % len(INTERLUDE_FAMILIES)]


def _writing_lines(c, x: float, top: float, w: float, count: int, step: float) -> None:
    c.setStrokeColor(rb.LINE)
    c.setLineWidth(0.7)
    y = top
    for _ in range(count):
        c.line(x, y, x + w, y)
        y -= step


def _interlude_columns(c, top: float, total_w: float) -> None:
    gap = 12
    panel_w = (total_w - 2 * gap) / 3
    panel_h = 330
    labels = (
        ("FACTS", "What is directly stated or visibly verified?"),
        ("SIGNALS", "What may matter, repeat, shift, or connect?"),
        ("QUESTIONS", "What still needs testing on the map?"),
    )
    for idx, (label, prompt) in enumerate(labels):
        x = rb.M + idx * (panel_w + gap)
        rb.box(c, x, top - panel_h, panel_w, panel_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.1)
        rb.label(c, label, x + 12, top - 23, size=10)
        rb.para(c, prompt, x + 12, top - 42, panel_w - 24, 48,
                size=9.2, font=rb.BOLD)
        _writing_lines(c, x + 12, top - 108, panel_w - 24, 6, 32)


def _interlude_rail(c, top: float, total_w: float, case_number: int) -> None:
    h = 330
    rail_w = 92
    gap = 12
    rb.box(c, rb.M, top - h, rail_w, h,
           fill=rb.BLACK, stroke=rb.BLACK, radius=10, sw=1.0)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.BOLD, 28)
    c.drawCentredString(rb.M + rail_w / 2, top - 58, f"{case_number:02d}")
    rb.label(c, "PIN", rb.M + 20, top - 88, size=9.2, color=rb.WHITE)
    rb.label(c, "BEFORE", rb.M + 20, top - 108, size=9.2, color=rb.WHITE)
    rb.label(c, "THE MAP", rb.M + 20, top - 128, size=9.2, color=rb.WHITE)
    rb.para(c, "FACTS → SIGNALS → QUESTIONS",
            rb.M + 13, top - 178, rail_w - 26, 88,
            size=9.4, font=rb.BOLD, color=rb.WHITE, align=1)

    x = rb.M + rail_w + gap
    w = total_w - rail_w - gap
    labels = (
        ("FACTS", "Pin only what the file actually proves."),
        ("SIGNALS", "Mark a repeat, shift, contradiction, or link."),
        ("QUESTIONS", "Write the one thing the map still has to test."),
    )
    gap_y = 8
    box_h = (h - 2 * gap_y) / 3
    for idx, (label, prompt) in enumerate(labels):
        box_top = top - idx * (box_h + gap_y)
        rb.box(c, x, box_top - box_h, w, box_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=8, sw=1.0)
        rb.label(c, label, x + 12, box_top - 22, size=9.8)
        rb.para(c, prompt, x + 12, box_top - 40, w - 24, 34,
                size=9.2, font=rb.BOLD)
        _writing_lines(c, x + 12, box_top - 77, w - 24, 2, 24)


def _interlude_strips(c, top: float, total_w: float) -> None:
    labels = (
        ("FACTS", "What survives if every guess is removed?"),
        ("SIGNALS", "What deserves a pin before you open the map?"),
        ("QUESTIONS", "What must the map answer before you commit?"),
    )
    h = 98
    gap = 12
    label_w = 112
    for idx, (label, prompt) in enumerate(labels):
        box_top = top - idx * (h + gap)
        rb.box(c, rb.M, box_top - h, total_w, h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.1)
        rb.box(c, rb.M, box_top - h, label_w, h,
               fill=rb.BLACK, stroke=rb.BLACK, radius=9, sw=1.0)
        rb.label(c, label, rb.M + 16, box_top - 32, size=10.2, color=rb.WHITE)
        rb.para(c, prompt, rb.M + label_w + 14, box_top - 18,
                total_w - label_w - 28, 34, size=9.3, font=rb.BOLD)
        _writing_lines(c, rb.M + label_w + 14, box_top - 61,
                       total_w - label_w - 28, 2, 20)


def _interlude_grid(c, top: float, total_w: float) -> None:
    gap = 12
    half = (total_w - gap) / 2
    upper_h = 148
    lower_h = 168
    upper = (
        ("FACTS", "What is certain enough to pin?"),
        ("SIGNALS", "What may connect to an older file?"),
    )
    for idx, (label, prompt) in enumerate(upper):
        x = rb.M + idx * (half + gap)
        rb.box(c, x, top - upper_h, half, upper_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.1)
        rb.label(c, label, x + 12, top - 22, size=9.8)
        rb.para(c, prompt, x + 12, top - 40, half - 24, 34,
                size=9.2, font=rb.BOLD)
        _writing_lines(c, x + 12, top - 82, half - 24, 3, 22)

    lower_top = top - upper_h - gap
    rb.box(c, rb.M, lower_top - lower_h, total_w, lower_h,
           fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.1)
    rb.label(c, "QUESTIONS // CROSS-CHECK", rb.M + 12, lower_top - 22, size=9.8)
    rb.para(c, "Write the test that could prove your favorite theory wrong.",
            rb.M + 12, lower_top - 40, total_w - 24, 34,
            size=9.2, font=rb.BOLD)
    _writing_lines(c, rb.M + 12, lower_top - 82, total_w - 24, 4, 22)


def parity_pause_v41(c, data, mission, page):
    """Render a case-specific field interlude through deterministic visual families.

    Pagination and case order remain untouched. The page exists only where V4
    already inserted a parity page before a spatial spread.
    """
    n = int(mission["number"])
    speaker, quip = _interlude_note(data, n)
    family = _interlude_family(n, page)
    rb.top_bar(c, f"CASE WALL // {family.replace('_', ' ')}", page)
    y = rb.PAGE_H - 64
    rb.para(c, f"CASE {n:02d} // CLEAR THE BOARD BEFORE THE MAP",
            rb.M, y, rb.PAGE_W - 2 * rb.M, 44, size=21, font=rb.BOLD)
    y -= 42
    title = str(mission.get("title", f"CASE {n:02d}"))
    rb.label(c, f"CURRENT FILE // {title[:68].upper()}", rb.M, y, size=9.2)
    y -= 18
    rb.para(
        c,
        "Use this wall before the facing Witness Board + Live Case Map. "
        "Write only what the current file gives you; do not solve ahead.",
        rb.M, y, rb.PAGE_W - 2 * rb.M, 42, size=10.6,
    )
    y -= 52

    total_w = rb.PAGE_W - 2 * rb.M
    if family == "TRIAGE_COLUMNS":
        _interlude_columns(c, y, total_w)
    elif family == "EVIDENCE_RAIL":
        _interlude_rail(c, y, total_w, n)
    elif family == "CASE_STRIPS":
        _interlude_strips(c, y, total_w)
    elif family == "CROSSCHECK_GRID":
        _interlude_grid(c, y, total_w)
    else:
        raise ValueError(f"Unknown interlude family: {family}")

    note_top = y - 348
    rb.box(c, rb.M, note_top - 88, total_w, 88,
           fill=rb.BLACK, stroke=rb.BLACK, radius=9)
    rb.label(c, f"FIELD NOTE // {speaker}", rb.M + 14, note_top - 23,
             size=9.5, color=rb.WHITE)
    rb.para(c, html.escape(quip), rb.M + 14, note_top - 44,
            total_w - 28, 36, size=11.0,
            font=rb.BOLD, color=rb.WHITE)

    rb.label(c, f"NEXT // WITNESS BOARD + LIVE CASE MAP // CASE {n:02d}",
             rb.M, 62, size=9.5)
    rb.footer(c, page)
    c.showPage()


def publication_page_v41(c, data, page):
    """Render publication data with no owner-review / proof-only leakage."""
    rb.top_bar(c, "PUBLICATION RECORD", page)
    y = rb.PAGE_H - 83
    rb.para(c, "HAPPY MAKERS DETECTIVE ACADEMY", rb.M, y,
            rb.PAGE_W - 2 * rb.M, 40, size=19, font=rb.BOLD)
    y -= 58
    pub = data.get("publication", {})
    copy = (
        f"{pub.get('copyright', '© 2026 Rise.Shine.Evolve. All rights reserved.')}<br/><br/>"
        f"{pub.get('isbn', 'ISBN Paperback: ______')}<br/><br/>"
        f"{pub.get('rights', 'No part of this publication may be reproduced, stored in a retrieval system, or transmitted in any form or by any means without prior written permission from the publisher, except for brief quotations used in reviews.')}<br/><br/>"
        f"{pub.get('ai_disclosure', 'The development of this book was supported by AI-assisted tools.')}<br/><br/>"
        f"{pub.get('website', 'Website: Rise.Shine.Evolve')}<br/>"
        f"{pub.get('facebook', 'Facebook: Rise.Shine.Evolve')}"
    )
    rb.text_card(c, copy, rb.M, y, rb.PAGE_W - 2 * rb.M,
                 heading="PUBLICATION RECORD", size=11.5,
                 fill=rb.WHITE, stroke=rb.BLACK)
    rb.footer(c, page)
    c.showPage()


def id_page_v41(c, data, page):
    """Keep one canonical Field Detective identity field plus signature.

    V4's source card already labels the identity line DETECTIVE NAME / CALL SIGN;
    rendering a second fallback CALL SIGN field duplicated the same identity.
    """
    card = data["opening"].get("id_card", {})
    rb.top_bar(c, "DETECTIVE SIX // FIELD DETECTIVE ID", page)
    y = rb.PAGE_H - 70
    rb.para(c, card.get("heading", "FIELD DETECTIVE ID"), rb.M, y,
            rb.PAGE_W - 2 * rb.M, 48, size=21, font=rb.BOLD)
    y -= 70
    rb.box(c, rb.M, y - 415, rb.PAGE_W - 2 * rb.M, 415,
           fill=rb.WHITE, stroke=rb.BLACK, radius=16, sw=1.6)
    rb.label(c, card.get("designation", "DETECTIVE SIX // RECRUIT"),
             rb.M + 18, y - 27, size=11)
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(4)
    c.circle(rb.PAGE_W - rb.M - 72, y - 67, 37, fill=0, stroke=1)
    c.setFillColor(rb.BLACK)
    c.setFont(rb.BOLD, 30)
    c.drawCentredString(rb.PAGE_W - rb.M - 72, y - 78, "06")

    fields = [card.get("name_label", "DETECTIVE NAME / CALL SIGN"), "SIGNATURE"]
    ty = y - 118
    for label in fields:
        rb.label(c, label, rb.M + 18, ty, size=9.5)
        c.setStrokeColor(rb.BLACK)
        c.setLineWidth(0.9)
        c.line(rb.M + 18, ty - 25, rb.PAGE_W - rb.M - 18, ty - 25)
        ty -= 92

    acceptance = card.get(
        "acceptance",
        "I accept the Academy rule: notice first, test the evidence, and explain my verdict.",
    )
    rb.para(c, html.escape(acceptance), rb.M + 18, ty,
            rb.PAGE_W - 2 * rb.M - 36, 52, size=11, font=rb.BOLD)
    rb.label(c, card.get("case_wall_label", "CASE WALL // FACTS, SIGNALS, QUESTIONS"),
             rb.M, y - 445, size=10)
    rb.writing_card(c, "FIRST CASE NOTES", rb.M, y - 465,
                    rb.PAGE_W - 2 * rb.M, 118)
    rb.para(c, card.get("footer", "Your name begins the file. Your evidence closes it."),
            rb.M, 62, rb.PAGE_W - 2 * rb.M, 28,
            size=10.5, font=rb.BOLD, align=1)
    rb.footer(c, page)
    c.showPage()


def nonspatial_solution_page_v41(c, mission, page):
    """Render the V4 solution without the internal spoiler-treatment note."""
    rb.top_bar(c, f"SOLUTION // CASE {mission['number']:02d}", page)
    w = rb.PAGE_W - 2 * rb.M
    y = rb.PAGE_H - 58
    rb.para(c, html.escape(mission["title"]), rb.M, y, w, 44,
            size=17, font=rb.BOLD)
    y -= 60
    answer = rb._solution_answer_text(mission) or mission.get(
        "verdict", mission.get("meta_reveal", "CHECK THE REASONING BELOW")
    )
    rb.box(c, rb.M, y - 76, w, 76,
           fill=rb.BLACK, stroke=rb.BLACK, radius=9)
    rb.label(c, "SPOILER // VERIFIED VERDICT", rb.M + 14, y - 20,
             size=9.5, color=rb.WHITE)
    rb.para(c, html.escape(str(answer)), rb.M + 14, y - 34,
            w - 28, 36, size=13, font=rb.BOLD, color=rb.WHITE)
    y -= 96
    rb.label(c, "HOW THE CASE FALLS INTO PLACE", rb.M, y, size=10)
    y -= 16
    steps = mission.get("solution_steps", [])
    if not steps:
        steps = [
            mission.get("objective", "Use the evidence to justify the verdict."),
            mission.get("meta_reveal", ""),
        ]
    for idx, step in enumerate([s for s in steps if str(s).strip()], 1):
        h = max(52, rb.text_height(str(step), w - 58, 11) + 18)
        if y - h < 105:
            raise ValueError(f"Case {mission['number']}: solution reasoning overflows")
        rb.box(c, rb.M, y - h, w, h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=7)
        rb.label(c, f"{idx:02d}", rb.M + 11, y - 21, size=9.5)
        rb.para(c, html.escape(str(step)), rb.M + 43, y - 10,
                w - 56, h - 14, size=11)
        y -= h + 6
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
    """Render the owner-locked Book 2 archival hook as a cinematic final beat."""
    scene = data.get("book2_scene", {})
    rb.top_bar(c, "NEW FILE // AFTER CERTIFICATION", page, 1.0)
    y = rb.PAGE_H - 62
    rb.para(c, scene.get("heading", "CASE 001 // STILL OPEN"), rb.M, y,
            rb.PAGE_W - 2 * rb.M, 40, size=21, font=rb.BOLD)
    y -= 52
    rb.label(c, "ARCHIVE WAKE // 00:01 AFTER CERTIFICATION", rb.M, y, size=9.3)
    y -= 18

    frame_x = rb.M + 18
    frame_w = rb.PAGE_W - 2 * rb.M - 36
    frame_h = 270
    rb.box(c, frame_x, y - frame_h, frame_w, frame_h,
           fill=rb.WHITE, stroke=rb.BLACK, radius=5, sw=1.5)
    rb.box(c, frame_x, y - 42, 96, 42,
           fill=rb.BLACK, stroke=rb.BLACK, radius=4)
    rb.label(c, "CASE 001", frame_x + 15, y - 26, size=10, color=rb.WHITE)
    rb.label(c, "ARCHIVE RELEASE // IMAGE RECOVERED", frame_x + 112, y - 27, size=9.3)

    photo = _owner_asset("book2_archive_photo.png")
    rb.draw_image_fit(c, photo, frame_x + 18, y - 230, frame_w - 36, 174)
    rb.label(c, "GROUP PHOTO // CENTRAL FIGURE PHYSICALLY REMOVED",
             frame_x + 18, y - 247, size=8.5)

    rb.box(c, frame_x + 72, y - 264, frame_w - 144, 34,
           fill=rb.BLACK, stroke=rb.BLACK, radius=2)
    rb.para(c, "RETURN BEFORE THE FIRST MEETING", frame_x + 80, y - 242,
            frame_w - 160, 22, size=10.8, font=rb.BOLD,
            color=rb.WHITE, align=1)

    y -= frame_h + 14
    beats = [str(item) for item in scene.get("beats", []) if str(item).strip()]
    groups = (beats[:2], beats[2:4], beats[4:])
    gap = 10
    card_w = (rb.PAGE_W - 2 * rb.M - 2 * gap) / 3
    card_h = 82
    for idx, group in enumerate(groups, 1):
        x = rb.M + (idx - 1) * (card_w + gap)
        rb.box(c, x, y - card_h, card_w, card_h,
               fill=rb.WHITE, stroke=rb.BLACK, radius=7, sw=1.0)
        rb.label(c, f"CUT {idx:02d}", x + 10, y - 19, size=8.8)
        text = " ".join(group) if group else "The file waits in silence."
        rb.para(c, html.escape(text), x + 10, y - 34,
                card_w - 20, 43, size=8.8, font=rb.BOLD)

    y -= card_h + 12
    chat = scene.get("chat", [])
    rb.box(c, rb.M, y - 118, rb.PAGE_W - 2 * rb.M, 118,
           fill=rb.BLACK, stroke=rb.BLACK, radius=8)
    rb.label(c, "VOICE TRACK // HAPPY MAKERS", rb.M + 14, y - 22,
             size=9.2, color=rb.WHITE)
    chat_y = y - 42
    if chat:
        for item in chat[:4]:
            speaker = data["characters"][item["speaker"]]["name"]
            text = f"<b>{html.escape(speaker)}:</b> {html.escape(item['text'])}"
            h = rb.text_height(text, rb.PAGE_W - 2 * rb.M - 28, 8.9)
            rb.para(c, text, rb.M + 14, chat_y,
                    rb.PAGE_W - 2 * rb.M - 28, h + 1,
                    size=8.9, color=rb.WHITE)
            chat_y -= h + 2
    else:
        rb.para(c, "No one speaks. The missing center of the photograph says enough.",
                rb.M + 14, chat_y, rb.PAGE_W - 2 * rb.M - 28, 38,
                size=9.1, font=rb.BOLD, color=rb.WHITE)

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
    data["production_state"]["v41_reader_surface_cleanup"] = {
        "publication_internal_copy_removed": True,
        "field_detective_id_normalized": True,
        "solution_internal_note_removed": True,
    }
    data["production_state"]["v41_interlude_visual_contract"] = {
        "families": list(INTERLUDE_FAMILIES),
        "selector": "(case_number * 7 + physical_page * 3) mod 4",
        "case_specific_copy": True,
        "pagination_changed": False,
    }
    data["production_state"]["v41_book2_hook_contract"] = {
        "presentation": "CINEMATIC_ARCHIVE_WAKE_V1",
        "owner_art_required": True,
        "owner_art_transform": "FIT_ONLY_PRESERVE_ASPECT_RATIO",
        "premise_changed": False,
        "pagination_changed": False,
    }
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
    original_publication = v4.publication_page
    original_id_page = v4.id_page
    original_nonspatial_solution = v4.nonspatial_solution_page
    if visuals_integrated:
        v4.case03_photo_page = case03_photo_page
        v4.book2_scene_page = book2_scene_page
    v4.parity_pause = parity_pause_v41
    v4.publication_page = publication_page_v41
    v4.id_page = id_page_v41
    v4.nonspatial_solution_page = nonspatial_solution_page_v41
    try:
        pages, _index = v4.render_v4(data, cases, v41_master, args.output.resolve())
    finally:
        v4.case03_photo_page = original_case03
        v4.book2_scene_page = original_book2
        v4.parity_pause = original_parity
        v4.publication_page = original_publication
        v4.id_page = original_id_page
        v4.nonspatial_solution_page = original_nonspatial_solution
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
            "parity_interludes": {
                "status": "case-specific deterministic visual-family rotation",
                "families": list(INTERLUDE_FAMILIES),
                "case_specific_copy": True,
            },
            "book2_hook": {
                "presentation": "CINEMATIC_ARCHIVE_WAKE_V1",
                "owner_art_required": True,
                "owner_art_regenerated": False,
                "owner_art_destructively_cropped": False,
                "premise_changed": False,
            },
            "reader_surface_cleanup": {
                "publication_internal_copy_removed": True,
                "field_detective_id_normalized": True,
                "solution_internal_note_removed": True,
            },
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
