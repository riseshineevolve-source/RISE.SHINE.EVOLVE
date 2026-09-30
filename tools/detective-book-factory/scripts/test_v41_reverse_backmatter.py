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
    index = {"title": 1, "page_count": 146, "support_divider": 110}
    for i, key in enumerate(rbm.HINT_KEYS, start=111):
        index[key] = i
    for n in range(1, 31):
        index[f"{n:02d}_solution"] = 116 + n
    return index


def test_contract() -> None:
    index = synthetic_index()
    sequence = rbm.forward_source_page_sequence(index)
    assert sequence[:110] == list(range(1, 111))
    assert sequence[110:140] == list(range(146, 116, -1))
    assert sequence[140:] == [116, 115, 114, 113, 112, 111]

    physical = rbm.physical_back_to_front_labels(index)
    assert physical[:6] == list(rbm.HINT_KEYS)
    assert physical[6:] == [f"{n:02d}_solution" for n in range(1, 31)]

    remapped = rbm.remap_index(index, sequence)
    assert remapped["support_divider"] == 110
    assert remapped["hints_level_1_cases_01_15"] == 146
    assert remapped["hints_level_3_cases_16_30"] == 141
    assert remapped["01_solution"] == 140
    assert remapped["30_solution"] == 111
    assert remapped["page_count"] == 146


def test_pdf_transform() -> None:
    index = synthetic_index()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source.pdf"
        target = root / "target.pdf"

        writer = PdfWriter()
        for n in range(1, 147):
            page = writer.add_blank_page(width=100, height=200)
            page[NameObject("/RSESourcePage")] = NumberObject(n)
        with source.open("wb") as fh:
            writer.write(fh)

        remapped, contract = rbm.apply_reverse_backmatter(source, target, index)
        reader = PdfReader(str(target))
        assert len(reader.pages) == 146

        # Locked main content and dedicated divider keep source-page order/orientation.
        assert int(reader.pages[0]["/RSESourcePage"]) == 1
        assert int(reader.pages[108]["/RSESourcePage"]) == 109
        assert int(reader.pages[109]["/RSESourcePage"]) == 110
        assert reader.pages[108].rotation % 360 == 0
        assert reader.pages[109].rotation % 360 == 0

        # PDF-forward tail is reversed so physical back-to-front reading is natural.
        assert int(reader.pages[110]["/RSESourcePage"]) == 146
        assert int(reader.pages[139]["/RSESourcePage"]) == 117
        assert int(reader.pages[140]["/RSESourcePage"]) == 116
        assert int(reader.pages[145]["/RSESourcePage"]) == 111
        for page in reader.pages[110:]:
            assert page.rotation % 360 == 180

        assert remapped["01_solution"] == 140
        assert remapped["hints_level_1_cases_01_15"] == 146
        assert contract["support_divider_page"] == 110
        assert contract["locked_main_content_pages"] == [1, 109]
        assert contract["english_frozen"] is False
        assert contract["presentation_only"] is True
        assert len(contract["physical_reading_order"]) == 36
        json.dumps(contract)


if __name__ == "__main__":
    test_contract()
    test_pdf_transform()
    print("PASS: V4.1 reverse-entry backmatter contract")
