# MATLAB MCP Server（官方）接入指南

MathWorks 官方的 MATLAB MCP Server，让 AI Agent 执行 MATLAB 代码、跑脚本与测试、静态检查代码、探测已装工具箱。

- 上游：<https://github.com/matlab/matlab-mcp-server>
- 形态：Go 编译的单文件二进制，按平台分发，**无需 Python / Node**
- 本机实测：`v0.16.1` + MATLAB **R2024b**（Windows 11）

照着下面做完，任意一台机器约 5 分钟可跑通。

## 0. 前置条件

| 项 | 要求 | 检查 |
|---|---|---|
| MATLAB | **R2021a 或更高**，且 `matlab.exe` 在 PATH 里 | `matlab -batch "disp(version)"` |
| Simulink | **R2023a 或更高**（只有要用 Simulink 相关能力时才需要） | `matlab -batch "disp(ver('simulink').Version)"` |
| 授权 | 官方要求 MCP Server **只能配合 MATLAB 授权使用，且不得多人共享** | — |

> `matlab` 不在 PATH 时，注册 MCP 时加参数 `--matlab-root=<MATLAB 安装目录>`。

## 1. 下载二进制

从 GitHub Releases 取对应平台的资产（Windows 是 `matlab-mcp-server-windows-x64.exe`）。下面是 PowerShell 版，带官方 SHA256 校验：

```powershell
$ProgressPreference = 'SilentlyContinue'
$rel = Invoke-RestMethod 'https://api.github.com/repos/matlab/matlab-mcp-server/releases/latest' -Headers @{'User-Agent'='setup'}
$a   = $rel.assets | Where-Object { $_.name -eq 'matlab-mcp-server-windows-x64.exe' }
New-Item -ItemType Directory -Force 'D:\matlab-mcp' | Out-Null
$out = 'D:\matlab-mcp\matlab-mcp-server.exe'
Invoke-WebRequest $a.browser_download_url -OutFile $out -UseBasicParsing
$h = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
if ($a.digest -and $a.digest -ne "sha256:$h") { throw "SHA256 不匹配：$($a.digest) vs $h" }
& $out --version          # 应输出 github.com/matlab/matlab-mcp-server vX.Y.Z
```

