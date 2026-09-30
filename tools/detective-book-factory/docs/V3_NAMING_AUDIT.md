# V3 naming audit

Status: baseline audited; the production lead adopted the complete presentation-only allocation unchanged and applied it to `content/spatial_character_aliases.yml`. Final PDF verification remains a separate gate.

## Authority and scope

The V3 owner brief makes Naming B mandatory and forbids unexplained guest reuse. The production lead explicitly requires unique modern replacements rather than retrospectively declaring repeated names a recurring roster. Source identity, placement, room membership, clue constraints and answer coordinate must remain unchanged. The six Happy Makers are intentional recurring characters. No other recurrence is assumed.

Baseline: `content/spatial_character_aliases.yml` at the start of V3; the V2 generated master and PDF apply these aliases contextually. Raw names in immutable source/runtime records are legitimate implementation identities and must not be destroyed.

Automated inventory: **103 spatial identities, 33 distinct display names, 24 repeated display-name groups, 70 excess uses**. The adopted replacement allocation below has **103 distinct display names** and changes **71** mappings. Tutorial names Ari, Bea, Cole, Dani and Case 14 names Maya, Leo, Sofia, Noah also remain unique against this allocation: **111 distinct guest names** across those reader-facing rosters.

## Every repeated baseline alias

| Alias | Count | Cases |
|---|---:|---|
| Arlo | 3 | 06, 19, 20 |
| Atlas | 2 | 02, 17 |
| Blaze | 4 | 07, 10, 13, 29 |
| Clover | 7 | 04, 12, 15, 22, 23, 25, 29 |
| Dash | 4 | 10, 15, 19, 20 |
| Echo | 4 | 04, 10, 12, 13 |
| Gia | 2 | 22, 25 |
| Hugo | 2 | 06, 15 |
| Indigo | 4 | 07, 12, 15, 22 |
| Juno | 4 | 13, 15, 23, 29 |
| Kai | 4 | 04, 12, 17, 19 |
| Luna | 3 | 17, 20, 22 |
| Moxie | 7 | 13, 15, 17, 19, 20, 23, 29 |
| Nova | 5 | 02, 10, 12, 22, 25 |
| Otis | 3 | 17, 19, 23 |
| Pixel | 5 | 04, 15, 20, 23, 29 |
| Rook | 6 | 02, 13, 17, 23, 25, 29 |
| Scout | 6 | 06, 12, 17, 20, 25, 29 |
| Skye | 2 | 13, 19 |
| Theo | 3 | 19, 20, 25 |
| Vega | 2 | 06, 29 |
| Vera | 2 | 10, 23 |
| Wren | 7 | 06, 10, 12, 13, 22, 25, 29 |
| Zuri | 3 | 04, 07, 22 |

Bea also occurs in the guided Case 01 roster and in the baseline Case 04 aliases. Proposed Case 04 Briar removes that collision. Vega is reserved for the locked final answer in Case 29; Case 06 uses Vale. Max is a valid Group B alias in Case 02, but must be introduced as the trophy keeper before the objective uses the name. It must not appear as an unexplained Happy Maker or free-floating narrator.

## Adopted complete mapping

This YAML records the adopted presentation contract already applied to the existing alias file; it is documentation, not a second runtime source. It retains the initial of every V2 display name, so all existing within-case initial uniqueness is preserved. The owner now requires numeric witness IDs regardless; initials are only a defensive compatibility check.

