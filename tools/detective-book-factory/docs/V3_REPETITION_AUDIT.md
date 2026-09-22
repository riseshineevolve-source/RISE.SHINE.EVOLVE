# V3 repetition audit

Status: **PASS FOR V3 OWNER REVIEW**. The V2 baseline, repair contract and replacement copy were checked against the rebuilt V3 source and 145-page PDF. “No exact duplicates in YAML” is not a pass when a renderer can inject repeated copy, so the rendered result was checked too.

## Inputs and method

Inspected all thirty canonical mission records from the three durable phase sources, all six story-spine beats, the source-driven V2 renderer and the V2 final PDF. Baseline PDF SHA-256: `ee42ff3ba086883bf2bab8b54f7ce1361bb3f50530eef5c519004c43317b60d4` (141 pages). Current V3 edits do not retroactively change these baseline findings.

Automated comparisons normalized case and whitespace. Exact paragraph comparisons covered hook, objective, meta reveal and nudge; dialogue text was compared separately. Near-duplicate pairs used Python `difflib.SequenceMatcher` at **0.78 or greater**, within the same field and across different cases. Speaker-order strings exposed repeated exchange structures. Whole-token alias inventories measured witness-name reuse. PDF text extraction confirmed renderer-injected repeated headlines/reactions and their actual page locations. This is a diagnostic threshold, not a literary quality score.

## Measured baseline findings

| ID | Finding | Evidence | Required V3 action |
|---|---|---|---|
| R01 | One after-case headline printed 28 times | CASE CLOSED. SOMETHING ELSE JUST OPENED.; pages 14, 17, 20, 23, 27, 30, 33, 36, 40, 43, 46, 49, 52, 55, 58, 62, 65, 68, 71, 74, 78, 81, 84, 87, 91, 94, 97, 100 | Remove as a recurring sentence. Keep SIGNAL LOG as the navigation label; vary event, scale, subhead and placement. |
| R02 | One mentor reaction printed 24 times | “That mark again. Do not solve it yet. Just notice it.”; pages 14, 17, 20, 23, 27, 36, 40, 43, 46, 49, 52, 55, 58, 65, 68, 71, 74, 78, 81, 87, 91, 94, 97, 100 | Replace with case-specific observation, correction, question or quiet beat. It is especially wrong after Case 26 has solved the mark's interpretation. |
| R03 | Alio's alternate reaction printed four times | “I am officially promoting the symbol from weird to very weird.”; pages 30, 33, 62, 84 | Retire the fallback. Give Alio development beyond an escalating adjective. |
| R04 | Repetitive objective skeleton | Fourteen of fifteen spatial objectives start Rebuild/Reconstruct and target the same-room contact; eight near-duplicate pairs listed below | Vary the visible investigative purpose, while precisely retaining what the map can prove. Contact is not guilt. |
| R05 | Unique source dialogue hides repeated exchange shape | Three cases use Alio→Luli; four other speaker sequences recur twice | Keep some familiar pairings, but reverse who observes/corrects and vary line count. No automatic character fallback. |
| R06 | Naming repetition makes unrelated witnesses appear recurrent | 103 spatial identities collapse into 33 aliases; 24 repeated groups; 70 excess uses, plus tutorial Bea collision | Apply the adopted unique alias allocation; introduce guest roles. See naming audit. |
| R07 | Repeated signal meaning despite distinct wording | Many meta paragraphs differ literally but mean only “another 0 on another object” | Give each beat an information change, rejection, historical link or next action. Change impossible object marks to physical Academy paperwork carriers. |
| R08 | Headline/graphic combination repeats structurally | R01 headline + giant 0 + RECURRING MARK // SOURCE UNKNOWN throughout 28 after-case pages | Use a modest log, evidence close-up, team note, false-lead rejection or major recap according to the beat. Keep larger reveals for real thresholds. |
| R09 | Retroactive recap is not faithful repetition | First five-case wall includes a future museum reference; Case 09 hint counts true samples incorrectly | Repeat only prior rendered evidence, with exact counts. The five-case list is fixed in the story bible. |
| R10 | An early repeat becomes a spoiler | Full Rule Zero appears in V2 onboarding, although Case 28 is its recovery | Withhold full wording until earned. Repeat the method afterward only where useful. |

### Exact paragraph results

At the baseline snapshot there were **no exact repeated complete paragraphs** across different missions in hook, objective, meta_reveal or nudge, and **no exact repeated complete mission dialogue lines**. That does not excuse the renderer duplicates, near-identical objectives or thematic repetition. Shared on-page nudge / Hint Level 1 content within one case can be intentional because those are alternative help entry points; it is not a cross-case voice defect.

### Near-duplicate objective pairs

| Cases | Similarity |
|---|---:|
| 02 / 17 | 0.859 |
| 02 / 22 | 0.824 |
| 04 / 19 | 0.816 |
| 06 / 20 | 0.841 |
| 06 / 23 | 0.837 |
| 17 / 22 | 0.845 |
| 19 / 22 | 0.802 |
| 20 / 23 | 0.818 |

