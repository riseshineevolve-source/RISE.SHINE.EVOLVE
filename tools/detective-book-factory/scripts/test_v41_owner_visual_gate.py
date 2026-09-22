#!/usr/bin/env python3
"""Deterministic checks for the V4.1 owner-gated visual integration contract."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import build_owner_review_v41 as v41


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_packet(root: Path, *, owner_locked: bool, spec_status: str, count: int,
                  book2_locked: bool) -> Path:
    assets = {}
    for name in sorted(v41.EXPECTED_OWNER_ASSETS):
        path = root / name
        path.write_bytes(("fixture:" + name).encode("utf-8"))
        assets[name] = _sha(path)
    manifest = {
        "owner_locked": owner_locked,
        "case03_difference_count": count,
        "case03_spec_status": spec_status,
        "book2_visual_owner_locked": book2_locked,
        "assets": assets,
    }
    path = root / "owner_visual_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _expect_failure(path: Path) -> None:
    try:
        v41._load_owner_visual_packet(path)
    except (ValueError, FileNotFoundError):
        return
    raise AssertionError(f"Expected owner visual gate to reject {path}")


def main() -> None:
    pending = v41._load_owner_visual_packet(None)
    assert pending["status"] == "OWNER_GATE_PENDING"
    assert pending["integrated"] is False
    assert pending["owner_locked"] is False
    assert pending["case03_difference_count_required"] == 10

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)

        _expect_failure(_write_packet(
            root,
            owner_locked=False,
            spec_status=v41.OWNER_CASE03_SPEC_STATUS,
            count=10,
            book2_locked=True,
        ))
        _expect_failure(_write_packet(
            root,
            owner_locked=True,
            spec_status="EXPLORATORY_NOT_OWNER_LOCKED",
            count=10,
            book2_locked=True,
        ))
        _expect_failure(_write_packet(
            root,
            owner_locked=True,
            spec_status=v41.OWNER_CASE03_SPEC_STATUS,
            count=9,
            book2_locked=True,
        ))
        _expect_failure(_write_packet(
            root,
            owner_locked=True,
            spec_status=v41.OWNER_CASE03_SPEC_STATUS,
            count=10,
            book2_locked=False,
        ))

        approved = _write_packet(
            root,
            owner_locked=True,
            spec_status=v41.OWNER_CASE03_SPEC_STATUS,
            count=10,
            book2_locked=True,
        )
        packet = v41._load_owner_visual_packet(approved)
        assert packet["status"] == "OWNER_LOCKED_ASSETS_VALIDATED"
        assert packet["integrated"] is True
        assert packet["case03_difference_count"] == 10

    print("PASS: V4.1 owner visual gate rejects exploratory art and accepts only explicit owner-locked assets")


if __name__ == "__main__":
    main()
