#!/usr/bin/env python3
"""Compose the V3 reader text with the exact owner and spatial evidence assets.

This is an interior proof, not an English freeze or publication action. The
source verifier and asset hashes are mandatory. The physical page plan grows
with the copy, and reverse back matter is drawn upside down in the PDF.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import yaml
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import render_book as rb
from build_v3_final_text_contract import build_contract
from prepare_v3_premium_inputs import MASTER_SHA256, SQUAD_SCANNER_SHA256

W, H = letter
M = 45
TEXT_W = W - 2 * M
BOTTOM = 48
TOP = H - 72
WHITE = colors.white
INK = colors.black
GRAY = colors.HexColor("#626262")
LINE = colors.HexColor("#B8B8B8")
PALE = colors.HexColor("#F4F4F4")
OWNER_DIR = ROOT / "assets/production/v3_owner_locked"
MAP_DIR = ROOT / "assets/production/v3_spatial_locked"
OWNER_CONTRACT = ROOT / "content/v3_owner_visual_contract.json"
MAP_CONTRACT = ROOT / "content/v3_locked_spatial_evidence_contract.json"
MASTER = ROOT / "dist/book1_en_master_owner_review_v4.yml"
RUNTIME = ROOT / "dist/hmda_spatial_runtime_v4.json"
DEFAULT_PDF = ROOT / "dist/HMDA_Book1_EN_PREMIUM_ALMOST_KDP_READY_V3.pdf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_assets() -> dict:
    owner = json.loads(OWNER_CONTRACT.read_text(encoding="utf-8"))
    maps = json.loads(MAP_CONTRACT.read_text(encoding="utf-8"))
    for name, meta in owner["assets"].items():
        path = OWNER_DIR / name
        if not path.is_file() or sha(path) != meta["sha256"]:
            raise ValueError(f"owner visual contract failed: {name}")
    for name, expected in maps["maps"].items():
        path = MAP_DIR / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"spatial map contract failed: {name}")
    if sha(RUNTIME) != maps["runtime"]["packet_render_runtime_sha256"]:
        raise ValueError("packet render runtime hash drift")
    if sha(MASTER) != MASTER_SHA256:
        raise ValueError("audited evidence hydration master hash drift")
    if sha(ROOT / "assets/production/squad-scanner.png") != SQUAD_SCANNER_SHA256:
        raise ValueError("approved scanner squad variant hash drift")
    return {"owner_assets": 4, "locked_maps": 30, "runtime_sha256": sha(RUNTIME)}


def inline(source: str) -> str:
    value = html.escape(source.strip().replace("  ", " "))
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='RSE-Mono'>\1</font>", value)
    return value


def plain(source: str) -> str:
    return re.sub(r"\*\*|\*|`", "", source).strip()


def paragraphs(markdown: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    pending: list[str] = []
    def flush() -> None:
        if pending:
            blocks.append(("body", " ".join(line.strip() for line in pending)))
            pending.clear()
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line or line == "---":
            flush()
        elif line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
            flush(); blocks.append(("heading", line.lstrip("# ").strip()))
        elif line.startswith("- "):
            flush(); blocks.append(("bullet", line[2:]))
        elif re.match(r"^\d+\.\s", line):
            flush(); blocks.append(("number", line))
        else:
            pending.append(line)
    flush()
    return blocks


class Book:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.canvas = canvas.Canvas(str(path), pagesize=letter, pageCompression=1)
        self.canvas.setTitle("Happy Makers Detective Academy - The Mystery of Room Zero - V3 Interior Proof")
        self.canvas.setAuthor("Rise.Shine.Evolve")
        self.path = path
        self.page = 0
        self.open = False
        self.y = TOP
        self.current: dict = {}
        self.index: list[dict] = []
        self.errors: list[str] = []

    def begin(self, family: str, case: int | None = None, side: str = "upright", label: str | None = None) -> None:
        if self.open:
            self.end()
        self.page += 1
        self.open = True
        self.current = {
            "physical_page": self.page,
            "family": family,
            "case": case,
            "physical_side": "verso / left" if self.page % 2 == 0 else "recto / right",
            "side": side,
        }
        self.index.append(self.current)
        self.y = TOP
        c = self.canvas
        if side == "reverse":
            c.saveState(); c.translate(W, H); c.rotate(180)
        c.setFillColor(WHITE); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(INK); c.rect(M, H-43, TEXT_W, 25, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(rb.BOLD, 9.3)
        c.drawString(M+10, H-34, "DETECTIVE ACADEMY")
        title = plain(label or family).upper()
        c.drawRightString(W-M-10, H-34, f"{title[:37]}  /  {self.page:03d}")
        c.setFillColor(INK); c.setFont(rb.FONT, 9)
        c.drawRightString(W-M, 27, f"{self.page:03d}")
        self.grid(M, H-58, 58, 5)

    def grid(self, x: float, y: float, w: float, h: float) -> None:
        c = self.canvas
        c.setStrokeColor(colors.HexColor("#D3D3D3")); c.setLineWidth(.3)
        for xx in range(int(x), int(x+w)+1, 9):
            c.line(xx, y, xx, y+h)
        for yy in range(int(y), int(y+h)+1, 9):
            c.line(x, yy, x+w, yy)

    def end(self) -> None:
        if not self.open:
            return
        if self.current["side"] == "reverse":
            self.canvas.restoreState()
        self.canvas.showPage()
        self.open = False

    def ensure(self, height: float, gap: float = 8) -> None:
        if self.y - height - gap < BOTTOM:
            meta = self.current.copy()
            self.begin(meta["family"] + " continuation", meta["case"], meta["side"])

    def rule(self) -> None:
        self.ensure(8)
        self.canvas.setStrokeColor(LINE); self.canvas.setLineWidth(.7)
        self.canvas.line(M, self.y, W-M, self.y)
        self.y -= 13

    def text(self, source: str, size: float = 10.8, bold: bool = False, color=INK,
             width: float = TEXT_W, x: float = M, gap: float = 10, keep: bool = True) -> float:
        markup = inline(source)
        style = ParagraphStyle("v3", fontName=rb.BOLD if bold else rb.FONT,
                               fontSize=size, leading=size*1.38, textColor=color)
        p = Paragraph(markup, style)
        _, height = p.wrap(width, H)
        if keep:
            self.ensure(height, gap)
        if self.y - height < BOTTOM - 1:
            self.errors.append(f"text outside safe area on page {self.page}: {source[:55]}")
        p.drawOn(self.canvas, x, self.y-height)
        self.y -= height+gap
        return height

    def heading(self, source: str, size: float = 16) -> None:
        self.ensure(size*2.5)
        self.text(plain(source), size=size, bold=True, gap=12)
        self.rule()

    def card(self, heading: str, text: str, kind: str = "body") -> None:
        size = 11.1 if kind == "objective" else 10.8
        body = Paragraph(inline(text), ParagraphStyle("card", fontName=rb.BOLD if kind == "objective" else rb.FONT,
                                  fontSize=size, leading=size*1.35, textColor=INK))
        _, body_h = body.wrap(TEXT_W-32, H)
        h = body_h+42
        self.ensure(h, 12)
        x, top = M, self.y
        c = self.canvas
        c.setFillColor(WHITE); c.setStrokeColor(INK if kind == "objective" else LINE)
        c.setLineWidth(1.35 if kind == "objective" else .75)
        c.roundRect(x, top-h, TEXT_W, h, 8, fill=1, stroke=1)
        c.setFillColor(INK); c.setFont(rb.BOLD, 9.3)
        c.drawString(x+16, top-19, plain(heading).upper())
        self.grid(x+TEXT_W-76, top-22, 58, 5)
        body.drawOn(c, x+16, top-30-body_h)
        self.y -= h+12

    def image(self, path: Path, max_w: float, max_h: float, gap: float = 12) -> None:
        with Image.open(path) as im:
            iw, ih = im.size
            rgba = im.convert("RGBA")
            paper = Image.new("RGBA", rgba.size, (255,255,255,255))
            paper.alpha_composite(rgba)
            grayscale = paper.convert("RGB").convert("L")
        scale = min(max_w/iw, max_h/ih)
        w, h = iw*scale, ih*scale
        self.ensure(h, gap)
        x = (W-w)/2
        self.canvas.drawImage(ImageReader(grayscale), x, self.y-h, w, h, preserveAspectRatio=True)
        self.y -= h+gap

    def render_md(self, markdown: str, heading_size: float = 16, compact: bool = False) -> None:
        for kind, value in paragraphs(markdown):
            if kind == "heading":
                self.heading(value, 11.5 if compact else heading_size)
            elif kind == "bullet":
                self.text("• " + value, size=9.35 if compact else 10.6, gap=3 if compact else 5)
            elif kind == "number":
                self.text(value, size=9.35 if compact else 10.6, gap=3 if compact else 5)
            else:
                self.text(value, size=9.35 if compact else 10.8, gap=4 if compact else 10)

    def save(self) -> None:
        self.end(); self.canvas.save()


def split_case(markdown: str) -> tuple[str, dict[str, str]]:
    pieces = re.split(r"(?=^### )", markdown, flags=re.MULTILINE)
    opening = pieces[0]
    sections: dict[str, str] = {}
    for piece in pieces[1:]:
        title = piece.splitlines()[0][4:].strip()
        sections[title] = "\n".join(piece.splitlines()[1:]).strip()
    return opening, sections


def evidence_cards(mission: dict, number: int) -> list[str]:
    """Read only puzzle payload fields from the verified earlier data model."""
    t = mission.get("type")
    payload_key = {"room-zero-checkpoint": "checkpoint", "multi-stage-finale": "finale"}.get(t, t.replace("-", "_"))
    data = mission.get(payload_key, {})
    cards: list[str] = []
    if number == 9:
        return [
            "RECRUIT BADGE RECORD: plain Academy 0",
            "TROPHY HALL TAG: plain Academy 0",
            "OPEN NIGHT EVIDENCE LABEL: plain Academy 0",
            "OLD LOCKER ENVELOPE: plain Academy 0",
            "LOOK-TWICE ROUTING FILE: no Academy mark",
            "POSTER DECORATION: striped circle",
            "STAGE-LIGHT DIAL: ring with pointer",
        ]
    if t == "route":
        cards += [f"START: {data.get('start')}    GOAL: {data.get('goal')}"]
        cards += [f"ROUTE {v.get('id')}: " + " → ".join(v.get("path", [])) for v in data.get("options", [])]
        cards += [str(v) for v in data.get("site_conditions", [])]
    elif t == "classification":
        cards += [f"CASE WINDOW: {data.get('case_window', '')}"]
        cards += [f"RECORD {v.get('id')}: {v.get('item')} — {v.get('label')}" for v in data.get("items", [])]
    elif t == "consistency":
        mp = data.get("map", {})
        cards += [f"Each map edge takes {mp.get('walking_minutes_per_edge')} minutes."]
        cards += ["MAP LINK: " + " ↔ ".join(v) for v in mp.get("edges", [])]
        cards += [f"{v.get('speaker')}: {v.get('text')}" for v in data.get("statements", [])]
    elif t == "timeline":
        cards += data.get("rules", [])
        cards += [f"{v.get('id')}: {v.get('source')} / {v.get('shown')} / {v.get('event')}" for v in data.get("records", [])]
    elif t == "timeline-visual":
        cards += ["BUILDINGS: " + " / ".join(data.get("candidate_buildings", [])),
                  "YEARS: " + " / ".join(str(v) for v in data.get("candidate_years", []))]
        cards += data.get("evidence", [])
    elif t == "reconstruction":
        cards += [f"SCRAP {v.get('id')}: {v.get('left_edge')} | {v.get('text')} | {v.get('right_edge')}" for v in data.get("scraps", [])]
    elif t == "visual-sequence":
        cards += [str(data.get("rule", ""))]
        cards += [f"PRINT {v.get('position')}: mud {v.get('mud')}; tread {v.get('tread_arrow')}" for v in data.get("prints", [])]
    elif t == "room-zero-checkpoint":
        cards += [str(data.get("instruction", ""))]
        cards += [f"{v.get('item')}: {v.get('mark')}" for v in data.get("evidence", [])]
        if data.get("case_numbers"):
            cards += ["REVISIT CASES: " + ", ".join(str(v).zfill(2) for v in data["case_numbers"])]
    elif t == "map-overlay":
        cards += [f"LANDMARK: OLD {v.get('old')} ↔ CURRENT {v.get('current')}" for v in data.get("anchors", [])]
    elif t == "fact-theory-sort":
        cards += [f"{k}: {v}" for k,v in data.get("definitions", {}).items()]
        cards += [v.get("text", "") for v in data.get("cards", [])]
    elif t == "multi-stage-finale":
        for stage in data.get("stages", []):
            prompt = stage.get("prompt", "")
            if stage.get("id") == "CODE":
                prompt = "Enter Dilo's six-symbol locker sequence from Case 05."
            cards.append(f"{stage.get('id')}: {prompt}")
    return [str(v) for v in cards if str(v).strip()]


def draw_case_brief(book: Book, case: dict) -> dict[str, str]:
    number = case["number"]
    opening, sections = split_case(case["markdown"])
    book.begin("case brief", number, label=f"case {number:02d} / case file")
    book.text(f"CASE {number:02d}  /  {case.get('rank') or 'DETECTIVE'}  /  {case.get('status') or 'ACTIVE'}", 9.5, True)
    book.heading(case["title"], 19)
    for name in ("CASE FILE // WHAT HAPPENED", "YOUR OBJECTIVE", "INVESTIGATION RULES", "HAPPY MAKERS CHAT"):
        content = sections.get(name, "")
        if not content:
            raise ValueError(f"Case {number:02d}: missing {name}")
        if name == "HAPPY MAKERS CHAT":
            book.heading(name, 12)
            beats = [line for kind, line in paragraphs(content) if kind == "bullet"]
            col_w = (TEXT_W-11)/2
            for start in range(0, len(beats), 2):
                pair = beats[start:start+2]
                rendered = []
                for line in pair:
                    speaker, speech = line.split(":", 1) if ":" in line else ("CHAT", line)
                    # V3 speaker labels are **NAME:**; the closing Markdown
                    # asterisks after the colon belong to the label, not speech.
                    if speaker.startswith("**") and speech.startswith("**"):
                        speech = speech[2:].lstrip()
                    p = Paragraph(inline(speech.strip()), ParagraphStyle(
                        "chat", fontName=rb.FONT, fontSize=9.8, leading=12.8))
                    _, ph = p.wrap(col_w-22, H)
                    rendered.append((plain(speaker).upper(), p, ph))
                h = max(53, max(v[2] for v in rendered)+34)
                book.ensure(h, 6)
                for col, (speaker, p, ph) in enumerate(rendered):
                    x = M+col*(col_w+11)
                    book.canvas.setFillColor(WHITE); book.canvas.setStrokeColor(LINE)
                    book.canvas.roundRect(x, book.y-h, col_w, h, 6, fill=1, stroke=1)
                    book.canvas.setFillColor(INK); book.canvas.setFont(rb.BOLD, 9.2)
                    book.canvas.drawString(x+11, book.y-17, speaker)
                    p.drawOn(book.canvas, x+11, book.y-27-ph)
                book.y -= h+6
        elif name == "YOUR OBJECTIVE":
            book.card(name, content, "objective")
        else:
            panel_page, panel_top = book.page, book.y + 4
            book.heading(name, 12)
            book.render_md(content, 12)
            if book.page == panel_page:
                book.canvas.setStrokeColor(LINE)
                book.canvas.setLineWidth(.7)
                book.canvas.roundRect(M-7, book.y+2, TEXT_W+14,
                                      panel_top-book.y-2, 6, fill=0, stroke=1)
    book.end()
    return sections


def parity_prep(book: Book, number: int, label: str) -> None:
    if (book.page + 1) % 2 == 1:
        book.begin("evidence notes", number, label=label)
        book.heading(f"CASE {number:02d} // PREP THE EVIDENCE", 18)
        book.text("The paired evidence begins on the next facing spread. Keep your deductions here while you inspect it.")
        for name in ("FACTS", "POSSIBLE LINKS", "OPEN QUESTIONS"):
            height = 145
            book.ensure(height, 10)
            x, top = M, book.y
            book.canvas.setStrokeColor(LINE)
            book.canvas.setLineWidth(.8)
            book.canvas.roundRect(x, top-height, TEXT_W, height, 7, fill=0, stroke=1)
            book.canvas.setFillColor(INK)
            book.canvas.setFont(rb.BOLD, 10)
            book.canvas.drawString(x+16, top-21, name)
            book.grid(x+TEXT_W-76, top-23, 58, 5)
            for offset in (48, 72, 96, 120):
                book.canvas.setStrokeColor(LINE)
                book.canvas.setLineWidth(.45)
                book.canvas.line(x+16, top-offset, x+TEXT_W-16, top-offset)
            book.y -= height+10
        book.end()


def draw_witness_board(book: Book, case: dict, number: int) -> None:
    parity_prep(book, number, "spread preparation")
    book.begin("witness board", number, label=f"case {number:02d} / witness board")
    if book.page % 2:
        raise ValueError("Witness Board must be on physical left/even page")
    book.heading(f"CASE {number:02d} // WITNESS BOARD", 20)
    book.text("Place every witness once. Tick each statement as you use it. Keep the completed map for later evidence.")
    col_w = (TEXT_W-12)/2
    people = case["characters"]
    for start in range(0, len(people), 2):
        row = people[start:start+2]
        rendered = []
        for person in row:
            p = Paragraph(inline(person["raw_clue"]), ParagraphStyle(
                "witness", fontName=rb.FONT, fontSize=10.5, leading=14.0))
            _, ph = p.wrap(col_w-24, H)
            rendered.append((p, ph))
        h = max(77, max(v[1] for v in rendered)+40)
        if book.y-h < BOTTOM:
            raise ValueError(f"Case {number:02d}: Witness Board cannot fit one even page")
        for column, person in enumerate(row):
            x = M + column*(col_w+12)
            book.canvas.setFillColor(WHITE); book.canvas.setStrokeColor(LINE)
            book.canvas.roundRect(x, book.y-h, col_w, h, 7, fill=1, stroke=1)
            book.canvas.setFillColor(INK); book.canvas.setFont(rb.BOLD, 10.6)
            book.canvas.drawString(x+12, book.y-19, f"{start+column+1:02d} / {person['display_name'].upper()}")
            p, ph = rendered[column]
            p.drawOn(book.canvas, x+12, book.y-32-ph)
        book.y -= h+9
    book.end()


def map_crop(path: Path) -> ImageReader:
    with Image.open(path) as image:
        if image.size != (2550, 3300):
            raise ValueError(f"unexpected locked map geometry: {path}")
        return ImageReader(image.crop((158, 431, 2390, 2665)).copy())


def draw_map(book: Book, case: dict, number: int, solution: bool = False,
             response: str = "") -> None:
    family = "solution map" if solution else "live case map"
    side = "reverse" if solution else "upright"
    book.begin(family, number, side, label=f"case {number:02d} / {family}")
    if not solution and book.page % 2 != 1:
        raise ValueError("live map must immediately follow Witness Board on right/odd page")
    book.heading(f"CASE {number:02d} // {family.upper()}", 17)
    filename = f"HMDA_{number:02d}_{'solution' if solution else 'puzzle'}.png"
    c = book.canvas
    img = map_crop(MAP_DIR / filename)
    rows, cols = int(case["grid"]["rows"]), int(case["grid"]["columns"])
    image_size = 482
    x = (W-image_size)/2 + 7
    top = book.y - 25
    y = top-image_size
    if y < 162:
        raise ValueError(f"Case {number:02d}: map does not fit the page")
    c.drawImage(img, x, y, image_size, image_size)
    c.setFillColor(INK); c.setFont(rb.BOLD, 14 if cols <= 7 else 12)
    for col in range(cols):
        c.drawCentredString(x+(col+.5)*image_size/cols, top+5, chr(65+col))
    for row in range(rows):
        c.drawRightString(x-7, top-(row+.5)*image_size/rows-4, str(row+1))
    book.y = y-8
    if solution:
        answer = case["source_answer"]
        book.text(f"VERIFIED VERDICT: {answer['display_name']} at {answer['coordinate']}", 11.5, True, gap=4)
    else:
        book.text("MAP KEY  /  □ usable floor   ■ blocked object   ━ wall   · doorway", 9.7, True, gap=7)
        book.card("YOUR VERDICT / RESPONSE", response or "PERSON / WITNESS: ____________________    COORDINATE: ______")
    book.end()


def draw_case01(book: Book, mission: dict, sections: dict) -> None:
    book.begin("intake evidence", 1, label="case 01 / intake board")
    book.heading("CASE 01 // THE INTAKE GRID", 18)
    tut = mission["tutorial"]
    grid_size = 282
    grid_y = book.y-grid_size-20
    rb.draw_tutorial_grid(book.canvas, tut, (W-grid_size)/2, grid_y, grid_size, grid_size, False)
    book.y = grid_y-15
    aliases = {"ARI":"QUILL", "BEA":"MORSE", "COLE":"PIP", "DANI":"KNOX"}
    clues = []
    for clue in tut["clues"]:
        for old, new in aliases.items():
            clue = re.sub(rf"\b{old}\b", new, clue)
        clues.append(clue)
    col_w = (TEXT_W-11)/2
    for start in range(0, len(clues), 2):
        pair = clues[start:start+2]
        rendered = []
        for clue in pair:
            p = Paragraph(inline(clue), ParagraphStyle("intake", fontName=rb.FONT, fontSize=9.8, leading=12.8))
            _, ph = p.wrap(col_w-20, H)
            rendered.append((p, ph))
        h = max(53, max(v[1] for v in rendered)+29)
        for col, (p, ph) in enumerate(rendered):
            x = M+col*(col_w+11)
            book.canvas.setFillColor(WHITE); book.canvas.setStrokeColor(LINE)
            book.canvas.roundRect(x, book.y-h, col_w, h, 6, fill=1, stroke=1)
            book.canvas.setFillColor(INK); book.canvas.setFont(rb.BOLD, 9)
            book.canvas.drawString(x+10, book.y-16, f"WITNESS CLUE {start+col+1:02d}")
            p.drawOn(book.canvas, x+10, book.y-25-ph)
        book.y -= h+7
    book.render_md(sections.get("YOUR VERDICT / RESPONSE", ""), 11)
    book.end()


def draw_case03(book: Book, sections: dict) -> None:
    parity_prep(book, 3, "photo comparison preparation")
    for letter in ("A", "B"):
        book.begin(f"photo {letter}", 3, label=f"case 03 / photo {letter}")
        if (book.page % 2 == 0) != (letter == "A"):
            raise ValueError("Case 03 photographs are not facing left/right pages")
        book.heading(f"CASE 03 // PHOTO {letter}", 18)
        book.image(OWNER_DIR / f"case03_photo_{letter}.png", 450, 500, gap=5)
        if letter == "B":
            if book.y < 111:
                raise ValueError("Case 03 ten-mark tracker cannot fit below Photo B")
            spacing = TEXT_W/10
            book.canvas.setStrokeColor(INK); book.canvas.setFillColor(INK)
            book.canvas.setLineWidth(1.1); book.canvas.setFont(rb.BOLD, 12)
            for i in range(10):
                cx = M+(i+.5)*spacing
                book.canvas.circle(cx, book.y-13, 10.5, fill=0, stroke=1)
                book.canvas.drawCentredString(cx, book.y-17, "?")
            book.y -= 31
            book.text("Color one question mark for each difference you find.", 9.8, gap=2)
            book.text("Mark the ten changes directly on Photo A / Photo B.", 9.8, gap=2)
        book.end()


def draw_visual_payload(book: Book, number: int, mission: dict) -> bool:
    """Draw the nonspatial evidence as an inspectable physical surface."""
    c = book.canvas
    if number == 8:
        route = mission["route"]
        book.text(f"START: {route['start']}     GOAL: {route['goal']}", 10.5, True)
        sites = (("LOBBY",0,1), ("PAINT CORRIDOR",1,0), ("COSTUME STORAGE",1,1),
                 ("STAFF STAIRS",2,0), ("SIDE HALL",2,1), ("PROP ROOM",3,1))
        for option in route["options"]:
            h = 142
            book.ensure(h, 9)
            x, top = M, book.y
            c.setStrokeColor(INK); c.setFillColor(WHITE); c.roundRect(x, top-h, TEXT_W, h, 6, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont(rb.BOLD, 9.5); c.drawString(x+12, top-17, f"ROUTE {option['id']}")
            gx, gy, cw, ch = x+18, top-103, 118, 32
            for name, col, row in sites:
                bx, by = gx+col*cw, gy+(1-row)*ch
                c.setStrokeColor(LINE); c.setFillColor(WHITE); c.rect(bx, by, cw-7, ch-5, fill=1, stroke=1)
                c.setFillColor(INK); c.setFont(rb.BOLD, 7.5)
                c.drawCentredString(bx+(cw-7)/2, by+9, name)
            path = " → ".join(option.get("path", []))
            book.y = top-h+24
            book.text(f"PATH: {path}", 8.9, True, width=TEXT_W-24, x=x+12, gap=0, keep=False)
            book.y = top-h-9
        book.text("SITE CONDITIONS: Paint Corridor closes at 16:30. Staff Stairs are locked. Walls cannot be crossed.", 10.2, True)
        return True
    if number == 11:
        items = mission["classification"]["items"]
        book.text("Compare timestamped records A-D with the printed case window. Inspect the other bag items separately.", 10.2)
        col_w = (TEXT_W-11)/2
        for start in range(0, len(items), 2):
            row = items[start:start+2]
            h = 104
            book.ensure(h, 7)
            for col, item in enumerate(row):
                x, top = M+col*(col_w+11), book.y
                c.setFillColor(WHITE); c.setStrokeColor(LINE)
                c.roundRect(x, top-h, col_w, h, 6, fill=1, stroke=1)
                c.setFillColor(INK); c.setFont(rb.BOLD, 9)
                c.drawString(x+10, top-17, f"RECORD {item.get('id', start+col+1)}")
                c.setLineWidth(1.1); c.roundRect(x+12, top-77, 47, 42, 3, fill=0, stroke=1)
                c.line(x+20, top-46, x+52, top-46)
                p = Paragraph(inline(f"{item.get('item','')}<br/>{item.get('label','')}"),
                              ParagraphStyle("item", fontName=rb.FONT, fontSize=9.4, leading=12.3))
                _, ph = p.wrap(col_w-78, H)
                p.drawOn(c, x+69, top-31-ph)
            book.y -= h+7
        return True
    if number == 16:
        photo = ROOT / "assets/production/v4/case16_old_academy_photo.png"
        if not photo.is_file():
            raise FileNotFoundError(photo)
        book.image(photo, 360, 265, gap=8)
        return False
    if number == 21:
        scraps = mission["reconstruction"]["scraps"]
        for start in range(0, len(scraps), 2):
            row = scraps[start:start+2]
            h = 126
            book.ensure(h, 14)
            for col, scrap in enumerate(row):
                x, top = M+col*270+9, book.y
                x0, x1, yt, yb = x+7, x+214, top-10, top-109
                p = c.beginPath(); p.moveTo(x0, yt); p.lineTo(x1, yt)
                edge = scrap["right_edge"]
                if edge == "straight": p.lineTo(x1, yb)
                elif edge == "notch-3":
                    p.lineTo(x1, yt-28); p.lineTo(x1+15, yt-39); p.lineTo(x1+15, yt-66); p.lineTo(x1, yt-78); p.lineTo(x1, yb)
                elif edge == "zigzag-2":
                    p.lineTo(x1, yt-24); p.lineTo(x1+15, yt-39); p.lineTo(x1-6, yt-55); p.lineTo(x1+15, yt-72); p.lineTo(x1, yb)
                elif edge == "curve-1":
                    p.lineTo(x1, yt-29); p.curveTo(x1+22, yt-35, x1+22, yt-72, x1, yt-78); p.lineTo(x1, yb)
                else: raise ValueError(f"Case 21 unsupported edge: {edge}")
                p.lineTo(x0, yb)
                edge = scrap["left_edge"]
                if edge == "straight": p.lineTo(x0, yt)
                elif edge == "notch-3":
                    p.lineTo(x0, yb+34); p.lineTo(x0+15, yb+46); p.lineTo(x0+15, yb+73); p.lineTo(x0, yb+84); p.lineTo(x0, yt)
                elif edge == "zigzag-2":
                    p.lineTo(x0, yb+33); p.lineTo(x0+15, yb+48); p.lineTo(x0-6, yb+64); p.lineTo(x0+15, yb+81); p.lineTo(x0, yt)
                elif edge == "curve-1":
                    p.lineTo(x0, yb+34); p.curveTo(x0+22, yb+40, x0+22, yb+76, x0, yb+83); p.lineTo(x0, yt)
                else: raise ValueError(f"Case 21 unsupported edge: {edge}")
                p.close()
                c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1.3)
                c.drawPath(p, fill=1, stroke=1)
                c.setFillColor(INK); c.setFont(rb.BOLD, 10)
                c.drawString(x+29, top-34, f"SCRAP {scrap['id']}")
                ptext = Paragraph(inline(str(scrap["text"])), ParagraphStyle(
                    "scrap", fontName=rb.BOLD, fontSize=11.2, leading=14))
                _, pheight = ptext.wrap(165, H)
                ptext.drawOn(c, x+29, top-54-pheight)
                c.setFont(rb.FONT, 8.6)
                c.drawString(x+29, top-94, f"{scrap['left_edge']}  /  {scrap['right_edge']}")
            book.y -= h+14
        return True
    if number == 24:
        prints = mission["visual_sequence"]["prints"]
        panel_w = (TEXT_W-30)/4
        h = 285
        book.ensure(h, 8)
        top = book.y
        for i, item in enumerate(prints):
            x = M+i*(panel_w+10)
            c.setFillColor(WHITE); c.setStrokeColor(LINE)
            c.roundRect(x, top-h, panel_w, h, 5, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont(rb.BOLD, 9.2)
            c.drawCentredString(x+panel_w/2, top-20, f"PRINT {i+1}")
            cx, sole_y = x+panel_w/2, top-203
            c.setStrokeColor(INK); c.setLineWidth(1.4)
            c.ellipse(cx-20, sole_y+72, cx+20, sole_y+126, fill=0, stroke=1)
            c.roundRect(cx-14, sole_y+8, 28, 75, 7, fill=0, stroke=1)
            density = max(1, min(10, int(''.join(v for v in str(item.get('mud',50)) if v.isdigit()) or '50')//10))
            for j in range(density):
                yy = sole_y+14+j*10
                if yy < sole_y+117:
                    c.line(cx-10, yy, cx+10, yy+4)
            c.setFont(rb.FONT, 8.9)
            c.drawCentredString(cx, top-h+46, f"MUD: {item.get('mud')}")
            c.drawCentredString(cx, top-h+29, f"TREAD: {item.get('tread_arrow')}")
        book.y -= h+14
        book.text(str(mission["visual_sequence"].get("rule", "")), 10.2, True)
        return True
    if number == 27:
        overlay = mission["map_overlay"]
        rows, cols = overlay["grid"]["rows"], overlay["grid"]["columns"]
        gap, gw, gh = 18, (TEXT_W-18)/2, 212
        book.ensure(gh+96, 8)
        top = book.y
        for side, label in enumerate(("OLD PLAN", "CURRENT PLAN")):
            x = M+side*(gw+gap)
            c.setFillColor(INK); c.setFont(rb.BOLD, 11); c.drawString(x, top-15, label)
            gy = top-30-gh
            c.setStrokeColor(INK); c.setLineWidth(.75); c.rect(x, gy, gw, gh, fill=0, stroke=1)
            for i in range(1, cols): c.line(x+i*gw/cols, gy, x+i*gw/cols, gy+gh)
            for i in range(1, rows): c.line(x, gy+i*gh/rows, x+gw, gy+i*gh/rows)
            cells = overlay["old_room_cells"] if side == 0 else overlay["current_archive_wall_cells"]
            for cell in cells:
                col, row = ord(cell[0])-65, int(cell[1:])-1
                xx = x+col*gw/cols; yy = gy+gh-(row+1)*gh/rows
                c.setFillColor(PALE if side else WHITE); c.setStrokeColor(INK)
                c.rect(xx+1, yy+1, gw/cols-2, gh/rows-2, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont(rb.BOLD, 8.5)
            for a in overlay["anchors"]:
                cell = a["old_cell"] if side == 0 else a["current_cell"]
                col, row = ord(cell[0])-65, int(cell[1:])-1
                short = {"NORTH STAIR":"STAIR", "COURTYARD COLUMN":"COLUMN", "WEST LIFT SHAFT":"LIFT"}[a["old"]]
                c.drawCentredString(x+(col+.5)*gw/cols, gy+gh-(row+.55)*gh/rows, short)
            for col in range(cols):
                c.drawCentredString(x+(col+.5)*gw/cols, gy+gh+3, chr(65+col))
            for row in range(rows):
                c.drawString(x+2, gy+gh-(row+.55)*gh/rows, str(row+1))
        book.y = top-gh-52
        book.text(overlay["transform"], 10.2, True)
        return True
    return False


def draw_other_evidence(book: Book, number: int, mission: dict, sections: dict) -> None:
    book.begin("puzzle evidence", number, label=f"case {number:02d} / evidence")
    book.heading(f"CASE {number:02d} // EVIDENCE", 18)
    evidence = sections.get("PUZZLE / EVIDENCE SURFACE", "")
    if number == 5:
        evidence += "\n\n### CODE CLUES\n" + sections.get("CODE CLUES", "")
        evidence += "\n\n### CODE SLOTS\n" + sections.get("CODE SLOTS", "")
        if not all(item in evidence for item in ("STAR", "BOLT", "KEY", "MOON", "[ 6 ]")):
            raise ValueError("Case 05 current six-symbol evidence missing")
        book.render_md(evidence, 12)
    else:
        visual_complete = draw_visual_payload(book, number, mission)
        if not visual_complete:
            cards = evidence_cards(mission, number)
            if not cards:
                raise ValueError(f"Case {number:02d}: no source-backed evidence payload")
            for idx, card in enumerate(cards, 1):
                book.card(f"EVIDENCE {idx:02d}", card)
    response = sections.get("YOUR VERDICT / RESPONSE", "")
    if response:
        book.heading("YOUR VERDICT / RESPONSE", 12)
        book.render_md(response, 11)
    for extra in ("DIFFERENCE TRACKER", "CASE WALL -> PAGE 9"):
        if sections.get(extra):
            book.heading(extra, 12)
            book.render_md(sections[extra], 11)
    book.end()


def draw_front(book: Book, front: list[dict]) -> None:
    for item in front:
        number = item["number"]
        book.begin("front matter", label=f"opening {number:02d}")
        if book.page != number:
            raise ValueError(f"front matter physical page drift at {number}")
        if number == 1:
            book.heading("HAPPY MAKERS DETECTIVE ACADEMY", 28)
            book.text("THE MYSTERY OF ROOM ZERO", 21, True)
            book.text("BOOK 1", 15, True)
            book.grid(M+5, 400, TEXT_W-10, 155)
            book.y = 360
            book.render_md(item["markdown"].splitlines()[1:], 13) if False else None
        elif number == 2:
            c=book.canvas; c.setStrokeColor(INK); c.setLineWidth(2)
            c.circle(W/2, 508, 84, fill=0, stroke=1)
            c.setFont(rb.BOLD, 103); c.drawCentredString(W/2, 477, "?")
            book.y = 245
            book.render_md("\n".join(item["markdown"].splitlines()[1:]), 11)
        elif number == 3:
            book.heading("YOUR SQUAD", 21)
            book.image(ROOT/"assets/production/squad-scanner.png", TEXT_W, 350)
            book.render_md("\n".join(item["markdown"].splitlines()[1:]), 12, compact=True)
        elif number == 9:
            book.heading("YOUR CASE WALL + HINT VAULT", 19)
            body = "\n".join(item["markdown"].splitlines()[1:])
            left, right = body.split("### HINT VAULT + SOLUTION FILES", 1)
            col_w = (TEXT_W-19)/2
            def column(markdown: str, x: float, top: float) -> float:
                y = top
                for kind, value in paragraphs(markdown):
                    size = 10.5 if kind == "heading" else 9.1
                    p = Paragraph(inline(("• " if kind == "bullet" else "") + value),
                                  ParagraphStyle("front9", fontName=rb.BOLD if kind == "heading" else rb.FONT,
                                                 fontSize=size, leading=size*1.25))
                    _, h = p.wrap(col_w, H)
                    if y-h < BOTTOM:
                        raise ValueError("physical page 9 Case Wall copy does not fit")
                    p.drawOn(book.canvas, x, y-h)
                    y -= h + (7 if kind == "heading" else 3)
                return y
            left_y = column(left, M, book.y)
            right_y = column("### HINT VAULT + SOLUTION FILES" + right, M+col_w+19, book.y)
            for zone in ("MATCHING MARKS", "MESSAGES / RULES", "CODES / COORDINATES", "FALSE LEADS", "OPEN QUESTIONS"):
                left_y -= 38
                if left_y < BOTTOM:
                    raise ValueError("physical page 9 Evidence Log zones do not fit")
                book.canvas.setStrokeColor(LINE)
                book.canvas.roundRect(M, left_y, col_w, 35, 4, fill=0, stroke=1)
                book.canvas.setFillColor(INK); book.canvas.setFont(rb.BOLD, 8.7)
                book.canvas.drawString(M+8, left_y+23, zone)
            book.y = min(left_y, right_y)
        elif number == 10:
            book.heading("30 ACTIVE FILES", 20)
            entries = re.findall(r"^(\d{2})\s+—\s+(.+?)\s*$", item["markdown"], flags=re.MULTILINE)
            if len(entries) != 30:
                raise ValueError("page 10 Case Index lost a case")
            col_w = (TEXT_W-18)/2
            for col in range(2):
                y = book.y-2
                x = M+col*(col_w+18)
                for number_text, title in entries[col*15:(col+1)*15]:
                    p = Paragraph(inline(title), ParagraphStyle("index", fontName=rb.BOLD,
                                  fontSize=9.4, leading=12.4))
                    _, ph = p.wrap(col_w-35, H)
                    h = max(30, ph+12)
                    book.canvas.setStrokeColor(LINE); book.canvas.setLineWidth(.55)
                    book.canvas.line(x, y-h, x+col_w, y-h)
                    book.canvas.setFillColor(INK); book.canvas.setFont(rb.BOLD, 10)
                    book.canvas.drawString(x+2, y-15, number_text)
                    p.drawOn(book.canvas, x+33, y-6-ph)
                    y -= h+2
                if y < 87:
                    raise ValueError("Case Index column exceeds page 10 safe area")
            book.y = 85
            book.text("No answers here. Just doors.", 10.4, True, gap=3)
            book.text("Turn the page. Case 01 is waiting.", 10.4, True, gap=2)
        else:
            book.render_md(item["markdown"], 17, compact=number >= 4)
        book.end()


def build(pdf_path: Path) -> dict:
    source = build_contract()
    assets = verify_assets()
    old = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
    missions = {int(m["number"]): m for m in old["missions"]}
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    spatial = {int(c["id"].split("_")[1]): c for c in runtime["cases"]}
    if set(spatial) != set(json.loads(MAP_CONTRACT.read_text())["spatial_cases"]):
        raise ValueError("spatial runtime case set differs from locked contract")
    book = Book(pdf_path)
    draw_front(book, source["front_pages"])
    for block in source["main_flow"]:
        if block["kind"] == "section":
            book.begin("story bridge", label=block["title"][:33])
            book.render_md(block["markdown"], 18)
            if block["title"].startswith("ARCHIVE FILE 001"):
                book.image(OWNER_DIR/"book2_archive_photo.png", 250, 340)
            book.end()
        else:
            number = block["number"]
            case = next(v for v in source["main_cases"] if v["number"] == number)
            sections = draw_case_brief(book, case)
            if number in spatial:
                draw_witness_board(book, spatial[number], number)
                draw_map(book, spatial[number], number, response=sections.get("YOUR VERDICT / RESPONSE", ""))
                if sections.get("CASE WALL -> PAGE 9"):
                    book.begin("case wall update", number, label=f"case {number:02d} / case wall")
                    book.render_md("### CASE WALL -> PAGE 9\n"+sections["CASE WALL -> PAGE 9"], 13)
                    book.end()
            elif number == 1:
                draw_case01(book, missions[number], sections)
            elif number == 3:
                draw_case03(book, sections)
            else:
                draw_other_evidence(book, number, missions[number], sections)
    book.begin("stop divider", label="STOP / HINT VAULT")
    book.y = 540
    book.heading("STOP // HINT VAULT", 29)
    book.text("Turn the whole book around to enter the Hint Vault and Solution Files.", 15)
    book.text("Try one hint level at a time. Keep your verdict yours until you choose a solution.", 11)
    book.end()
    for level in ("1", "2", "3"):
        book.begin(f"hint vault level {level}", side="reverse", label=f"hint vault / level {level}")
        book.render_md(f"# HINT VAULT // LEVEL {level}", 20)
        book.render_md(source["hint_intros"][level], 12)
        for case in source["hint_levels"][level]:
            book.render_md(case["markdown"], 12)
        book.end()
    book.begin("solutions entry", side="reverse", label="solution files")
    book.render_md("# SOLUTION FILES", 20)
    book.render_md(source["solutions_intro"], 12)
    book.end()
    for case in source["solution_files"]:
        number = case["number"]
        book.begin("solution", number, "reverse", f"solution / case {number:02d}")
        book.render_md(case["markdown"], 15)
        if number == 3:
            book.image(OWNER_DIR/"case03_solution.png", 370, 460)
        book.end()
        if number in spatial:
            draw_map(book, spatial[number], number, True)
    book.save()
    qa = {
        "status": "RENDERED_REVIEW_REQUIRED" if not book.errors else "BLOCKED",
        "source_blob_sha1": source["authority"]["blob_sha1"],
        "assets": assets,
        "physical_pages": len(book.index),
        "front_pages": 10,
        "main_cases": 30,
        "hint_levels": 3,
        "solutions": 30,
        "errors": book.errors,
        "pdf_sha256": sha(pdf_path),
        "english_frozen": False,
        "kdp_publication_authorized": False,
    }
    prefix = pdf_path.with_suffix("")
    prefix.with_name(prefix.name+"_page_index.json").write_text(json.dumps(book.index, indent=2)+"\n", encoding="utf-8")
    prefix.with_name(prefix.name+"_QA.json").write_text(json.dumps(qa, indent=2)+"\n", encoding="utf-8")
    return qa


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=DEFAULT_PDF)
    args = p.parse_args()
    result = build(args.output)
    print(json.dumps(result, indent=2))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
