"""Print-size spatial framing shared by the book, map PDFs and paired spreads."""
from pathlib import Path
import html
import sys
from PIL import Image
from reportlab.lib.units import inch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_book as rb


def draw_grid(c, path, case, top, height=7.0*inch):
    with Image.open(path) as im:
        iw, ih = im.size
    # The normalized source rasters vary by a pixel at their outer crop.  A
    # 72.1pt/300px cap keeps effective resolution above 299 DPI while ensuring
    # a nominal six-inch writable field does not become 431.76pt.
    scale = min((rb.PAGE_W-2*rb.M-28)/iw, height/ih, 72.1/300)
    w,h=iw*scale,ih*scale
    x=rb.PAGE_W/2-w/2+9; y=top-h
    c.drawImage(str(path),x,y,w,h)
    if case:
        rows,cols=int(case['grid']['rows']),int(case['grid']['columns'])
        c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,16 if cols<=7 else 14)
        for col in range(cols):
            c.drawCentredString(x+(col+.5)*w/cols,top+10,chr(65+col))
        for row in range(rows):
            c.drawRightString(x-10,top-(row+.5)*h/rows-5,str(row+1))
    return y,w,h


def verdict_card(c, top, answer=None):
    x=rb.M; w=rb.PAGE_W-2*x
    rb.box(c,x,top-62,w,62,fill=rb.WHITE,stroke=rb.BLACK,radius=10,sw=1.3)
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,10)
    c.drawString(x+12,top-18,'YOUR VERDICT // WITNESS / PERSON' if not answer else 'VERIFIED WITNESS / PERSON')
    c.drawString(x+w-120,top-18,'COORDINATE')
    c.setLineWidth(.9)
    c.line(x+12,top-49,x+w-148,top-49)
    c.line(x+w-120,top-49,x+w-12,top-49)
    if answer:
        c.setFont(rb.BOLD,12)
        c.drawString(x+14,top-43,str(answer.get('display_name',answer.get('name',''))))
        c.drawString(x+w-118,top-43,str(answer.get('coordinate','')))


def map_page(c, mission, map_path, page_no, case=None, solution=False):
    rb.top_bar(c,'SOLUTION MAP' if solution else 'LIVE CASE MAP',page_no)
    top=rb.PAGE_H-58
    number=mission.get('number',int(case['id'].split('_')[-1]) if case else 0)
    c.setFillColor(rb.BLACK); c.setFont(rb.BOLD,10)
    c.drawString(rb.M,top,f"CASE {number:02d}  /  {str(mission.get('rank','')).upper()}")
    rb.para(c,html.escape(mission['title']),rb.M,top-13,rb.PAGE_W-2*rb.M,46,size=18,font=rb.BOLD)
    # Rules and roster belong before the grid so children know how to mark it.
    key='One person per row and column. Use each witness clue.'
    if case and not solution:
        allowed=sorted({('desk chair' if o['type']=='deskchair' else o['display_label'])
                        for o in case.get('objects',[]) if o.get('occupiable')})
        key='One person per row and column. Usable: empty floor; '+', '.join(allowed)+'. Other objects block squares.'
    if solution:
        key='  |  '.join(f"{index:02d} = {p['display_name']}" for index,p in enumerate(case.get('characters',[]),1))
    # The coordinate glyphs occupy a real reserved band.  The old formula
    # placed that band inside the rules paragraph on eleven maps.  Measure the
    # copy, then stack rules -> 10pt clearance -> coordinates -> 6pt -> map.
    rules_top=top-60
    key_h=rb.text_height(html.escape(key),rb.PAGE_W-2*rb.M-24,10.5)
    rules_h=key_h+34
    rb.box(c,rb.M,rules_top-rules_h,rb.PAGE_W-2*rb.M,rules_h,
           fill=rb.WHITE,stroke=rb.BLACK,radius=7,sw=0.9)
    rb.label(c,'MAP RULES / WITNESS KEY',rb.M+12,rules_top-17,size=9.5)
    rb.para(c,html.escape(key),rb.M+12,rules_top-27,rb.PAGE_W-2*rb.M-24,key_h+1,size=10.5)
    rules_bottom=rules_top-rules_h
    coordinate_band=20
    grid_top=rules_bottom-10-coordinate_band-6
    bottom,_,_=draw_grid(c,map_path,case,grid_top,6.02*inch)
    verdict_card(c,bottom-12,case.get('source_answer') if solution else None)
    rb.footer(c,page_no); c.showPage()