```yaml
cases:
  HMDA_02:
    Hope: Nova
    Drew: Dax
    Rory: Rook
    Edgar: Atlas
    Vesta: Ivy
    Bobby: Max
  HMDA_04:
    Finlay: Echo
    Ivor: Kai
    Raquel: Zuri
    Amelie: Briar
    Clarissa: Clover
    Lisa: Pixel
  HMDA_06:
    Stafford: Scout
    Hubert: Hugo
    Ava: Arlo
    Vera: Vale
    Wallace: Wren
    Eunice: Uma
  HMDA_07:
    Bruce: Blaze
    Isla: Indigo
    Winifred: Willa
    Zelda: Zoe
    Roscoe: Rocket
    Grayson: Gray
  HMDA_10:
    Eliza: Ember
    Nicholas: Nico
    Willie: Wyatt
    Frances: Finn
    Blythe: Beck
    Verity: Vera
    Dora: Dash
  HMDA_12:
    Kendra: Kira
    Norris: Nell
    Irma: Iris
    Earlene: Eli
    Cleo: Cove
    Siobhan: Sage
    Winthrop: Winter
  HMDA_13:
    Jewel: Juno
    Shirley: Skye
    Elliot: Eden
    Wanda: Willow
    Bronwen: Bodhi
    Mercer: Moxie
    Rafferty: Remy
  HMDA_15:
    Hiram: Harper
    Primrose: Piper
    Damian: Duke
    Carolyn: Cruz
    Jonquil: Jett
    Isabella: Inez
    Mona: Milo
  HMDA_17:
    Octavia: Otis
    Margaret: Mika
    Kerry: Koa
    Samuel: Sunny
    Lincoln: Luna
    Ambrose: Axel
    Rhoda: Reed
  HMDA_19:
    Archibald: Avery
    Theodore: Theo
    Ottoline: Ollie
    Drew: Dex
    Madge: Mack
    Kimberly: Kian
    Sonia: Sasha
  HMDA_20:
    Standish: Sid
    Pamela: Pax
    Leslie: Luca
    Millie: Mara
    Aurora: Asa
    Thatcher: Toby
    Danielle: Demi
  HMDA_22:
    Leigh: Lex
    Irene: Imani
    Clarence: Cody
    Natasha: Nia
    Gemma: Gia
    William: Wes
    Zelda: Zara
  HMDA_23:
    Vesta: Vivi
    Charlene: Cora
    Owen: Ozzy
    Rebecca: Rae
    Madge: Mae
    Peyton: Pia
    Judy: Jude
  HMDA_25:
    Giselle: Gabe
    Celia: Casey
    Regan: Rio
    Theodore: Tate
    Silas: Sol
    Warren: Wynn
    Noreen: Nori
  HMDA_29:
    Michelle: Mavis
    Cassandra: Cato
    Jordana: Jules
    Betsy: Bryn
    Vera: Vega
    Ransom: Ren
    Payton: Poppy
    Wilhelmina: Wade
    Shepherd: Seth
```

## Required migration behavior

- Substitute by `(case_id, source_identity)`, using one simultaneous whole-token transform. Never cascade replacement strings or use a global raw-name ban; a valid alias in one case can also be a source name elsewhere.
- Apply the same display identity to hook, objective, witness roster, clue text, hints, nudges, dialogue, verdict, solution reasoning and completed-map legend. Rebuild generated masters and map labels from source after changing aliases.
- Each board assigns two-digit IDs `01` through roster length. A solution uses `03 — NAME — C3`, never `C = C3`. Keep the source roster order stable. Tutorial people require numeric IDs too; their coordinates remain unchanged.
- Preserve `Vera -> Vega` and D3 in HMDA_29. Preserve the fourteen ROOM initials and `CHECK THE OLD MAP`; witness names are not the meta alphabet.
- Room and prop aliases need a separate contextual audit: displayed clue terminology must match displayed map legend exactly. Modern prop reskins must not rename a clue object without the paired label change.
- Names do not establish a witness's gender. If a source clue depends on a gender predicate, supply that attribute explicitly in the case roster or have the logic owner revise and deterministically revalidate the clue. In particular, Case 23's “man on a bench” predicate cannot rely on the reader guessing a gender from a new alias.

## Automated checks performed for this allocation

PASS: 15 case keys; 103 source keys retained; 103 unique adopted spatial aliases; no collision with eight existing nonspatial guests or six Happy Makers; unique initial per case; every V2 alias initial preserved; final Vera/Vega identity retained. The documented mapping was compared directly with the current canonical alias file and is identical. This verifies source allocation, not its application to generated output.

## Final production gate

Search every rendered page, including Hint Vault and solutions, by its case context; compare its expected roster and numeric ID mapping. Reject raw names from that same case, unexplained MAX, placeholder labels, alphabetic witness tokens that conflict with map columns, and any proposed alias applied to the wrong source identity. Confirm all source placements and answer coordinates before/after remain identical. Read the final PDF after extraction because embedded art may not expose text.

Final source application: confirmed and checked against the adopted mapping. Final V3 PDF check: pending; do not label Naming B production PASS from this document alone.
