from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml
from pypdf import PdfReader

REQUIRED_MISSION_KEYS = {"number","rank","type","title","guides","hook","objective","dialogue","meta_reveal","nudge","solution_steps"}


def check_content(root: Path, content: Path) -> list[str]:
    errors=[]
    data=yaml.safe_load(content.read_text(encoding='utf-8'))
    missions=data.get('missions',[])
    nums=[m.get('number') for m in missions]
    if nums != sorted(nums): errors.append('Mission numbers are not sorted.')
    if len(nums)!=len(set(nums)): errors.append('Mission numbers are not unique.')
    for m in missions:
        missing=sorted(REQUIRED_MISSION_KEYS-set(m))
        if missing: errors.append(f"Case {m.get('number')}: missing keys {missing}")
        if not m.get('solution_steps'): errors.append(f"Case {m.get('number')}: no solution steps")
        for d in m.get('dialogue',[]):
            if d.get('speaker') not in data.get('characters',{}):
                errors.append(f"Case {m.get('number')}: unknown speaker {d.get('speaker')}")
        if m.get('type')=='spatial':
            sp=m.get('spatial',{})
            for key in ('source_page_asset','solution_asset'):
                p=root/sp.get(key,'')
                if not p.exists(): errors.append(f"Case {m.get('number')}: missing {key}: {p}")
    for key,info in data.get('characters',{}).items():
        p=root/info.get('asset','')
        if not p.exists(): errors.append(f"Character {key}: missing asset {p}")
    return errors


def check_pdf(pdf: Path, min_pages=10) -> list[str]:
    errors=[]
    if not pdf.exists(): return [f'Missing PDF: {pdf}']
    try:
        r=PdfReader(str(pdf))
    except Exception as e:
        return [f'PDF cannot be opened: {e}']
    if len(r.pages)<min_pages: errors.append(f'PDF has {len(r.pages)} pages; expected at least {min_pages}.')
    target=(612.0,792.0)
    for i,p in enumerate(r.pages,1):
        w=float(p.mediabox.width); h=float(p.mediabox.height)
        if abs(w-target[0])>0.5 or abs(h-target[1])>0.5:
            errors.append(f'Page {i}: unexpected size {w:.1f}x{h:.1f} pt')
    return errors


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--content',required=True)
    ap.add_argument('--pdf',required=True)
    ap.add_argument('--min-pages',type=int,default=10)
    ap.add_argument('--report',default=None)
    a=ap.parse_args()
    content=Path(a.content).resolve(); root=content.parent.parent
    pdf=Path(a.pdf).resolve()
    errors=check_content(root,content)+check_pdf(pdf,a.min_pages)
    lines=[f'HMDA PREFLIGHT: {"PASS" if not errors else "FAIL"}',f'Content: {content}',f'PDF: {pdf}']
    if errors:
        lines.append(''); lines.extend(f'- {e}' for e in errors)
    else:
        lines += ['', 'All required content fields are present.', 'Referenced character and spatial assets exist.', 'Mission numbers are unique and sorted.', 'PDF is openable and uses Letter 8.5x11 on every page.']
    text='\n'.join(lines)+'\n'
    print(text,end='')
    if a.report:
        rp=Path(a.report); rp.parent.mkdir(parents=True,exist_ok=True); rp.write_text(text,encoding='utf-8')
    sys.exit(1 if errors else 0)

if __name__=='__main__': main()
