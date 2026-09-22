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
BLACK = colors.black
CHARCOAL = colors.HexColor('#202020')
DARK = colors.HexColor('#343434')
MID = colors.HexColor('#777777')
LINE = colors.HexColor('#C7C7C7')
PALE = colors.HexColor('#EEEEEE')
PALE2 = colors.HexColor('#F7F7F7')
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
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)


def pstyle(size=11, leading=None, font=FONT, color=BLACK, align=0):
    return ParagraphStyle('p', fontName=font, fontSize=size, leading=leading or size * 1.27,
                          textColor=color, alignment=align, spaceBefore=0, spaceAfter=0)


def text_height(text, w, size=11, font=FONT):
    p = Paragraph((text or '').replace('\n', '<br/>'), pstyle(size=size, font=font))
    return p.wrap(w, PAGE_H)[1]


def label(c, text, x, y, color=BLACK, size=9.5):
    c.setFillColor(color); c.setFont(BOLD, size); c.drawString(x, y, text)


def text_card(c, text, x, top, w, heading=None, size=11, fill=WHITE, stroke=LINE, font=FONT):
    padding=12
    used=text_height(text,w-2*padding,size,font)
    heading_h=19 if heading else 0
    h=used+2*padding+heading_h
    box(c,x,top-h,w,h,fill=fill,stroke=stroke,radius=10)
    if heading: label(c,heading,x+padding,top-padding-8)
    para(c,text,x+padding,top-padding-heading_h,w-2*padding,used+0.1,size=size,font=font)
    return h


def writing_card(c, title, x, top, w, h=70):
    box(c,x,top-h,w,h,fill=WHITE,stroke=BLACK,radius=11,sw=1.2)
    label(c,title,x+13,top-20)
    c.setStrokeColor(BLACK); c.setLineWidth(0.8)
    c.line(x+13,top-h+15,x+w-13,top-h+15)
    return h

def para(c, text, x, top, w, h, size=11, font=FONT, color=BLACK, align=0):
    text = (text or '').replace('\n', '<br/>')
    p = Paragraph(text, pstyle(size=size, font=font, color=color, align=align))
    _, used = p.wrap(w, h)
    if used > h + 0.5:
        raise ValueError(f'Page {c.getPageNumber()}: paragraph overflow ({used:.1f}pt > {h:.1f}pt), {text[:110]!r}')
    if top-used < 30 or top > PAGE_H-30:
        raise ValueError(f'Page {c.getPageNumber()}: paragraph outside safe page area: {text[:90]!r}')
    p.drawOn(c, x, top - used)
    return used

def fit_para(c, text, x, top, w, h, max_size=11.0, min_size=11.0, font=FONT, color=BLACK, align=0):
    # A layout must earn its font size. Never rescue an overflowing case by
    # silently reducing its required reading copy to microtype.
    size=max(11.0,max_size)
    used=para(c,text,x,top,w,h,size=size,font=font,color=color,align=align)
    return used,size

