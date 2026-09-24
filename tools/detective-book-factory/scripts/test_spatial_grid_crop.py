#!/usr/bin/env python3
"""Regression for complete source-map framing, using only synthetic pixels.

Protect against choosing an interior wall when a solution-page map starts
above 12% of the image, and against accepting a full-width footer as the map
bottom. No private source images or source-label metadata are changed.
"""
from __future__ import annotations

import numpy as np

from render_spatial_map_hybrid import detect_grid_bbox


def scene(top: int = 80) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    page = np.full((1200, 1000), 255, dtype=np.uint8)
    left, right, bottom, thickness = 100, 900, top + 800, 6
    page[top:bottom + 1, left:left + thickness] = 0
    page[top:bottom + 1, right - thickness + 1:right + 1] = 0
    page[top:top + thickness, left:right + 1] = 0
    page[bottom - thickness + 1:bottom + 1, left:right + 1] = 0
    # Interior walls are plausible false top/bottom candidates for a detector
    # based only on the first/last sufficiently dark horizontal run.
    for offset in (200, 400, 600):
        page[top + offset:top + offset + thickness, left:right + 1] = 0
    # Isolated furniture-like marks add dark pixels without forming a frame.
    page[top + 30:top + 110, 230:320] = 40
    page[top + 430:top + 490, 650:730] = 30
    return page, (left, top, right, bottom)


def expect_rejection(page: np.ndarray, label: str) -> None:
    try:
        detect_grid_bbox(page)
    except SystemExit:
        return
    raise AssertionError(f"{label}: incomplete geometry must fail closed")


def main() -> None:
    short_header, expected = scene()
    assert expected[1] < short_header.shape[0] * .12
    actual = detect_grid_bbox(short_header)
    assert actual == expected, f"Short header lost first map rows: {actual} != {expected}"

    footer_bars = short_header.copy()
    footer_bars[35:41, 30:971] = 0
    footer_bars[965:971, 30:971] = 0
    # This footer forms an approximately square top/bottom pair with the
    # first interior wall. Its disconnected vertical edges must reject it.
    footer_bars[1080:1086, 30:971] = 0
    actual = detect_grid_bbox(footer_bars)
    assert actual == expected, f"Non-map bars expanded/truncated map crop: {actual}"

    regular_header, regular_expected = scene(top=180)
    assert detect_grid_bbox(regular_header) == regular_expected, "Ordinary source-page frame regressed"

    missing_top = footer_bars.copy()
    missing_top[80:86, 100:901] = 255
    expect_rejection(missing_top, "Missing top outer border")

    broken_sides = footer_bars.copy()
    broken_sides[400:600, 100:106] = 255
    broken_sides[400:600, 895:901] = 255
    expect_rejection(broken_sides, "Disconnected outer vertical borders")

    print("PASS: complete square frame retained above legacy 12% cutoff")
    print("PASS: header/footer bars and interior walls excluded from map bounds")
    print("PASS: ordinary framing retained; missing top/broken sides fail closed")


if __name__ == "__main__":
    main()
