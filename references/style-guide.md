# News_SciPaper Style Guide

This guide summarizes a local sample set of 8 paired English PDFs and Chinese Word news releases. The sample corpus is not included in this repository. This guide intentionally stores reusable rules and statistics, not full sample drafts.

## Sample Pattern

- Pairing: each article has one same-name `.pdf` and one same-name `.docx`.
- Length: originally about 1078-1883 Chinese characters; for future releases default to about 1000-1300 Chinese characters in the main body.
- Structure: usually 9-14 non-empty Word paragraphs including title, link, figure captions, and figure notes.
- Figures: usually 2-6 in the samples; for future releases prefer 2-4重点图, inserted after the text and fixed information fields.
- Platforms: write for the Institute of Tibetan Plateau Research official website and WeChat account.
- Word layout: A4 default margins, left/right about 3.17 cm, top/bottom about 2.54 cm; figures are centered at about 14.65 cm width.
- Verification: after building a Word file, run `scripts/validate_news_docx.py` and fix validation errors before delivery.

## Title Pattern

Use `期刊简称：中文研究亮点`.

Examples of journal-prefix style observed in the samples include `RSE：`, `JAG：`, `SB：`, `NG：`, `NREE：`, and `ISPRS：`. Translate the research highlight as a concise noun phrase, not a sentence. Keep the title direct and specific:

- Good: `RSE：基于ICESat-2激光雷达高度计数据的青藏高原湖泊水储量估算`
- Good: `NG：喜马拉雅冰湖接触冰川质量损失被低估`
- Avoid: broad promotional titles, question titles, or over-interpreted impact claims.

## Body Structure

Use this default arc unless the paper type requires a small adjustment:

1. Background and pain point: one paragraph explaining why the topic matters and what limitation exists.
2. Team and method: one paragraph beginning with phrases such as `鉴于此` or `在此背景下`, naming the research team and summarizing the method/data/framework.
3. Main results: one or two paragraphs with exact numbers, regions, validation metrics, or scenario outcomes.
4. Scientific significance: one paragraph on what the work enables, improves, or supports.
5. Publication details: one paragraph beginning with `上述研究成果以...为题` or `该成果以...为题`, including journal, first/corresponding authors, and current corresponding-author affiliations/team wording from the new paper.
6. Fixed information fields: standalone lines for `项目支持：`, `论文链接：`, `在线发表日期：`, and `影响因子：`. Leave values blank or with a confirmation placeholder if not yet known. Do not infer the impact factor automatically.
7. Figures: each figure image followed by a Chinese `图N ...` caption and, when needed, one explanatory sentence.

## Voice and Phrasing

- Use a research institute news voice: factual, concise, and achievement-oriented.
- Prefer `研究表明`, `研究结果显示`, `该研究提出`, `该框架`, `该方法`, `为...提供了重要科学依据`.
- Use the new paper's current corresponding-author units and team wording. Do not reuse sample unit wording if the new paper shows a different affiliation.
- Avoid first-person marketing language, exaggerated novelty, and unsupported social-impact claims.
- Use Chinese punctuation and units. Keep acronyms with Chinese expansion on first mention when useful, for example `冰湖溃决洪水（GLOF）`.

## Figure Selection Rules

- Prefer 2-4 figures that support the news logic, not necessarily every figure in the paper.
- Typical choices: study area/data overview, method/framework diagram, key validation/result map, future impact/risk framework.
- For review or perspective papers, select conceptual diagrams and synthesis figures.
- For method papers, select workflow, validation comparison, and final product/application figures.
- For projection/risk papers, select impact schematic, spatial result map, and mitigation/framework figure.
- Do not select supplementary figures unless the paper's main figures are insufficient.
- Present a candidate list and ask the user to confirm final figure numbers before building the Word document.
- When original figure files are not supplied, crop selected figures directly from the PDF page renderings and insert those PDF-derived images.
- If the PDF text layer fails to provide usable captions, use rendered visual page candidates as the fallback and ask the user to confirm the final page/figure.
- Treat long captions or captions marked `needs_review` as unreliable until checked against the rendered PDF page.

## Handling Uncertainty

Ask for confirmation when any of the following is unclear:

- Chinese names of authors.
- First author, corresponding author, or equal contribution wording.
- Chinese institution names and team wording.
- Funding project names.
- Online publication date.
- Impact factor.
- Whether to use `论文链接` or `文章链接`.
- Which figures should appear in the final release.

If a detail is not confirmed, write a visible placeholder such as `【请确认中文姓名】` in the draft rather than inventing the information.

## Output Defaults

- Target main news text: 4-6 body paragraphs before fixed information fields.
- Target total body length excluding fixed fields and figure captions: 1000-1300 Chinese characters.
- Fixed fields: always include `项目支持：`, `论文链接：`, `在线发表日期：`, and `影响因子：`.
- Impact factor: leave blank or write `待确认` unless the user provides it or a verified source is checked.
- Word file: centered title, left-aligned body paragraphs, standalone link paragraph, centered figures, centered captions.
- Image width: 14.65 cm by default, preserving aspect ratio.
- Encoding: if PowerShell displays Chinese as mojibake, verify with UTF-8 Python or by reopening the Word file; do not treat display mojibake alone as file corruption.
