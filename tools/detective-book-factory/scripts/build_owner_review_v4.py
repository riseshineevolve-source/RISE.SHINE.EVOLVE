#!/usr/bin/env python3
"""Build the definitive HMDA Book 1 V4 premier owner-review candidate.

V4 is a versioned composition layer.  It preserves every verified case answer
and spatial runtime while replacing the opening, evidence presentation,
navigation, finale and print QA contract requested by the owner.
"""
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


def publication_page(c,data,page):
    rb.top_bar(c,"PUBLICATION RECORD",page)
    y=rb.PAGE_H-1.15*inch
    rb.para(c,"HAPPY MAKERS DETECTIVE ACADEMY",rb.M,y,rb.PAGE_W-2*rb.M,40,size=19,font=rb.BOLD)
    y-=58
    pub=data.get("publication",{})
    copy=(f"{pub.get('copyright','© 2026 Rise.Shine.Evolve. All rights reserved.')}<br/><br/>"
          f"{pub.get('isbn','ISBN Paperback: ______')}<br/><br/>"
          f"{pub.get('rights','No part of this publication may be reproduced, stored in a retrieval system, or transmitted in any form or by any means without prior written permission from the publisher, except for brief quotations used in reviews.')}<br/><br/>"
          f"{pub.get('ai_disclosure','The development of this book was supported by AI-assisted tools.')}<br/><br/>"
          f"{pub.get('website','Website: Rise.Shine.Evolve')}<br/>{pub.get('facebook','Facebook: Rise.Shine.Evolve')}")
    rb.text_card(c,copy,rb.M,y,rb.PAGE_W-2*rb.M,heading="PUBLICATION RECORD",size=11.5,fill=rb.WHITE,stroke=rb.BLACK)
    rb.para(c,"English premier owner-review edition // Interior proof",rb.M,1.2*inch,rb.PAGE_W-2*rb.M,36,size=11,color=rb.BLACK)
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


def v4_title_page(c,data):
    b=data["book"]
    c.setFillColor(rb.BLACK); c.rect(rb.M,rb.PAGE_H-315,rb.PAGE_W-2*rb.M,297,fill=1,stroke=0)
    rb.tiny_grid(c,rb.PAGE_W-rb.M-42,rb.PAGE_H-315,42,297,step=21)
    rb.label(c,"ACADEMY INTAKE // FILE 001",rb.M+15,rb.PAGE_H-58,color=rb.WHITE)
    rb.para(c,b["title"],rb.M+15,rb.PAGE_H-86,rb.PAGE_W-2*rb.M-65,86,size=27,font=rb.BOLD,color=rb.WHITE)
    rb.para(c,b["subtitle"],rb.M+15,rb.PAGE_H-186,rb.PAGE_W-2*rb.M-65,48,size=18,font=rb.BOLD,color=rb.WHITE)
    rb.para(c,b["strapline"],rb.M+15,rb.PAGE_H-243,rb.PAGE_W-2*rb.M-65,32,size=10.5,color=rb.WHITE)
    y=rb.PAGE_H-350
    rb.label(c,"FIELD CERTIFICATION RACK",rb.M,y,size=10)
    y-=26; gap=10; w=(rb.PAGE_W-2*rb.M-gap*5)/6
    names=["MIMI","LULI","DILO","ALIO","NINI","YOU"]
    for i,name in enumerate(names):
        x=rb.M+i*(w+gap); empty=i==5
        rb.box(c,x,y-78,w,78,fill=rb.WHITE,stroke=rb.BLACK,radius=9,sw=1.2 if empty else .8)
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,12)
        c.drawCentredString(x+w/2,y-35,"?" if empty else f"{i+1:02d}")
        c.setFont(rb.BOLD,9.5); c.drawCentredString(x+w/2,y-61,name)
    rb.para(c,b.get("opening_code","THE ACADEMY HAS FIVE DETECTIVES. THE SIGNAL IS LOOKING FOR SIX."),rb.M,250,rb.PAGE_W-2*rb.M,72,size=18,font=rb.BOLD,align=1)
    rb.box(c,rb.M,95,rb.PAGE_W-2*rb.M,82,fill=rb.BLACK,stroke=rb.BLACK,radius=10)
    rb.para(c,"ONE HOOK IS EMPTY. ONE FILE HAS YOUR NAME LINE.",rb.M+15,146,rb.PAGE_W-2*rb.M-30,32,size=12,font=rb.BOLD,color=rb.WHITE,align=1)
    rb.para(c,"OPEN THE CASE.",rb.M+15,119,rb.PAGE_W-2*rb.M-30,24,size=10.5,color=rb.WHITE,align=1)
    c.showPage()


def academy_page(c,data,page):
    rb.top_bar(c,"YOUR SQUAD // THE ACADEMY",page)
    intro=data.get("opening",{}).get("academy_intro",{})
    y=rb.PAGE_H-65
    rb.para(c,intro.get("headline","FIVE FIELD DETECTIVES. ONE ARCHIVE MENTOR. ONE OPEN PLACE."),rb.M,y,rb.PAGE_W-2*rb.M,60,size=20,font=rb.BOLD); y-=72
    squad=ROOT/data["characters"]["squad"]["asset"]
    rb.box(c,rb.M,y-285,rb.PAGE_W-2*rb.M,285,fill=rb.WHITE,stroke=rb.BLACK,radius=10)
    rb.draw_image_fit(c,squad,rb.M+12,y-273,rb.PAGE_W-2*rb.M-24,261); y-=305
    body=intro.get("body",data["opening"].get("squad_intro",""))
    h=rb.text_height(body,rb.PAGE_W-2*rb.M,11.5)
    rb.para(c,body,rb.M,y,rb.PAGE_W-2*rb.M,h+1,size=11.5); y-=h+18
    for line in intro.get("chat",[])[:2]:
        text=f"<b>{data['characters'][line['speaker']]['name']}:</b> {html.escape(line['text'])}"
        h=rb.text_height(text,rb.PAGE_W-2*rb.M,11)
        rb.para(c,text,rb.M,y,rb.PAGE_W-2*rb.M,h+1,size=11); y-=h+7
    rb.label(c,"GRANDMA BIBI // ARCHIVE MENTOR // OUTSIDE THE SIX FIELD SLOTS",rb.M,60,size=9.5)
    rb.footer(c,page); c.showPage()


def character_page(c,data,page,cards,part):
    rb.top_bar(c,f"MEET THE HAPPY MAKERS // {part}",page)
    y=rb.PAGE_H-64
    for card in cards:
        key=card.get("speaker") or card.get("key")
        info=data["characters"][key]
        h=205
        rb.box(c,rb.M,y-h,rb.PAGE_W-2*rb.M,h,fill=rb.WHITE,stroke=rb.BLACK,radius=12)
        av=ROOT/"cache"/"avatars"/f"{key}.png"; rb.preprocess_avatar(ROOT/info["asset"],av)
        rb.draw_image_fit(c,av,rb.M+13,y-h+18,112,h-36)
        x=rb.M+140; tw=rb.PAGE_W-rb.M-x-14
        rb.para(c,card.get("name",info["name"]),x,y-18,tw,28,size=17,font=rb.BOLD)
        rb.label(c,card.get("role",info.get("tag","FIELD DETECTIVE")),x,y-49,size=9.5)
        ty=y-70
        lines=card.get("lines",[])
        if isinstance(lines,str): lines=[lines]
        for line in lines[:3]:
            hh=rb.text_height("• "+line,tw,10.5)
            rb.para(c,"• "+html.escape(line),x,ty,tw,hh+1,size=10.5); ty-=hh+5
        for label,value in (("STRENGTH",card.get("strength")),("FUNNY HABIT",card.get("funny_habit"))):
            if value:
                hh=rb.text_height(f"<b>{label}:</b> {html.escape(value)}",tw,10)
                rb.para(c,f"<b>{label}:</b> {html.escape(value)}",x,ty,tw,hh+1,size=10); ty-=hh+4
        y-=h+12
    rb.footer(c,page); c.showPage()


