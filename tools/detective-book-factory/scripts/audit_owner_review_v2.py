#!/usr/bin/env python3
"""Measure an owner-review PDF and prepare its complete visual QA packet.

Machine checks do not certify visual readability, writing surfaces, clipping
inside cards, raster labels, or puzzle solvability. Those limits are explicit
in both reports. No source content or PDF is modified by this command.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECORATIVE = [
    r"^(?:HAPPY MAKERS )?DETECTIVE ACADEMY$", r"^\d{3}$",
    r"^CASE SYSTEM // OFFLINE$", r"^ENGLISH EDITION$",
    r"^ROOM ZERO // CASE FILE OPEN$",
]
FORBIDDEN = re.compile(
    r"\b(?:Shigai|raw\s+modules?|verified\s+module|generator\s+ID|source\s+ID|"
    r"TODO|TBD|TBC|FIXME|placeholder|lorem\s+ipsum)\b|HMDA_\d{2}", re.I
)
CASE_PATTERN = re.compile(r"^(?:[A-Z ]+\s*//\s*)?CASE\s+(\d{2})(?!\d)", re.I | re.M)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_font(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.split("+")[-1].lower())


def family(text: str, page: int) -> str:
    head = text[:350].upper()
    if "HINT VAULT" in head:
        return "hint_vault"
    if "SOLUTION" in head:
        return "solution"
    if "WITNESS BOARD" in head:
        return "witness_board"
    if "LIVE CASE MAP" in head:
        return "live_case_map"
    if "YOUR SQUAD" in head:
        return "squad"
    if re.search(r"^(?:BUILD YOUR )?DETECTIVE ID(?:\s*//|$)|^PLAYER PROFILE", head, re.M):
        return "detective_id"
    if "CERTIFICATE" in head:
        return "certificate"
    if any(token in head for token in ("ROOM ZERO", "FINAL FILE", "OLD MAP")) and page > 8:
        return "room_zero"
    if page <= 8:
        return "opening_onboarding"
    if "MISSION BRIEF" in text[:900] or "CASE FILE" in head:
        return "mission_brief"
    return "case_activity"


def case_sections(text: str) -> list[tuple[str, str]]:
    """Scope name checks to each case, including multi-case Hint Vault pages."""
    matches = list(CASE_PATTERN.finditer(text))
    if not matches:
        return []
    return [(f"HMDA_{match.group(1)}", text[match.start():matches[i + 1].start()
            if i + 1 < len(matches) else len(text)]) for i, match in enumerate(matches)]


def font(size: int):
    for path in (Path("C:/Windows/Fonts/arial.ttf"),
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def contact_sheet(pages: list[int], previews: Path, target: Path, title: str,
                  thumbnail_width: int = 510, columns: int = 3) -> None:
    if not pages:
        return
    gap, heading, caption = 20, 60, 32
    thumb_h = round(thumbnail_width * 792 / 612)
    rows = math.ceil(len(pages) / columns)
    sheet = Image.new("RGB", (columns * (thumbnail_width + gap) + gap,
                              heading + rows * (thumb_h + caption + gap) + gap), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 14), title, fill="black", font=font(26))
    for idx, page in enumerate(pages):
        with Image.open(previews / f"page_{page:03d}.png") as im:
            tile = ImageOps.contain(im.convert("RGB"), (thumbnail_width, thumb_h), Image.Resampling.LANCZOS)
        x = gap + (idx % columns) * (thumbnail_width + gap)
        y = heading + (idx // columns) * (thumb_h + caption + gap)
        sheet.paste(tile, (x, y))
        draw.rectangle((x, y, x + tile.width, y + tile.height), outline="#AAAAAA", width=1)
        draw.text((x, y + thumb_h + 4), f"Printed page {page}", fill="black", font=font(20))
    sheet.save(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expected-pages", type=int, default=141)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--min-essential-pt", type=float, default=9.5)
    parser.add_argument("--margin-pt", type=float, default=27,
                        help="Text-safe inset; this is not a binding/gutter certification.")
    parser.add_argument("--decorative-regex", action="append", default=[],
                        help="Explicit additional full-span metadata exclusion; repeatable and reported.")
    parser.add_argument("--skip-previews", action="store_true",
                        help="Focused machine recheck only; does not create or certify a QA packet.")
    parser.add_argument("--report-title", default="HMDA OWNER REVIEW V2 MACHINE AUDIT",
                        help="Heading written to audit.txt.")
    args = parser.parse_args()
    if args.dpi < 72 or args.expected_pages < 1:
        parser.error("dpi must be >=72 and expected-pages must be positive")
    for path in (args.pdf, args.content, args.runtime):
        if not path.is_file():
            parser.error(f"Missing input: {path}")
    args.out.mkdir(parents=True, exist_ok=True)
    previews = args.out / "previews_150dpi"
    sheets = args.out / "contact_sheets"
    if not args.skip_previews:
        previews.mkdir(exist_ok=True)
        sheets.mkdir(exist_ok=True)
    content = yaml.safe_load(args.content.read_text(encoding="utf-8"))
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in runtime["cases"]}
    issues: list[dict] = []
    checks: dict = {}

    def finding(level: str, code: str, message: str, page: int | None = None, **details):
        issues.append({"severity": level, "code": code, "message": message,
                       **({"page": page} if page is not None else {}), **details})

    missions = content.get("missions", [])
    checks["mission_numbers"] = [m.get("number") for m in missions]
    if checks["mission_numbers"] != list(range(1, 31)):
        finding("error", "mission_structure", "Content must contain exactly missions 01-30 in order.")
    spatial = [m for m in missions if m.get("spatial_source_id")]
    checks["spatial_case_ids"] = [m["spatial_source_id"] for m in spatial]
    if len(cases) != 15 or set(checks["spatial_case_ids"]) != set(cases) or len(spatial) != 15:
        finding("error", "spatial_structure", "Exactly the 15 runtime spatial cases must be attached.")
    for mission in missions:
        if len(mission.get("hints", [])) != 3 or not mission.get("solution_steps"):
            finding("error", "hint_solution", f"Case {mission.get('number')}: needs three hints and reasoning.")
    checks["meta_message"] = runtime.get("meta_message")
    if checks["meta_message"] != "CHECKTHEOLDMAP":
        finding("error", "meta_message", "Runtime meta message changed.")
    asset_records = []
    hashes: dict[str, str] = {}
    for mission in spatial:
        info = mission.get("spatial", {})
        for role in ("source_page_asset", "solution_asset"):
            value = info.get(role) or (info.get("puzzle_asset") if role == "source_page_asset" else None)
            path = Path(value) if value else None
            if path is not None and not path.is_absolute():
                path = ROOT / path
            label = f"{mission['spatial_source_id']} {role}"
            if path is None or not path.is_file():
                finding("error", "missing_asset", f"{label}: missing file", path=str(path))
                continue
            digest = sha(path)
            if digest in hashes:
                finding("error", "duplicate_spatial_asset", f"{label} duplicates {hashes[digest]}")
            hashes[digest] = label
            try:
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    size = list(im.size)
                asset_records.append({"case": mission["spatial_source_id"], "role": role,
                                      "path": str(path), "sha256": digest, "pixels": size})
            except Exception as exc:
                finding("error", "unreadable_asset", f"{label}: {exc}")
    checks["spatial_assets"] = asset_records
    for key, character in content.get("characters", {}).items():
        path = ROOT / character.get("asset", "__MISSING__")
        if not path.is_file():
            finding("error", "missing_character", f"Character asset missing: {key}", path=str(path))
    squad_source=ROOT.parents[1]/'assets/images/Happy Makers detectives.png'
    squad_output=ROOT/content['characters']['squad']['asset']
    with Image.open(squad_source) as source, Image.open(squad_output) as output:
        expected=ImageOps.autocontrast(source.convert('L'),cutoff=.5)
        expected.thumbnail((1800,1800),Image.Resampling.LANCZOS)
        if expected.size != output.size:
            finding('error','squad_identity','Squad dimensions differ from approved source normalization.')
        else:
            diff=ImageChops.difference(expected,output.convert('L'))
            hist=diff.histogram(); mean=sum(i*n for i,n in enumerate(hist))/sum(hist)
            if mean>3: finding('error','squad_identity','Squad pixels do not match the approved detective artwork.')
            checks['approved_squad']={'source_sha256':sha(squad_source),'output_sha256':sha(squad_output),'mean_jpeg_difference':round(mean,3)}

    exclusions = [re.compile(pattern, re.I) for pattern in DEFAULT_DECORATIVE + args.decorative_regex]
    page_records = []
    font_records: dict[int, dict] = {}
    doc = fitz.open(args.pdf)
    checks["page_count"] = len(doc)
    checks["expected_pages"] = args.expected_pages
    if len(doc) != args.expected_pages:
        finding("error", "page_count", f"Expected {args.expected_pages} pages; found {len(doc)}.")
    witness_ids, map_ids, solution_ids = set(), set(), set()
    for number, page in enumerate(doc, 1):
        rect = page.rect
        text = page.get_text()
        page_family = family(text, number)
        spans = [span for block in page.get_text("dict")["blocks"] if block.get("type") == 0
                 for line in block.get("lines", []) for span in line.get("spans", []) if span["text"].strip()]
        used_fonts = {normalized_font(span["font"]) for span in spans}
        # No-bleed Letter: include folios and decoration, not only body copy.
        # KDP gutter <=150 pages is 0.375in; all outer edges need 0.25in.
        gutter=27 if len(doc)<=150 else 36
        safe=fitz.Rect(gutter if number%2 else 18,18,
                       612-(18 if number%2 else gutter),774)
        for span in spans:
            if not (safe+(-.5,-.5,.5,.5)).contains(fitz.Rect(span['bbox'])):
                finding('error','kdp_text_margin',span['text'],number,bbox=list(span['bbox']))
        for drawing in page.get_drawings():
            paint=[drawing.get('fill'),drawing.get('color')]
            if not any(color is not None and min(color)<.97 for color in paint): continue
            if not (safe+(-.5,-.5,.5,.5)).contains(drawing['rect']):
                finding('error','kdp_graphic_margin','Nonwhite vector artwork outside no-bleed safe area.',number,bbox=list(drawing['rect']))
        if abs(rect.width - 612) > .5 or abs(rect.height - 792) > .5:
            finding("error", "trim", f"Page size {rect.width:.2f} x {rect.height:.2f} pt is not Letter.", number)
        for match in FORBIDDEN.finditer(text):
            finding("error", "forbidden_copy", f"Reader-facing term: {match.group(0)}", number)
        for info in page.get_fonts(full=True):
            xref, extension, kind, basefont = info[:4]
            if normalized_font(basefont) not in used_fonts:
                continue  # ReportLab may declare an unused base-14 default.
            if xref not in font_records:
                extracted = doc.extract_font(xref) if xref else ("", "", "", b"")
                font_records[xref] = {"xref": xref, "name": basefont, "type": kind,
                                      "embedded": bool(extracted[3]), "pages": []}
            font_records[xref]["pages"].append(number)
            if not font_records[xref]["embedded"]:
                finding("error", "font_not_embedded", f"Used font {basefont} is not embedded.", number)
        significant_sizes = []
        excluded_count = 0
        for span in spans:
            value = span["text"].strip()
            box = [round(v, 2) for v in span["bbox"]]
            x0, y0, x1, y1 = box
            if x0 < -.5 or y0 < -.5 or x1 > rect.width + .5 or y1 > rect.height + .5:
                finding("error", "text_outside_page", value, number, bbox=box)
            decorative = any(pattern.fullmatch(value) for pattern in exclusions)
            # Only running page headers/folios qualify by location. The lower
            # content area is never excluded wholesale.
            decorative = decorative or (y1 < 43 and re.search(r"//\s*\d{3}$", value) is not None)
            if decorative:
                excluded_count += 1
                continue
            significant_sizes.append(span["size"])
            if span["size"] < args.min_essential_pt - .15:
                finding("error", "small_required_text", value, number, size_pt=round(span["size"], 2), bbox=box)
            elif span["size"] < 10.8 and len(value) > 55 and not value.isupper():
                finding("warning", "body_below_target", value, number, size_pt=round(span["size"], 2), bbox=box)
            rgb = ((span["color"] >> 16) & 255, (span["color"] >> 8) & 255, span["color"] & 255)
            if not (max(rgb) <= 8 or min(rgb) >= 247):
                finding("error", "meaningful_gray_text", value, number, rgb=rgb, bbox=box)
            if x0 < args.margin_pt - .5 or x1 > rect.width - args.margin_pt + .5 or y0 < 27 or y1 > rect.height - 27:
                finding("warning", "text_near_trim", value, number, bbox=box)
        sections = case_sections(text)
        for cid, section in sections:
            if cid not in cases:
                continue
            case = cases[cid]
            display = {person["display_name"].casefold() for person in case["characters"]}
            for person in case["characters"]:
                raw = person["source_name"]
                if raw.casefold() not in display and re.search(rf"\b{re.escape(raw)}\b", section, re.I):
                    finding("error", "raw_name", f"{cid}: raw identity {raw} (expected {person['display_name']})", number)
            # Remove complete accepted display phrases before checking old
            # terms, so Robotics Lab is not mistaken for an old Lab label.
            room_text=section
            if page_family=='witness_board':
                room_text=section.split('WITNESS STATEMENTS',1)[-1]
            elif page_family=='solution':
                room_text=section.split('HOW THE CASE FALLS INTO PLACE',1)[-1]
            elif page_family!='hint_vault':
                # Map names are raster text and require the visual gate. Its
                # narrative title ("library book") is not a room reference.
                room_text=''
            for room in sorted(case['rooms'],key=lambda r:len(r['final_name']),reverse=True):
                room_text=re.sub(rf"\b{re.escape(room['final_name'])}\b",'',room_text,flags=re.I)
            for room in case['rooms']:
                if re.search(rf"\b{re.escape(room['source_name'])}\b",room_text,re.I):
                    finding('error','raw_room_name',f"{cid}: source room name {room['source_name']}",number)
            if page_family == "witness_board":
                witness_ids.add(cid)
                absent = [p["display_name"] for p in case["characters"]
                          if not re.search(rf"\b{re.escape(p['display_name'])}\b", section, re.I)]
                if absent:
                    finding("error", "missing_witness_alias", f"{cid}: names absent from Witness Board: {absent}", number)
            elif page_family == "live_case_map":
                map_ids.add(cid)
            elif page_family == "solution":
                solution_ids.add(cid)
                answer = case["source_answer"]
                if not re.search(rf"\b{re.escape(answer['coordinate'])}\b", section, re.I):
                    finding("error", "solution_answer_coordinate", f"{cid}: solution lacks {answer['coordinate']}", number)
            if page_family in {"witness_board", "live_case_map"}:
                answer = case["source_answer"]
                if re.search(rf"\b{re.escape(answer['display_name'])}\s*@\s*{re.escape(answer['coordinate'])}\b", section, re.I):
                    finding("error", "answer_marker_on_puzzle", f"{cid}: explicit answer marker appears before solution.", number)
        images = []
        for info in page.get_image_info(xrefs=True):
            image_rect = fitz.Rect(info["bbox"])
            if image_rect.width <= 0 or image_rect.height <= 0:
                continue
            resolution = min(info["width"] * 72 / image_rect.width, info["height"] * 72 / image_rect.height)
            images.append({"pixels": [info["width"], info["height"]], "bbox": list(image_rect),
                           "effective_dpi": round(resolution, 1), "colorspace": info.get("cs-name")})
            if not (safe+(-.5,-.5,.5,.5)).contains(image_rect):
                finding('error','kdp_image_margin','Image outside no-bleed safe area.',number,bbox=list(image_rect))
            if resolution < 299:
                finding("error", "raster_resolution",
                        f"Placed raster has {resolution:.1f} effective DPI.", number, bbox=list(image_rect))
        # Render at low resolution for actual color evidence, including raster
        # content; RGB containers alone do not mean an image is visibly colored.
        pix = page.get_pixmap(matrix=fitz.Matrix(.5, .5), colorspace=fitz.csRGB, alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        red, green, blue = im.split()
        chroma = ImageChops.lighter(ImageChops.difference(red, green), ImageChops.difference(green, blue))
        colored = sum(chroma.histogram()[5:])
        color_fraction = colored / (pix.width * pix.height)
        if color_fraction > .001:
            finding("error", "visible_color", f"{color_fraction:.2%} of sampled pixels differ by >4 RGB levels.", number)
        record = {"page": number, "family": page_family, "case_ids": sorted({cid for cid, _ in sections}),
                  "minimum_essential_font_pt": round(min(significant_sizes), 2) if significant_sizes else None,
                  "excluded_metadata_spans": excluded_count, "text_excerpt": text[:180],
                  "images": images, "sampled_color_fraction": color_fraction,
                  "writing_surface_candidate": bool(re.search(
                      r"YOUR VERDICT|COORDINATE|DETECTIVE NAME|DETECTIVE ID|PLAYER PROFILE|WRITE|MY THEORY|MY CONCLUSION|SIGNATURE|EMPTY ROOM|CODE RULES|AWARDED TO|YOUR MOVE|_{4,}", text, re.I))}
        page_records.append(record)
        if not args.skip_previews:
            page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False).save(previews / f"page_{number:03d}.png")
        if number % 12 == 0:
            print(f"Audited {number}/{len(doc)} pages", flush=True)
    checks["used_fonts"] = list(font_records.values())
    checks["witness_board_cases"] = sorted(witness_ids)
    checks["live_map_cases"] = sorted(map_ids)
    checks["spatial_solution_cases"] = sorted(solution_ids)
    for label, found in (("Witness Boards", witness_ids), ("Live Case Maps", map_ids), ("spatial solutions", solution_ids)):
        if found != set(cases):
            finding("error", "page_family_coverage", f"{label}: missing {sorted(set(cases)-found)}; extra {sorted(found-set(cases))}")
    fulltext = "\n".join(page.get_text() for page in doc)
    for expected in ("CHECK THE OLD MAP", "ZERO ASSUMPTIONS", "NEXT DETECTIVE"):
        if expected not in re.sub(r"\s+", " ", fulltext).upper():
            finding("error", "room_zero_copy", f"Required Room Zero phrase absent: {expected}")
    checks["page_families"] = dict(Counter(record["family"] for record in page_records))
    generated = []
    if not args.skip_previews:
        all_pages = list(range(1, len(doc) + 1))
        groups = {
            "opening_onboarding": [r["page"] for r in page_records if r["page"] <= 8],
            "all15_maps": [r["page"] for r in page_records if r["family"] == "live_case_map"],
            "all15_witness_boards": [r["page"] for r in page_records if r["family"] == "witness_board"],
            "writing_verdict_surfaces": [r["page"] for r in page_records if r["writing_surface_candidate"]],
            "all_pages": all_pages,
        }
        for name, pages in groups.items():
            batch = 15 if name.startswith("all15") else 12
            for offset in range(0, len(pages), batch):
                selected = pages[offset:offset + batch]
                target = sheets / f"{name}_{offset // batch + 1:02d}.png"
                contact_sheet(selected, previews, target, f"{name.replace('_', ' ').title()} | pages {', '.join(map(str, selected))}")
                generated.append({"path": str(target), "pages": selected})
        samples = {}
        for label, cid in (("early_case", "HMDA_02"), ("mid_case", "HMDA_15"), ("late_case", "HMDA_29")):
            selected = next((r["page"] for r in page_records if r["family"] == "witness_board" and cid in r["case_ids"]), None)
            if selected:
                samples[label] = selected
        for label, selected_family in (("hint_vault", "hint_vault"), ("solution", "solution"),
                                       ("room_zero_finale", "certificate"), ("squad_page", "squad")):
            selected = next((r["page"] for r in page_records if r["family"] == selected_family), None)
            if selected:
                samples[label] = selected
            else:
                finding("error", "missing_representative", f"Cannot find page family for {label}")
        for label, number in samples.items():
            target = args.out / f"{label}.png"
            shutil.copyfile(previews / f"page_{number:03d}.png", target)
            generated.append({"path": str(target), "pages": [number]})
        contact_sheet(list(samples.values()), previews, sheets / "representative_pages.png", "Representative page families")
        generated.append({"path": str(sheets / "representative_pages.png"), "pages": list(samples.values())})
    counts = Counter(issue["severity"] for issue in issues)
    status = "NEEDS WORK" if counts["error"] else "MACHINE CHECKS PASS; VISUAL REVIEW REQUIRED"
    report = {"status": status, "inputs": {"pdf": str(args.pdf.resolve()), "pdf_sha256": sha(args.pdf),
               "content": str(args.content.resolve()), "content_sha256": sha(args.content),
               "runtime": str(args.runtime.resolve()), "runtime_sha256": sha(args.runtime)},
              "settings": {"dpi": args.dpi, "expected_pages": args.expected_pages,
                           "minimum_essential_pt": args.min_essential_pt, "margin_pt": args.margin_pt,
                           "decorative_exclusions": DEFAULT_DECORATIVE + args.decorative_regex},
              "checks": checks, "issue_counts": dict(counts), "issues": issues, "pages": page_records,
              "qa_artifacts": generated, "preview_count": 0 if args.skip_previews else len(doc),
              "visual_review": "REQUIRED; never inferred from machine checks",
              "limits": ["No OCR: raster map labels, coordinates and solution markers need visual inspection.",
                         "Span bounds do not prove absence of clipping inside cards, overlaps or hidden text.",
                         "Writing-surface lightness and pencil usability need visual inspection.",
                         "No solver: source/checkpoint and clue semantics require separate logic validation.",
                         "No-bleed margins and gutter are measured; paper, binding and pencil feel require a physical proof.",
                         "Squad source identity is checked numerically; page composition still needs visual review."]}
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [args.report_title, status,
             f"PDF: {args.pdf.resolve()}", f"SHA256: {report['inputs']['pdf_sha256']}",
             f"Pages: {len(doc)} (expected {args.expected_pages}); missions: {len(missions)}; spatial assets: {len(asset_records)}",
             f"Errors: {counts['error']}; warnings: {counts['warning']}; previews: {report['preview_count']}",
             "Visual review: REQUIRED", "", "FINDINGS"]
    for issue in issues:
        prefix = f"page {issue['page']}: " if "page" in issue else ""
        lines.append(f"{issue['severity'].upper()} [{issue['code']}] {prefix}{issue['message']}")
    lines.extend(["", "SCOPE LIMITS", *report["limits"], "", "QA ARTIFACTS"])
    lines.extend(item["path"] for item in generated)
    (args.out / "audit.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{status}: {counts['error']} errors; {counts['warning']} warnings. {args.out / 'audit.txt'}")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
