#!/usr/bin/env python
"""Crop a figure image directly from a rendered PDF page.

The crop box defaults to relative page coordinates: left,top,right,bottom,
where each value is between 0 and 1. Use --pixels for pixel coordinates in the
rendered image. A sidecar JSON file records page, crop box, image size, and a
simple nonblank check.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import ImageStat

try:
    import pypdfium2 as pdfium
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"pypdfium2 is required for PDF rendering: {exc}")


def parse_box(value: str) -> tuple[float, float, float, float]:
    parts = [float(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box must contain four comma-separated values")
    left, top, right, bottom = parts
    if right <= left or bottom <= top:
        raise argparse.ArgumentTypeError("--box must satisfy right > left and bottom > top")
    return left, top, right, bottom


def image_nonblank_stats(image) -> dict[str, Any]:
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    mean_gray = round(float(stat.mean[0]), 2)
    extrema = gray.getextrema()
    nonblank_ok = image.size[0] > 200 and image.size[1] > 200 and 5 < mean_gray < 250 and extrema[0] != extrema[1]
    return {
        "size": list(image.size),
        "mean_gray": mean_gray,
        "extrema": list(extrema),
        "nonblank_ok": nonblank_ok,
    }


def crop_pdf(
    pdf_path: Path,
    page_no: int,
    box: tuple[float, float, float, float] | None,
    out: Path,
    scale: float,
    pixels: bool,
) -> dict[str, Any]:
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page_count = len(pdf)
        if page_no < 1 or page_no > page_count:
            raise ValueError(f"Page {page_no} is outside PDF page range 1-{page_count}")
        image = pdf[page_no - 1].render(scale=scale).to_pil()
    finally:
        pdf.close()

    rendered_size = list(image.size)
    resolved_box = None
    if box:
        left, top, right, bottom = box
        if not pixels:
            width, height = image.size
            left, right = left * width, right * width
            top, bottom = top * height, bottom * height
        resolved_box = [round(left), round(top), round(right), round(bottom)]
        image = image.crop(tuple(resolved_box))

    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    stats = image_nonblank_stats(image)
    return {
        "pdf": str(pdf_path),
        "page": page_no,
        "scale": scale,
        "input_box": list(box) if box else None,
        "box_units": "pixels" if pixels else "relative",
        "resolved_pixel_box": resolved_box,
        "rendered_page_size": rendered_size,
        "output": str(out),
        **stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--box", type=parse_box, help="Crop box as left,top,right,bottom. Defaults to full page.")
    parser.add_argument("--pixels", action="store_true", help="Treat --box as rendered-image pixel coordinates.")
    parser.add_argument("--scale", type=float, default=3.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--meta-out", type=Path, help="Optional crop metadata JSON path. Defaults to <out>.json.")
    parser.add_argument("--no-meta", action="store_true", help="Do not write crop metadata JSON.")
    args = parser.parse_args()

    metadata = crop_pdf(args.pdf, args.page, args.box, args.out, args.scale, args.pixels)
    if not args.no_meta:
        meta_out = args.meta_out or args.out.with_name(args.out.name + ".json")
        meta_out.parent.mkdir(parents=True, exist_ok=True)
        meta_out.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        metadata["metadata_json"] = str(meta_out)
    print(str(args.out))
    return 0 if metadata.get("nonblank_ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