def detective_six_invitation(c,data,page):
    o=data["opening"].get("acceptance_letter",{})
    seq=data["opening"].get("sequence",[])
    rb.top_bar(c,"THE SIXTH HOOK // BLACK ENVELOPE",page)
    y=rb.PAGE_H-64
    rb.para(c,"THE OLD INTAKE WAKES.",rb.M,y,rb.PAGE_W-2*rb.M,36,size=21,font=rb.BOLD); y-=50
    rb.box(c,rb.M,y-120,rb.PAGE_W-2*rb.M,108,fill=rb.BLACK,stroke=rb.BLACK,radius=9)
    c.setStrokeColor(rb.WHITE); c.setLineWidth(1.5)
    c.line(rb.M+10,y-22,rb.PAGE_W/2,y-88); c.line(rb.PAGE_W-rb.M-10,y-22,rb.PAGE_W/2,y-88)
    c.setFillColor(rb.WHITE); c.setFont(rb.BOLD,11); c.drawCentredString(rb.PAGE_W/2,y-103,"06 // FOR THE PERSON HOLDING THIS BOOK")
    y-=142
    rb.box(c,rb.M+17,y-350,rb.PAGE_W-2*rb.M-34,350,fill=rb.WHITE,stroke=rb.BLACK,radius=2,sw=1.2)
    rb.label(c,o.get("status","INTAKE PRINTER // 00:01"),rb.M+34,y-24,size=9.5)
    rb.para(c,o.get("headline","TO THE PERSON HOLDING THIS BOOK"),rb.M+34,y-44,rb.PAGE_W-2*rb.M-68,42,size=18,font=rb.BOLD)
    ty=y-92
    lines=o.get("letter_lines") or [o.get("body","")]
    if isinstance(lines,str): lines=[lines]
    for line in lines:
        hh=rb.text_height(line,rb.PAGE_W-2*rb.M-68,11)
        rb.para(c,html.escape(line),rb.M+34,ty,rb.PAGE_W-2*rb.M-68,hh+1,size=11); ty-=hh+9
    note=o.get("note","")
    if note:
        c.setStrokeColor(rb.BLACK); c.line(rb.M+34,ty-3,rb.PAGE_W-rb.M-34,ty-3); ty-=18
        hh=rb.text_height(note,rb.PAGE_W-2*rb.M-68,11,rb.BOLD)
        rb.para(c,html.escape(note),rb.M+34,ty,rb.PAGE_W-2*rb.M-68,hh+1,size=11,font=rb.BOLD)
    y-=372
    rb.box(c,rb.M,y-72,rb.PAGE_W-2*rb.M,72,fill=rb.BLACK,stroke=rb.BLACK,radius=9)
    rb.para(c,"THE OPEN FIELD SLOT IS YOURS. YOU ARE DETECTIVE SIX.",rb.M+12,y-22,rb.PAGE_W-2*rb.M-24,34,size=12.5,font=rb.BOLD,color=rb.WHITE,align=1)
    rb.footer(c,page); c.showPage()


def id_page(c,data,page):
    card=data["opening"].get("id_card",{})
    rb.top_bar(c,"DETECTIVE SIX // INTAKE ID",page)
    y=rb.PAGE_H-70
    rb.para(c,card.get("heading","CLAIM THE SIXTH FIELD SLOT"),rb.M,y,rb.PAGE_W-2*rb.M,48,size=21,font=rb.BOLD); y-=70
    rb.box(c,rb.M,y-415,rb.PAGE_W-2*rb.M,415,fill=rb.WHITE,stroke=rb.BLACK,radius=16,sw=1.6)
    rb.label(c,card.get("designation","DETECTIVE SIX // RECRUIT"),rb.M+18,y-27,size=11)
    c.setStrokeColor(rb.BLACK); c.setLineWidth(4); c.circle(rb.PAGE_W-rb.M-72,y-67,37,fill=0,stroke=1)
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,30); c.drawCentredString(rb.PAGE_W-rb.M-72,y-78,"06")
    fields=[card.get("name_label","DETECTIVE NAME"),card.get("call_sign_label","CALL SIGN"),"SIGNATURE"]
    ty=y-118
    for label in fields:
        rb.label(c,label,rb.M+18,ty,size=9.5); c.setStrokeColor(rb.BLACK); c.setLineWidth(.9)
        c.line(rb.M+18,ty-25,rb.PAGE_W-rb.M-18,ty-25); ty-=75
    acceptance=card.get("acceptance","I accept the Academy rule: notice first, test the evidence, and explain my verdict.")
    rb.para(c,html.escape(acceptance),rb.M+18,ty,rb.PAGE_W-2*rb.M-36,52,size=11,font=rb.BOLD)
    rb.label(c,card.get("case_wall_label","CASE WALL // FACTS, SIGNALS, QUESTIONS"),rb.M,y-445,size=10)
    rb.writing_card(c,"FIRST CASE NOTES",rb.M,y-465,rb.PAGE_W-2*rb.M,118)
    rb.para(c,card.get("footer","Your name begins the file. Your evidence closes it."),rb.M,62,rb.PAGE_W-2*rb.M,28,size=10.5,font=rb.BOLD,align=1)
    rb.footer(c,page); c.showPage()


def how_to_page(c,data,page):
    rb.top_bar(c,"HOW TO WORK A CASE",page)
    y=rb.PAGE_H-66
    rb.para(c,"TEN MOVES. ONE DETECTIVE HABIT: EXPLAIN WHY.",rb.M,y,rb.PAGE_W-2*rb.M,42,size=18.5,font=rb.BOLD); y-=55
    steps=data["opening"].get("how_to_play",[])
    if len(steps)<10:
        defaults=["Read the situation.","Find the objective.","Mark exact evidence first.","Cross out what cannot work.","Use the map rules above the map.","Record witness numbers, not initials.","Write a verdict and coordinate when asked.","Take only the smallest hint you need.","Check the solution after committing.","Log the signal and keep solved maps."]
        steps=(steps+defaults)[:10]
    for i,item in enumerate(steps[:10],1):
        h=max(48,rb.text_height(item,rb.PAGE_W-2*rb.M-54,10.5)+16)
        rb.box(c,rb.M,y-h,rb.PAGE_W-2*rb.M,h,fill=rb.WHITE,stroke=rb.BLACK,radius=7)
        c.setFillColor(rb.BLACK); c.circle(rb.M+20,y-h/2,12,fill=1,stroke=0)
        c.setFillColor(rb.WHITE); c.setFont(rb.BOLD,9.5); c.drawCentredString(rb.M+20,y-h/2-3,str(i))
        rb.para(c,html.escape(item),rb.M+43,y-8,rb.PAGE_W-2*rb.M-54,h-12,size=10.5); y-=h+4
    rb.footer(c,page); c.showPage()


def hint_guide_page(c,data,page):
    rb.top_bar(c,"HINT VAULT // SOLUTION ARCHIVE",page)
    y=rb.PAGE_H-68
    rb.para(c,"ASK FOR THE SMALLEST NUDGE.",rb.M,y,rb.PAGE_W-2*rb.M,40,size=20,font=rb.BOLD); y-=62
    exact=["LEVEL 1 gives a small direction. Stop there if the case moves.","LEVEL 2 gives a stronger constraint. Return to the case before Level 3.","LEVEL 3 gives the decisive next step. The final verdict is still yours.","Commit to a verdict before opening the Solution Archive.","Solution pages begin with a black spoiler band. Cover it with your hand, then reveal it when ready."]
    instructions=data["opening"].get("hint_instructions") or exact
    for i,item in enumerate(instructions[:6],1):
        h=max(62,rb.text_height(item,rb.PAGE_W-2*rb.M-62,11.5)+22)
        rb.box(c,rb.M,y-h,rb.PAGE_W-2*rb.M,h,fill=rb.WHITE,stroke=rb.BLACK,radius=10)
        rb.label(c,f"{i:02d}",rb.M+13,y-23,size=11)
        rb.para(c,html.escape(item),rb.M+48,y-13,rb.PAGE_W-2*rb.M-62,h-18,size=11.5); y-=h+10
    rb.box(c,rb.M,75,rb.PAGE_W-2*rb.M,72,fill=rb.BLACK,stroke=rb.BLACK,radius=10)
    rb.para(c,"NO PENALTY FOR A HINT. THE GOAL IS THE NEXT TRUE STEP.",rb.M+14,117,rb.PAGE_W-2*rb.M-28,30,size=11.5,font=rb.BOLD,color=rb.WHITE,align=1)
    rb.footer(c,page); c.showPage()


