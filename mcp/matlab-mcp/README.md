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

官方装法是 `agentic-toolkit-installer`，但它只自动配 Claude Code / Copilot / Codex，**Cherry Studio 不在支持列表**，所以手动两步。下面是本机（R2024b）实跑通的步骤。

#### 第一步：把工具函数挂到 MATLAB 路径

```powershell
git clone --depth 1 https://github.com/matlab/simulink-agentic-toolkit.git D:\matlab-mcp\agentic-toolkits\simulink-agentic-toolkit
```

然后在 MATLAB 里执行一次（会持久化到 `pathdef`）：

```matlab
tk = 'D:\matlab-mcp\agentic-toolkits\simulink-agentic-toolkit\tools';
addpath(genpath(tk));
savepath;
which model_overview     % 应指向 ...\tools\model_overview\model_overview.p
```

九个函数全部应能 `which` 到（都是 `.p` 文件）：`model_overview`、`model_read`、`model_query_params`、`model_resolve_params`、`model_edit`、`model_read_diagnostics`、`model_check`、`model_scan`、`model_test`。

#### 第二步：给 MCP 服务器加 `--extension-file`

参数追加到注册项（可与其他参数共存，可重复多次）：

```
--extension-file=D:\matlab-mcp\agentic-toolkits\simulink-agentic-toolkit\tools\tools.json
```

`tools.json` 里定义了 9 个工具和它们到同名 MATLAB 函数的映射（`signatures` 段给了位置参数顺序）。加完后重启 Cherry，工具总数从 5 → **14**。

> ⚠️ **在 Cherry 里改参数会新增一条定义，不是覆盖**。用 MCP 管理工具重新注册时如果参数变了，会生成第二个同名 server（新旧各启一个进程）。改完去数据库或设置页确认只有一条，旧的要删掉。

#### 实测结论（PLECS 4.7.4 那套的经验同样适用：只写跑过的）

| 工具 | 实测 |
|---|---|
| `model_scan` | ✅ 正则扫磁盘上的 `.slx`，返回 `blk_N` id 与命中上下文。**模型有未保存修改会返回 `MODEL_LOCKED`** |
| `model_read` | ✅ 给出块的 id、类型、表达式（`y1 = u1 - u2 where u1=blk_1.y1`），可直接用于 `model_edit` |
| `model_overview` | ✅ 层级视图；注意扁平模型（全在 root、无子系统）的 `connections` 会是空，不代表没连线 |
| `model_resolve_params` | ✅ 把 `Kp` 解析成 `2`（来自 base workspace）。**这个会编译模型**，模型有未接端口时会报 `OPERATION_FAILED` |
| `model_edit` | ✅ `configure` 改 Gain 成功；改错块类型时会给可用参数提示（如「Gain 不在 Sum 上，可用 Inputs/OutMin」） |
| `model_query_params` | ✅ 回读到新值 `"5"` |
| `model_check` | ✅ 连完后返回 `status: healthy` |
| `model_read_diagnostics` | ✅ 可用；**`detail="summary"` 时不能再传 `limit`**（会报 INVALID_PARAM） |
| `model_test` | ⚠️ **未验证**：需要 Simulink Test + 带 TOML front-matter 的 Gherkin 规格文件，格式得照 `testing-simulink-models` 技能写 |

#### 造模型时踩到的坑

- **Outport 没有输出端口**。`add_line(m, 'yout/1', 'Err/2')` 会报「对象名称无效」——因为 `yout` 是 Outport，只有输入口。反馈要从上游块的输出端口分支：`add_line(m,'Plant/1','Err/2')`。
- **`add_line` 用相对名**（`'Plant/1'`），全路径（`'model/Plant/1'`）反而报错。
- `sim()` 的 `yout` 默认是 `Simulink.SimulationData.Dataset`，不是 double 数组，索引前要取元素或改 `SaveFormat='Array'`。

## 6. 已知问题

- **首次调用慢**：要启动 MATLAB，20~60 秒。之后同一会话内就快了。
- **`isError=true` 不一定是链路问题**：MATLAB 里代码报错也算工具失败。看返回文本里的 `matlab error:` 后面写了什么。
- **一次只能一个 MATLAB 实例**：MCP 服务器启动的 MATLAB 常驻；多会话并发会互相阻塞（workspace 和当前目录共享）。
- **长仿真会撞超时**：Cherry 侧 MCP 工具调用默认超时可能不够，跑长仿真时先在 MATLAB 侧确认时长，必要时改用 `run_matlab_file` 跑脚本。
- **RPC 语义差异**：它不提供「模型对象」接口，一切通过执行 MATLAB 代码完成；要结构化地读模型，得靠 5.2 的 Simulink 工具集。
