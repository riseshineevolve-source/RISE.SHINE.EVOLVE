from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parent
DEFAULT_CONTENT = ROOT / "content" / "book_en.yml"
DEFAULT_OUTPUT = ROOT / "dist" / "happy-makers-detective-academy-blueprint.pdf"

PAGE_W, PAGE_H = letter
MARGIN = 0.55 * inch
BLACK = colors.HexColor("#111111")
DARK = colors.HexColor("#252525")
MID = colors.HexColor("#777777")
LIGHT = colors.HexColor("#E7E7E7")
VERY_LIGHT = colors.HexColor("#F5F5F5")
WHITE = colors.white


def register_fonts() -> tuple[str, str]:
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont("RSE", regular))
            pdfmetrics.registerFont(TTFont("RSE-Bold", bold))
            return "RSE", "RSE-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def paragraph_style(size: float = 10.2, leading: float | None = None, bold: bool = False, color=BLACK, align: int = 0) -> ParagraphStyle:
    return ParagraphStyle(
        "rse",
        fontName=FONT_BOLD if bold else FONT,
        fontSize=size,
        leading=leading or size * 1.28,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
    )


def draw_paragraph(c: canvas.Canvas, text: str, x: float, y_top: float, w: float, h: float, *, size: float = 10.2, bold: bool = False, color=BLACK, align: int = 0) -> float:
    p = Paragraph(text.replace("\n", "<br/>"), paragraph_style(size=size, bold=bold, color=color, align=align))
    _, used_h = p.wrap(w, h)
    p.drawOn(c, x, y_top - used_h)
    return used_h


def rounded_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, *, fill=WHITE, stroke=BLACK, radius: float = 10, width: float = 1.2) -> None:
    c.setLineWidth(width)
    c.setStrokeColor(stroke)
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def header(c: canvas.Canvas, label: str, page_no: int) -> None:
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.1)
    c.line(MARGIN, PAGE_H - 0.43 * inch, PAGE_W - MARGIN, PAGE_H - 0.43 * inch)
    c.setFillColor(BLACK)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(MARGIN, PAGE_H - 0.32 * inch, "HAPPY MAKERS DETECTIVE ACADEMY")
    c.setFont(FONT, 8.2)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.32 * inch, f"{label}  |  {page_no:03d}")


def footer(c: canvas.Canvas) -> None:
    c.setStrokeColor(LIGHT)
    c.line(MARGIN, 0.38 * inch, PAGE_W - MARGIN, 0.38 * inch)
    c.setFillColor(MID)
    c.setFont(FONT, 7.2)
    c.drawString(MARGIN, 0.23 * inch, "Rise.Shine.Evolve. | Draft generated from structured content")


