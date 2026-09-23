#!/usr/bin/env python3
"""Regression contract for V4.1 reader-facing cleanup.

This test is intentionally source-bounded: it verifies that the V4.1 wrapper,
not the locked V4 baseline, owns the cleanup and that render_v4 is monkeypatched
only for the three presentation surfaces in scope. Puzzle logic, spatial
geometry, owner-gated visuals and pagination stay outside this contract.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import yaml

import build_owner_review_v41 as v41

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    publication_src = inspect.getsource(v41.publication_page_v41).lower()
    require("owner-review" not in publication_src,
            "V4.1 publication surface still exposes owner-review copy")
    require("interior proof" not in publication_src,
            "V4.1 publication surface still exposes proof-only copy")

    solution_src = inspect.getsource(v41.nonspatial_solution_page_v41).lower()
    require("spoiler treatment:" not in solution_src,
            "V4.1 solution surface still exposes an internal rendering note")

    id_src = inspect.getsource(v41.id_page_v41)
    require("call_sign_label" not in id_src,
            "Field Detective ID still renders a duplicate fallback call-sign field")
    require("DETECTIVE NAME / CALL SIGN" in id_src,
            "Field Detective ID lost its canonical combined identity label")
    require("FIELD DETECTIVE ID" in id_src,
            "Field Detective ID naming is not normalized on the V4.1 surface")

    main_src = inspect.getsource(v41.main)
    required_wiring = (
        "v4.publication_page = publication_page_v41",
        "v4.id_page = id_page_v41",
        "v4.nonspatial_solution_page = nonspatial_solution_page_v41",
        "v4.publication_page = original_publication",
        "v4.id_page = original_id_page",
        "v4.nonspatial_solution_page = original_nonspatial_solution",
    )
    for line in required_wiring:
        require(line in main_src, f"V4.1 cleanup wiring missing: {line}")

    overrides = yaml.safe_load(
        (ROOT / "content" / "book1_v4_overrides.yml").read_text(encoding="utf-8")
    )
    card = overrides["opening"]["id_card"]
    require(card.get("heading") == "FIELD DETECTIVE ID",
            "Canonical ID heading drifted")
    require(card.get("name_label") == "DETECTIVE NAME / CALL SIGN",
            "Canonical one-line identity label drifted")

    print("PASS: V4.1 reader-facing cleanup contract")
    print("- publication proof/internal copy blocked")
    print("- Field Detective ID uses one canonical identity field")
    print("- nonspatial solution internal rendering note blocked")
    print("- V4 baseline is restored after bounded render")


if __name__ == "__main__":
    main()
