#!/usr/bin/env python3
"""Render publication-safe HMDA spatial puzzle/solution pages from normalized runtime JSON.

Input is produced by scripts/extract_shigai_runtime.py from the locked native
Shigai checkpoint. This renderer does not alter geometry. It only applies the
RSE visual layer: grayscale room fields, final ROOM/ZONE names, object chips,
coordinates, and optional solution placements.

Outputs are private/generated assets by default and should not be committed to
a public repository unless the owner explicitly chooses to do so.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

PAGE_W = 2550
PAGE_H = 3300
MARGIN = 180
TOP_H = 210
BOTTOM_H = 220
INK = 18
MID = 92
LIGHT = 205
GRID = 120
ROOM_FILLS = [246, 235, 224, 242, 230, 218, 238, 228]
ZONE_FILL = 250


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def parse_cell(cell: str) -> tuple[int, int]:
    m = re.fullmatch(r"([A-Z]+)(\d+)", cell)
    if not m:
        raise ValueError(f"Invalid cell {cell!r}")
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - ord("A") + 1
    return col - 1, int(m.group(2)) - 1


def label_for_object(item: dict[str, Any]) -> str:
    raw = str(item.get("display_label") or item.get("type") or "object")
    words = raw.replace("_", " ").replace("-", " ").split()
    if len(words) <= 2 and len(raw) <= 16:
        return " ".join(words).upper()
    return "".join(w[0] for w in words[:4]).upper()


def fit_text(draw, text: str, box: tuple[int, int, int, int], max_size: int, min_size: int, bold=False):
    x0, y0, x1, y1 = box
    for size in range(max_size, min_size - 1, -1):
        f = font(size, bold=bold)
        bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=max(3, size // 5), align="center")
        if bbox[2] - bbox[0] <= x1 - x0 and bbox[3] - bbox[1] <= y1 - y0:
            return f
    return font(min_size, bold=bold)


def nearest_room_label_cell(cells: list[str]) -> str:
    pts = [parse_cell(c) for c in cells]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return min(cells, key=lambda c: (parse_cell(c)[0]-cx)**2 + (parse_cell(c)[1]-cy)**2)


def render(case: dict[str, Any], out: Path, solution: bool) -> None:
    rows = int(case["grid"]["rows"])
    cols = int(case["grid"]["columns"])
    img = Image.new("L", (PAGE_W, PAGE_H), 255)
    d = ImageDraw.Draw(img)

    # Header
    d.rectangle((0, 0, PAGE_W, 120), fill=INK)
    d.text((MARGIN, 34), "HAPPY MAKERS DETECTIVE ACADEMY", font=font(44, True), fill=255)
    right = "SOLUTION MAP" if solution else "DEDUCTION GRID"
    rb = d.textbbox((0,0), right, font=font(34, True))
    d.text((PAGE_W-MARGIN-(rb[2]-rb[0]), 42), right, font=font(34, True), fill=255)

    title = str(case.get("final_title") or case["id"]).upper()
    d.text((MARGIN, 160), f"{case['id']}  //  {title}", font=font(52, True), fill=INK)
    sub = "Use the witness clues. One person per row and one per column."
    if solution:
        ans = case.get("source_answer", {})
        sub = f"Verified source solution: {str(ans.get('name','')).upper()} @ {ans.get('coordinate','')}"
    d.text((MARGIN, 230), sub, font=font(28), fill=MID)

    # Grid geometry
    available_w = PAGE_W - 2*MARGIN
    available_h = PAGE_H - 430 - BOTTOM_H
    cell = min(available_w // cols, available_h // rows)
    gw, gh = cell*cols, cell*rows
    gx = (PAGE_W-gw)//2
    gy = 380

    # Room lookup
    room_for: dict[str, dict[str, Any]] = {}
    for idx, room in enumerate(case["rooms"]):
        room = dict(room)
        room["_fill"] = ROOM_FILLS[idx % len(ROOM_FILLS)] if room.get("kind") == "room" else ZONE_FILL
        for c in room["cells"]:
            room_for[c] = room

    # Fill cells
    for r in range(rows):
        for c in range(cols):
            cell_name = chr(ord("A")+c)+str(r+1)
            room = room_for[cell_name]
            x0, y0 = gx+c*cell, gy+r*cell
            d.rectangle((x0, y0, x0+cell, y0+cell), fill=room["_fill"])

    # Thin grid
    for c in range(cols+1):
        x = gx+c*cell
        d.line((x, gy, x, gy+gh), fill=GRID, width=2)
    for r in range(rows+1):
        y = gy+r*cell
        d.line((gx, y, gx+gw, y), fill=GRID, width=2)

    # Thick room boundaries
    for r in range(rows):
        for c in range(cols):
            name = chr(ord("A")+c)+str(r+1)
            room = room_for[name]
            x0, y0 = gx+c*cell, gy+r*cell
            neigh = [
                (c-1,r,(x0,y0,x0,y0+cell)),
                (c+1,r,(x0+cell,y0,x0+cell,y0+cell)),
                (c,r-1,(x0,y0,x0+cell,y0)),
                (c,r+1,(x0,y0+cell,x0+cell,y0+cell)),
            ]
            for nc,nr,line in neigh:
                other = None
                if 0 <= nc < cols and 0 <= nr < rows:
                    other = room_for[chr(ord("A")+nc)+str(nr+1)]
                if other is None or other["source_room_id"] != room["source_room_id"]:
                    d.line(line, fill=INK, width=8)

    # Coordinates
    for c in range(cols):
        txt = chr(ord("A")+c)
        bb=d.textbbox((0,0),txt,font=font(28,True))
        d.text((gx+c*cell+cell/2-(bb[2]-bb[0])/2, gy-44),txt,font=font(28,True),fill=INK)
    for r in range(rows):
        txt=str(r+1)
        bb=d.textbbox((0,0),txt,font=font(28,True))
        d.text((gx-44-(bb[2]-bb[0]), gy+r*cell+cell/2-(bb[3]-bb[1])/2),txt,font=font(28,True),fill=INK)

    # Room labels
    for room in case["rooms"]:
        target = nearest_room_label_cell(room["cells"])
        c,r = parse_cell(target)
        x0,y0=gx+c*cell,gy+r*cell
        label = str(room["final_name"]).upper()
        if room.get("kind") == "zone":
            label += "  // ZONE"
        f=fit_text(d,label,(x0+12,y0+12,x0+cell-12,y0+cell*0.35),max(18,cell//10),14,True)
        tb=d.multiline_textbbox((0,0),label,font=f,align="center")
        tw,th=tb[2]-tb[0],tb[3]-tb[1]
        px=x0+cell/2-tw/2
        py=y0+18
        d.rounded_rectangle((px-8,py-4,px+tw+8,py+th+5),radius=8,fill=255,outline=LIGHT,width=2)
        d.multiline_text((px,py),label,font=f,fill=INK,align="center",spacing=2)

    # Objects
    objects_by_cell: dict[str, list[dict[str, Any]]] = {}
    for obj in case.get("objects", []):
        objects_by_cell.setdefault(obj["cell"], []).append(obj)
    for cell_name, objects in objects_by_cell.items():
        c,r=parse_cell(cell_name)
        x0,y0=gx+c*cell,gy+r*cell
        for j,obj in enumerate(objects[:2]):
            label=label_for_object(obj)
            h=max(26,int(cell*0.13))
            yy=y0+cell-h-10-j*(h+5)
            d.rounded_rectangle((x0+10,yy,x0+cell-10,yy+h),radius=8,fill=255,outline=INK if obj.get("blocked") else MID,width=3)
            f=fit_text(d,label,(x0+15,yy+2,x0+cell-15,yy+h-2),max(18,int(cell*0.08)),12,True)
            bb=d.textbbox((0,0),label,font=f)
            d.text((x0+cell/2-(bb[2]-bb[0])/2,yy+h/2-(bb[3]-bb[1])/2-2),label,font=f,fill=INK)
            if obj.get("blocked"):
                d.line((x0+16,yy+6,x0+30,yy+20),fill=MID,width=2)

    # Solution people
    if solution:
        for p in case.get("characters", []):
            cell_name=p["placement"]
            c,r=parse_cell(cell_name)
            x0,y0=gx+c*cell,gy+r*cell
            radius=max(25,int(cell*0.16))
            cx=x0+cell/2
            cy=y0+cell*0.50
            is_answer = p["source_name"] == case.get("source_answer",{}).get("name")
            d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=INK if is_answer else 255,outline=INK,width=5)
            initial=p["source_name"][0].upper()
            f=font(max(22,int(radius*0.9)),True)
            bb=d.textbbox((0,0),initial,font=f)
            d.text((cx-(bb[2]-bb[0])/2,cy-(bb[3]-bb[1])/2-3),initial,font=f,fill=255 if is_answer else INK)

    # Footer legend
    fy=gy+gh+55
    d.text((MARGIN,fy),"MAP KEY",font=font(28,True),fill=INK)
    d.text((MARGIN,fy+48),"ROOM = named solve space    ZONE = corridor/platform/queue, excluded from Room Zero meta",font=font(22),fill=MID)
    d.text((MARGIN,fy+86),"Object chip with corner slash = blocked cell. Plain chip = occupiable object.",font=font(22),fill=MID)
    if solution:
        names = "   ".join(f"{p['source_name'][0].upper()} = {p['source_name']}" for p in case.get("characters",[]))
        f=fit_text(d,names,(MARGIN,fy+125,PAGE_W-MARGIN,fy+180),30,17,False)
        d.text((MARGIN,fy+132),names,font=f,fill=INK)
        ans=case.get("source_answer",{})
        d.rounded_rectangle((MARGIN,fy+190,PAGE_W-MARGIN,fy+260),radius=16,fill=INK)
        verdict=f"VERDICT: {str(ans.get('name','')).upper()} @ {ans.get('coordinate','')}"
        bb=d.textbbox((0,0),verdict,font=font(32,True))
        d.text((PAGE_W/2-(bb[2]-bb[0])/2,fy+208),verdict,font=font(32,True),fill=255)

    img.convert("RGB").save(out, quality=96, dpi=(300,300))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--runtime", required=True, type=Path)
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--out", required=True, type=Path)
    args=ap.parse_args()

    data=json.loads(args.runtime.read_text(encoding="utf-8"))
    cases={c["id"]:c for c in data.get("cases",[])}
    selected=args.case or list(cases)
    args.out.mkdir(parents=True,exist_ok=True)

    for cid in selected:
        if cid not in cases:
            raise SystemExit(f"Unknown runtime case {cid}")
        case=cases[cid]
        puzzle=args.out/f"{cid}_puzzle.png"
        solution=args.out/f"{cid}_solution.png"
        render(case,puzzle,False)
        render(case,solution,True)
        print(f"{cid}: {puzzle} | {solution}")


if __name__=="__main__":
    main()
