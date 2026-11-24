# 部署指南

供Agent阅读并执行。README 是索引，本文件是可操作的细节。

> 已经在本机部署过、只是要改仓库内容时，先跑 `scripts\prep.ps1`（见第 6 节），跳过下面全部内容。
>
> 另：`AQUARIUM.md`（水族箱）是常驻 agent「大肥鱼」的私有文件，**只读，任何其他 agent 不得修改**，详见 README「专属区域」。

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

3. 保存后确认工具列表里出现 `plecs_status` / `plecs_simulate` 等十个工具

改完服务端代码后要**重启 Cherry Studio**（或重新连接该 MCP）才会加载新版本。

### 7.3 装技能

```
安装这个技能：https://github.com/HanaNeko1/cherryuse/blob/main/skills/plecs-mcp/SKILL.md
```

装完建议顺手核对两件事（实测踩过）：

- 技能目录名应为 `plecs-cscript` 这类**技能名**，不是 `content`。装错名就改目录名并同步更新数据库里的 `folder_name`。
- 领域知识另外由 `plecs-cscript` 技能提供（原件：`github.com/alembrt-cmyk/plecs-skill`，MIT）。两者互补：`plecs-mcp` 讲本机工具层，`plecs-cscript` 讲元件、C-Script、`.plecs` 语法与排错。

## 8. 已知问题

**输入输出编码**：PowerShell 5.1 会把无 BOM 的 UTF-8 脚本按 ANSI 解析，中文提示会导致语法错误。本仓库的 `setup.ps1`、`scripts\prep.ps1` 全部使用英文输出。

**透明加密（DLP）**：部分企业机器上文件会被 DLP 加密（文件头 `%TSD-Header-###%`）。LibreOffice 导出的图片可能变成密文，Agent 读不到。校验生成结果时优先用 Python 直接渲染。

**PATH 生效时机**：脚本修改的是用户 PATH，已打开的终端不会刷新。执行完后新开终端，或用绝对路径调用。
