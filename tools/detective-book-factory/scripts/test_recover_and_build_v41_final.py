#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

import recover_and_build_v41_final as bridge
import recover_v4_embedded_spatial_assets as recovery

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "content/book1_en_master.yml"
OVERRIDES = ROOT / "content/book1_v4_overrides.yml"
LOCKED_V4_SHA256 = "1b2b908763e76b42321035fb1faf91056bd2a8a1301ea0a2f84944c91287e1cb"


def main() -> None:
    assert recovery.LOCKED_V4_PDF_SHA256 == LOCKED_V4_SHA256

    with tempfile.TemporaryDirectory(prefix="hmda-v41-recovery-bridge-test-") as tmp:
        work = Path(tmp)
        recovery_master, recovery_index, page_index = bridge.build_recovery_index(
            MASTER, OVERRIDES, work
        )

        assert recovery_master.is_file()
        assert recovery_index.is_file()
        assert page_index["page_count"] == 145

        stored_index = json.loads(recovery_index.read_text(encoding="utf-8"))
        assert stored_index == page_index

        master_data = yaml.safe_load(recovery_master.read_text(encoding="utf-8"))
        assert isinstance(master_data, dict)
        assert isinstance(master_data.get("missions"), list)
        assert len(master_data["missions"]) == 30

        spatial_case_numbers = sorted(
            int(mission["number"])
            for mission in master_data["missions"]
            if mission.get("spatial_source_id")
        )
        assert len(spatial_case_numbers) == 15

        map_keys = [f"{number:02d}_map" for number in spatial_case_numbers]
        solution_keys = [f"{number:02d}_solution" for number in spatial_case_numbers]
        assert all(key in page_index for key in map_keys)
        assert all(key in page_index for key in solution_keys)

        spatial_pages = [page_index[key] for key in map_keys + solution_keys]
        assert len(spatial_pages) == 30
        assert len(set(spatial_pages)) == 30
        assert all(isinstance(page, int) and 1 <= page <= 145 for page in spatial_pages)

    print("PASS: locked V4 recovery -> V4.1 final-build bridge contract")


if __name__ == "__main__":
    main()
