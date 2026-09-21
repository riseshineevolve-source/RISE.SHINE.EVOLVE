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

from render_spatial_map_hybrid_hardened import _self_test


if __name__ == "__main__":
    _self_test()
    print("PASS: topology-aware room-label assignment synthetic regression")
