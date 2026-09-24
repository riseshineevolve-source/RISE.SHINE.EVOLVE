#!/usr/bin/env python3
"""Apply bounded V4.1 premium presentation polish.

This wrapper deliberately changes presentation only. It delegates all content,
logic, pagination, owner-visual gating and English-freeze behavior to the
existing V4.1 builder while temporarily replacing the Signal Log and Witness
Board renderers with deterministic premium presentation layers.

No case answer, clue text, signal text, Room Zero mechanism, spatial geometry or
owner-gated art is changed here.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import build_owner_review_v4 as v4
import build_owner_review_v41 as v41
import render_spatial_case_spreads as spreads

rb = v4.rb
SIGNAL_FAMILIES = ("TRACE", "ARCHIVE", "ROUTING")
WITNESS_BOARD_STYLE = "DOSSIER_EVIDENCE_RAIL_V1"
MANIFEST_NAME = "HMDA_Book1_EN_OwnerReview_v41_manifest.json"


def signal_family_for_case(case_number: int) -> str:
    """Return one of three deterministic visual families without changing data."""
    if not 1 <= int(case_number) <= 30:
        raise ValueError(f"Unsupported Detective case number: {case_number}")
    return SIGNAL_FAMILIES[(int(case_number) - 1) % len(SIGNAL_FAMILIES)]


def _signal_panel_trace(c, s: dict, mission: dict, x: float, top: float, w: float, h: float) -> None:
    rb.box(c, x, top - h, w, h, fill=rb.BLACK, stroke=rb.BLACK, radius=12)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.BOLD, 42)
    c.drawString(x + 18, top - 77, "0")
    rb.label(c, f"CASE {int(mission['number']):02d} // {html.escape(str(s['code']))}", x + 88, top - 31,
             size=10, color=rb.WHITE)
    rb.para(c, html.escape(str(s["status"])), x + 88, top - 47, w - 108, 34,
            size=14, font=rb.BOLD, color=rb.WHITE)
    rb.label(c, "ROOM ZERO TRACE // VERIFIED CONTEXT", x + 88, top - 93,
             size=9.2, color=rb.WHITE)


def _signal_panel_archive(c, s: dict, mission: dict, x: float, top: float, w: float, h: float) -> None:
    rb.box(c, x, top - h, w, h, fill=rb.WHITE, stroke=rb.BLACK, radius=12, sw=1.3)
    rail = 76
    rb.box(c, x, top - h, rail, h, fill=rb.BLACK, stroke=rb.BLACK, radius=12)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.BOLD, 38)
    c.drawCentredString(x + rail / 2, top - 67, "0")
    rb.label(c, "ARCHIVE", x + 13, top - 98, size=8.8, color=rb.WHITE)
    body_x = x + rail + 14
    body_w = w - rail - 28
    rb.label(c, f"CASE {int(mission['number']):02d} // SIGNAL RECORD", body_x, top - 24, size=9.5)
    rb.para(c, html.escape(str(s["code"])), body_x, top - 43, body_w * 0.38, 26,
            size=16, font=rb.BOLD)
    rb.para(c, html.escape(str(s["status"])), body_x + body_w * 0.40, top - 43,
            body_w * 0.60, 38, size=12, font=rb.BOLD)
    c.setStrokeColor(rb.LINE)
    c.setLineWidth(0.8)
    c.line(body_x, top - 89, x + w - 14, top - 89)
    rb.label(c, "CASE → SIGNAL CODE → VERIFIED STATUS", body_x, top - 105, size=9)


def _signal_panel_routing(c, s: dict, mission: dict, x: float, top: float, w: float, h: float) -> None:
    rb.box(c, x, top - h, w, h, fill=rb.WHITE, stroke=rb.BLACK, radius=12, sw=1.3)
    rb.label(c, "ROOM ZERO // ROUTING TRACE", x + 12, top - 20, size=9.5)
    nodes = (
        (f"CASE {int(mission['number']):02d}", "CASE"),
        (str(s["code"]), "SIGNAL"),
        (str(s["status"]), "STATUS"),
    )
    left = x + 64
    right = x + w - 64
    cy = top - 72
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(2)
    c.line(left + 18, cy, right - 18, cy)
    span = (right - left) / 2
    for idx, (value, label) in enumerate(nodes):
        cx = left + idx * span
        c.setFillColor(rb.WHITE)
        c.setStrokeColor(rb.BLACK)
        c.setLineWidth(2)
        c.circle(cx, cy, 18, fill=1, stroke=1)
        c.setFillColor(rb.BLACK)
        c.setFont(rb.BOLD, 9)
        c.drawCentredString(cx, cy - 3, f"{idx + 1:02d}")
        rb.label(c, label, cx - 31, cy - 35, size=8.4)
        rb.para(c, html.escape(value), cx - 52, cy - 49, 104, 35,
                size=9.2, font=rb.BOLD, align=1)


def signal_page_v41(c, data: dict, mission: dict, page: int, progress: float) -> None:
    """Render unchanged Signal Log content through a deterministic visual family."""
    signal = mission["signal_log"]
    family = signal_family_for_case(int(mission["number"]))
    rb.top_bar(c, f"ROOM ZERO TRACE // SIGNAL LOG // {family}", page, progress)
    y = rb.PAGE_H - 64
    rb.para(c, signal["label"], rb.M, y, rb.PAGE_W - 2 * rb.M, 48,
            size=21, font=rb.BOLD)
    y -= 64

    panel_h = 132
    panel_w = rb.PAGE_W - 2 * rb.M
    panel = {
        "TRACE": _signal_panel_trace,
        "ARCHIVE": _signal_panel_archive,
        "ROUTING": _signal_panel_routing,
    }[family]
    panel(c, signal, mission, rb.M, y, panel_w, panel_h)
    y -= panel_h + 24

    rb.avatar_callout(
        c,
        data["characters"],
        signal["speaker"],
        signal["reaction"],
        rb.M,
        y,
        panel_w,
    )
    y -= 108
    rb.text_card(
        c,
        signal["reader_move"],
        rb.M,
        y,
        panel_w,
        heading="YOUR MOVE // SIGNAL LOG",
        size=11.5,
        stroke=rb.BLACK,
    )
    rb.label(
        c,
        f"READER STATUS // {mission.get('reader_stage', 'DETECTIVE')} // TRACE SAVED",
        rb.M,
        62,
        size=9.5,
    )
    rb.footer(c, page)
    c.showPage()


def witness_board_v41(c, mission: dict, case: dict, page_no: int) -> None:
    """Render the canonical Witness Board copy with stronger dossier hierarchy."""
    rb.top_bar(c, "WITNESS BOARD // LIVE EVIDENCE", page_no)
    x = rb.M
    w = rb.PAGE_W - 2 * x
    y = rb.PAGE_H - 61

    # Strong dossier masthead: case/rank/status are easier to scan at print size.
    mast_h = 34
    rb.box(c, x, y - mast_h, w, mast_h, fill=rb.BLACK, stroke=rb.BLACK, radius=7)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.BOLD, 10.5)
    c.drawString(x + 12, y - 22, f"CASE {int(mission['number']):02d} // {mission['rank'].upper()}")
    c.drawRightString(x + w - 12, y - 22, "STATUS // OPEN")
    y -= mast_h + 8

    used = spreads.paragraph(c, html.escape(mission["title"]), x, y, w, 52, 21, bold=True)
    y -= used + 8
    used = spreads.paragraph(c, spreads.alias_text(mission["hook"], case), x, y, w, 65, 11.5)
    y -= used + 9

    # Objective remains verbatim; the heavier frame creates a clear task hierarchy.
    obj = spreads.Paragraph(
        spreads.alias_text(mission["objective"], case),
        spreads.ParagraphStyle("objective_v41", fontName=rb.BOLD, fontSize=11.5, leading=14.5),
    )
    _, oh = obj.wrap(w - 36, 100)
    card_h = oh + 40
    rb.box(c, x, y - card_h, w, card_h, fill=rb.WHITE, stroke=rb.BLACK, radius=10, sw=1.5)
    c.setFillColor(rb.BLACK)
    c.rect(x, y - card_h, 6, card_h, fill=1, stroke=0)
    c.setFont(rb.BOLD, 9.5)
    c.drawString(x + 18, y - 18, "YOUR OBJECTIVE // LOCK THE TARGET")
    obj.drawOn(c, x + 18, y - 27 - oh)
    y -= card_h + 12

    # Preserve the numbered witness identities exactly; present them as a clean roster rail.
    roster = "  |  ".join(
        f"{index:02d} {person['display_name']}" for index, person in enumerate(case["characters"], 1)
    )
    c.setStrokeColor(rb.LINE)
    c.setLineWidth(0.8)
    c.line(x, y + 4, x + w, y + 4)
    roster_h = spreads.paragraph(c, html.escape(roster), x, y, w, 46, 11, bold=True)
    y -= roster_h + 8

    notes = mission.get("dialogue", [])
    if notes:
        c.setFillColor(rb.BLACK)
        c.setFont(rb.BOLD, 9.5)
        c.drawString(x, y, "FIELD NOTE // HAPPY MAKERS CHAT")
        y -= 13
        note = "  ".join(f"{item['speaker'].upper()}: {item['text']}" for item in notes)
        used = spreads.paragraph(c, spreads.alias_text(note, case), x, y, w, 65, 11)
        y -= used + 10

    c.setFillColor(rb.BLACK)
    c.setFont(rb.BOLD, 12)
    c.drawString(x, y, "WITNESS STATEMENTS")
    c.setFont(rb.FONT, 10)
    c.drawRightString(x + w, y, "Tick each fact you use.")
    y -= 16

    # Keep every canonical clue verbatim. The numbered evidence rail makes the page
    # read as a real case file without shrinking the working text or changing logic.
    clues = mission["spatial_copy"]["clue_cards"]
    cards = []
    for clue in clues:
        markup = spreads.alias_text(clue, case)
        for person in case["characters"]:
            name = person["display_name"]
            markup = re.sub(
                rf"(?<!>)\b{re.escape(name)}\b(?!</b>)",
                f"<b>{name}</b>",
                markup,
                flags=re.IGNORECASE,
            )
        p = spreads.Paragraph(
            markup,
            spreads.ParagraphStyle(
                "evidence_v41", fontName=rb.FONT, fontSize=11.5, leading=14.5, textColor=rb.BLACK
            ),
        )
        _, height = p.wrap(w - 82, 100)
        cards.append((p, height + 20))

    available = y - 87
    needed = sum(h for _, h in cards) + 5 * (len(cards) - 1)
    if needed > available:
        raise ValueError(
            f"Case {mission['number']}: V4.1 evidence needs {needed:.1f}pt, has {available:.1f}pt"
        )
    extra = min(9, (available - needed) / len(cards))
    for index, (p, h) in enumerate(cards, 1):
        h += extra
        rb.box(c, x, y - h, w, h, fill=rb.WHITE, stroke=rb.BLACK, radius=8, sw=1.0)
        rail_w = 34
        rb.box(c, x, y - h, rail_w, h, fill=rb.BLACK, stroke=rb.BLACK, radius=8)
        c.setFillColor(rb.WHITE)
        c.setFont(rb.BOLD, 11)
        c.drawCentredString(x + rail_w / 2, y - 21, f"{index:02d}")
        p.drawOn(c, x + 45, y - 10 - p.height)
        c.setStrokeColor(rb.BLACK)
        c.setLineWidth(1.0)
        c.rect(x + w - 24, y - h / 2 - 5, 10, 10, fill=0, stroke=1)
        y -= h + 5

    c.setFillColor(rb.BLACK)
    c.setFont(rb.BOLD, 11)
    c.drawString(x, 58, "FOLLOW THE EVIDENCE. DON'T GUESS.")
    rb.footer(c, page_no)
    c.showPage()


def _manifest_path_from_argv(argv: list[str]) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", required=True, type=Path)
    known, _ = parser.parse_known_args(argv)
    return known.output.resolve().parent / MANIFEST_NAME


def _mark_manifest(manifest_path: Path) -> None:
    packet = json.loads(manifest_path.read_text(encoding="utf-8"))
    if packet.get("revision") != "v4.1" or packet.get("english_frozen") is not False:
        raise ValueError("Unexpected V4.1 manifest state after premium presentation render")
    premium = packet.setdefault("premium_polish", {})
    premium["signal_log_visual_families"] = {
        "status": "INTEGRATED",
        "families": list(SIGNAL_FAMILIES),
        "selection": "CASE_NUMBER_MODULO_3",
        "content_changed": False,
        "pagination_changed": False,
    }
    premium["room_zero_trace_presentation"] = {
        "status": "INTEGRATED",
        "chain": "CASE -> SIGNAL CODE -> VERIFIED STATUS",
        "mechanism_changed": False,
    }
    premium["witness_board_presentation"] = {
        "status": "INTEGRATED",
        "style": WITNESS_BOARD_STYLE,
        "clue_text_changed": False,
        "witness_identity_changed": False,
        "pagination_changed": False,
        "spatial_geometry_changed": False,
    }
    manifest_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")


def main() -> None:
    manifest_path = _manifest_path_from_argv(sys.argv[1:])
    original_signal_page = v4.signal_page
    original_witness_board = v4.witness_board
    v4.signal_page = signal_page_v41
    v4.witness_board = witness_board_v41
    try:
        v41.main()
    finally:
        v4.signal_page = original_signal_page
        v4.witness_board = original_witness_board
    _mark_manifest(manifest_path)
    print("PASS: V4.1 premium Signal Log / Room Zero / Witness Board presentation integrated")
    print("English frozen: false")


if __name__ == "__main__":
    main()
