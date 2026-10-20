"""Generate app icon (dark-red + blood-red liquid glass) from Lain artwork.

Run: python tools/make_icon.py  →  assets/icon.png + assets/icon.ico
Falls back to a pure procedural icon if artwork is missing.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

SIZE = 512
DARK = (13, 2, 2)
BLOOD = (193, 39, 39)


def load_artwork() -> Image.Image | None:
    for name in ("Lain.jfif", "ii'm like antoher.jfif"):
        p = ROOT / name
        if p.is_file():
            try:
                return Image.open(p).convert("RGB")
            except Exception:
                pass
    return None


def cover(img: Image.Image, size: int) -> Image.Image:
    w, h = img.size
    s = max(size / w, size / h)
    img = img.resize((int(w * s) + 1, int(h * s) + 1), Image.LANCZOS)
    x = (img.width - size) // 2
    y = (img.height - size) // 2
    return img.crop((x, y, x + size, y + size))


def rounded_mask(size: int, radius: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def main() -> None:
    art = load_artwork()
    if art is not None:
        base = cover(art, SIZE)
    else:
        base = Image.new("RGB", (SIZE, SIZE), DARK)
        d = ImageDraw.Draw(base)
        d.ellipse([60, 60, SIZE - 60, SIZE - 60], fill=(42, 8, 8))

    # darken + red tint for brand identity
    overlay = Image.new("RGB", (SIZE, SIZE), (26, 4, 4))
    base = Image.blend(base, overlay, 0.45)

    # red glow rim
    rim = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(rim)
    d.rounded_rectangle([6, 6, SIZE - 7, SIZE - 7], radius=110,
                        outline=BLOOD + (255,), width=14)
    rim = rim.filter(ImageFilter.GaussianBlur(6))
    base = base.convert("RGBA")
    base.alpha_composite(rim)

    # JP monogram パ in blood red glass pill
    pill = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([SIZE // 2 - 120, SIZE - 190, SIZE // 2 + 120, SIZE - 90],
                        radius=45, fill=(20, 3, 3, 210), outline=BLOOD + (255,), width=4)
    base.alpha_composite(pill)
    d = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("msgothic.ttc", 72)
    except Exception:
        font = ImageFont.load_default()
    d.text((SIZE // 2, SIZE - 140), "パ", fill=(255, 227, 227, 255),
           font=font, anchor="mm")

    base = base.convert("RGB")
    base.putalpha(rounded_mask(SIZE, 110))
    bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg.paste(base, mask=rounded_mask(SIZE, 110))

    bg.save(ASSETS / "icon.png")
    bg.resize((256, 256), Image.LANCZOS).save(ASSETS / "icon.ico")
    print(f"icon written: {ASSETS / 'icon.png'} , {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
