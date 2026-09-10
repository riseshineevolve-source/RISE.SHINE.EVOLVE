# Happy Makers Detective Academy - Book Factory

Reusable content-driven PDF generator for the Rise.Shine.Evolve. Detective Academy series.

## Why this exists

The layout engine lives in code. Story, dialogue, puzzle descriptions and metadata live in YAML. New editions should mostly require editing content and swapping puzzle assets rather than rebuilding page geometry in Canva or Colab.

## Current phase

Phase 1 renders the complete 30-mission story blueprint into a deterministic Letter-size PDF. Phase 2 will add production page templates, Shigai grid assets, Happy Makers art, hint pages, solutions, KDP bleed and preflight checks.

## Structure

- `content/book_en.yml` - master English story blueprint and 30-mission plan
- `render_book.py` - reusable PDF renderer
- `dist/` - generated output, not source of truth
- `.github/workflows/build-detective-book.yml` - automatic cloud build

## Local Windows build

```bat
cd tools\detective-book-factory
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python render_book.py
```

## Cloud build

Every push to `feature/detective-book-factory` that changes this tool triggers GitHub Actions. You can also run the workflow manually from Actions > Build Detective Academy PDF > Run workflow.

The PDF is uploaded as a workflow artifact named `detective-academy-pdf`.

## Planned production architecture

The final renderer will support reusable page types:

1. title / copyright / detective ID
2. squad introduction
3. chapter opener
4. guided training case
5. two-page spatial case spread
6. quick mission
7. Room Zero checkpoint
8. three-level hint vault
9. step-by-step solutions
10. grand final
11. certificate / series hook

Content remains separate from design. English and Polish editions will use separate YAML files while sharing exactly the same templates and puzzle geometry.

## Canva handoff

The code-generated PDF is the master source. The production build will also export high-resolution page previews. Canva is intended for light art-direction tweaks only, not for rebuilding pagination or the logic system.

## Non-negotiable logic rule

Every final puzzle must have one valid solution. Any time a Shigai grid is reframed, room names or clue wording are changed consistently and the resulting case is revalidated before publication.
