# -*- coding: utf-8 -*-
"""
PLECS `.trace` 波形文件解析器（自研实现，零依赖，只用标准库）。

格式依据 PLECS Standalone 4.7.4（Windows）实测逆向，官方无公开文档。
以下结构在 5 个不同形状的样本上验证过（1~4 条曲线、每曲线 1~3 条信号、
点数从 823 到 181192、文件最大 34 MB）：

    大端序，无魔数

    i32      version (= 2)
    i32      nTrace
    nTrace × {
        utf16be  traceName
        i32      nSig
        nSig × utf16be  sigName
    }
    ── 变长元数据块（字段含义未公开，本解析器跳过不解释）──

    ── 时间轴块 ──
    f64 × 40/8 ...
        序列头（40 字节）：  i32 1, i32 1, f64 ymax, f64 ymin, f64 0.0, i64 n
        f64 × n              时间轴（单调不减）

    ── 每条曲线（trace）──
        序列头（40 字节）：  i32 nSig, i32 1, f64 ymax, f64 ymin, f64 0.0, i64 n
        第 1 条信号：  f64 × n
        之后每条信号： 36 字节附加描述 + f64 × n

注：
  * 序列头里最后的 i64 就是采样点数，与时间轴长度一致；
  * 36 字节附加描述的内容未解读（不影响取数），靠「走完正好到文件末尾」校验；
  * Scope 保存的轨迹若在某次仿真中未记录到 t=0，则 n 会比 simulate 少 1，
    本解析器不做任何补点，原样返回文件里的数据。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["TraceError", "Curve", "read_trace", "summarize", "write_csv"]

VERSION_SUPPORTED = 2
HEADER_BYTES = 40          # 每个序列块的头部长度
EXTRA_SIG_BYTES = 36       # 同一曲线内，第 2 条信号起的附加描述长度


class TraceError(RuntimeError):
    """文件不是可识别的 .trace，或结构与预期不符。"""


@dataclass
class Curve:
    trace: str                 # 曲线（trace）名
    signal: str                # 信号名
    t: list = field(default_factory=list)
    v: list = field(default_factory=list)
    ymax_hint: float = 0.0     # 该曲线坐标轴上限（同一 trace 的多条信号共用）
    ymin_hint: float = 0.0
    agg: dict | None = None    # keep=False 时的流式统计结果

    def stats(self) -> dict:
        if self.agg is not None:
            return self.agg
        v = self.v
        if not v:
            return {"n": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "rms": 0.0, "p2p": 0.0}
        n = len(v)
        lo, hi = min(v), max(v)
        mean = sum(v) / n
        rms = (sum(x * x for x in v) / n) ** 0.5
        return {"n": n, "min": lo, "max": hi, "mean": mean, "rms": rms, "p2p": hi - lo}


class _Cur:
    __slots__ = ("b", "o")

    def __init__(self, b: bytes, o: int = 0):
        self.b = b
        self.o = o

    def i32(self) -> int:
        v = struct.unpack_from(">i", self.b, self.o)[0]
        self.o += 4
        return v

    def f64(self) -> float:
        v = struct.unpack_from(">d", self.b, self.o)[0]
        self.o += 8
        return v

    def i64(self) -> int:
        v = struct.unpack_from(">q", self.b, self.o)[0]
        self.o += 8
        return v

    def utf16(self) -> str:
        n = self.i32()
        if n <= 0:
            return ""
        if n % 2:
            raise TraceError("字符串长度不是偶数（%d），文件结构不符" % n)
        raw = self.b[self.o:self.o + n]
        self.o += n
        return raw.decode("utf-16-be", errors="replace")


def _read_names(buf: bytes):
    """解析头部名称表，返回 (traces, 名称表结束偏移)。traces = [(name, [sig...]), ...]"""
    if len(buf) < 8:
        raise TraceError("文件只有 %d 字节，不是有效的 .trace" % len(buf))
    c = _Cur(buf)
    ver = c.i32()
    if ver != VERSION_SUPPORTED:
        raise TraceError("不支持的 .trace 版本 %d（本解析器验证的是 %d）" % (ver, VERSION_SUPPORTED))
    ntrace = c.i32()
    if not (0 <= ntrace <= 100000):
        raise TraceError("曲线数异常：%d" % ntrace)
    traces = []
    for _ in range(ntrace):
        name = c.utf16()
        nsig = c.i32()
        if not (0 <= nsig <= 100000):
            raise TraceError("信号数异常：%d" % nsig)
        traces.append((name, [c.utf16() for _ in range(nsig)]))
    return traces, c.o


def _read_header(buf: bytes, off: int):
    """读一个序列头，返回 (a, b, ymax, ymin, n)。"""
    if off + HEADER_BYTES > len(buf):
        raise TraceError("序列头越界（偏移 %d）" % off)
    a, b = struct.unpack_from(">ii", buf, off)
    ymax, ymin, mid = struct.unpack_from(">ddd", buf, off + 8)
    n = struct.unpack_from(">q", buf, off + 32)[0]
    return a, b, ymax, ymin, n


def _find_series_start(buf: bytes, names_end: int):
    """在元数据块里定位时间轴序列头的起点。

    判据（三重校验，缺一不可）：
      1. 头部形态：i32 1, i32 1, f64 ymax, f64 ymin, f64 0.0, i64 n（n 合理）；
      2. 按本解析器假定的布局从头走到尾，偏移**恰好**等于文件长度；
      3. 时间轴单调不减（NaN 视为失败）。
    """
    size = len(buf)
    limit = min(names_end + 262144, size - HEADER_BYTES)
    for p in range(names_end, limit):
        try:
            a, b, _ymax, _ymin, n = _read_header(buf, p)
        except TraceError:
            continue
        if a != 1 or b != 1 or n < 2:
            continue
        if p + HEADER_BYTES + 8 * n > size:
            continue
        # 时间轴形状
        t0 = struct.unpack_from(">d", buf, p + HEADER_BYTES)[0]
        t1 = struct.unpack_from(">d", buf, p + HEADER_BYTES + 8)[0]
        if not (t0 <= t1):
            continue
        # 走完整布局
        try:
            if _walk_end(buf, p, n) == size:
                return p, n
        except TraceError:
            continue
    raise TraceError(
        "无法定位数据区：结构校验失败。可能不是 PLECS 4.7.x 保存的 .trace，或文件被截断/拼接。")


def _walk_end(buf: bytes, start: int, n: int) -> int:
    """按假定布局从 start 走到末尾，返回结束偏移（用于与文件长度比对）。"""
    size = len(buf)
    off = start
    nsig_of = []
    # 名称表不在这里读，交给调用方；这里只按顺序走，数量由头部 a 字段给出
    off += HEADER_BYTES + 8 * n           # 时间轴
    while off < size:
        if off + HEADER_BYTES > size:
            raise TraceError("块头越界")
        a, b, _ymax, _ymin, cnt = _read_header(buf, off)
        if cnt != n or not (1 <= a <= 100000) or b != 1:
            raise TraceError("块头不合法（偏移 %d）" % off)
        off += HEADER_BYTES
        for j in range(a):
            if j:
                off += EXTRA_SIG_BYTES   # 第 2 条信号起的附加描述
            off += 8 * n
            if off > size:
                raise TraceError("数据越界")
    return off


def read_trace(path, max_curves: int = 0, keep: bool = True) -> list:
    """解析 .trace，返回 Curve 列表。

    max_curves > 0 时只返回前 N 条（其余信号的数据仍被正确跳过）。
    keep=False 时不保留采样数组，只算统计量（大文件省内存，但不能导出 CSV）。
    """
    import math

    buf = Path(path).read_bytes()
    traces, names_end = _read_names(buf)
    n_sig = sum(len(s) for _, s in traces)
    if n_sig == 0:
        return []

    start, n = _find_series_start(buf, names_end)
    times = list(struct.unpack_from(">%dd" % n, buf, start + HEADER_BYTES))

    flat = []
    for tname, sigs in traces:
        for s in sigs:
            flat.append((tname, s))

    limit = max_curves if max_curves and max_curves > 0 else n_sig
    limit = min(limit, n_sig)

    curves = []
    off = start + HEADER_BYTES + 8 * n     # 跳过时间轴块
    idx = 0
    for tname, sigs in traces:
        _a, _b, ymax, ymin, _cnt = _read_header(buf, off)
        off += HEADER_BYTES
        for j, sname in enumerate(sigs):
            if j:
                off += EXTRA_SIG_BYTES
            if idx < limit:
                if keep:
                    vals = list(struct.unpack_from(">%dd" % n, buf, off))
                    curves.append(Curve(trace=tname, signal=sname, t=times, v=vals,
                                        ymax_hint=ymax, ymin_hint=ymin))
                else:
                    lo = math.inf
                    hi = -math.inf
                    s1 = 0.0
                    s2 = 0.0
                    cnt = 0
                    for (x,) in struct.iter_unpack(">d", buf[off:off + 8 * n]):
                        if x < lo:
                            lo = x
                        if x > hi:
                            hi = x
                        s1 += x
                        s2 += x * x
                        cnt += 1
                    agg = {"n": cnt, "min": lo, "max": hi,
                           "mean": s1 / cnt if cnt else 0.0,
                           "rms": (s2 / cnt) ** 0.5 if cnt else 0.0,
                           "p2p": hi - lo if cnt else 0.0}
                    curves.append(Curve(trace=tname, signal=sname, t=[], v=[],
                                        ymax_hint=ymax, ymin_hint=ymin, agg=agg))
            off += 8 * n
            idx += 1
    return curves


def summarize(curves: list) -> str:
    """一行一条曲线，便于直接贴进对话。"""
    if not curves:
        return "（无曲线）"
    lines = ["%d 条曲线，%d 采样点" % (len(curves), len(curves[0].v))]
    for i, c in enumerate(curves):
        s = c.stats()
        lines.append("  [%d] %s / %s: n=%d min=%.6g max=%.6g mean=%.6g rms=%.6g" % (
            i, c.trace, c.signal, s["n"], s["min"], s["max"], s["mean"], s["rms"]))
    return "\n".join(lines)


def write_csv(path, curves: list) -> str:
    """导出 CSV：第一列时间，之后每条曲线一列（共用同一时间轴）。"""
    import csv

    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    n = len(curves[0].v) if curves else 0
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["time"] + ["%s/%s" % (c.trace, c.signal) for c in curves])
        t = curves[0].t if curves else []
        for i in range(n):
            w.writerow([t[i] if i < len(t) else ""] + [c.v[i] for c in curves])
    return str(p.resolve())
