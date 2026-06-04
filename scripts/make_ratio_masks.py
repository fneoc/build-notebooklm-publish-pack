#!/usr/bin/env python3
"""Create blurred-background ratio variants for publish package images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("Pillow is required. Install pillow or use a bundled Python runtime that includes PIL.") from exc


DEFAULT_VARIANTS = {
    "vertical-3x4-mask": (3, 4),
    "rich-4x3-mask": (4, 3),
}


def parse_variant(raw: str) -> tuple[str, tuple[int, int]]:
    if "=" not in raw or "x" not in raw:
        raise argparse.ArgumentTypeError("variant must look like name=3x4")
    name, ratio = raw.split("=", 1)
    width, height = ratio.lower().split("x", 1)
    width_i = int(width)
    height_i = int(height)
    if width_i <= 0 or height_i <= 0:
        raise argparse.ArgumentTypeError("ratio values must be positive")
    return name.strip(), (width_i, height_i)


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def fit_resize(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    max_w, max_h = max_size
    src_w, src_h = image.size
    scale = min(max_w / src_w, max_h / src_h, 1.0)
    return image.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)


def canvas_size(source_size: tuple[int, int], ratio: tuple[int, int]) -> tuple[int, int]:
    src_w, src_h = source_size
    ratio_w, ratio_h = ratio
    src_area = src_w * src_h
    target_w = round((src_area * ratio_w / ratio_h) ** 0.5)
    target_h = round(target_w * ratio_h / ratio_w)
    min_w = max(src_w, 900)
    min_h = max(src_h, 900)
    if target_w < min_w:
        target_w = min_w
        target_h = round(target_w * ratio_h / ratio_w)
    if target_h < min_h:
        target_h = min_h
        target_w = round(target_h * ratio_w / ratio_h)
    return target_w, target_h


def make_variant(
    source: Path,
    output_dir: Path,
    variant_name: str,
    ratio: tuple[int, int],
    prefix: str | None,
    foreground_scale: float,
    blur_radius: int,
    brightness: float,
) -> dict[str, object]:
    image = Image.open(source).convert("RGB")
    size = canvas_size(image.size, ratio)
    background = cover_resize(image, size)
    background = background.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    background = ImageEnhance.Brightness(background).enhance(brightness)

    max_foreground = (round(size[0] * foreground_scale), round(size[1] * foreground_scale))
    foreground = fit_resize(image, max_foreground)
    left = (size[0] - foreground.width) // 2
    top = (size[1] - foreground.height) // 2
    background.paste(foreground, (left, top))

    stem = prefix or source.stem
    output = output_dir / f"{stem}-{variant_name}.png"
    background.save(output)
    return {
        "source": str(source),
        "output": str(output),
        "width": size[0],
        "height": size[1],
        "ratio": f"{ratio[0]}:{ratio[1]}",
    }


def iter_variants(raw_variants: Iterable[str] | None) -> dict[str, tuple[int, int]]:
    if not raw_variants:
        return dict(DEFAULT_VARIANTS)
    return dict(parse_variant(raw) for raw in raw_variants)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--prefix", default=None, help="Output filename prefix. Only use with one input image.")
    parser.add_argument("--variant", action="append", help="Add/replace variants as name=3x4. Can be repeated.")
    parser.add_argument("--foreground-scale", type=float, default=0.92)
    parser.add_argument("--blur-radius", type=int, default=28)
    parser.add_argument("--brightness", type=float, default=0.62)
    args = parser.parse_args()

    if args.prefix and len(args.images) > 1:
        parser.error("--prefix can only be used with one input image")
    if not (0.1 <= args.foreground_scale <= 1.0):
        parser.error("--foreground-scale must be between 0.1 and 1.0")

    variants = iter_variants(args.variant)
    results = []
    for image_path in args.images:
        if not image_path.exists():
            raise SystemExit(f"Missing image: {image_path}")
        output_dir = args.output_dir or image_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, ratio in variants.items():
            results.append(
                make_variant(
                    image_path,
                    output_dir,
                    name,
                    ratio,
                    args.prefix,
                    args.foreground_scale,
                    args.blur_radius,
                    args.brightness,
                )
            )

    print(json.dumps({"outputs": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
