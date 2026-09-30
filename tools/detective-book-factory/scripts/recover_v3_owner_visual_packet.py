#!/usr/bin/env python3
"""Recover the exact owner-locked Detective V3 visual packet without transforming bytes.

This is a provenance bridge from the verified owner review ZIP into the book
factory. It refuses any packet, manifest, image hash, filename, or PNG dimension
that differs from the durable V3 owner-visual contract.

It does not render, resize, crop, re-encode, regenerate, or publish anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "content" / "v3_owner_visual_contract.json"
DEFAULT_OUTPUT_DIR = ROOT / "assets" / "production" / "v3_owner_locked"
OWNER_PREFIX = "04_OWNER_VISUALS/"
MANIFEST_MEMBER = OWNER_PREFIX + "owner_visual_manifest.json"
SHA_TABLE_MEMBER = OWNER_PREFIX + "sha_table.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError("asset is not a valid PNG with an IHDR header")
    return struct.unpack(">II", data[16:24])


def load_contract(path: Path) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema") != "hmda-v3-owner-visual-contract-v1":
        raise ValueError("unexpected V3 owner visual contract schema")
    if contract.get("version_family") != "V3":
        raise ValueError("owner visual contract must remain in V3")
    if contract.get("english_frozen") is not False:
        raise ValueError("owner visual recovery must not freeze English")
    if contract.get("policy", {}).get("exact_bytes_required") is not True:
        raise ValueError("owner visual contract must require exact bytes")
    return contract


def verify_owner_manifest(manifest: dict, contract: dict) -> None:
    if manifest.get("owner_locked") is not True:
        raise ValueError("packet manifest is not owner-locked")
    if manifest.get("case03_difference_count") != contract["case03"]["difference_count"]:
        raise ValueError("Case 03 difference count mismatch")
    if manifest.get("case03_spec_status") != contract["case03"]["spec_status"]:
        raise ValueError("Case 03 owner spec status mismatch")
    if manifest.get("book2_visual_owner_locked") is not True:
        raise ValueError("Book 2 archival visual is not owner-locked")

    expected_assets = {
        name: meta["sha256"] for name, meta in contract["assets"].items()
    }
    if manifest.get("assets") != expected_assets:
        raise ValueError("packet asset hash map differs from the durable V3 contract")


def verify_sha_table(table: list[dict], contract: dict) -> None:
    indexed = {item.get("filename"): item for item in table}
    if set(indexed) != set(contract["assets"]):
        raise ValueError("packet SHA table asset set differs from the V3 contract")
    for name, expected in contract["assets"].items():
        row = indexed[name]
        if row.get("source_sha256") != expected["sha256"]:
            raise ValueError(f"SHA table mismatch for {name}")
        if row.get("dimensions") != [expected["width"], expected["height"]]:
            raise ValueError(f"dimension table mismatch for {name}")
        if row.get("embedded_grayscale_pixels_identical") is not True:
            raise ValueError(f"embedded grayscale identity proof missing for {name}")


def recover(packet: Path, contract_path: Path, output_dir: Path) -> dict:
    contract = load_contract(contract_path)

    actual_packet_sha = sha256_file(packet)
    expected_packet_sha = contract["source_packet"]["sha256"]
    if actual_packet_sha != expected_packet_sha:
        raise ValueError(
            f"owner packet SHA-256 mismatch: expected {expected_packet_sha}, got {actual_packet_sha}"
        )

    with zipfile.ZipFile(packet) as archive:
        names = set(archive.namelist())
        required_members = {
            MANIFEST_MEMBER,
            SHA_TABLE_MEMBER,
            *{OWNER_PREFIX + name for name in contract["assets"]},
        }
        missing = sorted(required_members - names)
        if missing:
            raise ValueError(f"owner packet missing required members: {missing}")

        manifest_bytes = archive.read(MANIFEST_MEMBER)
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        verify_owner_manifest(manifest, contract)

        sha_table = json.loads(archive.read(SHA_TABLE_MEMBER).decode("utf-8"))
        verify_sha_table(sha_table, contract)

        verified_assets: dict[str, dict] = {}
        payloads: dict[str, bytes] = {}
        for name, expected in contract["assets"].items():
            data = archive.read(OWNER_PREFIX + name)
            actual_sha = sha256_bytes(data)
            if actual_sha != expected["sha256"]:
                raise ValueError(
                    f"asset SHA-256 mismatch for {name}: expected {expected['sha256']}, got {actual_sha}"
                )
            width, height = png_dimensions(data)
            if (width, height) != (expected["width"], expected["height"]):
                raise ValueError(
                    f"asset dimensions mismatch for {name}: "
                    f"expected {expected['width']}x{expected['height']}, got {width}x{height}"
                )
            payloads[name] = data
            verified_assets[name] = {
                "sha256": actual_sha,
                "width": width,
                "height": height,
                "bytes": len(data),
            }

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in payloads.items():
        target = output_dir / name
        target.write_bytes(data)
        if sha256_file(target) != contract["assets"][name]["sha256"]:
            raise ValueError(f"post-write byte verification failed for {name}")

    # The legacy owner-visual loader consumes this exact shape. Write a canonical
    # JSON serialization after validating that the packet's manifest has the same
    # semantic content and hash map.
    output_manifest = output_dir / "owner_visual_manifest.json"
    output_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    recovery_report = {
        "status": "PASS",
        "schema": "hmda-v3-owner-visual-recovery-v1",
        "version_family": "V3",
        "source_packet_sha256": actual_packet_sha,
        "contract": str(contract_path),
        "output_dir": str(output_dir),
        "assets": verified_assets,
        "owner_manifest": str(output_manifest),
        "exact_bytes_preserved": True,
        "image_transforms_applied": False,
        "english_frozen": False,
        "main_merge_authorized": False,
        "kdp_publication_authorized": False,
    }
    report_path = output_dir / "v3_owner_visual_recovery_report.json"
    report_path.write_text(
        json.dumps(recovery_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return recovery_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = recover(
        args.packet.resolve(),
        args.contract.resolve(),
        args.output_dir.resolve(),
    )
    print("PASS: exact V3 owner visual packet recovered")
    print(f"ASSETS: {len(report['assets'])}/4")
    print(f"OUTPUT: {report['output_dir']}")
    print("English frozen: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
