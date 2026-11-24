---
name: plecs-mcp
description: 本机 PLECS MCP 服务的接线层——用 plecs_status / load_model / get / set / simulate / scope / codegen / trace_read / call 这十一个工具驱动 PLECS Standalone（XML-RPC 1080）。当用户要跑 PLECS 仿真、改模型参数、读波形（含 .trace 文件）、批量扫参数，或遇到 PLECS 连不上（WinError 10061）、仿真报 stiffness/-34000、plecs_call 报 -32601/-32602、需要从摘要换回完整波形时使用。元件参数名、C-Script 写法、.plecs 私有语法、深度排错请看 plecs-cscript 技能。
---

# PLECS MCP（本机接线层）

只讲**本机这套 MCP 怎么用**。PLECS 领域知识（元件参数名、端子号、C-Script 模板、`.plecs` 私有语法、40 条排错表）在 `plecs-cscript` 技能里，别在这儿重复查。

## 链路

```
Agent ──MCP(stdio)──> plecs_mcp_server.py ──XML-RPC :1080──> PLECS Standalone
```

- 服务端：`mcp/plecs-mcp/plecs_mcp_server.py`（本仓库内，单文件、**零依赖**、只用标准库；本机运行副本在 `D:\plecs-mcp\`）
- 版本：1.2.0
- 启动：`D:\PRRRRRRODUCTIN\ServBay\packages\python\current\python.exe` + 上面那个脚本
- MCP 名字：`plecs-mcp`（stdio）
- 端口默认 1080，可用环境变量 `PLECS_RPC_URL` 覆盖（如 `http://localhost:1080/RPC2`）

## 十个工具

| 工具 | 必填参数 | 用途 |
|---|---|---|
| `plecs_status` | — | 连接自检，返回 `ok` 和 RPC 方法清单 |
| `plecs_help` | — | 内置命令速查 |
| `plecs_load_model` | `path` | 加载 `.plecs`，返回模型名 |
| `plecs_close` | — | 关闭模型（省略则关最近加载的） |
| `plecs_get` | `path`,`param` | 读参数，返回**字符串** |
| `plecs_set` | `path`,`param`,`value` | 写参数 |
| `plecs_simulate` | — | 跑仿真；支持 `params`/`solver_opts`/`model_name`/`summary`/`max_points`/`save_to` |
| `plecs_scope` | `scope_path` | Scope 操作（`ClearTraces` / `HoldTrace`） |
| `plecs_codegen` | `path` | 代码生成 |
| `plecs_trace_read` | `path` | 解析 `.trace`（Scope 的 SaveTraces 产物），可选 CSV / 预览 |
| `plecs_call` | `method` | 透传其他 PLECS RPC 方法 |

`path` 写法 `模型名/元件名`，例如 `buck_converter_with_parameter_sweep/R1`；`param` 是元件属性，常见 `R`、`C`、`L`、`Vf`、`Ron`。

## 开工检查顺序

```powershell
# 1. 端口在听吗——判断 PLECS 是否可用，看端口而不是进程名（见下方陷阱）
Get-NetTCPConnection -LocalPort 1080 -State Listen
```

然后 MCP 侧 `plecs_status`，返回 `ok:true` 才往下走。

**陷阱：`PLECS.exe` 可能只是个启动器。** 实测启动后有两个 PLECS 进程：一个 24MB、没有窗口标题、RPC 也不在它名下；真正干活的是另一个 200MB+、窗口标题为 `Library Browser` 的进程。用户关掉 PLECS 窗口后，启动器（24MB 那个）会**残留**，此时 `Get-Process PLECS` 仍然为真但端口已关。所以：**用 1080 是否 LISTEN 判断生死，别用进程名。**

RPC 开关持久化在注册表 `HKCU\Software\Plexim\PLECS4.7` → `XmlRpcEnabled=true`，勾过一次后每次启动自动生效。

## 已验证行为（PLECS 4.7.4，2026-11-24 实测）

