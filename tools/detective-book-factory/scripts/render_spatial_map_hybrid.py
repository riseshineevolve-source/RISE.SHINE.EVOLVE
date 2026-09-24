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
import os
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
    # Short solution headers can put the real top border above the legacy
    # 12%-of-page cutoff. Require the complete square outer frame instead of
    # accepting an interior wall and silently dropping the first grid rows.
    outer_rows=[g for g in contiguous_groups(np.where(row_fraction>.85)[0])
                if 2<=g[1]-g[0]+1<=int(h*.04)]
    candidates=[]
    for upper in outer_rows:
        for lower in outer_rows:
            gh=lower[1]-upper[0]
            if abs(gh-(right-left))>max(5,(right-left)*.01): continue
            edge=dark[upper[0]:lower[1]+1,[left,right]].mean()
            if edge>.85: candidates.append((abs(gh-(right-left)),upper[0],lower[1]))
    if not candidates:
        raise SystemExit('Could not verify a complete square source-grid outer frame.')
    _,top,bottom=min(candidates)
    if right-left < w*0.45 or bottom-top < h*0.45:
        raise SystemExit(f"Implausible grid crop: {(left,top,right,bottom)}")
    return left,top,right,bottom


def detect_room_label_boxes(grid_gray: np.ndarray, broad: bool = False) -> list[tuple[int,int,int,int]]:
    """Detect Shigai's white rounded room-name pills, not furniture."""
    inv=cv2.threshold(grid_gray,120,255,cv2.THRESH_BINARY_INV)[1]
    contours,_=cv2.findContours(inv,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    h,w=grid_gray.shape
    candidates=[]
    for cnt in contours:
        x,y,bw,bh=cv2.boundingRect(cnt)
        min_w, max_w = (w*0.025, w*0.38) if broad else (w*0.035, w*0.30)
        min_h, max_h = (h*0.008, h*0.080) if broad else (h*0.012, h*0.055)
        if not (min_w <= bw <= max_w and min_h <= bh <= max_h):
            continue
        if bw/max(bh,1) < (1.25 if broad else 1.55):
            continue
        area=float(cv2.contourArea(cnt))
        rectangularity=area/max(1.0,float(bw*bh))
        if rectangularity < (0.68 if broad else 0.82):
            continue
        roi=grid_gray[y:y+bh,x:x+bw]
        inset=max(2,int(min(bw,bh)*0.12))
        inner=roi[inset:bh-inset, inset:bw-inset]
        if inner.size==0:
            continue
        white_fraction=float((inner>220).mean())
        if white_fraction < (0.32 if broad else 0.40):
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
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate,size=size)
    raise RuntimeError("A scalable print font is required; bitmap fallback makes map labels unreadable.")


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


def room_overlap_scores(case: dict[str, Any], box: tuple[int, int, int, int], grid_w: int, grid_h: int) -> dict[int, float]:
    """Score a detected pill against immutable runtime room masks.

    A source label may straddle a grid-cell boundary; its center is therefore
    not authoritative. The runtime topology is. Scores are exact rectangle
    overlap areas expressed in source-grid pixel coordinates.
    """
    x, y, bw, bh = box
    x2, y2 = x + bw, y + bh
    rows, cols = int(case["grid"]["rows"]), int(case["grid"]["columns"])
    scores: dict[int, float] = {int(room["source_room_id"]): 0.0 for room in case["rooms"]}
    for room in case["rooms"]:
        for cell in room["cells"]:
            match = re.fullmatch(r"([A-Z]+)(\d+)", cell)
            col = ord(match.group(1)) - ord("A")
            row = int(match.group(2)) - 1
            cx0, cy0 = col * grid_w / cols, row * grid_h / rows
            cx1, cy1 = (col + 1) * grid_w / cols, (row + 1) * grid_h / rows
            overlap = max(0.0, min(x2, cx1) - max(x, cx0)) * max(0.0, min(y2, cy1) - max(y, cy0))
            scores[int(room["source_room_id"])] += overlap
    return scores