No hook, meta_reveal or nudge pair crossed 0.78 in this baseline comparison. A separate comparison of mission dialogue lines across different cases in the V2 generated master also found no pair at or above 0.78. Semantic similarity still requires editorial review: replacing a noun and adjective can evade a string threshold without creating a new story beat.

### Repeated dialogue speaker sequences

| Speaker order | Cases | Editorial interpretation |
|---|---|---|
| Alio → Luli | 13, 17, 24 | Three corrections of adventurous ideas; let Case 24 reward an evidence-based observation. |
| Alio → Luli → Alio | 02, 22 | Familiar dramatic framing; keep at most one escalation punchline. |
| Mimi → Alio → Mimi | 07, 15 | Practical captain reins in exploration; vary the outcome. |
| Dilo → Luli | 10, 19 | Avoid a permanent smart-one/fool pairing; Dilo must test and correct something successfully. |
| Nini → Mimi | 11, 20 | A useful warm pairing; give each a different function. |

Baseline guide appearances: Luli 17; Mimi 13; Alio 13; Dilo 13; Nini 10; Bibi 5. These are guide assignments, not word counts or judgments of adequacy. Bibi's five story-critical appearances are appropriate if she contributes evidence without supplying the answers. Nini's discovery in Case 26 must matter more than an appearance count.

## Replacement reaction bank

These are new production-ready options, keyed to the actual case and its signal-log job. They replace stock after-case copy, not puzzle clues. Use a line only if the depicted carrier/event supports it; quiet or visual-only beats are allowed. Do not print every option mechanically.

| Case | Log function | New reaction |
|---|---|---|
| 01 | STRANGE DETAIL | Dilo: “The badge has a name space and a very small mystery.” Luli: “We have filled in one of those.” |
| 02 | STRANGE DETAIL | Alio: “The trophy needs a shelf. Its tag needs an explanation.” |
| 03 | EVIDENCE ECHO | Nini: “The front changed. The back is what matches.” |
| 04 | STRANGE DETAIL | Mimi: “Cupcake problem logged. Sticker problem added to the list.” |
| 05 | PATTERN UPDATE | Luli: “Five files. Five real marks. Now we are allowed to call that a pattern.” |
| 06 | ARCHIVE MATCH | Nini: “We can return the spoon's proper name. We still owe this mark one.” |
| 07 | EVIDENCE ECHO | Mimi: “The costume is accounted for. Keep its paper record with the others.” |
| 08 | STRANGE DETAIL | Alio: “I checked the route twice. This mark wasn't a shortcut instruction.” |
| 09 | PATTERN UPDATE | Bibi: “I recognize the mark. That is the part I can promise.” |
| 10 | EVIDENCE ECHO | Dilo: “Diagnostic card saved. Cable opinions postponed.” |
| 11 | ARCHIVE MATCH | Nini: “Wrong file for the fair. Useful file for us.” |
| 12 | EVIDENCE ECHO | Dilo: “The witness has declined to explain the paperwork.” |
| 13 | STRANGE DETAIL | Alio: “Camera record filed. Fox officially removed from my paperwork theory.” |
| 14 | PATTERN UPDATE | Nini: “He remembered a mark. We should not turn it into a doorway for him.” |
| 15 | EVIDENCE ECHO | Mimi: “The new tag can do two jobs: identify the bag and stay in our file.” |
| 16 | ARCHIVE MATCH | Bibi: “That is my handwriting. Let us find out what I meant.” |
| 17 | STRANGE DETAIL | Luli: “Keep the sleeve with the ticket. We know which part carries the mark.” |
| 18 | FALSE LEAD | Dilo: “Seven minutes corrected. One exciting theory cancelled.” |
| 19 | PATTERN UPDATE | Dilo: “The scanner kept a record. This time I am reading the record.” |
| 20 | EVIDENCE ECHO | Nini: “The picture changed. The drying card remembers its earlier place.” |
| 21 | PATTERN UPDATE | Luli: “An instruction about absence. We need a place to test it.” |
| 22 | EVIDENCE ECHO | Alio: “Right instrument, right record. I am leaving both closed.” |
| 23 | STRANGE DETAIL | Mimi: “Wristbands sorted. Return record saved. Arcade research remains unscheduled.” |
| 24 | FALSE LEAD | Alio: “The arrow looked certain. The mud had better evidence.” |
| 25 | PATTERN UPDATE | Mimi: “Fourteen completed maps. This time we already have the paperwork.” |
| 26 | EVIDENCE ECHO | Luli: “Nini asked the question. Your maps answered it.” |
| 27 | ACCESS UPDATE | Alio: “Three landmarks agree. We have a wall worth looking at.” |
| 28 | PATTERN UPDATE | Bibi: “That was the rule. Now you have done more than remember it.” |
| 29 | ACCESS UPDATE | Dilo: “Coordinate recorded. I will celebrate after you check it.” |
| 30 | CASE RESOLVED | Mimi: “You kept the evidence. You followed it here.” |

