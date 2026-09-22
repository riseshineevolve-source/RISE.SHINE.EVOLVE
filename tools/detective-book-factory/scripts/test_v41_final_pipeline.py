#!/usr/bin/env python3
"""Deterministic smoke test for complete V4.1 artifact finalization."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject
import yaml

import apply_v41_reverse_backmatter as rbm
import build_owner_review_v41_final as finalizer


def synthetic_index() -> dict:
    index = {"title": 1, "page_count": 145, "26_brief": 86, "26_puzzle": 87}
    for i, key in enumerate(rbm.HINT_KEYS, start=110):
        index[key] = i
    for n in range(1, 31):
        index[f"{n:02d}_solution"] = 115 + n
    return index


def test_case26_lookup_master() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        master_path = root / "master.yml"
        overrides_path = root / "overrides.yml"
        output_path = root / "lookup-master.yml"

        spatial_cases = {2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25}
        missions = []
        for n in range(1, 31):
            mission = {
                "number": n,
                "type": "spatial" if n in spatial_cases else "guided",
                "hints": [f"Case {n} hint one", f"Case {n} hint two", f"Case {n} hint three"],
            }
            missions.append(mission)

        master_path.write_text(
            yaml.safe_dump({
                "missions": missions,
                "story_spine": {"beats": []},
                "production_state": {},
            }, sort_keys=False),
            encoding="utf-8",
        )
        overrides_path.write_text(
            yaml.safe_dump({
                "production": {"compact_cases": [], "artifact_cases": []},
                "cases": {},
            }, sort_keys=False),
            encoding="utf-8",
        )

        refs = finalizer.prepare_case26_lookup_master(
            master_path, overrides_path, output_path
        )
        assert len(refs) == 14
        assert [item["case"] for item in refs] == sorted(spatial_cases)

        prepared = yaml.safe_load(output_path.read_text(encoding="utf-8"))
        case26 = next(m for m in prepared["missions"] if int(m["number"]) == 26)
        hint = case26["hints"][0]
        assert hint.startswith("Case 26 hint one\n\nMAP LOOKUP //")
        for item in refs:
            assert f"Case {item['case']:02d} p. {item['page']}" in hint
        assert prepared["production_state"]["case26_lookup_scope"] == "HINT_LEVEL_1_ONLY"
        assert prepared["production_state"]["case26_lookup_changes_logic"] is False
        assert case26["hints"][1] == "Case 26 hint two"
        assert case26["hints"][2] == "Case 26 hint three"


def test_finalizer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "upright.pdf"
        final = root / "final.pdf"
        index_path = root / finalizer.INDEX_NAME
        manifest_path = root / finalizer.MANIFEST_NAME
        contract_path = root / finalizer.REVERSE_CONTRACT_NAME

        writer = PdfWriter()
        for n in range(1, 146):
            page = writer.add_blank_page(width=100, height=200)
            page[NameObject("/RSESourcePage")] = NumberObject(n)
        with source.open("wb") as fh:
            writer.write(fh)

        index_path.write_text(json.dumps(synthetic_index()), encoding="utf-8")
        manifest_path.write_text(
            json.dumps({
                "revision": "v4.1",
                "pages": 145,
                "pdf_sha256": finalizer.sha256(source),
                "owner_visual_gate": {"status": "OWNER_GATE_PENDING"},
                "english_frozen": False,
            }),
            encoding="utf-8",
        )

        manifest = finalizer.finalize_rendered_artifact(
            source, final, index_path, manifest_path, contract_path
        )

        reader = PdfReader(str(final))
        assert len(reader.pages) == 145
        assert int(reader.pages[108]["/RSESourcePage"]) == 109
        assert int(reader.pages[109]["/RSESourcePage"]) == 145
        assert int(reader.pages[144]["/RSESourcePage"]) == 110
        assert reader.pages[109].rotation % 360 == 180
        assert reader.pages[144].rotation % 360 == 180

        remapped = json.loads(index_path.read_text(encoding="utf-8"))
        assert remapped["26_brief"] == 86
        assert remapped["26_puzzle"] == 87
        assert remapped["26_solution"] == 114
        assert remapped["hints_level_1_cases_01_15"] == 145

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract["english_frozen"] is False
        assert contract["presentation_only"] is True
        assert manifest["english_frozen"] is False
        assert manifest["pdf_sha256"] == finalizer.sha256(final)
        assert manifest["reverse_entry"]["integrated"] is True
        assert manifest["owner_visual_gate"]["status"] == "OWNER_GATE_PENDING"


if __name__ == "__main__":
    test_case26_lookup_master()
    test_finalizer()
    print("PASS: complete V4.1 final artifact pipeline contract")
