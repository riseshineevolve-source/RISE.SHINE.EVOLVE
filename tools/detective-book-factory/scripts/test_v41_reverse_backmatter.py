#!/usr/bin/env python3
"""Deterministic tests for the V4.1 reverse-entry physical back matter."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject

import apply_v41_reverse_backmatter as rbm


def synthetic_index() -> dict:
    index = {"title": 1, "page_count": 145}
    for i, key in enumerate(rbm.HINT_KEYS, start=110):
        index[key] = i
    for n in range(1, 31):
        index[f"{n:02d}_solution"] = 115 + n
    return index


def test_contract() -> None:
    index = synthetic_index()
    sequence = rbm.forward_source_page_sequence(index)
    assert sequence[:109] == list(range(1, 110))
    assert sequence[109:139] == list(range(145, 115, -1))
    assert sequence[139:] == [115, 114, 113, 112, 111, 110]

    physical = rbm.physical_back_to_front_labels(index)
    assert physical[:6] == list(rbm.HINT_KEYS)
    assert physical[6:] == [f"{n:02d}_solution" for n in range(1, 31)]

    remapped = rbm.remap_index(index, sequence)
    assert remapped["hints_level_1_cases_01_15"] == 145
    assert remapped["hints_level_3_cases_16_30"] == 140
    assert remapped["01_solution"] == 139
    assert remapped["30_solution"] == 110
    assert remapped["page_count"] == 145


def test_pdf_transform() -> None:
    index = synthetic_index()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source.pdf"
        target = root / "target.pdf"

        writer = PdfWriter()
        for n in range(1, 146):
            page = writer.add_blank_page(width=100, height=200)
            page[NameObject("/RSESourcePage")] = NumberObject(n)
        with source.open("wb") as fh:
            writer.write(fh)

        remapped, contract = rbm.apply_reverse_backmatter(source, target, index)
        reader = PdfReader(str(target))
        assert len(reader.pages) == 145

        # Front section keeps source-page order and orientation.
        assert int(reader.pages[0]["/RSESourcePage"]) == 1
        assert int(reader.pages[108]["/RSESourcePage"]) == 109
        assert reader.pages[108].rotation % 360 == 0

        # PDF-forward tail is reversed so physical back-to-front reading is natural.
        assert int(reader.pages[109]["/RSESourcePage"]) == 145
        assert int(reader.pages[138]["/RSESourcePage"]) == 116
        assert int(reader.pages[139]["/RSESourcePage"]) == 115
        assert int(reader.pages[144]["/RSESourcePage"]) == 110
        for page in reader.pages[109:]:
            assert page.rotation % 360 == 180

        assert remapped["01_solution"] == 139
        assert remapped["hints_level_1_cases_01_15"] == 145
        assert contract["english_frozen"] is False
        assert contract["presentation_only"] is True
        assert len(contract["physical_reading_order"]) == 36
        json.dumps(contract)


if __name__ == "__main__":
    test_contract()
    test_pdf_transform()
    print("PASS: V4.1 reverse-entry backmatter contract")