| 项 | 结论 |
|---|---|
| `status` `load` `get` `set` `simulate` `close` `call` | 全部可用 |
| `plecs_set` 传数字 | **能成功**（服务端会转字符串），不必先手动转字符串 |
| `simulate` 取波形 | 模型**没有顶层 outport 也返回** `Time` + `Values` |
| `simulate` 阻塞性 | 是，同一时刻只能跑一个，调用要给足超时 |
| `plecs_call` 的 method | **相对 `plecs` 命名空间**：写 `statistics` 而不是 `plecs.statistics` |
| `plecs_call` 调 `system.*` | **调不到**（会被拼成 `plecs.system.xxx`），需要直连 xmlrpc |
| `analyze` 签名 | `[模型名, 分析类型, opts]`，分析类型必须**与模型 Analysis Tools 里定义的名字完全一致** |

## simulate 的返回值：摘要 / 抽点 / 落盘

服务端 1.2.0 起不会再把上下文塞满：

| 情况 | 行为 |
|---|---|
| 结果 < 20000 字符 | 直接返回 `Time` + `Values` |
| 结果 ≥ 20000 字符 | **自动**转统计摘要 + 全量落盘到 `%TEMP%\plecs-mcp\`，响应里给 `saved` 路径 |
| `summary=true` | 强制摘要，不回传波形数组 |
| `max_points=N` | 摘要模式下作为 `preview` 点数；普通模式下对 `Time`/`Values` 等间隔抽点（首尾必留） |
| `save_to=<路径>` | 指定落盘位置（目录自动创建），响应仍走摘要 |

摘要包含：`points`、`t_start`/`t_end`、每通道 `min`/`max`/`mean`/`rms`/`p2p`/`n`。实测一个 823 点的 buck demo：从 60015 字符降到 **802 字符**。

需要逐点数据时读 `saved` 指向的 JSON，别让模型把数组搬进上下文。

> 1.1.0 及以前会在 60000 字符处硬截断，得到的 JSON 是坏的、无法解析。如果看到「已截断」字样，说明跑的是旧版服务端，重启 Cherry 即可加载新版。

## 常见报错对照

| 报错 | 含义 | 处理 |
|---|---|---|
| `[WinError 10061] 积极拒绝` | PLECS 没开，或 RPC 没勾 | 看 1080 端口；必要时重启 PLECS |
| `-34000 ... model seems to become stiff` | 电路变刚性（常见于负载阻值改得极小） | 恢复原参数；或 `solver_opts` 切 Radau；或 Diagnostics → Stiffness detection 设为 warning |
| `-32601 requested method not found` | 方法名不对（常见于多写了 `plecs.` 前缀） | 去掉前缀，方法名相对 `plecs` |
| `-32602 invalid method parameters` | 参数个数/形状不对 | 按签名传，如 `analyze` 要三个位置参数 |
| `-32500 method execution error: Cannot find analysis named 'X'` | 参数对了，但模型里没有这个分析工具 | 换成模型里真实存在的分析名 |

## 取轨迹（模型没有 outport 时）

```python
# 1) 让 Scope 把轨迹存下来；第三个参数是“文件名”，会被拼到模型所在目录
plecs_call(method="scope", args=["模型名/Scope名", "SaveTraces", "trace_name"])

