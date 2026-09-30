#!/usr/bin/env python3
"""Synthetic smoke test for the HMDA Witness Board + Live Case Map spread.

No Shigai/private source bytes are used here. The test protects the reusable
presentation layer, alias substitution, print-page generation and basic overflow
behavior with synthetic data only.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from render_spatial_case_spreads import map_page, witness_board
import render_book as rb


def main() -> None:
    case = {
        "characters": [
            {"source_name": "Alice", "display_name": "Nova"},
            {"source_name": "Bob", "display_name": "Atlas"},
            {"source_name": "Cara", "display_name": "Cleo"},
        ]
    }
    mission = {
        "number": 7,
        "rank": "Rookie",
        "status": "ACTIVE FILE",
        "title": "The Missing Archive Key",
        "hook": "A sealed archive drawer was opened during lunch, but every witness remembers a different detail.",
        "objective": "Use only the witness statements and the case map to identify the one location that fits every fact.",
        "dialogue": [
            {"speaker": "nini", "text": "Start with the exact facts."},
            {"speaker": "dilo", "text": "Then test the suspicious parts."},
        ],
        "spatial_copy": {
            "clue_cards": [
                "Alice was in the north room and never crossed the center corridor.",
                "Bob stood two rooms away from Alice, not beside the archive door.",
                "Cara was in a room on the east side of the map.",
                "Alice and Cara were never in the same row.",
                "Bob could see the stairs but could not see the archive desk.",
                "Cara was closer to the evidence locker than Bob was.",
                "The archive key was not found in any room used by Alice.",
                "The final location must satisfy all seven earlier statements at once.",
            ]
        },
    }

    with tempfile.TemporaryDirectory(prefix="hmda-spread-smoke-") as td:
        tmp = Path(td)
        map_png = tmp / "synthetic_map.png"
        im = Image.new("RGB", (1200, 1500), "white")
        draw = ImageDraw.Draw(im)
        for x in (100, 500, 900):
            draw.rectangle((x, 180, x + 220, 1320), outline="black", width=8)
        for y in (380, 760, 1140):
            draw.line((100, y, 1120, y), fill="black", width=6)
        im.save(map_png)

        out = tmp / "paired_spread.pdf"
        c = Canvas(str(out), pagesize=(rb.PAGE_W, rb.PAGE_H))
        witness_board(c, mission, case, 1)
        map_page(c, mission, map_png, 2)
        c.save()

        reader = PdfReader(str(out))
        assert len(reader.pages) == 2, "paired spread must contain exactly 2 pages"
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        for expected in (
            "WITNESS BOARD",
            "YOUR OBJECTIVE",
            "WITNESS STATEMENTS",
            "FOLLOW THE EVIDENCE",
            "LIVE CASE MAP",
            "YOUR VERDICT",
            "Nova",
            "Atlas",
            "Cleo",
        ):
            assert expected in text, f"missing expected spread text: {expected}"

        for forbidden in ("Alice", "Bob", "Cara"):
            assert forbidden not in text, f"raw source identity leaked into reader-facing spread: {forbidden}"

        assert out.stat().st_size > 10_000, "spread PDF unexpectedly small"

    print("PASS: synthetic premium Witness Board + Live Case Map spread renders with alias-safe reader copy")


if __name__ == "__main__":
    main()
