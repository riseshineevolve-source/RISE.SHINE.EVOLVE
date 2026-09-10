# Happy Makers Detective Academy - Book Factory

Reusable content-driven PDF generator for the Rise.Shine.Evolve. Detective Academy series.

## Production model

Story and puzzle data live in YAML. Layout lives in Python. Character portraits and spatial logic modules are replaceable assets. Canva is a finishing layer, not the source of pagination.

The current production preview renders the opening and Cases 01-05 of Book 1, `The Mystery of Room Zero`, with:

- grayscale gaming/dossier design
- Happy Makers avatar dialogue cards
- guided training grid
- reusable spatial deduction page template
- quick visual-evidence template
- code puzzle template
- Room Zero meta-story beats
- Hint Vault
- step-by-step solution pages
- automatic preflight
- automatic PNG page previews

`content/book_en.yml` remains the 30-case master blueprint. `content/book1_en_production.yml` contains production-ready copy for the first rendered tranche.

## Build locally

```bash
cd tools/detective-book-factory
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python render_book.py --content content/book1_en_production.yml --output dist/HMDA_Book1_Production_Preview_v1.pdf
python scripts/preflight.py --content content/book1_en_production.yml --pdf dist/HMDA_Book1_Production_Preview_v1.pdf --min-pages 25 --report dist/preflight.txt
python scripts/make_previews.py --pdf dist/HMDA_Book1_Production_Preview_v1.pdf --out dist/previews --dpi 144
```

## Cloud build

Pushes to `feature/detective-book-factory` trigger `.github/workflows/build-detective-book.yml`. The workflow builds the PDF, runs preflight, creates PNG previews, and uploads everything as a GitHub Actions artifact.

## Asset rules

- `assets/production/*.png|jpg`: normalized grayscale Happy Makers portraits and temporary verified spatial modules.
- Temporary Shigai map assets are logic references only. Final publication art should be rebuilt/rethemed while preserving verified clue geometry.
- Every reframed spatial case must be revalidated before publication.

## Series reuse

Book 2 or another language edition should require mostly new YAML plus new puzzle/art assets. Page templates, callout components, chapter gates, hint pages, solution layouts, preflight, and export stay reusable.