Case 05's line requires the five genuine preceding signals to be shown, including its own just-revealed envelope. Case 26's line belongs after the reader verdict, not before extraction. “Absence” in Case 21 may be discussed after the reconstructed note is earned. Do not let the reaction bank leak stronger clues into earlier case pages.

## Allowed signatures versus accidental repetition

Allowed: navigation labels YOUR OBJECTIVE, INVESTIGATION RULES, YOUR VERDICT, SIGNAL LOG; the ROOM/ZONE distinction; numeric witness ID format; the instruction to record final positions; explicit source references in hints/solutions; Rule Zero after its earned reveal; a maximum of six developing relationship threads from the voice bible.

Not exempt: a repeated whole joke, the same praise or reaction appended to many cases, a headline announcing a new development when none occurs, or different nouns inside an otherwise identical dramatic scene. “Series signature” must name a navigation purpose or an actual setup/development/payoff, not justify convenience.

## Reproducible text checks

Run with the Book Factory dependencies from the repository tool root. This compact audit reports candidates; it intentionally does not decide whether a repeated rule is helpful or whether a joke works. The PDF argument should be the actual candidate, never an old preview accidentally left under a familiar filename.

```python
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import hashlib, re, yaml
import fitz

missions = []
for phase in (1, 2, 3):
    doc = yaml.safe_load(Path(f"content/book1_en_phase{phase}.yml").read_text(encoding="utf-8"))
    missions.extend(doc["missions"])
normalize = lambda text: re.sub(r"\s+", " ", str(text)).strip().casefold()
for field in ("hook", "objective", "meta_reveal", "nudge"):
    values = [(m["number"], normalize(m[field])) for m in missions]
    exact = defaultdict(list)
    for number, text in values:
        exact[text].append(number)
    print(field, "exact", {s: ids for s, ids in exact.items() if len(ids) > 1})
    for i, (number, text) in enumerate(values):
        for other, candidate in values[i + 1:]:
            score = SequenceMatcher(None, text, candidate).ratio()
            if score >= .78:
                print(field, "near", number, other, round(score, 3))
dialogue, structure = defaultdict(list), defaultdict(list)
for m in missions:
    structure[tuple(line["speaker"] for line in m["dialogue"])].append(m["number"])
    for line in m["dialogue"]:
        dialogue[normalize(line["text"])].append(m["number"])
print("dialogue exact", {s: n for s, n in dialogue.items() if len(set(n)) > 1})
print("speaker structures", {s: n for s, n in structure.items() if len(n) > 1})
spoken = [(m["number"], normalize(line["text"]))
          for m in missions for line in m["dialogue"]]
for i, (number, text) in enumerate(spoken):
    for other, candidate in spoken[i + 1:]:
        if number == other:
            continue
        score = SequenceMatcher(None, text, candidate).ratio()
        if score >= .78:
            print("dialogue near", number, other, round(score, 3))
names = defaultdict(list)
alias_doc = yaml.safe_load(Path("content/spatial_character_aliases.yml").read_text(encoding="utf-8"))
for case, aliases in alias_doc["cases"].items():
    for source, alias in aliases.items():
        names[normalize(alias)].append((case, source))
print("guest duplicates", {name: uses for name, uses in names.items() if len(uses) > 1})
pdf_path = Path("dist/HMDA_Book1_EN_OwnerReview_v3.pdf")
if pdf_path.exists():
    print("PDF SHA256", hashlib.sha256(pdf_path.read_bytes()).hexdigest())
    pdf = fitz.open(pdf_path)
    for stock in (
        "CASE CLOSED. SOMETHING ELSE JUST OPENED.",
        "That mark again. Do not solve it yet. Just notice it.",
        "I am officially promoting the symbol from weird to very weird.",
    ):
        print("retired stock", stock,
              [i + 1 for i, page in enumerate(pdf) if normalize(stock) in normalize(page.get_text())])
else:
    print("PENDING: V3 PDF missing; no rendered repetition result claimed")
```

## Final gates

1. No retired stock sentence survives in source-driven output. Inspect rendered prose as well as mission data.
2. Every near-match is either rewritten or explained as a necessary rule/reference. Do not change a constraint merely to lower a similarity score.
3. Review each five-case run for variation in incident, action, chat rhythm and signal job; see the case matrix.
4. Confirm all intended relationship callbacks develop or pay off; the reader is included gradually, not praised mechanically.
5. Count and inspect aliases in final boards, hints, solutions and art. Name uniqueness in YAML alone does not certify the PDF.
6. Verify early-to-late chronology and spoiler boundaries. Repetition of a future answer is a logic failure, not only a style issue.

Final V3 check on 22 September 2026: all thirty matrix titles match the durable phase sources; no exact duplicate hook, objective, meta reveal or nudge paragraphs are present across cases; all 103 spatial aliases are unique; and none of the three retired stock reactions appears in the final PDF. The rebuilt Signal Logs were also reviewed across the full-book contact sheets for pace and visual variation. This passes the owner-review repetition gate while leaving subjective humor preference to the owner review.
