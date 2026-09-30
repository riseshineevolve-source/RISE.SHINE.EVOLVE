"""Make numbered every-page contact sheets from the V3 interior PNG render."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "dist/v3_premium_review")
ROOT = parser.parse_args().root
pages = sorted((ROOT / "pages").glob("page-*.png"))
if not pages:
    raise SystemExit("No rendered pages")
for offset in range(0, len(pages), 20):
    sheet = Image.new("RGB", (960, 1560), "white")
    draw = ImageDraw.Draw(sheet)
    for position, path in enumerate(pages[offset:offset+20]):
        thumbnail = ImageOps.contain(Image.open(path).convert("RGB"), (220, 285))
        x = (position % 4) * 240 + 10
        y = (position // 4) * 310 + 20
        sheet.paste(thumbnail, (x, y))
        draw.text((x, y-15), f"PAGE {offset+position+1:03d}", fill="black")
    sheet.save(ROOT / f"contact-{offset//20+1:02d}.jpg", quality=88)
print(f"PASS: {len(pages)} pages in {(len(pages)+19)//20} contact sheets")
