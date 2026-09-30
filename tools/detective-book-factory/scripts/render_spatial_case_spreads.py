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
    rb.top_bar(c, "WITNESS BOARD // CASE FILE", page_no)
    x=rb.M; w=rb.PAGE_W-2*x; y=rb.PAGE_H-61
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,10)
    c.drawString(x,y,f"CASE {mission['number']:02d}  /  {mission['rank'].upper()}")
    c.drawRightString(rb.PAGE_W-x,y,"STATUS: OPEN")
    y-=14
    used=paragraph(c,html.escape(mission['title']),x,y,w,52,21,bold=True); y-=used+14
    used=paragraph(c,alias_text(mission['hook'],case),x,y,w,65,11.5); y-=used+15
    # One strong objective card, with evidence flowing down the dossier.
    obj=Paragraph(alias_text(mission['objective'],case),ParagraphStyle('objective',fontName=rb.BOLD,fontSize=11.5,leading=14.5))
    _,oh=obj.wrap(w-28,100)
    rb.box(c,x,y-oh-44,w,oh+44,fill=rb.WHITE,stroke=rb.BLACK,radius=11,sw=1.3)
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,10); c.drawString(x+14,y-19,'YOUR OBJECTIVE')
    obj.drawOn(c,x+14,y-30-oh); y-=oh+58
    roster='  |  '.join(f"{index:02d} {person['display_name']}" for index,person in enumerate(case['characters'],1))
    roster_h=paragraph(c,html.escape(roster),x,y,w,46,11,bold=True); y-=roster_h+12
    notes=mission.get('dialogue',[])
    if notes:
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,10)
        c.drawString(x,y,'HAPPY MAKERS CHAT')
        y-=15
        note='  '.join(f"{item['speaker'].upper()}: {item['text']}" for item in notes)
        used=paragraph(c,alias_text(note,case),x,y,w,65,11); y-=used+16
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,12); c.drawString(x,y,'WITNESS STATEMENTS')
    c.setFont(rb.FONT,10); c.drawRightString(rb.PAGE_W-x,y,'Tick each fact you use.')
    y-=16
    clues=mission['spatial_copy']['clue_cards']
    cards=[]
    for clue in clues:
        markup=alias_text(clue,case)
        for person in case['characters']:
            name=person['display_name']
            # Generated masters already contain aliases; bold those too.
            markup=re.sub(rf'(?<!>)\b{re.escape(name)}\b(?!</b>)',f'<b>{name}</b>',markup,flags=re.IGNORECASE)
        p=Paragraph(markup,ParagraphStyle('evidence',fontName=rb.FONT,fontSize=11.5,leading=14.5,textColor=rb.BLACK))
        _,height=p.wrap(w-82,100)
        cards.append((p,height+20))
    available=y-87
    needed=sum(h for _,h in cards)+5*(len(cards)-1)
    if needed>available: raise ValueError(f"Case {mission['number']}: evidence needs {needed:.1f}pt, has {available:.1f}pt")
    extra=min(9,(available-needed)/len(cards))
    for index,(p,h) in enumerate(cards,1):
        h+=extra
        rb.box(c,x,y-h,w,h,fill=rb.WHITE,stroke=rb.LINE,radius=8)
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,11); c.drawString(x+12,y-20,f'{index:02d}')
        p.drawOn(c,x+45,y-10-p.height)
        c.setStrokeColor(rb.BLACK); c.rect(x+w-24,y-h/2-5,10,10,fill=0,stroke=1)
        y-=h+5
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,11)
    c.drawString(x,58,"FOLLOW THE EVIDENCE. DON'T GUESS.")
    rb.footer(c,page_no); c.showPage()


def map_page(c: Canvas, mission: dict, map_path: Path, page_no: int, case=None) -> None:
    from spatial_presentation import map_page as draw_map
    draw_map(c,mission,map_path,page_no,case)


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
        witness_board(c, missions[cid], cases[cid], 1); map_page(c, missions[cid], map_path, 2, cases[cid]); c.save()
        print(f"PASS {cid}: {out}")

if __name__ == "__main__": main()
