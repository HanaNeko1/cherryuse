# plecs-mcp 服务端

把 Cherry Studio（或任何 MCP 客户端）桥接到 **PLECS Standalone** 的 XML-RPC 接口（默认 `localhost:1080`）。

- **零依赖**：只用 Python 标准库（`json` / `math` / `os` / `sys` / `time` / `xmlrpc.client`）
- **协议**：MCP over stdio，逐行 JSON-RPC 2.0
- **版本**：1.2.0
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

`plecs_status`、`plecs_help`、`plecs_load_model`、`plecs_close`、`plecs_get`、`plecs_set`、`plecs_simulate`、`plecs_scope`、`plecs_codegen`、`plecs_call`。用法见技能 `skills/plecs-mcp/SKILL.md`。

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
