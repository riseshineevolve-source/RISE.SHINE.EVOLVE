#!/usr/bin/env python3
"""Bounded V3.1 correction layer for the HMDA Book 1 owner-review PDF.

This intentionally wraps V3 instead of reopening the narrative, puzzle logic,
spatial geometry, aliases or naming system. It addresses only concrete defects
from the independent owner-level V3 PDF review.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import inch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_owner_review_v3 as v3
import render_book as rb
from spatial_presentation import draw_grid, verdict_card

ORIG_BUILD_DATA = v3.build_data
ORIG_STRUCTURED = rb.structured_puzzle_page
ORIG_ARTIFACT = v3.artifact_page

TARGET_VISUAL_CASES = {3, 8, 11, 24}


def build_data_v31(*args, **kwargs):
    data, cases, master, runtime = ORIG_BUILD_DATA(*args, **kwargs)

    # V3.1 wording correction only: the field team has five detectives,
    # Grandma Bibi is the archive mentor, and the reader fills field slot six.
    data["book"]["opening_code"] = (
        "FIVE FIELD DETECTIVES. ONE ARCHIVE MENTOR. ONE EMPTY FIELD BADGE."
    )
    acceptance = data["opening"]["acceptance_letter"]
    acceptance["body"] = (
        "The Happy Makers' five field detectives were closing the Academy for the night when the old "
        "intake printer woke up. It printed one line: ONE DETECTIVE IS STILL MISSING. Then a black "
        "envelope slid from a slot that had been sealed for years. Inside was an Academy badge with a "
        "blank name line and a tiny 0. The team checked the field roster: five names. Grandma Bibi's "
        "archive badge is separate. Six field badge hooks. If you found this file, the empty field "
        "badge was meant for you."
    )
    acceptance["note"] = (
        "Write your detective name on the official ID. Mimi, Luli, Dilo, Alio and Nini are the five "
        "field detectives. Grandma Bibi is their archive mentor. You are the sixth field recruit, and "
        "you make the final call."
    )
    data["opening"]["squad_intro"] = (
        "Mimi, Luli, Dilo, Alio and Nini are the Academy's five field detectives. Mimi keeps the case "
        "moving. Luli tests every claim. Dilo handles codes and machines. Alio checks routes and carries "
        "too many helmets. Nini notices people and quiet details. Grandma Bibi is their archive mentor: "
        "she connects present evidence to incomplete Academy history. They disagree, recover and make "
        "room for the sixth field recruit: you."
    )
    how = list(data["opening"]["how_to_play"])
    how[2] = (
        "NEED A NUDGE? The Hint Vault is near the back. Find your case and read Level 1 only, then "
        "return to the case. Use Level 2 or Level 3 only if you still need help."
    )
    how[3] = (
        "WRITE YOUR VERDICT BEFORE CHECKING. Solutions come after the Hint Vault and explain why the "
        "case closes. Use a solution only after you have committed to an answer."
    )
    data["opening"]["how_to_play"] = how
    return data, cases, master, runtime


def chapter_gate_v31(c, title, subtitle, rank, page_no):
    if str(rank).upper() == "ACT I":
        subtitle = "Five field detectives. One archive mentor. One empty field badge is waiting for you."
    panel_h = 4.15 * inch
    c.setFillColor(rb.BLACK)
    c.rect(rb.M, rb.PAGE_H - panel_h, rb.PAGE_W - 2 * rb.M, panel_h - 18, fill=1, stroke=0)
    rb.tiny_grid(c, rb.PAGE_W - rb.M - 30, rb.PAGE_H - panel_h, 30, panel_h - 18, step=20)
    rb.label(c, "ACADEMY ACCESS // NEW LEVEL", rb.M + 14, rb.PAGE_H - 0.80 * inch, color=rb.WHITE)
    rb.para(c, title.upper(), rb.M + 14, rb.PAGE_H - 1.55 * inch,
            rb.PAGE_W - 2 * rb.M - 150, 68, size=27, font=rb.BOLD, color=rb.WHITE)

    # Integrated act badge replaces the detached/floating circle from V3.
    badge_w, badge_h = 118, 78
    badge_x = rb.PAGE_W - rb.M - badge_w - 14
    badge_y = rb.PAGE_H - 2.20 * inch
    c.setStrokeColor(rb.WHITE)
    c.setLineWidth(1.4)
    c.roundRect(badge_x, badge_y, badge_w, badge_h, 10, fill=0, stroke=1)
    c.setFillColor(rb.WHITE)
    c.setFont(rb.MONO, 9.5)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 53, "CASE ARC")
    c.setFont(rb.BOLD, 21)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 24, str(rank).upper())

    rb.text_card(c, subtitle, rb.M, rb.PAGE_H - 3.80 * inch, rb.PAGE_W - 2 * rb.M,
                 heading="WHAT CHANGES NOW", size=12.5, fill=rb.PALE2)
    rb.label(c, "STATUS: MISSIONS UNLOCKED", rb.M, 0.68 * inch)
    rb.footer(c, page_no)
    c.showPage()


def certificate_page_v31(c, data, page_no):
    rb.top_bar(c, "DETECTIVE ACADEMY", page_no, 1.0)
    y = rb.PAGE_H - 1.05 * inch
    rb.para(c, "CASE CLOSED.", rb.M, y, rb.PAGE_W - 2 * rb.M, 0.58 * inch,
            size=27, font=rb.BOLD, align=1)
    rb.para(c, "ROOM ZERO // CLEARED", rb.M, y - 0.55 * inch, rb.PAGE_W - 2 * rb.M,
            0.38 * inch, size=11, font=rb.MONO, align=1)
    y -= 1.35 * inch
    rb.box(c, rb.M, y - 3.55 * inch, rb.PAGE_W - 2 * rb.M, 3.35 * inch,
           fill=rb.PALE2, stroke=rb.BLACK, radius=18, sw=1.2)
    rb.para(c, "DETECTIVE ACADEMY CERTIFICATE", rb.M + 0.25 * inch, y - 0.52 * inch,
            rb.PAGE_W - 2 * rb.M - 0.50 * inch, 0.42 * inch, size=17, font=rb.BOLD, align=1)
    rb.para(c, "Awarded to", rb.M + 0.25 * inch, y - 1.04 * inch,
            rb.PAGE_W - 2 * rb.M - 0.50 * inch, 0.30 * inch, size=11, align=1)
    c.setStrokeColor(rb.BLACK)
    c.setLineWidth(1.0)
    c.line(rb.M + 0.95 * inch, y - 1.65 * inch, rb.PAGE_W - rb.M - 0.95 * inch, y - 1.65 * inch)
    rb.para(c, "for closing THE MYSTERY OF ROOM ZERO by following the evidence and making the final call.",
            rb.M + 0.45 * inch, y - 2.03 * inch, rb.PAGE_W - 2 * rb.M - 0.90 * inch,
            0.62 * inch, size=11, align=1)
    rb.para(c, "STATUS // ACADEMY MEMBER", rb.M + 0.45 * inch, y - 2.84 * inch,
            rb.PAGE_W - 2 * rb.M - 0.90 * inch, 0.38 * inch, size=12, font=rb.BOLD, align=1)
    y -= 3.92 * inch
    rb.box(c, rb.M, y - 0.92 * inch, rb.PAGE_W - 2 * rb.M, 0.82 * inch,
           fill=rb.BLACK, stroke=rb.BLACK, radius=12)
    rb.para(c, "YOUR FIELD BADGE // SLOT 06", rb.M + 0.16 * inch, y - 0.27 * inch,
            rb.PAGE_W - 2 * rb.M - 0.32 * inch, 0.32 * inch,
            size=13, font=rb.BOLD, color=rb.WHITE, align=1)
    rb.footer(c, page_no)
    c.showPage()


def map_page_v31(c, mission, map_path, page_no, case=None, solution=False):
    """V3 map page with an explicit safe gap between rule copy and coordinates."""
    rb.top_bar(c, "SOLUTION MAP" if solution else "LIVE CASE MAP", page_no)
    top = rb.PAGE_H - 58
    number = mission.get("number", int(case["id"].split("_")[-1]) if case else 0)
    c.setFillColor(rb.BLACK)
    c.setFont(rb.BOLD, 10)
    c.drawString(rb.M, top, f"CASE {number:02d}  /  {str(mission.get('rank', '')).upper()}")
    rb.para(c, html.escape(mission["title"]), rb.M, top - 13, rb.PAGE_W - 2 * rb.M,
            46, size=18, font=rb.BOLD)

    key = "One person per row and column. Use each witness clue."
    if case and not solution:
        allowed = sorted({("desk chair" if o["type"] == "deskchair" else o["display_label"])
                          for o in case.get("objects", []) if o.get("occupiable")})
        key = "One person per row and column. Usable: empty floor; " + ", ".join(allowed) + ". Other objects block squares."
    if solution:
        key = "  |  ".join(f"{index:02d} = {p['display_name']}"
                            for index, p in enumerate(case.get("characters", []), 1))

    rb.label(c, "MAP RULES / WITNESS KEY", rb.M, top - 62, size=10)
    key_h = rb.text_height(html.escape(key), rb.PAGE_W - 2 * rb.M, 11)
    rule_top = top - 75
    rb.para(c, html.escape(key), rb.M, rule_top, rb.PAGE_W - 2 * rb.M, key_h + 1, size=11)
    rule_bottom = rule_top - key_h

    # draw_grid places column letters 10pt above grid_top. V3 left only ~3pt
    # after the rule paragraph; V3.1 guarantees a 16pt text-to-coordinate gap.
    grid_top = rule_bottom - 26
    bottom, _, _ = draw_grid(c, map_path, case, grid_top, 6.45 * inch)
    verdict_card(c, bottom - 48, case.get("source_answer") if solution else None)
    rb.footer(c, page_no)
    c.showPage()


def _visual_header(c, m, page_no, progress, label="VISUAL EVIDENCE"):
    rb.top_bar(c, label, page_no, progress)
    y = rb.PAGE_H - 0.88 * inch
    rb.pill(c, f"CASE {m['number']:02d} // EVIDENCE", rb.M, y - 12, 9.5, fill=rb.CHARCOAL, h=21)
    title_h = rb.text_height(m["title"], rb.PAGE_W - 2 * rb.M, 17.5, rb.BOLD)
    rb.para(c, m["title"], rb.M, y - 31, rb.PAGE_W - 2 * rb.M, title_h + 1, size=17.5, font=rb.BOLD)
    objective_top = y - 42 - title_h
    used = rb.text_card(c, m["objective"], rb.M, objective_top, rb.PAGE_W - 2 * rb.M,
                        heading="YOUR TASK", size=11.2, stroke=rb.BLACK)
    return objective_top - used - 18


def _case03(c, m, page_no, progress):
    y = _visual_header(c, m, page_no, progress, "PHOTO COMPARISON")
    gap = 18
    w = (rb.PAGE_W - 2 * rb.M - gap) / 2
    h = 280
    for idx, label in enumerate(("PHOTO A // 14:32:08", "PHOTO B // 14:32:51")):
        x = rb.M + idx * (w + gap)
        rb.box(c, x, y - h, w, h, fill=rb.PALE2, stroke=rb.BLACK, radius=5)
        rb.label(c, label, x + 10, y - 20, size=9.5)
        # poster stars (decoy)
        c.setFont(rb.BOLD, 10)
        c.drawString(x + 12, y - 52, "POSTER: " + ("★ ★ ★" if idx == 0 else "★ ★ ★ ★"))
        # parcel + ribbon knot + evidence tag
        px, py, pw, ph = x + 40, y - 170, w - 80, 82
        c.setStrokeColor(rb.BLACK); c.setLineWidth(1.2); c.rect(px, py, pw, ph, fill=0, stroke=1)
        knot_x = px + 12 if idx == 0 else px + pw - 12
        c.circle(knot_x, py + ph / 2, 6, fill=0, stroke=1)
        c.line(px + pw / 2, py, px + pw / 2, py + ph)
        c.setFont(rb.MONO, 11)
        c.drawCentredString(px + pw / 2, py + ph / 2 - 4, "TAG 0417" if idx == 0 else "TAG 0471")
        # footprint direction; door is on the right
        fy = y - 218
        c.setFont(rb.BOLD, 9.5); c.drawRightString(x + w - 11, fy + 20, "DOOR")
        c.line(x + w - 18, fy - 10, x + w - 18, fy + 12)
        start = x + 84 if idx == 0 else x + 55
        end = x + 44 if idx == 0 else x + w - 42
        c.setLineWidth(2.0); c.line(start, fy, end, fy)
        direction = -1 if idx == 0 else 1
        tip = end
        c.line(tip, fy, tip - 8 * direction, fy + 5)
        c.line(tip, fy, tip - 8 * direction, fy - 5)
        # cup and pencil (decoys)
        c.rect(x + 15, y - 258, 22, 18, fill=0, stroke=1)
        if idx == 0: c.line(x + 37, y - 253, x + 45, y - 250)
        else: c.line(x + 15, y - 253, x + 7, y - 250)
        pshift = 0 if idx == 0 else 18
        c.line(x + 80 + pshift, y - 250, x + 130 + pshift, y - 250)
    rule = m.get("visual", {}).get("relevance_rule", "Compare identity, tag and travel direction; decorative changes are not evidence.")
    rb.text_card(c, rule, rb.M, y - h - 16, rb.PAGE_W - 2 * rb.M,
                 heading="EVIDENCE RULE", size=10.8, stroke=rb.BLACK)
    rb.footer(c, page_no); c.showPage()


def _route_row(c, x, top, w, route_id, nodes, note=None, wall=False):
    rb.box(c, x, top - 82, w, 74, fill=rb.WHITE, stroke=rb.LINE, radius=8)
    rb.label(c, f"ROUTE {route_id}", x + 10, top - 24, size=10)
    inner_x = x + 74
    usable_w = w - 88
    step = usable_w / max(1, len(nodes) - 1)
    cy = top - 43
    for i, node in enumerate(nodes):
        nx = inner_x + i * step
        if i:
            c.setStrokeColor(rb.BLACK); c.setLineWidth(1.2); c.line(nx - step + 20, cy, nx - 20, cy)
        c.setFillColor(rb.PALE2); c.setStrokeColor(rb.BLACK)
        c.roundRect(nx - 20, cy - 13, 40, 26, 5, fill=1, stroke=1)
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD, 7.3)
        short = node.replace("COSTUME STORAGE", "COSTUME").replace("PAINT CORRIDOR", "PAINT").replace("PROP ROOM", "PROP").replace("STAFF STAIRS", "STAIRS").replace("SIDE HALL", "SIDE HALL")
        c.drawCentredString(nx, cy - 2.5, short[:12])
    if wall:
        wx = inner_x + step * 1.45
        c.setStrokeColor(rb.BLACK); c.setLineWidth(3)
        c.line(wx, cy - 19, wx, cy + 19)
        c.setFont(rb.BOLD, 7.5); c.drawCentredString(wx, cy + 24, "WALL")
    if note:
        c.setFillColor(rb.BLACK); c.setFont(rb.MONO, 8.4); c.drawRightString(x + w - 10, top - 68, note)


def _case08(c, m, page_no, progress):
    y = _visual_header(c, m, page_no, progress, "ROUTE EVIDENCE")
    rb.label(c, "CURRENT TIME // 16:20", rb.M, y, size=10); y -= 14
    route = m["route"]
    notes = {
        "A": "PAINT CORRIDOR CLOSED UNTIL 16:30",
        "B": "STAFF DOOR LOCKED",
        "C": "NO CLOSURE LISTED",
    }
    for opt in route["options"]:
        _route_row(c, rb.M, y, rb.PAGE_W - 2 * rb.M, opt["id"], opt["path"],
                   note=notes[opt["id"]], wall=(opt["id"] == "B"))
        y -= 88
    rb.writing_card(c, "YOUR CHOICE // A, B OR C + ONE REASON", rb.M, y - 2,
                    rb.PAGE_W - 2 * rb.M, 82)
    rb.footer(c, page_no); c.showPage()


def _evidence_card(c, x, top, w, item_id, item, stamp, icon="card"):
    rb.box(c, x, top - 106, w, 98, fill=rb.PALE2, stroke=rb.BLACK, radius=8)
    rb.label(c, f"RECORD {item_id}", x + 10, top - 23, size=9.5)
    c.setStrokeColor(rb.BLACK); c.setLineWidth(1.2)
    if icon == "phone":
        c.roundRect(x + 12, top - 87, 35, 52, 6, fill=0, stroke=1)
        c.line(x + 18, top - 43, x + 41, top - 43)
    else:
        c.rect(x + 12, top - 79, 38, 35, fill=0, stroke=1)
        c.line(x + 17, top - 61, x + 45, top - 61)
    rb.para(c, html.escape(item), x + 60, top - 38, w - 72, 35, size=10.5, font=rb.BOLD)
    rb.para(c, html.escape(stamp), x + 60, top - 72, w - 72, 28, size=9.5, font=rb.MONO)


def _case11(c, m, page_no, progress):
    y = _visual_header(c, m, page_no, progress, "EVIDENCE BAG")
    data = m["classification"]
    rb.box(c, rb.M, y - 37, rb.PAGE_W - 2 * rb.M, 35, fill=rb.BLACK, stroke=rb.BLACK, radius=6)
    rb.para(c, f"CASE WINDOW // {data['case_window']}", rb.M + 10, y - 11,
            rb.PAGE_W - 2 * rb.M - 20, 20, size=10.5, font=rb.BOLD, color=rb.WHITE)
    y -= 55
    cards = data["items"][:4]
    gap = 14; w = (rb.PAGE_W - 2 * rb.M - gap) / 2
    for i, item in enumerate(cards):
        col = i % 2; row = i // 2
        _evidence_card(c, rb.M + col * (w + gap), y - row * 114, w,
                       item["id"], item["item"], item["label"],
                       icon="phone" if item["id"] == "D" else "card")
    y -= 238
    rb.label(c, "OTHER BAG CONTENTS // NOT PART OF TIMESTAMP SET A-D", rb.M, y, size=9.5)
    y -= 18
    others = data["items"][4:]
    ow = (rb.PAGE_W - 2 * rb.M - 20) / 3
    for i, item in enumerate(others):
        x = rb.M + i * (ow + 10)
        rb.box(c, x, y - 48, ow, 44, fill=rb.WHITE, stroke=rb.LINE, radius=6)
        rb.label(c, f"{item['id']} // {item['item'].upper()}", x + 8, y - 19, size=8.5)
        rb.para(c, item["label"], x + 8, y - 26, ow - 16, 16, size=8.5)
    rb.writing_card(c, "WHICH TIMESTAMPED RECORD A-D FALLS OUTSIDE THE WINDOW?", rb.M, y - 62,
                    rb.PAGE_W - 2 * rb.M, 72)
    rb.footer(c, page_no); c.showPage()


def _footprint(c, cx, cy, shade, arrow="EAST"):
    gray = max(0.08, min(0.90, 1.0 - shade / 120.0))
    fill = colors.Color(gray, gray, gray)
    c.setFillColor(fill); c.setStrokeColor(rb.BLACK); c.setLineWidth(1.0)
    c.ellipse(cx - 22, cy - 39, cx + 22, cy + 30, fill=1, stroke=1)
    for dx in (-10, 0, 10):
        c.circle(cx + dx, cy + 31, 4, fill=1, stroke=1)
    c.setStrokeColor(rb.WHITE if gray < 0.50 else rb.BLACK); c.setLineWidth(2)
    c.line(cx - 10, cy - 3, cx + 10, cy - 3)
    c.line(cx + 10, cy - 3, cx + 3, cy + 3)
    c.line(cx + 10, cy - 3, cx + 3, cy - 9)


def _case24(c, m, page_no, progress):
    y = _visual_header(c, m, page_no, progress, "TRACK EVIDENCE")
    seq = m["visual_sequence"]
    rb.text_card(c, seq["rule"], rb.M, y, rb.PAGE_W - 2 * rb.M,
                 heading="CONTROLLED-TRACK RULE", size=10.8, stroke=rb.BLACK)
    y -= 82
    positions = ["WEST GATE", "P2", "P3", "EAST PATH"]
    by_pos = {p["position"]: p for p in seq["prints"]}
    gap = 10; w = (rb.PAGE_W - 2 * rb.M - gap * 3) / 4
    for i, pos in enumerate(positions):
        x = rb.M + i * (w + gap)
        rb.box(c, x, y - 216, w, 206, fill=rb.PALE2, stroke=rb.BLACK, radius=8)
        rb.para(c, pos, x + 5, y - 22, w - 10, 24, size=9.3, font=rb.BOLD, align=1)
        p = by_pos[pos]
        _footprint(c, x + w / 2, y - 100, p["mud"], p["tread_arrow"])
        rb.para(c, f"MUD TRANSFER {p['mud']}", x + 5, y - 162, w - 10, 20,
                size=8.8, font=rb.MONO, align=1)
        rb.para(c, f"TREAD ARROW {p['tread_arrow']}", x + 5, y - 184, w - 10, 18,
                size=8.1, align=1)
    rb.writing_card(c, "REAL DIRECTION OF TRAVEL // FROM __________ TO __________", rb.M,
                    y - 232, rb.PAGE_W - 2 * rb.M, 82)
    rb.footer(c, page_no); c.showPage()


def structured_puzzle_page_v31(c, data, m, page_no, progress):
    n = int(m["number"])
    if n == 3:
        return _case03(c, m, page_no, progress)
    if n == 8:
        return _case08(c, m, page_no, progress)
    if n == 11:
        return _case11(c, m, page_no, progress)
    if n == 24:
        return _case24(c, m, page_no, progress)
    return ORIG_STRUCTURED(c, data, m, page_no, progress)


def artifact_page_v31(c, data, m, page_no):
    if int(m["number"]) != 16:
        return ORIG_ARTIFACT(c, data, m, page_no)

    rb.top_bar(c, "PHYSICAL EVIDENCE", page_no)
    y = rb.PAGE_H - 0.90 * inch
    rb.para(c, "CASE 16 // DATE THE ARCHIVE PHOTOGRAPH", rb.M, y,
            rb.PAGE_W - 2 * rb.M, 38, size=19, font=rb.BOLD)
    y -= 54

    # Actual evidence composition: photo, plaque, dated sticker, badge style,
    # processing envelope and candidate boxes all appear on-page.
    photo_x, photo_w, photo_h = rb.M, rb.PAGE_W - 2 * rb.M, 292
    rb.box(c, photo_x, y - photo_h, photo_w, photo_h, fill=colors.HexColor("#E7E7E7"),
           stroke=rb.BLACK, radius=5)
    rb.box(c, photo_x + 18, y - 62, photo_w - 36, 42, fill=rb.WHITE, stroke=rb.BLACK, radius=3)
    rb.para(c, "OLD ACADEMY CREST // TRAINING ANNEX", photo_x + 28, y - 33,
            photo_w - 56, 20, size=11.5, font=rb.BOLD, align=1)
    rb.box(c, photo_x + 24, y - 121, 205, 42, fill=rb.WHITE, stroke=rb.BLACK, radius=3)
    rb.para(c, "SECURITY UPGRADE COMPLETED 2001", photo_x + 32, y - 92,
            189, 20, size=9.2, font=rb.MONO)

    # Five children in the archival photo, each with a visible striped badge.
    base_y = y - 220
    for i in range(5):
        cx = photo_x + 82 + i * 89
        c.setStrokeColor(rb.BLACK); c.setLineWidth(1.1)
        c.circle(cx, base_y + 65, 18, fill=0, stroke=1)
        c.line(cx, base_y + 47, cx, base_y - 1)
        c.line(cx, base_y + 30, cx - 18, base_y + 12)
        c.line(cx, base_y + 30, cx + 18, base_y + 12)
        c.line(cx, base_y - 1, cx - 14, base_y - 27)
        c.line(cx, base_y - 1, cx + 14, base_y - 27)
        bx, by = cx + 9, base_y + 22
        c.rect(bx, by, 19, 13, fill=0, stroke=1)
        for off in (4, 9, 14): c.line(bx + off, by, bx + off - 5, by + 13)
    rb.label(c, "ARCHIVE RULE // STRIPED BADGES: OFFICIAL EVENTS 1999-2003",
             photo_x + 22, y - photo_h + 16, size=9.0)

    y -= photo_h + 16
    gap = 14; left_w = (photo_w - gap) * 0.58; right_w = photo_w - gap - left_w
    rb.box(c, rb.M, y - 96, left_w, 90, fill=rb.WHITE, stroke=rb.BLACK, radius=6)
    rb.label(c, "PHOTO LAB ENVELOPE", rb.M + 10, y - 24, size=9.5)
    rb.para(c, "EXPIRES 2004", rb.M + 10, y - 42, left_w - 20, 26, size=18, font=rb.MONO, align=1)
    rb.para(c, "PROCESSING LOG // USED BEFORE EXPIRY", rb.M + 10, y - 71,
            left_w - 20, 16, size=8.5, font=rb.BOLD, align=1)
    rx = rb.M + left_w + gap
    rb.box(c, rx, y - 96, right_w, 90, fill=rb.PALE2, stroke=rb.BLACK, radius=6)
    rb.label(c, "RECORD NOTE", rx + 10, y - 24, size=9.5)
    rb.para(c, "Photograph taken after the 2001 security sticker was installed.",
            rx + 10, y - 39, right_w - 20, 42, size=9.5)

    rb.writing_card(c, "BUILDING:  OLD ACADEMY ANNEX  /  CITY LIBRARY  /  NORTH STATION",
                    rb.M, y - 112, rb.PAGE_W - 2 * rb.M, 55)
    rb.writing_card(c, "YEAR:  1998  /  2002  /  2008", rb.M, y - 176,
                    rb.PAGE_W - 2 * rb.M, 55)
    rb.footer(c, page_no); c.showPage()


def install_patches():
    v3.build_data = build_data_v31
    v3.map_page = map_page_v31
    rb.chapter_gate = chapter_gate_v31
    rb.certificate_page = certificate_page_v31
    rb.structured_puzzle_page = structured_puzzle_page_v31
    v3.artifact_page = artifact_page_v31


def main():
    install_patches()
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True, type=Path)
    ap.add_argument("--runtime", required=True, type=Path)
    ap.add_argument("--maps", required=True, type=Path)
    ap.add_argument("--overrides", default=ROOT / "content/book1_v3_overrides.yml", type=Path)
    ap.add_argument("--aliases", default=ROOT / "content/spatial_character_aliases.yml", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    data, cases, master, runtime = v3.build_data(
        args.master.resolve(), args.runtime.resolve(), args.maps.resolve(),
        args.overrides.resolve(), args.aliases.resolve(), args.output.resolve()
    )
    pages, index = v3.render_v3(data, cases, master, args.output.resolve())
    sha = hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    index_path = args.output.resolve().parent / "HMDA_Book1_EN_OwnerReview_v31_page_index.json"
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"PASS: V3.1 bounded owner-review correction rendered, {pages} pages")
    print(f"SHA256: {sha}")


if __name__ == "__main__":
    main()
