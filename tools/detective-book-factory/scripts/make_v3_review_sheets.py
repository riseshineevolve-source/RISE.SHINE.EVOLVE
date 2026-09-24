#!/usr/bin/env python3
"""Build the owner-requested V3 review sheets from final full-page previews."""
from __future__ import annotations
import argparse,json,math,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

def font(size):
    p=Path("C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(p),size) if p.is_file() else ImageFont.load_default()

def sheets(name,title,pages,previews,out,per=12,cols=4):
    outputs=[]
    for start in range(0,len(pages),per):
        batch=pages[start:start+per]; tw=360; th=round(tw*792/612); gap=18; head=54; cap=28
        rows=math.ceil(len(batch)/cols)
        canvas=Image.new("RGB",(cols*(tw+gap)+gap,head+rows*(th+cap+gap)+gap),"white")
        draw=ImageDraw.Draw(canvas); draw.text((gap,12),title,fill="black",font=font(24))
        for i,page in enumerate(batch):
            img=Image.open(previews/f"page_{page:03d}.png").convert("RGB")
            tile=ImageOps.contain(img,(tw,th),Image.Resampling.LANCZOS)
            x=gap+(i%cols)*(tw+gap); y=head+(i//cols)*(th+cap+gap)
            canvas.paste(tile,(x,y)); draw.rectangle((x,y,x+tile.width,y+tile.height),outline="#888",width=1)
            draw.text((x,y+th+3),f"PAGE {page}",fill="black",font=font(18))
        path=out/f"{name}_{start//per+1:02d}.png"; canvas.save(path); outputs.append(path)
    return outputs

def object_sheet(report_path,map_dir,out):
    """Crop one real V3 map cell for every distinct spatial object type."""
    report=json.loads(report_path.read_text(encoding="utf-8")); first={}
    for check in report["checks"]:
        if check.get("role")=="puzzle": first.setdefault(check["object_type"],check)
    cols=7; cell_w=210; cell_h=220; gap=12; head=76; rows=math.ceil(len(first)/cols)
    canvas=Image.new("RGB",(cols*(cell_w+gap)+gap,head+rows*(cell_h+gap)+gap),"white")
    draw=ImageDraw.Draw(canvas); draw.text((gap,12),f"ALL DISTINCT SPATIAL OBJECT TYPES — {len(first)}",fill="black",font=font(26))
    draw.text((gap,44),"Cropped from the final V3 puzzle maps at actual occupied-cell bounds.",fill="black",font=font(16))
    for i,(name,check) in enumerate(sorted(first.items())):
        source=map_dir/f'{check["case"]}_puzzle_original_shigai_relabelled.png'
        with Image.open(source) as image:
            crop=image.convert("L").crop(tuple(check["bbox"]))
        crop=ImageOps.contain(crop,(174,158),Image.Resampling.LANCZOS)
        x=gap+(i%cols)*(cell_w+gap); y=head+(i//cols)*(cell_h+gap)
        draw.rectangle((x,y,x+cell_w,y+cell_h),fill="white",outline="#777",width=1)
        canvas.paste(crop,(x+(cell_w-crop.width)//2,y+8))
        lines=textwrap.wrap(name.replace("_"," ").upper(),20)[:2]
        for line_no,line in enumerate(lines):
            box=draw.textbbox((0,0),line,font=font(15)); tx=x+(cell_w-(box[2]-box[0]))//2
            draw.text((tx,y+172+line_no*18),line,fill="black",font=font(15))
        draw.text((x+7,y+204),f'{check["case"]} / {check["cell"]}',fill="#444",font=font(12))
    target=out/"map_object_types_01.png"; canvas.save(target); return target

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--index",required=True,type=Path); ap.add_argument("--previews",required=True,type=Path); ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--object-report",type=Path); ap.add_argument("--map-dir",type=Path)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True); idx=json.loads(a.index.read_text())
    briefs=[idx[f"{n:02d}_brief"] for n in range(1,31)]
    maps=[idx[f"{n:02d}_map"] for n in (2,4,6,7,10,12,13,15,17,19,20,22,23,25,29)]
    solutions=[idx[f"{n:02d}_solution"] for n in range(1,31)]
    hint_pages=list(range(min(solutions)-6,min(solutions)))
    finale=list(range(idx["30_brief"],idx["30_signal"]+1))
    visuals=[18,idx["16_artifact"],idx["21_artifact"],88,idx["27_artifact"]]
    groups=[
        ("opening","OPENING / RECRUITMENT / ONBOARDING",list(range(1,8)),8,4),
        ("all_30_cases","ALL 30 CASE OPENERS",briefs,10,5),
        ("all_15_spatial_maps","ALL 15 LIVE CASE MAPS",maps,8,4),
        ("all_15_witness_boards","ALL 15 WITNESS BOARDS",[p-1 for p in maps],8,4),
        ("modern_visual_evidence","MODERN VISUAL EVIDENCE",visuals,8,4),
        ("hint_vault","HINT VAULT — LEVEL MAJOR",hint_pages,8,4),
        ("solutions","ALL 30 SOLUTIONS",solutions,10,5),
        ("finale","ROOM ZERO FINALE",finale,8,4),
    ]
    count=0
    for name,title,pages,per,cols in groups:
        made=sheets(name,title,pages,a.previews,a.out,per,cols); count+=len(made)
        for path in made: print(path)
    if bool(a.object_report) != bool(a.map_dir): ap.error("--object-report and --map-dir must be supplied together")
    if a.object_report:
        path=object_sheet(a.object_report,a.map_dir,a.out); count+=1; print(path)
    print(f"PASS: {count} V3 review sheets")
if __name__=="__main__": main()
