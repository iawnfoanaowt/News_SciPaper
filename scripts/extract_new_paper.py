#!/usr/bin/env python
"""Extract planning signals from a scientific paper PDF for News_SciPaper."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None  # type: ignore

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore

try:
    import pypdfium2 as pdfium
except Exception:  # pragma: no cover
    pdfium = None  # type: ignore


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", re.IGNORECASE)
SECTION_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*\.?\s+)?(abstract|summary|introduction|materials and methods|methods|results|discussion|conclusions?|data availability|acknowledg(?:e)?ments?|references)\b",
    re.IGNORECASE,
)
FIGURE_START_RE = re.compile(
    r"^(?P<label>(?:fig(?:ure)?\.?|FIGURE)\s*[\dIVX]+[A-Za-z]?)(?P<sep>[\.:|])?\s*(?P<body>.*)$",
    re.IGNORECASE,
)
FIGURE_REF_ONLY_RE = re.compile(r"^\(?fig(?:ure)?\.?\s*\d+[A-Za-z]?\)?[.,;:]?$", re.IGNORECASE)
TABLE_START_RE = re.compile(r"^(?:table|extended data fig|supplementary fig)\b", re.IGNORECASE)
PAGE_NO_RE = re.compile(r"^\d{1,3}$")

TARGET_PLATFORMS = ["青藏所官网", "公众号"]
PUBLICATION_INFO = {
    "project_support": "",
    "paper_link": "",
    "online_publication_date": "",
    "impact_factor": "",
}


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf_text(pdf_path: Path, max_pages: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata: dict[str, Any] = {"pages": None, "title": ""}
    if PdfReader is not None:
        reader = PdfReader(str(pdf_path))
        metadata["pages"] = len(reader.pages)
        md = reader.metadata or {}
        metadata["title"] = str(md.get("/Title") or md.get("title") or "")

    pages: list[dict[str, Any]] = []
    if pdfplumber is None:
        return pages, metadata

    with pdfplumber.open(str(pdf_path)) as pdf:
        metadata["pages"] = len(pdf.pages)
        limit = len(pdf.pages) if max_pages is None else min(max_pages, len(pdf.pages))
        for idx in range(limit):
            page = pdf.pages[idx]
            text = page.extract_text() or ""
            pages.append(
                {
                    "page": idx + 1,
                    "text": normalize_text(text),
                    "image_count": len(page.images or []),
                    "width": float(page.width),
                    "height": float(page.height),
                }
            )
    return pages, metadata


def guess_title(pages: list[dict[str, Any]], metadata_title: str = "") -> tuple[str, bool]:
    if metadata_title and len(metadata_title) > 8 and "Microsoft" not in metadata_title:
        return metadata_title.strip(), False
    if not pages:
        return "", True

    lines = [line.strip() for line in pages[0]["text"].splitlines() if line.strip()]
    candidates = []
    for line in lines[:35]:
        if len(line) < 12 or len(line) > 220:
            continue
        if DOI_RE.search(line) or SECTION_RE.search(line):
            continue
        if re.search(r"\b(journal|article|www\.|http|received|accepted|available online)\b", line, re.IGNORECASE):
            continue
        candidates.append(line)
    title = max(candidates[:10], key=len, default="")
    return title, not bool(title)


def extract_dois(pages: list[dict[str, Any]]) -> list[str]:
    dois: list[str] = []
    seen = set()
    for page in pages:
        for match in DOI_RE.finditer(page["text"]):
            doi = match.group(0).rstrip(".,;:)])}").lower()
            if doi not in seen:
                seen.add(doi)
                dois.append(doi)
    return dois


def cleanup_abstract(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:Editor|Handling Editor|Article history|Received|Accepted|Available online)[: ].{0,180}?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Keywords?|Key words)[: ].{0,240}?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b©\s*\d{4}\b.*$", "", text).strip()
    return text[:3000]


def extract_abstract(pages: list[dict[str, Any]]) -> tuple[str, bool]:
    text = "\n".join(page["text"] for page in pages[:5])
    text = re.sub(r"\bA\s+B\s+S\s+T\s+R\s+A\s+C\s+T\b", "Abstract", text, flags=re.IGNORECASE)
    match = re.search(
        r"\b(?:Abstract|Summary)\b\s*(.+?)(?:\n\s*(?:Keywords?|Key words|Introduction|1\.?\s+Introduction)\b)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return "", True
    abstract = cleanup_abstract(match.group(1))
    suspicious = len(abstract) < 120 or re.search(r"\b(Editor|Article history|Received|Accepted|Available online)\b", abstract[:220], re.IGNORECASE)
    if suspicious:
        return abstract, True
    return abstract, False


def extract_sections(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found = []
    seen = set()
    for page in pages:
        for line in page["text"].splitlines():
            clean = line.strip()
            if not clean or len(clean) > 90:
                continue
            match = SECTION_RE.match(clean)
            if match:
                key = match.group(1).lower()
                if key not in seen:
                    seen.add(key)
                    found.append({"section": clean, "page": page["page"]})
    return found


def is_caption_stop_line(line: str) -> bool:
    clean = line.strip()
    if not clean:
        return True
    if PAGE_NO_RE.match(clean):
        return True
    if TABLE_START_RE.match(clean):
        return True
    if FIGURE_START_RE.match(clean) and not FIGURE_REF_ONLY_RE.match(clean):
        return True
    if SECTION_RE.match(clean):
        return True
    if re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z][A-Za-z][A-Za-z\s,\-()]{8,100}$", clean):
        return True
    if re.search(r"\b(?:et al\.|doi\.org|Elsevier|Springer Nature|Published by)\b", clean, re.IGNORECASE):
        return True
    return False


def normalize_figure_label(label: str) -> str:
    label = re.sub(r"\s+", " ", label).strip()
    label = re.sub(r"^Figure\b", "Fig.", label, flags=re.IGNORECASE)
    label = re.sub(r"^Fig\b(?!\.)", "Fig.", label, flags=re.IGNORECASE)
    return label


def clean_caption(text: str) -> str:
    caption = re.sub(r"\s+", " ", text).strip()
    section_match = re.search(
        r"\s+\d+(?:\.\d+)+\.?\s+[A-Z][A-Za-z][A-Za-z\s,\-()]{8,120}",
        caption,
    )
    if section_match and section_match.start() > 60:
        caption = caption[: section_match.start()].strip()
    caption = re.sub(r"\s+\d+\s*$", "", caption).strip()
    return caption[:650]


def caption_quality(caption: str) -> tuple[float, bool, list[str]]:
    reasons: list[str] = []
    confidence = 0.75
    body_len = len(caption)
    if body_len < 35:
        confidence -= 0.35
        reasons.append("caption_too_short")
    if body_len > 450:
        confidence -= 0.25
        reasons.append("caption_long_needs_review")
    if re.search(r"\b(Fig\.\s*\d+[A-Za-z]?\)|Fig\.\s*\d+[A-Za-z]?\b.*Fig\.)", caption, re.IGNORECASE):
        confidence -= 0.15
        reasons.append("may_include_body_figure_references")
    if re.search(r"\b(?:container|division|therefore|however|we used|we found|this study)\b", caption[180:], re.IGNORECASE):
        confidence -= 0.15
        reasons.append("may_include_body_text")
    confidence = max(0.05, min(0.95, confidence))
    return confidence, bool(reasons), reasons


def extract_figure_candidates(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen = set()
    for page in pages:
        lines = [line.strip() for line in page["text"].splitlines()]
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            match = FIGURE_START_RE.match(line)
            if not match or FIGURE_REF_ONLY_RE.match(line) or TABLE_START_RE.match(line):
                idx += 1
                continue

            label = normalize_figure_label(match.group("label"))
            initial_body = (match.group("body") or "").strip()
            caption_parts = [f"{label} {initial_body}".strip()]
            j = idx + 1
            while j < len(lines) and len(" ".join(caption_parts)) < 560:
                nxt = lines[j].strip()
                if is_caption_stop_line(nxt):
                    break
                caption_parts.append(nxt)
                j += 1

            caption = clean_caption(" ".join(caption_parts))
            key = (label.lower(), caption[:160].lower())
            if label and key not in seen:
                seen.add(key)
                confidence, needs_review, reasons = caption_quality(caption)
                candidates.append(
                    {
                        "candidate_type": "text_caption",
                        "label": label,
                        "page": page["page"],
                        "caption": caption,
                        "caption_zh": "",
                        "recommended_use": "",
                        "confidence": round(confidence, 2),
                        "needs_review": needs_review,
                        "reason": reasons,
                    }
                )
            idx = max(j, idx + 1)
    return candidates


def visual_fallback_pages(pages: list[dict[str, Any]], max_pages: int) -> list[int]:
    scored = []
    for page in pages:
        text = page["text"]
        refs = len(re.findall(r"\bfig(?:ure)?\.?\s*\d+", text, re.IGNORECASE))
        image_count = int(page.get("image_count") or 0)
        # Skip title/metadata pages unless they visibly contain images.
        score = image_count * 4 + refs
        if page["page"] <= 2 and image_count == 0:
            score -= 2
        if score > 0:
            scored.append((score, page["page"]))
    if not scored:
        return [page["page"] for page in pages[:max_pages]]
    scored.sort(key=lambda item: (-item[0], item[1]))
    return sorted({page_no for _, page_no in scored[:max_pages]})


def add_visual_candidates(candidates: list[dict[str, Any]], pages: list[dict[str, Any]], min_count: int, max_visual_pages: int) -> list[dict[str, Any]]:
    if len(candidates) >= min_count:
        return candidates
    existing_pages = {int(candidate["page"]) for candidate in candidates}
    for page_no in visual_fallback_pages(pages, max_visual_pages):
        if page_no in existing_pages and candidates:
            continue
        candidates.append(
            {
                "candidate_type": "visual_page",
                "label": f"Page {page_no} visual candidate",
                "page": page_no,
                "caption": "",
                "caption_zh": "",
                "recommended_use": "",
                "confidence": 0.2,
                "needs_review": True,
                "reason": ["no_reliable_text_caption_visual_fallback"],
            }
        )
        existing_pages.add(page_no)
        if len(candidates) >= min_count:
            break
    return candidates


def render_pages(pdf_path: Path, pages: list[int], out_dir: Path, scale: float = 2.0, max_pages: int = 12) -> dict[int, str]:
    rendered: dict[int, str] = {}
    if not pages or pdfium is None:
        return rendered
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered_pages = []
    for page_no in pages:
        if page_no not in ordered_pages:
            ordered_pages.append(page_no)
    ordered_pages = ordered_pages[:max_pages]

    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        for page_no in ordered_pages:
            if page_no < 1 or page_no > len(pdf):
                continue
            bitmap = pdf[page_no - 1].render(scale=scale).to_pil()
            out_path = out_dir / f"page_{page_no:03d}.png"
            bitmap.save(out_path)
            rendered[page_no] = str(out_path)
    finally:
        pdf.close()
    return rendered


def extract(
    pdf_path: Path,
    max_pages: int | None,
    render_dir: Path | None,
    min_figure_candidates: int,
    max_visual_pages: int,
    max_render_pages: int,
) -> dict[str, Any]:
    pages, metadata = read_pdf_text(pdf_path, max_pages=max_pages)
    title_guess, title_needs_review = guess_title(pages, metadata.get("title") or "")
    dois = extract_dois(pages)
    abstract, abstract_needs_review = extract_abstract(pages)
    figure_candidates = extract_figure_candidates(pages)
    text_caption_count = len(figure_candidates)
    figure_candidates = add_visual_candidates(figure_candidates, pages, min_figure_candidates, max_visual_pages)

    rendered: dict[int, str] = {}
    if render_dir:
        render_page_list = [int(candidate["page"]) for candidate in figure_candidates]
        rendered = render_pages(pdf_path, render_page_list, render_dir, max_pages=max_render_pages)
        for candidate in figure_candidates:
            candidate["rendered_page"] = rendered.get(int(candidate["page"]), "")

    publication_info = dict(PUBLICATION_INFO)
    publication_info["paper_link"] = f"https://doi.org/{dois[0]}" if dois else ""

    return {
        "pdf": str(pdf_path),
        "metadata": metadata,
        "title_guess": title_guess,
        "title_needs_review": title_needs_review,
        "doi_candidates": dois,
        "doi_lookup_needed": not bool(dois),
        "target_platforms": TARGET_PLATFORMS,
        "publication_info": publication_info,
        "publication_info_notes": {
            "impact_factor": "Do not infer automatically; leave blank or mark 待确认 unless the user or a verified source provides it.",
            "online_publication_date": "Verify from publisher/DOI page when not present in the PDF.",
        },
        "abstract": abstract,
        "abstract_needs_review": abstract_needs_review,
        "sections": extract_sections(pages),
        "figure_candidates": figure_candidates,
        "figure_candidate_summary": {
            "text_caption_count": text_caption_count,
            "total_candidate_count": len(figure_candidates),
            "visual_fallback_used": len(figure_candidates) > text_caption_count,
            "rendered_page_count": len(rendered),
            "max_render_pages": max_render_pages,
        },
        "confirmation_needed": [
            "Chinese title",
            "Chinese author names and roles",
            "Current corresponding-author affiliations/team wording",
            "funding statement",
            "online publication date",
            "impact factor",
            "final figure choices",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, help="Optional JSON output path.")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--render-pages", type=Path, help="Render pages containing candidate figures to this directory.")
    parser.add_argument("--min-figure-candidates", type=int, default=2)
    parser.add_argument("--max-visual-pages", type=int, default=6)
    parser.add_argument("--max-render-pages", type=int, default=12)
    args = parser.parse_args()

    result = extract(
        args.pdf,
        args.max_pages,
        args.render_pages,
        args.min_figure_candidates,
        args.max_visual_pages,
        args.max_render_pages,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
