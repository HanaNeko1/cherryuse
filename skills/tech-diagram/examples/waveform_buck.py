"""BUCK converter CCM waveforms — matplotlib template.

Usage:  python waveform_buck.py [output.png]
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Chinese labels need an explicit CJK font on Windows
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

out = sys.argv[1] if len(sys.argv) > 1 else "buck_waveform.png"

# ---- operating point ----
Vin = 12.0      # V
Vo = 5.0        # V
f = 500e3       # Hz
L = 10e-6       # H
Io = 2.0        # A

D = Vo / Vin
T = 1 / f
dI = (Vin - Vo) * D * T / L
Imax, Imin = Io + dI / 2, Io - dI / 2
slope_on = (Vin - Vo) / L
slope_off = -Vo / L

t = np.linspace(0, 2 * T, 4000)
phase = (t % T) / T
gate = (phase < D).astype(float)
vsw = np.where(phase < D, Vin, 0.0)
iL = np.where(
    phase < D,
    Imin + slope_on * (phase * T),
    Imax + slope_off * (phase * T - D * T),
)
t_us = t * 1e6

fig, (ax_gate, ax_sw, ax_il) = plt.subplots(
    3, 1, figsize=(10, 8), sharex=True, gridspec_kw={"height_ratios": [1, 1.2, 2.2]}
)

# Mode shading: orange = switch on, blue = switch off
for k in range(2):
    on0, on1 = k * T, k * T + D * T
    off0, off1 = on1, (k + 1) * T
    for ax in (ax_gate, ax_sw, ax_il):
        ax.axvspan(on0 * 1e6, on1 * 1e6, color="#f6c77a", alpha=0.18, lw=0)
        ax.axvspan(off0 * 1e6, off1 * 1e6, color="#8ab4f8", alpha=0.14, lw=0)

ax_gate.text(D * T / 2 * 1e6, 1.35, "模态 1：S 导通，D 截止", ha="center", fontsize=10, color="#a25c00")
ax_gate.text((D + (1 - D) / 2) * T * 1e6, 1.35, "模态 2：S 关断，D 续流", ha="center", fontsize=10, color="#1a4d8f")

ax_gate.step(t_us, gate, where="post", color="#2e7d32", lw=2)
ax_gate.set_ylim(-0.2, 1.6)
ax_gate.set_yticks([0, 1])
ax_gate.set_yticklabels(["关", "开"])
ax_gate.set_ylabel("开关驱动", fontsize=11)

ax_sw.step(t_us, vsw, where="post", color="#6a1b9a", lw=2)
ax_sw.set_ylim(-0.8, Vin * 1.2)
ax_sw.set_yticks([0, Vin])
ax_sw.set_yticklabels(["0", f"{Vin:g}"])
ax_sw.set_ylabel("V_SW (V)", fontsize=11)

ax_il.plot(t_us, iL, color="#1565c0", lw=2.2)
ax_il.axhline(Io, color="gray", ls="--", lw=1)
ax_il.axhline(Imax, color="#b71c1c", ls=":", lw=1)
ax_il.axhline(Imin, color="#b71c1c", ls=":", lw=1)
ax_il.set_ylim(Imin - 0.35, Imax + 0.5)
ax_il.set_ylabel("i_L (A)", fontsize=11)
ax_il.set_xlabel("时间 (µs)", fontsize=11)

x_peak = (T + D * T) * 1e6
ax_il.annotate(
    "",
    xy=(x_peak + 0.14, Imax),
    xytext=(x_peak + 0.14, Imin),
    arrowprops=dict(arrowstyle="<->", color="#b71c1c", lw=1.2),
)
ax_il.text(x_peak + 0.22, Imax + 0.24, f"ΔI_L = {dI:.2f} A", color="#b71c1c", fontsize=10)
ax_il.text(0.25, Imax + 0.22, f"I_max = {Imax:.2f} A", color="#b71c1c", fontsize=9)
ax_il.text(1.05, Io - 0.18, f"I_o = {Io:.2f} A", color="gray", va="top", fontsize=9)
ax_il.text(0.28, Imin - 0.16, "斜率 = (V_in − V_o)/L", fontsize=9, color="#a25c00", va="top")
ax_il.text(1.15, Imin - 0.16, "斜率 = −V_o/L", fontsize=9, color="#1a4d8f", va="top")

fig.suptitle(
    f"BUCK 变换器运行波形（V_in={Vin:g} V, V_o={Vo:g} V, f_sw={f/1e3:g} kHz, L={L*1e6:g} µH, I_o={Io:g} A, D={D:.2f}）",
    fontsize=12,
    y=0.97,
)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(out, dpi=160, bbox_inches="tight")
print("OK:", out)