def case_index_page(c,missions,plan,page,first,last):
    rb.top_bar(c,"CASE INDEX // NO SPOILERS",page)
    y=rb.PAGE_H-65
    rb.para(c,f"FILES {first:02d}-{last:02d}",rb.M,y,rb.PAGE_W-2*rb.M,32,size=19,font=rb.BOLD); y-=46
    for n in range(first,last+1):
        m=missions[n-1]; p=plan[f"{n:02d}_brief"]
        h=37
        rb.box(c,rb.M,y-h,rb.PAGE_W-2*rb.M,h,fill=rb.WHITE,stroke=rb.BLACK,radius=5)
        rb.label(c,f"{n:02d}",rb.M+10,y-17,size=10)
        title=str(m["title"]).upper(); rb.para(c,html.escape(title),rb.M+43,y-8,rb.PAGE_W-2*rb.M-100,23,size=9.5,font=rb.BOLD)
        rb.label(c,f"{p:03d}",rb.PAGE_W-rb.M-33,y-17,size=10); y-=h+3
    rb.footer(c,page); c.showPage()


def act_gate(c,title,subtitle,act,page):
    rb.top_bar(c,f"ACT {act} // ACADEMY FILE",page)
    c.setFillColor(rb.BLACK); c.rect(rb.M,rb.PAGE_H-330,rb.PAGE_W-2*rb.M,260,fill=1,stroke=0)
    rb.tiny_grid(c,rb.PAGE_W-rb.M-90,rb.PAGE_H-330,90,260,step=18)
    rb.label(c,f"ACT {act}",rb.M+18,rb.PAGE_H-113,color=rb.WHITE,size=11)
    rb.para(c,title,rb.M+18,rb.PAGE_H-152,rb.PAGE_W-2*rb.M-120,86,size=27,font=rb.BOLD,color=rb.WHITE)
    rb.box(c,rb.M,285,rb.PAGE_W-2*rb.M,135,fill=rb.WHITE,stroke=rb.BLACK,radius=12)
    rb.label(c,"WHAT CHANGES NOW",rb.M+16,393,size=10)
    rb.para(c,subtitle,rb.M+16,368,rb.PAGE_W-2*rb.M-32,65,size=12,font=rb.BOLD)
    rb.label(c,"STATUS // NEXT FILE UNLOCKED",rb.M,68,size=10)
    rb.footer(c,page); c.showPage()


def chat_block(c,data,dialogue,top,max_lines=5):
    if not dialogue: return 0
    rb.label(c,"HAPPY MAKERS CHAT",rb.M,top,size=10); y=top-14
    start=y
    for item in dialogue[:max_lines]:
        name=data["characters"][item["speaker"]]["name"]
        txt=f"<b>{name}:</b> {html.escape(item['text'])}"
        h=rb.text_height(txt,rb.PAGE_W-2*rb.M,10.5)
        rb.para(c,txt,rb.M,y,rb.PAGE_W-2*rb.M,h+1,size=10.5); y-=h+5
    return start-y+14


def mission_brief_page(c,data,m,page,progress):
    rb.top_bar(c,m.get("status","CASE FILE"),page,progress)
    y=rb.PAGE_H-62
    rb.pill(c,f"{m['rank']} // CASE {m['number']:02d}",rb.M,y-12,9,fill=rb.BLACK,h=21)
    th=rb.text_height(m["title"],rb.PAGE_W-2*rb.M,19,rb.BOLD)
    rb.para(c,m["title"],rb.M,y-34,rb.PAGE_W-2*rb.M,th+1,size=19,font=rb.BOLD); y-=th+54
    hook_h=rb.text_height(m["hook"],rb.PAGE_W-2*rb.M-28,11.5)
    rb.box(c,rb.M,y-hook_h-44,rb.PAGE_W-2*rb.M,hook_h+44,fill=rb.WHITE,stroke=rb.BLACK,radius=10)
    rb.label(c,"MISSION BRIEF",rb.M+14,y-19,size=9.5)
    rb.para(c,html.escape(m["hook"]),rb.M+14,y-30,rb.PAGE_W-2*rb.M-28,hook_h+1,size=11.5); y-=hook_h+59
    oh=rb.text_height(m["objective"],rb.PAGE_W-2*rb.M-28,12,rb.BOLD)
    rb.box(c,rb.M,y-oh-45,rb.PAGE_W-2*rb.M,oh+45,fill=rb.BLACK,stroke=rb.BLACK,radius=10)
    rb.label(c,"YOUR OBJECTIVE",rb.M+14,y-19,size=9.5,color=rb.WHITE)
    rb.para(c,html.escape(m["objective"]),rb.M+14,y-31,rb.PAGE_W-2*rb.M-28,oh+1,size=12,font=rb.BOLD,color=rb.WHITE); y-=oh+62
    used=chat_block(c,data,m.get("dialogue",[]),y); y-=used+8
    if int(m["number"])==1 and m.get("intake_receipt"):
        receipt=m["intake_receipt"]; lines=receipt.get("lines",[])
        hh=28+len(lines)*18
        rb.box(c,rb.M,y-hh,rb.PAGE_W-2*rb.M,hh,fill=rb.WHITE,stroke=rb.BLACK,radius=4)
        rb.label(c,receipt.get("heading","INTAKE-01 // ORIGINAL RECEIPT"),rb.M+12,y-18,size=9.5)
        for i,line in enumerate(lines): rb.label(c,str(line),rb.M+12,y-37-i*18,size=9.5)
    else:
        rb.writing_card(c,"EVIDENCE TO TEST / FIRST QUESTION",rb.M,max(88,y),rb.PAGE_W-2*rb.M,min(96,max(55,y-48)))
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


def compact_signal_bar(c,m):
    s=m.get("signal_log",{})
    if not s: return
    rb.box(c,rb.M,43,rb.PAGE_W-2*rb.M,52,fill=rb.BLACK,stroke=rb.BLACK,radius=6)
    rb.para(c,f"SIGNAL LOG // {html.escape(str(s.get('code','')))} // {html.escape(str(s.get('status','')))} — {html.escape(str(s.get('reaction','')))}",rb.M+9,85,rb.PAGE_W-2*rb.M-18,34,size=9.5,font=rb.BOLD,color=rb.WHITE)