def box(c, x, y, w, h, fill=WHITE, stroke=LINE, radius=10, sw=0.8):
    c.setLineWidth(sw)
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def pill(c, text, x, y, font_size=9.5, fill=BLACK, text_color=WHITE, pad_x=9, h=18):
    font_size=max(9.5,font_size)
    width = pdfmetrics.stringWidth(text, BOLD, font_size) + pad_x * 2
    c.setFillColor(fill)
    c.roundRect(x, y, width, h, h/2, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont(BOLD, font_size)
    c.drawCentredString(x + width/2, y + (h-font_size)/2 + 1.4, text)
    return width


def tiny_grid(c, x, y, w, h, step=12):
    c.saveState()
    c.setStrokeColor(colors.HexColor('#E8E8E8'))
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
    # Letter no-bleed interior: graphic edges stay inside the trim-safe area.
    c.setFillColor(BLACK)
    c.rect(M,PAGE_H-43,PAGE_W-2*M,25,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont(BOLD,9.5)
    c.drawString(M+9,PAGE_H-34,'DETECTIVE ACADEMY')
    c.setFont(MONO,9.5)
    right=label.upper()
    if page_no is not None: right+=f'  //  {page_no:03d}'
    c.drawRightString(PAGE_W-M-9,PAGE_H-34,right)
    if progress is not None:
        y=PAGE_H-50
        c.setFillColor(PALE); c.rect(M,y,PAGE_W-2*M,3,fill=1,stroke=0)
        c.setFillColor(BLACK); c.rect(M,y,(PAGE_W-2*M)*max(0,min(1,progress)),3,fill=1,stroke=0)


def footer(c, page_no=None):
    c.setStrokeColor(PALE)
    c.setLineWidth(0.5)
    # Keep the page number; remove repeating micro-brand chrome that competes
    # with child-facing instructions and pencil space.
    c.setFillColor(BLACK)
    c.setFont(FONT,9.5)
    if page_no is not None:
        c.drawRightString(PAGE_W-M, 0.30*inch, f'{page_no:03d}')


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
    # White-map treatment: retain dark walls, labels and object art while
    # lifting the neutral Shigai paper/grid field to clean print white.
    crop_im = crop_im.point(lambda value: 255 if value >= 205 else value)
    crop_im.save(dst, optimize=True)


def draw_image_fit(c, path: Path, x, y, w, h, preserve=True):
    if not path.exists():
        box(c,x,y,w,h,fill=PALE2,stroke=LINE)
        c.setFillColor(BLACK); c.setFont(MONO,9.5)
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
    bg=CHARCOAL if style=='dark' else PALE2
    fg=WHITE if style=='dark' else BLACK
    body_w=w-76
    body_h=text_height(text,body_w,11)
    h=max(70,body_h+38)
    box(c,x,top-h,w,h,fill=bg,stroke=LINE,radius=12)
    av=ROOT/'cache'/'avatars'/f'{key}.png'
    preprocess_avatar(ROOT/info['asset'],av)
    draw_image_fit(c,av,x+9,top-h+12,45,45)
    label(c,info['name'],x+64,top-19,color=fg)
    para(c,text,x+64,top-29,body_w,body_h+0.1,size=11,color=fg)
    return h

def chapter_gate(c, title, subtitle, rank, page_no):
    c.setFillColor(BLACK); c.rect(M,PAGE_H-2.65*inch,PAGE_W-2*M,2.65*inch-18,fill=1,stroke=0)
    # Keep the dossier grid in the side rail; clear dark paper sits under text.
    tiny_grid(c,PAGE_W-M-45,PAGE_H-2.65*inch,45,2.65*inch-18,step=20)
    label(c,'ACADEMY ACCESS // NEW LEVEL',M+14,PAGE_H-0.80*inch,color=WHITE)
    para(c,rank.upper(),M+14,PAGE_H-1.23*inch,PAGE_W-2*M-0.65*inch,30,size=12.0,font=BOLD,color=WHITE)
    para(c,title.upper(),M+14,PAGE_H-1.70*inch,PAGE_W-2*M-0.65*inch,60,size=28.0,font=BOLD,color=WHITE)
    c.setStrokeColor(LINE); c.setLineWidth(5)
    c.circle(PAGE_W*0.80,PAGE_H*0.50,0.95*inch,stroke=1,fill=0)
    c.setFillColor(BLACK); c.setFont(BOLD,34.0)
    c.drawCentredString(PAGE_W*0.80,PAGE_H*0.50-12,rank[:1].upper())
    text_card(c,subtitle,M,PAGE_H-3.80*inch,PAGE_W-2*M,heading='WHAT CHANGES NOW',size=12.5,fill=PALE2)
    label(c,'STATUS: MISSIONS UNLOCKED',M,0.68*inch)
    footer(c,page_no); c.showPage()

def title_page(c, data):
    b=data['book']
    panel_h=4.15*inch
    c.setFillColor(BLACK); c.rect(M,PAGE_H-panel_h,PAGE_W-2*M,panel_h-18,fill=1,stroke=0)
    tiny_grid(c,PAGE_W-M-34,PAGE_H-panel_h,34,panel_h-18,step=22)
    label(c,'CASE SYSTEM // OFFLINE',M+14,PAGE_H-0.80*inch,color=WHITE)
    para(c,b['title'],M+14,PAGE_H-1.28*inch,PAGE_W-2*M-62,1.35*inch,size=27.0,font=BOLD,color=WHITE)
    para(c,b['subtitle'],M+14,PAGE_H-2.68*inch,PAGE_W-2*M-62,0.64*inch,size=17.5,font=BOLD,color=WHITE)
    para(c,b['strapline'],M+14,PAGE_H-3.37*inch,PAGE_W-2*M-62,0.42*inch,size=11,color=WHITE)
    y=PAGE_H-panel_h-0.55*inch
    label(c,'INCOMING MESSAGE // PRIORITY',M,y)
    para(c,b['opening_code'],M,y-0.32*inch,PAGE_W-2*M,0.75*inch,size=18.0,font=BOLD,align=1)
    y-=1.28*inch
    box(c,M,y-1.42*inch,PAGE_W-2*M,1.42*inch,fill=WHITE,stroke=BLACK,radius=16,sw=1.0)
    label(c,'DETECTIVE SLOT // 06',M+16,y-24)
    label(c,'STATUS: EMPTY',PAGE_W-M-115,y-24)
    c.setStrokeColor(BLACK); c.setLineWidth(3); c.circle(PAGE_W/2,y-68,19,stroke=1,fill=0)
    c.setFillColor(BLACK); c.setFont(BOLD,20.0); c.drawCentredString(PAGE_W/2,y-75,'?')
    if str(b.get('edition','')).strip():
        label(c,str(b['edition']).upper(),M,0.62*inch)
    c.showPage()

def acceptance_page(c,data,page_no):
    top_bar(c,'RECRUITMENT',page_no,0.02)
    o=data['opening']['acceptance_letter']
    y=PAGE_H-0.92*inch
    pill(c,'CLASSIFIED // RECRUITMENT',M,y-0.14*inch,7.4,fill=CHARCOAL)
    para(c,o['headline'],M,y-0.42*inch,PAGE_W-2*M,0.55*inch,size=20.0,font=BOLD)
    y-=1.15*inch
    box(c,M,y-2.45*inch,PAGE_W-2*M,2.3*inch,fill=PALE2,stroke=LINE,radius=15)
    c.setFont(MONO,9.5); c.setFillColor(BLACK)
    c.drawString(M+0.22*inch,y-0.35*inch,'SOURCE: UNKNOWN  //  DELIVERY: IMPOSSIBLE')
    para(c,o['body'],M+0.22*inch,y-0.65*inch,PAGE_W-2*M-0.44*inch,1.45*inch,size=11.4)
    y-=2.72*inch
    # The final Player Profile page is the single pencil-friendly Detective
    # ID.  Do not duplicate an earlier name-entry panel here.
    box(c,M,y-0.76*inch,PAGE_W-2*M,0.66*inch,fill=WHITE,stroke=BLACK,radius=13)
    c.setFillColor(BLACK); c.setFont(BOLD,10.0)
    c.drawString(M+0.22*inch,y-0.31*inch,'YOUR ACADEMY INVITATION IS READY.')
    y-=1.10*inch
    avatar_callout(c,data['characters'],'mimi',o['note'],M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def squad_page(c,data,page_no):
    top_bar(c,'YOUR SQUAD',page_no,0.03)
    y=PAGE_H-0.90*inch
    para(c,'YOU ARE THE DETECTIVE.',M,y,PAGE_W-2*M,0.42*inch,size=21.0,font=BOLD)
    para(c,'THEY ARE YOUR SQUAD.',M,y-0.43*inch,PAGE_W-2*M,0.4*inch,size=17.0,font=BOLD,color=BLACK)
    y-=0.98*inch
    squad=data['characters']['squad']['asset']
    box(c,M,y-3.12*inch,PAGE_W-2*M,3.0*inch,fill=PALE2,stroke=LINE,radius=16)
    draw_image_fit(c,ROOT/squad,M+0.22*inch,y-2.92*inch,PAGE_W-2*M-0.44*inch,2.75*inch)
    y-=3.36*inch
    para(c,data['opening']['squad_intro'],M,y,PAGE_W-2*M,0.82*inch,size=11)
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
        c.setFillColor(BLACK); c.setFont(BOLD,9.5); c.drawString(x+0.63*inch,top-0.27*inch,info['name'])
        c.setFillColor(BLACK); c.setFont(MONO,9.5); c.drawString(x+0.63*inch,top-0.47*inch,info['tag'])
    footer(c,page_no); c.showPage()


def how_to_play_page(c,data,page_no):
    top_bar(c,'HOW TO PLAY',page_no,0.04)
    y=PAGE_H-0.9*inch
    para(c,'THIS BOOK PLAYS LIKE A GAME.',M,y,PAGE_W-2*M,0.5*inch,size=20.0,font=BOLD)
    para(c,'Only the controller is a pencil.',M,y-0.43*inch,PAGE_W-2*M,0.4*inch,size=12.0,font=FONT,color=BLACK)
    y-=1.08*inch
    for i,item in enumerate(data['opening']['how_to_play'],start=1):
        h=0.88*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.06*inch,fill=PALE2 if i%2 else WHITE,stroke=LINE,radius=12)
        c.setFillColor(BLACK); c.circle(M+0.28*inch,y-0.39*inch,0.16*inch,fill=1,stroke=0)
        c.setFillColor(WHITE); c.setFont(BOLD,9.5); c.drawCentredString(M+0.28*inch,y-0.43*inch,str(i))
        fit_para(c,item,M+0.57*inch,y-0.20*inch,PAGE_W-2*M-0.75*inch,0.55*inch,max_size=11,min_size=11,font=FONT)
        y-=h
    y-=0.12*inch
    box(c,M,y-1.12*inch,PAGE_W-2*M,1.04*inch,fill=BLACK,stroke=BLACK,radius=13)
    c.setFillColor(WHITE); c.setFont(MONO,9.5); c.drawString(M+0.20*inch,y-0.28*inch,'RULE ZERO // ACADEMY CORE')
    para(c,data['book']['rule_zero'],M+0.20*inch,y-0.48*inch,PAGE_W-2*M-0.4*inch,0.45*inch,size=13.5,font=BOLD,color=WHITE,align=1)
    footer(c,page_no); c.showPage()


def detective_id_page(c,data,page_no):
    top_bar(c,'PLAYER PROFILE',page_no,0.05)
    y=PAGE_H-0.90*inch
    para(c,'BUILD YOUR DETECTIVE ID',M,y,PAGE_W-2*M,40,size=20.0,font=BOLD)
    y-=60
    fields=['DETECTIVE NAME','BEST DETECTIVE SKILL','MOST SUSPICIOUS SNACK','SIGNATURE MOVE','WHAT I DO WHEN I GET STUCK','CASE WALL // FACTS & ZERO MARKS']
    for idx,title in enumerate(fields):
        h=72 if idx==5 else 61
        writing_card(c,title,M,y,PAGE_W-2*M,h)
        y-=h+9
    y-=5
    avatar_callout(c,data['characters'],'nini','Stuck is not game over. It usually means you found the interesting part.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()

def mission_brief_page(c,data,m,page_no,progress):
    top_bar(c,m['status'],page_no,progress)
    y=PAGE_H-0.86*inch
    pill(c,f"{m['rank']} // CASE {m['number']:02d}",M,y-13,9.5,fill=CHARCOAL,h=21)
    title_h=text_height(m['title'],PAGE_W-2*M,19.5,BOLD)
    para(c,m['title'],M,y-32,PAGE_W-2*M,title_h+1,size=19.5,font=BOLD)
    y-=title_h+53
    y-=text_card(c,m['hook'],M,y,PAGE_W-2*M,heading='MISSION BRIEF',size=11.5,fill=PALE2)+18
    label(c,'YOUR OBJECTIVE',M,y)
    y-=14
    used=text_height(m['objective'],PAGE_W-2*M,12,BOLD)
    para(c,m['objective'],M,y,PAGE_W-2*M,used+1,size=12.0,font=BOLD)
    y-=used+22
    for d in m.get('dialogue',[]):
        y-=avatar_callout(c,data['characters'],d['speaker'],d['text'],M,y,PAGE_W-2*M)+8
    if y>110: label(c,'CASE STATUS // OPEN / EVIDENCE NOT YET VERIFIED',M,65)
    footer(c,page_no); c.showPage()

def draw_tutorial_grid(c,tut,x,y,w,h,solution=False):
    n=tut['size']; cw=w/n; ch=h/n
    c.setFillColor(WHITE); c.rect(x,y,w,h,fill=1,stroke=0)
    c.setStrokeColor(LINE); c.setLineWidth(0.6)
    for i in range(n+1):
        c.line(x+i*cw,y,x+i*cw,y+h); c.line(x,y+i*ch,x+w,y+i*ch)
    # All writable grid cells are white. Room ownership is shown by walls,
    # derived from the unchanged source cell lists rather than gray fills.
    owners={cell:idx for idx,room in enumerate(tut['rooms']) for cell in room['cells']}
    for idx,room in enumerate(tut['rooms']):
        for cell in room['cells']:
            col=ord(cell[0])-ord('A'); row=int(cell[1:])-1
            cy=y+h-(row+1)*ch
            c.setFillColor(WHITE); c.rect(x+col*cw,cy,cw,ch,fill=1,stroke=0)
        cell=room['cells'][0]; col=ord(cell[0])-65; row=int(cell[1:])-1
        cx=x+(col+0.08)*cw; cy=y+h-(row+0.20)*ch
        c.setFillColor(BLACK); c.setFont(BOLD,11); c.drawString(cx,cy,room['name'])
    c.setStrokeColor(colors.HexColor('#B8B8B8')); c.setLineWidth(0.6)
    for i in range(n+1):
        c.line(x+i*cw,y,x+i*cw,y+h); c.line(x,y+i*ch,x+w,y+i*ch)
    c.setStrokeColor(BLACK); c.setLineWidth(1.3)
    c.rect(x,y,w,h,fill=0,stroke=1)
    for row in range(n):
        for col in range(n):
            cell=f'{chr(65+col)}{row+1}'
            if col<n-1 and owners.get(cell)!=owners.get(f'{chr(66+col)}{row+1}'):
                bx=x+(col+1)*cw; by=y+h-row*ch
                c.line(bx,by,bx,by-ch)
            if row<n-1 and owners.get(cell)!=owners.get(f'{chr(65+col)}{row+2}'):
                bx=x+col*cw; by=y+h-(row+1)*ch
                c.line(bx,by,bx+cw,by)
    c.setFillColor(BLACK); c.setFont(BOLD,15)
    for i,col in enumerate(tut['cols']): c.drawCentredString(x+(i+0.5)*cw,y+h+8,col)
    for i,row in enumerate(tut['rows']): c.drawRightString(x-6,y+h-(i+0.56)*ch,str(row))
    if solution:
        for person,pos in tut['positions'].items():
            col=ord(pos[0])-65; row=int(pos[1:])-1
            cx=x+(col+0.5)*cw; cy=y+h-(row+0.5)*ch
            c.setFillColor(BLACK); c.circle(cx,cy,min(cw,ch)*0.23,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont(BOLD,9.5); c.drawCentredString(cx,cy-2.3,person[0])


def guided_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'TRAINING GRID',page_no,progress)
    y=PAGE_H-0.88*inch
    para(c,'LEARN THE GRID BY SOLVING IT',M,y,PAGE_W-2*M,40,size=19.0,font=BOLD)
    para(c,'One exact clue at a time. No guessing required.',M,y-35,PAGE_W-2*M,25,size=11)
    tut=m['tutorial']; y-=86
    grid_h=3.15*inch
    draw_tutorial_grid(c,tut,M+24,y-grid_h,PAGE_W-2*M-48,grid_h,solution=False)
    y-=grid_h+20
    for i,clue in enumerate(tut['clues']):
        h=max(35,text_height(clue,PAGE_W-2*M-65,11)+16)
        box(c,M,y-h,PAGE_W-2*M,h,fill=WHITE,stroke=LINE,radius=8)
        label(c,f'{i+1:02d}',M+11,y-21)
        para(c,clue,M+42,y-9,PAGE_W-2*M-55,h-13,size=11)
        y-=h+5
    writing_card(c,'WHO WAS AT THE DELIVERY DESK?  YOUR VERDICT',M,y-6,PAGE_W-2*M,68)
    footer(c,page_no); c.showPage()

def guided_steps_page(c,data,m,page_no,progress):
    top_bar(c,'TRAINING // STEP MODE',page_no,progress)
    y=PAGE_H-0.88*inch
    para(c,'THE GRID DOES NOT NEED A MAGIC TRICK.',M,y,PAGE_W-2*M,55,size=18.5,font=BOLD)
    para(c,'It needs a next step.',M,y-55,PAGE_W-2*M,25,size=11)
    y-=100
    for idx,step in enumerate(m['tutorial']['guided_steps'],1):
        y-=text_card(c,step,M,y,PAGE_W-2*M,heading=f'STEP {idx:02d}',size=11.5,fill=PALE2)+12
    avatar_callout(c,data['characters'],'luli','Exact clues are free points. Take them before you wrestle with the clever ones.',M,y-8,PAGE_W-2*M)
    footer(c,page_no); c.showPage()

def verdict_reveal_page(c,data,m,page_no,progress):
    top_bar(c,'CASE CLEARED',page_no,progress)
    y=PAGE_H-0.95*inch
    pill(c,'VERIFIED',M,y-0.14*inch,7.6,fill=BLACK)
    para(c,'YOUR FIRST CASE IS CLOSED.',M,y-0.43*inch,PAGE_W-2*M,0.55*inch,size=22.0,font=BOLD)
    y-=1.22*inch
    draw_tutorial_grid(c,m['tutorial'],M+0.7*inch,y-3.15*inch,PAGE_W-2*M-1.4*inch,3.15*inch,solution=True)
    y-=3.48*inch
    box(c,M,y-0.78*inch,PAGE_W-2*M,0.70*inch,fill=BLACK,stroke=BLACK,radius=12)
    para(c,m['tutorial']['verdict'],M+0.18*inch,y-0.22*inch,PAGE_W-2*M-0.36*inch,0.35*inch,size=11,font=BOLD,color=WHITE,align=1)
    y-=1.04*inch
    avatar_callout(c,data['characters'],'mimi','Good. Nobody guessed. Nobody panicked. One mug was moved without authorization, but we will handle that internally.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()


def meta_signal_page(c,data,m,page_no,progress):
    top_bar(c,'EVIDENCE UNLOCKED',page_no,progress)
    c.setFillColor(BLACK); c.circle(PAGE_W/2,PAGE_H*0.64,1.02*inch,fill=0,stroke=1)
    c.setLineWidth(8); c.setStrokeColor(BLACK); c.circle(PAGE_W/2,PAGE_H*0.64,0.82*inch,fill=0,stroke=1)
    c.setFillColor(BLACK); c.setFont(BOLD,60.0); c.drawCentredString(PAGE_W/2,PAGE_H*0.64-21,'0')
    para(c,'TURN THE BADGE OVER.',M,PAGE_H*0.46,PAGE_W-2*M,0.48*inch,size=18.0,font=BOLD,align=1)
    para(c,m['meta_reveal'],M,PAGE_H*0.42,PAGE_W-2*M,0.65*inch,size=11,align=1)
    y=3.0*inch
    h=avatar_callout(c,data['characters'],'dilo','Anonymous symbol. Secret badge. Zero sender. This is statistically suspicious.',M,y,PAGE_W-2*M)
    y-=h+12
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
    c.setFillColor(BLACK); c.setFont(MONO,9.5); c.drawString(M,y,'WITNESS CLUES // TICK EACH ONE AFTER YOU USE IT')
    y-=0.16*inch
    clues=m['spatial']['clue_cards']; colw=(PAGE_W-2*M-0.12*inch)/2
    cardh=0.72*inch
    for idx,clue in enumerate(clues):
        col=idx%2; row=idx//2; x=M+col*(colw+0.12*inch); top=y-row*(cardh+0.08*inch)
        box(c,x,top-cardh,colw,cardh,fill=PALE2,stroke=LINE,radius=9)
        c.setFillColor(WHITE); c.setStrokeColor(MID); c.rect(x+0.10*inch,top-0.22*inch,9,9,fill=1,stroke=1)
        fit_para(c,clue,x+0.28*inch,top-0.16*inch,colw-0.38*inch,cardh-0.12*inch,max_size=7.8,min_size=6.4)
    box(c,M,0.59*inch,PAGE_W-2*M,0.70*inch,fill=WHITE,stroke=BLACK,radius=11)
    para(c,'YOUR VERDICT: _______________________________________________',M+0.17*inch,1.04*inch,PAGE_W-2*M-0.34*inch,0.28*inch,size=11,font=BOLD,color=BLACK)
    footer(c,page_no); c.showPage()


def meta_strip(c,data,m,page_no,progress):
    top_bar(c,'AFTER-CASE SIGNAL',page_no,progress)
    y=PAGE_H-1.05*inch
    para(c,'CASE CLOSED. SOMETHING ELSE JUST OPENED.',M,y,PAGE_W-2*M,0.55*inch,size=20.0,font=BOLD)
    y-=0.92*inch
    box(c,M,y-2.2*inch,PAGE_W-2*M,2.05*inch,fill=BLACK,stroke=BLACK,radius=16)
    c.setFillColor(WHITE); c.setFont(BOLD,56.0); c.drawCentredString(PAGE_W/2,y-1.12*inch,'0')
    c.setFont(MONO,9.5); c.drawCentredString(PAGE_W/2,y-1.65*inch,'RECURRING MARK // SOURCE UNKNOWN')
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
    rule=m.get('visual',{}).get('relevance_rule','Meaningful changes affect who, when or where.')
    para(c,rule,M,y-0.38*inch,PAGE_W-2*M,0.45*inch,size=11,font=BOLD)
    y-=0.90*inch
    gap=0.18*inch; pw=(PAGE_W-2*M-gap)/2; ph=3.42*inch
    for i,label in enumerate(['PHOTO A // 15:42','PHOTO B // 15:43']):
        x=M+i*(pw+gap)
        box(c,x,y-ph,pw,ph,fill=PALE2,stroke=LINE,radius=13)
        c.setFillColor(BLACK); c.setFont(MONO,9.5); c.drawString(x+0.12*inch,y-0.20*inch,label)
        c.setFillColor(WHITE); c.setStrokeColor(DARK); c.setLineWidth(1)
        c.rect(x+0.28*inch,y-1.12*inch,pw-0.56*inch,0.55*inch,fill=1,stroke=1)
        # The locked clue is a LEFT-to-RIGHT knot change. A clear bow moves
        # across the same parcel; the former almost-identical V strokes did
        # not communicate that already-established evidence at print size.
        knot_x=x+(0.82*inch if i==0 else pw-0.82*inch)
        knot_y=y-0.84*inch
        c.setStrokeColor(BLACK); c.setLineWidth(1.8)
        c.line(knot_x,y-1.11*inch,knot_x,y-0.58*inch)
        c.ellipse(knot_x-18,knot_y-7,knot_x,knot_y+7,fill=0,stroke=1)
        c.ellipse(knot_x,knot_y-7,knot_x+18,knot_y+7,fill=0,stroke=1)
        c.line(knot_x,knot_y,knot_x-10,knot_y-14)
        c.line(knot_x,knot_y,knot_x+10,knot_y-14)
        c.setFillColor(BLACK); c.circle(knot_x,knot_y,3,fill=1,stroke=0)
        tag='0417' if i==0 else '0471'
        arrow=1 if i==0 else -1
        c.setFillColor(WHITE); c.setStrokeColor(BLACK); c.roundRect(x+0.42*inch,y-1.92*inch,1.0*inch,0.48*inch,7,fill=1,stroke=1)
        c.setFillColor(BLACK); c.setFont(MONO,10.0); c.drawCentredString(x+0.92*inch,y-1.72*inch,tag)
        c.setFillColor(DARK); c.ellipse(x+1.72*inch,y-2.12*inch,x+2.02*inch,y-1.70*inch,fill=1,stroke=0)
        c.setStrokeColor(BLACK); c.setLineWidth(2)
        ax=x+2.15*inch; ay=y-1.90*inch
        if arrow>0:
            c.line(ax-0.25*inch,ay,ax+0.20*inch,ay); c.line(ax+0.20*inch,ay,ax+0.06*inch,ay+0.10*inch); c.line(ax+0.20*inch,ay,ax+0.06*inch,ay-0.10*inch)
        else:
            c.line(ax+0.25*inch,ay,ax-0.20*inch,ay); c.line(ax-0.20*inch,ay,ax-0.06*inch,ay+0.10*inch); c.line(ax-0.20*inch,ay,ax-0.06*inch,ay-0.10*inch)
        c.setFillColor(BLACK); c.setFont(BOLD,11.0); c.drawString(x+0.44*inch,y-2.55*inch,'*  *  *' if i==0 else '*  *  *  *')
        c.setFont(FONT,11); c.drawString(x+0.44*inch,y-2.82*inch,'cup handle >' if i==0 else '< cup handle')
        c.setStrokeColor(MID); c.line(x+0.50*inch,y-3.05*inch,x+1.25*inch,y-3.05*inch)
    y-=ph+0.20*inch
    avatar_callout(c,data['characters'],'luli','Do not count differences. Test them. Which ones change the parcel, the evidence tag or the recorded route?',M,y,PAGE_W-2*M)
    box(c,M,0.58*inch,PAGE_W-2*M,0.68*inch,fill=BLACK,stroke=BLACK,radius=11)
    para(c,'CIRCLE 3 MEANINGFUL CHANGES.  IGNORE THE NOISE.',M+0.15*inch,1.00*inch,PAGE_W-2*M-0.30*inch,0.28*inch,size=11,font=BOLD,color=WHITE,align=1)
    footer(c,page_no); c.showPage()


def code_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,'CODE DROP',page_no,progress)
    y=PAGE_H-0.87*inch
    para(c,'FOUR SLOTS. FOUR SYMBOLS. ONE ORDER.',M,y,PAGE_W-2*M,0.50*inch,size=19.0,font=BOLD)
    para(c,'No random tapping. The keypad is offline anyway.',M,y-0.38*inch,PAGE_W-2*M,0.34*inch,size=11,color=BLACK)
    y-=1.00*inch
    slotw=1.18*inch; gap=0.12*inch; total=4*slotw+3*gap; sx=(PAGE_W-total)/2
    for i in range(4):
        box(c,sx+i*(slotw+gap),y-1.0*inch,slotw,0.90*inch,fill=WHITE,stroke=BLACK,radius=14)
        c.setFillColor(BLACK); c.setFont(MONO,9.5); c.drawCentredString(sx+i*(slotw+gap)+slotw/2,y-0.28*inch,f'SLOT {i+1}')
    y-=1.32*inch
    labels=m['code']['symbols']; chipw=(PAGE_W-2*M-0.30*inch)/4
    for i,sym in enumerate(labels):
        x=M+i*(chipw+0.10*inch)
        box(c,x,y-0.62*inch,chipw,0.56*inch,fill=PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(BOLD,9.5); c.drawCentredString(x+chipw/2,y-0.38*inch,sym)
    y-=0.93*inch
    c.setFillColor(BLACK); c.setFont(MONO,9.5); c.drawString(M,y,'CODE RULES')
    y-=0.15*inch
    for idx,clue in enumerate(m['code']['clues'],1):
        h=0.65*inch
        box(c,M,y-h,PAGE_W-2*M,h-0.05*inch,fill=WHITE if idx%2 else PALE2,stroke=LINE,radius=10)
        c.setFillColor(BLACK); c.setFont(BOLD,9.5); c.drawString(M+0.14*inch,y-0.22*inch,f'{idx:02d}')
        para(c,clue,M+0.44*inch,y-0.17*inch,PAGE_W-2*M-0.58*inch,0.34*inch,size=11)
        y-=h
    y-=0.12*inch
    avatar_callout(c,data['characters'],'dilo','If you are about to try random orders, I respect the chaos. Luli does not.',M,y,PAGE_W-2*M)
    footer(c,page_no); c.showPage()



def _structured_type_label(m):
    return {
        'route': 'ROUTE FILE',
        'classification': 'EVIDENCE SORT',
        'consistency': 'CONSISTENCY CHECK',
        'timeline': 'TIMELINE',
        'timeline-visual': 'VISUAL TIMELINE',
        'reconstruction': 'RECONSTRUCTION',
        'visual-sequence': 'VISUAL SEQUENCE',
        'room-zero-checkpoint': 'ROOM ZERO CHECKPOINT',
        'map-overlay': 'MAP OVERLAY',
        'fact-theory-sort': 'FACT / THEORY',
        'multi-stage-finale': 'FINAL LOCK',
    }.get(m.get('type'), str(m.get('type','MISSION')).upper())


def _structured_cards(m):
    t=m.get('type')
    cards=[]
    footer_note=None
    if t=='route':
        data=m.get('route',{})
        cards.append(f"START: {data.get('start','?')}   GOAL: {data.get('goal','?')}")
        for opt in data.get('options',[]):
            cards.append(f"ROUTE {opt.get('id','?')}: " + "  >  ".join(opt.get('path',[])))
        for opt in data.get('options',[]):
            rule=opt.get('fails')
            if rule:
                cards.append(f"SITE CONDITION: {rule}")
        footer_note='Choose one route and justify it with the site conditions.'
    elif t=='classification':
        data=m.get('classification',{})
        cards.append(f"CASE WINDOW: {data.get('case_window','')}")
        for item in data.get('items',[]):
            cards.append(f"{item.get('id','?')} // {item.get('item','')} // {item.get('label','')}")
        footer_note=data.get('question')
    elif t=='consistency':
        data=m.get('consistency',{})
        mp=data.get('map',{})
        cards.append(f"TRAVEL RULE: each map edge = {mp.get('walking_minutes_per_edge','?')} minutes")
        for edge in mp.get('edges',[]):
            cards.append("MAP LINK: " + "  <->  ".join(edge))
        for st in data.get('statements',[]):
            cards.append(f"{st.get('speaker','?')}: {st.get('text','')}")
        footer_note='Circle the statement that cannot fit the map and clock together.'
    elif t=='timeline':
        data=m.get('timeline',{})
        cards.extend(data.get('rules',[]))
        for rec in data.get('records',[]):
            cards.append(f"{rec.get('id','?')} // {rec.get('source','')} // shows {rec.get('shown','')} // {rec.get('event','')}")
        footer_note='Convert every record to real time, then write the event order.'
    elif t=='timeline-visual':
        data=m.get('timeline_visual',{})
        cards.append("BUILDING OPTIONS: " + " / ".join(data.get('candidate_buildings',[])))
        cards.append("YEAR OPTIONS: " + " / ".join(str(x) for x in data.get('candidate_years',[])))
        cards.extend(data.get('evidence',[]))
        footer_note='Name the building and year using only the evidence above.'
    elif t=='reconstruction':
        data=m.get('reconstruction',{})
        for scrap in data.get('scraps',[]):
            cards.append(
                f"SCRAP {scrap.get('id','?')} // {scrap.get('left_edge','?')} | {scrap.get('text','')} | {scrap.get('right_edge','?')}"
            )
        footer_note='Rebuild the note. Use physical edges before sentence logic.'
    elif t=='visual-sequence':
        data=m.get('visual_sequence',{})
        cards.append(f"RULE: {data.get('rule','')}")
        for rec in data.get('prints',[]):
            cards.append(
                f"{rec.get('position','?')} // mud {rec.get('mud','?')} // tread arrow {rec.get('tread_arrow','?')}"
            )
        footer_note='Write the real direction of travel.'
    elif t=='room-zero-checkpoint':
        data=m.get('checkpoint',{})
        if data.get('instruction'):
            cards.append(data['instruction'])
        for item in data.get('evidence',[]):
            cards.append(f"{item.get('item','')} // mark: {item.get('mark','')}")
        if data.get('case_numbers'):
            cards.append("REVISIT CASES: " + ", ".join(f"{int(n):02d}" for n in data['case_numbers']))
        footer_note='Write your conclusion before turning the page.'
    elif t=='map-overlay':
        data=m.get('map_overlay',{})
        for anchor in data.get('anchors',[]):
            cards.append(f"ANCHOR // old: {anchor.get('old','')}  <->  current: {anchor.get('current','')}")
        cards.append(f"OLD PLAN EXTRA SPACE: {data.get('old_only_space','')}")
        cards.append(f"CURRENT LOCATION: {data.get('current_covering_space','')}")
        footer_note='Align the plans using permanent landmarks. Mark the sealed space.'
    elif t=='fact-theory-sort':
        data=m.get('fact_theory_sort',{})
        cards.append("SORT EACH CARD INTO: FACT / THEORY / UNSUPPORTED ASSUMPTION")
        for name,definition in data.get('definitions',{}).items():
            cards.append(f"{name}: {definition}")
        for card in data.get('cards',[]):
            cards.append(card.get('text',''))
        cards.append("RULE ZERO: ZERO ____________. NOTICE FIRST. THEORIZE SECOND.")
        footer_note='Fill the missing word only after sorting the evidence.'
    elif t=='multi-stage-finale':
        data=m.get('finale',{})
        for stage in data.get('stages',[]):
            cards.append(f"{stage.get('id','LOCK')} // {stage.get('prompt','')}")
        footer_note='No new rule appears here. Every answer was earned earlier in the book.'
    return [str(x) for x in cards if str(x).strip()], footer_note


def structured_puzzle_page(c,data,m,page_no,progress):
    top_bar(c,_structured_type_label(m),page_no,progress)
    y=PAGE_H-0.88*inch
    pill(c,f"CASE {m['number']:02d} // PUZZLE",M,y-12,9.5,fill=CHARCOAL,h=21)
    title_h=text_height(m['title'],PAGE_W-2*M,17.5,BOLD)
    para(c,m['title'],M,y-31,PAGE_W-2*M,title_h+1,size=17.5,font=BOLD)
    y-=title_h+50
    cards,footer_note=_structured_cards(m)
    if not cards: cards=[m.get('objective','Use the evidence from the case brief to reach one justified verdict.')]
    # Measure full-width evidence rows first. Wide rows keep deduction copy
    # readable and avoid losing cards to the former arbitrary [:12] cutoff.
    text_w=PAGE_W-2*M-57
    writable_stages=m.get('type')=='multi-stage-finale'
    heights=[max(75 if writable_stages else 34,text_height(card,text_w,11)+18) for card in cards]
    needed=sum(heights)+5*(len(cards)-1)
    bottom=144
    if needed>y-bottom:
        raise ValueError(f"Case {m['number']}: evidence needs {needed:.1f}pt, available {y-bottom:.1f}pt")
    for idx,(card,h) in enumerate(zip(cards,heights),1):
        box(c,M,y-h,PAGE_W-2*M,h,fill=WHITE if idx%2 else PALE2,stroke=LINE,radius=8)
        label(c,f'{idx:02d}',M+11,y-21)
        para(c,card,M+40,y-9,text_w,h-15,size=11)
        if writable_stages:
            c.setStrokeColor(BLACK); c.setLineWidth(0.8)
            c.line(M+40,y-h+16,PAGE_W-M-14,y-h+16)
        y-=h+5
    revisit=m.get('checkpoint',{}).get('case_numbers',[]) if m.get('type')=='room-zero-checkpoint' else []
    if revisit:
        label(c,'CASE',M+9,y-16)
        label(c,'EMPTY ROOM',M+83,y-16)
        label(c,'INITIAL',PAGE_W-M-62,y-16)
        y-=24
        if y-len(revisit)*23<144:
            raise ValueError('Room Zero empty-room record exceeds page')
        for number in revisit:
            label(c,f'{int(number):02d}',M+12,y-14)
            c.setStrokeColor(BLACK); c.setLineWidth(0.65)
            c.line(M+82,y-19,PAGE_W-M-80,y-19)
            c.line(PAGE_W-M-61,y-19,PAGE_W-M-15,y-19)
            y-=23
    if footer_note:
        used=text_height(footer_note,PAGE_W-2*M,11,BOLD)
        para(c,footer_note,M,132,PAGE_W-2*M,used+1,size=11,font=BOLD)
    writing_card(c,'YOUR VERDICT / EVIDENCE NOTES',M,92,PAGE_W-2*M,56)
    footer(c,page_no); c.showPage()

def spatial_source_preview_page(c,data,m,page_no,progress):
    """Readable editorial-only placeholder; never a release map substitute."""
    top_bar(c,'DEDUCTION GRID // FINAL SOURCE',page_no,progress)
    y=PAGE_H-0.86*inch
    pill(c,f"{m.get('spatial_source_id','SOURCE')} // CASE {m['number']:02d}",M,y-13,9.5,fill=CHARCOAL,h=21)
    th=text_height(m['title'],PAGE_W-2*M,17.2,BOLD)
    para(c,m['title'],M,y-31,PAGE_W-2*M,th+1,size=17.2,font=BOLD)
    y-=th+51
    y-=text_card(c,'Logic is locked to the verified source ID above. This editorial placeholder cannot pass release preflight.',
                 M,y,PAGE_W-2*M,heading='FINAL MAP FACTORY ASSET PENDING',size=11,stroke=BLACK)+14
    clues=m.get('spatial_copy',{}).get('clue_cards',[])
    width=PAGE_W-2*M-54
    heights=[max(35,text_height(clue,width,11)+18) for clue in clues]
    if y-sum(heights)-5*len(clues)<120:
        raise ValueError(f"Editorial case {m['number']}: witness copy exceeds readable preview page")
    for idx,(clue,h) in enumerate(zip(clues,heights),1):
        box(c,M,y-h,PAGE_W-2*M,h,fill=WHITE,stroke=LINE,radius=8)
        c.setStrokeColor(BLACK); c.setLineWidth(0.7)
        c.rect(M+12,y-23,10,10,fill=0,stroke=1)
        para(c,clue,M+37,y-9,width,h-14,size=11)
        y-=h+5
    writing_card(c,m.get('verdict_label','YOUR VERDICT'),M,100,PAGE_W-2*M,62)
    footer(c,page_no); c.showPage()


def finale_reveal_page(c,data,m,page_no):
    top_bar(c,'ROOM ZERO // REVEAL',page_no,1.0)
    y=PAGE_H-0.92*inch
    title='THE ROOM WAS WAITING FOR A DETECTIVE.'
    h=text_height(title,PAGE_W-2*M,20,BOLD)
    para(c,title,M,y,PAGE_W-2*M,h+1,size=20.0,font=BOLD); y-=h+24
    finale=m.get('finale',{})
    y-=text_card(c,finale.get('reveal',''),M,y,PAGE_W-2*M,size=12.0,fill=PALE2,stroke=BLACK)+20
    y-=text_card(c,finale.get('reader_payoff',''),M,y,PAGE_W-2*M,size=12.0,font=BOLD,stroke=BLACK)+20
    y-=avatar_callout(c,data['characters'],'nini','So the missing detective was here the whole time.',M,y,PAGE_W-2*M)+20
    text_card(c,finale.get('series_hook',''),M,y,PAGE_W-2*M,size=11.5,font=BOLD)
    footer(c,page_no); c.showPage()

def certificate_page(c,data,page_no):
    top_bar(c,'DETECTIVE ACADEMY',page_no,1.0)
    y=PAGE_H-1.05*inch
    para(c,'CASE CLOSED.',M,y,PAGE_W-2*M,0.58*inch,size=27.0,font=BOLD,align=1)
    para(c,'ROOM ZERO // CLEARED',M,y-0.55*inch,PAGE_W-2*M,0.38*inch,size=11,font=MONO,color=BLACK,align=1)
    y-=1.35*inch
    box(c,M,y-3.55*inch,PAGE_W-2*M,3.35*inch,fill=PALE2,stroke=BLACK,radius=18,sw=1.2)
    para(c,'DETECTIVE ACADEMY CERTIFICATE',M+0.25*inch,y-0.52*inch,PAGE_W-2*M-0.50*inch,0.42*inch,size=17.0,font=BOLD,align=1)
    para(c,'Awarded to',M+0.25*inch,y-1.04*inch,PAGE_W-2*M-0.50*inch,0.30*inch,size=11,color=BLACK,align=1)
    c.setStrokeColor(BLACK); c.setLineWidth(1.0); c.line(M+0.95*inch,y-1.65*inch,PAGE_W-M-0.95*inch,y-1.65*inch)
    para(c,'for closing THE MYSTERY OF ROOM ZERO with zero guesses required by the certificate committee.',
         M+0.45*inch,y-2.03*inch,PAGE_W-2*M-0.90*inch,0.62*inch,size=11,align=1)
    para(c,'STATUS // NEXT DETECTIVE',M+0.45*inch,y-2.84*inch,PAGE_W-2*M-0.90*inch,0.38*inch,size=12.0,font=BOLD,align=1)
    y-=3.92*inch
    box(c,M,y-0.92*inch,PAGE_W-2*M,0.82*inch,fill=BLACK,stroke=BLACK,radius=12)
    para(c,'CASE 001 // STILL OPEN',M+0.16*inch,y-0.27*inch,PAGE_W-2*M-0.32*inch,0.32*inch,size=13.0,font=BOLD,color=WHITE,align=1)
    footer(c,page_no); c.showPage()

def big_case_wall_page(c,data,beat,page_no):
    top_bar(c,beat.get('eyebrow','THE BIG CASE // EVIDENCE WALL'),page_no,0.72)
    y=PAGE_H-0.90*inch
    heading=beat.get('headline','THE CASE GETS BIGGER.')
    h=text_height(heading,PAGE_W-2*M,19.5,BOLD)
    para(c,heading,M,y,PAGE_W-2*M,h+1,size=19.5,font=BOLD); y-=h+16
    y-=text_card(c,beat.get('question',''),M,y,PAGE_W-2*M,size=11.5,font=BOLD,fill=PALE2,stroke=BLACK)+14
    label(c,'ROOM ZERO // ACTIVE EVIDENCE WALL',M,y); y-=15
    for idx,item in enumerate(beat.get('evidence',[]),1):
        h=text_height(item,PAGE_W-2*M-34,11)
        label(c,f'{idx:02d}',M,y-10)
        para(c,item,M+29,y,PAGE_W-2*M-34,h+1,size=11)
        y-=h+10
    y-=4
    label(c,'SQUAD READ // FACTS FIRST, THEORIES SECOND',M,y); y-=16
    for line in beat.get('squad',[]):
        name=data['characters'][line['speaker']]['name']
        text=f"<b>{name}:</b> {line.get('text','')}"
        h=text_height(text,PAGE_W-2*M,11)
        para(c,text,M,y,PAGE_W-2*M,h+1,size=11); y-=h+8
    y-=10
    if beat.get('reader_move'):
        y-=text_card(c,beat['reader_move'],M,y,PAGE_W-2*M,heading='YOUR MOVE // UPDATE THE CASE WALL',size=11,stroke=BLACK)+10
    # A white field is provided whenever an interlude asks for pencil work.
    if y>=95: writing_card(c,'CASE WALL / DETECTIVE NOTES',M,y,PAGE_W-2*M,min(75,y-38))
    footer(c,page_no); c.showPage()

def preview_end_page(c,data,page_no):
    top_bar(c,'ROOKIE ACCESS',page_no,0.18)
    y=PAGE_H-0.95*inch
    para(c,data['preview_end']['headline'],M,y,PAGE_W-2*M,0.55*inch,size=21.0,font=BOLD)
    y-=0.82*inch
    para(c,data['preview_end']['body'],M,y,PAGE_W-2*M,0.95*inch,size=11.2)
    y-=1.15*inch
    box(c,M,y-1.45*inch,PAGE_W-2*M,1.35*inch,fill=BLACK,stroke=BLACK,radius=15)
    c.setFillColor(WHITE); c.setFont(MONO,9.5); c.drawString(M+0.18*inch,y-0.28*inch,'ROOM ZERO SIGNALS FOUND')
    c.setFont(BOLD,33.0); c.drawString(M+0.18*inch,y-0.86*inch,'05')
    c.setFont(MONO,9.5); c.drawString(M+1.05*inch,y-0.78*inch,'STATUS: PATTERN NOT YET EXPLAINED')
    y-=1.78*inch
    for d in data['preview_end']['dialogue']:
        h=avatar_callout(c,data['characters'],d['speaker'],d['text'],M,y,PAGE_W-2*M)
        y-=h+0.09*inch
    footer(c,page_no); c.showPage()


def hint_vault_page(c,data,missions,page_no):
    # Five complete hint ladders per page retain the established six-page
    # Vault. Rows are measured at 11pt; no nudge can silently be clipped.
    for offset in range(0,len(missions),5):
        group=missions[offset:offset+5]
        top_bar(c,'HINT VAULT',page_no,0.19)
        y=PAGE_H-0.88*inch
        if offset==0:
            para(c,'TAKE THE SMALLEST NUDGE FIRST.',M,y,PAGE_W-2*M,32,size=18.5,font=BOLD); y-=39
            para(c,'Stop the moment the case starts moving again.',M,y,PAGE_W-2*M,20,size=11); y-=30
        else:
            label(c,'HINT VAULT // ONE NUDGE AT A TIME',M,y); y-=22
        for m in group:
            hints=[h for h in (m.get('hints') or [m.get('nudge','Look for the most exact clue first.')]) if h][:3]
            widths=PAGE_W-2*M-47
            heights=[text_height(h,widths,11) for h in hints]
            card_h=sum(heights)+8*len(hints)+32
            if y-card_h<35: raise ValueError(f"Hint Vault Case {m['number']}: 11pt hints exceed page")
            box(c,M,y-card_h,PAGE_W-2*M,card_h,fill=WHITE,stroke=LINE,radius=10)
            label(c,f"CASE {m['number']:02d} // NUDGE LADDER",M+11,y-20)
            ty=y-32
            for idx,(hint,h) in enumerate(zip(hints,heights),1):
                label(c,f'H{idx}',M+11,ty-10)
                para(c,hint,M+36,ty,widths,h+1,size=11); ty-=h+8
            y-=card_h+8
        footer(c,page_no); c.showPage(); page_no+=1
    return page_no

def _solution_answer_text(m):
    if m.get('type') in ('spatial','boss-spatial'):
        sp=m.get('spatial_copy') or m.get('spatial') or {}
        ans=sp.get('answer')
        coord=sp.get('answer_coordinate')
        return f"{ans} @ {coord}" if ans and coord else (ans or '')
    t=m.get('type')
    if t=='route':
        return str(m.get('route',{}).get('answer',''))
    if t=='classification':
        return str(m.get('classification',{}).get('answer',''))
    if t=='consistency':
        return str(m.get('consistency',{}).get('answer',''))
    if t=='timeline':
        return '  >  '.join(m.get('timeline',{}).get('answer_order',[]))
    if t=='timeline-visual':
        a=m.get('timeline_visual',{}).get('answer',{})
        return f"{a.get('building','')} // {a.get('year','')}".strip(' /')
    if t=='reconstruction':
        return str(m.get('reconstruction',{}).get('answer_text',''))
    if t=='visual-sequence':
        return str(m.get('visual_sequence',{}).get('answer',''))
    if t=='room-zero-checkpoint':
        return str(m.get('checkpoint',{}).get('answer',m.get('answer','')))
    if t=='map-overlay':
        return str(m.get('map_overlay',{}).get('answer',''))
    if t=='fact-theory-sort':
        return str(m.get('fact_theory_sort',{}).get('rule_zero',m.get('answer','')))
    if t=='multi-stage-finale':
        return 'ROOM ZERO // NEXT DETECTIVE'
    if t=='code':
        return '  >  '.join(m.get('code',{}).get('answer',[]))
    if t=='visual':
        return str(m.get('visual',{}).get('answer','')).replace(' + ','  /  ')
    if t=='guided':
        return str(m.get('tutorial',{}).get('verdict',''))
    return str(m.get('answer',''))


def solutions_pages(c,data,missions,page_no):
    for m in missions:
        top_bar(c,f"SOLUTION // CASE {m['number']:02d}",page_no,0.20)
        y=PAGE_H-0.90*inch
        h=text_height(m['title'],PAGE_W-2*M,18,BOLD)
        para(c,m['title'],M,y,PAGE_W-2*M,h+1,size=18.0,font=BOLD); y-=h+20
        if m.get('type') in ('spatial','boss-spatial') and m.get('spatial'):
            sp=m['spatial']; src=ROOT/sp['solution_asset']; dst=ROOT/'cache'/'crops'/f"case{m['number']:02d}_solution.png"
            preprocess_crop(src,sp.get('solution_crop'),dst)
            draw_image_fit(c,dst,M,y-216,PAGE_W-2*M,216); y-=235
        elif m.get('type')=='guided':
            draw_tutorial_grid(c,m['tutorial'],M+45,y-170,PAGE_W-2*M-90,170,solution=True); y-=194
        answer=_solution_answer_text(m)
        if answer:
            y-=text_card(c,answer,M,y,PAGE_W-2*M,size=12.0,font=BOLD,stroke=BLACK)+16
        label(c,'HOW THE CASE FALLS INTO PLACE',M,y); y-=19
        for idx,step in enumerate(m['solution_steps'],1):
            h=text_height(step,PAGE_W-2*M-45,11)+20
            if y-h<35:
                raise ValueError(f"Solution Case {m['number']}: 11pt explanation exceeds page")
            box(c,M,y-h,PAGE_W-2*M,h,fill=WHITE if idx%2 else PALE2,stroke=LINE,radius=9)
            label(c,f'{idx:02d}',M+10,y-21)
            para(c,step,M+33,y-10,PAGE_W-2*M-45,h-15,size=11)
            y-=h+7
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
    spine_beats=(data.get('story_spine') or {}).get('beats',[])
    spine_by_case={int(beat['after_case']): beat for beat in spine_beats if beat.get('after_case') is not None}
    m=missions[0]; prog=0.07
    mission_brief_page(c,data,m,page,prog); page+=1
    guided_puzzle_page(c,data,m,page,prog); page+=1
    guided_steps_page(c,data,m,page,prog); page+=1
    verdict_reveal_page(c,data,m,page,prog); page+=1
    meta_signal_page(c,data,m,page,prog); page+=1

    structured_types={
        'route','classification','consistency','timeline','timeline-visual',
        'reconstruction','visual-sequence','room-zero-checkpoint','map-overlay',
        'fact-theory-sort','multi-stage-finale'
    }
    for m in missions[1:]:
        prog=min(0.98,0.07 + m['number']*0.030)
        mission_brief_page(c,data,m,page,prog); page+=1
        typ=m.get('type')
        if typ in ('spatial','boss-spatial'):
            if m.get('spatial'):
                spatial_puzzle_page(c,data,m,page,prog)
            else:
                spatial_source_preview_page(c,data,m,page,prog)
            page+=1
            meta_strip(c,data,m,page,prog); page+=1
        elif typ=='visual':
            visual_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1
        elif typ=='code':
            code_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1
        elif typ in structured_types:
            structured_puzzle_page(c,data,m,page,prog); page+=1
            if typ=='multi-stage-finale':
                finale_reveal_page(c,data,m,page); page+=1
                certificate_page(c,data,page); page+=1
            else:
                meta_strip(c,data,m,page,prog); page+=1
        else:
            structured_puzzle_page(c,data,m,page,prog); page+=1
            meta_strip(c,data,m,page,prog); page+=1

        beat=spine_by_case.get(int(m['number']))
        if beat:
            big_case_wall_page(c,data,beat,page); page+=1

    if data.get('preview_end'):
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
