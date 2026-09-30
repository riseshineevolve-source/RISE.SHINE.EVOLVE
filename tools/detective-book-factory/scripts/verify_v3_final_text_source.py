#!/usr/bin/env python3
"""Fail-closed provenance and invariant checks for the Detective Academy V3 final text.

This verifier deliberately validates the exact owner-authorized text source only.
It does not infer, rewrite, synthesize, or approve evidence artwork. Evidence
hydration remains a separate production gate.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "DETECTIVE_ACADEMY_BOOK1_TEXT_GOLD_MASTER_V3.md"

EXPECTED_BLOB_SHA1 = "8685f8e561d0bfb3837445b72b4d6f799a9a48f2"
EXPECTED_SOURCE_COMMIT = "e136e94402c8f870f3d9221b7047c1406cbec813"
EXPECTED_CASE26_MAPS = [2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25]


class VerificationError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def exact_case_sequence(text: str, pattern: str, label: str) -> None:
    found = [int(value) for value in re.findall(pattern, text, flags=re.MULTILINE)]
    expected = list(range(1, 31))
    require(found == expected, f"{label}: expected cases 01-30 exactly once in order; got {found}")


def section_between(text: str, start: str, end: str | None) -> str:
    require(start in text, f"missing section marker: {start}")
    section = text.split(start, 1)[1]
    if end is not None:
        require(end in section, f"missing section end marker after {start}: {end}")
        section = section.split(end, 1)[0]
    return section


def verify() -> dict[str, object]:
    require(SOURCE.is_file(), f"missing canonical V3 source snapshot: {SOURCE}")
    # Git's canonical blob is LF; a Windows checkout may materialize CRLF.
    # Normalize only line endings before checking the exact repository blob.
    data = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    blob = git_blob_sha1(data)
    require(
        blob == EXPECTED_BLOB_SHA1,
        f"canonical V3 blob drift: expected {EXPECTED_BLOB_SHA1}, got {blob}",
    )
    text = data.decode("utf-8")

    require(
        "FINAL PRE-CODEX TEXT MASTER FOR PRODUCTION INTEGRATION" in text,
        "V3 source does not identify itself as the final production-integration text master",
    )
    require(
        "English remains **NOT FROZEN**" in text,
        "English freeze state drifted from the authorized V3 source",
    )

    front = section_between(text, "# FRONT MATTER // LOCKED READER PAGES 1-10", "# ACT 1 // SOMETHING IS OFF")
    require(
        front.index("## PAGE 3 // THE BLACK ENVELOPE") < front.index("## YOUR SQUAD"),
        "front-matter order drift: the black-envelope cold open must precede YOUR SQUAD",
    )
    black_envelope = section_between(front, "## PAGE 3 // THE BLACK ENVELOPE", "## YOUR SQUAD")
    require("YOUR SQUAD" not in black_envelope, "Page 3 cold open must not contain squad heading")
    require("WILL YOU CLAIM IT?" in black_envelope, "Page 3 cold open lost WILL YOU CLAIM IT?")
    require(
        "IF ACCEPTED: REPORT TO THE CASE TABLE." not in black_envelope,
        "Page 3 cold open must end before Academy/team explanation",
    )

    main = section_between(text, "# ACT 1 // SOMETHING IS OFF", "# HINT VAULT // LEVEL 1")
    exact_case_sequence(main, r"^## CASE (\d{2}) //", "main reader cases")

    level1 = section_between(text, "# HINT VAULT // LEVEL 1", "# HINT VAULT // LEVEL 2")
    level2 = section_between(text, "# HINT VAULT // LEVEL 2", "# HINT VAULT // LEVEL 3")
    level3 = section_between(text, "# HINT VAULT // LEVEL 3", "# SOLUTION FILES")
    for index, section in enumerate((level1, level2, level3), start=1):
        exact_case_sequence(section, r"^## CASE (\d{2})\s*$", f"Hint Vault Level {index}")

    solutions = section_between(text, "# SOLUTION FILES", None)
    exact_case_sequence(solutions, r"^## CASE (\d{2}) //", "Solution Files")

    # Owner-locked reader logic and narrative invariants.
    required_fragments = {
        "Max/Cup clarification": "Max signed it out for a Hall demonstration - but his return form was never completed.",
        "Case 03 exact-ten objective": "FIND ALL 10 DIFFERENCES between Photo A and Photo B.",
        "Case 05 six-symbol solution": "**ANSWER:** BALL -> STAR -> BOLT -> HEART -> KEY -> MOON",
        "Case 21 recovered message": "THE ANSWER IS IN WHAT YOU LEAVE EMPTY",
        "Case 26 meta message": "CHECK THE OLD MAP",
        "Rule Zero": "ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.",
        "Case 29 access coordinate": "D3",
        "Book 2 archive hook": "# ARCHIVE FILE 001 // STILL OPEN",
        "final field role wording": "sixth field detective",
        "Case 03 to 06 017/071 payoff": "**017** is a current storage reference; **071** belongs to the retired intake series kept in Heritage.",
        "Case 25 to 27 restoration payoff": "Inside are transparent overlay sleeves and old alignment clips borrowed long ago from **Archive Restoration**",
        "Bibi trainee route-note proof": "**ROUTE NOTE AUTHOR: BIBI // TRAINEE ARCHIVE TEAM**",
        "Case 24 Rule Zero callback": "The arrow shouts. The mud explains.",
        "Book 2 triangle callback": "difference number eight - the same three-part shape is hiding in plain sight.",
        "Case 06 Uma incident bridge": "I'm glad you're here. Something very odd happened.",
        "Case 07 spoon/label closure": "Nothing was stolen; the **dragon-tooth label card** was the thing that moved.",
        "owner website CTA": "Come visit us online - we saved a cozy spot just for you:",\n        "owner Facebook CTA": "Rise.Shine.Evolve.Learning Hub.",\n        "owner squad opener": "New recruit at the Case Table.",
        "Case 03 progress tracker": "Color one question mark for each difference you find.",
        "upright Hint Vault wording": "Need help? Turn to the Hint Vault at the back, behind the **STOP // HINT VAULT** divider.",
        "Case 13 parrot closure": "Nini's follow-up closes the parrot file: the phrase came from an ordinary rehearsal cue repeated near the Stage Wing.",
        "Case 22 witness-aligned story": "Her Rehearsal Room is the last clean snapshot of who was beside her before the instrument cases were moved.",
        "parcel handoff wording": "After Reception confirms the handoff with Nori's room companion, staff finally open the parcel.",
        "Case 28 damaged rule": "ZERO ____________. NOTICE FIRST. THEORIZE SECOND.",
    }
    for label, fragment in required_fragments.items():
        require(fragment in text, f"missing locked V3 invariant: {label}")

    # Case 03 must expose exactly the locked ten solution differences.
    case03_solution = section_between(
        solutions,
        "## CASE 03 // LULI'S LOOK-TWICE FILE",
        "## CASE 04 //",
    )
    numbered_differences = re.findall(r"^(\d+)\.\s+", case03_solution, flags=re.MULTILINE)
    require(
        numbered_differences == [str(i) for i in range(1, 11)],
        f"Case 03 solution must contain exactly numbered differences 1-10; got {numbered_differences}",
    )

    # Case 05 must be the six-symbol production contract, not the historical four-symbol puzzle.
    case05_main = section_between(main, "## CASE 05 //", "## CASE 06 //")
    require("Use each of the six symbols exactly once." in case05_main, "Case 05 six-symbol rule missing")
    require("123456" in case05_main, "Case 05 title no longer signals the six-symbol version")

    # Case 21 causal message and physical reconstruction order must both survive.
    case21_solution = section_between(solutions, "## CASE 21 //", "## CASE 22 //")
    require("**ANSWER:** B → D → A → C;" in case21_solution, "Case 21 physical scrap order B → D → A → C missing")
    require(
        "THE ANSWER IS IN WHAT YOU LEAVE EMPTY" in case21_solution,
        "Case 21 recovered sentence missing from Solution File",
    )

    # Case 26 uses exactly fourteen route-selected spatial maps; Case 01 is the intake trigger only.
    lookup_match = re.search(r"^MAP LOOKUP // Cases ([^.]+)\.", level1, flags=re.MULTILINE)
    require(lookup_match is not None, "Case 26 MAP LOOKUP line missing from Hint Vault Level 1")
    map_numbers = [int(value) for value in re.findall(r"\d{2}", lookup_match.group(1))]
    require(
        map_numbers == EXPECTED_CASE26_MAPS,
        f"Case 26 map extraction set drifted: expected {EXPECTED_CASE26_MAPS}, got {map_numbers}",
    )
    require(1 not in map_numbers, "Case 01 must not enter the Case 26 fourteen-map extraction set")

    # Case 01 reader-facing aliases must remain consistent through hints and solution support.
    case01_hints = "\n".join(
        section_between(section, "## CASE 01", "## CASE 02")
        for section in (level1, level2, level3)
    )
    case01_solution = section_between(solutions, "## CASE 01 //", "## CASE 02 //")
    for alias in ("QUILL", "MORSE", "PIP", "KNOX"):
        require(alias in case01_hints.upper(), f"Case 01 alias {alias} missing from Hint Vault")
        require(alias in case01_solution.upper(), f"Case 01 alias {alias} missing from Solution File")

    # The master contains placeholders by design; they are a production hydration gate, not release evidence.
    placeholder_count = text.count("### PUZZLE / EVIDENCE SURFACE")
    require(
        placeholder_count > 0,
        "expected evidence placeholders are absent; do not silently treat prose as evidence source truth",
    )

    return {
        "status": "PASS",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "blob_sha1": blob,
        "main_cases": 30,
        "hint_levels": 3,
        "solution_files": 30,
        "case03_differences": 10,
        "case26_map_count": len(EXPECTED_CASE26_MAPS),
        "evidence_placeholders": placeholder_count,
        "english_frozen": False,
    }


def main() -> int:
    result = verify()
    print("PASS: Detective Academy exact V3 final-text source verified")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