def case03_photo_page(c,data,m,page,progress):
    rb.top_bar(c,"VISUAL EVIDENCE // PHOTO PAIR",page,progress)
    y=rb.PAGE_H-64
    rb.para(c,"SAME TABLE. ONE MINUTE APART.",rb.M,y,rb.PAGE_W-2*rb.M,38,size=19,font=rb.BOLD); y-=52
    rule=m.get("visual",{}).get("relevance_rule","A useful change affects the parcel, its tag, or its recorded route.")
    rb.para(c,html.escape(rule),rb.M,y,rb.PAGE_W-2*rb.M,42,size=11,font=rb.BOLD); y-=55
    gap=14; pw=(rb.PAGE_W-2*rb.M-gap)/2; ph=315
    for i in range(2):
        x=rb.M+i*(pw+gap); rb.box(c,x,y-ph,pw,ph,fill=rb.WHITE,stroke=rb.BLACK,radius=8)
        rb.label(c,f"PHOTO {'A' if i==0 else 'B'} // 15:{42+i:02d}",x+10,y-18,size=9.5)
        # Table horizon and parcel remain identical so the three material
        # changes read as evidence rather than decorative spot-the-difference.
        c.setStrokeColor(rb.BLACK); c.setLineWidth(1); c.line(x+14,y-76,x+pw-14,y-76)
        px=x+32; py=y-160; ww=pw-64
        c.rect(px,py,ww,72,fill=0,stroke=1)
        knot=px+(35 if i==0 else ww-35)
        c.setLineWidth(1.8); c.line(knot,py,knot,py+72)
        c.ellipse(knot-17,py+28,knot,py+42,fill=0,stroke=1); c.ellipse(knot,py+28,knot+17,py+42,fill=0,stroke=1)
        c.line(knot,py+35,knot-10,py+20); c.line(knot,py+35,knot+10,py+20)
        rb.box(c,x+24,y-230,82,35,fill=rb.WHITE,stroke=rb.BLACK,radius=4)
        c.setFont(rb.MONO,10); c.setFillColor(rb.BLACK); c.drawCentredString(x+65,y-218,"0417" if i==0 else "0471")
        # A real muddy shoeprint changes travel direction.  Toe pads make the
        # orientation legible without a helper arrow; Photo B points at door.
        ax=x+pw-72; ay=y-215; c.saveState(); c.translate(ax,ay); c.rotate(90 if i else -90)
        c.setFillColor(rb.BLACK); c.ellipse(-13,-27,13,22,fill=1,stroke=0)
        for tx in (-12,-6,0,6,12): c.circle(tx,27-abs(tx)*.25,4.2,fill=1,stroke=0)
        c.restoreState()
        c.setStrokeColor(rb.BLACK); c.setLineWidth(2); c.line(x+pw-25,y-244,x+pw-25,y-183)
        rb.label(c,"DOOR",x+pw-57,y-176,size=9.5)
        # Three harmless changes are present too: poster star, cup handle and
        # pencil position.  They are visible decoys, not silently held equal.
        stars=3+i
        c.setFont(rb.BOLD,10); c.drawString(x+22,y-268,f"POSTER  {stars} STARS")
        c.circle(x+pw-51,y-269,14,fill=0,stroke=1)
        if i==0: c.line(x+pw-37,y-269,x+pw-27,y-269)
        else: c.line(x+pw-65,y-269,x+pw-75,y-269)
        c.setLineWidth(2)
        if i==0: c.line(x+76,y-297,x+139,y-286)
        else: c.line(x+98,y-286,x+161,y-297)
        rb.label(c,"BACKGROUND OBJECTS",x+22,y-307,size=9.5)
    y-=ph+18
    rb.writing_card(c,"CIRCLE THE 3 CHANGES THAT ALTER THE EVIDENCE",rb.M,y,rb.PAGE_W-2*rb.M,72)
    compact_signal_bar(c,m)
    rb.footer(c,page); c.showPage()


def case08_route_page(c,data,m,page,progress):
    rb.top_bar(c,"ROUTE FILE // DRAWN OPTIONS",page,progress)
    y=rb.PAGE_H-64
    rb.para(c,"TRACE EACH ROUTE. TEST EVERY SITE CONDITION.",rb.M,y,rb.PAGE_W-2*rb.M,42,size=18,font=rb.BOLD); y-=60
    route=m.get("route",{}); options=route.get("options",[])[:3]
    # Every candidate uses the same floor plan. Route waypoints sit in a
    # separate path strip so the line of travel never obscures room labels.
    for idx,opt in enumerate(options):
        h=165; x=rb.M; w=rb.PAGE_W-2*rb.M
        rb.box(c,x,y-h,w,h,fill=rb.WHITE,stroke=rb.BLACK,radius=8)
        rb.label(c,f"ROUTE {opt.get('id',chr(65+idx))}",x+10,y-18,size=10)
        fx=x+12; fy=y-h+58; fw=w-24; fh=65
        rooms={
            "LOBBY":(.02,.23,.15,.54),"PAINT CORRIDOR":(.21,.00,.23,.44),
            "COSTUME STORAGE":(.21,.54,.23,.46),"SIDE HALL":(.50,.54,.19,.46),
            "STAFF STAIRS":(.50,.00,.19,.44),"PROP ROOM":(.78,.23,.20,.54),
        }
        centers={}
        for name,(rx,ry,rw,rh) in rooms.items():
            xx=fx+rx*fw; yy=fy+ry*fh; ww=rw*fw; hh=rh*fh
            c.setFillColor(rb.WHITE); c.setStrokeColor(rb.BLACK); c.setLineWidth(1.1); c.rect(xx,yy,ww,hh,fill=1,stroke=1)
            label=name
            if name=="PAINT CORRIDOR": label="PAINT CORRIDOR<br/><b>CLOSED 16:30</b>"
            if name=="STAFF STAIRS": label="STAFF STAIRS<br/><b>LOCKED</b>"
            rb.para(c,label,xx+3,yy+hh-2,ww-6,hh-3,size=9.5,font=rb.BOLD,align=1)
            centers[name]=(xx+ww/2,yy+hh/2)
        # Structural wall and locked door remain visible in the shared plan.
        c.setStrokeColor(rb.BLACK); c.setLineWidth(4); wallx=fx+.735*fw
        wall_top=fy+fh*.45
        c.line(wallx,fy,wallx,wall_top)
        c.setLineWidth(2); c.line(wallx-8,fy+19,wallx+8,fy+5)
        rb.label(c,"WALL",wallx-13,wall_top+11,size=9.5)
        nodes=opt.get("path",[])
        route_text="  >  ".join(f"{j} {node}" for j,node in enumerate(nodes,1))
        rb.para(c,"<b>PATH // </b>"+html.escape(route_text),x+10,y-h+43,w-20,20,size=9.5,font=rb.BOLD)
        fail=opt.get("fails")
        status="SITE CHECK // OPEN ROUTE" if not fail else "SITE CHECK // "+str(fail)
        rb.para(c,html.escape(status),x+10,y-h+24,w-20,22,size=9.5,font=rb.BOLD)
        y-=h+8
    rb.writing_card(c,"VALID ROUTE / REASON",rb.M,y,rb.PAGE_W-2*rb.M,36)
    compact_signal_bar(c,m)
    rb.footer(c,page); c.showPage()


def case11_bag_page(c,data,m,page,progress):
    rb.top_bar(c,"EVIDENCE SORT // SEALED ITEMS",page,progress)
    y=rb.PAGE_H-64
    rb.para(c,"LABEL THE EVIDENCE BEFORE YOU EXPLAIN IT.",rb.M,y,rb.PAGE_W-2*rb.M,42,size=18.5,font=rb.BOLD); y-=58
    window=m.get("classification",{}).get("case_window","")
    rb.box(c,rb.M,y-36,rb.PAGE_W-2*rb.M,34,fill=rb.BLACK,stroke=rb.BLACK,radius=5)
    rb.para(c,"CASE WINDOW // "+html.escape(window),rb.M+10,y-12,rb.PAGE_W-2*rb.M-20,22,size=10,font=rb.BOLD,color=rb.WHITE,align=1); y-=48
    items=m.get("classification",{}).get("items",[])[:7]
    cols=2; gap=12; cw=(rb.PAGE_W-2*rb.M-gap)/2; ch=104
    for i,item in enumerate(items):
        row=i//cols; col=i%cols; x=rb.M+col*(cw+gap); top=y-row*(ch+8)
        rb.box(c,x,top-ch,cw,ch,fill=rb.WHITE,stroke=rb.BLACK,radius=5)
        rb.label(c,f"RECORD {item.get('id',i+1)}",x+10,top-18,size=9.5)
        kind=str(item.get("item",item.get("label","OBJECT")))
        cx=x+42; cy=top-57; lower=kind.lower(); c.setStrokeColor(rb.BLACK); c.setLineWidth(1.4)
        if "card" in lower:
            c.roundRect(cx-25,cy-18,50,36,4,fill=0,stroke=1); c.line(cx-19,cy+7,cx+19,cy+7)
        elif "cable" in lower:
            c.circle(cx,cy,20,fill=0,stroke=1); c.line(cx+15,cy+13,cx+28,cy+24); c.line(cx-15,cy-13,cx-27,cy-23)
        elif "wheel" in lower:
            c.circle(cx,cy,23,fill=0,stroke=1); c.circle(cx,cy,9,fill=0,stroke=1)
        elif "phone" in lower:
            c.roundRect(cx-17,cy-27,34,54,5,fill=0,stroke=1); c.line(cx-10,cy+18,cx+10,cy+18)
        elif "pen" in lower:
            c.line(cx-23,cy-13,cx+22,cy+16); c.line(cx+18,cy+20,cx+26,cy+10)
        elif "oat" in lower:
            c.rect(cx-27,cy-18,54,36,fill=0,stroke=1); c.line(cx-27,cy+11,cx+27,cy+11); c.line(cx-27,cy-11,cx+27,cy-11)
        else:
            c.rect(cx-22,cy-18,44,36,fill=0,stroke=1)
        tx=x+78; tw=cw-88
        rb.para(c,html.escape(kind.upper()),tx,top-35,tw,28,size=9.5,font=rb.BOLD)
        rb.para(c,html.escape(str(item.get("label",""))),tx,top-64,tw,34,size=9.5)
    rb.writing_card(c,"WHICH TIMESTAMPED RECORD A-D FALLS OUTSIDE THE WINDOW?",rb.M,160,rb.PAGE_W-2*rb.M,55)
    compact_signal_bar(c,m)
    rb.footer(c,page); c.showPage()


