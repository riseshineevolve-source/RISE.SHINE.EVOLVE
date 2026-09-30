#!/usr/bin/env python3
"""Deterministic PDF typography / print-safety QA for HMDA interiors.

This check intentionally stays presentation-only. It reads the rendered PDF,
verifies Letter trim, inspects every ReportLab/PDF `Tf` font-size operator, and
fails if child-facing sans text drops below 9 pt or monospace accent text drops
below 6.8 pt. Those thresholds come from the canonical gaming_grayscale style
contract. It does not change story, puzzle logic, pagination, visual choices,
or English freeze state.

Physical proof remains an owner gate; this script catches deterministic digital
print defects only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader

TF_RE = re.compile(rb"/([A-Za-z0-9_.+\-]+)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s+Tf\b")


def _deref(value):
    return value.get_object() if hasattr(value, "get_object") else value


def _font_map(page) -> dict[str, str]:
    resources = _deref(page.get("/Resources") or {})
    fonts = _deref(resources.get("/Font") or {}) if hasattr(resources, "get") else {}
    result: dict[str, str] = {}
    if hasattr(fonts, "items"):
        for key, ref in fonts.items():
            font = _deref(ref)
            base = str(font.get("/BaseFont", key)) if hasattr(font, "get") else str(key)
            result[str(key).lstrip("/")] = base.lstrip("/")
    return result


def _content_bytes(page) -> bytes:
    contents = page.get_contents()
    if contents is None:
        return b""
    try:
        return contents.get_data()
    except AttributeError:
        # Defensive fallback for older pypdf content-array shapes.
        parts = []
        for item in contents:
            obj = _deref(item)
            if hasattr(obj, "get_data"):
                parts.append(obj.get_data())
        return b"\n".join(parts)


def audit(pdf: Path, body_min: float, mono_min: float, min_pages: int,
          expected_pages: int | None) -> dict:
    reader = PdfReader(str(pdf))
    errors: list[str] = []
    warnings: list[str] = []
    usage = Counter()
    small_body_pages: dict[int, list[str]] = defaultdict(list)
    smallest: dict[str, float] = {}

    page_count = len(reader.pages)
    if page_count < min_pages:
        errors.append(f"PDF has {page_count} pages; expected at least {min_pages}.")
    if expected_pages is not None and page_count != expected_pages:
        errors.append(f"PDF has {page_count} pages; expected exactly {expected_pages}.")

    for page_no, page in enumerate(reader.pages, start=1):
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        if abs(w - 612.0) > 0.5 or abs(h - 792.0) > 0.5:
            errors.append(f"Page {page_no}: unexpected trim {w:.1f}x{h:.1f} pt.")

        rotation = int(page.get("/Rotate", 0) or 0) % 360
        if rotation not in (0, 180):
            errors.append(f"Page {page_no}: unsupported print rotation {rotation} degrees.")

        font_map = _font_map(page)
        data = _content_bytes(page)
        matches = list(TF_RE.finditer(data))
        if not matches:
            warnings.append(f"Page {page_no}: no explicit Tf typography operator found.")
            continue

        for match in matches:
            resource = match.group(1).decode("ascii", "replace")
            size = float(match.group(2))
            base_font = font_map.get(resource, resource)
            is_mono = "mono" in base_font.lower() or "courier" in base_font.lower()
            threshold = mono_min if is_mono else body_min
            role = "mono" if is_mono else "body/display"
            usage[(base_font, size)] += 1
            smallest[base_font] = min(size, smallest.get(base_font, size))

            if size + 1e-6 < threshold:
                errors.append(
                    f"Page {page_no}: {role} font {base_font} uses {size:g} pt "
                    f"(< {threshold:g} pt minimum)."
                )
            elif not is_mono and size < 10.5:
                small_body_pages[page_no].append(f"{base_font} {size:g}pt")

    if small_body_pages:
        pages = sorted(small_body_pages)
        preview = ", ".join(str(n) for n in pages[:24])
        suffix = "…" if len(pages) > 24 else ""
        warnings.append(
            "Body/display text between 9 pt and the 10.5 pt target occurs on "
            f"{len(pages)} page(s): {preview}{suffix}. This is allowed but must remain "
            "comfortable in the representative physical proof."
        )

    return {
        "status": "PASS" if not errors else "FAIL",
        "pdf": str(pdf),
        "page_count": page_count,
        "thresholds": {
            "body_display_min_pt": body_min,
            "body_target_pt": 10.5,
            "mono_accent_min_pt": mono_min,
            "trim_pt": [612.0, 792.0],
            "allowed_rotation_degrees": [0, 180],
        },
        "smallest_font_pt_by_base_font": dict(sorted(smallest.items())),
        "font_setting_count": sum(usage.values()),
        "errors": errors,
        "warnings": warnings,
        "physical_proof_still_required": True,
        "english_frozen": False,
        "presentation_only": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--body-min", type=float, default=9.0)
    ap.add_argument("--mono-min", type=float, default=6.8)
    ap.add_argument("--min-pages", type=int, default=1)
    ap.add_argument("--expected-pages", type=int)
    args = ap.parse_args()

    result = audit(
        args.pdf.resolve(),
        body_min=args.body_min,
        mono_min=args.mono_min,
        min_pages=args.min_pages,
        expected_pages=args.expected_pages,
    )
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
