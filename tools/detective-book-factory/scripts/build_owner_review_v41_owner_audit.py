#!/usr/bin/env python3
"""Apply owner-audit presentation corrections on top of the canonical V4.1 stack.

This layer is intentionally bounded:
- preserves all locked case logic, spatial geometry, pagination and owner-gated art;
- normalizes Field Detective identity surfaces to DETECTIVE NAME + OFFICIAL CALL SIGN + 06;
- makes Case 30 ask for the OFFICIAL CALL SIGN rather than a vague name;
- removes non-ceremonial certificate meta copy;
- diversifies the ARCHIVE Signal Log family so it no longer repeats a giant zero.

English remains NOT FROZEN.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import build_owner_review_v4 as v4
import build_owner_review_v41 as v41
import build_owner_review_v41_premium as premium
import build_owner_review_v41_finale as finale

rb = v4.rb
MANIFEST_NAME = "HMDA_Book1_EN_OwnerReview_v41_manifest.json"

_ORIGINAL_BUILD_DATA = v4.build_data


def _patched_build_data(*args, **kwargs):
    data, cases, v4_master, runtime = _ORIGINAL_BUILD_DATA(*args, **kwargs)

    opening = data.setdefault("opening", {})
    card = opening.setdefault("id_card", {})
    card["name_label"] = "DETECTIVE NAME"
    card["call_sign_label"] = "OFFICIAL CALL SIGN"

    acceptance = opening.get("acceptance_letter")
    if isinstance(acceptance, dict):
        note = acceptance.get("note")
        if isinstance(note, str):
            acceptance["note"] = note.replace(
                "Write your call sign.",
                "Write your OFFICIAL CALL SIGN.",
            )

    for mission in data.get("missions", []):
        if int(mission.get("number", 0)) != 30:
            continue

        signal = mission.get("signal_log")
        if isinstance(signal, dict):
            signal["reader_move"] = (
                "Use the same OFFICIAL CALL SIGN from your Field Detective ID "
                "on the certificate. Book 1 closes before the next file arrives."
            )

        finale_data = mission.get("finale")
        if isinstance(finale_data, dict):
            for stage in finale_data.get("stages", []):
                if str(stage.get("id", "")).upper() == "DETECTIVE":
                    stage["prompt"] = (
                        "Write your OFFICIAL CALL SIGN from your Field Detective ID."
                    )
                    stage["answer"] = "READER-WRITTEN OFFICIAL CALL SIGN"

        hints = mission.get("hints")
        if isinstance(hints, list):
            mission["hints"] = [
                (
                    item.replace(
                        "use the call sign on your one Field Detective ID",
                        "use the OFFICIAL CALL SIGN on your one Field Detective ID",
                    )
                    if isinstance(item, str)
                    else item
                )
                for item in hints
            ]

        steps = mission.get("solution_steps")
        if isinstance(steps, list):
            mission["solution_steps"] = [
                (
                    item.replace(
                        "Use the call sign already written on your single Field Detective ID.",
                        "Use the OFFICIAL CALL SIGN already written on your single Field Detective ID.",
                    )
                    if isinstance(item, str)
                    else item
                )
                for item in steps
            ]

    state = data.setdefault("production_state", {})
    state["owner_audit_identity_contract"] = {
        "field_detective_id_fields": ["DETECTIVE NAME", "OFFICIAL CALL SIGN"],
        "field_slot": "06",
        "case30_requests_official_call_sign": True,
        "logic_changed": False,
        "pagination_changed": False,
    }
    return data, cases, v4_master, runtime


def id_page_owner_audit(c, data: dict, page: int) -> None:
    """Render exactly two recruit identity fields plus the fixed slot number 06."""
    card = data["opening"].get("id_card", {})
    rb.top_bar(c, "DETECTIVE SIX // FIELD DETECTIVE ID", page)
    y = rb.PAGE_H - 70
    rb.para(
        c,
        card.get("heading", "FIELD DETECTIVE ID"),
        rb.M,
        y,
        rb.PAGE_W - 2 * rb.M,
        48,
        size=21,
        font=rb.BOLD,
    )
    y -= 70

    rb.box(
        c,
        rb.M,
        y - 415,
        rb.PAGE_W - 2 * rb.M,
        415,
        fill=rb.WHITE,
        stroke=rb.BLACK,
        radius=16,
        sw=1.6,
    )
    rb.label(
        c,
        card.get("designation", "DETECTIVE SIX // RECRUIT"),
        rb.M + 18,
        y - 27,
        size=11,
    )

    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(4)
    c.circle(rb.PAGE_W - rb.M - 72, y - 67, 37, fill=0, stroke=1)
    c.setFillColor(rb.BLACK)
    c.setFont(rb.BOLD, 30)
    c.drawCentredString(rb.PAGE_W - rb.M - 72, y - 78, "06")

    fields = ("DETECTIVE NAME", "OFFICIAL CALL SIGN")
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
    rb.para(
        c,
        html.escape(str(acceptance)),
        rb.M + 18,
        ty,
        rb.PAGE_W - 2 * rb.M - 36,
        60,
        size=11,
        font=rb.BOLD,
    )

    rb.box(
        c,
        rb.M,
        y - 445,
        rb.PAGE_W - 2 * rb.M,
        102,
        fill=rb.WHITE,
        stroke=rb.BLACK,
        radius=9,
        sw=1.0,
    )
    rb.label(c, "FIELD ID // KEEP THIS CARD", rb.M + 14, y - 469, size=9.5)
    rb.para(
        c,
        "Use the same OFFICIAL CALL SIGN when the final certification check asks for it.",
        rb.M + 14,
        y - 488,
        rb.PAGE_W - 2 * rb.M - 28,
        48,
        size=10.8,
        font=rb.BOLD,
    )

    rb.para(
        c,
        "FIELD SLOT 06 // RECRUIT STATUS",
        rb.M,
        62,
        rb.PAGE_W - 2 * rb.M,
        28,
        size=10.5,
        font=rb.BOLD,
        align=1,
    )
    rb.footer(c, page)
    c.showPage()


def archive_signal_panel_owner_audit(
    c, s: dict, mission: dict, x: float, top: float, w: float, h: float
) -> None:
    """Use a case-number archive rail instead of repeating the giant Room Zero glyph."""
    rb.box(c, x, top - h, w, h, fill=rb.WHITE, stroke=rb.BLACK, radius=12, sw=1.3)
    rail = 76
    rb.box(c, x, top - h, rail, h, fill=rb.BLACK, stroke=rb.BLACK, radius=12)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.BOLD, 24)
    c.drawCentredString(x + rail / 2, top - 57, f"{int(mission['number']):02d}")
    rb.label(c, "CASE FILE", x + 14, top - 83, size=8.4, color=rb.WHITE)
    rb.label(c, "ARCHIVE", x + 13, top - 102, size=8.8, color=rb.WHITE)

    body_x = x + rail + 14
    body_w = w - rail - 28
    rb.label(
        c,
        f"CASE {int(mission['number']):02d} // SIGNAL RECORD",
        body_x,
        top - 24,
        size=9.5,
    )
    rb.para(
        c,
        html.escape(str(s["code"])),
        body_x,
        top - 43,
        body_w * 0.38,
        26,
        size=16,
        font=rb.BOLD,
    )
    rb.para(
        c,
        html.escape(str(s["status"])),
        body_x + body_w * 0.40,
        top - 43,
        body_w * 0.60,
        38,
        size=12,
        font=rb.BOLD,
    )
    c.setStrokeColor(rb.LINE)
    c.setLineWidth(0.8)
    c.line(body_x, top - 89, x + w - 14, top - 89)
    rb.label(c, "CASE → SIGNAL CODE → VERIFIED STATUS", body_x, top - 105, size=9)


def certificate_page_owner_audit(c, data: dict, page: int) -> None:
    """Render the canonical certificate without non-ceremonial instructional meta copy."""
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

    rack_y = top - 52
    rb.label(c, "FIELD CERTIFICATION RACK // SLOT 06 EARNED", x + 24, rack_y + 21, size=8.8)
    left = x + 62
    right = x + w - 62
    span = (right - left) / 5
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(1.0)
    c.line(left, rack_y, right, rack_y)
    for i in range(6):
        finale._draw_badge_slot(c, left + i * span, rack_y, i + 1, active=(i == 5))

    rb.para(
        c,
        cert.get("heading", "DETECTIVE ACADEMY // FIELD CERTIFICATION"),
        x + 35,
        rack_y - 58,
        w - 70,
        60,
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
    rb.label(c, "OFFICIAL CALL SIGN", field_left, label_y, size=9.2)
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
    rb.label(
        c,
        cert.get("archive_confirmation", "BIBI // ARCHIVE MENTOR"),
        rb.PAGE_W / 2 + 12,
        sig_y,
        size=9.0,
    )
    c.line(rb.PAGE_W / 2 + 12, sig_y - 19, field_right, sig_y - 19)

    rb.label(
        c,
        "DETECTIVE SIX // FIELD SLOT 06 CERTIFIED",
        x + 42,
        151,
        size=9.3,
    )
    rb.footer(c, page)
    c.showPage()


def _manifest_path_from_argv(argv: list[str]) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", required=True, type=Path)
    known, _ = parser.parse_known_args(argv)
    return known.output.resolve().parent / MANIFEST_NAME


def _mark_manifest(path: Path) -> None:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if packet.get("revision") != "v4.1" or packet.get("english_frozen") is not False:
        raise ValueError("Unexpected V4.1 manifest state after owner-audit correction layer")
    packet["owner_audit_corrections"] = {
        "field_detective_id": {
            "fields": ["DETECTIVE NAME", "OFFICIAL CALL SIGN"],
            "field_slot": "06",
            "combined_name_call_sign_removed": True,
        },
        "case30_official_call_sign_prompt": True,
        "certificate_nonceremonial_meta_removed": True,
        "signal_archive_giant_zero_removed": True,
        "owner_gated_art_changed": False,
        "logic_changed": False,
        "pagination_changed": False,
        "english_frozen": False,
    }
    path.write_text(json.dumps(packet, indent=2), encoding="utf-8")


def main() -> None:
    manifest_path = _manifest_path_from_argv(sys.argv[1:])

    original_build_data = v4.build_data
    original_id = v41.id_page_v41
    original_archive_panel = premium._signal_panel_archive
    original_certificate = finale.certificate_page_v41

    v4.build_data = _patched_build_data
    v41.id_page_v41 = id_page_owner_audit
    premium._signal_panel_archive = archive_signal_panel_owner_audit
    finale.certificate_page_v41 = certificate_page_owner_audit
    try:
        finale.main()
    finally:
        v4.build_data = original_build_data
        v41.id_page_v41 = original_id
        premium._signal_panel_archive = original_archive_panel
        finale.certificate_page_v41 = original_certificate

    _mark_manifest(manifest_path)
    print("PASS: V4.1 owner-audit identity / Case 30 / certificate / Signal Log corrections integrated")
    print("English frozen: false")


if __name__ == "__main__":
    main()
