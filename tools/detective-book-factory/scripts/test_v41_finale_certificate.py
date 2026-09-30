#!/usr/bin/env python3
"""Deterministic contract test for V4.1 finale/certificate presentation."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from reportlab.pdfgen import canvas
from pypdf import PdfReader

import build_owner_review_v4 as v4
import build_owner_review_v41_finale as fc
import build_owner_review_v41_premium as premium

rb = v4.rb


def test_render_smoke() -> None:
    data = {
        "characters": {
            "dilo": {"name": "Dilo"},
            "luli": {"name": "Luli"},
            "alio": {"name": "Alio"},
            "bibi": {"name": "Grandma Bibi"},
        },
        "finale_sections": [
            {"heading": f"Section {i}", "body": "Canonical explanation stays unchanged."}
            for i in range(1, 8)
        ],
        "finale_chat": [
            {"speaker": "dilo", "text": "The secret system is real. May I look pleased?"},
            {"speaker": "luli", "text": "Yes. Keep the imaginary delivery van out of the report."},
            {"speaker": "alio", "text": "Retired with honours."},
            {"speaker": "bibi", "text": "Please let the archive enjoy one quiet minute."},
        ],
        "certificate": {
            "heading": "DETECTIVE ACADEMY // FIELD CERTIFICATION",
            "awarded_to_label": "AWARDED TO",
            "call_sign_label": "OFFICIAL CALL SIGN",
            "achievement": "FOR SOLVING THE MYSTERY OF ROOM ZERO BY FOLLOWING THE EVIDENCE ALL THE WAY TO THE TRUTH.",
            "rank": "CERTIFIED FIELD DETECTIVE // DETECTIVE SIX",
            "case_status": "ROOM ZERO // CLOSED",
            "signed_by": "Happy Makers Detective Academy",
            "archive_confirmation": "BIBI // ARCHIVE MENTOR",
            "note": "Use the call sign from your Field Detective ID. This certificate records achievement; it is not another recruit card.",
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "smoke.pdf"
        c = canvas.Canvas(str(out), pagesize=(rb.PAGE_W, rb.PAGE_H), pageCompression=1)
        fc.finale_page_v41(c, data, {"number": 30}, 107)
        fc.certificate_page_v41(c, data, 108)
        c.save()
        reader = PdfReader(str(out))
        assert len(reader.pages) == 2
        text0 = reader.pages[0].extract_text()
        text1 = reader.pages[1].extract_text()
        assert "ROOM ZERO" in text0
        assert "CASE CLOSED" in text0
        assert "FIELD CERTIFICATION" in text1
        assert "DETECTIVE SIX" in text1
        assert "SLOT 06 EARNED" in text1


def test_wrapper_patches_only_during_delegate() -> None:
    original_finale = v4.finale_page
    original_certificate = v4.certificate_page
    original_main = premium.main
    original_argv = list(sys.argv)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "owner-review.pdf"
        manifest = Path(tmp) / fc.MANIFEST_NAME

        def fake_main() -> None:
            assert v4.finale_page is fc.finale_page_v41
            assert v4.certificate_page is fc.certificate_page_v41
            manifest.write_text(
                json.dumps(
                    {
                        "revision": "v4.1",
                        "english_frozen": False,
                        "premium_polish": {
                            "logic_changed": False,
                            "pagination_changed": False,
                        },
                    }
                ),
                encoding="utf-8",
            )

        try:
            premium.main = fake_main
            sys.argv = ["build_owner_review_v41_finale.py", "--output", str(out)]
            fc.main()
        finally:
            premium.main = original_main
            sys.argv = original_argv

        assert v4.finale_page is original_finale
        assert v4.certificate_page is original_certificate

        packet = json.loads(manifest.read_text(encoding="utf-8"))
        assert packet["english_frozen"] is False
        finale = packet["premium_polish"]["finale_presentation"]
        certificate = packet["premium_polish"]["certificate_presentation"]
        assert finale["status"] == "INTEGRATED"
        assert finale["style"] == fc.FINALE_STYLE
        assert finale["canonical_sections_changed"] is False
        assert finale["room_zero_mechanism_changed"] is False
        assert finale["pagination_changed"] is False
        assert certificate["status"] == "INTEGRATED"
        assert certificate["style"] == fc.CERTIFICATE_STYLE
        assert certificate["achievement_copy_changed"] is False
        assert certificate["detective_six_premise_changed"] is False
        assert certificate["pagination_changed"] is False


if __name__ == "__main__":
    test_render_smoke()
    test_wrapper_patches_only_during_delegate()
    print("PASS: V4.1 finale / certificate presentation contract")
