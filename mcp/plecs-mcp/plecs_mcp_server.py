#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLECS MCP Server —— 通过 stdio 桥接 Cherry Studio 与 PLECS Standalone 的 XML-RPC 接口。

零依赖：仅使用 Python 标准库（xmlrpc.client / json / sys / math / os）。
协议：MCP (Model Context Protocol) over stdio，逐行 JSON-RPC 2.0。

用法（stdio 模式，由 Cherry Studio 等 MCP 客户端拉起）：
    python plecs_mcp_server.py

环境变量（可选）：
    PLECS_RPC_URL    PLECS RPC 地址，默认 http://localhost:1080
                     （若连接失败，可尝试 http://localhost:1080/RPC2）
"""

import json
import math
import os
import sys
import time
import xmlrpc.client

PLECS_RPC_URL = os.environ.get("PLECS_RPC_URL", "http://localhost:1080")
SERVER_INFO = {"name": "plecs-mcp", "version": "1.3.0"}
MAX_OUTPUT_CHARS = 60000

# 仿真结果超过这个体积就自动转成摘要 + 落盘，避免把上下文塞满
AUTO_SUMMARY_CHARS = 20000
# summary 模式下如果需要预览，默认抽成这么多点（除非调用方自己给 max_points）
SIM_DUMP_DIR = os.path.join(os.environ.get("TEMP") or os.environ.get("TMP") or ".", "plecs-mcp")

# 最近一次 load 的模型名，供 simulate / close 省略 model_name 时回退使用
_last_model = None


def log(*args):
    """调试日志写到 stderr，不影响 stdio 上的协议输出。"""
    print("[plecs-mcp]", *args, file=sys.stderr, flush=True)


def get_proxy():
    """创建 PLECS XML-RPC 代理。HTTP 无状态，每次新建即可。"""
    return xmlrpc.client.ServerProxy(PLECS_RPC_URL, allow_none=True)


CONNECTION_HINT = (
    "无法连接 PLECS RPC（{}）。请确认：1) PLECS Standalone 已启动；"
    "2) File → PLECS Preferences → General 勾选 XML-RPC interface 并设端口 1080，然后重启 PLECS；"
    "3) 若仍失败，把环境变量 PLECS_RPC_URL 设为 http://localhost:1080/RPC2 重试。"
)


def _call(fn):
    """执行一次 RPC 调用，把 Fault / 连接错误统一转成带清晰提示的 RuntimeError。"""
    try:
        return fn()
    except xmlrpc.client.Fault as f:
        raise RuntimeError("PLECS 返回错误（{} {}）".format(f.faultCode, f.faultString)) from f
    except Exception as e:
        raise RuntimeError(CONNECTION_HINT.format(e)) from e


def _sanitize(obj):
    """把 XML-RPC 返回结果转成 JSON 安全数据（处理 NaN/Inf/Binary/DateTime）。"""
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj):
            return "NaN"
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        return obj
    if isinstance(obj, xmlrpc.client.DateTime):
        return str(obj)
    if isinstance(obj, xmlrpc.client.Binary):
        return {"__binary__": len(obj.data)}
    return obj


def _dumps(result):
    """序列化成 JSON 文本。超长时**绝不**返回被截断的半截 JSON：
    先试紧凑格式，仍超长就返回一个合法的说明对象，让调用方知道发生了什么。"""
    data = _sanitize(result)
    pretty = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if len(pretty) <= MAX_OUTPUT_CHARS:
        return pretty
    compact = json.dumps(data, ensure_ascii=False, default=str)
    if len(compact) <= MAX_OUTPUT_CHARS:
        log("output too long for pretty-print, fell back to compact json", len(compact))
        return compact
    log("output exceeds limit even compact, returning stub", len(compact))
    return json.dumps({
        "truncated": True,
        "chars": len(compact),
        "limit": MAX_OUTPUT_CHARS,
        "message": "结果过大，未返回完整数据（截断会产生非法 JSON，所以改为返回这段说明）。",
        "hint": "plecs_simulate 支持 summary / max_points / save_to 三个参数，用它取摘要或落盘。",
    }, ensure_ascii=False, indent=2, default=str)


def _channel_stats(values):
    """一通道波形的统计量；非数值项忽略。"""
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    n = len(nums)
    lo, hi = min(nums), max(nums)
    return {
        "min": lo,
        "max": hi,
        "mean": sum(nums) / n,
        "rms": math.sqrt(sum(v * v for v in nums) / n),
        "p2p": hi - lo,
        "n": n,
    }


def _summarize_sim(result):
    """把 {'Time': [...], 'Values': [[...], ...]} 压成统计摘要。"""
    if not isinstance(result, dict) or "Time" not in result:
        return {"raw": result}
    t = result.get("Time") or []
    vals = result.get("Values") or []
    out = {"points": len(t)}
    if t:
        out["t_start"] = t[0]
        out["t_end"] = t[-1]
    chans = []
    for i, ch in enumerate(vals):
        s = _channel_stats(ch) if isinstance(ch, list) else None
        if s is None:
            s = {"note": "非数值通道"}
        s["channel"] = i
        chans.append(s)
    out["channels"] = chans
    extra = {k: v for k, v in result.items() if k not in ("Time", "Values")}
    if extra:
        out["extra"] = extra
    return out


def _downsample(seq, max_points):
    """等间隔抽点，保留首尾。max_points <= 0 或本来就够少时原样返回。"""
    if not isinstance(seq, list) or not max_points or max_points <= 0:
        return seq
    n = len(seq)
    if n <= max_points:
        return seq
    step = n / float(max_points)
    idx = sorted({min(int(i * step), n - 1) for i in range(max_points)} | {n - 1})
    return [seq[i] for i in idx]


def _write_json(path, payload):
    """把完整结果写到文件，目录不存在就建。返回绝对路径。"""
    path = os.path.abspath(os.path.expanduser(path))
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_sanitize(payload), f, ensure_ascii=False, default=str)
    return path


def _dump_sim(model_name, result):
    """自动落盘到 TEMP。"""
    os.makedirs(SIM_DUMP_DIR, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (model_name or "model"))
    name = "sim_{}_{}.json".format(safe, time.strftime("%Y%m%d-%H%M%S"))
    return _write_json(os.path.join(SIM_DUMP_DIR, name), result)


def _tool_result(result):
    return {"content": [{"type": "text", "text": _dumps(result)}], "isError": False}


def _tool_error(message):
    return {"content": [{"type": "text", "text": str(message)}], "isError": True}


# --------------------------------------------------------------------------
# 工具实现
# --------------------------------------------------------------------------

def tool_status(args):
    """检查与 PLECS RPC 的连接状态。"""
    proxy = get_proxy()
    try:
        methods = proxy.system.listMethods()
        return {"ok": True, "url": PLECS_RPC_URL, "note": "已连接", "methods": methods}
    except xmlrpc.client.Fault:
        return {"ok": True, "url": PLECS_RPC_URL, "note": "已连接（无自省）"}
    except Exception as e:
        return {"ok": False, "url": PLECS_RPC_URL, "error": str(e),
                "hint": "确认 PLECS 已启动并在 Preferences 中开启 RPC（端口 1080）"}


def tool_load_model(args):
    """加载 .plecs 模型文件，并记录模型名供后续 simulate/close 回退。"""
    global _last_model
    path = args.get("path")
    if not path:
        raise RuntimeError("缺少参数 path（.plecs 文件的绝对路径）")
    proxy = get_proxy()
    result = _call(lambda: proxy.plecs.load(path))
    _last_model = os.path.splitext(os.path.basename(path))[0]
    return {"ok": True, "loaded": path, "model": _last_model, "result": result}


def tool_close(args):
    """关闭模型（默认关闭最近加载的模型）。"""
    model_name = args.get("model_name") or _last_model
    if not model_name:
        raise RuntimeError("缺少 model_name（要关闭的模型名，不含 .plecs 扩展名）")
    proxy = get_proxy()
    result = _call(lambda: proxy.plecs.close(model_name))
    return {"ok": True, "closed": model_name, "result": result}


def tool_get(args):
    """读取元件参数值（返回字符串）。"""
    path = args.get("path")
    param = args.get("param")
    if not path:
        raise RuntimeError("缺少 path（元件路径，如 'ModelName/R1'）")
    if not param:
        raise RuntimeError("缺少 param（参数名，如 'R'）")
    proxy = get_proxy()
    value = _call(lambda: proxy.plecs.get(path, param))
    return {"path": path, "param": param, "value": value}


def tool_set(args):
    """设置元件参数。value 可传字符串或数字，统一转成字符串再发给 PLECS。"""
    path = args.get("path")
    param = args.get("param")
    value = args.get("value")
    if not path:
        raise RuntimeError("缺少 path（元件路径，如 'ModelName/R1'）")
    if not param:
        raise RuntimeError("缺少 param（参数名，如 'R'）")
    if value is None:
        raise RuntimeError("缺少 value（字符串，如 '22000' 或 '22e3'）")
    value_str = value if isinstance(value, str) else str(value)
    proxy = get_proxy()
    result = _call(lambda: proxy.plecs.set(path, param, value_str))
    return {"path": path, "param": param, "value": value_str, "result": result}


def tool_simulate(args):
    """运行仿真。结果过大时自动转摘要 + 落盘，避免把上下文塞满。"""
    model_name = args.get("model_name")
    params = args.get("params") or {}
    solver_opts = args.get("solver_opts") or {}
    want_summary = bool(args.get("summary"))
    max_points = args.get("max_points")
    save_to = args.get("save_to")

    if not model_name:
        model_name = _last_model
        if not model_name:
            raise RuntimeError(
                "未指定 model_name，且没有通过 plecs_load_model 加载过模型。"
                "请传入 model_name（模型名，不含 .plecs 扩展名）。")

    opts = {}
    if params:
        opts["ModelVars"] = params
    if solver_opts:
        opts["SolverOpts"] = solver_opts

    proxy = get_proxy()
    if opts:
        result = _call(lambda: proxy.plecs.simulate(model_name, opts))
    else:
        result = _call(lambda: proxy.plecs.simulate(model_name))

    # 体积估算用紧凑格式：紧凑都超限才是真的超
    approx = len(json.dumps(_sanitize(result), ensure_ascii=False, default=str))

    saved = None
    if save_to:
        saved = _write_json(save_to, result)

    if want_summary or approx > AUTO_SUMMARY_CHARS:
        if saved is None:
            saved = _dump_sim(model_name, result)
        out = {
            "model": model_name,
            "summary": _summarize_sim(result),
            "saved": saved,
            "chars": approx,
            "note": "波形全量已落盘，本响应只含统计摘要；需要逐点数据请读 saved 指向的 JSON。",
        }
        if max_points:
            t = result.get("Time") or []
            vals = result.get("Values") or []
            keep = _downsample(list(range(len(t))), max_points)
            out["preview"] = {
                "Time": [t[i] for i in keep],
                "Values": [[ch[i] for i in keep] for ch in vals if isinstance(ch, list)],
                "note": "等间隔抽点，首尾保留",
            }
        return out

    payload = {"model": model_name, "result": result}
    if max_points and isinstance(result, dict):
        t = result.get("Time") or []
        vals = result.get("Values") or []
        keep = _downsample(list(range(len(t))), max_points)
        payload["result"] = {
            "Time": [t[i] for i in keep],
            "Values": [[ch[i] for i in keep] for ch in vals if isinstance(ch, list)],
            "note": "已按 max_points 抽点",
        }
    return payload


def tool_scope(args):
    """对 Scope 执行操作（清空轨迹 / 保持轨迹等）。"""
    scope_path = args.get("scope_path")
    if not scope_path:
        raise RuntimeError("缺少 scope_path（如 'ModelName/Scope'）")
    action = args.get("action", "ClearTraces")
    extra = []
    if args.get("label") is not None:
        extra.append(args["label"])
    if args.get("param") is not None:
        extra.append(args["param"])

    proxy = get_proxy()
    result = _call(lambda: proxy.plecs.scope(scope_path, action, *extra))
    return {"ok": True, "scope": scope_path, "action": action, "result": result}


def tool_trace_read(args):
    """解析 .trace（Scope 的 SaveTraces 产物），返回每通道统计量。

    解析器为自研实现（见 trace_reader.py），对照 PLECS 4.7.4 的 simulate 输出逐点验证过。
    """
    path = args.get("path")
    if not path:
        raise RuntimeError("缺少 path（.trace 文件的绝对路径）")
    if not os.path.exists(path):
        raise RuntimeError("文件不存在：{}".format(path))
    try:
        from trace_reader import read_trace, write_csv, TraceError
    except ImportError as e:
        raise RuntimeError("缺少 trace_reader.py（需与本脚本放在同一目录）：{}".format(e)) from e

    max_curves = args.get("max_curves") or 0
    stats_only = bool(args.get("stats_only"))
    csv_path = args.get("csv")
    preview_points = args.get("preview_points") or 0

    try:
        curves = read_trace(path, max_curves=int(max_curves), keep=not stats_only)
    except TraceError as e:
        raise RuntimeError("解析 .trace 失败：{}".format(e)) from e

    out_curves = []
    for i, c in enumerate(curves):
        st = c.stats()
        item = {
            "index": i,
            "trace": c.trace,
            "signal": c.signal,
            "n": st.get("n"),
            "min": st.get("min"),
            "max": st.get("max"),
            "mean": st.get("mean", st.get("avg")),
            "rms": st.get("rms"),
            "p2p": st.get("p2p", st.get("pp")),
        }
        if c.t and not stats_only:
            item["t_start"] = c.t[0]
            item["t_end"] = c.t[-1]
        if preview_points and c.t and not stats_only:
            step = max(1, len(c.t) // int(preview_points))
            item["preview"] = {
                "t": c.t[::step][:int(preview_points)],
                "v": c.v[::step][:int(preview_points)],
            }
        out_curves.append(item)

    result = {
        "path": os.path.abspath(path),
        "size": os.path.getsize(path),
        "curve_count": len(curves),
        "curves": out_curves,
    }
    if csv_path:
        if stats_only:
            result["csv"] = None
            result["note"] = "stats_only=true 时数据未保留，未导出 CSV"
        else:
            result["csv"] = write_csv(csv_path, curves)
    return result


def tool_codegen(args):
    """对模型 / 子系统生成代码（签名待对照本机文档验证）。"""
    path = args.get("path")
    if not path:
        raise RuntimeError("缺少 path（模型名或子系统路径，如 'ModelName/Subsystem'）")
    opt_struct = args.get("opt_struct")
    output_dir = args.get("output_dir")

    a = [path]
    if opt_struct is not None:
        a.append(opt_struct)
    if output_dir is not None:
        a.append(output_dir)

    proxy = get_proxy()
    result = _call(lambda: proxy.plecs.codegen(*a))
    return {"ok": True, "path": path, "result": result}


def tool_call(args):
    """通用透传：调用任意 PLECS RPC 命令（analyze / statistics / webserver 等未单独封装的命令）。"""
    method = args.get("method")
    if not method:
        raise RuntimeError("缺少 method（如 'analyze' / 'statistics' / 'codegen' 等）")
    call_args = args.get("args")
    if call_args is None:
        call_args = []
    elif not isinstance(call_args, list):
        call_args = [call_args]

    proxy = get_proxy()
    fn = getattr(proxy.plecs, method)
    result = _call(lambda: fn(*call_args))
    return {"method": method, "result": result}


COMMAND_REFERENCE = (
    "PLECS Standalone RPC 命令（本机 4.7.4 实测验证）：\n"
    "  load(modelFile)                        加载 .plecs 模型（绝对路径），返回 0\n"
    "  get(path, param)                       读元件参数，返回字符串；如 get('Model/R1','R') -> '11e3'\n"
    "  set(path, param, value)                设元件参数，value 必须为字符串；如 set('Model/R1','R','22000')\n"
    "  simulate(modelName[, opts])            运行仿真，返回 {Time, Values, ...}；opts 可含 ModelVars\n"
    "  scope(scopeRef, action[, label])       scope 操作；action 如 'ClearTraces'、'HoldTrace'；返回 0\n"
    "  close(modelName)                       关闭模型，返回 0\n"
    "  codegen(path[, optStruct[, outDir]])   代码生成（签名待验证）\n"
    "  analyze(modelName, analysisName)       启动分析（签名待验证）\n"
    "  statistics()                           使用统计（签名待验证）\n"
    "  webserver.*                            webserver 专用（签名待验证）\n"
    "\n"
    "要点：\n"
    "  * 元件路径 = 模型名/元件名，如 'buck_converter_with_parameter_sweep/R1'\n"
    "  * set 的 value 必须是字符串（数字会被 PLECS 拒绝）；get 返回的也是字符串\n"
    "  * get('', 'CurrentCircuit') 不可用（空路径无效）\n"
    "  * simulate 是阻塞命令，同一时刻只能一个\n"
    "  * RPC 仅允许本机 localhost\n"
    "  * 覆盖模型变量用 ModelVars：opts = {\"ModelVars\": {\"varL\": \"50e-6\"}}（数字或字符串均可）\n"
)


def tool_help(args):
    """返回 PLECS RPC 命令速查表。"""
    return {"reference": COMMAND_REFERENCE}


# --------------------------------------------------------------------------
# 工具清单（MCP tools/list）
# --------------------------------------------------------------------------

TOOLS = [
    {
        "name": "plecs_status",
        "description": "检查与 PLECS Standalone RPC 的连接状态；已连接时返回可用命令列表。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "plecs_help",
        "description": "返回 PLECS RPC 命令速查表（load/get/set/simulate/scope/close/codegen 等用法）。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "plecs_load_model",
        "description": "在 PLECS 中加载一个 .plecs 模型文件，并记录模型名供后续 simulate/close 使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".plecs 文件的绝对路径，如 D:/PLECS/demos/buck_converter_with_parameter_sweep/buck_converter_with_parameter_sweep.plecs"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "plecs_close",
        "description": "关闭模型。省略 model_name 时关闭最近加载的模型。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "模型名（不含扩展名）"}
            },
            "required": [],
        },
    },
    {
        "name": "plecs_get",
        "description": "读取 PLECS 元件参数值（返回字符串）。path 为元件路径（如 'ModelName/R1'），param 为参数名（如 'R'）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "元件路径，如 'ModelName/R1'"},
                "param": {"type": "string", "description": "参数名，如 'R' / 'L' / 'C'"},
            },
            "required": ["path", "param"],
        },
    },
    {
        "name": "plecs_set",
        "description": "设置 PLECS 元件参数。path 为元件路径，param 为参数名，value 可传字符串或数字（服务端统一转成字符串），如 '22000' 或 '22e3'。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "元件路径，如 'ModelName/R1'"},
                "param": {"type": "string", "description": "参数名，如 'R'"},
                "value": {"type": "string", "description": "参数值（字符串），如 '22000' 或 '22e3'"},
            },
            "required": ["path", "param", "value"],
        },
    },
    {
        "name": "plecs_simulate",
        "description": "运行仿真。省略 model_name 时用最近加载的模型；params 覆盖模型变量（ModelVars），solver_opts 覆盖求解器选项。结果体积超 20000 字符时**自动**转成统计摘要并落盘（时间、通道 min/max/mean/rms、保存路径），避免把上下文塞满；summary=true 可强制摘要，max_points 可抽点，save_to 可指定落盘路径。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "模型名（不含扩展名）"},
                "params": {"type": "object", "description": "覆盖的模型变量，如 {\"varL\": \"50e-6\", \"varR\": 1}"},
                "solver_opts": {"type": "object", "description": "求解器选项覆盖"},
                "summary": {"type": "boolean", "description": "true = 只返回统计摘要 + 落盘路径，不回传波形数组"},
                "max_points": {"type": "integer", "description": "抽点上限；摘要模式下当作 preview 点数，普通模式下对 Time/Values 等间隔抽点"},
                "save_to": {"type": "string", "description": "把完整波形 JSON 写到这个路径（目录会自动创建）"},
            },
            "required": [],
        },
    },
    {
        "name": "plecs_scope",
        "description": "对 Scope 执行操作。action 常用 'ClearTraces'（清空）或 'HoldTrace'（保持当前轨迹，需 label）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope_path": {"type": "string", "description": "Scope 路径，如 'ModelName/Scope'"},
                "action": {"type": "string", "description": "动作，如 ClearTraces / HoldTrace"},
                "label": {"type": "string", "description": "HoldTrace 时的轨迹标签"},
                "param": {"type": "string", "description": "额外参数（可选）"},
            },
            "required": ["scope_path"],
        },
    },
    {
        "name": "plecs_codegen",
        "description": "对模型或子系统生成代码（签名待对照本机文档验证）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "模型名或子系统路径，如 'ModelName/Subsystem'"},
                "opt_struct": {"type": "object", "description": "代码生成选项（可选）"},
                "output_dir": {"type": "string", "description": "输出目录（可选）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "plecs_trace_read",
        "description": "解析 Scope 的 SaveTraces 产出的 .trace 二进制文件，返回每通道统计量（min/max/mean/rms/p2p/n），可选导出 CSV 或预览若干点。模型顶层没 outport 时，这是取波形的正路。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".trace 文件绝对路径"},
                "max_curves": {"type": "integer", "description": "只解析前 N 条曲线（0 = 全部）"},
                "stats_only": {"type": "boolean", "description": "true = 不保留数组，只算统计量（大文件省内存，但不能导 CSV）"},
                "csv": {"type": "string", "description": "导出 CSV 的路径（可选）"},
                "preview_points": {"type": "integer", "description": "每条曲线预览点数（0 = 不预览）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "plecs_call",
        "description": "通用透传：调用任意 PLECS RPC 命令（analyze / statistics / webserver 等未单独封装的命令）。method 为命令名，args 为位置参数列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "description": "PLECS 命令名，如 analyze / statistics / codegen / load / simulate"},
                "args": {"type": "array", "description": "位置参数列表", "items": {}},
            },
            "required": ["method"],
        },
    },
]

TOOL_IMPL = {
    "plecs_status": tool_status,
    "plecs_help": tool_help,
    "plecs_load_model": tool_load_model,
    "plecs_close": tool_close,
    "plecs_get": tool_get,
    "plecs_set": tool_set,
    "plecs_simulate": tool_simulate,
    "plecs_scope": tool_scope,
    "plecs_codegen": tool_codegen,
    "plecs_trace_read": tool_trace_read,
    "plecs_call": tool_call,
}


# --------------------------------------------------------------------------
# MCP 协议处理
# --------------------------------------------------------------------------

def handle_message(msg):
    method = msg.get("method")
    msg_id = msg.get("id")

    # 通知（无 id）不回复
    if msg_id is None:
        return None

    if method == "initialize":
        protocol = (msg.get("params") or {}).get("protocolVersion", "2024-11-05")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": protocol,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        impl = TOOL_IMPL.get(name)
        if impl is None:
            return {"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32602, "message": "未知工具: {}".format(name)}}
        try:
            return {"jsonrpc": "2.0", "id": msg_id, "result": _tool_result(impl(arguments))}
        except Exception as e:
            log("tool error [{}]: {}".format(name, e))
            return {"jsonrpc": "2.0", "id": msg_id, "result": _tool_error(e)}
    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}
    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}
    if method == "resources/templates/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resourceTemplates": []}}

    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": -32601, "message": "Method not found: {}".format(method)}}


def main():
    log("starting, PLECS_RPC_URL =", PLECS_RPC_URL)
    for line in sys.stdin:
        line = line.strip()
        if line.startswith("﻿"):  # 防御：剥掉可能的 BOM
            line = line[1:]
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            log("bad json line:", line[:200])
            continue
        try:
            resp = handle_message(msg)
        except Exception as e:
            log("unhandled error:", e)
            resp = {"jsonrpc": "2.0", "id": msg.get("id"),
                    "result": _tool_error("内部错误: {}".format(e))}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=True) + "\n")
            sys.stdout.flush()
    log("stdin closed, exiting")


if __name__ == "__main__":
    main()
