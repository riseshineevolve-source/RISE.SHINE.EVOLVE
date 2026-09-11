from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
SOURCE = REPO_ROOT / "assets" / "images"
TARGET = TOOL_ROOT / "assets" / "production"
TARGET.mkdir(parents=True, exist_ok=True)

ASSETS = {
    "bibi.png": "Grandma Bibi.png",
    "luli.png": "Luli.png",
    "dilo.png": "Dilo.png",
    "alio.png": "Alio.png",
    "nini.png": "Nini.png",
    "mimi.png": "Mimi.png",
    # Existing RSE group/brand art. Can later be replaced with the dedicated
    # Detective Academy squad composition without changing YAML or templates.
    "squad.jpg": "Happy Makers floating box.png",
}


def normalize(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing canonical RSE asset: {src}")

    with Image.open(src) as im:
        im = im.convert("L")
        im = ImageOps.autocontrast(im, cutoff=0.5)
        max_side = 1800 if dst.name == "squad.jpg" else 1200
        im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        if dst.suffix.lower() == ".jpg":
            im.save(dst, quality=91, optimize=True, progressive=True)
        else:
            im.save(dst, optimize=True)


if __name__ == "__main__":
    print(f"RSE asset source: {SOURCE}")
    print(f"Book factory target: {TARGET}")
    for output_name, source_name in ASSETS.items():
        src = SOURCE / source_name
        dst = TARGET / output_name
        normalize(src, dst)
        print(f"OK  {source_name} -> {dst.relative_to(REPO_ROOT)}")
