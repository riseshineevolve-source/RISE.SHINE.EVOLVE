from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve()
TOOL_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
SOURCE = REPO_ROOT / "assets" / "images"
TARGET = TOOL_ROOT / "assets" / "production"
TARGET.mkdir(parents=True, exist_ok=True)

OWNER_APPROVED_SQUAD = "Happy Makers detectives.png"
LEGACY_SQUAD_FALLBACK = "Happy Makers floating box.png"

BASE_ASSETS = {
    "bibi.png": "Grandma Bibi.png",
    "luli.png": "Luli.png",
    "dilo.png": "Dilo.png",
    "alio.png": "Alio.png",
    "nini.png": "Nini.png",
    "mimi.png": "Mimi.png",
}


def asset_map(require_approved_squad: bool = False) -> dict[str, str]:
    """Resolve production asset sources without silently claiming V2 readiness.

    The owner-review V2 path must use the owner-approved Detective squad. Remote
    CI/checkouts created before that binary is durable may still use the legacy
    group art for non-V2 regression builds, but the strict V2 switch fails closed.
    """
    approved = SOURCE / OWNER_APPROVED_SQUAD
    if approved.exists():
        squad = OWNER_APPROVED_SQUAD
    elif require_approved_squad:
        raise FileNotFoundError(
            f"Owner-review V2 requires approved squad asset: {approved}. "
            "Do not substitute the legacy group image."
        )
    else:
        squad = LEGACY_SQUAD_FALLBACK
    return {**BASE_ASSETS, "squad.jpg": squad}


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-approved-squad",
        action="store_true",
        help="Fail unless assets/images/Happy Makers detectives.png is present; required for owner-review V2.",
    )
    args = parser.parse_args()

    assets = asset_map(args.require_approved_squad)
    print(f"RSE asset source: {SOURCE}")
    print(f"Book factory target: {TARGET}")
    print(f"Detective squad source: {assets['squad.jpg']}")
    if assets["squad.jpg"] != OWNER_APPROVED_SQUAD:
        print("NOTICE: legacy squad fallback in use; this build is NOT owner-review V2 squad-ready.")
    for output_name, source_name in assets.items():
        src = SOURCE / source_name
        dst = TARGET / output_name
        normalize(src, dst)
        print(f"OK  {source_name} -> {dst.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
