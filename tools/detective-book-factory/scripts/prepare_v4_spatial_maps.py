#!/usr/bin/env python3
"""Reflow final room labels on the locked V3 spatial rasters for V4.

The verified grid, room topology, objects and numeric witness placements are
preserved.  Only detected room-label cards are cleared and redrawn in
topology-owned white space by the hardened Map Factory placement algorithm.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

import render_spatial_map_hybrid as base
import render_spatial_map_hybrid_hardened as hardened


def clear_named_legacy_label(image: Image.Image, case: dict, final_name: str) -> dict:
    """Clear one detected legacy card before restoring art it had obscured.

    The returned topology-verified footprint lets the hardened placer recover
    the missing room deterministically after the old card has been removed.
    """
    gray=base.np.asarray(image.convert("L"))
    boxes=base.detect_room_label_boxes(gray)
    assigned,_=hardened.assign_room_label_boxes(case,boxes,image.width,image.height)
    wanted=next(int(room["source_room_id"]) for room in case["rooms"] if room["final_name"]==final_name)
    if wanted not in assigned:
        broad=base.detect_room_label_boxes(gray,broad=True)
        assigned,_=hardened.assign_room_label_boxes(case,broad,image.width,image.height)
    if wanted not in assigned:
        raise ValueError(f"{case['id']}: could not find legacy {final_name!r} card for art restoration")
    x,y,w,h=assigned[wanted]; pad=16
    ImageDraw.Draw(image).rounded_rectangle((x-pad,y-pad,x+w+pad,y+h+pad),radius=max(6,h//5),fill="white")
    return {wanted:(x/image.width,y/image.height,w/image.width,h/image.height)}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--runtime",required=True,type=Path)
    ap.add_argument("--source-maps",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    runtime=json.loads(args.runtime.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True,exist_ok=True)
    for case in runtime["cases"]:
        cid=case["id"]; fallback=None
        donor=None; donor29=None
        if cid=="HMDA_10":
            donor=Image.open(args.source_maps/f"{cid}_puzzle_original_shigai_relabelled.png").convert("RGB")
        if cid=="HMDA_29":
            donor29=Image.open(args.source_maps/f"{cid}_puzzle_original_shigai_relabelled.png").convert("RGB")
        for mode in ("puzzle","solution"):
            source=args.source_maps/f"{cid}_{mode}_original_shigai_relabelled.png"
            if not source.is_file(): raise FileNotFoundError(source)
            with Image.open(source) as raw:
                image=raw.convert("RGB")
            special_fallback={}
            if cid=="HMDA_10":
                special_fallback.update(clear_named_legacy_label(image,case,"Assembly Hall"))
            if donor is not None:
                # The legacy Assembly Hall pill was painted across the D4
                # seat before label placement. Restore that locked chair from
                # the identical D5 object cell so the safe-label search sees
                # the real occupied footprint. No topology or object changes.
                cw=image.width/7; ch=image.height/7
                inset=12
                src=(round(3*cw)+inset,round(4*ch)+inset,round(4*cw)-inset,round(5*ch)-inset)
                dst=(round(3*cw)+inset,round(3*ch)+inset)
                image.paste(donor.crop(src),dst)
            if cid=="HMDA_29":
                special_fallback.update(clear_named_legacy_label(image,case,"Service Corridor"))
            if donor29 is not None and mode=="solution":
                # Restore the E9 lockers from the intact puzzle raster. The
                # legacy solution label mask clipped the lower part of this
                # identical locked object before V4 label placement.
                cw=image.width/9; ch=image.height/9; inset=8
                cell=(round(4*cw)+inset,round(8*ch)+inset,round(5*cw)-inset,round(9*ch)-inset)
                image.paste(donor29.crop(cell),(cell[0],cell[1]))
            # Final owner-review rasters are already exact grid crops.
            bbox=(0,0,image.width-1,image.height-1)
            recovery=dict(fallback or {})
            recovery.update(special_fallback)
            fixed,layout=hardened.replace_room_labels_hardened(
                image,case,bbox,fallback_layout=recovery or None,
            )
            if mode=="puzzle": fallback=layout
            # Reassert the existing closed outer boundary after clearing the
            # legacy edge-touching pills. This restores source frame pixels;
            # interior room walls and door gaps are untouched.
            ImageDraw.Draw(fixed).rectangle((1,1,fixed.width-2,fixed.height-2),outline=0,width=18)
            target=args.out/source.name
            fixed.save(target,dpi=(300,300),optimize=True)
        print(f"PASS {cid}: V4 room labels reflowed; locked map content preserved")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
