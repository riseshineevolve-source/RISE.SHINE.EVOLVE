"""Fail-closed V4 logic/publication gate, reusing the independently enumerated V3 CSP.

The baseline-audit option diagnoses V3; it can never certify a V4 publication.
Changed evidence must have a reviewed exact payload hash below, even if the
unchanged abstract solver still finds one answer. PDF geometry is measured from
the actual final artifact. This tool never substitutes for visual inspection.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import validate_book1_v3_logic as v3

ROOT = Path(__file__).resolve().parents[1]
BASELINE_HASHES = {
    "master": "bd0d8f464097f35073c85cedfb623de59483adf6436bd24e111e282fa2061bb5",
    "runtime": "06bb284162ab62e993c8eee9237c58b67b6b545a425d2b04085725a81d50afc8",
    "pdf": "994db4ec8b2bc4f95e351b40646add51e55bc71b29379217be15b1752a6d6eb8",
}
EVIDENCE_BLOCKS = (
    "tutorial", "visual", "code", "route", "classification", "consistency",
    "timeline_visual", "timeline", "reconstruction", "visual_sequence",
    "checkpoint", "map_overlay", "fact_theory_sort", "finale",
)
# Add only after inspecting the exact changed evidence and documenting why it
# implements the same constraints. There is deliberately no --accept-all flag.
REVIEWED_PUBLICATION_PAYLOADS: dict[int, dict[str, str]] = {
    2: {
        "1af40ed6ab7865b051a898d38caaa732d99811fd481097ad9eb93c00555b477e":
        "Terminology correction only: the locked ON predicate targets the deskchair at C5; teacher desks remain blocked.",
    },
    23: {
        "039f54ce91ef7bac769a933600f5d44450e75c8317693f0f61d1007dbe63bc6b":
        "Grammar correction makes the existing OR bench predicate unambiguous without changing either candidate or answer.",
    },
    30: {
        "e5dd7995c00147a823a7e1b376c777e30506b875839ecac4f199b93001fb1148":
        "Narrative reveal, reader payoff and series hook were rewritten for continuity; all four locked finale stages, prompts and answers are unchanged.",
    },
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def payload_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def publication_payload(mission):
    """Fields that directly encode reader constraints/answers, excluding art paths."""
    out = {key: mission[key] for key in EVIDENCE_BLOCKS if key in mission}
    out["number"] = int(mission["number"])
    out["type"] = mission["type"]
    if mission.get("spatial_source_id"):
        spatial = mission.get("spatial", mission.get("spatial_copy", {}))
        out["spatial_source_id"] = mission["spatial_source_id"]
        out["spatial"] = {key: spatial.get(key) for key in
                          ("clue_cards", "answer", "answer_coordinate", "rows", "columns")}
    if "investigation_rules" in mission:
        out["investigation_rules"] = mission["investigation_rules"]
    return out


def locked_runtime(case):
    """Keep logical geometry, identities, meta roles and answers; discard art paths."""
    return {
        "id": case["id"], "grid": case["grid"], "doors": case["doors"],
        "objects": case["objects"], "rooms": case["rooms"],
        "characters": [{k: p.get(k) for k in
                        ("source_name", "display_name", "gender", "witness_id", "is_owner", "placement")}
                       for p in case["characters"]],
        "source_owner": case["source_owner"], "source_answer": case["source_answer"],
        "meta": case["meta"],
    }


def changed_paths(before, after, prefix=""):
    if isinstance(before, dict) and isinstance(after, dict):
        return [p for k in sorted(before.keys() | after.keys())
                for p in changed_paths(before.get(k), after.get(k), f"{prefix}.{k}".strip("."))]
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [p for i, (a, b) in enumerate(zip(before, after))
                for p in changed_paths(a, b, f"{prefix}[{i}]")]
    return [] if before == after else [prefix]


def publication_checks(data, runtime_cases, baseline_data, baseline_cases):
    issues, reviews = [], {}
    if [int(m["number"]) for m in data["missions"]] != list(range(1, 31)):
        raise ValueError("Publication must contain exactly 30 ordered cases")
    if set(runtime_cases) != set(v3.SPATIAL):
        raise ValueError("Runtime must contain exactly the 15 locked spatial cases")
    for mission in data["missions"]:
        n = int(mission["number"])
        before = publication_payload(baseline_data["missions"][n - 1])
        current = publication_payload(mission)
        digest = payload_sha(current)
        paths = changed_paths(before, current)
        rationale = REVIEWED_PUBLICATION_PAYLOADS.get(n, {}).get(digest)
        reviewed = not paths or bool(rationale)
        reviews[n] = {"payload_sha256": digest, "changed_paths": paths,
                      "reviewed": reviewed, "rationale": rationale or
                      ("Evidence payload unchanged from verified V3 baseline." if not paths else None)}
        if not reviewed:
            issues.append({"case": n, "code": "UNREVIEWED_EVIDENCE_CHANGE", "paths": paths})
        for field in ("title", "hook", "objective", "solution_steps"):
            if not mission.get(field):
                issues.append({"case": n, "code": "MISSING_READER_CONTENT", "field": field})
        if len(mission.get("hints", [])) != 3 or not all(mission.get("hints", [])):
            issues.append({"case": n, "code": "THREE_NONEMPTY_HINTS_REQUIRED"})
        if n not in runtime_cases:
            continue
        case = runtime_cases[n]
        drift = changed_paths(locked_runtime(baseline_cases[n]), locked_runtime(case))
        if drift:
            issues.append({"case": n, "code": "LOCKED_RUNTIME_DRIFT", "paths": drift})
        ids = [p.get("witness_id") for p in case["characters"]]
        if ids != [f"{i:02d}" for i in range(1, len(ids) + 1)]:
            issues.append({"case": n, "code": "WITNESS_IDS_NOT_SEQUENTIAL"})
        clues = mission.get("spatial", {}).get("clue_cards", [])
        if clues != mission.get("spatial_copy", {}).get("clue_cards"):
            issues.append({"case": n, "code": "DUPLICATE_CLUE_CONTENT_DRIFT"})
        # Whole final names are removed first so e.g. Equipment Hall is not
        # mistaken for a legacy partial word. These are publication-only names.
        # Narrative venue words such as "the library system" do not assert a
        # legacy room name. Restrict this check to the actual deduction text.
        readable = json.dumps({k: mission.get(k) for k in
                               ("hints", "solution_steps")}) + " " + " ".join(clues)
        for room in sorted(case["rooms"], key=lambda r: -len(r["final_name"])):
            readable = re.sub(r"\b" + re.escape(room["final_name"]) + r"\b", " ", readable, flags=re.I)
        for room in case["rooms"]:
            if room["source_name"] != room["final_name"] and re.search(
                    r"\b" + re.escape(room["source_name"]) + r"\b", readable, re.I):
                issues.append({"case": n, "code": "LEGACY_ROOM_NAME", "name": room["source_name"]})
        if n == 2 and any(re.search(r"standing on a desk\.", clue, re.I) for clue in clues):
            issues.append({"case": 2, "code": "DESK_VS_DESKCHAIR",
                           "detail": "Printed desk is blocked; locked on-object clue is deskchair at C5."})
        if n == 23 and any("either Ozzy or Pia, who was on a bench" in clue for clue in clues):
            issues.append({"case": 23, "code": "AMBIGUOUS_BENCH_RELATIVE_CLAUSE",
                           "detail": "Bench occupant may be either named person, not exclusively Pia."})
    return issues, reviews


def rect_overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def pdf_evidence_presence(pdf_path, index_path, data):
    """Check essential printed evidence, not merely populated source dictionaries.

    Raster art still needs visual inspection. Timestamps are deliberately vector
    labels in this pipeline, so a missing vector timestamp fails closed.
    """
    import pymupdf
    index = json.loads(index_path.read_text(encoding="utf-8"))
    document = pymupdf.open(pdf_path)
    missions = {int(m["number"]): m for m in data["missions"]}
    errors = []
    start, stop = index["11_brief"], index["12_brief"]
    printed = "\n".join(document[p - 1].get_text() for p in range(start, stop))
    required = sorted(set(re.findall(r"\b\d\d:\d\d\b", json.dumps(missions[11]["classification"]["items"]))))
    missing = [stamp for stamp in required if stamp not in printed]
    if missing:
        errors.append({"case": 11, "code": "MISSING_PRE_SOLUTION_TIMESTAMPS",
                       "pages": list(range(start, stop)), "missing": missing,
                       "detail": "The reader needs the A–D record timestamps before the solution."})
    artifact = index.get("16_artifact")
    answer_year = str(missions[16]["timeline_visual"]["answer"]["year"])
    if artifact and re.search(r"(?m)^\s*" + answer_year + r"\s*$", document[artifact - 1].get_text()):
        errors.append({"case": 16, "code": "ANSWER_YEAR_PRINTED_ON_UNDATED_PHOTO",
                       "page": artifact, "detail": "The supposedly undated photo directly labels its answer year."})
    puzzle = index.get("24_puzzle")
    if puzzle and "TREAD DIRECTION DOES NOT LIE" in document[puzzle - 1].get_text():
        errors.append({"case": 24, "code": "TREAD_TITLE_CONTRADICTS_RULE",
                       "page": puzzle, "detail": "The solution rejects tread direction as proof of movement."})
    return {"status": "PASS" if not errors else "NEEDS WORK", "errors": errors,
            "case11_required_timestamps": required,
            "scope": "Known essential timestamp omissions and direct contradiction/answer-leak regressions; illustrations require separate visual review."}


def map_geometry(pdf_path, index_path, cases):
    import pymupdf
    index = json.loads(index_path.read_text(encoding="utf-8"))
    document = pymupdf.open(pdf_path)
    audit, errors = {}, []
    for n, case in sorted(cases.items()):
        page_no = index.get(f"{n:02d}_map")
        board_no = index.get(f"{n:02d}_brief")
        failures = []
        if not isinstance(page_no, int) or not 1 <= page_no <= len(document):
            errors.append({"case": n, "code": "MAP_PAGE_MISSING"})
            continue
        page = document[page_no - 1]
        spans = [s for b in page.get_text("dict")["blocks"] if b["type"] == 0
                 for line in b["lines"] for s in line["spans"] if s["text"].strip()]
        images = [list(im["bbox"]) for im in page.get_image_info()
                  if im["bbox"][2] - im["bbox"][0] > 300 and im["bbox"][3] - im["bbox"][1] > 300]
        if len(images) != 1:
            errors.append({"case": n, "page": page_no, "code": "UNMODELLED_MAP_IMAGE_GEOMETRY", "images": images})
            continue
        grid = images[0]
        columns = [s for s in spans if re.fullmatch("[A-I]", s["text"].strip())
                   and grid[0] < s["bbox"][0] < grid[2] and grid[1] - 55 < s["bbox"][1] < grid[1]]
        columns.sort(key=lambda s: s["bbox"][0])
        headings = [s for s in spans if "MAP RULES" in s["text"]]
        if len(headings) != 1 or not columns:
            errors.append({"case": n, "page": page_no, "code": "RULES_OR_COORDINATES_MISSING"})
            continue
        rules = [s for s in spans if s not in columns and
                 headings[0]["bbox"][3] <= s["bbox"][1] < grid[1]]
        if not rules:
            errors.append({"case": n, "page": page_no, "code": "RULE_BODY_MISSING"})
            continue
        col_top = min(s["bbox"][1] for s in columns)
        col_bottom = max(s["bbox"][3] for s in columns)
        rule_bottom = max(s["bbox"][3] for s in rules)
        clearance = col_top - rule_bottom
        image_gap = grid[1] - col_bottom
        intersections = [{"rule": r["text"], "column": c["text"]} for r in rules for c in columns
                         if rect_overlap(r["bbox"], c["bbox"])]
        expected_letters = [chr(65 + i) for i in range(case["grid"]["columns"])]
        if [s["text"] for s in columns] != expected_letters:
            failures.append("COLUMN_COORDINATES_INCOMPLETE")
        if clearance < 10 - 0.05:
            failures.append("RULE_TO_COORDINATE_CLEARANCE_UNDER_10PT")
        if image_gap < 6 - 0.05:
            failures.append("COORDINATE_TO_GRID_CLEARANCE_UNDER_6PT")
        if intersections:
            failures.append("RULE_COORDINATE_INTERSECTION")
        for i, column in enumerate(columns):
            expected_x = grid[0] + (i + .5) * (grid[2] - grid[0]) / len(expected_letters)
            if abs(sum(column["bbox"][::2]) / 2 - expected_x) > 2:
                failures.append("COLUMN_NOT_AT_CELL_CENTER")
                break
        row_spans = [s for s in spans if re.fullmatch(r"[1-9]", s["text"])
                     and grid[0] - 35 < s["bbox"][0] < grid[0] and grid[1] < s["bbox"][1] < grid[3]]
        row_spans.sort(key=lambda s: s["bbox"][1])
        if [s["text"] for s in row_spans] != [str(i + 1) for i in range(case["grid"]["rows"])]:
            failures.append("ROW_COORDINATES_INCOMPLETE")
        if min(grid[2] - grid[0], grid[3] - grid[1]) < 6 * 72:
            failures.append("WRITABLE_GRID_UNDER_6_INCHES")
        facing = board_no == page_no - 1 and board_no % 2 == 0 and page_no % 2 == 1
        if not facing:
            failures.append("BOARD_MAP_NOT_FACING")
        for page_key, code in ((f"{n:02d}_brief", "BOARD"), (f"{n:02d}_solution", "SOLUTION")):
            pno = index.get(page_key)
            if not pno or not 1 <= pno <= len(document):
                failures.append(f"{code}_PAGE_MISSING")
                continue
            text = document[pno - 1].get_text()
            for person in case["characters"]:
                if not re.search(r"\b" + re.escape(person["display_name"]) + r"\b", text, re.I):
                    failures.append(f"{code}_MISSING_NAME_{person['display_name']}")
                if not re.search(r"\b" + person["witness_id"] + r"\b", text):
                    failures.append(f"{code}_MISSING_WITNESS_{person['witness_id']}")
        audit[n] = {"page": page_no, "board_page": board_no, "grid_bbox": grid,
                    "rules_bottom": round(rule_bottom, 3), "columns_top": round(col_top, 3),
                    "rules_to_coordinates_pt": round(clearance, 3),
                    "coordinates_to_grid_pt": round(image_gap, 3),
                    "intersection_count": len(intersections), "intersections": intersections,
                    "facing_spread": facing, "failures": failures,
                    "status": "PASS" if not failures else "NEEDS WORK"}
        errors.extend({"case": n, "page": page_no, "code": failure} for failure in failures)
    return {"status": "PASS" if not errors and len(audit) == 15 else "NEEDS WORK",
            "pdf_sha256": sha(pdf_path), "page_index_sha256": sha(index_path),
            "page_count": len(document), "maps": audit, "errors": errors,
            "boundary": "Vector text geometry and raster map placement only; internal map labels, art semantics and contrast require visual inspection."}


def write_ledger(path, data, cases, results, report):
    # Reuse the complete per-case evidence ledger, then add the stricter V4 gate.
    v3.write_ledger(path, data, cases, results, report["bindings"])
    body = path.read_text(encoding="utf-8")
    body = body.replace("Book 1 V3", "Book 1 V4").replace("validate_book1_v3_logic.py", "validate_book1_v4_logic.py")
    body = body.replace("book1_en_master_owner_review_v3.yml", "book1_en_master_owner_review_v4.yml")
    body = body.replace("separate V3 PDF audit", "separate V4 PDF and visual audits")
    intro = ["# HMDA Book 1 V4 — Publication logic ledger", "",
             f"Final V4 publication state: **{report['status']}**. Input mode: **{report['mode']}**.", "",
             "The 30-case enumeration below is not a publication/visual approval. The exact final V4 master, runtime and PDF must pass the gates in the accompanying JSON report. Baseline-only evidence cannot certify V4.", "",
             f"- Encoded case checks: {sum(r['status'] == 'PASS' for r in results.values())}/30 PASS.",
             f"- Publication issues: {len(report['publication_issues'])}.",
             f"- PDF map geometry: {report['pdf_geometry']['status']}.",
             "- Rendered visual evidence: see the separate hash-bound assessment in `V4_VISUAL_EVIDENCE_AUDIT.md`; this machine gate does not certify it.",
             "- Spatial layout/objects: see `V4_MAP_LAYOUT_AUDIT.md`; no tool-only visual PASS.", "",
             "## Current gate findings", ""]
    if report["mode"] == "V3 baseline diagnosis":
        intro.append("V4 implementation and final artifacts are pending. The baseline has preserved abstract solutions but known publication/art defects; the following V3 findings must be repaired in V4.")
    for issue in report["publication_issues"]:
        intro.append(f"- Case {issue.get('case', 0):02d}: `{issue['code']}` — {issue.get('detail', issue.get('paths', issue.get('name', '')))}")
    intro += ["", "## Per-case requirements", "",
              "Each section records the current situation/setting, objective, people/aliases, rules, evidence, deduction, unique answer, visual asset, signal, meta role, timing assumptions and callback. Modern setting is taken from each case's narrative setup and title; no independent story facts are invented here.", ""]
    path.write_text("\n".join(intro) + body[body.index("\n"):] , encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--master", type=Path, default=ROOT / "dist/book1_en_master_owner_review_v4.yml")
    ap.add_argument("--runtime", type=Path, default=ROOT / "dist/hmda_spatial_runtime_v4.json")
    ap.add_argument("--pdf", type=Path, default=ROOT / "dist/HMDA_Book1_EN_OwnerReview_v4.pdf")
    ap.add_argument("--page-index", type=Path, default=ROOT / "dist/HMDA_Book1_EN_OwnerReview_v4_page_index.json")
    ap.add_argument("--report", type=Path, default=ROOT / "docs/HMDA_BOOK1_V4_LOGIC_REPORT.json")
    ap.add_argument("--ledger", type=Path, default=ROOT / "docs/HMDA_BOOK1_V4_LOGIC_LEDGER.md")
    ap.add_argument("--baseline-audit", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    baseline_paths = {"master": ROOT / "dist/book1_en_master_owner_review_v3.yml",
                      "runtime": ROOT / "dist/hmda_spatial_runtime_v3.json",
                      "pdf": ROOT / "dist/HMDA_Book1_EN_OwnerReview_v3.pdf"}
    for kind, path in baseline_paths.items():
        if sha(path) != BASELINE_HASHES[kind]:
            raise ValueError(f"Frozen V3 baseline {kind} was altered; investigate before comparison")
    if args.baseline_audit:
        args.master, args.runtime, args.pdf = [baseline_paths[k] for k in ("master", "runtime", "pdf")]
        args.page_index = ROOT / "dist/HMDA_Book1_EN_OwnerReview_v3_page_index.json"
    paths = {k: getattr(args, k) for k in ("master", "runtime", "pdf", "page_index")}
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        report = {"status": "BLOCKED", "reason": "Required final V4 inputs are unavailable", "missing": missing}
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    data = v3.read_yaml(args.master)
    baseline_data = v3.read_yaml(baseline_paths["master"])
    runtime = json.loads(args.runtime.read_text(encoding="utf-8"))
    baseline_runtime = json.loads(baseline_paths["runtime"].read_text(encoding="utf-8"))
    cases = {int(c["id"].split("_")[1]): c for c in runtime["cases"]}
    baseline_cases = {int(c["id"].split("_")[1]): c for c in baseline_runtime["cases"]}
    issues, reviews = publication_checks(data, cases, baseline_data, baseline_cases)
    results = {n: v3.enumerate_spatial(c) for n, c in cases.items()}
    results.update(v3.nonspatial_checks(data["missions"], cases, results))
    pdf_audit = map_geometry(args.pdf, args.page_index, cases)
    evidence_audit = pdf_evidence_presence(args.pdf, args.page_index, data)
    issues.extend(evidence_audit["errors"])
    passed = all(r["status"] == "PASS" for r in results.values()) and not issues and pdf_audit["status"] == "PASS"
    report = {"status": "BLOCKED" if args.baseline_audit else "PASS" if passed else "NEEDS WORK",
              "mode": "V3 baseline diagnosis" if args.baseline_audit else "Final V4 machine gate",
              "scope": "30 encoded logic models, locked runtime identity, reviewed publication evidence and map/PDF text geometry. No visual approval.",
              "bindings": {k: {"path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p), "sha256": sha(p)} for k, p in paths.items()},
              "publication_issues": issues, "publication_reviews": reviews,
              "cases": dict(sorted(results.items())), "pdf_geometry": pdf_audit,
              "pdf_evidence": evidence_audit,
              "visual_review": "Separate hash-bound human assessment in V4_MAP_LAYOUT_AUDIT.md and V4_VISUAL_EVIDENCE_AUDIT.md; not certified by this machine gate."}
    if args.self_test:
        report["self_tests"] = v3.self_test(cases)
        changed = copy.deepcopy(data)
        changed["missions"][1]["spatial"]["clue_cards"][0] = "Nova was in row 2 and column B."
        changed_issues, _ = publication_checks(changed, cases, baseline_data, baseline_cases)
        assert any(i["code"] == "UNREVIEWED_EVIDENCE_CHANGE" and i["case"] == 2 for i in changed_issues)
        report["self_tests"].append("Changed printed row clue is rejected even when the locked abstract CSP is unchanged.")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_ledger(args.ledger, data, cases, results, report)
    print(json.dumps({"status": report["status"], "mode": report["mode"],
                      "encoded_cases_pass": sum(r["status"] == "PASS" for r in results.values()),
                      "publication_issues": issues, "map_geometry": pdf_audit["status"],
                      "map_failures": {n: r["failures"] for n, r in pdf_audit["maps"].items() if r["failures"]}}, indent=2))
    return 2 if args.baseline_audit else 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