def case24_footprint_page(c,data,m,page,progress):
    rb.top_bar(c,"VISUAL SEQUENCE // FOOTPRINT RUN",page,progress)
    y=rb.PAGE_H-68
    rb.para(c,"MUD FADES. THE TREAD ARROW CAN MISLEAD.",rb.M,y,rb.PAGE_W-2*rb.M,40,size=18.5,font=rb.BOLD); y-=58
    prints=m.get("visual_sequence",{}).get("prints",[])
    if not prints: prints=[{"position":str(i+1),"mud":v,"tread_arrow":"→"} for i,v in enumerate((90,70,45,20))]
    stepw=(rb.PAGE_W-2*rb.M-30)/max(1,len(prints)); panel_bottom=y-305
    rb.box(c,rb.M,panel_bottom,rb.PAGE_W-2*rb.M,305,fill=rb.WHITE,stroke=rb.BLACK,radius=8)
    for i,p in enumerate(prints):
        x=rb.M+15+i*stepw; mud=str(p.get("mud","")); digits=''.join(ch for ch in mud if ch.isdigit())
        density=max(1,min(10,(int(digits) if digits else 50)//10))
        cx=x+stepw/2-8; sole_y=panel_bottom+104
        # One unmistakable shoeprint: broad toe/forefoot, narrow waist and heel.
        c.setStrokeColor(rb.BLACK); c.setLineWidth(1.4)
        c.ellipse(cx-22,sole_y+70,cx+22,sole_y+132,fill=0,stroke=1)
        c.roundRect(cx-14,sole_y+10,28,76,8,fill=0,stroke=1)
        c.line(cx-13,sole_y+64,cx+13,sole_y+64)
        c.line(cx-12,sole_y+30,cx+12,sole_y+30)
        for k in range(density):
            yy=sole_y+18+k*9
            if yy<sole_y+126:
                c.setLineWidth(.65); c.line(cx-11,yy,cx+11,yy+5)
        rb.label(c,f"PRINT {i+1}",x,panel_bottom+276,size=9.5)
        rb.para(c,html.escape(str(p.get('position',i+1))),x,panel_bottom+256,stepw-10,26,size=9.5,font=rb.BOLD,align=1)
        rb.label(c,f"MUD {mud}",x,panel_bottom+82,size=9.5)
        rb.para(c,f"TREAD {html.escape(str(p.get('tread_arrow','EAST')))}",x,panel_bottom+57,stepw-10,24,size=9.5,font=rb.BOLD,align=1)
    rule=m.get("visual_sequence",{}).get("rule","")
    rb.para(c,html.escape(rule),rb.M,y-335,rb.PAGE_W-2*rb.M,45,size=10.5,font=rb.BOLD)
    rb.writing_card(c,"DIRECTION OF TRAVEL / EVIDENCE",rb.M,190,rb.PAGE_W-2*rb.M,82)
    compact_signal_bar(c,m)
    rb.footer(c,page); c.showPage()


def puzzle_page(c,data,m,page,progress):
    n=int(m["number"])
    if n==3: return case03_photo_page(c,data,m,page,progress)
    if n==8: return case08_route_page(c,data,m,page,progress)
    if n==11: return case11_bag_page(c,data,m,page,progress)
    if n==24: return case24_footprint_page(c,data,m,page,progress)
    if m.get("type")=="guided": return rb.guided_puzzle_page(c,data,m,page,progress)
    if m.get("type")=="code": return rb.code_puzzle_page(c,data,m,page,progress)
    if m.get("type")=="visual": return rb.visual_puzzle_page(c,data,m,page,progress)
    return rb.structured_puzzle_page(c,data,m,page,progress)


def solution_page(c,mission,case,image,page):
    rb.top_bar(c,f"SOLUTION // CASE {mission['number']:02d}",page)
    width=rb.PAGE_W-2*rb.M
    rb.para(c,html.escape(mission["title"]),rb.M,rb.PAGE_H-54,width,40,size=16.5,font=rb.BOLD)
    bottom,_,_=draw_grid(c,image,case,rb.PAGE_H-102,4.45*72)
    legend="  |  ".join(f"{i:02d} {p['display_name']}" for i,p in enumerate(case["characters"],1))
    lh=rb.text_height(legend,width,9.5)
    rb.para(c,legend,rb.M,bottom-5,width,lh+1,size=9.5)
    y=bottom-lh-18
    answer=case["source_answer"]
    answer_source=answer.get("source_name",answer.get("name"))
    answer_index=next(i for i,p in enumerate(case["characters"],1) if p["source_name"]==answer_source)
    rb.box(c,rb.M,y-54,width,54,fill=rb.BLACK,stroke=rb.BLACK,radius=8)
    rb.label(c,"SPOILER // VERIFIED VERDICT",rb.M+12,y-17,size=9.5,color=rb.WHITE)
    rb.para(c,f"{answer_index:02d} — {html.escape(answer['display_name'])} — {answer['coordinate']}",rb.M+12,y-27,width-24,23,size=12,font=rb.BOLD,color=rb.WHITE)
    y-=70; rb.label(c,"HOW THE CASE FALLS INTO PLACE",rb.M,y,size=10); y-=11
    steps=mission["solution_steps"]; split=(len(steps)+1)//2; colw=(width-22)/2
    for col,items in enumerate((steps[:split],steps[split:])):
        ty=y
        for idx,step in enumerate(items,1+col*split):
            used=rb.text_height(f"<b>{idx:02d}</b>  "+html.escape(step),colw,11)
            rb.para(c,f"<b>{idx:02d}</b>  "+html.escape(step),rb.M+col*(colw+22),ty,colw,used+1,size=11)
            ty-=used+7
    rb.footer(c,page); c.showPage()


def nonspatial_solution_page(c,mission,page):
    rb.top_bar(c,f"SOLUTION // CASE {mission['number']:02d}",page)
    w=rb.PAGE_W-2*rb.M; y=rb.PAGE_H-58
    rb.para(c,html.escape(mission["title"]),rb.M,y,w,44,size=17,font=rb.BOLD); y-=60
    answer=rb._solution_answer_text(mission) or mission.get("verdict",mission.get("meta_reveal","CHECK THE REASONING BELOW"))
    rb.box(c,rb.M,y-76,w,76,fill=rb.BLACK,stroke=rb.BLACK,radius=9)
    rb.label(c,"SPOILER // VERIFIED VERDICT",rb.M+14,y-20,size=9.5,color=rb.WHITE)
    rb.para(c,html.escape(str(answer)),rb.M+14,y-34,w-28,36,size=13,font=rb.BOLD,color=rb.WHITE); y-=96
    rb.label(c,"HOW THE CASE FALLS INTO PLACE",rb.M,y,size=10); y-=16
    steps=mission.get("solution_steps",[])
    if not steps: steps=[mission.get("objective","Use the evidence to justify the verdict."),mission.get("meta_reveal","")]
    for idx,step in enumerate([s for s in steps if str(s).strip()],1):
        h=max(52,rb.text_height(str(step),w-58,11)+18)
        if y-h<105: raise ValueError(f"Case {mission['number']}: solution reasoning overflows")
        rb.box(c,rb.M,y-h,w,h,fill=rb.WHITE,stroke=rb.BLACK,radius=7)
        rb.label(c,f"{idx:02d}",rb.M+11,y-21,size=9.5)
        rb.para(c,html.escape(str(step)),rb.M+43,y-10,w-56,h-14,size=11); y-=h+6
    rb.para(c,"Spoiler treatment: the answer is held in a solid black band so it can be covered by hand; reasoning remains upright for comfortable reading.",rb.M,79,w,34,size=9.5)
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
        rb.box(c,rb.M+24,y-357,rb.PAGE_W-2*rb.M-48,342,fill=rb.WHITE,stroke=rb.BLACK,radius=3,sw=1.3)
        photo=ROOT/"assets"/"production"/"v4"/"case16_old_academy_photo.png"
        rb.draw_image_fit(c,photo,rb.M+34,y-345,rb.PAGE_W-2*rb.M-68,320)
        rb.label(c,"ARCHIVE PHOTOGRAPH // DATE UNKNOWN",rb.M+34,y-8,size=9.5)
        evidence=("STRIPED BADGES: official events, 1999-2003.  SECURITY PANEL: installed 2001 and visible in the room.  "
                  "ENVELOPE STOCK IN THE SAME FILE: expired 2004.  Use the overlap; do not guess from clothing.")
        rb.text_card(c,evidence,rb.M,y-377,rb.PAGE_W-2*rb.M,heading="DATE THE PHOTO",size=10.5,stroke=rb.BLACK)
    elif m["number"]==21:
        scraps=m["reconstruction"]["scraps"]
        positions=[(rb.M+10,y-90),(rb.M+270,y-90),(rb.M+80,y-255),(rb.M+335,y-255)]
        for scrap,(x,top) in zip(scraps,positions):
            # Canonical complementary profiles: B→D notch, D→A zigzag,
            # A→C curve. Straight edges remain the message's outer edges.
            x0=x+8; x1=x+195; yt=top-7; yb=top-112
            p=c.beginPath(); p.moveTo(x0,yt); p.lineTo(x1,yt)
            edge=scrap["right_edge"]
            if edge=="straight": p.lineTo(x1,yb)
            elif edge=="notch-3":
                p.lineTo(x1,yt-28); p.lineTo(x1+15,yt-39); p.lineTo(x1+15,yt-66); p.lineTo(x1,yt-78); p.lineTo(x1,yb)
            elif edge=="zigzag-2":
                p.lineTo(x1,yt-24); p.lineTo(x1+15,yt-39); p.lineTo(x1-6,yt-55); p.lineTo(x1+15,yt-72); p.lineTo(x1,yb)
            else:  # curve-1
                p.lineTo(x1,yt-29); p.curveTo(x1+22,yt-35,x1+22,yt-72,x1,yt-78); p.lineTo(x1,yb)
            p.lineTo(x0,yb)
            edge=scrap["left_edge"]
            if edge=="straight": p.lineTo(x0,yt)
            elif edge=="notch-3":
                p.lineTo(x0,yb+34); p.lineTo(x0+15,yb+46); p.lineTo(x0+15,yb+73); p.lineTo(x0,yb+84); p.lineTo(x0,yt)
            elif edge=="zigzag-2":
                p.lineTo(x0,yb+33); p.lineTo(x0+15,yb+48); p.lineTo(x0-6,yb+64); p.lineTo(x0+15,yb+81); p.lineTo(x0,yt)
            else:  # curve-1
                p.lineTo(x0,yb+34); p.curveTo(x0+22,yb+40,x0+22,yb+76,x0,yb+83); p.lineTo(x0,yt)
            p.close(); c.setFillColor(rb.WHITE); c.setStrokeColor(rb.BLACK)
            c.drawPath(p,fill=1,stroke=1)
            c.setFillColor(rb.BLACK)
            c.setFont(rb.BOLD,11); c.drawString(x+30,top-25,f"SCRAP {scrap['id']}")
            c.setFont(rb.BOLD,15); c.drawCentredString(x+103,top-68,scrap["text"])
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
            c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,9.5)
            for i in range(cols): c.drawCentredString(x+(i+.5)*gw/cols,top+7,chr(65+i))
            for i in range(rows): c.drawString(x+4,top-(i+.55)*gh/rows,str(i+1))
            cells=overlay["old_room_cells"] if side==0 else overlay["current_archive_wall_cells"]
            c.setFillColor(rb.WHITE)
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


def finale_page(c,data,m,page):
    rb.top_bar(c,"ROOM ZERO // THE FULL EXPLANATION",page,1.0)
    y=rb.PAGE_H-62
    rb.para(c,"THE DOOR OPENS. THE EVIDENCE EXPLAINS WHY.",rb.M,y,rb.PAGE_W-2*rb.M,40,size=18.5,font=rb.BOLD); y-=50
    sections=data.get("finale_sections",[])
    gap=12; cw=(rb.PAGE_W-2*rb.M-gap)/2; ch=122
    for i,sec in enumerate(sections[:7]):
        col=i%2; row=i//2; x=rb.M+col*(cw+gap); top=y-row*(ch+8)
        rb.box(c,x,top-ch,cw,ch,fill=rb.WHITE,stroke=rb.BLACK,radius=8)
        rb.label(c,f"{i+1:02d} // {sec.get('heading','').upper()}",x+10,top-20,size=9.5)
        rb.para(c,html.escape(sec.get("body","")),x+10,top-34,cw-20,ch-41,size=10.2)
    # The routing log proves how the two triggers and selected cases connect.
    if len(sections)==7:
        x=rb.M+cw+gap; top=y-3*(ch+8)
        rb.box(c,x,top-ch,cw,ch,fill=rb.BLACK,stroke=rb.BLACK,radius=8)
        rb.label(c,"DATED ROUTING / SELECTION LOG",x+10,top-19,size=9.5,color=rb.WHITE)
        log=("00:00  ROSTER SAVED // SLOT 06 OPEN // ENVELOPE RELEASED<br/>"
             "00:01  CASE 01 CLOSED // QUEUE RESTARTED<br/>"
             "CASE 05  LOCKER: BALL &gt; STAR &gt; BOLT &gt; HEART<br/>"
             "SELECTED MAPS: 02 04 06 07 10 12 13<br/>"
             "15 17 19 20 22 23 25")
        rb.para(c,log,x+10,top-34,cw-20,ch-41,size=9.5,font=rb.BOLD,color=rb.WHITE)
    rb.footer(c,page); c.showPage()


def certificate_page(c,data,page):
    cert=data.get("certificate",{})
    rb.top_bar(c,"DETECTIVE ACADEMY // CERTIFICATE",page,1.0)
    c.setStrokeColor(rb.BLACK); c.setLineWidth(2.2); c.rect(rb.M+18,90,rb.PAGE_W-2*rb.M-36,rb.PAGE_H-150,fill=0,stroke=1)
    c.setLineWidth(.7); c.rect(rb.M+28,100,rb.PAGE_W-2*rb.M-56,rb.PAGE_H-170,fill=0,stroke=1)
    rb.para(c,cert.get("heading","DETECTIVE ACADEMY // FIELD CERTIFICATION"),rb.M+48,rb.PAGE_H-108,rb.PAGE_W-2*rb.M-96,46,size=18,font=rb.BOLD,align=1)
    rb.label(c,cert.get("awarded_to_label","AWARDED TO"),rb.M+68,rb.PAGE_H-188,size=9.5)
    c.setLineWidth(1); c.line(rb.M+68,rb.PAGE_H-220,rb.PAGE_W-rb.M-68,rb.PAGE_H-220)
    rb.label(c,cert.get("call_sign_label","OFFICIAL CALL SIGN"),rb.M+68,rb.PAGE_H-258,size=9.5)
    c.line(rb.M+68,rb.PAGE_H-290,rb.PAGE_W-rb.M-68,rb.PAGE_H-290)
    achievement=cert.get("achievement","FOR SOLVING THE MYSTERY OF ROOM ZERO BY FOLLOWING THE EVIDENCE ALL THE WAY TO THE TRUTH.")
    rb.para(c,html.escape(achievement),rb.M+58,rb.PAGE_H-340,rb.PAGE_W-2*rb.M-116,90,size=13,font=rb.BOLD,align=1)
    rb.box(c,rb.M+63,265,rb.PAGE_W-2*rb.M-126,76,fill=rb.BLACK,stroke=rb.BLACK,radius=10)
    rb.para(c,cert.get("rank","CERTIFIED FIELD DETECTIVE // DETECTIVE SIX"),rb.M+76,311,rb.PAGE_W-2*rb.M-152,36,size=12.5,font=rb.BOLD,color=rb.WHITE,align=1)
    rb.para(c,cert.get("case_status","ROOM ZERO // CLOSED"),rb.M+76,285,rb.PAGE_W-2*rb.M-152,24,size=9.5,color=rb.WHITE,align=1)
    rb.label(c,cert.get("signed_by","Happy Makers Detective Academy"),rb.M+68,205,size=9.5)
    c.line(rb.M+68,185,rb.PAGE_W/2-12,185)
    rb.label(c,cert.get("archive_confirmation","BIBI // ARCHIVE MENTOR"),rb.PAGE_W/2+12,205,size=9.5)
    c.line(rb.PAGE_W/2+12,185,rb.PAGE_W-rb.M-68,185)
    rb.para(c,cert.get("note","Use the call sign from your Field Detective ID."),rb.M+56,145,rb.PAGE_W-2*rb.M-112,36,size=9.5,align=1)
    rb.footer(c,page); c.showPage()


def book2_scene_page(c,data,page):
    scene=data.get("book2_scene",{})
    rb.top_bar(c,"NEW FILE // AFTER CERTIFICATION",page,1.0)
    y=rb.PAGE_H-62
    rb.para(c,scene.get("heading","CASE 001 // STILL OPEN"),rb.M,y,rb.PAGE_W-2*rb.M,40,size=21,font=rb.BOLD); y-=55
    # Physical incoming file with a distinct triangular mark.
    folder_x=rb.M+30; folder_w=rb.PAGE_W-2*rb.M-60
    rb.box(c,folder_x,y-305,folder_w,285,fill=rb.WHITE,stroke=rb.BLACK,radius=5,sw=1.4)
    c.setFillColor(rb.BLACK); p=c.beginPath(); p.moveTo(folder_x+folder_w-68,y-50); p.lineTo(folder_x+folder_w-38,y-105); p.lineTo(folder_x+folder_w-98,y-105); p.close(); c.drawPath(p,fill=1,stroke=1)
    rb.label(c,"ARCHIVE RELEASE // CASE 001",folder_x+16,y-47,size=10)
    # Old photograph; the cutout is an obvious missing silhouette.
    photo_x=folder_x+28; photo_y=y-260; photo_w=folder_w-56; photo_h=158
    c.setFillColor(colors.HexColor("#E5E5E5")); c.rect(photo_x,photo_y,photo_w,photo_h,fill=1,stroke=1)
    for i in range(5):
        cx=photo_x+45+i*(photo_w-90)/4; cy=photo_y+74
        if i==2:
            c.setFillColor(rb.WHITE); c.setStrokeColor(rb.BLACK); c.setDash(4,3); c.rect(cx-22,cy-48,44,96,fill=1,stroke=1); c.setDash()
            rb.label(c,"CUT OUT",cx-23,cy-4,size=9.5)
        else:
            c.setFillColor(rb.WHITE); c.circle(cx,cy+27,17,fill=1,stroke=1); c.line(cx,cy+10,cx,cy-34); c.line(cx,cy-5,cx-16,cy-22); c.line(cx,cy-5,cx+16,cy-22)
    rb.box(c,folder_x+68,y-294,folder_w-136,38,fill=rb.BLACK,stroke=rb.BLACK,radius=2)
    rb.para(c,"RETURN BEFORE THE FIRST MEETING",folder_x+76,y-270,folder_w-152,24,size=11,font=rb.BOLD,color=rb.WHITE,align=1)
    y-=330
    beats=scene.get("beats",[])
    for beat in beats[:5]:
        h=rb.text_height(str(beat),rb.PAGE_W-2*rb.M-24,9.5)
        rb.para(c,"• "+html.escape(str(beat)),rb.M+12,y,rb.PAGE_W-2*rb.M-24,h+1,size=9.5); y-=h+5
    chat=scene.get("chat",[])
    if chat:
        rb.label(c,"HAPPY MAKERS CHAT",rb.M,y-2,size=9.5); y-=15
        for item in chat[:4]:
            txt=f"<b>{data['characters'][item['speaker']]['name']}:</b> {html.escape(item['text'])}"
            h=rb.text_height(txt,rb.PAGE_W-2*rb.M,9.5); rb.para(c,txt,rb.M,y,rb.PAGE_W-2*rb.M,h+1,size=9.5); y-=h+3
    rb.box(c,rb.M,55,rb.PAGE_W-2*rb.M,44,fill=rb.BLACK,stroke=rb.BLACK,radius=8)
    rb.para(c,scene.get("final_line","NEXT FILE INCOMING."),rb.M+12,84,rb.PAGE_W-2*rb.M-24,22,size=12,font=rb.BOLD,color=rb.WHITE,align=1)
    rb.footer(c,page); c.showPage()


def build_data(master_path,runtime_path,maps_path,overrides_path,aliases_path,output):
    data=load(master_path); overrides=load(overrides_path); runtime=json.loads(runtime_path.read_text(encoding="utf-8"))
    aliases=load(aliases_path)["cases"]
    data["book"].update(overrides["book"]); data["opening"].update(overrides["opening"])
    for key in ("publication","finale_sections","finale_chat","certificate","book2_scene","canon","case_index","acts"):
        if key in overrides: data[key]=copy.deepcopy(overrides[key])
    if "story_spine" in overrides: data["story_spine"]=copy.deepcopy(overrides["story_spine"])
    data["v4"]=copy.deepcopy(overrides)
    data["production_state"].update(owner_review_version=4,english_frozen=False,witness_marker_mode="numeric",
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
        mission.update(copy.deepcopy(overrides["cases"].get(number,{})))
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
        # Publication wording follows the verified object predicate exactly.
        # C5 in Case 02 is a desk chair; teacher desks are blocked cells.
        if number==2:
            for container in (updated.get("spatial_copy",{}),updated.get("spatial",{})):
                if "clue_cards" in container:
                    container["clue_cards"]=[str(x).replace("standing on a desk","standing on a desk chair") for x in container["clue_cards"]]
        if number==23:
            exact="Mae shared a room with a person who was on a bench. That person was either Ozzy or Pia."
            exact=replace_tokens(exact,names)
            for container in (updated.get("spatial_copy",{}),updated.get("spatial",{})):
                if "clue_cards" in container:
                    container["clue_cards"]=[exact if "shared a room with either" in str(x) else x for x in container["clue_cards"]]
        sp=updated.setdefault("spatial",copy.deepcopy(updated.get("spatial_copy",{})))
        for mode,key in (("puzzle","source_page_asset"),("solution","solution_asset")):
            asset=maps_path/f"{cid}_{mode}_original_shigai_relabelled.png"
            if not asset.is_file(): raise FileNotFoundError(asset)
            sp[key]=asset.relative_to(ROOT).as_posix()
        sp.update(puzzle_asset=sp["source_page_asset"],crop=None,solution_crop=None,
                  rows=case["grid"]["rows"],columns=case["grid"]["columns"])
        data["missions"][i]=updated
    out_master=output.parent/"book1_en_master_owner_review_v4.yml"
    out_runtime=output.parent/"hmda_spatial_runtime_v4.json"
    out_master.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True,width=110),encoding="utf-8")
    out_runtime.write_text(json.dumps(runtime,indent=2,ensure_ascii=False),encoding="utf-8")
    return data,cases,out_master,out_runtime


