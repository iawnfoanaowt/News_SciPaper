#!/usr/bin/env python
"""Analyze paired PDF/DOCX samples for News_SciPaper.

The script stores statistics and structural signals only. It does not persist
full sample body text.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Any
from xml.etree import ElementTree as ET

try:
    from docx import Document
except Exception:  # pragma: no cover - dependency may be absent elsewhere
    Document = None  # type: ignore

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


@dataclass
class SampleRecord:
    base: str
    has_pdf: bool
    has_docx: bool
    docx_title: str | None = None
    docx_paragraphs: int | None = None
    docx_chars: int | None = None
    docx_images: int | None = None
    figure_caption_count: int | None = None
    pdf_pages: int | None = None
    pdf_title: str | None = None


def _text_from_paragraph(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS)).strip()


def docx_stats(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
        media_count = sum(1 for name in zf.namelist() if name.startswith("word/media/"))
    root = ET.fromstring(xml)
    paragraphs = []
    for para in root.findall(".//w:body/w:p", NS):
        text = re.sub(r"\s+", " ", _text_from_paragraph(para)).strip()
        if text:
            paragraphs.append(text)
    title = paragraphs[0] if paragraphs else ""
    figure_caption_count = sum(1 for text in paragraphs if re.match(r"^图\d+", text))
    return {
        "title": title,
        "paragraphs": len(paragraphs),
        "chars": sum(len(text) for text in paragraphs),
        "images": media_count,
        "figure_caption_count": figure_caption_count,
    }


def pdf_stats(path: Path) -> dict[str, Any]:
    if PdfReader is None:
        return {"pages": None, "title": None}
    reader = PdfReader(str(path))
    metadata = reader.metadata or {}
    title = metadata.get("/Title") or metadata.get("title") or ""
    return {"pages": len(reader.pages), "title": str(title) if title else ""}


def analyze(sample_dir: Path) -> dict[str, Any]:
    files = [p for p in sample_dir.iterdir() if p.suffix.lower() in {".pdf", ".docx"}]
    stems = sorted({p.stem for p in files})
    records: list[SampleRecord] = []
    for stem in stems:
        pdf = sample_dir / f"{stem}.pdf"
        docx = sample_dir / f"{stem}.docx"
        record = SampleRecord(base=stem, has_pdf=pdf.exists(), has_docx=docx.exists())
        if docx.exists():
            stats = docx_stats(docx)
            record.docx_title = stats["title"]
            record.docx_paragraphs = stats["paragraphs"]
            record.docx_chars = stats["chars"]
            record.docx_images = stats["images"]
            record.figure_caption_count = stats["figure_caption_count"]
        if pdf.exists():
            stats = pdf_stats(pdf)
            record.pdf_pages = stats["pages"]
            record.pdf_title = stats["title"]
        records.append(record)

    char_counts = [r.docx_chars for r in records if r.docx_chars is not None]
    image_counts = [r.docx_images for r in records if r.docx_images is not None]
    paragraph_counts = [r.docx_paragraphs for r in records if r.docx_paragraphs is not None]
    summary = {
        "sample_dir": str(sample_dir),
        "pair_count": sum(1 for r in records if r.has_pdf and r.has_docx),
        "record_count": len(records),
        "docx_chars": _range_mean(char_counts),
        "docx_images": _range_mean(image_counts),
        "docx_paragraphs": _range_mean(paragraph_counts),
        "records": [asdict(r) for r in records],
    }
    return summary


def _range_mean(values: list[int | None]) -> dict[str, float | int | None]:
    clean = [int(v) for v in values if v is not None]
    if not clean:
        return {"min": None, "max": None, "mean": None}
    return {"min": min(clean), "max": max(clean), "mean": round(mean(clean), 2)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_dir", type=Path)
    parser.add_argument("--out", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    result = analyze(args.sample_dir)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
