#!/usr/bin/env python3
"""Deterministic smoke tests for the final owner-audit correction layer."""
from __future__ import annotations

import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import audit_pdf_grayscale as grayscale
import build_owner_review_v41_owner_audit as owner


def _extract(path: Path) -> str:
    return "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def test_identity_and_case30_contract(work: Path) -> None:
    original = owner._ORIGINAL_BUILD_DATA

    def fake_build_data(*_args, **_kwargs):
        data = {
            "opening": {
                "id_card": {"name_label": "DETECTIVE NAME / CALL SIGN"},
                "acceptance_letter": {"note": "Write your call sign."},
            },
            "missions": [
                {
                    "number": 30,
                    "signal_log": {"reader_move": "Use the same call sign on the certificate."},
                    "finale": {
                        "stages": [
                            {
                                "id": "DETECTIVE",
                                "prompt": "Write the name printed on your Detective ID.",
                                "answer": "READER-WRITTEN NAME",
                            }
                        ]
                    },
                    "hints": [
                        "For DETECTIVE, use the call sign on your one Field Detective ID."
                    ],
                    "solution_steps": [
                        "Use the call sign already written on your single Field Detective ID."
                    ],
                }
            ],
        }
        return data, {}, {}, {}

    owner._ORIGINAL_BUILD_DATA = fake_build_data
    try:
        data, *_ = owner._patched_build_data(None)
    finally:
        owner._ORIGINAL_BUILD_DATA = original

    card = data["opening"]["id_card"]
    assert card["name_label"] == "DETECTIVE NAME"
    assert card["call_sign_label"] == "OFFICIAL CALL SIGN"
    assert card["case_wall_label"] == "CASE WALL / EVIDENCE LOG // P. 009"
    assert "OFFICIAL CALL SIGN" in data["opening"]["acceptance_letter"]["note"]

    case30 = data["missions"][0]
    stage = case30["finale"]["stages"][0]
    assert stage["prompt"] == "Write your OFFICIAL CALL SIGN from your Field Detective ID."
    assert stage["answer"] == "READER-WRITTEN OFFICIAL CALL SIGN"
    assert "OFFICIAL CALL SIGN" in case30["signal_log"]["reader_move"]
    assert "OFFICIAL CALL SIGN" in case30["hints"][0]
    assert "OFFICIAL CALL SIGN" in case30["solution_steps"][0]
    assert data["production_state"]["owner_audit_identity_contract"]["field_slot"] == "06"
    nav = data["production_state"]["owner_audit_navigation_contract"]
    assert nav["how_to_page"] == 8
    assert nav["case_wall_evidence_log_page"] == 9
    assert nav["reverse_support_instruction"] == "STOP_TURN_UPSIDE_DOWN_OPEN_FROM_BACK"
    assert nav["case_pages_shifted"] is False
    assert nav["pagination_changed"] is False

    path = work / "identity.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    owner.id_page_owner_audit(c, {"opening": {"id_card": {}}}, 1)
    c.save()
    text = _extract(path)
    assert "DETECTIVE NAME" in text
    assert "OFFICIAL CALL SIGN" in text
    assert "06" in text
    assert "DETECTIVE NAME / CALL SIGN" not in text
    assert "SIGNATURE" not in text
    assert "CASE WALL / EVIDENCE LOG" in text
    assert "P. 009" in text


def test_front_navigation_surfaces(work: Path) -> None:
    how_to = work / "how_to.pdf"
    c = canvas.Canvas(str(how_to), pagesize=letter)
    owner.how_to_page_owner_audit(c, {}, 8)
    c.save()
    text = _extract(how_to)
    assert "WORK FORWARD. GET HELP FROM THE BACK." in text
    assert "CASE WALL / EVIDENCE LOG" in text
    assert "p. 009" in text
    assert "STOP." in text
    assert "Turn this book upside down" in text
    assert "open it from the BACK" in text
    assert "Hint Vault and Solutions" in text
    assert "HINT 1 = nudge" in text

    wall = work / "case_wall.pdf"
    c = canvas.Canvas(str(wall), pagesize=letter)
    owner.case_wall_page_owner_audit(c, {}, 9)
    c.save()
    wall_text = _extract(wall)
    assert "CASE WALL / EVIDENCE LOG" in wall_text
    assert "VERIFIED FACTS" in wall_text
    assert "SIGNAL CODES" in wall_text
    assert "OPEN QUESTIONS" in wall_text
    assert "CROSS-CASE LINKS" in wall_text
    assert "IF A LATER FILE SAYS CHECK THE WALL, THIS IS THE WALL." in wall_text


def test_certificate_and_signal_presentation(work: Path) -> None:
    path = work / "certificate.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    owner.certificate_page_owner_audit(
        c,
        {"certificate": {"note": "INTERNAL META COPY MUST NEVER RENDER"}},
        1,
    )
    c.save()
    text = _extract(path)
    assert "OFFICIAL CALL SIGN" in text
    assert "INTERNAL META COPY MUST NEVER RENDER" not in text
    assert "FIELD SLOT 06 CERTIFIED" in text

    signal = work / "archive_signal.pdf"
    c = canvas.Canvas(str(signal), pagesize=letter)
    owner.archive_signal_panel_owner_audit(
        c,
        {"code": "ARCH-02", "status": "VERIFIED"},
        {"number": 2},
        40,
        740,
        530,
        132,
    )
    c.showPage()
    c.save()
    signal_text = _extract(signal)
    assert "CASE FILE" in signal_text
    assert "ARCHIVE" in signal_text
    assert "02" in signal_text
    assert "CASE → SIGNAL CODE → VERIFIED STATUS" in signal_text


def test_grayscale_fail_closed(work: Path) -> None:
    good = work / "good.pdf"
    c = canvas.Canvas(str(good), pagesize=letter)
    c.setFillGray(0.4)
    c.rect(40, 700, 120, 30, fill=1, stroke=0)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(40, 670, "gray")
    c.save()
    report = grayscale.audit_pdf_grayscale(good)
    assert report["status"] == "PASS"
    assert report["grayscale_only"] is True

    bad = work / "bad.pdf"
    c = canvas.Canvas(str(bad), pagesize=letter)
    c.setFillColorRGB(1, 0, 0)
    c.rect(40, 700, 120, 30, fill=1, stroke=0)
    c.save()
    try:
        grayscale.audit_pdf_grayscale(bad)
    except ValueError as exc:
        assert "not grayscale-only" in str(exc)
    else:
        raise AssertionError("Chromatic PDF must fail the grayscale audit")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hmda-v41-owner-audit-test-") as tmp:
        work = Path(tmp)
        test_identity_and_case30_contract(work)
        test_front_navigation_surfaces(work)
        test_certificate_and_signal_presentation(work)
        test_grayscale_fail_closed(work)
    print("PASS: V4.1 owner-audit corrections + navigation + grayscale fail-closed contract")


if __name__ == "__main__":
    main()
