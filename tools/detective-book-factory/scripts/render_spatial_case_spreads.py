#!/usr/bin/env python3
"""Render reusable HMDA Witness Board + Live Case Map pilot spreads.

This presentation layer reads canonical mission copy and validated runtime
aliases. It never edits a source clue, geometry, placement, or answer.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
import sys
sys.path.insert(0, str(ROOT))
import render_book as rb  # noqa: E402


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def alias_text(text: str, case: dict) -> str:
    result = html.escape(text)
    for person in sorted(case["characters"], key=lambda item: len(item["source_name"]), reverse=True):
        result = re.sub(
            rf"\b{re.escape(person['source_name'])}\b",
            f"<b>{person['display_name']}</b>", result, flags=re.IGNORECASE,
        )
    return result


def paragraph(c: Canvas, markup: str, x: float, top: float, width: float, height: float, size: float, *, bold=False, color=rb.BLACK, align=0):
    style = ParagraphStyle(
        "hmda", fontName=rb.BOLD if bold else rb.FONT, fontSize=size, leading=size * 1.25,
        textColor=color, alignment=align, spaceAfter=0,
    )
    p = Paragraph(markup, style)
    _, used = p.wrap(width, height)
    if used > height + 0.5:
        raise ValueError("Witness Board text overflow")
    p.drawOn(c, x, top - used)
    return used


def witness_board(c: Canvas, mission: dict, case: dict, page_no: int) -> None:
    rb.top_bar(c, "WITNESS BOARD // CASE FILE", page_no, 0.68)
    y = rb.PAGE_H - 0.80 * inch
    rank = mission["rank"].upper()
    rb.pill(c, f"CASE {mission['number']:02d} // {rank}", rb.M, y, 8.0, fill=rb.CHARCOAL)
    rb.pill(c, mission.get("status", "ACTIVE FILE"), rb.PAGE_W - rb.M - 1.65 * inch, y, 7.2, fill=rb.MID)
    paragraph(c, html.escape(mission["title"]), rb.M, y - 0.26 * inch, rb.PAGE_W - 2 * rb.M, 0.48 * inch, 17.5, bold=True)
    y -= 0.78 * inch

    rb.box(c, rb.M, y - 0.88 * inch, rb.PAGE_W - 2 * rb.M, 0.80 * inch, fill=rb.PALE2, stroke=rb.LINE, radius=12)
    c.setFillColor(rb.MID); c.setFont(rb.MONO, 7.0); c.drawString(rb.M + 0.14 * inch, y - 0.20 * inch, "CASE HOOK")
    paragraph(c, html.escape(mission["hook"]), rb.M + 0.14 * inch, y - 0.31 * inch, rb.PAGE_W - 2 * rb.M - 0.28 * inch, 0.43 * inch, 9.5)
    y -= 1.04 * inch

    rb.box(c, rb.M, y - 0.72 * inch, rb.PAGE_W - 2 * rb.M, 0.64 * inch, fill=rb.WHITE, stroke=rb.BLACK, radius=11)
    c.setFillColor(rb.MID); c.setFont(rb.MONO, 7.0); c.drawString(rb.M + 0.14 * inch, y - 0.20 * inch, "YOUR OBJECTIVE")
    paragraph(c, html.escape(mission["objective"]), rb.M + 0.14 * inch, y - 0.29 * inch, rb.PAGE_W - 2 * rb.M - 0.28 * inch, 0.30 * inch, 9.6, bold=True)
    y -= 0.88 * inch

    notes = mission.get("dialogue", [])[:3]
    if notes:
        note = "  ".join(f"{item['speaker'].upper()}: {item['text']}" for item in notes)
        rb.box(c, rb.M, y - 0.48 * inch, rb.PAGE_W - 2 * rb.M, 0.40 * inch, fill=rb.WHITE, stroke=rb.LINE, radius=9)
        paragraph(c, html.escape(note), rb.M + 0.14 * inch, y - 0.15 * inch, rb.PAGE_W - 2 * rb.M - 0.28 * inch, 0.20 * inch, 7.7, color=rb.MID)
        y -= 0.64 * inch

    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD, 10.5); c.drawString(rb.M, y, "WITNESS STATEMENTS")
    c.setFillColor(rb.MID); c.setFont(rb.MONO, 6.8); c.drawRightString(rb.PAGE_W-rb.M, y, "TICK EACH FACT YOU USE")
    y -= 0.16 * inch
    clues = mission["spatial_copy"]["clue_cards"]
    card_h = 0.49 * inch if len(clues) >= 8 else 0.55 * inch
    for index, clue in enumerate(clues, 1):
        top = y - (index - 1) * (card_h + 0.055 * inch)
        rb.box(c, rb.M, top-card_h, rb.PAGE_W-2*rb.M, card_h, fill=rb.WHITE if index % 2 else rb.PALE2, stroke=rb.LINE, radius=8)
        c.setStrokeColor(rb.MID); c.rect(rb.M+0.12*inch, top-0.28*inch, 11, 11, fill=0, stroke=1)
        c.setFillColor(rb.MID); c.setFont(rb.MONO, 6.3); c.drawString(rb.M+0.36*inch, top-0.17*inch, f"EVIDENCE {index:02d}")
        paragraph(c, alias_text(clue, case), rb.M+0.36*inch, top-0.26*inch, rb.PAGE_W-2*rb.M-0.52*inch, card_h-0.20*inch, 8.9)
    rb.box(c, rb.M, 0.54*inch, rb.PAGE_W-2*rb.M, 0.40*inch, fill=rb.BLACK, stroke=rb.BLACK, radius=9)
    paragraph(c, "FOLLOW THE EVIDENCE. DON'T GUESS.", rb.M+0.10*inch, 0.80*inch, rb.PAGE_W-2*rb.M-0.20*inch, 0.20*inch, 8.5, bold=True, color=rb.WHITE, align=TA_CENTER)
    rb.footer(c, page_no); c.showPage()


def map_page(c: Canvas, mission: dict, map_path: Path, page_no: int) -> None:
    rb.top_bar(c, "LIVE CASE MAP", page_no, 0.70)
    y=rb.PAGE_H-0.82*inch
    rb.pill(c, f"CASE {mission['number']:02d} // LIVE EVIDENCE", rb.M, y, 7.6, fill=rb.CHARCOAL)
    paragraph(c, html.escape(mission["title"]), rb.M, y-0.26*inch, rb.PAGE_W-2*rb.M, 0.42*inch, 16.0, bold=True)
    y -= 0.70*inch
    rb.box(c, rb.M, y-5.92*inch, rb.PAGE_W-2*rb.M, 5.82*inch, fill=rb.WHITE, stroke=rb.LINE, radius=12)
    image=map_path
    from PIL import Image
    img=Image.open(image); iw,ih=img.size
    scale=min((rb.PAGE_W-2*rb.M-0.18*inch)/iw, (5.64*inch)/ih)
    w,h=iw*scale,ih*scale
    c.drawImage(str(image), rb.PAGE_W/2-w/2, y-5.82*inch+(5.82*inch-h)/2, width=w, height=h)
    rb.box(c, rb.M, 0.54*inch, rb.PAGE_W-2*rb.M, 0.40*inch, fill=rb.WHITE, stroke=rb.BLACK, radius=9)
    paragraph(c, "YOUR VERDICT: ________________________________    COORDINATE: ______", rb.M+0.12*inch, 0.80*inch, rb.PAGE_W-2*rb.M-0.24*inch, 0.20*inch, 8.4, bold=True, align=TA_CENTER)
    rb.footer(c, page_no); c.showPage()


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--master", required=True, type=Path)
    ap.add_argument("--runtime", required=True, type=Path)
    ap.add_argument("--maps", required=True, type=Path)
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--out", required=True, type=Path)
    args=ap.parse_args()
    master=load_yaml(args.master); runtime=json.loads(args.runtime.read_text(encoding="utf-8"))
    cases={c["id"]:c for c in runtime["cases"]}
    missions={m.get("spatial_source_id"):m for m in master["missions"] if m.get("spatial_source_id")}
    selected=args.case or list(missions)
    args.out.mkdir(parents=True, exist_ok=True)
    for cid in selected:
        if cid not in cases or cid not in missions: raise SystemExit(f"Missing validated case/master copy: {cid}")
        map_path=args.maps/f"{cid}_puzzle_original_shigai_relabelled.png"
        if not map_path.is_file(): raise SystemExit(f"Missing map asset: {map_path}")
        out=args.out/f"{cid}_paired_spread.pdf"; c=Canvas(str(out), pagesize=(rb.PAGE_W, rb.PAGE_H))
        witness_board(c, missions[cid], cases[cid], 1); map_page(c, missions[cid], map_path, 2); c.save()
        print(f"PASS {cid}: {out}")

if __name__ == "__main__": main()
