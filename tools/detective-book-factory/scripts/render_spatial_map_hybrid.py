#!/usr/bin/env python3
"""Premium HMDA hybrid Map Factory.

Uses the ORIGINAL Shigai raster map as the scene/art layer, then applies the
canonical RSE / Room Zero naming and book framing without changing geometry.

Pipeline:
  locked source PDF -> SHA verification -> exact embedded page image
  -> detect map grid -> replace raw room labels with final RSE ROOM/ZONE names
  -> HMDA puzzle/solution page

The source PDF remains external/private. Only code, manifests and hashes live
in GitHub.

Usage:
  python scripts/render_spatial_map_hybrid.py \
    --source-pdf /private/HMDA_SHIGAI_SOURCE_15_MODULES_FINAL.pdf \
    --runtime /private/HMDA_BOOK1_RUNTIME.json \
    --case HMDA_02 --case HMDA_13 --case HMDA_29 \
    --out dist/map_factory_hybrid
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as canvas_module

HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]
sys.path.insert(0, str(TOOL_ROOT))
import render_book as rb  # noqa: E402


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise SystemExit(f"Invalid YAML mapping: {path}")
    return data


def load_runtime(path: Path) -> dict[str, Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("format")!="hmda-shigai-runtime":
        raise SystemExit("Runtime is not an hmda-shigai-runtime bundle.")
    return data


def contiguous_groups(values: np.ndarray) -> list[tuple[int,int]]:
    values=[int(v) for v in values]
    if not values:
        return []
    groups=[]
    start=prev=values[0]
    for value in values[1:]:
        if value==prev+1:
            prev=value
        else:
            groups.append((start,prev))
            start=prev=value
    groups.append((start,prev))
    return groups


def detect_grid_bbox(gray: np.ndarray) -> tuple[int,int,int,int]:
    """Find the heavy outer map border in the original Shigai raster."""
    h,w=gray.shape
    dark=gray<72

    y0,y1=int(h*0.16),int(h*0.97)
    col_fraction=dark[y0:y1,:].mean(axis=0)
    col_groups=[
        g for g in contiguous_groups(np.where(col_fraction>0.31)[0])
        if 2 <= g[1]-g[0]+1 <= int(w*0.04)
        and g[0] > int(w*0.02) and g[1] < int(w*0.98)
    ]
    if len(col_groups)<2:
        raise SystemExit("Could not detect Shigai grid outer vertical border.")
    left=col_groups[0][0]
    right=col_groups[-1][1]

    row_fraction=dark[:,left:right+1].mean(axis=1)
    row_groups=[
        g for g in contiguous_groups(np.where(row_fraction>0.31)[0])
        if 2 <= g[1]-g[0]+1 <= int(h*0.04)
        and g[0] > int(h*0.12) and g[1] < int(h*0.98)
    ]
    if len(row_groups)<2:
        raise SystemExit("Could not detect Shigai grid outer horizontal border.")
    top=row_groups[0][0]
    bottom=row_groups[-1][1]
    if right-left < w*0.45 or bottom-top < h*0.45:
        raise SystemExit(f"Implausible grid crop: {(left,top,right,bottom)}")
    return left,top,right,bottom


def detect_room_label_boxes(grid_gray: np.ndarray) -> list[tuple[int,int,int,int]]:
    """Detect Shigai's white rounded room-name pills, not furniture."""
    inv=cv2.threshold(grid_gray,120,255,cv2.THRESH_BINARY_INV)[1]
    contours,_=cv2.findContours(inv,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    h,w=grid_gray.shape
    candidates=[]
    for cnt in contours:
        x,y,bw,bh=cv2.boundingRect(cnt)
        if not (w*0.035 <= bw <= w*0.30 and h*0.012 <= bh <= h*0.055):
            continue
        if bw/max(bh,1) < 1.55:
            continue
        area=float(cv2.contourArea(cnt))
        rectangularity=area/max(1.0,float(bw*bh))
        if rectangularity < 0.82:
            continue
        roi=grid_gray[y:y+bh,x:x+bw]
        inset=max(2,int(min(bw,bh)*0.12))
        inner=roi[inset:bh-inset, inset:bw-inset]
        if inner.size==0:
            continue
        white_fraction=float((inner>220).mean())
        if white_fraction < 0.40:
            continue
        candidates.append((x,y,bw,bh,rectangularity,white_fraction))

    # One outer contour per pill. Collapse near-duplicates.
    candidates.sort(key=lambda r:(r[4],r[5],r[2]*r[3]),reverse=True)
    kept=[]
    for cand in candidates:
        x,y,bw,bh,*_=cand
        cx,cy=x+bw/2,y+bh/2
        duplicate=False
        for ox,oy,ow,oh in kept:
            ocx,ocy=ox+ow/2,oy+oh/2
            if abs(cx-ocx)<max(bw,ow)*0.20 and abs(cy-ocy)<max(bh,oh)*0.35:
                duplicate=True
                break
        if not duplicate:
            kept.append((x,y,bw,bh))
    return kept


def font(size: int, bold: bool=True) -> ImageFont.FreeTypeFont:
    candidates=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate,size=size)
    return ImageFont.load_default()