放哪都行，本仓库约定 `D:\matlab-mcp\`（与 `D:\plecs-mcp\` 并列）。**路径不要放在需要管理员权限的目录**，MCP 客户端是普通权限启动的。

其他平台资产名：`matlab-mcp-server-linux-x64`、`matlab-mcp-server-macos-arm64`、`matlab-mcp-server-macos-x64`。

## 2. 注册到 Cherry Studio

**设置 → MCP → 添加**，类型 `stdio`：

| 字段 | 值 |
|---|---|
| 名称 | `matlab-mcp` |
| 类型 | `stdio` |
| 命令 | `D:\matlab-mcp\matlab-mcp-server.exe` |
| 参数 | `--disable-telemetry=true` |

参数说明：官方默认**开启匿名遥测**，`--disable-telemetry=true` 关掉。想保留就删掉这个参数。

注册完 **重启 Cherry Studio**（或等它重新列工具），工具名会以 `mcp__…__` 前缀出现。

## 3. 验证

```
调用 detect_matlab_toolboxes，告诉我 MATLAB 版本和装了哪些工具箱
```

本机实测：**22.8 秒**返回（首次调用要启动 MATLAB，慢是正常的），返回 R2024b + Simulink + 全套工具箱列表。

再验代码执行：

```
用 evaluate_matlab_code 跑 disp(sum(1:10))，应该是 55
```

再验 Simulink（可选，约 40 秒）：

```matlab
m = 't_mcpsmoke';
if bdIsLoaded(m), close_system(m, 0); end
new_system(m);
add_block('simulink/Sources/Constant', [m '/C'], 'Value', '3');
add_block('simulink/Math Operations/Gain', [m '/G'], 'Gain', '2');
add_block('simulink/Sinks/Out1', [m '/O']);
add_line(m, 'C/1', 'G/1', 'autorouting', 'on');
add_line(m, 'G/1', 'O/1', 'autorouting', 'on');
set_param(m, 'StopTime', '0.1', 'SaveOutput', 'on', 'SaveFormat', 'Array');
o = sim(m); fprintf('SIM_OK yout=%s size=%s\n', mat2str(o.get('yout')(end)), mat2str(size(o.get('yout'))));
close_system(m, 0);
```

本机实测输出：`SIM_OK yout=6 size=[51 1]`（3×2=6，51 个采样点）。

## 4. 工具清单（5 个）

| 工具 | 作用 | 必填 |
|---|---|---|
| `detect_matlab_toolboxes` | 列出 MATLAB 版本与已装工具箱 | — |
| `evaluate_matlab_code` | 执行一段代码，返回命令窗口输出 | `code`（+ 可选 `project_path` 作为工作目录） |
| `run_matlab_file` | 跑 `.m` / `.p` 文件 | `script_path` |
| `run_matlab_test_file` | 跑 MATLAB 单元测试 | `script_path` |
| `check_matlab_code` | 静态检查（`checkcode`），不执行 | `script_path` |

## 5. 可选组件

### 5.1 接管已打开的 MATLAB 会话（`.mltbx`）

默认行为是**自己启动一个 MATLAB**。想复用它已经开着的那个（保住 workspace 和已加载模型），需要装官方工具箱：

1. 从同一个 Release 下载 `MATLABMCPServerToolbox.mltbx`
2. 装进去：`matlab -batch "matlab.addons.toolbox.installToolbox('<绝对路径>.mltbx')"`
3. 在目标 MATLAB 会话里执行 `shareMATLABSession`

### 5.2 Simulink Agentic Toolkit（模型级工具 + 技能）

裸 MCP 只能执行代码；Simulink 模型级操作（`model_overview` / `model_read` / `model_edit` / `model_check` / `model_scan` / `model_query_params` / `model_resolve_params` / `model_read_diagnostics` / `model_test`）和**领域技能**来自另一个官方仓库：

- <https://github.com/matlab/simulink-agentic-toolkit>
- 要求 MATLAB **R2023a+** + Simulink；`model_test` 还要 Simulink Test

官方装法是 `agentic-toolkit-installer`，但它只自动配置 Claude Code / Copilot / Codex，**Cherry Studio 不在支持列表**，需要手动：

1. clone 该仓库，`skills-catalog/` 下每个技能都是独立目录（含 `SKILL.md` 和 `manifest.yaml`，后者声明依赖的产品）
2. 按需把技能目录拷进 `%APPDATA%\CherryStudio\Data\Skills\`
3. 模型级工具需要 MATLAB 侧注册工具函数路径，再用 MCP 服务器的 `--extension-file` 参数加载 `tools/tools.json`

> 这一步本机**尚未验证**。验证通过后再把步骤补全到这里，别照抄未验证的配置。

## 6. 已知问题

- **首次调用慢**：要启动 MATLAB，20~60 秒。之后同一会话内就快了。
- **`isError=true` 不一定是链路问题**：MATLAB 里代码报错也算工具失败。看返回文本里的 `matlab error:` 后面写了什么。
- **一次只能一个 MATLAB 实例**：MCP 服务器启动的 MATLAB 常驻；多会话并发会互相阻塞（workspace 和当前目录共享）。
- **长仿真会撞超时**：Cherry 侧 MCP 工具调用默认超时可能不够，跑长仿真时先在 MATLAB 侧确认时长，必要时改用 `run_matlab_file` 跑脚本。
- **RPC 语义差异**：它不提供「模型对象」接口，一切通过执行 MATLAB 代码完成；要结构化地读模型，得靠 5.2 的 Simulink 工具集。
