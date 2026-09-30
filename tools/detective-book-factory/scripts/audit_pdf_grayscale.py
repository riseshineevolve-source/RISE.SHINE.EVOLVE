#!/usr/bin/env python3
"""Fail-closed grayscale audit for the final HMDA PDF.

The final interior may use black, white and grayscale only. Equal-channel RGB
operators are accepted as grayscale; CMYK operators are accepted only when
C=M=Y=0. Embedded images are decoded and checked pixel-for-pixel for R=G=B.

This audit does not modify the PDF.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import ImageChops
from pypdf import PdfReader
from pypdf.generic import ContentStream

EPS = 1e-9


def _num(value) -> float:
    return float(value)


def _equal3(values) -> bool:
    a, b, c = (_num(v) for v in values[:3])
    return abs(a - b) <= EPS and abs(a - c) <= EPS


def _black_only_cmyk(values) -> bool:
    c, m, y, _k = (_num(v) for v in values[:4])
    return abs(c) <= EPS and abs(m) <= EPS and abs(y) <= EPS


def _image_is_grayscale(image) -> bool:
    rgb = image.convert("RGB")
    r, g, b = rgb.split()
    rg = ImageChops.difference(r, g).getextrema()
    rb = ImageChops.difference(r, b).getextrema()
    return rg == (0, 0) and rb == (0, 0)


def audit_pdf_grayscale(pdf_path: Path, report_path: Path | None = None) -> dict:
    reader = PdfReader(str(pdf_path))
    errors: list[str] = []
    vector_checks = 0
    image_checks = 0

    for page_no, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents is not None:
            stream = ContentStream(contents, reader)
            for operands, operator in stream.operations:
                op = operator.decode("latin-1") if isinstance(operator, bytes) else str(operator)
                if op in ("rg", "RG"):
                    vector_checks += 1
                    if len(operands) < 3 or not _equal3(operands):
                        errors.append(
                            f"page {page_no}: non-grayscale RGB operator {op} "
                            f"{[str(v) for v in operands]}"
                        )
                elif op in ("k", "K"):
                    vector_checks += 1
                    if len(operands) < 4 or not _black_only_cmyk(operands):
                        errors.append(
                            f"page {page_no}: chromatic CMYK operator {op} "
                            f"{[str(v) for v in operands]}"
                        )
                elif op in ("g", "G"):
                    vector_checks += 1

        try:
            images = list(page.images)
        except Exception as exc:
            errors.append(f"page {page_no}: could not enumerate embedded images: {exc}")
            continue

        for image_file in images:
            image_checks += 1
            try:
                image = image_file.image
                if image is None:
                    raise ValueError("decoded image is unavailable")
                if not _image_is_grayscale(image):
                    errors.append(
                        f"page {page_no}: embedded image {getattr(image_file, 'name', '<unnamed>')} "
                        "contains non-grayscale pixels"
                    )
            except Exception as exc:
                errors.append(
                    f"page {page_no}: could not verify embedded image "
                    f"{getattr(image_file, 'name', '<unnamed>')}: {exc}"
                )

    report = {
        "status": "PASS" if not errors else "FAIL",
        "pdf": str(pdf_path),
        "pages": len(reader.pages),
        "vector_color_operators_checked": vector_checks,
        "embedded_images_checked": image_checks,
        "grayscale_only": not errors,
        "errors": errors,
    }

    if report_path is not None:
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if errors:
        preview = "\n".join(errors[:20])
        extra = "" if len(errors) <= 20 else f"\n... {len(errors) - 20} more"
        raise ValueError(
            f"Final HMDA artifact is not grayscale-only ({len(errors)} issue(s)):\n"
            f"{preview}{extra}"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = audit_pdf_grayscale(args.pdf.resolve(), args.report.resolve() if args.report else None)
    print(
        "PASS: grayscale-only final PDF // "
        f"{report['pages']} pages // "
        f"{report['vector_color_operators_checked']} vector color ops // "
        f"{report['embedded_images_checked']} embedded images"
    )


if __name__ == "__main__":
    main()
