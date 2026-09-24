#!/usr/bin/env python3
"""Build the definitive HMDA Book 1 V3 owner-review candidate."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import yaml
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import render_book as rb
from render_spatial_case_spreads import witness_board
from spatial_presentation import draw_grid, map_page


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def replace_tokens(value, names):
    if isinstance(value,str):
        pattern=r"\b("+"|".join(re.escape(k) for k in sorted(names,key=len,reverse=True))+r")\b"
        return re.sub(pattern,lambda m:names[m.group(0).lower()],value,flags=re.I)
    if isinstance(value,list): return [replace_tokens(v,names) for v in value]
    if isinstance(value,dict): return {k:replace_tokens(v,names) for k,v in value.items()}
    return value


def copyright_page(c,data,page):
    rb.top_bar(c,"COPYRIGHT / IMPRINT",page)
    y=rb.PAGE_H-1.15*inch
    rb.para(c,"HAPPY MAKERS DETECTIVE ACADEMY",rb.M,y,rb.PAGE_W-2*rb.M,40,size=19,font=rb.BOLD)
    y-=58
    copy=(
        "Copyright © [YEAR] [RIGHTS HOLDER]. All rights reserved.<br/><br/>"
        "Written and produced by Rise.Shine.Evolve. [IMPRINT / PUBLISHER ADDRESS TO BE CONFIRMED].<br/><br/>"
        "No part of this publication may be reproduced or distributed without permission, except brief "
        "quotations for review. Names and case situations are fictional. Printed in [COUNTRY].<br/><br/>"
        "Edition: English owner-review V3 &nbsp;&nbsp; ISBN: [TO BE ASSIGNED]"
    )
    rb.text_card(c,copy,rb.M,y,rb.PAGE_W-2*rb.M,heading="PUBLICATION RECORD",size=11.5,fill=rb.WHITE,stroke=rb.BLACK)
    rb.para(c,"Legal placeholders remain intentionally open for owner approval before publication.",rb.M,1.2*inch,rb.PAGE_W-2*rb.M,36,size=11,color=rb.BLACK)
    rb.footer(c,page); c.showPage()


def invitation_page(c,data,page):
    rb.top_bar(c,"THE INVITATION",page)
    o=data["opening"]["acceptance_letter"]
    x=rb.M; w=rb.PAGE_W-2*x; top=rb.PAGE_H-62
    # Closed envelope and flap.
    rb.box(c,x,top-126,w,112,fill=rb.BLACK,stroke=rb.BLACK,radius=10)
    c.setStrokeColor(rb.WHITE); c.setLineWidth(1.5)
    c.line(x+8,top-22,x+w/2,top-87); c.line(x+w-8,top-22,x+w/2,top-87)
    c.setFillColor(rb.WHITE); c.setFont(rb.BOLD,12); c.drawCentredString(rb.PAGE_W/2,top-104,"0 // FOR THE PERSON HOLDING THIS BOOK")
    # Unfolded letter.
    letter_top=top-150
    rb.box(c,x+18,letter_top-382,w-36,370,fill=rb.WHITE,stroke=rb.BLACK,radius=2,sw=1.1)
    rb.label(c,"UNFOLDED LETTER // INTAKE PRINTER 00:01",x+36,letter_top-38,size=9.5)
    rb.para(c,o["headline"],x+36,letter_top-61,w-72,58,size=20,font=rb.BOLD)
    used=rb.text_height(o["body"],w-72,11.5)
    rb.para(c,o["body"],x+36,letter_top-126,w-72,used+1,size=11.5)
    y=letter_top-145-used
    c.setStrokeColor(rb.LINE); c.line(x+36,y,x+w-36,y); y-=20
    rb.para(c,o["note"],x+36,y,w-72,92,size=11.5,font=rb.BOLD)
    rb.footer(c,page); c.showPage()


def signal_page(c,data,m,page,progress):
    s=m["signal_log"]
    rb.top_bar(c,"SIGNAL LOG",page,progress)
    y=rb.PAGE_H-0.95*inch
    rb.pill(c,f"{s['code']} // CASE {m['number']:02d}",rb.M,y-12,9.5,fill=rb.BLACK,h=21)
    rb.para(c,s["label"],rb.M,y-47,rb.PAGE_W-2*rb.M,48,size=22,font=rb.BOLD)
    y-=112
    rb.box(c,rb.M,y-138,rb.PAGE_W-2*rb.M,126,fill=rb.BLACK,stroke=rb.BLACK,radius=14)
    c.setFillColor(rb.WHITE); c.setFont(rb.BOLD,42); c.drawString(rb.M+18,y-75,"0")
    c.setFont(rb.BOLD,14); c.drawString(rb.M+88,y-48,s["status"])
    c.setFont(rb.MONO,9.5); c.drawString(rb.M+88,y-76,"ACADEMY INTAKE / VERIFIED CONTEXT")
    y-=170
    rb.avatar_callout(c,data["characters"],s["speaker"],s["reaction"],rb.M,y,rb.PAGE_W-2*rb.M)
    y-=104
    rb.text_card(c,s["reader_move"],rb.M,y,rb.PAGE_W-2*rb.M,heading="YOUR MOVE // SIGNAL LOG",size=11.5,stroke=rb.BLACK)
    rb.label(c,f"READER STATUS // {m.get('reader_stage','DETECTIVE')}",rb.M,62,size=10)
    rb.footer(c,page); c.showPage()


def parity_pause(c,data,m,page):
    rb.top_bar(c,"FIELD PAUSE // PREP THE BOARD",page)
    y=rb.PAGE_H-1.0*inch
    rb.para(c,"SET UP CASE %02d"%m["number"],rb.M,y,rb.PAGE_W-2*rb.M,50,size=24,font=rb.BOLD)
    y-=75
    rb.text_card(c,"The Witness Board and Live Case Map begin on the next facing spread. Read the rules before the grid, number the witnesses in roster order, and keep this page for rough eliminations.",rb.M,y,rb.PAGE_W-2*rb.M,heading="SPREAD READY",size=12,stroke=rb.BLACK)
    rb.writing_card(c,"ROUGH ELIMINATIONS / QUESTIONS",rb.M,4.45*inch,rb.PAGE_W-2*rb.M,2.25*inch)
    rb.avatar_callout(c,data["characters"],m["guides"][0],"A pause is part of the solve. Set the board before you chase the clever clue.",rb.M,1.80*inch,rb.PAGE_W-2*rb.M)
    rb.footer(c,page); c.showPage()


def solution_page(c,mission,case,image,page):
    rb.top_bar(c,f"SOLUTION // CASE {mission['number']:02d}",page)
    width=rb.PAGE_W-2*rb.M
    rb.para(c,html.escape(mission["title"]),rb.M,rb.PAGE_H-54,width,44,size=17,font=rb.BOLD)
    bottom,_,_=draw_grid(c,image,case,rb.PAGE_H-108,5.75*72)
    legend="  |  ".join(f"{i:02d} {p['display_name']}" for i,p in enumerate(case["characters"],1))
    lh=rb.text_height(legend,width,11)
    rb.para(c,legend,rb.M,bottom-8,width,lh+1,size=11)
    y=bottom-lh-24
    answer=case["source_answer"]
    answer_source=answer.get("source_name",answer.get("name"))
    answer_index=next(i for i,p in enumerate(case["characters"],1) if p["source_name"]==answer_source)
    rb.label(c,f"VERDICT: {answer_index:02d} — {answer['display_name']} — {answer['coordinate']}",rb.M,y,size=12)
    y-=20; rb.label(c,"HOW THE CASE FALLS INTO PLACE",rb.M,y,size=10); y-=11
    steps=mission["solution_steps"]; split=(len(steps)+1)//2; colw=(width-22)/2
    for col,items in enumerate((steps[:split],steps[split:])):
        ty=y
        for idx,step in enumerate(items,1+col*split):
            used=rb.text_height(f"<b>{idx:02d}</b>  "+html.escape(step),colw,11)
            rb.para(c,f"<b>{idx:02d}</b>  "+html.escape(step),rb.M+col*(colw+22),ty,colw,used+1,size=11)
            ty-=used+7
    rb.footer(c,page); c.showPage()


def hint_vault(c,data,missions,page):
    # Level-major navigation: finish all Level 1 pages before Level 2 or 3.
    for level in range(3):
        for offset in (0,15):
            group=missions[offset:offset+15]
            rb.top_bar(c,f"HINT VAULT // LEVEL {level+1}",page)
            y=rb.PAGE_H-0.88*inch
            rb.para(c,f"LEVEL {level+1} // CASES {offset+1:02d}-{offset+len(group):02d}",rb.M,y,rb.PAGE_W-2*rb.M,32,size=18.5,font=rb.BOLD)
            y-=42
            note=("A small direction. Stop here if the case moves." if level==0 else
                  "A stronger constraint. Return to the case before Level 3." if level==1 else
                  "The decisive next step. The final verdict is still yours.")
            rb.para(c,note,rb.M,y,rb.PAGE_W-2*rb.M,24,size=11); y-=28
            for m in group:
                hints=m.get("hints") or [m.get("nudge","")]*3
                text_h=rb.text_height(hints[level],rb.PAGE_W-2*rb.M-48,11)
                h=max(34,text_h+8)
                if y-h<35: raise ValueError(f"Hint Vault Level {level+1}: page overflow at Case {m['number']}")
                rb.box(c,rb.M,y-h,rb.PAGE_W-2*rb.M,h,fill=rb.WHITE if m["number"]%2 else rb.PALE2,stroke=rb.LINE,radius=5)
                rb.label(c,f"{m['number']:02d}",rb.M+9,y-21,size=10)
                rb.para(c,hints[level],rb.M+38,y-5,rb.PAGE_W-2*rb.M-48,text_h+1,size=11)
                y-=h+2
            rb.footer(c,page); c.showPage(); page+=1
    return page


def artifact_page(c,data,m,page):
    rb.top_bar(c,"PHYSICAL EVIDENCE",page)
    y=rb.PAGE_H-0.9*inch
    rb.para(c,f"CASE {m['number']:02d} // EVIDENCE YOU CAN TEST",rb.M,y,rb.PAGE_W-2*rb.M,38,size=19,font=rb.BOLD)
    y-=58
    if m["number"]==16:
        rb.box(c,rb.M,y-330,rb.PAGE_W-2*rb.M,320,fill=rb.PALE2,stroke=rb.BLACK,radius=4)
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,15); c.drawCentredString(rb.PAGE_W/2,y-45,"TRAINING ANNEX")
        c.setFont(rb.MONO,10); c.drawString(rb.M+25,y-78,"SECURITY UPGRADE COMPLETED 2001")
        for i in range(5):
            cx=rb.M+75+i*92; cy=y-175
            c.circle(cx,cy,26,fill=0,stroke=1); c.line(cx,cy-26,cx,cy-75)
            c.setFont(rb.BOLD,11); c.drawCentredString(cx,cy-94,f"BADGE {i+1:02d}")
        rb.text_card(c,"ARCHIVE RULE: striped badges were worn at official events only, 1999-2003. Processing log: photograph made after the 2001 sticker and before the envelope's 2004 expiry.",rb.M,y-350,rb.PAGE_W-2*rb.M,heading="DATE THE PHOTO",size=11.5,stroke=rb.BLACK)
    elif m["number"]==21:
        scraps=m["reconstruction"]["scraps"]
        positions=[(rb.M+10,y-90),(rb.M+270,y-90),(rb.M+80,y-255),(rb.M+335,y-255)]
        for scrap,(x,top) in zip(scraps,positions):
            pts=[(x,top),(x+205,top-8),(x+195,top-116),(x+8,top-108)]
            c.setFillColor(rb.WHITE); c.setStrokeColor(rb.BLACK); c.polygon if False else None
            p=c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close()
            c.drawPath(p,fill=1,stroke=1)
            c.setFillColor(rb.BLACK)
            c.setFont(rb.BOLD,11); c.drawString(x+12,top-25,f"SCRAP {scrap['id']}")
            c.setFont(rb.BOLD,15); c.drawCentredString(x+103,top-68,scrap["text"])
            c.setFont(rb.MONO,9.5); c.drawString(x+12,top-97,f"{scrap['left_edge']}  ->  {scrap['right_edge']}")
        rb.writing_card(c,"FINAL SCRAP ORDER / MESSAGE",rb.M,2.05*inch,rb.PAGE_W-2*rb.M,1.25*inch)
    else:
        overlay=m["map_overlay"]; cols=overlay["grid"]["columns"]; rows=overlay["grid"]["rows"]
        gap=18; gw=(rb.PAGE_W-2*rb.M-gap)/2; gh=300
        for side,label in enumerate(("OLD PLAN","CURRENT PLAN")):
            x=rb.M+side*(gw+gap); top=y-25
            rb.label(c,label,x,top,size=11); top-=16
            c.setStrokeColor(rb.BLACK); c.rect(x,top-gh,gw,gh,fill=0,stroke=1)
            for i in range(1,cols): c.line(x+i*gw/cols,top-gh,x+i*gw/cols,top)
            for i in range(1,rows): c.line(x,top-i*gh/rows,x+gw,top-i*gh/rows)
            cells=overlay["old_room_cells"] if side==0 else overlay["current_archive_wall_cells"]
            c.setFillColor(colors.HexColor("#D9D9D9"))
            for cell in cells:
                col=ord(cell[0])-65; row=int(cell[1:])-1
                c.rect(x+col*gw/cols,top-(row+1)*gh/rows,gw/cols,gh/rows,fill=1,stroke=0)
            c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,9.5)
            for a in overlay["anchors"]:
                cell=a["old_cell"] if side==0 else a["current_cell"]
                col=ord(cell[0])-65; row=int(cell[1:])-1
                short={"NORTH STAIR":"STAIR","COURTYARD COLUMN":"COLUMN","WEST LIFT SHAFT":"LIFT"}[a["old"]]
                c.drawCentredString(x+(col+.5)*gw/cols,top-(row+.55)*gh/rows,short)
            room_label="SEALED TRAINING\nROOM" if side==0 else "ARCHIVE WALL\nNO DOOR"
            rb.para(c,room_label,x+3*gw/cols,top-1.78*gh/rows,2*gw/cols,56,size=10,font=rb.BOLD,align=1)
        rb.text_card(c,overlay["transform"],rb.M,2.08*inch,rb.PAGE_W-2*rb.M,heading="ALIGNMENT RULE",size=11.5,stroke=rb.BLACK)
    rb.footer(c,page); c.showPage()


def build_data(master_path,runtime_path,maps_path,overrides_path,aliases_path,output):
    data=load(master_path); overrides=load(overrides_path); runtime=json.loads(runtime_path.read_text(encoding="utf-8"))
    aliases=load(aliases_path)["cases"]
    data["book"].update(overrides["book"]); data["opening"].update(overrides["opening"])
    data["v3"]=copy.deepcopy(overrides)
    data["production_state"].update(owner_review_version=3,english_frozen=False,witness_marker_mode="numeric",
                                     aliases="content/spatial_character_aliases.yml",spatial_assets_attached=True)
    cases={case["id"]:case for case in runtime["cases"]}
    for cid,case in cases.items():
        mapping=aliases[cid]
        for index,person in enumerate(case["characters"],1):
            person["display_name"]=mapping[person["source_name"]]
            person["witness_id"]=f"{index:02d}"
        ans=case["source_answer"]
        answer_source=ans.get("source_name",ans.get("name"))
        ans["display_name"]=mapping[answer_source]
        ans["witness_id"]=next(p["witness_id"] for p in case["characters"] if p["source_name"]==answer_source)
    stages=sorted((int(k),v) for k,v in overrides["reader_arc"].items())
    for i,mission in enumerate(data["missions"]):
        number=int(mission["number"])
        mission.update(copy.deepcopy(overrides["cases"][number]))
        mission["reader_stage"]=max((name for start,name in stages if start<=number),key=lambda _: [s for s,_ in stages if s<=number][-1] if False else 0)
        # Above max is intentionally replaced below with an ordered scan for YAML portability.
        for start,name in stages:
            if start<=number: mission["reader_stage"]=name
        cid=mission.get("spatial_source_id")
        if not cid: continue
        case=cases[cid]
        names={p["source_name"].lower():p["display_name"] for p in case["characters"]}
        updated=replace_tokens(copy.deepcopy(mission),names)
        rooms={r["source_name"].lower():r["final_name"] for r in case["rooms"]}
        rooms.update({r["final_name"].lower():r["final_name"] for r in case["rooms"]})
        for field in ("spatial_copy","hints","nudge","solution_steps"):
            if field in updated: updated[field]=replace_tokens(updated[field],rooms)
        sp=updated.setdefault("spatial",copy.deepcopy(updated.get("spatial_copy",{})))
        for mode,key in (("puzzle","source_page_asset"),("solution","solution_asset")):
            asset=maps_path/f"{cid}_{mode}_original_shigai_relabelled.png"
            if not asset.is_file(): raise FileNotFoundError(asset)
            sp[key]=asset.relative_to(ROOT).as_posix()
        sp.update(puzzle_asset=sp["source_page_asset"],crop=None,solution_crop=None,
                  rows=case["grid"]["rows"],columns=case["grid"]["columns"])
        data["missions"][i]=updated
    out_master=output.parent/"book1_en_master_owner_review_v3.yml"
    out_runtime=output.parent/"hmda_spatial_runtime_v3.json"
    out_master.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True,width=110),encoding="utf-8")
    out_runtime.write_text(json.dumps(runtime,indent=2,ensure_ascii=False),encoding="utf-8")
    return data,cases,out_master,out_runtime


def render_v3(data,cases,master_path,output):
    rb.ROOT=ROOT
    output.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(output),pagesize=(rb.PAGE_W,rb.PAGE_H),pageCompression=1)
    c.setTitle(f"{data['book']['title']} — {data['book']['subtitle']}")
    c.setAuthor("Rise.Shine.Evolve.")
    c.setSubject(data["book"]["pdf_subject"]); c.setKeywords(data["book"]["pdf_keywords"])
    rb.title_page(c,data); page=2
    copyright_page(c,data,page); page+=1
    invitation_page(c,data,page); page+=1
    rb.squad_page(c,data,page); page+=1
    original_rule=data["book"]["rule_zero"]; data["book"]["rule_zero"]=data["book"]["rule_zero_teaser"]
    rb.how_to_play_page(c,data,page); page+=1; data["book"]["rule_zero"]=original_rule
    rb.detective_id_page(c,data,page); page+=1
    rb.chapter_gate(c,"SOMETHING IS OFF","Five detectives. Six badge hooks. One intake signal that should be asleep.","ACT I",page); page+=1
    missions=data["missions"]; page_index={}
    m=missions[0]; prog=.07; page_index["01_brief"]=page
    rb.mission_brief_page(c,data,m,page,prog); page+=1
    rb.guided_puzzle_page(c,data,m,page,prog); page+=1
    rb.guided_steps_page(c,data,m,page,prog); page+=1
    rb.verdict_reveal_page(c,data,m,page,prog); page+=1
    signal_page(c,data,m,page,prog); page_index["01_signal"]=page; page+=1
    spine={int(b["after_case"]):b for b in data["story_spine"]["beats"]}
    compact=set(data["v3"]["production"]["compact_cases"]); artifacts=set(data["v3"]["production"]["artifact_cases"])
    structured={"route","classification","consistency","timeline","timeline-visual","reconstruction","visual-sequence","room-zero-checkpoint","map-overlay","fact-theory-sort","multi-stage-finale"}
    original_cards=rb._structured_cards
    def cards_with_signal(mission):
        cards,note=original_cards(mission)
        if mission.get("number") in compact:
            s=mission["signal_log"]
            note=f"SIGNAL LOG // {s['code']} // {s['status']} — {s['reaction']}"
        return cards,note
    rb._structured_cards=cards_with_signal
    for m in missions[1:]:
        n=int(m["number"]); prog=min(.98,.07+n*.030); typ=m.get("type")
        if typ in ("spatial","boss-spatial") and page%2==1:
            parity_pause(c,data,m,page); page_index[f"{n:02d}_parity_pause"]=page; page+=1
        page_index[f"{n:02d}_brief"]=page
        if typ in ("spatial","boss-spatial"):
            witness_board(c,m,cases[m["spatial_source_id"]],page)
        else: rb.mission_brief_page(c,data,m,page,prog)
        page+=1
        if typ in ("spatial","boss-spatial"):
            cid=m["spatial_source_id"]; map_page(c,m,ROOT/m["spatial"]["source_page_asset"],page,cases[cid]); page_index[f"{n:02d}_map"]=page; page+=1
        elif typ=="visual": rb.visual_puzzle_page(c,data,m,page,prog); page+=1
        elif typ=="code": rb.code_puzzle_page(c,data,m,page,prog); page+=1
        else: rb.structured_puzzle_page(c,data,m,page,prog); page+=1
        if n in artifacts:
            artifact_page(c,data,m,page); page_index[f"{n:02d}_artifact"]=page; page+=1
        if typ=="multi-stage-finale":
            rb.finale_reveal_page(c,data,m,page); page+=1
            rb.certificate_page(c,data,page); page+=1
        # At act boundaries the Evidence Wall carries the same case-specific
        # signal, avoiding a duplicate transition page.
        if n not in compact and n not in spine:
            signal_page(c,data,m,page,prog); page_index[f"{n:02d}_signal"]=page; page+=1
        if n in spine:
            beat=copy.deepcopy(spine[n]); s=m["signal_log"]
            beat["eyebrow"]=f"SIGNAL LOG // {s['code']} // {beat['eyebrow']}"
            beat["progress"]=f"{s['status']} // {beat['progress']}"
            rb.big_case_wall_page(c,data,beat,page); page_index[f"{n:02d}_act"]=page; page+=1
    page=hint_vault(c,data,missions,page)
    for m in missions:
        cid=m.get("spatial_source_id")
        if cid:
            solution_page(c,m,cases[cid],ROOT/m["spatial"]["solution_asset"],page)
        else:
            page=rb.solutions_pages(c,data,[m],page)-1
        page_index[f"{int(m['number']):02d}_solution"]=page; page+=1
    rb._structured_cards=original_cards
    c.save()
    (output.parent/"HMDA_Book1_EN_OwnerReview_v3_page_index.json").write_text(json.dumps(page_index,indent=2),encoding="utf-8")
    return page-1,page_index


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--master",required=True,type=Path)
    ap.add_argument("--runtime",required=True,type=Path)
    ap.add_argument("--maps",required=True,type=Path)
    ap.add_argument("--overrides",default=ROOT/"content/book1_v3_overrides.yml",type=Path)
    ap.add_argument("--aliases",default=ROOT/"content/spatial_character_aliases.yml",type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    data,cases,master,runtime=build_data(args.master.resolve(),args.runtime.resolve(),args.maps.resolve(),args.overrides.resolve(),args.aliases.resolve(),args.output.resolve())
    pages,index=render_v3(data,cases,master,args.output.resolve())
    sha=hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    print(f"PASS: V3 owner review rendered, {pages} pages")
    print(f"MASTER: {master}\nRUNTIME: {runtime}\nPDF: {args.output.resolve()}\nSHA256: {sha}")


if __name__=="__main__": main()
