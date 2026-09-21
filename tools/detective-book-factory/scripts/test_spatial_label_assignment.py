#!/usr/bin/env python3
"""Synthetic regression for topology-aware HMDA room-label assignment.

No private Shigai bytes or production case data are required. CI deliberately
stubs image-only imports because this regression exercises pure topology math,
not OpenCV/PDF rendering.
"""

import sys
import types

# The production renderer uses OpenCV/NumPy only when real source images are
# processed. This synthetic test does not touch those paths, so keep the test
# lightweight instead of expanding the editorial CI dependency set.
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))

from render_spatial_map_hybrid_hardened import _self_test, assign_room_label_boxes


def test_object_contour_is_not_a_room_label():
    """A bench's white seat must not beat the real nearby room-name pill."""
    case = {
        "id": "BENCH_CONTOUR",
        "grid": {"columns": 2, "rows": 2},
        "rooms": [
            {"source_room_id": 0, "cells": ["A1", "A2"]},
            {"source_room_id": 1, "cells": ["B1", "B2"]},
        ],
        "objects": [{"cell": "A1", "type": "bench"}],
    }
    bench_seat = (20, 40, 60, 20)
    source_pill = (25, 85, 50, 10)
    assigned, diagnostics = assign_room_label_boxes(case, [bench_seat, source_pill], 200, 200)
    assert assigned == {0: source_pill}, diagnostics
    rejected = next(item for item in diagnostics if item["box"] == bench_seat)
    assert rejected["object_center"] and not rejected["accepted"], diagnostics
    # With no label available the same seat must remain unresolved, never
    # become a white erasure over clue-critical furniture.
    assigned, diagnostics = assign_room_label_boxes(case, [bench_seat], 200, 200)
    assert assigned == {}, diagnostics


if __name__ == "__main__":
    _self_test()
    test_object_contour_is_not_a_room_label()
    print("PASS: topology-aware room-label assignment synthetic regression")
    print("PASS: object-centered bench contours are rejected while nearby source labels survive")