def assign_room_by_overlap(case: dict[str, Any], box: tuple[int, int, int, int], grid_w: int, grid_h: int) -> tuple[int, float, float]:
    scores = room_overlap_scores(case, box, grid_w, grid_h)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_room, best = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    total = max(1.0, sum(scores.values()))
    # Require both substantial mask coverage and a non-trivial lead over the
    # next room. This prevents boundary-straddling pills from being guessed.
    if best / total < 0.60 or best - second < total * 0.18:
        raise ValueError(f"ambiguous overlap best={best_room}:{best/total:.2f}, second={second/total:.2f}")
    return best_room, best / total, second / total


def replace_room_labels(
    source: Image.Image,
    case: dict[str,Any],
    bbox: tuple[int,int,int,int],
    fallback_layout: dict[int, tuple[float,float,float,float]] | None = None,
) -> tuple[Image.Image, dict[int, tuple[float,float,float,float]]]:
    """Replace raw Shigai room labels while leaving art/geometry untouched."""
    left,top,right,bottom=bbox
    grid=source.crop((left,top,right+1,bottom+1)).convert("RGB")
    gray=np.asarray(grid.convert("L"))
    boxes=detect_room_label_boxes(gray)

    assigned: dict[int,tuple[int,int,int,int]]={}
    for box in boxes:
        x,y,bw,bh=box
        center_room=int(room_for_point(case,x+bw/2,y+bh/2,grid.width,grid.height)["source_room_id"])
        scores=room_overlap_scores(case, box, grid.width, grid.height)
        ranked=sorted(scores.items(), key=lambda item:item[1], reverse=True)
        try:
            rid, confidence, runner_up=assign_room_by_overlap(case, box, grid.width, grid.height)
        except ValueError as error:
            if os.environ.get("HMDA_LABEL_DIAGNOSTIC"):
                print(f"LABEL {case['id']} box={box} center={center_room} scores={ranked} REJECT {error}")
            continue
        if os.environ.get("HMDA_LABEL_DIAGNOSTIC"):
            print(f"LABEL {case['id']} box={box} center={center_room} scores={ranked} assign={rid} confidence={confidence:.2f}/{runner_up:.2f}")
        previous=assigned.get(rid)
        if previous is None or bw*bh > previous[2]*previous[3]:
            assigned[rid]=box

    expected={int(room["source_room_id"]) for room in case["rooms"]}
    missing=sorted(expected-set(assigned))

    # Only for still-missing rooms, inspect broader pill candidates. The
    # authoritative mask assignment and one-label-per-room rule remain intact;
    # this recovers clipped/expanded source contours without loosening the
    # primary detector globally.
    if missing:
        for box in detect_room_label_boxes(gray, broad=True):
            x,y,bw,bh=box
            try:
                rid, confidence, runner_up=assign_room_by_overlap(case, box, grid.width, grid.height)
            except ValueError:
                continue
            if rid not in missing or rid in assigned:
                continue
            assigned[rid]=box
            if os.environ.get("HMDA_LABEL_DIAGNOSTIC"):
                print(f"SECONDARY LABEL {case['id']} box={box} assign={rid} confidence={confidence:.2f}/{runner_up:.2f}")
        missing=sorted(expected-set(assigned))

    # Some solution pages place a label tight against the crop edge. Use the
    # puzzle page's normalized label position only for rooms that could not be
    # safely detected on the current page. Detected labels always win.
    if missing and fallback_layout:
        for rid in list(missing):
            if rid not in fallback_layout:
                continue
            nx,ny,nw,nh=fallback_layout[rid]
            assigned[rid]=(
                int(round(nx*grid.width)),
                int(round(ny*grid.height)),
                int(round(nw*grid.width)),
                int(round(nh*grid.height)),
            )
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
        # The source labels are sized for a smaller original page. This
        # presentation layer deliberately allocates a larger, bold print label
        # without moving a wall, object, cell, or source placement.
        max_size=max(20,int(bh*0.86))
        min_size=max(15,int(bh*0.52))
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

    normalized={
        rid:(x/grid.width,y/grid.height,bw/grid.width,bh/grid.height)
        for rid,(x,y,bw,bh) in assigned.items()
    }
    return grid, normalized


