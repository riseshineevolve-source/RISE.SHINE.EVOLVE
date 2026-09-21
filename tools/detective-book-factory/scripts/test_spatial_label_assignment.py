#!/usr/bin/env python3
"""Synthetic regression for topology-aware HMDA room-label assignment.

No private Shigai bytes or production case data are required.
"""

from render_spatial_map_hybrid_hardened import _self_test


if __name__ == "__main__":
    _self_test()
    print("PASS: topology-aware room-label assignment synthetic regression")