def room_for_point(case: dict[str,Any], x: float, y: float, grid_w: int, grid_h: int) -> dict[str,Any]:
    cols=int(case["grid"]["columns"])
    rows=int(case["grid"]["rows"])
    col=min(cols-1,max(0,int(x/(grid_w/cols))))
    row=min(rows-1,max(0,int(y/(grid_h/rows))))
    cell=f"{chr(ord('A')+col)}{row+1}"
    for room in case["rooms"]:
        if cell in room.get("cells",[]):
            return room
    raise SystemExit(f"{case['id']}: no room owns detected label cell {cell}")


def replace_room_labels(source: Image.Image, case: dict[str,Any], bbox: tuple[int,int,int,int]) -> Image.Image:
    """Replace raw Shigai room labels while leaving art/geometry untouched."""
    left,top,right,bottom=bbox
    grid=source.crop((left,top,right+1,bottom+1)).convert("RGB")
    gray=np.asarray(grid.convert("L"))
    boxes=detect_room_label_boxes(gray)

    assigned: dict[int,tuple[int,int,int,int]]={}
    for box in boxes:
        x,y,bw,bh=box
        room=room_for_point(case,x+bw/2,y+bh/2,grid.width,grid.height)
        rid=int(room["source_room_id"])
        previous=assigned.get(rid)
        if previous is None or bw*bh > previous[2]*previous[3]:
            assigned[rid]=box

    expected={int(room["source_room_id"]) for room in case["rooms"]}
    missing=sorted(expected-set(assigned))
    if missing:
        raise SystemExit(
            f"{case['id']}: could not safely identify original room labels for source room ids {missing}. "
            "Failing closed rather than damaging the verified map."
        )

    draw=ImageDraw.Draw(grid)
    for room in case["rooms"]:
        rid=int(room["source_room_id"])
        x,y,bw,bh=assigned[rid]
        final=str(room["final_name"]).upper()
        if room.get("kind")=="zone":
            final += " // ZONE"

        pad_x=max(8,int(bh*0.20))
        x0=max(0,x-pad_x)
        x1=min(grid.width,x+bw+pad_x)
        y0=max(0,y-int(bh*0.10))
        y1=min(grid.height,y+bh+int(bh*0.10))

        # Preserve nearby wall geometry by repainting only the old label footprint.
        draw.rounded_rectangle((x0,y0,x1,y1),radius=max(6,int(bh*0.22)),fill="white",outline=(20,20,20),width=max(2,int(bh*0.06)))
        max_size=max(14,int(bh*0.62))
        min_size=max(10,int(bh*0.34))
        chosen=font(min_size)
        for size in range(max_size,min_size-1,-1):
            f=font(size)
            tb=draw.textbbox((0,0),final,font=f)
            if tb[2]-tb[0] <= (x1-x0)-14 and tb[3]-tb[1] <= (y1-y0)-8:
                chosen=f
                break
        tb=draw.textbbox((0,0),final,font=chosen)
        tw,th=tb[2]-tb[0],tb[3]-tb[1]
        draw.text(((x0+x1-tw)/2,(y0+y1-th)/2-2),final,font=chosen,fill=(20,20,20))

    return grid


def extract_embedded_page_image(doc: fitz.Document, page_no: int) -> Image.Image:
    page=doc[page_no-1]
    info=page.get_image_info(xrefs=True)
    if len(info)!=1:
        raise SystemExit(f"Source PDF page {page_no}: expected exactly one embedded page image, found {len(info)}")
    base=doc.extract_image(info[0]["xref"])
    from io import BytesIO
    return Image.open(BytesIO(base["image"])).convert("RGB")


def fit_image(c, image_path: Path, x: float, y: float, w: float, h: float) -> None:
    img=Image.open(image_path)
    iw,ih=img.size
    scale=min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    c.drawImage(str(image_path),x+(w-dw)/2,y+(h-dh)/2,width=dw,height=dh,preserveAspectRatio=True,anchor='c')


