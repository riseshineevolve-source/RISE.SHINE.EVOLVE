#!/usr/bin/env python3
"""Fail-closed regression guard for the owner-locked Detective V3 opening.

This test intentionally does not need private visual assets. It protects the
semantic page order and the renderer wiring that previously mixed Page 3 and
Page 4.
"""
from __future__ import annotations

from pathlib import Path
import re

from build_v3_final_text_contract import build_contract

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts/build_v3_premium_interior.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    contract = build_contract()
    front = {item["number"]: item["markdown"] for item in contract["front_pages"]}

    require("WILL YOU CLAIM IT?" in front[3], "Page 3 lost the cold-open invitation")
    require("YOUR SQUAD" not in front[3], "Page 3 source is contaminated by squad content")
    require("IF ACCEPTED: REPORT TO THE CASE TABLE." not in front[3],
            "Page 3 must end before Academy/team explanation")
    require("YOUR SQUAD" in front[4], "Page 4 lost YOUR SQUAD")
    require("New recruit at the Case Table." in front[4],
            "Page 4 lost the owner-approved general squad opener")
    require("Helmet on or off?" not in front[4],
            "Page 4 opening COMMS regressed to the premature helmet joke")
    require("Come visit us online - we saved a cozy spot just for you:" in front[2],
            "Page 2 lost the owner website CTA")
    require("Rise.Shine.Evolve.Learning Hub." in front[2],
            "Page 2 lost the Facebook line")

    source = RENDERER.read_text(encoding="utf-8")
    require("self.grid(M, H-58, 58, 5)" not in source,
            "global upper-left ruler/micro-grid regressed")
    require("def draw_comms_frame(" in source,
            "readable COMMS frame helper missing")
    require(re.search(r"elif number == 3:\s*\n\s*draw_black_envelope_page\(", source) is not None,
            "renderer Page 3 is not bound to black-envelope layout")
    require(re.search(r"elif number == 4:\s*\n\s*draw_squad_page\(", source) is not None,
            "renderer Page 4 is not bound to squad layout")
    require("draw_dark_grid(book.canvas, x, top-panel_h, TEXT_W, panel_h" not in source,
            "full-grid case COMMS background regressed")
    require("draw_comms_frame(book.canvas, x, top-panel_h, TEXT_W, panel_h" in source,
            "case COMMS is not wired to readable light frame")

    print("PASS: Detective V3 owner front-matter source lock")
    print("PAGE 3: black envelope only")
    print("PAGE 4: squad + general recruit COMMS")
    print("GLOBAL MICRO-GRID: absent")
    print("COMMS: readable field + decorative side grid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
