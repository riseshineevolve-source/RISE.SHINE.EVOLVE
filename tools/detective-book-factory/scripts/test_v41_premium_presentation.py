#!/usr/bin/env python3
"""Deterministic contract test for V4.1 premium presentation layers."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import build_owner_review_v4 as v4
import build_owner_review_v41 as v41
import build_owner_review_v41_premium as premium


def test_family_routing() -> None:
    expected = ["TRACE", "ARCHIVE", "ROUTING", "TRACE", "ARCHIVE", "ROUTING"]
    assert [premium.signal_family_for_case(n) for n in range(1, 7)] == expected
    assert {premium.signal_family_for_case(n) for n in range(1, 31)} == set(premium.SIGNAL_FAMILIES)
    try:
        premium.signal_family_for_case(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Case 0 must fail closed")


def test_wrapper_patches_only_during_delegate() -> None:
    original_signal = v4.signal_page
    original_witness = v4.witness_board
    original_main = v41.main
    original_argv = list(sys.argv)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "owner-review.pdf"
        manifest = Path(tmp) / premium.MANIFEST_NAME

        def fake_main() -> None:
            assert v4.signal_page is premium.signal_page_v41
            assert v4.witness_board is premium.witness_board_v41
            manifest.write_text(json.dumps({
                "revision": "v4.1",
                "english_frozen": False,
                "premium_polish": {
                    "logic_changed": False,
                    "pagination_changed": False,
                },
            }), encoding="utf-8")

        try:
            v41.main = fake_main
            sys.argv = ["build_owner_review_v41_premium.py", "--output", str(out)]
            premium.main()
        finally:
            v41.main = original_main
            sys.argv = original_argv

        assert v4.signal_page is original_signal
        assert v4.witness_board is original_witness
        packet = json.loads(manifest.read_text(encoding="utf-8"))
        assert packet["english_frozen"] is False
        signal = packet["premium_polish"]["signal_log_visual_families"]
        assert signal["status"] == "INTEGRATED"
        assert signal["content_changed"] is False
        assert signal["pagination_changed"] is False
        room_zero = packet["premium_polish"]["room_zero_trace_presentation"]
        assert room_zero["mechanism_changed"] is False
        assert room_zero["chain"] == "CASE -> SIGNAL CODE -> VERIFIED STATUS"
        witness = packet["premium_polish"]["witness_board_presentation"]
        assert witness["status"] == "INTEGRATED"
        assert witness["style"] == premium.WITNESS_BOARD_STYLE
        assert witness["clue_text_changed"] is False
        assert witness["witness_identity_changed"] is False
        assert witness["pagination_changed"] is False
        assert witness["spatial_geometry_changed"] is False


if __name__ == "__main__":
    test_family_routing()
    test_wrapper_patches_only_during_delegate()
    print("PASS: V4.1 premium presentation contract")
