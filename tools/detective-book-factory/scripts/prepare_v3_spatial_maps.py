#!/usr/bin/env python3
"""Create V3 map rasters with numeric witness markers.

Puzzle geometry and room art are copied byte-for-byte from the validated V2
Map Factory output. Only completed-map person markers are repainted from
letters to stable two-digit witness IDs in source-roster order.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arial.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def numeric_solution_markers(image: Image.Image, case: dict) -> Image.Image:
    image=image.convert("L")
    gray=np.asarray(image)
    draw=ImageDraw.Draw(image)
    rows,cols=int(case["grid"]["rows"]),int(case["grid"]["columns"])
    cw,ch=image.width/cols,image.height/rows
    for index,person in enumerate(case["characters"],1):
        col=ord(person["placement"][0])-65
        row=int(person["placement"][1:])-1
        x0,y0=round(col*cw),round(row*ch)
        roi=gray[y0:round((row+1)*ch),x0:round((col+1)*cw)]
        circles=cv2.HoughCircles(
            roi,cv2.HOUGH_GRADIENT,1.1,cw*.3,param1=100,param2=28,
            minRadius=round(cw*.1),maxRadius=round(cw*.23),
        )
        if circles is None:
            raise ValueError(f"{case['id']}: missing solution marker at {person['placement']}")
        mx,my,r=min(circles[0],key=lambda v:(v[0]/cw-.73)**2+(v[1]/ch-.27)**2)
        if ((mx/cw-.73)**2+(my/ch-.27)**2)**.5>.13:
            raise ValueError(f"{case['id']}: ambiguous solution marker at {person['placement']}")
        cx,cy=x0+float(mx),y0+float(my)
        radius=float(r)+2
        draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=255,outline=0,width=4)
        text=f"{index:02d}"
        face=font(max(16,round(cw*.15)))
        bb=draw.textbbox((0,0),text,font=face)
        draw.text((cx-(bb[2]-bb[0])/2-bb[0],cy-(bb[3]-bb[1])/2-bb[1]),text,font=face,fill=0)
    return image


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--runtime",required=True,type=Path)
    ap.add_argument("--source-maps",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    runtime=json.loads(args.runtime.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True,exist_ok=True)
    for case in runtime["cases"]:
        cid=case["id"]
        puzzle=args.source_maps/f"{cid}_puzzle_original_shigai_relabelled.png"
        solution=args.source_maps/f"{cid}_solution_original_shigai_relabelled.png"
        if not puzzle.is_file() or not solution.is_file():
            raise FileNotFoundError(f"{cid}: missing validated V2 map raster")
        shutil.copy2(puzzle,args.out/puzzle.name)
        numeric_solution_markers(Image.open(solution),case).save(args.out/solution.name,dpi=(300,300))
        print(f"PASS {cid}: puzzle preserved; solution markers 01-{len(case['characters']):02d}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
