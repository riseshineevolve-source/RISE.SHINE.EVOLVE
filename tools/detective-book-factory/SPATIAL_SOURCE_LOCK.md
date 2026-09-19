# HMDA BOOK 1 - SPATIAL SOURCE LOCK

Status: **LOCKED FOR RSE MAP REBUILD**

This file is the human-readable companion to `content/spatial_source_manifest_final.yml`. The native Shigai checkpoint and 60-page source PDF remain immutable reference material. All final book maps are redrawn/re-themed by RSE while preserving source topology and stored placement.

## Final 15-module bank

| HMDA | Final case | Raw source | Grid / grade | Source answer | Meta | Final meta room | PDF puzzle / statements / solution |
|---|---|---|---|---|---|---|---|
| HMDA_02 | The Trophy That Never Reached the Shelf | The Curious Security Tag and the Secret Gem | 6x6 / EASY 2 | Drew @ D2 | C | Coach's Office | 1 / 2 / 41 |
| HMDA_04 | The Cupcake Box with Six Alibis | The Hidden Display Card and the Unclaimed Relic | 6x6 / EASY 2.2 | Raquel @ F4 | H | Hospitality Room | 6 / 5 / 43 |
| HMDA_06 | The Museum Label That Lied | A Mysterious Hunt at the Museum | 6x6 / EASY 2.1 | Ava @ D2 | E | Egypt Room | 8 / 7 / 44 |
| HMDA_07 | The Costume That Walked Away | The Secret Alarm Record and the Mysterious Gem | 6x6 / MEDIUM 5.2 | Zelda @ C6 | C | Costume Room | 10 / 9 / 45 |
| HMDA_10 | The Robot with Two Owners | The Unexpected Fingerprint and the Secret Treasure | 7x7 / MEDIUM 5.2 | Eliza @ D5 | K | Kinetics Lab | 12 / 11 / 46 |
| HMDA_12 | The Parrot Who Knew the Password | The Last Security Tag and the Secret Relic | 7x7 / MEDIUM 5.3 | Norris @ G2 | T | Training Room | 14 / 13 / 47 |
| HMDA_13 | The Camera That Blinked at 4:17 | What Happened to the Empty Display? | 7x7 / EXPERT 8.4 | Bronwen @ B7 | H | Hide Room | 32 / 31 / 56 |
| HMDA_15 | The Backpack That Changed Owners | The Remarkable Puzzle: The Heirloom | 7x7 / HARD 6.7 | Hiram @ D2 | E | Equipment Room | 18 / 17 / 49 |
| HMDA_17 | The Train Ticket That Wasn't Lost | Rhoda and the Faint Fingerprint | 7x7 / HARD 7.1 | Ambrose @ E3 | O | Observation Car | 20 / 19 / 50 |
| HMDA_19 | The Library Book That Checked Itself Out | The Relic and the Little Ledger Note | 7x7 / EXPERT 8.2 | Madge @ A7 | L | Library Office | 34 / 33 / 57 |
| HMDA_20 | The Paint-Splattered Alibi | The Adventure: The Missing Relic | 7x7 / EXPERT 8.3 | Pamela @ F5 | D | Drying Room | 40 / 39 / 60 |
| HMDA_22 | The Music Room Mix-Up | The Remarkable Adventure: The Heirloom | 7x7 / EXPERT 8.3 | Clarence @ C4 | M | Music Archive | 36 / 35 / 58 |
| HMDA_23 | The Wristband Switch at Adventure Park | The Hidden Clue and the Hidden Prize | 7x7 / EXPERT 8.4 | Rebecca @ F6 | A | Access Office | 26 / 25 / 53 |
| HMDA_25 | The Package with No Name | The Unusual Hunt: The Prize | 7x7 / EXPERT 8.1 | Celia @ D5 | P | Parcel Room | 28 / 27 / 54 |
| HMDA_29 | The Map Beneath the Map | The Search for the Unclaimed Gem | 9x9 / EXPERT 8.2 | Vera @ D3 | - | - | 30 / 29 / 55 |

## Locked meta engine

The fourteen non-boss spatial cases spell **CHECK THE OLD MAP** in book order. The final RSE maps distinguish **ROOMS** from **ZONES**. At Mission 26, the reader considers only spaces visually marked as ROOM. After the verified solution, exactly one ROOM is empty in each marked case; its first letter is the meta letter. This solves the source issue that several Shigai geometries naturally contain more than one unoccupied source area.

## Boss source clarification

The **actual final exported checkpoint/PDF** contains the 9x9 Expert source **The Search for the Unclaimed Gem**, with stored answer **Vera @ D3**. An earlier chat candidate, *Patience Follows the Fresh Velvet Thread* (Ezra @ D6), was not present in the final exported source files and is therefore **not** part of the locked production bank. Do not silently switch the boss back without a new explicit source export and revalidation.

## Validation gate

`scripts/validate_spatial_source_manifest.py` must pass before and after any manifest change. It checks grid partition, row/column uniqueness, blocked-cell safety, owner-answer room relation, stored coordinate, and the 14-letter meta carrier design.
