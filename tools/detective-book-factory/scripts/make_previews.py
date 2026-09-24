from __future__ import annotations
import argparse
from pathlib import Path
import fitz


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pdf',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--dpi',type=int,default=144)
    a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    doc=fitz.open(a.pdf); zoom=a.dpi/72
    mat=fitz.Matrix(zoom,zoom)
    for i,page in enumerate(doc,1):
        pix=page.get_pixmap(matrix=mat,alpha=False)
        pix.save(out/f'page_{i:03d}.png')
    print(f'Rendered {len(doc)} previews to {out}')

if __name__=='__main__':
    main()
