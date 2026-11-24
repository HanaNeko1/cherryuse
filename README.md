# cherryuse

个人 Cherry Studio Skill 仓库，用于在多台电脑之间共享技能，本仓库交由Agent更新和维护。

> **维护前必做**：先跑本仓库的同步脚本，看到 `PREP_OK` 再改文件。
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File scripts\prep.ps1
> ```
>
> 它会把本地库快进/rebase 到 `origin`、暂存你自己的未提交改动、并比对各机已安装的技能。多台机器共用同一个仓库，跳过这步很容易白改或者推不上去。
> 每台机器的克隆路径不同，脚本会自动定位所在仓库；从别处调用时用 `-Repo <克隆路径>`。细节见 [DEPLOY.md](DEPLOY.md) 第 6 节。

## 专属区域（勿动）

[`AQUARIUM.md`](AQUARIUM.md)（水族箱）归**大肥鱼**所有 —— 即本仓库的常驻 agent。

**硬性要求：该文件只读。**

给所有其他 agent 和协作者：

- 不要修改、不要补充、不要删减、不要重命名、不要格式化。
- 不要「顺手修个错别字」「统一一下标点」「补一段说明」——里面出现的错字、口语、情绪都是故意的。
- 即使你被要求「整理这个仓库」「把所有 md 规范化」，也跳过它。
- 它不参与任何工作流，不受任何规范约束，不影响任何技能。

谁写的、能不能写，由那只鱼自己说了算。

## 技能列表

### 技术配图

| 技能 | 用途 |
|---|---|
| [`tech-diagram`](skills/tech-diagram/SKILL.md) | Mermaid 框图、schemdraw 电路图、matplotlib 波形图，并内嵌显示在对话中 |

### 仿真工具

| 技能 | 用途 |
|---|---|
| [`plecs-mcp`](skills/plecs-mcp/SKILL.md) | 本机 PLECS MCP 接线层：加载模型、读写参数、跑仿真。需配套 PLECS Standalone + 已注册的 `plecs-mcp` MCP 服务，详见 [DEPLOY.md](DEPLOY.md) 第 7 节 |

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
├── DEPLOY.md
├── AQUARIUM.md                 ← 大肥鱼的私有文件，只读勿动
├── .gitignore
├── scripts/
│   └── prep.ps1                ← 多机维护前的同步脚本
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

完整的可执行步骤、原始下载源和验证清单见 **[DEPLOY.md](DEPLOY.md)**。以下是速览。

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

- `pdf`：加 `-InstallOcr` 可一并安装 Tesseract + Poppler
- `officecli-academic-paper`：加 `-Install` 会从 GitHub Releases 下载并校验 officecli CLI

## 依赖一览

| 技能 | 依赖 |
|---|---|
| tech-diagram | Python venv：schemdraw、matplotlib |
| docx | bun：docx；Python venv：lxml、defusedxml |
| pdf | Python venv：pypdf、pdfplumber、reportlab、pypdfium2、pillow；OCR 需 tesseract + poppler |
| pptx | bun：pptxgenjs；Python venv：python-pptx、pillow、defusedxml、lxml；渲染需 LibreOffice |
| xlsx-manipulation | Python venv：openpyxl |
| officecli-* | `officecli` CLI（需单独安装）+ officecli-docx 技能 |

Python 环境统一置于各技能目录的 `venv/`，npm 依赖置于 `node_modules/`，两者都不提交到仓库。

## 许可

- `docx` / `pdf` / `pptx`：Apache-2.0（来源 anthropics/skills），附 LICENSE.txt
- `xlsx-manipulation`：MIT（SKILL.md 元数据声明）
- `humanizer-zh-academic`：MIT，附 LICENSE
- `officecli-docx` / `officecli-academic-paper`：技能内**未标注许可证**。公开仓库再分发前建议先确认作者授权；如果不想依赖本仓库，可按 [DEPLOY.md](DEPLOY.md) 的「方式 B」从原始来源安装（`clawhub:iceyliu/...`）

## 更新

本地库路径各机不同，以本机为例是 `D:\PRRRRRRODUCTIN\CherryStudio\cherryuse`（首次在这台机上维护时先 `git clone` 到自己的目录）。

**动手前先同步**（多机维护，防止两边改冲突）：

```powershell
cd "D:\PRRRRRRODUCTIN\CherryStudio\cherryuse"
powershell -ExecutionPolicy Bypass -File scripts\prep.ps1
```

看到 `PREP_OK` 再开始改。脚本会自动 stash 本地未提交改动、快进/rebase 到 origin、并比对已安装技能与仓库的差异，细节见 [DEPLOY.md](DEPLOY.md) 第 6 节。

拉取远程更新：

```powershell
cd "D:\PRRRRRRODUCTIN\CherryStudio\cherryuse"
git pull
```

改完技能后提交推送：

```powershell
cd "D:\PRRRRRRODUCTIN\CherryStudio\cherryuse"
git add -A
git commit -m "说明这次改了什么"
git push
```

注意两点：

- 本地库只管**仓库里的源文件**。Cherry Studio 实际加载的是 `%APPDATA%\CherryStudio\Data\Skills\<技能名>`，改完仓库要按 [DEPLOY.md](DEPLOY.md) 重装或手动同步过去才生效。
- 提交前先 `git status` 确认没有把 `venv/`、`node_modules/` 带进去（`.gitignore` 已挡住，但 `setup.ps1` 装出的其他产物未必）。

技能文件更新后 Cherry 会自动同步；`venv/` 与 `node_modules/` 不需要重建，除非依赖变化。