def plan_pages(missions,data):
    """Return the complete deterministic V4 index before any page is drawn."""
    index={
        "title":1,"publication":2,"academy":3,"characters_1":4,"characters_2":5,
        "invitation":6,"detective_id":7,"how_to":8,"hint_guide":9,
        "case_index_1":10,"case_index_2":11,"act_1":12,
    }
    page=13
    compact=set(data["v4"]["production"]["compact_cases"])|{3,26,27}
    artifacts=set(data["v4"]["production"]["artifact_cases"])
    spine={int(b["after_case"]):b for b in data["story_spine"]["beats"]}
    for m in missions:
        n=int(m["number"]); typ=m.get("type")
        if n>1 and typ in ("spatial","boss-spatial") and page%2==1:
            index[f"{n:02d}_parity_pause"]=page; page+=1
        index[f"{n:02d}_brief"]=page; page+=1
        index[f"{n:02d}_{'map' if typ in ('spatial','boss-spatial') else 'puzzle'}"]=page; page+=1
        if n in artifacts: index[f"{n:02d}_artifact"]=page; page+=1
        if n==30:
            index["30_finale"]=page; page+=1
            index["certificate"]=page; page+=1
            index["book2_scene"]=page; page+=1
        elif n in spine:
            index[f"{n:02d}_act"]=page; page+=1
        elif n not in compact:
            index[f"{n:02d}_signal"]=page; page+=1
    for level in range(1,4):
        index[f"hints_level_{level}_cases_01_15"]=page; page+=1
        index[f"hints_level_{level}_cases_16_30"]=page; page+=1
    for m in missions:
        index[f"{int(m['number']):02d}_solution"]=page; page+=1
    index["page_count"]=page-1
    return index


