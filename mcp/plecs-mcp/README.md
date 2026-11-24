# plecs-mcp 服务端

把 Cherry Studio（或任何 MCP 客户端）桥接到 **PLECS Standalone** 的 XML-RPC 接口（默认 `localhost:1080`）。

- **零依赖**：只用 Python 标准库（`json` / `math` / `os` / `struct` / `sys` / `time` / `csv` / `xmlrpc.client`）
- **协议**：MCP over stdio，逐行 JSON-RPC 2.0
- **版本**：1.3.0
- **实测环境**：PLECS Standalone 4.7.4（Windows）、Python 3.13

## 注册（Cherry Studio 设置 → MCP → 添加，类型 stdio）

| 字段 | 值 |
|---|---|
| 名称 | `plecs-mcp` |
| 命令 | 任意 Python 3.8+ 解释器（如 `D:\PRRRRRRODUCTIN\ServBay\packages\python\current\python.exe`） |
| 参数 | 本文件 `plecs_mcp_server.py` 的绝对路径 |

前置条件：PLECS 已启动，且 **Preferences → General → XML-RPC interface** 已勾选（端口 1080）。勾选后要重启 PLECS 生效。

环境变量 `PLECS_RPC_URL` 可覆盖 RPC 地址（如 `http://localhost:1080/RPC2`）。

## 工具

`plecs_status`、`plecs_help`、`plecs_load_model`、`plecs_close`、`plecs_get`、`plecs_set`、`plecs_simulate`、`plecs_scope`、`plecs_codegen`、`plecs_trace_read`、`plecs_call`。用法见技能 `skills/plecs-mcp/SKILL.md`。

## 1.3.0 新增：`.trace` 读波形

`plecs_trace_read` 解析 Scope 的 `SaveTraces` 产物，配套 `trace_reader.py`（自研，382 行，只用 `struct`，不包含任何第三方代码）。

格式是逆向出来的（PLECS 官方无文档）：大端、`version=2`、`nTrace` + 名称表（UTF-16BE）→ 一段未公开的变长元数据（不解释，靠结构校验跳过）→ 时间轴序列 → 每条曲线一组「40 字节序列头 + 信号数据」（同一曲线内第 2 条信号起多 36 字节附加描述）。

验证：5 个不同形状的样本（1~4 条曲线、每曲线 1~3 条信号、823~615348 点、最大 34 MB），其中 buck demo 与 `plecs_simulate` 的时间轴和两条通道**逐点完全相同**。

| 参数 | 作用 |
|---|---|
| `path` | `.trace` 文件路径 |
| `max_curves` | 只返回前 N 条曲线 |
| `stats_only` | 不保留数组，只算统计量（34 MB 文件 0.38 s） |
| `csv` | 导出 CSV（时间 + 每条曲线一列） |
| `preview_points` | 每条曲线抽几个点做预览 |

容易误读的地方：序列头里的 `ymax/ymin` 是**整条曲线的坐标轴范围**，同一曲线下的多条信号共用，不能当单条信号的最值。

## 1.2.0 相比 1.1.0 的改动

1. **`plecs_simulate` 不再把上下文塞满**
   - 结果超过 20000 字符时**自动**转成统计摘要（时间范围、每通道 min/max/mean/rms/p2p/点数），全量波形落到 `%TEMP%\plecs-mcp\sim_<模型>_<时间戳>.json`，响应里给路径。
   - 新增参数：`summary`（强制摘要）、`max_points`（抽点上限，摘要模式下作为预览点数）、`save_to`（指定落盘路径）。
   - 实测：一个 823 点的 buck demo 从 60015 字符降到 802 字符。
2. **截断不再产生非法 JSON**：超长时先退回紧凑格式，仍超长则返回一段合法说明对象，而不是半截 JSON。
3. **修中文被转义**：输出改为 `ensure_ascii=False`，中文直接可读。
4. **纠正 `plecs_set` 的描述**：`value` 传数字也能成功（服务端统一转字符串），原描述「PLECS 要求字符串」不准确。

## 注意

- `simulate` 是阻塞调用，同一时刻只能跑一个。
- RPC 仅监听 localhost，PLECS 与服务端必须同机。
- 判断 PLECS 是否可用看 **1080 端口**，不要看 `PLECS.exe` 进程——它可能只是个启动器，关窗口后会残留。
