#!/usr/bin/env python3
"""Compose the V3 reader text with the exact owner and spatial evidence assets.

This is an interior proof, not an English freeze or publication action. The
source verifier and asset hashes are mandatory. The physical page plan grows
with the copy, and the back matter remains upright for paperback printing.
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
from prepare_v3_print_derivatives import OUTPUT as PRINT_DERIVATIVES, prepare as prepare_print_derivatives
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
WITNESS_COPY = ROOT / "content/v3_witness_board_copy.json"
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


def project_front_markdown(number: int, markdown: str) -> str:
    """Canonical V3 already contains final reader-facing front-matter wording."""
    return markdown

def project_case_markdown(number: int, markdown: str) -> str:
    """Canonical V3 is the sole authority for reader-facing case copy."""
    return markdown

def project_solution_markdown(number: int, markdown: str) -> str:
    """Canonical V3 is the sole authority for solution wording."""
    return markdown

def draw_dark_grid(canvas_obj, x: float, y: float, w: float, h: float,
                   step: float = 16, radius: float = 8, alpha: float = 0.25) -> None:
    """Signature HMDA evidence-grid motif: black field + thin white grid."""
    canvas_obj.setFillColor(INK)
    canvas_obj.setStrokeColor(INK)
    canvas_obj.roundRect(x, y, w, h, radius, fill=1, stroke=0)
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(colors.HexColor("#FFFFFF"))
    canvas_obj.setStrokeAlpha(alpha)
    canvas_obj.setLineWidth(0.85)
    xx = x + step
    while xx < x + w:
        canvas_obj.line(xx, y, xx, y + h)
        xx += step
    yy = y + step
    while yy < y + h:
        canvas_obj.line(x, yy, x + w, yy)
        yy += step
    canvas_obj.restoreState()


def draw_comms_frame(canvas_obj, x: float, y: float, w: float, h: float,
                     radius: float = 8, grid_strip: float = 34) -> None:
    """Readable COMMS panel: white copy field + decorative grid strip only."""
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setStrokeColor(INK)
    canvas_obj.setLineWidth(1.0)
    canvas_obj.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    strip = min(grid_strip, max(24, w * 0.09))
    draw_dark_grid(canvas_obj, x+w-strip, y, strip, h, step=12, radius=radius, alpha=0.20)
    canvas_obj.setFillColor(INK)
    canvas_obj.rect(x, y+h-28, w-strip, 28, fill=1, stroke=0)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont(rb.BOLD, 9.2)
    canvas_obj.drawString(x+14, y+h-19, "HAPPY MAKERS // COMMS")


def draw_scanner_question_mark(canvas_obj, cx: float, cy: float) -> None:
    """Vector scanner-question-mark brand mark; no generic circle badge."""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(INK)
    canvas_obj.setFillColor(INK)
    canvas_obj.setLineWidth(2.2)
    size = 86
    corner = 25
    # Four scanner brackets.
    for sx, sy in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        x = cx + sx * size
        y = cy + sy * size
        canvas_obj.line(x, y, x - sx * corner, y)
        canvas_obj.line(x, y, x, y - sy * corner)
    # Scanner crosshair around the question mark, without a badge circle.
    canvas_obj.setLineWidth(1.0)
    canvas_obj.line(cx - 82, cy, cx - 62, cy)
    canvas_obj.line(cx + 62, cy, cx + 82, cy)
    canvas_obj.line(cx, cy - 82, cx, cy - 62)
    canvas_obj.line(cx, cy + 62, cx, cy + 82)
    canvas_obj.setFont(rb.BOLD, 88)
    canvas_obj.drawCentredString(cx, cy - 31, "?")
    canvas_obj.restoreState()


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
        self.canvas.setTitle("Happy Makers Detective Academy - The Mystery of Room Zero - Book 1")
        self.canvas.setAuthor("Rise.Shine.Evolve")
        self.canvas.setCreator("Rise.Shine.Evolve")
        self.canvas.setSubject("Detective puzzle and logic activity book for ages 8-12")
        self.path = path
        self.page = 0
        self.open = False
        self.y = TOP
        self.current: dict = {}
        self.continuation_label = ""
        self.index: list[dict] = []
        self.errors: list[str] = []

    def begin(self, family: str, case: int | None = None, side: str = "upright", label: str | None = None) -> None:
        if side != "upright":
            raise ValueError("paperback pages must remain physically upright")
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
        self.continuation_label = label or family
        self.index.append(self.current)
        self.y = TOP
        c = self.canvas
        c.setFillColor(WHITE); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(INK); c.rect(M, H-43, TEXT_W, 25, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(rb.BOLD, 9.3)
        c.drawString(M+10, H-34, "DETECTIVE ACADEMY")
        title = plain(label or family).upper()
        c.drawRightString(W-M-10, H-34, f"{title[:37]}  /  {self.page:03d}")
        c.setFillColor(INK); c.setFont(rb.FONT, 9)
        c.drawRightString(W-M, 27, f"{self.page:03d}")

    def grid(self, x: float, y: float, w: float, h: float) -> None:
        c = self.canvas
        c.setStrokeColor(colors.HexColor("#D3D3D3")); c.setLineWidth(.85)
        for xx in range(int(x), int(x+w)+1, 9):
            c.line(xx, y, xx, y+h)
        for yy in range(int(y), int(y+h)+1, 9):
            c.line(x, yy, x+w, yy)

    def end(self) -> None:
        if not self.open:
            return
        self.canvas.showPage()
        self.open = False

    def ensure(self, height: float, gap: float = 8) -> None:
        if self.y - height - gap < BOTTOM:
            meta = self.current.copy()
            self.begin(meta["family"] + " continuation", meta["case"], meta["side"],
                       label=self.continuation_label)

    def rule(self) -> None:
        self.ensure(8)
        self.canvas.setStrokeColor(LINE); self.canvas.setLineWidth(.85)
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
        c.setLineWidth(1.35 if kind == "objective" else .85)
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
        evidence = list(data.get("evidence", []))
        if number == 16:
            revealing = "The 2008 candidate is therefore too late, and 1998 is too early"
            if len(evidence) != 5 or not evidence[-1].startswith(revealing):
                raise ValueError("Case 16 year evidence source drift")
            evidence.pop()
        cards += evidence
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
            elif stage.get("id") == "DETECTIVE":
                prompt = "Enter the OFFICIAL CALL SIGN from your Recruit Credential."
            cards.append(f"{stage.get('id')}: {prompt}")
    return [str(v) for v in cards if str(v).strip()]


def draw_case_brief(book: Book, case: dict) -> dict[str, str]:
    number = case["number"]
    opening, sections = split_case(project_case_markdown(number, case["markdown"]))
    book.begin("case brief", number, label=f"case {number:02d} / case file")
    # Signature evidence-grid band belongs to every new case without becoming a worksheet.
    banner_h = 30
    draw_dark_grid(book.canvas, M, book.y-banner_h, TEXT_W, banner_h, step=12, radius=5)
    book.canvas.setFillColor(WHITE); book.canvas.setFont(rb.BOLD, 9.5)
    book.canvas.drawString(M+12, book.y-19,
        f"CASE {number:02d}  //  {(case.get('rank') or 'DETECTIVE').upper()}  //  {(case.get('status') or 'ACTIVE').upper()}")
    book.y -= banner_h + 10
    book.heading(case["title"], 19)
    for name in ("CASE FILE // WHAT HAPPENED", "YOUR OBJECTIVE", "INVESTIGATION RULES", "HAPPY MAKERS CHAT"):
        content = sections.get(name, "")
        if not content:
            raise ValueError(f"Case {number:02d}: missing {name}")
        if name == "HAPPY MAKERS CHAT":
            beats = [line for kind, line in paragraphs(content) if kind == "bullet"]
            rendered = []
            featured = number == 6
            beat_gap = 9 if featured else 7
            style = ParagraphStyle(
                "chat_transcript", fontName=rb.FONT,
                fontSize=11.2 if featured else 10.0,
                leading=15.4 if featured else 13.2,
                textColor=INK)
            for line in beats:
                speaker, speech = line.split(":", 1) if ":" in line else ("CHAT", line)
                if speaker.startswith("**") and speech.startswith("**"):
                    speech = speech[2:].lstrip()
                who = plain(speaker).upper()
                markup = f"<b>{html.escape(who)}</b>  {inline(speech.strip())}"
                p = Paragraph(markup, style)
                _, ph = p.wrap(TEXT_W-32-42, H)
                rendered.append((p, ph))
            panel_h = 37 + sum(ph + beat_gap for _, ph in rendered) + 8
            if featured:
                book.begin("comms transcript", number, label="case 06 / live comms")
                book.heading("HERITAGE GALLERY // LIVE COMMS", 18)
                book.y = (book.y + BOTTOM + panel_h) / 2
            elif book.y - panel_h - 9 < BOTTOM:
                book.begin("comms transcript", number, label=f"case {number:02d} / comms")
            book.ensure(panel_h, 9)
            x, top = M, book.y
            draw_comms_frame(book.canvas, x, top-panel_h, TEXT_W, panel_h, radius=8, grid_strip=34)
            yy = top-39
            for p, ph in rendered:
                p.drawOn(book.canvas, x+16, yy-ph)
                yy -= ph + beat_gap
            book.y -= panel_h + 8
        elif name == "YOUR OBJECTIVE":
            book.card(name, content, "objective")
        else:
            panel_page, panel_top = book.page, book.y + 4
            book.heading(name, 12)
            book.render_md(content, 12)
            if book.page == panel_page:
                book.canvas.setStrokeColor(LINE)
                book.canvas.setLineWidth(.85)
                book.canvas.roundRect(M-7, book.y+2, TEXT_W+14,
                                      panel_top-book.y-2, 6, fill=0, stroke=1)
    # These three physical records are already named in the Room Zero trail.
    # Print their unobtrusive marks before the Case 09 comparison.
    marked_records = {
        2: "TROPHY HALL TAG",
        4: "OPEN NIGHT EVIDENCE LABEL",
        5: "OLD LOCKER ENVELOPE",
    }
    if number in marked_records:
        book.ensure(42, 5)
        c = book.canvas
        top = book.y
        c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(.85)
        c.roundRect(M, top-42, TEXT_W, 42, 5, fill=1, stroke=1)
        c.setFillColor(INK); c.setFont(rb.BOLD, 9.5)
        c.drawString(M+12, top-25, marked_records[number])
        c.setFont(rb.BOLD, 22)
        c.drawRightString(W-M-14, top-29, "0")
        book.y -= 47
    book.end()
    return sections


def parity_prep(book: Book, number: int, title: str, spread_label: str) -> None:
    """Preserve Witness Board LEFT / Map RIGHT without adding fake worksheet tasks."""
    if (book.page + 1) % 2 == 1:
        book.begin("evidence grid interstitial", number, label=f"case {number:02d} / evidence grid")
        x = M
        h = 410
        y = book.y-h
        draw_dark_grid(book.canvas, x, y, TEXT_W, h, step=18, radius=9)
        book.canvas.setFillColor(WHITE)
        book.canvas.setFont(rb.BOLD, 36)
        book.canvas.drawString(x+24, y+h-61, f"{number:02d}")
        title_style = ParagraphStyle("interstitial_title", fontName=rb.BOLD,
                                     fontSize=17, leading=21, textColor=WHITE)
        title_text = Paragraph(inline(title.upper()), title_style)
        _, title_h = title_text.wrap(TEXT_W-48, H)
        title_text.drawOn(book.canvas, x+24, y+h-90-title_h)
        book.canvas.setFont(rb.BOLD, 12.5)
        book.canvas.drawString(x+24, y+h-119-title_h, spread_label)
        book.y = y-12
        book.end()


def draw_witness_board(book: Book, case: dict, number: int, title: str) -> None:
    parity_prep(book, number, title, "WITNESS BOARD  ->  LIVE CASE MAP")
    book.begin("witness board", number, label=f"case {number:02d} / witness board")
    if book.page % 2:
        raise ValueError("Witness Board must be on physical left/even page")
    book.heading(f"CASE {number:02d} // WITNESS BOARD", 20)
    book.text("Place every witness once. Tick each statement as you use it. Keep the completed map for later evidence.")
    col_w = (TEXT_W-12)/2
    people = case["characters"]

    copy_contract = json.loads(WITNESS_COPY.read_text(encoding="utf-8"))
    locked = copy_contract["cases"].get(f"{number:02d}")
    if locked is None or len(locked) != len(people):
        raise ValueError(f"Case {number:02d}: missing or incomplete V3 Witness Board copy lock")
    for idx, (person, row_copy) in enumerate(zip(people, locked), 1):
        display_name, clue = row_copy
        if str(person["display_name"]).casefold() != str(display_name).casefold():
            raise ValueError(
                f"Case {number:02d}: Witness Board display-name drift at {idx}: "
                f"{person['display_name']} != {display_name}"
            )
        forbidden = tuple(v.casefold() for v in copy_contract.get("forbidden_reader_words", []))
        if any(word in clue.casefold() for word in forbidden):
            raise ValueError(f"Case {number:02d}: forbidden raw-source crime wording in Witness Board")
        person["presentation_clue"] = clue

    for start in range(0, len(people), 2):
        row = people[start:start+2]
        rendered = []
        for person in row:
            p = Paragraph(inline(person["presentation_clue"]), ParagraphStyle(
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
    book.begin(family, number, label=f"case {number:02d} / {family}")
    if not solution and book.page % 2 != 1:
        raise ValueError("live map must immediately follow Witness Board on right/odd page")
    book.heading(f"CASE {number:02d} // {family.upper()}", 17)
    filename = f"HMDA_{number:02d}_{'solution' if solution else 'puzzle'}.png"
    c = book.canvas
    img = map_crop(MAP_DIR / filename)
    rows, cols = int(case["grid"]["rows"]), int(case["grid"]["columns"])
    image_size = 489
    x = (W-image_size)/2 + 7
    top = book.y - 20
    y = top-image_size
    if y < 162:
        raise ValueError(f"Case {number:02d}: map does not fit the page (bottom={y:.1f} pt)")
    c.drawImage(img, x, y, image_size, image_size)
    c.setFillColor(INK); c.setFont(rb.BOLD, 17 if cols <= 7 else 14)
    for col in range(cols):
        c.drawCentredString(x+(col+.5)*image_size/cols, top+5, chr(65+col))
    for row in range(rows):
        c.drawRightString(x-7, top-(row+.5)*image_size/rows-4, str(row+1))
    book.y = y-8
    if solution:
        answer = case["source_answer"]
        book.text(f"VERIFIED VERDICT: {answer['display_name']} at {answer['coordinate']}", 11.5, True, gap=4)
    else:
        book.text("MAP KEY  /  □ usable floor; ■ blocked object; heavy line = wall; gap = doorway", 9.7, True, gap=7)
        book.card("YOUR VERDICT / RESPONSE", response or "PERSON / WITNESS: ____________________    COORDINATE: ______")
    book.end()


def draw_case01(book: Book, mission: dict, sections: dict) -> None:
    book.begin("intake evidence", 1, label="case 01 / intake board")
    book.heading("CASE 01 // THE INTAKE GRID", 18)
    book.text("HELPER ROSTER // QUILL / PIP / MORSE / KNOX", 10.4, True, gap=7)
    tut = mission["tutorial"]
    grid_size = 282
    grid_y = book.y-grid_size-20
    rb.draw_tutorial_grid(book.canvas, tut, (W-grid_size)/2, grid_y,
                          grid_size, grid_size, False, stroke_width=.85)
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
    book.ensure(34, 5)
    top = book.y
    c = book.canvas
    c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(.85)
    c.roundRect(M, top-34, TEXT_W, 34, 5, fill=1, stroke=1)
    c.setFillColor(INK); c.setFont(rb.BOLD, 9.3)
    c.drawString(M+12, top-21, "RECRUIT BADGE RECORD")
    c.setFont(rb.BOLD, 18)
    c.drawRightString(W-M-14, top-24, "0")
    book.y -= 39
    book.render_md(sections.get("YOUR VERDICT / RESPONSE", ""), 11)
    book.end()


def draw_case03(book: Book, sections: dict, title: str) -> None:
    parity_prep(book, 3, title, "PHOTO A  ->  PHOTO B")
    for letter in ("A", "B"):
        book.begin(f"photo {letter}", 3, label=f"case 03 / photo {letter}")
        if (book.page % 2 == 0) != (letter == "A"):
            raise ValueError("Case 03 photographs are not facing left/right pages")
        book.heading(f"CASE 03 // PHOTO {letter}", 18)
        book.image(PRINT_DERIVATIVES / f"case03_photo_{letter}_print.png", 450, 500, gap=5)
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


def draw_case09_marks(book: Book) -> None:
    """Show the seven record samples without printing their classification."""
    records = (
        ("RECRUIT BADGE RECORD", "zero"),
        ("TROPHY HALL TAG", "zero"),
        ("OPEN NIGHT EVIDENCE LABEL", "zero"),
        ("OLD LOCKER ENVELOPE", "zero"),
        ("LOOK-TWICE ROUTING FILE", "blank"),
        ("POSTER DECORATION", "stripe"),
        ("STAGE-LIGHT DIAL", "pointer"),
    )
    c = book.canvas
    col_w = (TEXT_W-12)/2
    for start in range(0, len(records), 2):
        row = records[start:start+2]
        h = 84
        book.ensure(h, 9)
        for col, (label, mark) in enumerate(row):
            x, top = M+col*(col_w+12), book.y
            c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(.85)
            c.roundRect(x, top-h, col_w, h, 6, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont(rb.BOLD, 9)
            c.drawString(x+12, top-19, label)
            cx, cy = x+col_w-33, top-49
            c.setStrokeColor(INK); c.setLineWidth(1.2)
            c.roundRect(cx-20, cy-20, 40, 40, 3, fill=0, stroke=1)
            if mark == "zero":
                c.setFont(rb.BOLD, 27)
                c.drawCentredString(cx, cy-9, "0")
            elif mark == "stripe":
                c.circle(cx, cy, 13, fill=0, stroke=1)
                c.saveState()
                clip = c.beginPath(); clip.circle(cx, cy, 12)
                c.clipPath(clip, stroke=0, fill=0)
                for yy in range(-12, 15, 6):
                    c.line(cx-13, cy+yy, cx+13, cy+yy)
                c.restoreState()
            elif mark == "pointer":
                c.circle(cx, cy, 13, fill=0, stroke=1)
                c.line(cx, cy, cx+8, cy+8)
                c.circle(cx, cy, 2.2, fill=1, stroke=0)
        book.y -= h+9


def draw_case26_boxes(book: Book, mission: dict) -> None:
    expected = [2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25]
    numbers = mission["checkpoint"]["case_numbers"]
    if numbers != expected:
        raise ValueError("Case 26 extraction order drift")
    book.heading("EMPTY-ROOM INITIALS // CASE ORDER", 12)
    cell_w = TEXT_W/7
    row_h = 58
    book.ensure(row_h*2+8, 10)
    c = book.canvas
    for idx, number in enumerate(numbers):
        col, row = idx % 7, idx // 7
        x = M+col*cell_w
        top = book.y-row*row_h
        c.setFillColor(INK); c.setFont(rb.BOLD, 9)
        c.drawCentredString(x+cell_w/2, top-12, f"{number:02d}")
        c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1)
        c.rect(x+cell_w/2-20, top-49, 40, 31, fill=1, stroke=1)
    book.y -= row_h*2+8


def draw_case28_sort(book: Book, mission: dict) -> None:
    cards = mission["fact_theory_sort"]["cards"]
    if len(cards) != 6:
        raise ValueError("Case 28 claim-card count drift")
    c = book.canvas
    col_w = (TEXT_W-12)/2
    card_h, card_step = 60, 65
    for start in range(0, 6, 2):
        book.ensure(card_h, 5)
        for col, item in enumerate(cards[start:start+2]):
            x, top = M+col*(col_w+12), book.y
            c.setFillColor(WHITE); c.setStrokeColor(LINE); c.setLineWidth(.85)
            c.roundRect(x, top-card_h, col_w, card_h, 5, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont(rb.BOLD, 9.4)
            c.drawString(x+11, top-17, f"CLAIM {chr(65+start+col)}")
            p = Paragraph(inline(item["text"]), ParagraphStyle(
                "claim", fontName=rb.FONT, fontSize=10.2, leading=13))
            _, ph = p.wrap(col_w-22, H)
            p.drawOn(c, x+11, top-24-ph)
        book.y -= card_step
    book.heading("DAMAGED RULE CARD", 12)
    book.card("RULE ZERO", "**ZERO ____________. NOTICE FIRST. THEORIZE SECOND.**", "objective")
    book.heading("SORT THE CLAIMS", 12)
    zone_labels = ("FACT", "THEORY", "UNSUPPORTED ASSUMPTION")
    gap = 9
    zone_w = (TEXT_W-2*gap)/3
    h = 96
    book.ensure(h, 7)
    for i, label in enumerate(zone_labels):
        x, top = M+i*(zone_w+gap), book.y
        c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(.85)
        c.roundRect(x, top-h, zone_w, h, 5, fill=1, stroke=1)
        p = Paragraph(label, ParagraphStyle("zone", fontName=rb.BOLD,
                          fontSize=9.5, leading=11, textColor=INK))
        _, ph = p.wrap(zone_w-16, H)
        p.drawOn(c, x+8, top-11-ph)
        for line in range(3):
            y = top-38-line*22
            c.line(x+11, y, x+zone_w-11, y)
    book.y -= h+7


def draw_case30_response(book: Book) -> None:
    book.heading("YOUR VERDICT / RESPONSE", 12)
    for label in ("RULE", "ROOM"):
        book.text(f"{label}: __________________________________________", 10.8, True, gap=7)
    book.ensure(51, 6)
    c = book.canvas
    c.setFillColor(INK); c.setFont(rb.BOLD, 10.8)
    c.drawString(M, book.y-17, "CODE:")
    for i in range(6):
        x = M+70+i*73
        c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1)
        c.rect(x, book.y-39, 55, 30, fill=1, stroke=1)
    book.y -= 50
    book.text("DETECTIVE: OFFICIAL CALL SIGN __________________________", 10.8, True, gap=5)


def draw_visual_payload(book: Book, number: int, mission: dict) -> bool:
    """Draw the nonspatial evidence as an inspectable physical surface."""
    c = book.canvas
    if number == 9:
        draw_case09_marks(book)
        return True
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
                c.setFillColor(INK); c.setFont(rb.BOLD, 9.0)
                c.drawCentredString(bx+(cw-7)/2, by+9, name)
            path = " → ".join(option.get("path", []))
            book.y = top-h+24
            book.text(f"PATH: {path}", 8.9, True, width=TEXT_W-24, x=x+12, gap=0, keep=False)
            book.y = top-h-9
        book.text("SITE CONDITIONS: Paint Corridor closes at 16:30. Staff Stairs are locked.", 10.2, True)
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
                label = str(item.get('label','')).replace("DO NOT CATALOGUE", "DO NOT CATALOG")
                p = Paragraph(inline(str(item.get('item',''))) + "<br/>" + inline(label),
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
            if i in (0, 3):
                c.setFont(rb.BOLD, 8.7)
                c.drawCentredString(x+panel_w/2, top-37,
                                    "EAST PATH" if i == 0 else "WEST GATE")
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
            c.setStrokeColor(INK); c.setLineWidth(.85); c.rect(x, gy, gw, gh, fill=0, stroke=1)
            for i in range(1, cols): c.line(x+i*gw/cols, gy, x+i*gw/cols, gy+gh)
            for i in range(1, rows): c.line(x, gy+i*gh/rows, x+gw, gy+i*gh/rows)
            cells = overlay["old_room_cells"] if side == 0 else overlay["current_archive_wall_cells"]
            if set(cells) != {"D2", "E2", "D3", "E3"}:
                raise ValueError("Case 27 locked old/current footprint drift")
            rx = x+3*gw/cols
            ry = gy+gh-3*gh/rows
            rw, rh = 2*gw/cols, 2*gh/rows
            if side == 0:
                c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1.6)
                c.rect(rx, ry, rw, rh, fill=1, stroke=1)
                room_label = "TRAINING ROOM"
                c.setFillColor(INK)
            else:
                c.setFillColor(colors.HexColor("#555555")); c.setStrokeColor(INK)
                c.setLineWidth(1.6)
                c.rect(rx, ry, rw, rh, fill=1, stroke=1)
                room_label = "ARCHIVE WALL"
                c.setFillColor(WHITE)
            c.setFont(rb.BOLD, 8.0)
            c.drawCentredString(rx+rw/2, ry+rh/2-3, room_label)
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
        book.text("ANCHORS // NORTH STAIR (C1) / COURTYARD COLUMN (F3) / WEST LIFT SHAFT (A5)", 8.8, True, gap=4)
        book.text("OLD-PLAN MARGIN NOTE // RULE FIRST, ROOM SECOND.", 9.4, True, gap=4)
        book.text(overlay["transform"], 10.2, True)
        return True
    if number == 28:
        draw_case28_sort(book, mission)
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
    if number == 26:
        draw_case26_boxes(book, mission)
    response = sections.get("YOUR VERDICT / RESPONSE", "")
    if response:
        if number == 30:
            draw_case30_response(book)
        else:
            book.heading("YOUR VERDICT / RESPONSE", 12)
            book.render_md(response, 11)
    for extra in ("DIFFERENCE TRACKER", "CASE WALL -> PAGE 9"):
        if sections.get(extra):
            book.heading(extra, 12)
            if number == 28 and extra == "CASE WALL -> PAGE 9":
                blocks = paragraphs(sections[extra])
                if len(blocks) != 3 or any(kind != "body" for kind, _ in blocks):
                    raise ValueError("Case 28 canonical Case Wall handoff drift")
                book.text(" ".join(value for _, value in blocks), size=9.35, gap=4)
            else:
                book.render_md(sections[extra], 11)
    book.end()


def draw_front_comms(book: Book, beats: list[str], x: float, top: float,
                     width: float, font_size: float, leading: float,
                     beat_gap: float) -> float:
    """Front-matter dialogue stays readable; evidence grid is decoration only."""
    copy_w = width - 28 - 38
    style = ParagraphStyle("front_comms", fontName=rb.FONT, fontSize=font_size,
                           leading=leading, textColor=INK)
    rendered = []
    for beat in beats:
        speaker, speech = beat.split(":", 1)
        if speaker.startswith("**") and speech.startswith("**"):
            speech = speech[2:].lstrip()
        markup = f"<b>{html.escape(plain(speaker).upper())}:</b>&nbsp;{inline(speech.strip())}"
        paragraph = Paragraph(markup, style)
        _, height = paragraph.wrap(copy_w, H)
        rendered.append((paragraph, height))
    panel_h = 36 + sum(height + beat_gap for _, height in rendered)
    if top-panel_h < BOTTOM:
        raise ValueError("front-matter COMMS panel does not fit")
    draw_comms_frame(book.canvas, x, top-panel_h, width, panel_h, radius=7, grid_strip=32)
    y = top-37
    for paragraph, height in rendered:
        paragraph.drawOn(book.canvas, x+14, y-height)
        y -= height + beat_gap
    return top-panel_h


def draw_opening_title(book: Book) -> None:
    """Modern detective title page inspired by the owner-approved dossier/evidence-board direction."""
    c = book.canvas
    # dossier frame
    c.setStrokeColor(INK); c.setLineWidth(1.6)
    c.rect(30, 36, W-60, H-70, fill=0, stroke=1)
    for x, y, sx, sy in ((42,H-50,1,-1),(W-42,H-50,-1,-1),(42,50,1,1),(W-42,50,-1,1)):
        c.setLineWidth(2.3)
        c.line(x, y, x+sx*26, y)
        c.line(x, y, x, y+sy*26)

    # scanner/question-mark accents
    draw_scanner_question_mark(c, 92, 695)
    c.setFont(rb.BOLD, 8.2); c.setFillColor(INK)
    c.drawRightString(W-46, 731, "OPENING 01 / 001")

    # title hierarchy
    c.setFont(rb.BOLD, 30)
    c.drawCentredString(W/2, 646, "HAPPY MAKERS")
    c.setFont(rb.BOLD, 49)
    c.drawCentredString(W/2, 596, "DETECTIVE")
    c.drawCentredString(W/2, 548, "ACADEMY")
    c.setFont(rb.BOLD, 15)
    c.drawCentredString(W/2, 511, "THE MYSTERY OF ROOM ZERO")
    c.setFillColor(INK); c.roundRect(W/2-74, 475, 148, 26, 4, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(rb.BOLD, 12)
    c.drawCentredString(W/2, 483, "BOOK 1")

    # evidence board
    board_x, board_y, board_w, board_h = 48, 220, W-96, 224
    c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.roundRect(board_x, board_y, board_w, board_h, 8, fill=1, stroke=1)
    c.setFillColor(INK); c.rect(board_x, board_y+board_h-30, board_w, 30, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont(rb.BOLD, 10)
    c.drawString(board_x+16, board_y+board_h-20, "EVIDENCE GRID // ROOM ZERO FILE")
    # faint grid only behind evidence thumbnails, never behind body text
    c.saveState()
    c.setStrokeColor(colors.HexColor("#D7D7D7")); c.setLineWidth(.6)
    for xx in range(int(board_x+12), int(board_x+board_w-8), 18):
        c.line(xx, board_y+10, xx, board_y+board_h-32)
    for yy in range(int(board_y+12), int(board_y+board_h-32), 18):
        c.line(board_x+8, yy, board_x+board_w-8, yy)
    c.restoreState()

    cards = [
        (board_x+27, board_y+116, 108, 70, "KEY"),
        (board_x+182, board_y+82, 116, 96, "ROOM 0"),
        (board_x+348, board_y+125, 112, 66, "CAMERA"),
        (board_x+67, board_y+25, 113, 72, "PRINT"),
        (board_x+326, board_y+24, 134, 78, "MAP"),
    ]
    centers = []
    for x, y, cw, ch, label in cards:
        c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1.1)
        c.rect(x, y, cw, ch, fill=1, stroke=1)
        c.setFillColor(INK); c.setFont(rb.BOLD, 10)
        c.drawCentredString(x+cw/2, y+ch/2-3, label)
        centers.append((x+cw/2, y+ch/2))
    c.setStrokeColor(INK); c.setLineWidth(1.0)
    for a, b in ((0,1),(1,2),(1,4),(3,1)):
        c.line(centers[a][0], centers[a][1], centers[b][0], centers[b][1])

    # modern tools strip
    c.setStrokeColor(INK); c.setFillColor(WHITE); c.setLineWidth(1.1)
    c.roundRect(49, 86, 155, 92, 7, fill=1, stroke=1)
    c.setFont(rb.BOLD, 10); c.setFillColor(INK)
    c.drawString(63, 153, "SCAN // ANALYZE")
    c.drawString(63, 136, "CONNECT // SOLVE")
    for i in range(4):
        c.rect(64+i*21, 106, 14, 12, fill=0, stroke=1)
    # binoculars
    for cx in (286, 333):
        c.circle(cx, 126, 31, fill=0, stroke=1)
        c.circle(cx, 126, 17, fill=0, stroke=1)
    c.line(303, 143, 316, 143); c.line(303, 109, 316, 109)
    # notebook + pen
    c.roundRect(387, 92, 132, 76, 5, fill=0, stroke=1)
    c.setFont(rb.BOLD, 9); c.drawCentredString(453, 126, "ROOM ZERO")
    c.line(530, 92, 554, 158)
    book.y = 70


def draw_publication_page(book: Book, markdown: str) -> None:
    c = book.canvas
    draw_scanner_question_mark(c, W/2, 625)
    c.setFillColor(INK); c.setFont(rb.BOLD, 10)
    c.drawCentredString(W/2, 524, "PUBLICATION RECORD // FILE 00")

    box_x, box_y, box_w, box_h = 74, 176, W-148, 326
    c.setFillColor(WHITE); c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.roundRect(box_x, box_y, box_w, box_h, 9, fill=1, stroke=1)
    # small decorative grid strip outside the text column
    draw_dark_grid(c, box_x+box_w-34, box_y, 34, box_h, step=12, radius=8, alpha=0.18)

    blocks = [value for kind, value in paragraphs(markdown) if kind != "heading"]
    y = box_y + box_h - 34
    for idx, value in enumerate(blocks):
        bold = idx in (0, 1) or value.startswith("Come visit us") or value.startswith("Follow us")
        size = 9.4 if idx >= 2 else 10.2
        style = ParagraphStyle("pub", fontName=rb.BOLD if bold else rb.FONT,
                               fontSize=size, leading=size*1.34, alignment=1, textColor=INK)
        p = Paragraph(inline(value), style)
        _, ph = p.wrap(box_w-74, H)
        if y-ph < box_y+20:
            raise ValueError("publication record does not fit owner page")
        p.drawOn(c, box_x+20, y-ph)
        y -= ph + (10 if idx < 2 else 9)
    c.setFillColor(INK); c.setFont(rb.BOLD, 8)
    c.drawCentredString(W/2, 142, "RISE.SHINE.EVOLVE. // DETECTIVE ACADEMY")
    book.y = 130


def draw_black_envelope_page(book: Book, markdown: str) -> None:
    """Cold open is a standalone reader beat: no squad art, no squad heading."""
    if "YOUR SQUAD" in markdown:
        raise ValueError("cold-open source contaminated by squad content")
    c = book.canvas
    blocks = [(kind, value) for kind, value in paragraphs(markdown) if kind != "heading"]
    copy = [value for _, value in blocks]
    if not copy or "WILL YOU CLAIM IT?" not in plain(copy[-1]).upper():
        raise ValueError("black-envelope page lost final invitation")

    # top narrative
    y = 644
    for value in copy[:-3]:
        style = ParagraphStyle("cold", fontName=rb.BOLD if value.startswith("No ") else rb.FONT,
                               fontSize=12.0, leading=16.2, alignment=1, textColor=INK)
        p = Paragraph(inline(value), style)
        _, ph = p.wrap(TEXT_W-90, H)
        p.drawOn(c, M+45, y-ph)
        y -= ph + 5

    # graphic black envelope
    ex, ey, ew, eh = 151, 246, W-302, 142
    c.setFillColor(INK); c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.roundRect(ex, ey, ew, eh, 8, fill=1, stroke=1)
    c.setStrokeColor(WHITE); c.setLineWidth(1.0)
    c.line(ex+8, ey+eh-8, ex+ew/2, ey+58)
    c.line(ex+ew-8, ey+eh-8, ex+ew/2, ey+58)
    c.setFillColor(WHITE); c.circle(ex+ew/2, ey+58, 20, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont(rb.BOLD, 25)
    c.drawCentredString(ex+ew/2, ey+49, "0")

    # final invitation
    final_values = copy[-3:]
    fy = 208
    for i, value in enumerate(final_values):
        text = plain(value)
        if "WILL YOU CLAIM IT?" in text.upper():
            c.setFillColor(INK); c.roundRect(106, 105, W-212, 48, 7, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont(rb.BOLD, 18)
            c.drawCentredString(W/2, 122, "WILL YOU CLAIM IT?")
        else:
            style = ParagraphStyle("invite", fontName=rb.BOLD, fontSize=15.5,
                                   leading=18, alignment=1, textColor=INK)
            p = Paragraph(inline(value), style)
            _, ph = p.wrap(TEXT_W-70, H)
            p.drawOn(c, M+35, fy-ph)
            fy -= ph + 4
    book.y = 86


def draw_squad_page(book: Book, markdown: str) -> None:
    """Owner-locked Page 4: squad image + compact team intro + general opening COMMS."""
    body, chat = markdown.split("### HAPPY MAKERS CHAT", 1)
    beats = [value for kind, value in paragraphs(chat) if kind == "bullet"]
    if len(beats) != 6:
        raise ValueError("squad-page canonical COMMS dialogue drift")

    book.heading("YOUR SQUAD", 20)
    c = book.canvas

    # Approved squad image on the left, team/welcome copy on the right.
    image_path = PRINT_DERIVATIVES / "squad_scanner_print.png"
    with Image.open(image_path) as im:
        iw, ih = im.size
        rgba = im.convert("RGBA")
        paper = Image.new("RGBA", rgba.size, (255,255,255,255))
        paper.alpha_composite(rgba)
        grayscale = paper.convert("RGB").convert("L")
    image_w = 202
    image_h = image_w * ih / iw
    image_top = book.y
    image_bottom = image_top - image_h
    c.drawImage(ImageReader(grayscale), M, image_bottom, image_w, image_h,
                preserveAspectRatio=True)

    right_x = M + 225
    right_w = W - M - right_x
    right_y = image_top
    blocks = [(kind, value) for kind, value in paragraphs(body)
              if plain(value).upper() != "YOUR SQUAD"]
    for kind, value in blocks:
        if kind == "heading":
            size, gap = 10.3, 5
            font = rb.BOLD
        else:
            size, gap = 7.55, 3
            font = rb.FONT
        paragraph = Paragraph(inline(value), ParagraphStyle(
            "squad_copy", fontName=font, fontSize=size,
            leading=size*1.22, textColor=INK))
        _, height = paragraph.wrap(right_w, H)
        if right_y-height < BOTTOM+190:
            raise ValueError("Page 4 squad copy does not fit above COMMS")
        paragraph.drawOn(c, right_x, right_y-height)
        right_y -= height + gap

    book.y = min(image_bottom, right_y) - 12
    book.y = draw_front_comms(book, beats, M, book.y, TEXT_W,
                              font_size=8.55, leading=10.5, beat_gap=2) - 2



def draw_front(book: Book, front: list[dict]) -> None:
    for item in front:
        number = item["number"]
        book.begin("front matter", label=f"opening {number:02d}")
        if book.page != number:
            raise ValueError(f"front matter physical page drift at {number}")
        if number == 1:
            draw_opening_title(book)
        elif number == 2:
            draw_publication_page(book, item["markdown"])
        elif number == 3:
            draw_black_envelope_page(book, item["markdown"])
        elif number == 4:
            draw_squad_page(book, item["markdown"])
        elif number == 9:
            book.heading("YOUR CASE WALL + HINT VAULT", 19)
            body = "\n".join(project_front_markdown(number, item["markdown"]).splitlines()[1:])
            left, right = body.split("### HINT VAULT + SOLUTION FILES", 1)
            col_w = (TEXT_W-19)/2
            copy_left_w = 220
            copy_right_w = TEXT_W-copy_left_w-19
            def column(markdown: str, x: float, top: float, width: float) -> float:
                y = top
                blocks = paragraphs(markdown)
                position = 0
                while position < len(blocks):
                    kind, value = blocks[position]
                    if kind == "heading" and plain(value) == "HAPPY MAKERS CHAT":
                        beats = []
                        position += 1
                        while position < len(blocks) and blocks[position][0] == "bullet":
                            beats.append(blocks[position][1])
                            position += 1
                        if len(beats) != 5:
                            raise ValueError("page 9 canonical COMMS dialogue drift")
                        y = draw_front_comms(book, beats, x, y-2, width,
                                             font_size=8.4, leading=10.5, beat_gap=2) - 4
                        continue
                    if kind == "body" and value == (
                        "**MATCHING MARKS** **MESSAGES / RULES** "
                        "**CODES / COORDINATES** **OPEN QUESTIONS**"
                    ):
                        value = ("**MATCHING MARKS** / **MESSAGES / RULES** / "
                                 "**CODES / COORDINATES** / **OPEN QUESTIONS**")
                    size = 10.5 if kind == "heading" else 9.1
                    p = Paragraph(inline(("• " if kind == "bullet" else "") + value),
                                  ParagraphStyle("front9", fontName=rb.BOLD if kind == "heading" else rb.FONT,
                                                 fontSize=size, leading=size*1.25))
                    _, h = p.wrap(width, H)
                    if y-h < BOTTOM:
                        raise ValueError("physical page 9 Case Wall copy does not fit")
                    p.drawOn(book.canvas, x, y-h)
                    y -= h + (7 if kind == "heading" else 3)
                    position += 1
                return y
            left_y = column(left, M, book.y, copy_left_w)
            right_y = column("### HINT VAULT + SOLUTION FILES" + right,
                             M+copy_left_w+19, book.y, copy_right_w)
            top = min(left_y, right_y)-10
            if top-308 < BOTTOM+4:
                raise ValueError(f"physical page 9 writable Case Wall does not fit (top={top:.1f})")
            cc = book.canvas
            right_x = M+col_w+19

            def zone(x: float, zone_top: float, height: float, title: str,
                     line_offsets: tuple[int, ...]) -> None:
                cc.setFillColor(WHITE); cc.setStrokeColor(LINE); cc.setLineWidth(.85)
                cc.roundRect(x, zone_top-height, col_w, height, 5, fill=1, stroke=1)
                cc.setFillColor(INK); cc.setFont(rb.BOLD, 9.1)
                cc.drawString(x+10, zone_top-18, title)
                for offset in line_offsets:
                    cc.setStrokeColor(LINE); cc.setLineWidth(.85)
                    cc.line(x+12, zone_top-offset, x+col_w-12, zone_top-offset)

            zone(M, top, 150, "MATCHING MARKS", (52, 77, 102, 127))
            cc.setFillColor(INK); cc.setFont(rb.BOLD, 8)
            cc.drawString(M+col_w-78, top-20, "MARK")
            cc.setFillColor(WHITE); cc.setStrokeColor(INK); cc.setLineWidth(.85)
            cc.rect(M+col_w-43, top-60, 29, 29, fill=1, stroke=1)

            zone(right_x, top, 178, "MESSAGES / RULES", (52, 77, 102, 127, 152))

            codes_top = top-160
            zone(M, codes_top, 120, "CODES / COORDINATES", ())
            cc.setFillColor(INK); cc.setFont(rb.BOLD, 8.4)
            cc.drawString(M+10, codes_top-39, "CASE 05 CODE")
            for slot in range(6):
                x = M+10+slot*37
                cc.setFillColor(WHITE); cc.setStrokeColor(INK); cc.setLineWidth(.85)
                cc.rect(x, codes_top-76, 29, 29, fill=1, stroke=1)
            cc.setFillColor(INK); cc.setFont(rb.BOLD, 8.4)
            cc.drawString(M+10, codes_top-101, "COORDINATE")
            cc.setStrokeColor(LINE); cc.setLineWidth(.85)
            cc.line(M+91, codes_top-103, M+col_w-12, codes_top-103)

            open_top = top-188
            zone(right_x, open_top, 120, "OPEN QUESTIONS", (42, 62, 82, 102))
            book.y = min(codes_top-120, open_top-120)
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
                    book.canvas.setStrokeColor(LINE); book.canvas.setLineWidth(.85)
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


def draw_story_comms(book: Book, beats: list[tuple[str, str]], label: str) -> None:
    """Keep meta-thread dialogue in readable, ordered full-width transcripts."""
    style = ParagraphStyle("story_comms", fontName=rb.FONT, fontSize=10.4,
                           leading=14.4, textColor=INK)
    rendered = []
    for kind, line in beats:
        if kind == "narration":
            markup = f"<i>{inline(line)}</i>"
        else:
            speaker, speech = line.split(":", 1) if ":" in line else ("CHAT", line)
            if speaker.startswith("**") and speech.startswith("**"):
                speech = speech[2:].lstrip()
            markup = f"<b>{html.escape(plain(speaker).upper())}</b>  {inline(speech.strip())}"
        paragraph = Paragraph(markup, style)
        _, height = paragraph.wrap(TEXT_W-36-42, H)
        rendered.append((paragraph, height))

    def paint(chunk: list[tuple[Paragraph, float]]) -> None:
        panel_h = 45 + sum(height + 8 for _, height in chunk)
        if book.y - panel_h - 12 < BOTTOM:
            book.begin("story bridge", label=label)
        x, top = M, book.y
        draw_comms_frame(book.canvas, x, top-panel_h, TEXT_W, panel_h, radius=8, grid_strip=34)
        yy = top-40
        for paragraph, height in chunk:
            paragraph.drawOn(book.canvas, x+18, yy-height)
            yy -= height + 8
        book.y -= panel_h + 12

    chunk: list[tuple[Paragraph, float]] = []
    chunk_h = 45
    for item in rendered:
        if chunk and chunk_h + item[1] + 8 > 600:
            paint(chunk)
            chunk, chunk_h = [], 45
        chunk.append(item)
        chunk_h += item[1] + 8
    if chunk:
        paint(chunk)


def draw_story_bridge(book: Book, block: dict) -> None:
    """Use the case COMMS language for the three explicit Room Zero chats."""
    finale = block["title"] == "ROOM ZERO // THE EXPLANATION"
    if finale:
        label = "ROOM ZERO // DEBRIEF"
    elif block["title"] == "ROOM ZERO THREAD // FOUR MATCHING MARKS":
        label = "ROOM ZERO // FOUR MATCHING MARKS"
    else:
        label = "ROOM ZERO // OLD CASES RETURN"
    book.begin("story bridge", label=label)
    in_chat = False
    beats: list[tuple[str, str]] = []

    def flush() -> None:
        if beats:
            draw_story_comms(book, beats, label)
            beats.clear()

    blocks = paragraphs(block["markdown"])
    for position, (kind, value) in enumerate(blocks):
        if kind == "heading":
            flush()
            title = plain(value).upper()
            if title == "HAPPY MAKERS CHAT":
                in_chat = True
                continue
            if finale and title == "THE SIXTH HOOK":
                book.begin("story bridge", label="THE SIXTH HOOK")
                label = "THE SIXTH HOOK"
            in_chat = False
            book.heading(value, 18)
        elif kind == "bullet" and in_chat:
            beats.append(("speaker", value))
        elif (kind == "body" and in_chat and position + 1 < len(blocks)
              and blocks[position + 1][0] == "bullet"):
            beats.append(("narration", value))
        else:
            flush()
            if kind == "bullet":
                book.text("• " + value, size=10.6, gap=5)
            elif kind == "number":
                book.text(value, size=10.6, gap=5)
            else:
                book.text(value, size=10.8, gap=10)
    flush()
    book.end()


def build(pdf_path: Path) -> dict:
    source = build_contract()
    assets = verify_assets()
    derivatives = prepare_print_derivatives()
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
            if block["title"] in (
                "ROOM ZERO THREAD // FOUR MATCHING MARKS",
                "ROOM ZERO THREAD // THE OLD CASES COME BACK",
                "ROOM ZERO // THE EXPLANATION",
            ):
                draw_story_bridge(book, block)
            else:
                section_labels = {
                    "ROOM ZERO THREAD // BIBI REMEMBERS THE FORM": "ROOM ZERO // BIBI REMEMBERS",
                    "ROOM ZERO CHECKPOINT // RULE 0 FIRST": "ROOM ZERO // RULE 0 FIRST",
                }
                book.begin("story bridge", label=section_labels.get(block["title"], block["title"][:33]))
                if block["title"] == "FIELD CERTIFICATION":
                    signature = ("Signed: **Happy Makers Detective Academy**  \n"
                                 "Archive confirmation: **BIBI // ARCHIVE MENTOR**")
                    if block["markdown"].count(signature) != 1:
                        raise ValueError("canonical Field Certification signature drift")
                    before, after = block["markdown"].split(signature, 1)
                    book.render_md(before, 18)
                    book.text("Signed: **Happy Makers Detective Academy**", gap=5)
                    book.text("Archive confirmation: **BIBI // ARCHIVE MENTOR**", gap=10)
                    book.render_md(after, 18)
                else:
                    book.render_md(block["markdown"], 18)
                if block["title"].startswith("ARCHIVE FILE 001"):
                    book.image(PRINT_DERIVATIVES/"book2_archive_photo_canon_print.png", 250, 340)
                book.end()
        else:
            number = block["number"]
            case = next(v for v in source["main_cases"] if v["number"] == number)
            sections = draw_case_brief(book, case)
            if number in spatial:
                draw_witness_board(book, spatial[number], number, case["title"])
                draw_map(book, spatial[number], number, response=sections.get("YOUR VERDICT / RESPONSE", ""))
                if sections.get("CASE WALL -> PAGE 9"):
                    book.begin("case wall update", number, label=f"case {number:02d} / case wall")
                    book.render_md("### CASE WALL -> PAGE 9\n"+sections["CASE WALL -> PAGE 9"], 13)
                    book.end()
            elif number == 1:
                draw_case01(book, missions[number], sections)
            elif number == 3:
                draw_case03(book, sections, case["title"])
            else:
                draw_other_evidence(book, number, missions[number], sections)
    book.begin("stop divider", label="STOP / HINT VAULT")
    book.y = 540
    book.heading("STOP // HINT VAULT", 29)
    book.text("The Hint Vault and Solution Files begin on the next page.", 15)
    book.text("Try one hint level at a time. Keep your verdict yours until you choose a solution.", 11)
    book.end()
    for level in ("1", "2", "3"):
        book.begin(f"hint vault level {level}", label=f"hint vault / level {level}")
        book.render_md(f"# HINT VAULT // LEVEL {level}", 20)
        book.render_md(source["hint_intros"][level], 12)
        for case in source["hint_levels"][level]:
            book.render_md(case["markdown"], 12)
        book.end()
    book.begin("solutions entry", label="solution files")
    book.render_md("# SOLUTION FILES", 20)
    book.render_md(source["solutions_intro"], 12)
    book.end()
    for case in source["solution_files"]:
        number = case["number"]
        book.begin("solution", number, label=f"solution / case {number:02d}")
        book.render_md(project_solution_markdown(number, case["markdown"]), 15)
        if number == 3:
            book.image(OWNER_DIR/"case03_solution.png", 370, 460)
        book.end()
        if number in spatial:
            draw_map(book, spatial[number], number, True)
    if book.page % 2:
        book.begin("closing", label="case closed")
        book.y = 510
        book.heading("CASE CLOSED", 27)
        draw_scanner_question_mark(book.canvas, W/2, 330)
        book.end()
    book.save()
    qa = {
        "status": "RENDERED_REVIEW_REQUIRED" if not book.errors else "BLOCKED",
        "source_blob_sha1": source["authority"]["blob_sha1"],
        "assets": assets,
        "derived_print_assets": derivatives["derivatives"],
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