def extract_embedded_page_image(doc: fitz.Document, page_no: int) -> Image.Image:
    page=doc[page_no-1]
    invoked=re.findall(rb'/([A-Za-z0-9]+)\s+Do\b',page.read_contents())
    resources=page.get_images(full=True)
    matches=[item[0] for item in resources if len(invoked)==1 and item[7]==invoked[0].decode('ascii')]
    if len(matches)==1:
        xref=matches[0]
    else:
        info=page.get_image_info(xrefs=True)
        if len(info)!=1:
            raise SystemExit(f"Source PDF page {page_no}: expected exactly one embedded page image, found {len(info)}")
        xref=info[0]['xref']
    base=doc.extract_image(xref)
    from io import BytesIO
    return Image.open(BytesIO(base["image"])).convert("RGB")


def fit_image(c, image_path: Path, x: float, y: float, w: float, h: float) -> tuple[float,float,float,float]:
    img=Image.open(image_path)
    iw,ih=img.size
    scale=min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    px,py=x+(w-dw)/2,y+(h-dh)/2
    c.drawImage(str(image_path),px,py,width=dw,height=dh,preserveAspectRatio=True,anchor='c')
    return px,py,dw,dh


def alias_solution_markers(image: Image.Image, case: dict[str,Any]) -> Image.Image:
    """Replace source initials at detected markers inside the locked cells."""
    image=image.convert('L'); gray=np.asarray(image); draw=ImageDraw.Draw(image)
    rows,cols=int(case['grid']['rows']),int(case['grid']['columns'])
    cw,ch=image.width/cols,image.height/rows
    for person in case['characters']:
        col=ord(person['placement'][0])-65; row=int(person['placement'][1:])-1
        x0,y0=round(col*cw),round(row*ch)
        roi=gray[y0:round((row+1)*ch),x0:round((col+1)*cw)]
        circles=cv2.HoughCircles(roi,cv2.HOUGH_GRADIENT,1.1,cw*.3,param1=100,param2=28,minRadius=round(cw*.1),maxRadius=round(cw*.23))
        if circles is None: raise ValueError(f"{case['id']}: missing solution marker at {person['placement']}")
        mx,my,r=min(circles[0],key=lambda v:(v[0]/cw-.73)**2+(v[1]/ch-.27)**2)
        if ((mx/cw-.73)**2+(my/ch-.27)**2)**.5>.13:
            raise ValueError(f"{case['id']}: ambiguous solution marker at {person['placement']}")
        cx,cy=x0+float(mx),y0+float(my); r=float(r)+2
        draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=255,outline=0,width=4)
        text=person['display_name'][0].upper(); f=font(round(cw*.23)); bb=draw.textbbox((0,0),text,font=f)
        draw.text((cx-(bb[2]-bb[0])/2-bb[0],cy-(bb[3]-bb[1])/2-bb[1]),text,font=f,fill=0)
    return image


def coordinate_rail(c, case: dict[str, Any], x: float, y: float, w: float, h: float) -> None:
    """Place high-contrast, print-sized coordinates outside the preserved art."""
    rows=int(case["grid"]["rows"]); cols=int(case["grid"]["columns"])
    c.saveState()
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD, 16.0 if cols <= 7 else 14.0)
    for col in range(cols):
        c.drawCentredString(x+(col+0.5)*w/cols, y+h+14, chr(ord("A")+col))
    for row in range(rows):
        c.drawRightString(x-12, y+h-(row+0.60)*h/rows, str(row+1))
    c.restoreState()


def hybrid_page(c, case: dict[str,Any], map_path: Path, mode: str, page_no: int=1) -> None:
    from spatial_presentation import map_page
    mission = {'number': int(case['id'].split('_')[-1]), 'title': case['final_title'], 'rank': str(case.get('tier','')).replace('_',' ')}
    map_page(c, mission, map_path, page_no, case, solution=mode=='solution')


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
        fallback_layout=None
        for mode,key in (("puzzle","puzzle_page"),("solution","solution_page")):
            page_no=int(decl["pdf"][key])
            original=extract_embedded_page_image(doc,page_no)
            gray=np.asarray(original.convert("L"))
            bbox=detect_grid_bbox(gray)
            relabeled,label_layout=replace_room_labels(
                original,case,bbox,
                fallback_layout=fallback_layout if mode=="solution" else None,
            )
            if mode=="puzzle":
                fallback_layout=label_layout
            else:
                relabeled=alias_solution_markers(relabeled,case)
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
