from __future__ import annotations

import argparse
import math
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
PAGE_W, PAGE_H = letter
M = 0.48 * inch
BLACK = colors.HexColor('#0B0B0D')
CHARCOAL = colors.HexColor('#202126')
DARK = colors.HexColor('#34363D')
MID = colors.HexColor('#777A83')
LINE = colors.HexColor('#C7C9CE')
PALE = colors.HexColor('#EEEEF1')
PALE2 = colors.HexColor('#F7F7F8')
WHITE = colors.white


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'),
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/consola.ttf'),
    ]
    for regular, bold, mono in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont('RSE', regular))
            pdfmetrics.registerFont(TTFont('RSE-Bold', bold))
            if Path(mono).exists():
                pdfmetrics.registerFont(TTFont('RSE-Mono', mono))
                mono_name = 'RSE-Mono'
            else:
                mono_name = 'Courier'
            return 'RSE', 'RSE-Bold', mono_name
    return 'Helvetica', 'Helvetica-Bold', 'Courier'


FONT, BOLD, MONO = register_fonts()


def pstyle(size=10.0, leading=None, font=FONT, color=BLACK, align=0):
    return ParagraphStyle('p', fontName=font, fontSize=size, leading=leading or size * 1.27,
                          textColor=color, alignment=align, spaceBefore=0, spaceAfter=0)


def para(c, text, x, top, w, h, size=10.0, font=FONT, color=BLACK, align=0):
    text = (text or '').replace('\n', '<br/>')
    p = Paragraph(text, pstyle(size=size, font=font, color=color, align=align))
    _, used = p.wrap(w, h)
    p.drawOn(c, x, top - used)
    return used


def fit_para(c, text, x, top, w, h, max_size=11.0, min_size=7.4, font=FONT, color=BLACK, align=0):
    size = max_size
    while size >= min_size:
        p = Paragraph((text or '').replace('\n', '<br/>'), pstyle(size=size, font=font, color=color, align=align))
        _, used = p.wrap(w, h)
        if used <= h:
            p.drawOn(c, x, top - used)
            return used, size
        size -= 0.3
    p = Paragraph((text or '').replace('\n', '<br/>'), pstyle(size=min_size, font=font, color=color, align=align))
    _, used = p.wrap(w, h)
    p.drawOn(c, x, top - min(used, h))
    return used, min_size


