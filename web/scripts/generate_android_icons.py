#!/usr/bin/env python3
"""Генерация квадратных Android-иконок без растягивания (Pillow)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "resources" / "checkly-icon-512.png"
RES = ROOT / "android" / "app" / "src" / "main" / "res"

BRAND_RGB = (22, 163, 74)  # #16a34a — ic_launcher_background
MASTER = 1024
GREEN_TOLERANCE = 32
OUTER_WHITE_MIN = 250

DENSITIES: list[tuple[str, int, int]] = [
    ("mdpi", 48, 108),
    ("hdpi", 72, 162),
    ("xhdpi", 96, 216),
    ("xxhdpi", 144, 324),
    ("xxxhdpi", 192, 432),
]


def _is_brand_green(r: int, g: int, b: int) -> bool:
    return (
        abs(r - BRAND_RGB[0]) <= GREEN_TOLERANCE
        and abs(g - BRAND_RGB[1]) <= GREEN_TOLERANCE
        and abs(b - BRAND_RGB[2]) <= GREEN_TOLERANCE
    )


def _is_outer_white(r: int, g: int, b: int) -> bool:
    return r >= OUTER_WHITE_MIN and g >= OUTER_WHITE_MIN and b >= OUTER_WHITE_MIN


def _content_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    px = img.load()
    w, h = img.size
    min_x, min_y, max_x, max_y = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y][:3]
            if _is_outer_white(r, g, b):
                continue
            found = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not found:
        return 0, 0, w, h
    return min_x, min_y, max_x + 1, max_y + 1


def _ensure_square_master(src: Path) -> tuple[Image.Image, Image.Image]:
    """Квадратный launcher (RGB) и foreground (RGBA, без зелёного фона)."""
    img = Image.open(src).convert("RGBA")
    cropped = img.crop(_content_bbox(img))
    w, h = cropped.size
    scale = min(MASTER / w, MASTER / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Белые углы исходника (скругления на белом фоне) → фирменный зелёный
    px = resized.load()
    for y in range(new_h):
        for x in range(new_w):
            r, g, b, a = px[x, y]
            if a >= 16 and _is_outer_white(r, g, b):
                px[x, y] = (*BRAND_RGB, 255)

    square_rgb = Image.new("RGB", (MASTER, MASTER), BRAND_RGB)
    offset = ((MASTER - new_w) // 2, (MASTER - new_h) // 2)
    square_rgb.paste(resized.convert("RGB"), offset, resized)

    foreground = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
    px = resized.load()
    fpx = foreground.load()
    ox, oy = offset
    for y in range(new_h):
        for x in range(new_w):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            if _is_brand_green(r, g, b):
                continue
            fpx[ox + x, oy + y] = (r, g, b, 255)

    return square_rgb, foreground


def _write_density(
    launcher: Image.Image,
    foreground: Image.Image,
    density: str,
    launcher_px: int,
    foreground_px: int,
) -> None:
    out_dir = RES / f"mipmap-{density}"
    out_dir.mkdir(parents=True, exist_ok=True)

    resample = Image.Resampling.LANCZOS
    launcher.resize((launcher_px, launcher_px), resample).save(out_dir / "ic_launcher.png", optimize=True)
    launcher.resize((launcher_px, launcher_px), resample).save(
        out_dir / "ic_launcher_round.png", optimize=True
    )
    foreground.resize((foreground_px, foreground_px), resample).save(
        out_dir / "ic_launcher_foreground.png", optimize=True
    )


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"Не найден исходник: {SRC}")

    launcher, foreground = _ensure_square_master(SRC)

    master_path = ROOT / "resources" / "checkly-icon-1024.png"
    launcher.save(master_path, optimize=True)
    foreground.save(ROOT / "resources" / "checkly-icon-foreground-1024.png", optimize=True)

    if not RES.is_dir():
        raise SystemExit(f"Нет Android-проекта — выполните: npx cap add android && npm run cap:sync")

    for density, launcher_px, foreground_px in DENSITIES:
        _write_density(launcher, foreground, density, launcher_px, foreground_px)

    print(f"✅ Иконки из {SRC.name}: квадрат {MASTER}px, пропорции сохранены")
    print(f"   Master: {master_path}")


if __name__ == "__main__":
    main()
