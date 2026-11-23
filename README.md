# cherryuse

个人 Cherry Studio Skill 仓库，用于在多台电脑之间共享技能。

## 技能列表

### 技术配图

| 技能 | 用途 |
|---|---|
| [`tech-diagram`](skills/tech-diagram/SKILL.md) | Mermaid 框图、schemdraw 电路图、matplotlib 波形图，并内嵌显示在对话中 |

### 文档处理（`skills/document/`）

| 技能 | 用途 | 许可 |
|---|---|---|
| [`docx`](skills/document/docx/SKILL.md) | Word 创建、读取、编辑：目录、表格、图片、修订、批注 | Apache-2.0 |
| [`pdf`](skills/document/pdf/SKILL.md) | PDF 文本/表格提取、合并拆分、水印、表单、加密、OCR | Apache-2.0 |
| [`pptx`](skills/document/pptx/SKILL.md) | PPT 创建、读取、编辑：版式、图表、备注 | Apache-2.0 |
| [`xlsx-manipulation`](skills/document/xlsx-manipulation/SKILL.md) | Excel 创建与编辑（openpyxl）：公式、样式、图表 | MIT |
| [`officecli-docx`](skills/document/officecli-docx/SKILL.md) | 基于 officecli CLI 的 Word 工作流 | 未标注 |
| [`officecli-academic-paper`](skills/document/officecli-academic-paper/SKILL.md) | 学术论文排版：APA/IEEE/MLA 引用、公式编号、交叉引用、参考文献 | 未标注 |

> `officecli-academic-paper` 是 `officecli-docx` 的场景层，两者都需要 `officecli` CLI。

### 写作

| 技能 | 用途 | 许可 |
|---|---|---|
| [`humanizer-zh-academic`](skills/humanizer-zh-academic/SKILL.md) | 中文学术写作去 AI 味，降低 AIGC 检测率 | MIT |

## 目录结构

```
cherryuse/
├── README.md
├── .gitignore
└── skills/
    ├── tech-diagram/
    │   ├── SKILL.md
    │   ├── setup.ps1
    │   ├── scripts/
    │   └── examples/
    ├── humanizer-zh-academic/
    │   ├── SKILL.md
    │   ├── SKILL_full.md
    │   ├── README.md
    │   └── LICENSE
    └── document/               ← 文档类技能统一放这里
        ├── docx/
        ├── pdf/
        ├── pptx/
        ├── xlsx-manipulation/
        ├── officecli-docx/
        └── officecli-academic-paper/
```

## 在另一台电脑安装

**1. 通过 GitHub 链接安装**

在目标机器的 Cherry Studio 里，对 Agent 说：

> 安装这个技能：https://github.com/HanaNeko1/cherryuse/blob/main/skills/document/docx/SKILL.md

各技能的链接：

| 技能 | SKILL.md 链接 |
|---|---|
| tech-diagram | `.../blob/main/skills/tech-diagram/SKILL.md` |
| docx | `.../blob/main/skills/document/docx/SKILL.md` |
| pdf | `.../blob/main/skills/document/pdf/SKILL.md` |
| pptx | `.../blob/main/skills/document/pptx/SKILL.md` |
| xlsx-manipulation | `.../blob/main/skills/document/xlsx-manipulation/SKILL.md` |
| officecli-docx | `.../blob/main/skills/document/officecli-docx/SKILL.md` |
| officecli-academic-paper | `.../blob/main/skills/document/officecli-academic-paper/SKILL.md` |
| humanizer-zh-academic | `.../blob/main/skills/humanizer-zh-academic/SKILL.md` |

**2. 初始化依赖**

需要依赖的技能，在技能目录下执行一次：

```powershell
powershell -ExecutionPolicy Bypass -File "<技能目录>\setup.ps1"
```

## 依赖一览

| 技能 | 依赖 |
|---|---|
| tech-diagram | Python venv：schemdraw、matplotlib |
| docx | bun：docx；Python venv：lxml、defusedxml |
| pdf | Python venv：pypdf、pdfplumber、reportlab、pypdfium2、pillow；OCR 需 tesseract + poppler |
| pptx | bun：pptxgenjs；Python venv：python-pptx、pillow、defusedxml、lxml；渲染需 LibreOffice |
| xlsx-manipulation | Python venv：openpyxl |
| officecli-* | `officecli` CLI（需单独安装）+ officecli-docx 技能 |

Python 环境统一放在各技能目录的 `venv/`，npm 依赖放在 `node_modules/`，两者都不提交到仓库。

## 许可

- `docx` / `pdf` / `pptx`：Apache-2.0（来源 anthropics/skills），附 LICENSE.txt
- `xlsx-manipulation`：MIT（SKILL.md 元数据声明）
- `humanizer-zh-academic`：MIT，附 LICENSE
- `officecli-docx` / `officecli-academic-paper`：技能内**未标注许可证**。公开仓库再分发前建议先确认作者授权；如只需要本地使用，可以不提交这两个目录

## 更新

```powershell
cd "D:\PROJECT BIN\home-skill-home\cherryuse"
git pull
```

技能文件更新后 Cherry 会自动同步；`venv/` 与 `node_modules/` 不需要重建，除非依赖变化。
