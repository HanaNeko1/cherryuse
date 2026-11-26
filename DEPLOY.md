# 部署指南

供Agent阅读并执行。README 是索引，本文件是可操作的细节。

> 已经在本机部署过、只是要改仓库内容时，先跑 `scripts\prep.ps1`（见第 6 节），跳过下面全部内容。
>
> 另：`AQUARIUM.md`（水族箱）是常驻 agent「大肥鱼」的私有文件，**只读，任何其他 agent 不得修改**，详见 README「专属区域」。
>
> 要接 MATLAB / Simulink 时（官方 MCP，不含在本技能的安装流程里），照 [`mcp/matlab-mcp/README.md`](mcp/matlab-mcp/README.md) 做。

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
| plecs-mcp | `skills/plecs-mcp/SKILL.md`（还需装 PLECS 并注册 MCP 服务，见第 7 节） |

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
| ppt-master | `skills.sh:hugohe3/ppt-master/ppt-master` | MIT |

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
| ppt-master | 见第 8 节（需建 venv） |

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

## 6. 开工前同步（多机维护）

仓库同时在多台工作站上维护。每次动手改东西之前，先跑一次同步：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\prep.ps1
```

脚本会依次做四件事：

1. **定位仓库**：从脚本位置往上找 git 根目录，不用关心当前在哪个路径。
2. **收起本地未提交改动**：脏工作区会自动 `git stash --include-untracked`，同步完再 `git stash pop` 放回。
3. **同步远程**：`git fetch --prune` 后按情况快进（本地无新提交）或 rebase（两边都有提交）。冲突时自动 `rebase --abort`，本地提交和 stash 都不会丢。
4. **比对已安装技能**：把仓库里每个 `SKILL.md` 和 `%APPDATA%\CherryStudio\Data\Skills\<技能名>\SKILL.md` 做 SHA256 对比，列出「未安装」和「仓库已改但没重装」的技能。

参数：

| 参数 | 作用 |
|---|---|
| `-NoStash` | 工作区脏就直接失败，不自动 stash（想先看改动时用） |
| `-SkipDrift` | 跳过已安装技能比对 |

退出码：`0` 可以开工；`1` 不是git仓库/ detached HEAD / 拉取失败；`2` rebase 冲突，需要人工处理；`3` 有脏文件且给了 `-NoStash`。

看到 `PREP_OK` 就可以动手了。脚本只读远程、不改远程，安全。

## 7. PLECS 仿真接入（可选）

只有需要跑 PLECS 电热/电力电子仿真时才装。两层东西：一个 MCP 服务（桥接 PLECS 的 XML-RPC）+ 一个技能（告诉 Agent 怎么用这套工具）。

### 7.1 装 PLECS 与开 RPC

1. 装 PLECS Standalone（已验证 4.7.4；更高版本 RPC 命令集可能变）
2. 启动后 **File → PLECS Preferences → General**，勾选 **XML-RPC interface**，端口 **1080**
3. **重启 PLECS 生效**

开关持久化在注册表 `HKCU\Software\Plexim\PLECS4.7`（`XmlRpcEnabled` / `XmlRpcPort`），勾一次以后每次启动自动生效。

验证：端口在听即算通。

```powershell
Get-NetTCPConnection -LocalPort 1080 -State Listen
```

> 判定生死看**端口**，不要看进程名：`PLECS.exe` 可能只是个启动器，关窗口后会残留，但 RPC 已随 GUI 进程消失。

### 7.2 部署 MCP 服务

服务端代码就在本仓库：`mcp/plecs-mcp/plecs_mcp_server.py`（单文件、零依赖、只用标准库）。clone 下来就能用，**不需要 pip 装任何东西**。

1. 把 `plecs_mcp_server.py` 放到固定路径（如 `D:\plecs-mcp\`），或直接从 clone 目录引用
2. 在 Cherry Studio **设置 → MCP → 添加** 一个 stdio 服务：

| 字段 | 值 |
|---|---|
| 名称 | `plecs-mcp` |
| 命令 | `D:\PRRRRRRODUCTIN\ServBay\packages\python\current\python.exe`（任何装得到的 Python 3.8+ 都行） |
| 参数 | 服务端脚本的绝对路径 |

3. 保存后确认工具列表里出现 `plecs_status` / `plecs_simulate` 等十一个工具

改完服务端代码后要**重启 Cherry Studio**（或重新连接该 MCP）才会加载新版本。

### 7.3 装技能

```
安装这个技能：https://github.com/HanaNeko1/cherryuse/blob/main/skills/plecs-mcp/SKILL.md
```

装完建议顺手核对两件事（实测踩过）：

- 技能目录名应为 `plecs-cscript` 这类**技能名**，不是 `content`。装错名就改目录名并同步更新数据库里的 `folder_name`。
- 领域知识另外由 `plecs-cscript` 技能提供（原件：`github.com/alembrt-cmyk/plecs-skill`，MIT）。两者互补：`plecs-mcp` 讲本机工具层，`plecs-cscript` 讲元件、C-Script、`.plecs` 语法与排错。

## 8. PPT Master（可选，不在仓库内）

[MIT](https://github.com/hugohe3/ppt-master)，做可编辑 pptx 的分路线工作流。**不进仓库**：安装后 36 MB+、1.6 万个文件（模板库占大头），塞进 git 会让每台机器 clone 变慢。

### 8.1 安装

```
安装技能：skills.sh:hugohe3/ppt-master/ppt-master
```

装完**核对目录名**：应为 `Skills\ppt-master`。渠道偶尔会把目录名装成 `content`，这时需改目录名并同步数据库里的 `folder_name`。

### 8.2 依赖

要求 Python 3.10–3.14。在技能目录建独立 venv，**不要装到系统 Python 里**：

```powershell
$s  = "$env:APPDATA\CherryStudio\Data\Skills\ppt-master"
$uv = "$env:USERPROFILE\.cherrystudio\bin\uv.exe"
& $uv venv "$s\venv" --python 3.12
& $uv pip install --python "$s\venv\Scripts\python.exe" `
  PyYAML "python-pptx>=0.6.21" "XlsxWriter>=3.0.0" "skia-pathops>=0.9.2" "uharfbuzz>=0.50.0" `
  "Pillow>=9.0.0" "numpy>=1.20.0" "requests>=2.31.0" "beautifulsoup4>=4.12.0" `
  "markdownify>=0.11.6" "mammoth>=1.6.0" "openpyxl>=3.1.0" "edge-tts>=7.2.8" `
  "flask>=3.0.0" "curl_cffi>=0.7.0" --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**故意不装的依赖**：

