#!/usr/bin/env python3
"""Fail-closed wall/door/label + topology guard for HMDA modern-prop proofs."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import sys
from typing import Any
from PIL import Image, ImageChops, ImageDraw
import yaml

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_META=ROOT/'content'/'spatial_source_label_metadata.yml'
LOCK_FORMAT='hmda-modern-prop-structure-lock'; VERSION=1
BOUNDARY_RATIO=.12; LABEL_PAD_RATIO=.04

class GuardError(RuntimeError): pass

def canon_sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str).encode()).hexdigest()
def file_sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
def load_json(p:Path)->dict:
    v=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise GuardError(f'{p} must contain a JSON object')
    return v
def load_yaml(p:Path)->dict:
    v=yaml.safe_load(p.read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise GuardError(f'{p} must contain a YAML mapping')
    return v

def parse_cell(cell:str)->tuple[int,int]:
    s=str(cell).strip().upper(); letters=''; digits=''
    for ch in s:
        if ch.isalpha() and not digits: letters+=ch
        elif ch.isdigit(): digits+=ch
        else: raise GuardError(f'invalid cell {cell!r}')
    if not letters or not digits: raise GuardError(f'invalid cell {cell!r}')
    col=0
    for ch in letters:
        if not 'A'<=ch<='Z': raise GuardError(f'invalid cell {cell!r}')
        col=col*26+ord(ch)-64
    return col-1,int(digits)-1
def cell_name(c:int,r:int)->str:
    n=c+1; s=''
    while n: n,rem=divmod(n-1,26); s=chr(65+rem)+s
    return f'{s}{r+1}'
def grid(case:dict)->tuple[int,int]:
    try: rows=int(case['grid']['rows']); cols=int(case['grid']['columns'])
    except Exception as e: raise GuardError(f"{case.get('id')}: invalid grid") from e
    if rows<=0 or cols<=0: raise GuardError(f"{case.get('id')}: invalid grid")
    return rows,cols

def spatial_record(case:dict)->dict:
    cid=case.get('id'); rows,cols=grid(case); rooms=case.get('rooms')
    if not isinstance(rooms,list) or not rooms: raise GuardError(f'{cid}: missing rooms')
    owners={}; room_ids=set(); normalized=[]
    for room in rooms:
        if not isinstance(room,dict) or not all(k in room for k in ('source_room_id','final_name','kind','cells')): raise GuardError(f'{cid}: invalid room')
        rid=str(room['source_room_id'])
        if rid in room_ids: raise GuardError(f'{cid}: duplicate room {rid}')
        room_ids.add(rid)
        if room['kind'] not in ('room','zone'): raise GuardError(f'{cid}/room {rid}: invalid kind')
        cells=[]
        for raw in room['cells']:
            c=str(raw).upper(); x,y=parse_cell(c)
            if not (0<=x<cols and 0<=y<rows): raise GuardError(f'{cid}: {c} outside grid')
            if c in owners: raise GuardError(f'{cid}: {c} belongs to two rooms')
            owners[c]=rid; cells.append(c)
        normalized.append({'source_room_id':room['source_room_id'],'source_name':room.get('source_name'),'final_name':room['final_name'],'kind':room['kind'],'meta_carrier':bool(room.get('meta_carrier',False)),'cells':sorted(cells)})
    expected={cell_name(c,r) for r in range(rows) for c in range(cols)}
    if set(owners)!=expected: raise GuardError(f'{cid}: room partition does not cover grid exactly')
    chars=[]; seen=set()
    for p in case.get('characters',[]):
        if not isinstance(p,dict) or 'placement' not in p: raise GuardError(f'{cid}: invalid character')
        c=str(p['placement']).upper(); x,y=parse_cell(c)
        if not (0<=x<cols and 0<=y<rows) or c in seen: raise GuardError(f'{cid}: invalid/duplicate character placement {c}')
        seen.add(c); chars.append({'source_name':p.get('source_name'),'display_name':p.get('display_name'),'placement':c})
    prov=case.get('provenance') or {}
    return {'id':cid,'grid':{'rows':rows,'columns':cols},'rooms':sorted(normalized,key=lambda x:str(x['source_room_id'])),'doors':case.get('doors') or [],'characters':sorted(chars,key=lambda x:(x['placement'],str(x['source_name']))),'source_answer':case.get('source_answer'),'meta':case.get('meta'),'provenance':{k:prov.get(k) for k in ('checkpoint_sha256','scene_index','clues_index','raw_title')}}

def make_lock(runtime:dict,meta:dict,label_sha:str)->dict:
    if runtime.get('format')!='hmda-shigai-runtime': raise GuardError('runtime format must be hmda-shigai-runtime')
    records=[spatial_record(c) for c in runtime.get('cases',[])]
    if not records or len({r['id'] for r in records})!=len(records): raise GuardError('runtime cases must be non-empty with unique ids')
    records.sort(key=lambda r:r['id'])
    return {'format':LOCK_FORMAT,'version':VERSION,'mode':'presentation_only','runtime_version':runtime.get('version'),'label_metadata_sha256':label_sha,'case_count':len(records),'spatial_invariants_sha256':canon_sha(records),'cases':{r['id']:canon_sha(r) for r in records}}
def verify_lock(runtime:dict,meta:dict,lock:dict,label_sha:str)->None:
    if lock.get('format')!=LOCK_FORMAT or lock.get('version')!=VERSION or lock.get('mode')!='presentation_only': raise GuardError('invalid structure lock')
    current=make_lock(runtime,meta,label_sha)
    for k in ('label_metadata_sha256','case_count','spatial_invariants_sha256','cases'):
        if lock.get(k)!=current[k]: raise GuardError(f'structure lock drift: {k}')

def changed(before:Image.Image,after:Image.Image)->Image.Image:
    if before.size!=after.size: raise GuardError(f'raster size mismatch {before.size} != {after.size}')
    bands=ImageChops.difference(before.convert('RGBA'),after.convert('RGBA')).split(); m=bands[0]
    for b in bands[1:]: m=ImageChops.lighter(m,b)
    return m.point(lambda x:255 if x else 0,mode='1')
def count(mask:Image.Image)->int: return int(sum(mask.histogram()[1:]))
def boundary_mask(case:dict,w:int,h:int)->tuple[Image.Image,int]:
    rows,cols=grid(case); cw=w/cols; ch=h/rows; band=max(2,round(min(cw,ch)*BOUNDARY_RATIO)); im=Image.new('1',(w,h),0); d=ImageDraw.Draw(im)
    for c in range(cols+1):
        x=round(c*cw); d.rectangle((max(0,x-band),0,min(w-1,x+band),h-1),fill=255)
    for r in range(rows+1):
        y=round(r*ch); d.rectangle((0,max(0,y-band),w-1,min(h-1,y+band)),fill=255)
    return im,band
def label_ref(data:dict,surface:str)->list[float]|None:
    if data.get('state')!='explicit_reference': return None
    conf=data.get('confidence') or {}; v=conf.get('puzzle_reference_normalized') if surface=='puzzle' and isinstance(conf,dict) else None
    if v is None: v=data.get('normalized_footprint')
    if not isinstance(v,list) or len(v)!=4: raise GuardError('explicit label reference missing normalized footprint')
    v=[float(x) for x in v]; x,y,w,h=v
    if data.get('coordinate_frame') not in (None,'complete_square_outer_border') or not(0<=x<=1 and 0<=y<=1 and w>0 and h>0 and x+w<=1.0005 and y+h<=1.0005): raise GuardError(f'invalid label footprint {v}')
    return v
def label_mask(case:dict,meta:dict,w:int,h:int,surface:str)->tuple[Image.Image,list[dict]]:
    rooms=((meta.get('cases') or {}).get(str(case.get('id')),{}) or {}).get('rooms',{})
    if not isinstance(rooms,dict): raise GuardError('label metadata rooms must be a mapping')
    rows,cols=grid(case); pad=max(2,round(min(w/cols,h/rows)*LABEL_PAD_RATIO)); im=Image.new('1',(w,h),0); d=ImageDraw.Draw(im); rec=[]
    for rid,data in rooms.items():
        if not isinstance(data,dict): raise GuardError(f'invalid label metadata room {rid}')
        v=label_ref(data,surface)
        if v is None: continue
        x,y,bw,bh=v; box=[max(0,round(x*w)-pad),max(0,round(y*h)-pad),min(w,round((x+bw)*w)+pad),min(h,round((y+bh)*h)+pad)]
        d.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255); rec.append({'source_room_id':str(rid),'bbox':box,'surface':surface})
    return im,rec
def validate_pixels(before:Image.Image,after:Image.Image,case:dict,meta:dict,surface:str)->dict:
    if surface not in ('puzzle','solution'): raise GuardError(f'bad surface {surface}')
    diff=changed(before,after); w,h=before.size; edges,band=boundary_mask(case,w,h); labels,recs=label_mask(case,meta,w,h,surface); protected=ImageChops.logical_or(edges,labels); bad=ImageChops.logical_and(diff,protected)
    if count(bad):
        hit=[r['source_room_id'] for r in recs if count(diff.crop(tuple(r['bbox'])))]; raise GuardError(f"{case.get('id')}: {count(bad)} changed pixels hit protected wall/door/label surfaces; bbox={bad.getbbox()}; label_rooms={sorted(hit)}")
    return {'status':'PASS','case_id':case.get('id'),'surface':surface,'image_size':[w,h],'changed_pixels':count(diff),'protected_pixels':count(protected),'boundary_band_px':band,'label_protection_boxes':recs,'violating_pixels':0}

def select_case(runtime:dict,cid:str)->dict:
    m=[c for c in runtime.get('cases',[]) if isinstance(c,dict) and c.get('id')==cid]
    if len(m)!=1: raise GuardError(f'case {cid!r} not found exactly once')
    return m[0]
def synthetic(n:int)->tuple[dict,dict]:
    cid=f'HMDA_{n}'; split=max(1,n//2); a=[cell_name(c,r) for r in range(n) for c in range(split)]; b=[cell_name(c,r) for r in range(n) for c in range(split,n)]
    runtime={'format':'hmda-shigai-runtime','version':1,'cases':[{'id':cid,'provenance':{'checkpoint_sha256':'a'*64,'scene_index':1,'clues_index':2,'raw_title':'Synthetic'},'grid':{'rows':n,'columns':n},'rooms':[{'source_room_id':0,'source_name':'A','final_name':'ROOM A','kind':'room','cells':a},{'source_room_id':1,'source_name':'B','final_name':'ZONE B','kind':'zone','cells':b}],'doors':[{'from':cell_name(split-1,1)+':E','to':cell_name(split,1)+':W'}],'objects':[],'characters':[{'source_name':'Alex','display_name':'Alex','placement':'A1'}],'source_answer':{'name':'Alex','display_name':'Alex','coordinate':'A1'},'meta':None}]}
    meta={'version':1,'source_pdf_sha256':'b'*64,'cases':{cid:{'rooms':{0:{'state':'explicit_reference','coordinate_frame':'complete_square_outer_border','normalized_footprint':[.36,.36,.12,.04],'confidence':{'puzzle_reference_normalized':[.52,.52,.12,.04]}},1:{'state':'absent_verified'}}}}}
    return runtime,meta
def grid_image(n:int,px:int=48)->Image.Image:
    s=n*px; im=Image.new('RGBA',(s,s),'white'); d=ImageDraw.Draw(im)
    for i in range(n+1): p=min(s-1,i*px); d.line((p,0,p,s-1),fill='black'); d.line((0,p,s-1,p),fill='black')
    return im
def self_test()->None:
    for n in (6,7,9):
        runtime,meta=synthetic(n); case=runtime['cases'][0]; sha=canon_sha(meta); lock=make_lock(runtime,meta,sha); verify_lock(runtime,meta,lock,sha); before=grid_image(n); px=before.width//n
        safe=before.copy(); ImageDraw.Draw(safe).rectangle((px+16,px+16,px+28,px+28),fill='black'); assert validate_pixels(before,safe,case,meta,'puzzle')['status']=='PASS'
        bad=before.copy(); bad.putpixel((px,px+24),(200,0,0,255))
        try: validate_pixels(before,bad,case,meta,'puzzle'); raise AssertionError('boundary change passed')
        except GuardError: pass
        for surface,v in (('puzzle',[.52,.52,.12,.04]),('solution',[.36,.36,.12,.04])):
            bad=before.copy(); bad.putpixel((round((v[0]+v[2]/2)*before.width),round((v[1]+v[3]/2)*before.height)),(100,100,100,255))
            try: validate_pixels(before,bad,case,meta,surface); raise AssertionError(f'{surface} label change passed')
            except GuardError: pass
        drift=json.loads(json.dumps(runtime)); drift['cases'][0]['rooms'][0]['cells'].remove('A1'); drift['cases'][0]['rooms'][1]['cells'].append('A1')
        try: verify_lock(drift,meta,lock,sha); raise AssertionError('room drift passed')
        except GuardError: pass
        drift=json.loads(json.dumps(runtime)); drift['cases'][0]['doors'].append({'from':'A1:E','to':'B1:W'})
        try: verify_lock(drift,meta,lock,sha); raise AssertionError('door drift passed')
        except GuardError: pass
    print('PASS: structural modern-prop guard protects wall/door edge bands, attached source labels, and hash-locks topology on 6x6/7x7/9x9')

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--runtime',type=Path); ap.add_argument('--label-metadata',type=Path,default=DEFAULT_META); ap.add_argument('--lock',type=Path); ap.add_argument('--write-lock',action='store_true'); ap.add_argument('--case-id'); ap.add_argument('--before',type=Path); ap.add_argument('--after',type=Path); ap.add_argument('--surface',choices=('puzzle','solution'),default='puzzle'); ap.add_argument('--report',type=Path); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test(); return 0
    if a.runtime is None or a.lock is None: ap.error('--runtime and --lock are required unless --self-test')
    try:
        rp=a.runtime.expanduser().resolve(); mp=a.label_metadata.expanduser().resolve(); runtime=load_json(rp); meta=load_yaml(mp); sha=file_sha(mp)
        if a.write_lock:
            lock=make_lock(runtime,meta,sha); t=a.lock.expanduser().resolve(); t.parent.mkdir(parents=True,exist_ok=True); t.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(f"PASS: wrote structure lock; spatial sha256={lock['spatial_invariants_sha256']}"); return 0
        lock=load_json(a.lock.expanduser().resolve()); verify_lock(runtime,meta,lock,sha); print('PASS: structure lock matches exact runtime + label metadata')
        if a.before is None and a.after is None and a.case_id is None: return 0
        if a.before is None or a.after is None or a.case_id is None: ap.error('--case-id, --before and --after must be supplied together')
        case=select_case(runtime,a.case_id)
        with Image.open(a.before) as b, Image.open(a.after) as c: report=validate_pixels(b.copy(),c.copy(),case,meta,a.surface)
        if a.report: t=a.report.expanduser().resolve(); t.parent.mkdir(parents=True,exist_ok=True); t.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(f"PASS: {report['case_id']} {report['surface']} structural surfaces unchanged; changed_pixels={report['changed_pixels']}"); return 0
    except (OSError,ValueError,json.JSONDecodeError,yaml.YAMLError,GuardError) as e: print(f'HMDA MODERN PROP STRUCTURE: BLOCKED - {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
