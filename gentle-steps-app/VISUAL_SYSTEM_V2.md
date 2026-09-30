# Gentle Steps App — Visual System V2

Status: ACTIVE VISUAL CONTRACT
Date: 2026-09-30
Scope: English app only

## Product identity

The app must read immediately as the same product as the final *24 Gentle Steps to Christmas* book, while using stronger mobile contrast than the printed pages.

Primary visual reference:
- elegant five-person Happy-Makers Christmas family;
- purple Christmas tree / wreath / decor;
- cream and warm white surfaces;
- gold trim, ornaments and light;
- restrained burgundy for editorial accents.

Do not default to classic red/green Christmas UI.
Do not let casual/sporty Happy-Makers artwork define the product surface.

## Mobile palette hierarchy

### Purple family — dominant
Use several distinct purples rather than one flat brand purple:
- Night plum: #24112F
- Aubergine: #351545
- Deep royal purple: #4C1D72
- Amethyst: #6F35A5
- Festive violet: #8E4BC1
- Soft lavender: #D9BFE8
- Pale lilac: #F1E5F5

Purple should occupy the largest visual share of hero/background/navigation accents.

### Gold — stronger than print
- Deep gold: #8F6114
- Rich gold: #B78325
- Bright gold: #D2A640
- Soft champagne: #E9D08B
- Pale gold: #FAF0D0

Gold is used for:
- CTA surfaces;
- selected/progress states;
- borders;
- stars/sparkles;
- ornament-like micro-details;
- premium separators.

### Cream — readability surface
- Cream: #FFF7E8
- Warm ivory: #FFFDF7
- Deep cream: #F6E8D4

Long reading content stays on cream/ivory rather than purple.

### Burgundy — editorial accent only
- Burgundy: #8B2249
- Deep burgundy: #6E1838

Use for small editorial labels, source-book echoes and occasional emphasis. It must not compete with purple as the product color.

## Happy-Makers image hierarchy

1. Elegant Christmas family scene = PRIMARY product image.
2. Individual character portraits = SECONDARY note avatars/cameos.
3. Casual/sporty purple images = tertiary/future motion references only.
4. Grandma Bibi is outside this product cast.

Repository assets currently used:
- ../assets/images/Happy Makers floating box.png
- ../assets/images/Mimi.png
- ../assets/images/Luli.png
- ../assets/images/Dilo.png
- ../assets/images/Alio.png
- ../assets/images/Nini.png

## Screen-by-screen contract

### Home
- Family must remain visible at 390px mobile width.
- Hero uses multiple purple tones, visible gold glow and cream/gold metadata.
- Elegant Happy-Makers image is a visual anchor, not hidden on mobile.
- Primary CTA is gold.
- Calendar remains secondary below hero and progress.

### Meet the Happy-Makers
- Dedicated modal/sheet reachable from home/top bar.
- Elegant group image first.
- Five compact profiles below.
- Portraits can be more casual than hero, but remain secondary.

### Daily screen
- Cream reading cards on a richer purple/lilac atmosphere.
- Strong editorial hierarchy: Day → ritual type → activity title → italic tagline → instructions.
- Ritual accent mapping:
  - Mindful Moment = purple/amethyst
  - Fun Spark = gold
  - Family Connection = burgundy/purple
- Character note includes the correct avatar when a named Happy-Maker owns the note.

### Progress / calendar
- Completed state = gold + purple, not green.
- Current day = gold ring/glow.
- Locked state remains legible, not greyed into invisibility.

## Interaction constraints

- Minimum touch target: 44px.
- Do not hide core family identity on mobile.
- Do not put text directly over busy character imagery.
- Do not use tiny decorative text to rescue layout.
- Respect prefers-reduced-motion.
- Keep long activity text fully readable without horizontal scroll.

## Review proof set

Every major visual pass must render:
- Home at 390x844
- Meet the Happy-Makers at 390x1000
- Day 01 at 390x1200
- Day 12 at 390x1200
- Day 22 at 390x1600 (current longest source-derived day)
- Day 23 at 390x1600 (current second-longest source-derived day)
- Day 24 at 390x1200
