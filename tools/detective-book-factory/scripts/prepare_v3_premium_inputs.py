#!/usr/bin/env python3
"""Stage the exact private inputs for the V3 premium renderer.

The source packet and scanner squad variant are supplied privately. This
script verifies every byte before writing and never replaces a different file.
No private asset or generated PDF belongs in Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER_CONTRACT = ROOT / "content/v3_owner_visual_contract.json"
SPATIAL_CONTRACT = ROOT / "content/v3_locked_spatial_evidence_contract.json"
MASTER_SHA256 = "0a61b726e6335cc731f114749db632b6b0a50f2a8da76ef763a8961e066feacc"
SQUAD_SCANNER_SHA256 = "9129bfa03c7f347e27ae9b98c431395916b0c9cc12924b158116360a4869620e"


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest()


def prepare(packet: Path, evidence_master: Path, squad_variant: Path,
            check_only: bool = False) -> dict:
    owner = json.loads(OWNER_CONTRACT.read_text(encoding="utf-8"))
    spatial = json.loads(SPATIAL_CONTRACT.read_text(encoding="utf-8"))
    expected_packet = owner["source_packet"]["sha256"]
    if spatial["source_packet"]["sha256"] != expected_packet:
        raise ValueError("owner and spatial contracts disagree about source packet")
    if sha256(packet) != expected_packet:
        raise ValueError("private owner packet SHA-256 mismatch")
    if sha256(evidence_master) != MASTER_SHA256:
        raise ValueError("audited evidence master SHA-256 mismatch")
    if sha256(squad_variant) != SQUAD_SCANNER_SHA256:
        raise ValueError("approved scanner squad variant SHA-256 mismatch")

    members: dict[str, tuple[Path, str]] = {
        spatial["runtime"]["packet_render_runtime_member"]:
            (ROOT / "dist/hmda_spatial_runtime_v4.json",
             spatial["runtime"]["packet_render_runtime_sha256"]),
    }
    members.update({
        "04_OWNER_VISUALS/" + name:
            (ROOT / "assets/production/v3_owner_locked" / name, meta["sha256"])
        for name, meta in owner["assets"].items()
    })
    members.update({
        "05_MAP_QA/approved_map_rasters/" + name:
            (ROOT / "assets/production/v3_spatial_locked" / name, expected)
        for name, expected in spatial["maps"].items()
    })
    master_target = ROOT / "dist/book1_en_master_owner_review_v4.yml"
    squad_target = ROOT / "assets/production/squad-scanner.png"
    outputs = [*members.values(), (master_target, MASTER_SHA256),
               (squad_target, SQUAD_SCANNER_SHA256)]
    with zipfile.ZipFile(packet) as archive:
        missing = sorted(set(members) - set(archive.namelist()))
        if missing:
            raise ValueError(f"private owner packet is missing {missing}")
        for member, (_target, expected) in members.items():
            if hashlib.sha256(archive.read(member)).hexdigest() != expected:
                raise ValueError(f"packet member hash mismatch: {member}")
        # Finish all checks before touching the workspace. Existing files with
        # different bytes are user work and must never be replaced here.
        for target, expected in outputs:
            if target.exists() and sha256(target) != expected:
                raise ValueError(f"refusing to replace a different local input: {target}")
        if not check_only:
            for member, (target, expected) in members.items():
                if target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
                if sha256(target) != expected:
                    raise ValueError(f"staged member hash mismatch: {target}")
            if not master_target.exists():
                master_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(evidence_master, master_target)
                if sha256(master_target) != MASTER_SHA256:
                    raise ValueError("staged evidence master hash mismatch")
            if not squad_target.exists():
                squad_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(squad_variant, squad_target)
                if sha256(squad_target) != SQUAD_SCANNER_SHA256:
                    raise ValueError("staged scanner squad variant hash mismatch")

    return {
        "status": "PASS",
        "check_only": check_only,
        "packet_sha256": expected_packet,
        "owner_visuals": len(owner["assets"]),
        "spatial_rasters": len(spatial["maps"]),
        "runtime_sha256": spatial["runtime"]["packet_render_runtime_sha256"],
        "evidence_master_sha256": MASTER_SHA256,
        "squad_scanner_sha256": SQUAD_SCANNER_SHA256,
        "input_files": len(outputs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--evidence-master", type=Path, required=True)
    parser.add_argument("--squad-variant", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    result = prepare(args.packet.resolve(), args.evidence_master.resolve(),
                     args.squad_variant.resolve(), args.check_only)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
