#!/usr/bin/env python3
"""Apply bounded V4.1 finale and certificate premium polish.

This wrapper changes presentation only. It temporarily replaces the V4 finale
and certificate renderers, delegates to the already-bounded V4.1 premium
builder, restores the canonical V4 functions, then records the presentation
contract in the V4.1 manifest.

It does not change story text, puzzle logic, witness identities, Room Zero
mechanism, pagination, owner-gated art, or English freeze state.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import build_owner_review_v4 as v4
import build_owner_review_v41_premium as premium

rb = v4.rb
MANIFEST_NAME = premium.MANIFEST_NAME
FINALE_STYLE = "ROOM_ZERO_EVIDENCE_GRID_V1"
CERTIFICATE_STYLE = "FIELD_CERTIFICATION_BADGE_RACK_V1"


def _draw_badge_slot(c, cx: float, cy: float, number: int, active: bool = False) -> None:
    """Draw one certification-rack slot; slot 06 is emphasized as reader-earned."""
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(2.1 if active else 1.0)
    c.setFillColor(rb.BLACK if active else rb.WHITE)
    c.circle(cx, cy, 17, fill=1, stroke=1)
    c.setFillColor(rb.WHITE if active else rb.BLACK)
    c.setFont(rb.BOLD, 9.5)
    c.drawCentredString(cx, cy - 3.2, f"{number:02d}")


def finale_page_v41(c, data: dict, mission: dict, page: int) -> None:
    """Render canonical Room Zero explanation as a premium evidence board."""
    rb.top_bar(c, "ROOM ZERO // CASE CLOSED", page, 1.0)
    x = rb.M
    w = rb.PAGE_W - 2 * rb.M
    y = rb.PAGE_H - 62

    rb.para(
        c,
        "THE DOOR OPENS. NOW THE WHOLE TRAIL HAS TO EXPLAIN ITSELF.",
        x,
        y,
        w,
        42,
        size=18.5,
        font=rb.BOLD,
    )
    y -= 50

    # Keep the seven canonical explanation sections verbatim; improve scan order.
    sections = data.get("finale_sections", [])
    gap = 10
    col_w = (w - gap) / 2
    card_h = 106
    for index, section in enumerate(sections[:7], 1):
        col = (index - 1) % 2
        row = (index - 1) // 2
        left = x + col * (col_w + gap)
        top = y - row * (card_h + 7)
        rb.box(c, left, top - card_h, col_w, card_h, fill=rb.WHITE, stroke=rb.BLACK, radius=8, sw=1.0)
        rail_w = 31
        rb.box(c, left, top - card_h, rail_w, card_h, fill=rb.BLACK, stroke=rb.BLACK, radius=8)
        c.setFillColor(rb.WHITE)
        c.setFont(rb.BOLD, 9.5)
        c.drawCentredString(left + rail_w / 2, top - 22, f"{index:02d}")
        rb.label(c, str(section.get("heading", "")).upper(), left + rail_w + 9, top - 19, size=8.8)
        rb.para(
            c,
            html.escape(str(section.get("body", ""))),
            left + rail_w + 9,
            top - 32,
            col_w - rail_w - 18,
            card_h - 39,
            size=9.2,
        )

    # The eighth cell is a compact routing-proof card. This is the same canonical
    # routing evidence as V4, only reformatted for a clearer close.
    left = x + col_w + gap
    top = y - 3 * (card_h + 7)
    rb.box(c, left, top - card_h, col_w, card_h, fill=rb.BLACK, stroke=rb.BLACK, radius=8)
    rb.label(c, "08 // ROUTING / SELECTION PROOF", left + 10, top - 19, size=8.8, color=rb.WHITE)
    log = (
        "00:00  ROSTER SAVED // SLOT 06 OPEN // ENVELOPE RELEASED<br/>"
        "00:01  CASE 01 CLOSED // QUEUE RESTARTED<br/>"
        "CASE 05  BALL &gt; STAR &gt; BOLT &gt; HEART<br/>"
        "SELECTED MAPS  02 04 06 07 10 12 13 / 15 17 19 20 22 23 25"
    )
    rb.para(c, log, left + 10, top - 34, col_w - 20, card_h - 40, size=8.7, font=rb.BOLD, color=rb.WHITE)

    # Render the already-canonical finale chat, previously present in source but
    # not surfaced on the V4 page, as a short debrief strip.
    chat = data.get("finale_chat", [])
    chat_top = 178
    rb.box(c, x, 86, w, chat_top - 86, fill=rb.WHITE, stroke=rb.BLACK, radius=9, sw=1.0)
    rb.label(c, "CASE CLOSED // HAPPY MAKERS DEBRIEF", x + 11, chat_top - 19, size=8.8)
    ty = chat_top - 34
    for item in chat[:4]:
        speaker = str(item.get("speaker", "")).upper()
        char_name = data.get("characters", {}).get(item.get("speaker"), {}).get("name", speaker)
        text = f"<b>{html.escape(str(char_name))}:</b> {html.escape(str(item.get('text', '')))}"
        h = rb.text_height(text, w - 22, 8.8)
        rb.para(c, text, x + 11, ty, w - 22, h + 1, size=8.8)
        ty -= h + 2

    rb.footer(c, page)
    c.showPage()


def certificate_page_v41(c, data: dict, page: int) -> None:
    """Render the canonical certificate as a premium earned-field-slot artifact."""
    cert = data.get("certificate", {})
    rb.top_bar(c, "DETECTIVE ACADEMY // FIELD CERTIFICATION", page, 1.0)

    x = rb.M + 22
    w = rb.PAGE_W - 2 * rb.M - 44
    bottom = 92
    top = rb.PAGE_H - 77

    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(2.2)
    c.rect(x, bottom, w, top - bottom, fill=0, stroke=1)
    c.setLineWidth(0.7)
    c.rect(x + 9, bottom + 9, w - 18, top - bottom - 18, fill=0, stroke=1)

    # Certification rack: five established slots + the reader-earned sixth slot.
    rack_y = top - 52
    rb.label(c, "FIELD CERTIFICATION RACK // SLOT 06 EARNED", x + 24, rack_y + 21, size=8.8)
    left = x + 62
    right = x + w - 62
    span = (right - left) / 5
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(1.0)
    c.line(left, rack_y, right, rack_y)
    for i in range(6):
        _draw_badge_slot(c, left + i * span, rack_y, i + 1, active=(i == 5))

    rb.para(
        c,
        cert.get("heading", "DETECTIVE ACADEMY // FIELD CERTIFICATION"),
        x + 35,
        rack_y - 58,
        w - 70,
        44,
        size=18,
        font=rb.BOLD,
        align=1,
    )

    field_left = x + 56
    field_right = x + w - 56
    label_y = rack_y - 119
    rb.label(c, cert.get("awarded_to_label", "AWARDED TO"), field_left, label_y, size=9.2)
    c.setLineWidth(1.0)
    c.line(field_left, label_y - 29, field_right, label_y - 29)

    label_y -= 70
    rb.label(c, cert.get("call_sign_label", "OFFICIAL CALL SIGN"), field_left, label_y, size=9.2)
    c.line(field_left, label_y - 29, field_right, label_y - 29)

    achievement = cert.get(
        "achievement",
        "FOR SOLVING THE MYSTERY OF ROOM ZERO BY FOLLOWING THE EVIDENCE ALL THE WAY TO THE TRUTH.",
    )
    rb.para(
        c,
        html.escape(str(achievement)),
        x + 52,
        label_y - 72,
        w - 104,
        76,
        size=12.5,
        font=rb.BOLD,
        align=1,
    )

    band_y = 262
    rb.box(c, x + 55, band_y, w - 110, 76, fill=rb.BLACK, stroke=rb.BLACK, radius=10)
    rb.para(
        c,
        cert.get("rank", "CERTIFIED FIELD DETECTIVE // DETECTIVE SIX"),
        x + 67,
        band_y + 49,
        w - 134,
        28,
        size=12.2,
        font=rb.BOLD,
        color=rb.WHITE,
        align=1,
    )
    rb.para(
        c,
        cert.get("case_status", "ROOM ZERO // CLOSED"),
        x + 67,
        band_y + 22,
        w - 134,
        20,
        size=9.4,
        color=rb.WHITE,
        align=1,
    )

    sig_y = 205
    rb.label(c, cert.get("signed_by", "Happy Makers Detective Academy"), field_left, sig_y, size=9.0)
    c.line(field_left, sig_y - 19, rb.PAGE_W / 2 - 12, sig_y - 19)
    rb.label(c, cert.get("archive_confirmation", "BIBI // ARCHIVE MENTOR"), rb.PAGE_W / 2 + 12, sig_y, size=9.0)
    c.line(rb.PAGE_W / 2 + 12, sig_y - 19, field_right, sig_y - 19)

    rb.para(
        c,
        cert.get("note", "Use the call sign from your Field Detective ID."),
        x + 42,
        144,
        w - 84,
        34,
        size=9.3,
        align=1,
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
        raise ValueError("Unexpected V4.1 manifest state after finale/certificate render")
    premium_polish = packet.setdefault("premium_polish", {})
    premium_polish["finale_presentation"] = {
        "status": "INTEGRATED",
        "style": FINALE_STYLE,
        "canonical_sections_changed": False,
        "room_zero_mechanism_changed": False,
        "pagination_changed": False,
    }
    premium_polish["certificate_presentation"] = {
        "status": "INTEGRATED",
        "style": CERTIFICATE_STYLE,
        "achievement_copy_changed": False,
        "detective_six_premise_changed": False,
        "pagination_changed": False,
    }
    manifest_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")


def main() -> None:
    manifest_path = _manifest_path_from_argv(sys.argv[1:])
    original_finale = v4.finale_page
    original_certificate = v4.certificate_page
    v4.finale_page = finale_page_v41
    v4.certificate_page = certificate_page_v41
    try:
        premium.main()
    finally:
        v4.finale_page = original_finale
        v4.certificate_page = original_certificate
    _mark_manifest(manifest_path)
    print("PASS: V4.1 finale / certificate premium presentation integrated")
    print("English frozen: false")


if __name__ == "__main__":
    main()