def render_v4(data,cases,master_path,output):
    rb.ROOT=ROOT
    output.parent.mkdir(parents=True,exist_ok=True)
    missions=data["missions"]; plan=plan_pages(missions,data)
    if plan["page_count"]!=145:
        raise ValueError(f"V4 pagination contract changed: expected 145, planned {plan['page_count']}")
    c=canvas.Canvas(str(output),pagesize=(rb.PAGE_W,rb.PAGE_H),pageCompression=1)
    c.setTitle(f"{data['book']['title']} — {data['book']['subtitle']}")
    c.setAuthor("Rise.Shine.Evolve")
    c.setSubject(data["book"]["pdf_subject"]); c.setKeywords(data["book"]["pdf_keywords"])
    page=1
    v4_title_page(c,data); page+=1
    publication_page(c,data,page); page+=1
    academy_page(c,data,page); page+=1
    cards=data["opening"].get("character_cards",[])
    character_page(c,data,page,cards[:3],"FIELD TEAM 01"); page+=1
    character_page(c,data,page,cards[3:6],"FIELD TEAM 02 / ARCHIVE MENTOR"); page+=1
    detective_six_invitation(c,data,page); page+=1
    id_page(c,data,page); page+=1
    how_to_page(c,data,page); page+=1
    hint_guide_page(c,data,page); page+=1
    case_index_page(c,missions,plan,page,1,15); page+=1
    case_index_page(c,missions,plan,page,16,30); page+=1
    act_gate(c,"SOMETHING IS OFF","Five current field badges. One open hook. One intake record that has started a much larger case.","I",page); page+=1

    compact=set(data["v4"]["production"]["compact_cases"])|{3,26,27}
    artifacts=set(data["v4"]["production"]["artifact_cases"])
    spine={int(b["after_case"]):b for b in data["story_spine"]["beats"]}
    original_cards=rb._structured_cards
    def cards_with_signal(mission):
        cards,note=original_cards(mission)
        if int(mission.get("number",0)) in compact:
            s=mission["signal_log"]
            note=f"SIGNAL LOG // {s['code']} // {s['status']} — {s['reaction']}"
        return cards,note
    rb._structured_cards=cards_with_signal
    try:
        for m in missions:
            n=int(m["number"]); prog=min(.98,.035+n*.03); typ=m.get("type")
            if n>1 and typ in ("spatial","boss-spatial") and page%2==1:
                assert plan[f"{n:02d}_parity_pause"]==page
                parity_pause(c,data,m,page); page+=1
            assert plan[f"{n:02d}_brief"]==page
            if typ in ("spatial","boss-spatial"):
                witness_board(c,m,cases[m["spatial_source_id"]],page)
            else:
                mission_brief_page(c,data,m,page,prog)
            page+=1
            if typ in ("spatial","boss-spatial"):
                cid=m["spatial_source_id"]
                assert plan[f"{n:02d}_map"]==page
                map_page(c,m,ROOT/m["spatial"]["source_page_asset"],page,cases[cid]); page+=1
            else:
                assert plan[f"{n:02d}_puzzle"]==page
                puzzle_page(c,data,m,page,prog); page+=1
            if n in artifacts:
                assert plan[f"{n:02d}_artifact"]==page
                artifact_page(c,data,m,page); page+=1
            if n==30:
                assert plan["30_finale"]==page; finale_page(c,data,m,page); page+=1
                assert plan["certificate"]==page; certificate_page(c,data,page); page+=1
                assert plan["book2_scene"]==page; book2_scene_page(c,data,page); page+=1
            elif n in spine:
                assert plan[f"{n:02d}_act"]==page
                beat=copy.deepcopy(spine[n]); s=m["signal_log"]
                beat["eyebrow"]=f"SIGNAL LOG // {s['code']} // {beat['eyebrow']}"
                beat["progress"]=f"{s['status']} // {beat['progress']}"
                rb.big_case_wall_page(c,data,beat,page); page+=1
            elif n not in compact:
                assert plan[f"{n:02d}_signal"]==page
                signal_page(c,data,m,page,prog); page+=1
        assert plan["hints_level_1_cases_01_15"]==page
        page=hint_vault(c,data,missions,page)
        for m in missions:
            n=int(m["number"]); assert plan[f"{n:02d}_solution"]==page
            cid=m.get("spatial_source_id")
            if cid: solution_page(c,m,cases[cid],ROOT/m["spatial"]["solution_asset"],page)
            else: nonspatial_solution_page(c,m,page)
            page+=1
    finally:
        rb._structured_cards=original_cards
    c.save()
    if page-1!=plan["page_count"]: raise ValueError(f"rendered {page-1}, planned {plan['page_count']}")
    index_path=output.parent/"HMDA_Book1_EN_OwnerReview_v4_page_index.json"
    index_path.write_text(json.dumps(plan,indent=2),encoding="utf-8")
    return page-1,plan


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--master",required=True,type=Path)
    ap.add_argument("--runtime",required=True,type=Path)
    ap.add_argument("--maps",required=True,type=Path)
    ap.add_argument("--overrides",default=ROOT/"content/book1_v4_overrides.yml",type=Path)
    ap.add_argument("--aliases",default=ROOT/"content/spatial_character_aliases.yml",type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    data,cases,master,runtime=build_data(args.master.resolve(),args.runtime.resolve(),args.maps.resolve(),args.overrides.resolve(),args.aliases.resolve(),args.output.resolve())
    pages,index=render_v4(data,cases,master,args.output.resolve())
    sha=hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    print(f"PASS: V4 owner review rendered, {pages} pages")
    print(f"MASTER: {master}\nRUNTIME: {runtime}\nPDF: {args.output.resolve()}\nSHA256: {sha}")


if __name__=="__main__": main()