# 2) 解析（模型目录下的 trace_name.trace）
plecs_trace_read(path=r"D:\PLECS\demos\xxx\trace_name.trace", csv="out.csv")
```

实测要点：

- `SaveTraces` 第三个参数传**绝对路径无效**，会被当成文件名拼在模型目录后面；也**不要带 `.trace` 后缀**。
- `.trace` 里的 `ymax/ymin` 是整条曲线的坐标轴范围，同一曲线下多条信号共用，不是单信号最值。
- 大文件用 `stats_only=true`：34 MB / 61 万点 约 0.4 s。
- 实测 buck demo 的 `.trace` 与 `simulate` 时间轴和通道值**逐点完全相同**（均含 t=0）；若某次保存缺首拍，点数会少 1，工具不补点。

## 调参（PID / PI）前先要这张表

要调 PID/PI 时，**先让对方把下面这张表填完再动手**。文字描述（「快一点」「少点超调」）无法判定，也无法验收；填表能省掉大半来回。

```
模型：<绝对路径>
参数：<元件路径> / <参数名>  ×2（Kp、Ki）
初值：Kp=____  Ki=____
指标：超调≤__%  调节时间≤__ms  稳态误差≤__%  相位裕度≥__°
扰动：<负载阶跃 / 输入阶跃 / 启动过程>
范围：Kp ∈ [__ , __]，Ki ∈ [__ , __]
```

没填齐的部分不要自己拍：尤其**指标、扰动、参数范围**三项，拍错了后面所有仿真都白费。

拿到表之后按这个契约做：

1. **记原值**：`plecs_get` 先读一遍原参数，结束无条件还原（除非对方要留最优值）；模型不落盘。
2. **局部扫**：以初值为中心，每个参数先走 ±10%、±20% 看灵敏度与方向，再沿有效方向细化。不铺全网格。
3. **预算**：一轮 15~30 次仿真（每次 0.5~3 s）。超了就停下来报告「初值离可行域太远」，别硬跑。
4. **判据**：优先 AC Sweep 的穿越频率/相位裕度（平滑可复现），时域指标做验收；两者矛盾时以裕度为准。
5. **交叉验收**：最优解要在**未参与优化的工况**上复测（负载阶跃上升/下降、Vin 边界），防止只对一个扰动好看。
6. **交付**：Kp/Ki → 超调/调节时间/裕度 的对照表，标出最优解与敏感度（「再大 20% 会怎样」）。

分工上最有效率的是：**对方做粗调（解析计算 + 手动初值），本工具做局部精调**。初值离可行域越近，精调花的仿真越少。

## 参数覆盖

```python
plecs_simulate(params={"varL": "50e-6"})            # → ModelVars
plecs_simulate(solver_opts={"SolverType": "Radau"}) # → SolverOpts
```

`SolverOpts` 会被接受，但**是否真正生效未经验证**（传 Radau 后波形点数与默认一致）。要确认就比 `Time` 数组长度。

## 和别家 PLECS MCP 的差异

网上其他实现（haitangccy/plecs-mcp、alembrt-cmyk/plecs-mcp）工具更多（11 / 19 个），但都要 `mcp[cli]` + `pyyaml` 依赖；本机这套零依赖。别家有的东西本机怎么替代：

| 别家工具 | 本机替代 |
|---|---|
| `plecs_connect` | `plecs_status` |
| `plecs_analyze` | `plecs_call("analyze", [模型, 类型, opts])` |
| `plecs_trace_read` | 本机同名工具，自研解析器（零依赖） |
| `plecs_file_get/set`（直接改 `.plecs` 文本） | 无；参数批量改优先用 `plecs_set`，文件级改动按 `.plecs` 语法手工编辑或用 `plecs-cscript` 里的 builder |
| `plecs_save` | **RPC 不提供该命令**（4.7.4 实测报 -32601），不是本机没实现 |

### 为什么这三项没做

边界原则：**MCP 只包 PLECS RPC 真正暴露的东西，文件级/格式级的活留在技能层。**

1. **`save`**：4.7.4 的方法清单里没有它，硬做只能绕路改文件，而那会让 PLECS 自己的内存状态和磁盘不一致（它不知道文件被外部改了）——比不做更危险。
2. **`.plecs` 文本读写**：这类操作的失败是**静默**的——字段名写错不会报错，PLECS 会用默认值，仿真照跑但结果是错的。验证成本远高于 RPC 封装，而本仓库是多机同步的，错一次会同步到所有机器。何况 `plecs-cscript` 已经带了格式说明和带静态自检的 builder。
3. **`.trace` 解析**：已补。取数流程是 `plecs_scope` 的 `SaveTraces` → `plecs_trace_read`。解析器是自研的（400 行左右，只用 `struct`），格式靠逆向 5 个不同形状的样本得出，再用 `simulate` 逐点对账验证。当初没直接用现成实现，是因为能找到的那个解析器所在仓库**没有 LICENSE**（同类技能仓库是 MIT，但那份 MCP 仓库不是），不能确定可以再分发。

## 安全边界

- 改参数只改内存里的模型，`close` 不保存，原始 `.plecs` 不动。**但别在别人的模型上乱改后随手 Ctrl+S。**
- 代码生成会往模型目录写文件，执行前先看清 `path`。
- RPC 只监听 localhost，跨机连不上是设计如此。