def title_page(c: canvas.Canvas, book: dict[str, Any]) -> None:
    c.setFillColor(BLACK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(MARGIN, PAGE_H - 0.8 * inch, "CASE SYSTEM: ONLINE")
    draw_paragraph(c, book["title"], MARGIN, PAGE_H - 2.0 * inch, PAGE_W - 2 * MARGIN, 1.8 * inch, size=27, bold=True, color=WHITE)
    draw_paragraph(c, book["subtitle"], MARGIN, PAGE_H - 3.25 * inch, PAGE_W - 2 * MARGIN, 0.9 * inch, size=14.5, color=colors.HexColor("#DDDDDD"))
    rounded_box(c, MARGIN, 1.35 * inch, PAGE_W - 2 * MARGIN, 1.35 * inch, fill=WHITE, stroke=WHITE, radius=14)
    draw_paragraph(c, book["hook"], MARGIN + 0.28 * inch, 2.42 * inch, PAGE_W - 2 * MARGIN - 0.56 * inch, 0.95 * inch, size=12.2, bold=True)
    c.setFillColor(colors.HexColor("#BDBDBD"))
    c.setFont(FONT, 8.3)
    c.drawString(MARGIN, 0.75 * inch, "BLUEPRINT EDITION | content-driven master for print production")
    c.showPage()


def intro_page(c: canvas.Canvas, book: dict[str, Any], page_no: int) -> int:
    header(c, "MISSION BRIEF", page_no)
    y = PAGE_H - 0.8 * inch
    draw_paragraph(c, "THE PREMISE", MARGIN, y, PAGE_W - 2 * MARGIN, 0.45 * inch, size=17, bold=True)
    y -= 0.55 * inch
    rounded_box(c, MARGIN, y - 2.1 * inch, PAGE_W - 2 * MARGIN, 2.0 * inch, fill=VERY_LIGHT, stroke=BLACK)
    draw_paragraph(c, book["premise"], MARGIN + 0.24 * inch, y - 0.18 * inch, PAGE_W - 2 * MARGIN - 0.48 * inch, 1.6 * inch, size=11.3)
    y -= 2.45 * inch
    draw_paragraph(c, "THE ZERO RULE", MARGIN, y, PAGE_W - 2 * MARGIN, 0.4 * inch, size=16, bold=True)
    y -= 0.48 * inch
    rounded_box(c, MARGIN, y - 1.2 * inch, PAGE_W - 2 * MARGIN, 1.12 * inch, fill=BLACK, stroke=BLACK)
    draw_paragraph(c, book["zero_rule"], MARGIN + 0.24 * inch, y - 0.18 * inch, PAGE_W - 2 * MARGIN - 0.48 * inch, 0.8 * inch, size=14, bold=True, color=WHITE, align=1)
    y -= 1.55 * inch
    draw_paragraph(c, "META-MYSTERY ENGINE", MARGIN, y, PAGE_W - 2 * MARGIN, 0.4 * inch, size=16, bold=True)
    y -= 0.45 * inch
    draw_paragraph(c, book["meta_engine"], MARGIN, y, PAGE_W - 2 * MARGIN, 1.8 * inch, size=10.7)
    footer(c)
    c.showPage()
    return page_no + 1


def squad_page(c: canvas.Canvas, squad: list[dict[str, str]], page_no: int) -> int:
    header(c, "YOUR SQUAD", page_no)
    draw_paragraph(c, "YOU ARE THE DETECTIVE. THEY ARE YOUR SQUAD.", MARGIN, PAGE_H - 0.9 * inch, PAGE_W - 2 * MARGIN, 0.55 * inch, size=18.5, bold=True)
    y = PAGE_H - 1.5 * inch
    box_h = 1.22 * inch
    for member in squad:
        rounded_box(c, MARGIN, y - box_h, PAGE_W - 2 * MARGIN, box_h - 0.08 * inch, fill=WHITE, stroke=LIGHT, radius=10, width=1)
        c.setFillColor(BLACK)
        c.setFont(FONT_BOLD, 11.2)
        c.drawString(MARGIN + 0.18 * inch, y - 0.27 * inch, f"{member['name']}  |  {member['role']}")
        draw_paragraph(c, member["voice"], MARGIN + 0.18 * inch, y - 0.43 * inch, PAGE_W - 2 * MARGIN - 0.36 * inch, 0.55 * inch, size=9.6)
        y -= box_h
    footer(c)
    c.showPage()
    return page_no + 1


def chapter_page(c: canvas.Canvas, chapter: dict[str, Any], page_no: int) -> int:
    c.setFillColor(BLACK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10)
    c.drawString(MARGIN, PAGE_H - 0.7 * inch, f"CHAPTER {chapter['number']:02d}")
    draw_paragraph(c, chapter["title"], MARGIN, PAGE_H - 1.65 * inch, PAGE_W - 2 * MARGIN, 1.4 * inch, size=28, bold=True, color=WHITE)
    draw_paragraph(c, chapter["promise"], MARGIN, PAGE_H - 3.0 * inch, PAGE_W - 2 * MARGIN, 1.0 * inch, size=13.5, color=colors.HexColor("#D0D0D0"))
    c.setStrokeColor(colors.HexColor("#888888"))
    c.line(MARGIN, 1.0 * inch, PAGE_W - MARGIN, 1.0 * inch)
    c.setFont(FONT_BOLD, 9)
    c.drawString(MARGIN, 0.72 * inch, "STATUS: NEW CASES UNLOCKED")
    c.showPage()
    return page_no + 1


def mission_page(c: canvas.Canvas, mission: dict[str, Any], page_no: int) -> int:
    header(c, f"CASE {mission['number']:02d}", page_no)
    top = PAGE_H - 0.82 * inch
    c.setFillColor(BLACK)
    c.setFont(FONT_BOLD, 8.8)
    c.drawString(MARGIN, top, mission["type"].upper())
    draw_paragraph(c, mission["title"], MARGIN, top - 0.18 * inch, PAGE_W - 2 * MARGIN, 0.65 * inch, size=19.5, bold=True)
    c.setFillColor(MID)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(MARGIN, top - 0.78 * inch, "SQUAD")
    c.setFont(FONT, 9)
    c.drawString(MARGIN + 0.58 * inch, top - 0.78 * inch, " + ".join(mission["guides"]))

    y = top - 1.05 * inch
    rounded_box(c, MARGIN, y - 0.96 * inch, PAGE_W - 2 * MARGIN, 0.9 * inch, fill=BLACK, stroke=BLACK)
    draw_paragraph(c, mission["objective"], MARGIN + 0.22 * inch, y - 0.17 * inch, PAGE_W - 2 * MARGIN - 0.44 * inch, 0.58 * inch, size=11.4, bold=True, color=WHITE)

    y -= 1.18 * inch
    sections = [
        ("STORY BEAT", mission["story"]),
        ("PUZZLE ENGINE", mission["puzzle"]),
        ("ROOM ZERO THREAD", mission["meta"]),
        ("SQUAD BANTER", mission["banter"]),
    ]
    heights = [1.35, 1.2, 1.05, 1.15]
    for (label, text), h_in in zip(sections, heights):
        h = h_in * inch
        rounded_box(c, MARGIN, y - h, PAGE_W - 2 * MARGIN, h - 0.07 * inch, fill=VERY_LIGHT if label != "SQUAD BANTER" else WHITE, stroke=LIGHT, radius=9, width=0.9)
        c.setFillColor(BLACK)
        c.setFont(FONT_BOLD, 8.1)
        c.drawString(MARGIN + 0.17 * inch, y - 0.24 * inch, label)
        draw_paragraph(c, text, MARGIN + 0.17 * inch, y - 0.38 * inch, PAGE_W - 2 * MARGIN - 0.34 * inch, h - 0.45 * inch, size=9.5)
        y -= h

    footer(c)
    c.showPage()
    return page_no + 1


def final_page(c: canvas.Canvas, book: dict[str, Any], page_no: int) -> int:
    header(c, "FINAL REVEAL", page_no)
    draw_paragraph(c, "THE ROOM ZERO TWIST", MARGIN, PAGE_H - 0.95 * inch, PAGE_W - 2 * MARGIN, 0.65 * inch, size=21, bold=True)
    rounded_box(c, MARGIN, PAGE_H - 4.0 * inch, PAGE_W - 2 * MARGIN, 2.55 * inch, fill=BLACK, stroke=BLACK, radius=14)
    draw_paragraph(c, book["final_twist"], MARGIN + 0.3 * inch, PAGE_H - 1.7 * inch, PAGE_W - 2 * MARGIN - 0.6 * inch, 2.0 * inch, size=12.2, color=WHITE)
    y = PAGE_H - 4.4 * inch
    draw_paragraph(c, "SERIES HOOK", MARGIN, y, PAGE_W - 2 * MARGIN, 0.4 * inch, size=15, bold=True)
    y -= 0.42 * inch
    draw_paragraph(c, book["series_hook"], MARGIN, y, PAGE_W - 2 * MARGIN, 1.2 * inch, size=11)
    footer(c)
    c.showPage()
    return page_no + 1


def validate(data: dict[str, Any]) -> None:
    required = ["book", "squad", "chapters", "missions"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Missing top-level keys: {', '.join(missing)}")
    numbers = [m["number"] for m in data["missions"]]
    if len(numbers) != len(set(numbers)):
        raise ValueError("Mission numbers must be unique")
    if numbers != sorted(numbers):
        raise ValueError("Missions must be sorted by number")


def render(content_path: Path, output_path: Path) -> None:
    data = yaml.safe_load(content_path.read_text(encoding="utf-8"))
    validate(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter, pageCompression=1)
    c.setTitle(data["book"]["title"])
    c.setAuthor("Rise.Shine.Evolve.")

    title_page(c, data["book"])
    page_no = 2
    page_no = intro_page(c, data["book"], page_no)
    page_no = squad_page(c, data["squad"], page_no)

    missions_by_chapter: dict[int, list[dict[str, Any]]] = {}
    for mission in data["missions"]:
        missions_by_chapter.setdefault(int(mission["chapter"]), []).append(mission)

    for chapter in data["chapters"]:
        page_no = chapter_page(c, chapter, page_no)
        for mission in missions_by_chapter.get(int(chapter["number"]), []):
            page_no = mission_page(c, mission, page_no)

    final_page(c, data["book"], page_no)
    c.save()
    print(f"Built: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Happy Makers Detective Academy PDF from YAML content.")
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render(args.content, args.output)


if __name__ == "__main__":
    main()
