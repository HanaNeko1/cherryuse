# 部署指南

供Agent阅读并执行。README 是索引，本文件是可操作的细节。

## 0. 前置检查

```powershell
uv --version
bun --version
git --version
```

缺失时：

| 工具 | 安装 |
|---|---|
| uv | `winget install --id=astral-sh.uv -e` |
| git | `winget install --id=Git.Git -e` |
| bun | 通常随 Cherry Studio 提供；缺失则安装 Node.js |

可选：LibreOffice（docx/pptx 的渲染校验、`.doc` 转换）。

## 1. 安装技能

### 方式 A：从本仓库安装（默认）

执行：

> 安装这个技能：https://github.com/HanaNeko1/cherryuse/blob/main/skills/<路径>/SKILL.md

| 技能 | 路径 |
|---|---|
| tech-diagram | `skills/tech-diagram/SKILL.md` |
| docx | `skills/document/docx/SKILL.md` |
| pdf | `skills/document/pdf/SKILL.md` |
| pptx | `skills/document/pptx/SKILL.md` |
| xlsx-manipulation | `skills/document/xlsx-manipulation/SKILL.md` |
| officecli-docx | `skills/document/officecli-docx/SKILL.md` |
| officecli-academic-paper | `skills/document/officecli-academic-paper/SKILL.md` |
| humanizer-zh-academic | `skills/humanizer-zh-academic/SKILL.md` |

### 方式 B：从原始来源安装

适用场景：本仓库不可用、某技能许可证不明确不希望再分发、或需要上游最新版本。

| 技能 | 原始安装源 | 许可 |
|---|---|---|
| docx | `skills.sh:anthropics/skills/docx` | Apache-2.0 |
| pdf | `skills.sh:anthropics/skills/pdf` | Apache-2.0 |
| pptx | `skills.sh:anthropics/skills/pptx` | Apache-2.0 |
| xlsx-manipulation | `skills.sh:claude-office-skills/skills/xlsx-manipulation` | MIT |
| officecli-docx | `clawhub:iceyliu/officecli-docx` | 未标注 |
| officecli-academic-paper | `clawhub:iceyliu/officecli-academic-paper` | 未标注 |
| humanizer-zh-academic | `https://skills.sh/redbaronyyyyy-eng/humanizer-zh-academic/humanizer-zh-academic` | MIT |

用法：对 Agent 说「安装技能：`clawhub:iceyliu/officecli-docx`」，或直接给对应页面的 URL。

> `officecli-docx` 与 `officecli-academic-paper` 在公开仓库中的再分发未获明确授权。如果不想依赖本仓库，请用上表的原始来源安装。

## 2. 初始化依赖

在技能目录下执行一次。技能安装后位于 `%APPDATA%\CherryStudio\Data\Skills\<技能名>`。

| 技能 | 命令 |
|---|---|
| docx | `powershell -ExecutionPolicy Bypass -File "$env:APPDATA\CherryStudio\Data\Skills\docx\setup.ps1"` |
| pdf | 同上，路径换成 `pdf`；需要 OCR 时加 `-InstallOcr` |
| pptx | 同上，路径换成 `pptx` |
| xlsx-manipulation | 同上，路径换成 `xlsx-manipulation` |
| officecli-academic-paper | 同上，路径换成 `officecli-academic-paper`；CLI 未装时加 `-Install` |
| tech-diagram | 同上，路径换成 `tech-diagram` |
| humanizer-zh-academic | 无依赖 |

成功标志：输出包含 `SETUP_OK`（pdf 的 OCR 部分输出 `OCR_OK`）。

## 3. officecli CLI（两个 officecli 技能必需）

### 自动安装

```powershell
powershell -ExecutionPolicy Bypass -File "$env:APPDATA\CherryStudio\Data\Skills\officecli-academic-paper\setup.ps1" -Install
```

脚本会：

1. 查询 `iOfficeAI/OfficeCLI` 的最新 GitHub Release
2. 下载 `officecli-win-x64.exe`
3. 用同版本的 `SHA256SUMS` 校验
4. 安装到 `%LOCALAPPDATA%\Programs\officecli\officecli.exe`
5. 加入用户 PATH

### 手动安装

1. 打开 <https://github.com/iOfficeAI/OfficeCLI/releases>
2. 下载对应资产：`officecli-win-x64.exe`（Windows x64）、`officecli-mac-arm64`、`officecli-mac-x64`、`officecli-linux-x64`、`officecli-linux-arm64`
3. Windows：核对 `SHA256SUMS`，重命名为 `officecli.exe`，放到一个固定目录并加入 PATH
4. 验证：`officecli --version`

> 只从 `iOfficeAI/OfficeCLI` 的 Releases 下载。不要执行来路不明的安装脚本。

## 4. OCR（pdf 技能，可选）

只有处理扫描版 PDF 时才需要。

### 自动安装

```powershell
powershell -ExecutionPolicy Bypass -File "$env:APPDATA\CherryStudio\Data\Skills\pdf\setup.ps1" -InstallOcr
```

脚本会：

1. `winget install -e --id UB-Mannheim.TesseractOCR` 安装 Tesseract
2. 从 `oschwartz10612/poppler-windows` 最新 Release 下载 zip
3. 解压到 `%LOCALAPPDATA%\Programs\poppler`
4. 把其中的 `Library\bin` 加入用户 PATH

### 手动安装

| 组件 | 来源 |
|---|---|
| Tesseract | `winget install -e --id UB-Mannheim.TesseractOCR` |
| Poppler | <https://github.com/oschwartz10612/poppler-windows/releases> 下载 zip，解压后把 `Library\bin` 加入 PATH |

验证：`tesseract --version`、`pdftoppm -v`。

## 5. 验证清单

```powershell
officecli --version
tesseract --version
pdftoppm -v
soffice --version          # 可选
```

Python 依赖逐个确认：

```powershell
& "$env:APPDATA\CherryStudio\Data\Skills\pdf\venv\Scripts\python.exe" -c "import pypdf, pdfplumber, reportlab, pypdfium2; print('pdf ok')"
& "$env:APPDATA\CherryStudio\Data\Skills\pptx\venv\Scripts\python.exe" -c "import pptx; print('pptx ok')"
& "$env:APPDATA\CherryStudio\Data\Skills\xlsx-manipulation\venv\Scripts\python.exe" -c "import openpyxl; print('xlsx ok')"
```

## 6. 已知问题

**PowerShell 编码**：PowerShell 5.1 会把无 BOM 的 UTF-8 脚本按 ANSI 解析，中文提示会导致语法错误。本仓库的 `setup.ps1` 全部使用英文输出。

**透明加密（DLP）**：部分企业机器上文件会被 DLP 加密（文件头 `%TSD-Header-###%`）。LibreOffice 导出的图片可能变成密文，Agent 读不到。校验生成结果时优先用 Python 直接渲染。

**PATH 生效时机**：脚本修改的是用户 PATH，已打开的终端不会刷新。执行完后新开终端，或用绝对路径调用。