| 包 | 为什么跳过 |
|---|---|
| `PyMuPDF` | **AGPL-3.0**。本仓库要再分发，不要沾它；只服务 PDF→Markdown 一条路，需要时单独装 |
| `google-genai` | AI 配图后端，需要 API key；不用 AI 配图就不装 |
| `nbconvert` / `ebooklib` | 仅 `.ipynb` / `.epub` 输入时需要 |
| `rapidocr` / `onnxruntime` | 仅 Image-to-PPTX 需要，带 OpenCV 约 170 MB |

### 8.3 验证

```powershell
$py = "$env:APPDATA\CherryStudio\Data\Skills\ppt-master\venv\Scripts\python.exe"
& $py "$env:APPDATA\CherryStudio\Data\Skills\ppt-master\scripts\attribution_guard.py"   # 必须 exit 0
```

`attribution_guard.py` 是作者内置的完整性校验门，返回非零就中止，**不要试图绕过**。

### 8.4 三个硬规则（踩过才知道）

1. **转换前必须有 `spec_lock.md`**，否则 `svg_to_pptx.py` 直接拒绝。模板在 `templates/scaffolds/spec_lock.md`。
2. **必须先有通过的质检报告**，否则拒绝发布：
   ```powershell
   & $py "...\scripts\svg_quality_checker.py" <项目路径> --canonical-authoring --stage final --json
   ```
3. **SVG 的书写约定**（质检器会逐条报错）：
   - 根 `<svg>` 必须带 `font-family` 默认值（否则中文宽度估算偏小）
   - 每个逻辑单元包在 `<g id="..." data-pptx-bounds="x y width height">` 里
   - 带 `data-pptx-role` 的元素必须有 `id`

### 8.5 已知问题

- 手写 SVG 里的中文文本**末尾单字会被挤到下一行**（宽度估算偏紧）。尚未跑完整工作流确认是否只是手写 SVG 的问题；用它的执行器生成页面时可能不复现。
- 项目建在 `<工作目录>/projects/<项目名>/` 下，不在技能目录里。在 Cherry 里用时把工作目录锚到会话工作区，否则文件会散。

## 9. 已知问题

**输入输出编码**：PowerShell 5.1 会把无 BOM 的 UTF-8 脚本按 ANSI 解析，中文提示会导致语法错误。本仓库的 `setup.ps1`、`scripts\prep.ps1` 全部使用英文输出。

**透明加密（DLP）**：部分企业机器上文件会被 DLP 加密（文件头 `%TSD-Header-###%`）。LibreOffice 导出的图片可能变成密文，Agent 读不到。校验生成结果时优先用 Python 直接渲染。

**PATH 生效时机**：脚本修改的是用户 PATH，已打开的终端不会刷新。执行完后新开终端，或用绝对路径调用。