def box(c, x, y, w, h, fill=WHITE, stroke=LINE, radius=10, sw=0.8):
    c.setLineWidth(sw)
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def pill(c, text, x, y, font_size=7.8, fill=BLACK, text_color=WHITE, pad_x=9, h=18):
    width = pdfmetrics.stringWidth(text, BOLD, font_size) + pad_x * 2
    c.setFillColor(fill)
    c.roundRect(x, y, width, h, h/2, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont(BOLD, font_size)
    c.drawCentredString(x + width/2, y + (h-font_size)/2 + 1.4, text)
    return width


def tiny_grid(c, x, y, w, h, step=12):
    c.saveState()
    c.setStrokeColor(colors.HexColor('#E8E8EB'))
    c.setLineWidth(0.25)
    xx = x
    while xx <= x+w:
        c.line(xx, y, xx, y+h)
        xx += step
    yy = y
    while yy <= y+h:
        c.line(x, yy, x+w, yy)
        yy += step
    c.restoreState()


def top_bar(c, label, page_no=None, progress=None):
    c.setFillColor(BLACK)
    c.rect(0, PAGE_H-0.48*inch, PAGE_W, 0.48*inch, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(BOLD, 8.4)
    c.drawString(M, PAGE_H-0.31*inch, 'HAPPY MAKERS DETECTIVE ACADEMY')
    c.setFont(MONO, 7.8)
    right = label.upper()
    if page_no is not None:
        right += f'  //  {page_no:03d}'
    c.drawRightString(PAGE_W-M, PAGE_H-0.31*inch, right)
    if progress is not None:
        y = PAGE_H-0.54*inch
        c.setFillColor(PALE)
        c.rect(M, y, PAGE_W-2*M, 3, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.rect(M, y, (PAGE_W-2*M)*max(0,min(1,progress)), 3, fill=1, stroke=0)


def footer(c, page_no=None):
    c.setStrokeColor(PALE)
    c.setLineWidth(0.5)
    c.line(M, 0.34*inch, PAGE_W-M, 0.34*inch)
    c.setFillColor(MID)
    c.setFont(FONT, 6.7)
    c.drawString(M, 0.20*inch, 'RISE.SHINE.EVOLVE.  //  OFFLINE MYSTERY ADVENTURE')
    if page_no is not None:
        c.drawRightString(PAGE_W-M, 0.20*inch, f'{page_no:03d}')


def preprocess_avatar(src: Path, dst: Path, size=512):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    im = Image.open(src).convert('L').convert('RGBA')
    side = min(im.size)
    left = (im.width-side)//2
    top = (im.height-side)//2
    im = im.crop((left, top, left+side, top+side)).resize((size,size), Image.Resampling.LANCZOS)
    mask = Image.new('L',(size,size),0)
    md = ImageDraw.Draw(mask)
    md.ellipse((5,5,size-5,size-5), fill=255)
    out = Image.new('RGBA',(size,size),(255,255,255,0))
    out.paste(im,(0,0),mask)
    draw = ImageDraw.Draw(out)
    draw.ellipse((5,5,size-5,size-5), outline=(25,25,25,255), width=max(3,size//80))
    out.save(dst)


def preprocess_crop(src: Path, crop, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    im = Image.open(src).convert('L')
    if crop:
        x1, y1, x2, y2 = crop
        im = im.crop((x1, y1, x2, y2))
    crop_im = ImageOps.autocontrast(im, cutoff=0.5)
    crop_im.save(dst, optimize=True)


def draw_image_fit(c, path: Path, x, y, w, h, preserve=True):
    if not path.exists():
        box(c,x,y,w,h,fill=PALE2,stroke=LINE)
        c.setFillColor(MID); c.setFont(MONO,7.4)
        c.drawCentredString(x+w/2,y+h/2,'ASSET MISSING')
        return
    with Image.open(path) as im:
        iw,ih = im.size
    if preserve:
        s=min(w/iw,h/ih)
        dw,dh=iw*s,ih*s
        dx=x+(w-dw)/2; dy=y+(h-dh)/2
    else:
        dx,dy,dw,dh=x,y,w,h
    c.drawImage(str(path),dx,dy,dw,dh,preserveAspectRatio=False,mask='auto')


def avatar_callout(c, chars, key, text, x, top, w, style='light', tag=None):
    info=chars[key]
    bg = CHARCOAL if style=='dark' else PALE2
    fg = WHITE if style=='dark' else BLACK
    stroke = CHARCOAL if style=='dark' else LINE
    h=0.86*inch
    box(c,x,top-h,w,h,fill=bg,stroke=stroke,radius=13,sw=0.8)
    av=ROOT/'cache'/'avatars'/f'{key}.png'
    preprocess_avatar(ROOT/info['asset'],av)
    s=0.62*inch
    draw_image_fit(c,av,x+0.10*inch,top-h+0.12*inch,s,s)
    c.setFillColor(fg); c.setFont(BOLD,8.5)
    c.drawString(x+0.83*inch, top-0.24*inch, f"{info['name']}  //  {(tag or info['tag']).upper()}")
    fit_para(c,text,x+0.83*inch,top-0.34*inch,w-0.98*inch,h-0.40*inch,max_size=9.2,min_size=7.4,font=FONT,color=fg)
    return h


def chapter_gate(c, title, subtitle, rank, page_no):
    c.setFillColor(BLACK); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    tiny_grid(c,0,0,PAGE_W,PAGE_H,step=20)
    c.setFillColor(WHITE)
    c.setFont(MONO,9)
    c.drawString(M,PAGE_H-0.80*inch,'ACADEMY ACCESS // NEW LEVEL')
    para(c,rank.upper(),M,PAGE_H-1.35*inch,PAGE_W-2*M,0.4*inch,size=11,font=BOLD,color=colors.HexColor('#BFC1C8'))
    para(c,title.upper(),M,PAGE_H-1.75*inch,PAGE_W-2*M,1.2*inch,size=30,font=BOLD,color=WHITE)
    para(c,subtitle,M,PAGE_H-3.05*inch,PAGE_W-2*M,1.0*inch,size=13,font=FONT,color=colors.HexColor('#D4D5D8'))
    c.setStrokeColor(colors.HexColor('#64666E')); c.setLineWidth(1)
    c.line(M,0.95*inch,PAGE_W-M,0.95*inch)
    c.setFont(BOLD,8.5); c.drawString(M,0.68*inch,'STATUS: MISSIONS UNLOCKED')
    c.setFont(MONO,7.5); c.drawRightString(PAGE_W-M,0.68*inch,f'PAGE {page_no:03d}')
    c.showPage()


def title_page(c, data):
    b=data['book']
    c.setFillColor(BLACK); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    tiny_grid(c,0,0,PAGE_W,PAGE_H,step=22)
    c.setStrokeColor(colors.HexColor('#3A3C43')); c.setLineWidth(8)
    c.circle(PAGE_W*0.77,PAGE_H*0.66,1.15*inch,stroke=1,fill=0)
    c.setFillColor(WHITE); c.setFont(MONO,9)
    c.drawString(M,PAGE_H-0.8*inch,'CASE SYSTEM // OFFLINE')
    para(c,b['title'],M,PAGE_H-1.55*inch,PAGE_W-2*M,1.4*inch,size=28,font=BOLD,color=WHITE)
    para(c,b['subtitle'],M,PAGE_H-2.82*inch,PAGE_W-2*M,0.7*inch,size=18,font=BOLD,color=colors.HexColor('#C8CAD0'))
    c.setFillColor(colors.HexColor('#B5B7BE')); c.setFont(MONO,8)
    c.drawString(M,PAGE_H-3.28*inch,b['strapline'])
    box(c,M,1.55*inch,PAGE_W-2*M,1.18*inch,fill=WHITE,stroke=WHITE,radius=14)
    c.setFillColor(BLACK); c.setFont(BOLD,10)
    c.drawString(M+0.22*inch,2.37*inch,'INCOMING MESSAGE')
    para(c,b['opening_code'],M+0.22*inch,2.18*inch,PAGE_W-2*M-0.44*inch,0.45*inch,size=15,font=BOLD,color=BLACK,align=1)
    c.setFillColor(colors.HexColor('#8D8F96')); c.setFont(MONO,7.2)
    c.drawString(M,0.62*inch,b['edition'].upper())
    c.showPage()


def acceptance_page(c,data,page_no):
    top_bar(c,'RECRUITMENT',page_no,0.02)
    o=data['opening']['acceptance_letter']
    y=PAGE_H-0.92*inch
    pill(c,'CLASSIFIED // RECRUITMENT',M,y-0.02*inch,7.4,fill=CHARCOAL)
    para(c,o['headline'],M,y-0.42*inch,PAGE_W-2*M,0.55*inch,size=20,font=BOLD)
    y-=1.15*inch
    box(c,M,y-2.45*inch,PAGE_W-2*M,2.3*inch,fill=PALE2,stroke=LINE,radius=15)
    c.setFont(MONO,7.7); c.setFillColor(MID)
    c.drawString(M+0.22*inch,y-0.25*inch,'SOURCE: UNKNOWN  //  DELIVERY: IMPOSSIBLE')
    para(c,o['body'],M+0.22*inch,y-0.52*inch,PAGE_W-2*M-0.44*inch,1.45*inch,size=11.4)
    y-=2.72*inch
    box(c,M,y-1.42*inch,PAGE_W-2*M,1.32*inch,fill=BLACK,stroke=BLACK,radius=15)
    c.setFillColor(WHITE); c.setFont(BOLD,9)
    c.drawString(M+0.22*inch,y-0.32*inch,'DETECTIVE ACADEMY // MEMBER ID')
    c.setFont(BOLD,15); c.drawString(M+0.22*inch,y-0.72*inch,'DETECTIVE NAME: ____________________')
    c.setFont(MONO,8); c.drawRightString(PAGE_W-M-0.22*inch,y-0.72*inch,'STATUS: INCOMPLETE')
    c.setStrokeColor(colors.HexColor('#767880')); c.setLineWidth(3); c.circle(PAGE_W-M-0.55*inch,y-1.02*inch,0.18*inch,stroke=1,fill=0)
    y-=1.70*inch
    avatar_callout(c,data['characters'],'mimi',o['note'],M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def squad_page(c,data,page_no):
    top_bar(c,'YOUR SQUAD',page_no,0.03)
    y=PAGE_H-0.90*inch
    para(c,'YOU ARE THE DETECTIVE.',M,y,PAGE_W-2*M,0.42*inch,size=21,font=BOLD)
    para(c,'THEY ARE YOUR SQUAD.',M,y-0.43*inch,PAGE_W-2*M,0.4*inch,size=17,font=BOLD,color=MID)
    y-=0.98*inch
    squad=data['characters']['squad']['asset']
    box(c,M,y-3.12*inch,PAGE_W-2*M,3.0*inch,fill=PALE2,stroke=LINE,radius=16)
    draw_image_fit(c,ROOT/squad,M+0.22*inch,y-2.92*inch,PAGE_W-2*M-0.44*inch,2.75*inch)
    y-=3.36*inch
    para(c,data['opening']['squad_intro'],M,y,PAGE_W-2*M,0.82*inch,size=10.5)
    y-=0.90*inch
    keys=['luli','dilo','alio','nini','mimi','bibi']
    col_w=(PAGE_W-2*M-0.18*inch)/2
    for idx,key in enumerate(keys):
        col=idx%2; row=idx//2
        x=M+col*(col_w+0.18*inch); top=y-row*0.82*inch
        info=data['characters'][key]
        box(c,x,top-0.70*inch,col_w,0.64*inch,fill=WHITE,stroke=LINE,radius=11)
        av=ROOT/'cache'/'avatars'/f'{key}.png'; preprocess_avatar(ROOT/info['asset'],av)
        draw_image_fit(c,av,x+0.07*inch,top-0.61*inch,0.48*inch,0.48*inch)
        c.setFillColor(BLACK); c.setFont(BOLD,8.5); c.drawString(x+0.63*inch,top-0.27*inch,info['name'])
        c.setFillColor(MID); c.setFont(MONO,6.9); c.drawString(x+0.63*inch,top-0.47*inch,info['tag'])
    footer(c,page_no); c.showPage()


def how_to_play_page(c,data,page_no):
    top_bar(c,'HOW TO PLAY',page_no,0.04)
    y=PAGE_H-0.9*inch
    para(c,'THIS BOOK PLAYS LIKE A GAME.',M,y,PAGE_W-2*M,0.5*inch,size=20,font=BOLD)
    para(c,'Only the controller is a pencil.',M,y-0.43*inch,PAGE_W-2*M,0.4*inch,size=12,font=FONT,color=MID)
    y-=1.08*inch
    for i,item in enumerate(data['opening']['how_to_play'],start=1):
        h=0.88*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.06*inch,fill=PALE2 if i%2 else WHITE,stroke=LINE,radius=12)
        c.setFillColor(BLACK); c.circle(M+0.28*inch,y-0.39*inch,0.16*inch,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont(BOLD,9); c.drawCentredString(M+0.28*inch,y-0.43*inch,str(i))
        fit_para(c,item,M+0.57*inch,y-0.20*inch,PAGE_W-2*M-0.75*inch,0.55*inch,max_size=9.6,min_size=8,font=FONT)
        y-=h
    y-=0.12*inch
    box(c,M,y-1.12*inch,PAGE_W-2*M,1.04*inch,fill=BLACK,stroke=BLACK,radius=13)
    c.setFillColor(WHITE); c.setFont(MONO,7.2); c.drawString(M+0.20*inch,y-0.28*inch,'RULE ZERO // ACADEMY CORE')
    para(c,data['book']['rule_zero'],M+0.20*inch,y-0.48*inch,PAGE_W-2*M-0.4*inch,0.45*inch,size=13.5,font=BOLD,color=WHITE,align=1)
    footer(c,page_no); c.showPage()


def detective_id_page(c,data,page_no):
    top_bar(c,'PLAYER PROFILE',page_no,0.05)
    y=PAGE_H-0.90*inch
    para(c,'BUILD YOUR DETECTIVE ID',M,y,PAGE_W-2*M,0.5*inch,size=20,font=BOLD)
    y-=0.74*inch
    box(c,M,y-4.1*inch,PAGE_W-2*M,3.95*inch,fill=PALE2,stroke=BLACK,radius=18,sw=1.2)
    c.setFillColor(BLACK); c.setFont(MONO,8)
    c.drawString(M+0.22*inch,y-0.32*inch,'DETECTIVE ACADEMY // ACTIVE RECRUIT')
    c.setFont(BOLD,14); c.drawString(M+0.22*inch,y-0.83*inch,'NAME  __________________________________')
    c.setFont(FONT,10); c.drawString(M+0.22*inch,y-1.33*inch,'Best detective skill: ______________________________')
    c.drawString(M+0.22*inch,y-1.82*inch,'Most suspicious snack: _____________________________')
    c.drawString(M+0.22*inch,y-2.31*inch,'Signature move: __________________________________')
    c.drawString(M+0.22*inch,y-2.80*inch,'What I do when I get stuck: ________________________')
    c.setStrokeColor(BLACK); c.setLineWidth(4); c.circle(PAGE_W-M-0.80*inch,y-3.22*inch,0.38*inch,stroke=1,fill=0)
    c.setFillColor(MID); c.setFont(MONO,7); c.drawCentredString(PAGE_W-M-0.80*inch,y-3.77*inch,'ZERO MARK')
    y-=4.45*inch
    avatar_callout(c,data['characters'],'nini','Stuck is not game over. It usually means you found the interesting part.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def mission_brief_page(c,data,m,page_no,progress):
    top_bar(c,m['status'],page_no,progress)
    y=PAGE_H-0.86*inch
    pill(c,f"{m['rank']} // CASE {m['number']:02d}",M,y-0.05*inch,7.3,fill=CHARCOAL)
    para(c,m['title'],M,y-0.43*inch,PAGE_W-2*M,0.72*inch,size=19.5,font=BOLD)
    y-=1.17*inch
    box(c,M,y-1.14*inch,PAGE_W-2*M,1.04*inch,fill=BLACK,stroke=BLACK,radius=13)
    c.setFillColor(WHITE); c.setFont(MONO,7.2); c.drawString(M+0.18*inch,y-0.26*inch,'MISSION BRIEF')
    fit_para(c,m['hook'],M+0.18*inch,y-0.45*inch,PAGE_W-2*M-0.36*inch,0.52*inch,max_size=10.2,min_size=8,font=FONT,color=WHITE)
    y-=1.35*inch
    c.setFillColor(MID); c.setFont(MONO,7.2); c.drawString(M,y-0.02*inch,'YOUR OBJECTIVE')
    para(c,m['objective'],M,y-0.15*inch,PAGE_W-2*M,0.52*inch,size=11.4,font=BOLD)
    y-=0.79*inch
    for d in m.get('dialogue',[]):
        h=avatar_callout(c,data['characters'],d['speaker'],d['text'],M,y,PAGE_W-2*M,style='light')
        y-=h+0.10*inch
    if y > 1.65*inch:
        box(c,M,0.62*inch,PAGE_W-2*M,0.72*inch,fill=PALE2,stroke=LINE,radius=11)
        c.setFillColor(BLACK); c.setFont(MONO,7.0)
        c.drawString(M+0.18*inch,1.06*inch,'CASE STATUS')
        c.setFont(BOLD,9.2); c.drawString(M+0.18*inch,0.80*inch,'OPEN // EVIDENCE NOT YET VERIFIED')
        c.setFont(MONO,6.9); c.drawRightString(PAGE_W-M-0.18*inch,0.84*inch,'PENCIL READY?')
    footer(c,page_no); c.showPage()


def draw_tutorial_grid(c,tut,x,y,w,h,solution=False):
    n=tut['size']; cw=w/n; ch=h/n
    c.setFillColor(WHITE); c.rect(x,y,w,h,fill=1,stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(0.6)
    for i in range(n+1):
        c.line(x+i*cw,y,x+i*cw,y+h); c.line(x,y+i*ch,x+w,y+i*ch)
    shades=[colors.HexColor('#F0F0F2'),colors.HexColor('#FAFAFA'),colors.HexColor('#E8E8EC'),colors.HexColor('#F6F6F8')]
    for idx,room in enumerate(tut['rooms']):
        for cell in room['cells']:
            col=ord(cell[0])-ord('A'); row=int(cell[1:])-1
            cy=y+h-(row+1)*ch
            c.setFillColor(shades[idx%len(shades)]); c.rect(x+col*cw,cy,cw,ch,fill=1,stroke=0)
        cell=room['cells'][0]; col=ord(cell[0])-65; row=int(cell[1:])-1
        cx=x+(col+0.08)*cw; cy=y+h-(row+0.20)*ch
        c.setFillColor(MID); c.setFont(MONO,5.9); c.drawString(cx,cy,room['name'])
    c.setStrokeColor(colors.HexColor('#B8BAC0')); c.setLineWidth(0.6)
    for i in range(n+1):
        c.line(x+i*cw,y,x+i*cw,y+h); c.line(x,y+i*ch,x+w,y+i*ch)
    c.setFillColor(BLACK); c.setFont(MONO,7)
    for i,col in enumerate(tut['cols']): c.drawCentredString(x+(i+0.5)*cw,y+h+8,col)
    for i,row in enumerate(tut['rows']): c.drawRightString(x-6,y+h-(i+0.56)*ch,str(row))
    if solution:
        for person,pos in tut['positions'].items():
            col=ord(pos[0])-65; row=int(pos[1:])-1
            cx=x+(col+0.5)*cw; cy=y+h-(row+0.5)*ch
            c.setFillColor(BLACK); c.circle(cx,cy,min(cw,ch)*0.23,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont(BOLD,6.5); c.drawCentredString(cx,cy-2.3,person[0])


def guided_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'TRAINING GRID',page_no,progress)
    y=PAGE_H-0.88*inch
    para(c,'LEARN THE GRID BY SOLVING IT',M,y,PAGE_W-2*M,0.46*inch,size=19,font=BOLD)
    para(c,'One exact clue at a time. No guessing required.',M,y-0.38*inch,PAGE_W-2*M,0.34*inch,size=10,color=MID)
    tut=m['tutorial']; y-=0.9*inch
    grid_h=3.25*inch
    draw_tutorial_grid(c,tut,M+0.35*inch,y-grid_h,PAGE_W-2*M-0.70*inch,grid_h,solution=False)
    y-=grid_h+0.25*inch
    colw=(PAGE_W-2*M-0.14*inch)/2
    for i,clue in enumerate(tut['clues'][:4]):
        col=i%2; row=i//2; x=M+col*(colw+0.14*inch); top=y-row*0.82*inch
        box(c,x,top-0.70*inch,colw,0.64*inch,fill=PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(MONO,6.5); c.drawString(x+0.12*inch,top-0.18*inch,f'CLUE {i+1:02d}')
        fit_para(c,clue,x+0.12*inch,top-0.30*inch,colw-0.24*inch,0.31*inch,max_size=8.1,min_size=6.9)
    y-=1.73*inch
    box(c,M,y-0.75*inch,PAGE_W-2*M,0.67*inch,fill=BLACK,stroke=BLACK,radius=11)
    para(c,'WHO WAS AT THE DELIVERY DESK?   YOUR VERDICT: ____________________',M+0.17*inch,y-0.22*inch,PAGE_W-2*M-0.34*inch,0.32*inch,size=9.2,font=BOLD,color=WHITE)
    footer(c,page_no); c.showPage()


def guided_steps_page(c,data,m,page_no,progress):
    top_bar(c,'TRAINING // STEP MODE',page_no,progress)
    y=PAGE_H-0.88*inch
    para(c,'THE GRID DOES NOT NEED A MAGIC TRICK.',M,y,PAGE_W-2*M,0.5*inch,size=18.5,font=BOLD)
    para(c,'It needs a next step.',M,y-0.38*inch,PAGE_W-2*M,0.34*inch,size=10.5,color=MID)
    y-=0.95*inch
    for idx,step in enumerate(m['tutorial']['guided_steps'],1):
        h=0.91*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.06*inch,fill=PALE2 if idx<4 else BLACK,stroke=LINE if idx<4 else BLACK,radius=12)
        fg=BLACK if idx<4 else WHITE
        c.setFillColor(fg); c.setFont(BOLD,8.5); c.drawString(M+0.18*inch,y-0.25*inch,f'STEP {idx:02d}')
        fit_para(c,step,M+0.18*inch,y-0.41*inch,PAGE_W-2*M-0.36*inch,0.38*inch,max_size=9.5,min_size=7.8,color=fg)
        y-=h
    y-=0.08*inch
    avatar_callout(c,data['characters'],'luli','Exact clues are free points. Take them before you wrestle with the clever ones.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def verdict_reveal_page(c,data,m,page_no,progress):
    top_bar(c,'CASE CLEARED',page_no,progress)
    y=PAGE_H-0.95*inch
    pill(c,'VERIFIED',M,y-0.03*inch,7.6,fill=BLACK)
    para(c,'YOUR FIRST CASE IS CLOSED.',M,y-0.43*inch,PAGE_W-2*M,0.55*inch,size=22,font=BOLD)
    y-=1.22*inch
    draw_tutorial_grid(c,m['tutorial'],M+0.7*inch,y-3.15*inch,PAGE_W-2*M-1.4*inch,3.15*inch,solution=True)
    y-=3.48*inch
    box(c,M,y-0.78*inch,PAGE_W-2*M,0.70*inch,fill=BLACK,stroke=BLACK,radius=12)
    para(c,m['tutorial']['verdict'],M+0.18*inch,y-0.22*inch,PAGE_W-2*M-0.36*inch,0.35*inch,size=10.8,font=BOLD,color=WHITE,align=1)
    y-=1.04*inch
    avatar_callout(c,data['characters'],'mimi','Good. Nobody guessed. Nobody panicked. One mug was moved without authorization, but we will handle that internally.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def meta_signal_page(c,data,m,page_no,progress):
    top_bar(c,'EVIDENCE UNLOCKED',page_no,progress)
    c.setFillColor(BLACK); c.circle(PAGE_W/2,PAGE_H*0.64,1.02*inch,fill=0,stroke=1)
    c.setLineWidth(8); c.setStrokeColor(BLACK); c.circle(PAGE_W/2,PAGE_H*0.64,0.82*inch,fill=0,stroke=1)
    c.setFillColor(BLACK); c.setFont(BOLD,60); c.drawCentredString(PAGE_W/2,PAGE_H*0.64-21,'0')
    para(c,'TURN THE BADGE OVER.',M,PAGE_H*0.46,PAGE_W-2*M,0.48*inch,size=18,font=BOLD,align=1)
    para(c,m['meta_reveal'],M,PAGE_H*0.42,PAGE_W-2*M,0.65*inch,size=10.8,align=1)
    y=2.05*inch
    avatar_callout(c,data['characters'],'dilo','Anonymous symbol. Secret badge. Zero sender. This is statistically suspicious.',M,y,PAGE_W-2*M)
    y-=0.98*inch
    avatar_callout(c,data['characters'],'luli','You invented that statistic.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def prepare_crop_asset(m,kind='spatial') -> Path | None:
    if kind!='spatial': return None
    sp=m['spatial']; src=ROOT/sp['source_page_asset']; crop=sp['crop']
    dst=ROOT/'cache'/'crops'/f"case{m['number']:02d}_grid.png"
    preprocess_crop(src,crop,dst); return dst


def spatial_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'DEDUCTION GRID',page_no,progress)
    y=PAGE_H-0.86*inch
    pill(c,f"CASE {m['number']:02d} // GRID",M,y-0.02*inch,7.3,fill=CHARCOAL)
    para(c,m['title'],M,y-0.42*inch,PAGE_W-2*M,0.52*inch,size=17.5,font=BOLD)
    y-=0.96*inch
    crop=prepare_crop_asset(m)
    grid_h=3.02*inch
    box(c,M,y-grid_h,PAGE_W-2*M,grid_h,fill=WHITE,stroke=LINE,radius=13)
    draw_image_fit(c,crop,M+0.12*inch,y-grid_h+0.10*inch,PAGE_W-2*M-0.24*inch,grid_h-0.20*inch)
    y-=grid_h+0.18*inch
    c.setFillColor(MID); c.setFont(MONO,6.8); c.drawString(M,y,'WITNESS CLUES // TICK EACH ONE AFTER YOU USE IT')
    y-=0.16*inch
    clues=m['spatial']['clue_cards']; colw=(PAGE_W-2*M-0.12*inch)/2
    cardh=0.72*inch
    for idx,clue in enumerate(clues):
        col=idx%2; row=idx//2; x=M+col*(colw+0.12*inch); top=y-row*(cardh+0.08*inch)
        box(c,x,top-cardh,colw,cardh,fill=PALE2,stroke=LINE,radius=9)
        c.setFillColor(WHITE); c.setStrokeColor(MID); c.rect(x+0.10*inch,top-0.22*inch,9,9,fill=1,stroke=1)
        fit_para(c,clue,x+0.28*inch,top-0.16*inch,colw-0.38*inch,cardh-0.12*inch,max_size=7.8,min_size=6.4)
    box(c,M,0.59*inch,PAGE_W-2*M,0.70*inch,fill=BLACK,stroke=BLACK,radius=11)
    para(c,'YOUR VERDICT: _______________________________________________',M+0.17*inch,1.04*inch,PAGE_W-2*M-0.34*inch,0.28*inch,size=9.5,font=BOLD,color=WHITE)
    footer(c,page_no); c.showPage()


def meta_strip(c,data,m,page_no,progress):
    top_bar(c,'AFTER-CASE SIGNAL',page_no,progress)
    y=PAGE_H-1.05*inch
    para(c,'CASE CLOSED. SOMETHING ELSE JUST OPENED.',M,y,PAGE_W-2*M,0.55*inch,size=20,font=BOLD)
    y-=0.92*inch
    box(c,M,y-2.2*inch,PAGE_W-2*M,2.05*inch,fill=BLACK,stroke=BLACK,radius=16)
    c.setFillColor(WHITE); c.setFont(BOLD,56); c.drawCentredString(PAGE_W/2,y-1.12*inch,'0')
    c.setFont(MONO,7.2); c.drawCentredString(PAGE_W/2,y-1.65*inch,'RECURRING MARK // SOURCE UNKNOWN')
    y-=2.50*inch
    para(c,m['meta_reveal'],M,y,PAGE_W-2*M,0.68*inch,size=11.2,align=1)
    y-=0.95*inch
    guide=m['guides'][0]
    reaction = 'That mark again. Do not solve it yet. Just notice it.' if guide!='alio' else 'I am officially promoting the symbol from weird to very weird.'
    avatar_callout(c,data['characters'],guide,reaction,M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def visual_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'VISUAL EVIDENCE',page_no,progress)
    y=PAGE_H-0.87*inch
    para(c,'LOOK TWICE. ONLY THREE CHANGES MATTER.',M,y,PAGE_W-2*M,0.48*inch,size=18.5,font=BOLD)
    y-=0.72*inch
    gap=0.18*inch; pw=(PAGE_W-2*M-gap)/2; ph=3.42*inch
    for i,label in enumerate(['PHOTO A // 15:42','PHOTO B // 15:43']):
        x=M+i*(pw+gap)
        box(c,x,y-ph,pw,ph,fill=PALE2,stroke=LINE,radius=13)
        c.setFillColor(BLACK); c.setFont(MONO,7); c.drawString(x+0.12*inch,y-0.20*inch,label)
        c.setFillColor(WHITE); c.setStrokeColor(DARK); c.setLineWidth(1)
        c.rect(x+0.28*inch,y-1.12*inch,pw-0.56*inch,0.55*inch,fill=1,stroke=1)
        c.setFillColor(DARK); c.rect(x+0.56*inch,y-1.02*inch,0.34*inch,0.34*inch,fill=1,stroke=0)
        c.setStrokeColor(BLACK); c.setLineWidth(2)
        if i==0:
            c.line(x+1.02*inch,y-0.84*inch,x+1.30*inch,y-0.68*inch); c.line(x+1.02*inch,y-0.84*inch,x+0.78*inch,y-0.66*inch)
            tag='0417'; arrow=1
        else:
            c.line(x+1.02*inch,y-0.84*inch,x+0.76*inch,y-0.68*inch); c.line(x+1.02*inch,y-0.84*inch,x+1.28*inch,y-0.66*inch)
            tag='0471'; arrow=-1
        c.setFillColor(WHITE); c.setStrokeColor(BLACK); c.roundRect(x+0.42*inch,y-1.92*inch,1.0*inch,0.48*inch,7,fill=1,stroke=1)
        c.setFillColor(BLACK); c.setFont(MONO,10); c.drawCentredString(x+0.92*inch,y-1.72*inch,tag)
        c.setFillColor(DARK); c.ellipse(x+1.72*inch,y-2.12*inch,x+2.02*inch,y-1.70*inch,fill=1,stroke=0)
        c.setStrokeColor(BLACK); c.setLineWidth(2)
        ax=x+2.15*inch; ay=y-1.90*inch
        if arrow>0:
            c.line(ax-0.25*inch,ay,ax+0.20*inch,ay); c.line(ax+0.20*inch,ay,ax+0.06*inch,ay+0.10*inch); c.line(ax+0.20*inch,ay,ax+0.06*inch,ay-0.10*inch)
        else:
            c.line(ax+0.25*inch,ay,ax-0.20*inch,ay); c.line(ax-0.20*inch,ay,ax-0.06*inch,ay+0.10*inch); c.line(ax-0.20*inch,ay,ax-0.06*inch,ay-0.10*inch)
        c.setFont(BOLD,11); c.drawString(x+0.44*inch,y-2.55*inch,'*  *  *' if i==0 else '*  *  *  *')
        c.setFont(FONT,8); c.drawString(x+0.44*inch,y-2.82*inch,'cup handle >' if i==0 else '< cup handle')
        c.setStrokeColor(MID); c.line(x+0.50*inch,y-3.05*inch,x+1.25*inch,y-3.05*inch)
    y-=ph+0.20*inch
    avatar_callout(c,data['characters'],'luli','Do not count differences. Rank them. Which ones can change who, when or where?',M,y,PAGE_W-2*M)
    box(c,M,0.58*inch,PAGE_W-2*M,0.68*inch,fill=BLACK,stroke=BLACK,radius=11)
    para(c,'CIRCLE 3 MEANINGFUL CHANGES.  IGNORE THE NOISE.',M+0.15*inch,1.00*inch,PAGE_W-2*M-0.30*inch,0.28*inch,size=9.0,font=BOLD,color=WHITE,align=1)
    footer(c,page_no); c.showPage()


def code_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'CODE DROP',page_no,progress)
    y=PAGE_H-0.87*inch
    para(c,'FOUR SLOTS. FOUR SYMBOLS. ONE ORDER.',M,y,PAGE_W-2*M,0.50*inch,size=19,font=BOLD)
    para(c,'No random tapping. The keypad is offline anyway.',M,y-0.38*inch,PAGE_W-2*M,0.34*inch,size=10.2,color=MID)
    y-=1.00*inch
    slotw=1.18*inch; gap=0.12*inch; total=4*slotw+3*gap; sx=(PAGE_W-total)/2
    for i in range(4):
        box(c,sx+i*(slotw+gap),y-1.0*inch,slotw,0.90*inch,fill=BLACK,stroke=BLACK,radius=14)
        c.setFillColor(colors.HexColor('#7A7C83')); c.setFont(MONO,8); c.drawCentredString(sx+i*(slotw+gap)+slotw/2,y-0.62*inch,f'SLOT {i+1}')
    y-=1.32*inch
    labels=m['code']['symbols']; chipw=(PAGE_W-2*M-0.30*inch)/4
    for i,sym in enumerate(labels):
        x=M+i*(chipw+0.10*inch)
        box(c,x,y-0.62*inch,chipw,0.56*inch,fill=PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(BOLD,8.4); c.drawCentredString(x+chipw/2,y-0.38*inch,sym)
    y-=0.93*inch
    c.setFillColor(MID); c.setFont(MONO,7.0); c.drawString(M,y,'CODE RULES')
    y-=0.15*inch
    for idx,clue in enumerate(m['code']['clues'],1):
        h=0.65*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.05*inch,fill=WHITE if idx%2 else PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(BOLD,8); c.drawString(M+0.14*inch,y-0.22*inch,f'{idx:02d}')
        para(c,clue,M+0.44*inch,y-0.17*inch,PAGE_W-2*M-0.58*inch,0.34*inch,size=8.8)
        y-=h
    y-=0.12*inch
    avatar_callout(c,data['characters'],'dilo','If you are about to try random orders, I respect the chaos. Luli does not.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def preview_end_page(c,data,page_no):
    top_bar(c,'ROOKIE ACCESS',page_no,0.18)
    y=PAGE_H-0.95*inch
    para(c,data['preview_end']['headline'],M,y,PAGE_W-2*M,0.55*inch,size=21,font=BOLD)
    y-=0.82*inch
    para(c,data['preview_end']['body'],M,y,PAGE_W-2*M,0.95*inch,size=11.2)
    y-=1.15*inch
    box(c,M,y-1.45*inch,PAGE_W-2*M,1.35*inch,fill=BLACK,stroke=BLACK,radius=15)
    c.setFillColor(WHITE); c.setFont(MONO,7.2); c.drawString(M+0.18*inch,y-0.28*inch,'ROOM ZERO SIGNALS FOUND')
    c.setFont(BOLD,33); c.drawString(M+0.18*inch,y-0.86*inch,'05')
    c.setFont(MONO,8); c.drawString(M+1.05*inch,y-0.78*inch,'STATUS: PATTERN NOT YET EXPLAINED')
    y-=1.78*inch
    for d in data['preview_end']['dialogue']:
        h=avatar_callout(c,data['characters'],d['speaker'],d['text'],M,y,PAGE_W-2*M)
        y-=h+0.09*inch
    footer(c,page_no); c.showPage()


def hint_vault_page(c,data,missions,page_no):
    top_bar(c,'HINT VAULT',page_no,0.19)
    y=PAGE_H-0.90*inch
    para(c,'STUCK? GOOD. PICK THE SMALLEST NUDGE.',M,y,PAGE_W-2*M,0.48*inch,size=18.5,font=BOLD)
    para(c,'Hints are separated from the cases so you cannot accidentally spoil the next step.',M,y-0.37*inch,PAGE_W-2*M,0.42*inch,size=9.7,color=MID)
    y-=0.95*inch
    for m in missions:
        h=0.88*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.06*inch,fill=PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(BOLD,8.2); c.drawString(M+0.14*inch,y-0.24*inch,f"CASE {m['number']:02d} // NINI NUDGE")
        fit_para(c,m.get('nudge','Look for the most exact clue first.'),M+0.14*inch,y-0.40*inch,PAGE_W-2*M-0.28*inch,0.36*inch,max_size=8.4,min_size=7)
        y-=h
        if y < 1.30*inch:
            footer(c,page_no); c.showPage(); page_no+=1; top_bar(c,'HINT VAULT',page_no,0.19); y=PAGE_H-0.84*inch
    footer(c,page_no); c.showPage(); return page_no+1


def solutions_pages(c,data,missions,page_no):
    for m in missions:
        top_bar(c,f"SOLUTION // CASE {m['number']:02d}",page_no,0.20)
        y=PAGE_H-0.90*inch
        para(c,m['title'],M,y,PAGE_W-2*M,0.55*inch,size=18,font=BOLD)
        y-=0.75*inch
        if m['type']=='spatial':
            sp=m['spatial']; src=ROOT/sp['solution_asset']; dst=ROOT/'cache'/'crops'/f"case{m['number']:02d}_solution.png"
            preprocess_crop(src,sp['solution_crop'],dst)
            box(c,M,y-3.0*inch,PAGE_W-2*M,2.88*inch,fill=WHITE,stroke=LINE,radius=12)
            draw_image_fit(c,dst,M+0.12*inch,y-2.88*inch,PAGE_W-2*M-0.24*inch,2.65*inch)
            y-=3.12*inch
        elif m['type']=='guided':
            draw_tutorial_grid(c,m['tutorial'],M+1.0*inch,y-2.35*inch,PAGE_W-2*M-2.0*inch,2.35*inch,solution=True)
            y-=2.58*inch
        elif m['type']=='code':
            ans='  >  '.join(m['code']['answer'])
            box(c,M,y-0.72*inch,PAGE_W-2*M,0.64*inch,fill=BLACK,stroke=BLACK,radius=11)
            para(c,ans,M+0.18*inch,y-0.22*inch,PAGE_W-2*M-0.36*inch,0.30*inch,size=11.4,font=BOLD,color=WHITE,align=1)
            y-=0.94*inch
        elif m['type']=='visual':
            ans=m['visual']['answer'].replace(' + ','  /  ')
            box(c,M,y-0.80*inch,PAGE_W-2*M,0.70*inch,fill=BLACK,stroke=BLACK,radius=11)
            fit_para(c,ans,M+0.16*inch,y-0.23*inch,PAGE_W-2*M-0.32*inch,0.36*inch,max_size=10,min_size=8,font=BOLD,color=WHITE,align=1)
            y-=1.0*inch
        c.setFillColor(MID); c.setFont(MONO,7); c.drawString(M,y,'HOW THE CASE FALLS INTO PLACE')
        y-=0.17*inch
        for idx,step in enumerate(m['solution_steps'],1):
            h=0.62*inch
            box(c,M,y-h,PAGE_W-2*M,h-0.05*inch,fill=PALE2,stroke=LINE,radius=9)
            c.setFillColor(BLACK); c.setFont(BOLD,7.7); c.drawString(M+0.14*inch,y-0.22*inch,f'{idx:02d}')
            fit_para(c,step,M+0.43*inch,y-0.17*inch,PAGE_W-2*M-0.57*inch,0.32*inch,max_size=8.5,min_size=6.9)
            y-=h
            if y<0.95*inch: break
        footer(c,page_no); c.showPage(); page_no+=1
    return page_no


def render(data_path: Path, output: Path):
    global ROOT
    ROOT=data_path.resolve().parent.parent
    data=yaml.safe_load(data_path.read_text(encoding='utf-8'))
    output.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(output),pagesize=letter,pageCompression=1)
    c.setTitle(f"{data['book']['title']} - {data['book']['subtitle']}")
    c.setAuthor('Rise.Shine.Evolve.')
    title_page(c,data)
    page=2
    acceptance_page(c,data,page); page+=1
    squad_page(c,data,page); page+=1
    how_to_play_page(c,data,page); page+=1
    detective_id_page(c,data,page); page+=1
    chapter_gate(c,'ROOKIE FILES','Short cases. Bold clues. One symbol that refuses to stay in the background.','ROOKIE',page); page+=1
    missions=data['missions']
    m=missions[0]; prog=0.07
    mission_brief_page(c,data,m,page,prog); page+=1
    guided_puzzle_page(c,data,m,page,prog); page+=1
    guided_steps_page(c,data,m,page,prog); page+=1
    verdict_reveal_page(c,data,m,page,prog); page+=1
    meta_signal_page(c,data,m,page,prog); page+=1
    for m in missions[1:]:
        prog=0.07 + m['number']*0.018
        mission_brief_page(c,data,m,page,prog); page+=1
        if m['type']=='spatial':
            spatial_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1
        elif m['type']=='visual':
            visual_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1
        elif m['type']=='code':
            code_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1
    preview_end_page(c,data,page); page+=1
    page=hint_vault_page(c,data,missions,page)
    page=solutions_pages(c,data,missions,page)
    c.save()
    return page-1


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--content',default='content/book1_en_production.yml')
    ap.add_argument('--output',default='dist/HMDA_Book1_Production_Preview_v1.pdf')
    args=ap.parse_args()
    content=Path(args.content)
    if not content.is_absolute(): content=(Path.cwd()/content).resolve()
    output=Path(args.output)
    if not output.is_absolute(): output=(Path.cwd()/output).resolve()
    pages=render(content,output)
    print(f'Built {output} ({pages} pages)')

if __name__=='__main__':
    main()
