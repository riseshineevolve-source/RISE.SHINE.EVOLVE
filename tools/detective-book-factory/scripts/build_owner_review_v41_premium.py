#!/usr/bin/env python3
"""Apply bounded V4.1 Room Zero / Signal Log presentation polish.

This wrapper deliberately changes presentation only. It delegates all content,
logic, pagination, owner-visual gating and English-freeze behavior to the
existing V4.1 builder while temporarily replacing the Signal Log renderer with
three deterministic visual families.

No case answer, signal text, Room Zero mechanism, spatial geometry or owner-
gated art is changed here.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import build_owner_review_v4 as v4
import build_owner_review_v41 as v41

rb = v4.rb
SIGNAL_FAMILIES = ("TRACE", "ARCHIVE", "ROUTING")
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
    manifest_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")


def main() -> None:
    manifest_path = _manifest_path_from_argv(sys.argv[1:])
    original_signal_page = v4.signal_page
    v4.signal_page = signal_page_v41
    try:
        v41.main()
    finally:
        v4.signal_page = original_signal_page
    _mark_manifest(manifest_path)
    print("PASS: V4.1 premium Signal Log / Room Zero presentation integrated")
    print("English frozen: false")


if __name__ == "__main__":
    main()