def hybrid_page(c, case: dict[str,Any], map_path: Path, mode: str, page_no: int=1) -> None:
    is_solution=mode=="solution"
    rb.top_bar(c,"SOLUTION MAP" if is_solution else "DEDUCTION GRID",page_no,0.70)
    y=rb.PAGE_H-0.78*inch
    rb.pill(c,case["id"],rb.M,y,7.0,fill=rb.CHARCOAL)
    rb.para(c,str(case.get("final_title",case["id"])).upper(),rb.M,y-0.20*inch,rb.PAGE_W-2*rb.M,0.48*inch,size=16.6,font=rb.BOLD)
    y-=0.78*inch

    hero_h=5.95*inch
    rb.box(c,rb.M,y-hero_h,rb.PAGE_W-2*rb.M,hero_h,fill=rb.WHITE,stroke=rb.LINE,radius=12)
    fit_image(c,map_path,rb.M+0.10*inch,y-hero_h+0.10*inch,rb.PAGE_W-2*rb.M-0.20*inch,hero_h-0.20*inch)
    y-=hero_h+0.12*inch

    if is_solution:
        names="   ".join(f"{p['source_name'][0].upper()} = {p['source_name']}" for p in case.get("characters",[]))
        rb.fit_para(c,names,rb.M,y,rb.PAGE_W-2*rb.M,0.28*inch,max_size=7.4,min_size=5.4,align=1)
        y-=0.35*inch
        ans=case.get("source_answer",{})
        rb.box(c,rb.M,y-0.48*inch,rb.PAGE_W-2*rb.M,0.43*inch,fill=rb.BLACK,stroke=rb.BLACK,radius=9)
        rb.fit_para(c,f"VERDICT: {str(ans.get('name','')).upper()} @ {ans.get('coordinate','')}",
                    rb.M+0.10*inch,y-0.13*inch,rb.PAGE_W-2*rb.M-0.20*inch,0.22*inch,
                    max_size=9.4,min_size=7.0,font=rb.BOLD,color=rb.WHITE,align=1)
    else:
        rb.box(c,rb.M,y-0.48*inch,rb.PAGE_W-2*rb.M,0.43*inch,fill=rb.BLACK,stroke=rb.BLACK,radius=9)
        rb.fit_para(c,"USE THE WITNESS CLUES. WRITE YOUR VERDICT ONLY WHEN THE MAP EARNS IT.",
                    rb.M+0.10*inch,y-0.13*inch,rb.PAGE_W-2*rb.M-0.20*inch,0.22*inch,
                    max_size=8.4,min_size=6.4,font=rb.BOLD,color=rb.WHITE,align=1)

    rb.footer(c,page_no)
    c.showPage()


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-pdf",required=True,type=Path)
    ap.add_argument("--runtime",required=True,type=Path)
    ap.add_argument("--selection",default=TOOL_ROOT/"content"/"spatial_source_manifest_final.yml",type=Path)
    ap.add_argument("--case",action="append",default=[])
    ap.add_argument("--out",default=TOOL_ROOT/"dist"/"map_factory_hybrid",type=Path)
    args=ap.parse_args()

    source=args.source_pdf.expanduser().resolve()
    selection=load_yaml(args.selection.expanduser().resolve())
    expected_hash=str(selection["source"]["source_pdf_sha256"])
    actual_hash=sha256(source)
    if actual_hash!=expected_hash:
        raise SystemExit(f"BLOCKED: source PDF SHA mismatch. expected {expected_hash}, got {actual_hash}")

    runtime=load_runtime(args.runtime.expanduser().resolve())
    runtime_cases={c["id"]:c for c in runtime.get("cases",[])}
    declarations={c["id"]:c for c in selection.get("cases",[])}
    requested=args.case or list(declarations)
    out=args.out.expanduser().resolve()
    out.mkdir(parents=True,exist_ok=True)

    doc=fitz.open(source)
    for cid in requested:
        if cid not in declarations or cid not in runtime_cases:
            raise SystemExit(f"Unknown or unverified case {cid}")
        decl=declarations[cid]
        case=runtime_cases[cid]

        assets={}
        for mode,key in (("puzzle","puzzle_page"),("solution","solution_page")):
            page_no=int(decl["pdf"][key])
            original=extract_embedded_page_image(doc,page_no)
            gray=np.asarray(original.convert("L"))
            bbox=detect_grid_bbox(gray)
            relabeled=replace_room_labels(original,case,bbox)
            path=out/f"{cid}_{mode}_original_shigai_relabelled.png"
            relabeled.save(path,quality=96,dpi=(300,300))
            assets[mode]=path

        pdf_path=out/f"{cid}_hybrid_final.pdf"
        c=canvas_module.Canvas(str(pdf_path),pagesize=(rb.PAGE_W,rb.PAGE_H))
        hybrid_page(c,case,assets["puzzle"],"puzzle",1)
        hybrid_page(c,case,assets["solution"],"solution",2)
        c.save()
        print(f"PASS {cid}: original Shigai art retained; RSE room labels applied -> {pdf_path}")

if __name__=="__main__":
    main()
