#!/usr/bin/env python3
"""Report whether HMDA Book 1 is reproducible from the current repository.

This is intentionally an audit, not a content generator. It prevents a local
preview or an old chat from being mistaken for a durable KDP source.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"MISSING: {rel}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def mission_numbers(doc) -> list[int]:
    return [int(m["number"]) for m in (doc or {}).get("missions", []) if "number" in m]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--require-canonical-30",
        action="store_true",
        help="Fail unless the renderer-ready production source has exactly Cases 01-30.",
    )
    args = ap.parse_args()

    production = load("content/book1_en_production.yml")
    blueprint = load("content/book_en.yml")
    phase3 = load("content/book1_en_phase3.yml")
    spatial = load("content/spatial_source_manifest_final.yml")

    prod_nums = mission_numbers(production)
    blueprint_nums = mission_numbers(blueprint)
    phase3_nums = mission_numbers(phase3)
    spatial_cases = [str(c.get("id")) for c in spatial.get("cases", [])]

    expected_30 = list(range(1, 31))
    selected_15 = [
        "HMDA_02", "HMDA_04", "HMDA_06", "HMDA_07", "HMDA_10",
        "HMDA_12", "HMDA_13", "HMDA_15", "HMDA_17", "HMDA_19",
        "HMDA_20", "HMDA_22", "HMDA_23", "HMDA_25", "HMDA_29",
    ]
    meta = str(spatial.get("meta_engine", {}).get("message", "")).replace(" ", "")

    print("HMDA BOOK 1 LAUNCH AUDIT")
    print(f"renderer-ready production missions: {len(prod_nums)} -> {prod_nums}")
    print(f"story blueprint missions:          {len(blueprint_nums)}")
    print(f"phase-3 production-copy missions:  {len(phase3_nums)} -> {phase3_nums}")
    print(f"locked spatial sources:            {len(spatial_cases)}")
    print(f"locked meta message:               {meta}")

    errors: list[str] = []
    warnings: list[str] = []

    if blueprint_nums != expected_30:
        errors.append("book_en.yml is not a complete ordered 01-30 blueprint.")
    if spatial_cases != selected_15:
        errors.append("final spatial manifest does not match the locked 15-case production bank.")
    if meta != "CHECKTHEOLDMAP":
        errors.append("final spatial manifest meta message is not CHECKTHEOLDMAP.")
    if prod_nums != expected_30:
        warnings.append(
            "book1_en_production.yml is not yet a durable complete Book 1 master. "
            "A historical full local PDF must not be treated as reproducible source."
        )
    if phase3_nums != list(range(17, 31)):
        warnings.append("book1_en_phase3.yml is not the expected Cases 17-30 support tranche.")

    print()
    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print("\nRESULT: FAIL")
        return 2
    if args.require_canonical_30 and prod_nums != expected_30:
        print("\nRESULT: BLOCKED - canonical renderer-ready 30-mission master not complete")
        return 3

    print("\nRESULT: PASS WITH KNOWN LAUNCH GAP" if warnings else "\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
