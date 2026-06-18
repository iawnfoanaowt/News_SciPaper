# News_SciPaper

版本：1.1

News_SciPaper 是一个 Codex skill，用于把英文科研论文 PDF 转写为中文科研新闻稿，并输出 Word 文档。它的默认写作目标是研究所官网和公众号风格：标题简洁、正文偏研究所新闻口吻、保留论文关键信息，并从 PDF 中截取重点图件插入 Word。

## 主要功能

- 从英文论文 PDF 中提取标题、摘要、DOI、章节、图题候选和重点图页。
- 按样本文稿风格生成中文新闻稿，默认正文约 1000-1300 字。
- 固定加入“项目支持、论文链接、在线发表日期、影响因子”等字段。
- 支持从 PDF 页面直接裁剪 2-4 张重点图，并写中文图题。
- 生成 `.docx` 新闻稿，图片居中，默认宽度约 14.65 cm。
- 提供 Word 输出质量检查脚本，自动检查篇幅、段落、图片数量、固定字段和占位符。

## 适用场景

- 课题组新论文发布前，需要快速起草中文科研新闻稿。
- 需要保持同一课题组既有新闻稿风格和格式。
- 需要将英文论文中的关键图件直接嵌入中文 Word 新闻稿。
- 需要先生成待确认提纲、候选图片和不确定信息清单，再形成正式稿。

不适合的场景：大众科普长文、媒体采访稿、完全脱离论文证据的宣传稿，或需要自动编造作者、基金、影响因子等未核验信息的任务。

## 安装方法

在 Windows PowerShell 中执行：

```powershell
git clone https://github.com/iawnfoanaowt/News_SciPaper.git "$env:USERPROFILE\.codex\skills\news-scipaper"
```

如果已经安装过，进入 skill 目录后更新：

```powershell
cd "$env:USERPROFILE\.codex\skills\news-scipaper"
git pull
```

安装后，在 Codex 中可以用下面的方式调用：

```text
$news-scipaper 请根据这篇英文论文 PDF 写一篇中文新闻稿，并输出 Word。
```

## 推荐使用流程

1. 提供英文论文 PDF。
2. skill 先提取论文结构、DOI、摘要、图题和候选图页。
3. 先生成确认简报：中文标题建议、正文结构、关键结果、作者/单位/基金疑点、候选图片清单。
4. 用户确认中文姓名、单位、基金、在线发表日期、影响因子和最终图件。
5. 生成正式 `.docx` 新闻稿。
6. 运行质量检查脚本，确认篇幅、固定字段、图片数量、图片宽度和中文图题。

## 输出内容

默认 Word 新闻稿包含：

- 标题：通常为“期刊简称：中文研究亮点”。
- 正文：研究背景、团队与方法、主要结果、科学意义、发表信息。
- 固定字段：项目支持、论文链接、在线发表日期、影响因子。
- 图片：2-4 张从 PDF 截取的重点图。
- 图题：每张图配中文图题。

## 目录说明

```text
SKILL.md                       skill 入口说明
VERSION                        当前版本号
agents/openai.yaml             Codex 显示名和默认调用提示
assets/news_template.docx      Word 输出模板
references/style-guide.md      中文新闻稿风格规则
references/sample-analysis.json 样本统计摘要，不含完整样本文本
scripts/analyze_samples.py     只读分析样本 PDF/DOCX
scripts/extract_new_paper.py   提取新论文候选信息
scripts/crop_pdf_region.py     从 PDF 页面裁剪图片
scripts/build_news_docx.py     根据 JSON 规格生成 Word
scripts/validate_news_docx.py  检查 Word 输出质量
```

## 依赖说明

在 Codex 桌面环境中，建议使用内置 Python 运行脚本。常用依赖包括：

- `python-docx`
- `pdfplumber`
- `pypdf`
- `pypdfium2`
- `Pillow`

如果在普通 Python 环境中使用，需要先安装这些依赖。

## 数据与隐私

本仓库只保存从样本中提炼出的写作规则、统计摘要、脚本和 Word 模板，不包含样本论文 PDF、样本新闻稿全文，也不包含后续生成的新闻稿成品。使用时请不要把未公开论文、完整样本稿或临时输出提交到仓库。

## 注意事项

- 影响因子、在线发表日期、作者中文名、通讯作者单位和基金项目默认需要核验；无法确认时应保留“待确认”，不要自动编造。
- PowerShell 可能把中文显示成乱码，但文件本身可能仍是 UTF-8；应使用 Python UTF-8 读取或打开 Word 检查。
- 图片默认从 PDF 中裁剪。若用户提供高清原图，可优先使用高清原图。
- 生成 Word 后应运行 `scripts/validate_news_docx.py`，发现篇幅、图片或固定字段问题后再交付。

## 版本记录

### 1.1

- 发布 GitHub 版本。
- 增加中文 README、VERSION 和 `.gitignore`。
- 保留 PDF 信息提取、图件裁剪、Word 生成和 Word 质量检查流程。
- 支持在生成规格中使用 `page_break_before_figures`，避免图片和中文图题跨页分离。
