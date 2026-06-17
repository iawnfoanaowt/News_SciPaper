---
name: news-scipaper
description: Convert English scientific paper PDFs into Chinese institute-style research news releases as Word documents. Use when the user asks to learn from paired English papers and Chinese news drafts, draft a Chinese research news article from a new paper, choose figures from a paper, or create a .docx news release with title, body text, paper link, and selected scientific figures.
---

# News_SciPaper

Version: 1.1

## Purpose

Use this skill to write Chinese research news releases from English scientific papers in the style of the Zhang Guoqing research group sample set. The expected output is a `.docx` file for the Institute of Tibetan Plateau Research official website and WeChat account, with a concise Chinese title, institute-style body text, required publication information, and selected paper figures with Chinese captions.

Before drafting, read `references/style-guide.md`. Do not copy full sample manuscripts into the output or into new resources; use the extracted style rules and statistics.

## Default Workflow

1. Inspect the new paper.
   - Run `scripts/extract_new_paper.py <paper.pdf> --out <workdir>/paper_extraction.json --render-pages <workdir>/figure_pages` when a PDF is available.
   - Use the extraction to identify title, DOI/link, abstract, key sections, numeric results, text-caption candidates, and visual page candidates.
   - If `doi_lookup_needed`, `title_needs_review`, `abstract_needs_review`, or figure-candidate `needs_review` is true, flag it in the confirmation brief.
   - If DOI, online date, journal name, or article link is unclear, verify from publisher/DOI pages when network access is allowed.
   - Do not infer impact factor automatically; leave it blank or mark it as `待确认` unless the user provides it or a verified source is checked.

2. Prepare a confirmation brief before writing the Word file.
   - Propose one Chinese title in the pattern `期刊简称：中文研究亮点`.
   - List the planned body arc: background/problem, team/method, main results, significance/application, publication details.
   - Use the new paper's current corresponding-author affiliations/team wording, not stale sample wording.
   - List uncertain Chinese author names, current affiliations, corresponding authors, funding programs, online publication date, impact factor, and article link.
   - List 2-4 recommended figure candidates by figure number when text captions are reliable; if text captions are missing or weak, list rendered visual page candidates and ask the user to specify final page/figure choices.
   - Ask the user to confirm only high-risk items: Chinese names/affiliations/funding, online date/impact factor if not found, and final figure choices.

3. Draft the news release after confirmation.
   - Target 1000-1300 Chinese characters for the main body, usually 4-6 main body paragraphs before fixed information and figures.
   - Use the institute/news style in `references/style-guide.md`, not a popular-science feature style.
   - Preserve exact quantitative results and avoid unsupported policy or impact claims.
   - Translate scientific terms consistently and keep English acronyms when they are useful on first mention.
   - Always include fixed fields for `项目支持`, `论文链接`, `在线发表日期`, and `影响因子`; leave the value blank or use a confirmation placeholder if not yet available.

4. Build the Word document.
   - Crop selected figures directly from the PDF when original figure files are not provided: use rendered pages from `extract_new_paper.py`, inspect them, then run `scripts/crop_pdf_region.py <paper.pdf> --page N --box left,top,right,bottom --out figure.png`.
   - Keep the crop metadata JSON produced by `crop_pdf_region.py`; use it to verify page number, crop box, image size, and nonblank status.
   - Create a JSON spec with `title`, `paragraphs`, `publication_info`, and `figures`.
   - Run `scripts/build_news_docx.py <spec.json> <output.docx> --template assets/news_template.docx`.
   - Use confirmed image files when available. If a figure image is still missing, insert a clear placeholder caption rather than inventing a figure.

5. Verify the Word output.
   - Run `scripts/validate_news_docx.py <output.docx> --out <workdir>/docx_validation.json`.
   - Confirm title, main-body length, paragraph count, fixed fields, figure count, image width, captions, and placeholder status.
   - Fix any validation error before delivery; warnings may be left only with a clear explanation.

## Script Reference

- `scripts/analyze_samples.py`: read paired sample PDFs/DOCX files and output style statistics without saving full sample body text.
- `scripts/extract_new_paper.py`: extract PDF metadata, DOI candidates, abstract-like text, section headings, figure captions, and optional rendered PDF pages.
- `scripts/crop_pdf_region.py`: render one PDF page and crop a confirmed figure region to PNG for direct PDF-derived figure insertion.
- `scripts/build_news_docx.py`: create the final Word news release from a structured JSON spec.
- `scripts/validate_news_docx.py`: validate final Word length, required fields, figure count, image width, captions, and unresolved placeholders.

Use the bundled Python runtime when available, because it has `python-docx`, `pypdf`, `pdfplumber`, `pypdfium2`, and Pillow installed in this environment.

## Editorial Defaults

- Treat `News_SciPaper` as the user-facing name; keep the technical skill name `news-scipaper`.
- Default platforms are the Institute of Tibetan Plateau Research website and WeChat account.
- Default to 2-4重点图, selected from PDF candidate figures after user confirmation.
- Default to direct PDF screenshot/crop insertion when original figure files are not supplied.
- Default to asking about uncertain Chinese names, author roles, affiliations, and funding rather than guessing.
- Default to current corresponding-author affiliation wording from the new paper.
- Always include `项目支持`, `论文链接`, `在线发表日期`, and `影响因子`, even when values are blank.
- Treat impact factor as a confirmation field, not an automatically inferred fact.
- In this Windows/PowerShell environment, Chinese can display as mojibake even when the UTF-8 file is correct; verify content with UTF-8 Python reads or Word rereads.
- Default to a Word file matching the sample format: A4, normal margins, body paragraphs in Normal style, centered title, centered figures, and figures near full text width.
