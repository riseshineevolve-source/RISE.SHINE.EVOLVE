"""Assemble the owner review from the existing renderer and validated spatial assets.

Reader aliases are a generated presentation layer; canonical source identities,
clues, geometry, placements and answers are never mutated.
"""
from __future__ import annotations
import argparse
import copy
import html
import hashlib
import json
from pathlib import Path
import re
import sys
import yaml
from reportlab.platypus import Paragraph
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import render_book as rb
from render_spatial_case_spreads import witness_board
from spatial_presentation import draw_grid, map_page


def reader_aliases(value, names):
    if isinstance(value, str):
        pattern=r'\b('+ '|'.join(re.escape(k) for k in sorted(names,key=len,reverse=True))+r')\b'
        return re.sub(pattern,lambda m:names[m.group(0).lower()],value,flags=re.I)
    if isinstance(value,list): return [reader_aliases(v,names) for v in value]
    if isinstance(value,dict): return {k:reader_aliases(v,names) for k,v in value.items()}
    return value


def solution_page(c, mission, case, image, page):
    rb.top_bar(c,f"SOLUTION // CASE {mission['number']:02d}",page)
    width=rb.PAGE_W-2*rb.M
    rb.para(c,html.escape(mission['title']),rb.M,rb.PAGE_H-54,width,44,size=17,font=rb.BOLD)
    # The same labels are designed to remain >=10.5pt at this six-inch map size.
    bottom,w,h=draw_grid(c,image,case,rb.PAGE_H-108,6*72)
    answer=case['source_answer']
    legend='  |  '.join(f"{p['display_name'][0]} = {p['display_name']}" for p in case['characters'])
    lh=rb.text_height(legend,width,11)
    rb.para(c,legend,rb.M,bottom-8,width,lh+.5,size=11)
    y=bottom-lh-25
    rb.label(c,f"VERDICT: {answer['display_name']}  /  {answer['coordinate']}",rb.M,y,size=12)
    y-=20
    rb.label(c,'HOW THE CASE FALLS INTO PLACE',rb.M,y,size=10); y-=11
    steps=mission['solution_steps']
    # Two reading columns preserve the complete deduction trail under a large map.
    split=(len(steps)+1)//2; colw=(width-22)/2
    for col,items in enumerate((steps[:split],steps[split:])):
        ty=y
        for idx,step in enumerate(items,1+col*split):
            text=f'<b>{idx:02d}</b>  '+html.escape(step)
            used=rb.text_height(text,colw,11)
            rb.para(c,text,rb.M+col*(colw+22),ty,colw,used+.5,size=11)
            ty-=used+7
    rb.footer(c,page); c.showPage()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--master',required=True,type=Path)
    ap.add_argument('--runtime',required=True,type=Path)
    ap.add_argument('--maps',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    runtime=json.loads(args.runtime.read_text(encoding='utf-8'))
    cases={c['id']:c for c in runtime['cases']}
    data=yaml.safe_load(args.master.read_text(encoding='utf-8'))
    if len(data['missions'])!=30 or len(cases)!=15: raise ValueError('Expected 30 missions and 15 locked spatial modules')
    root=Path(__file__).resolve().parents[1]
    selection=yaml.safe_load((root/'content/spatial_source_manifest_final.yml').read_text(encoding='utf-8'))
    if set(cases)!={c['id'] for c in selection['cases']}:
        raise ValueError('Runtime case identities differ from locked selection')
    data.setdefault('production_state',{}).update({
        'owner_review_version':2,'spatial_assets_attached':True,
        'runtime_sha256':hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
        'aliases':'content/spatial_character_aliases.yml',
        'english_frozen':False,
    })
    for i,mission in enumerate(data['missions']):
        cid=mission.get('spatial_source_id')
        if not cid: continue
        case=cases[cid]
        names={p['source_name'].lower():p['display_name'] for p in case['characters']}
        m=reader_aliases(copy.deepcopy(mission),names)
        rooms={r['source_name'].lower():r['final_name'] for r in case['rooms']}
        # Protect already skinned phrases (for example Robotics Lab) from a
        # second substitution of a contained source term such as Lab.
        for room in case['rooms']:
            rooms[room['final_name'].lower()]=room['final_name']
        # Room words in story titles/hooks (for example "library book") are
        # ordinary narrative language, not spatial references to rename.
        for field in ('spatial_copy','spatial','hints','nudge','solution_steps'):
            if field in m: m[field]=reader_aliases(m[field],rooms)
        sp=m.setdefault('spatial',copy.deepcopy(m.get('spatial_copy',{})))
        for mode,key in [('puzzle','source_page_asset'),('solution','solution_asset')]:
            asset=args.maps.resolve()/f'{cid}_{mode}_original_shigai_relabelled.png'
            if not asset.is_file(): raise FileNotFoundError(asset)
            sp[key]=asset.relative_to(root).as_posix()
        sp['puzzle_asset']=sp['source_page_asset']; sp['crop']=None; sp['solution_crop']=None
        sp.update(rows=case['grid']['rows'],columns=case['grid']['columns'],
                  source_pdf_sha256=selection['source']['source_pdf_sha256'])
        data['missions'][i]=m
    master=args.output.parent/'book1_en_master_owner_review_v2.yml'
    master.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True,width=110),encoding='utf-8')
    original_brief=rb.mission_brief_page
    original_solutions=rb.solutions_pages
    def brief(c,d,m,p,progress):
        cid=m.get('spatial_source_id')
        if cid: witness_board(c,m,cases[cid],p)
        else: original_brief(c,d,m,p,progress)
    def puzzle(c,d,m,p,progress):
        map_page(c,m,root/m['spatial']['source_page_asset'],p,cases[m['spatial_source_id']])
    def solutions(c,d,missions,page):
        for m in missions:
            cid=m.get('spatial_source_id')
            if cid:
                solution_page(c,m,cases[cid],root/m['spatial']['solution_asset'],page)
                page+=1
            else: page=original_solutions(c,d,[m],page)
        return page
    rb.mission_brief_page=brief; rb.spatial_puzzle_page=puzzle; rb.solutions_pages=solutions
    pages=rb.render(master,args.output)
    print(f'PASS: V2 owner review rendered, {pages} pages -> {args.output}')


if __name__=='__main__': main()
