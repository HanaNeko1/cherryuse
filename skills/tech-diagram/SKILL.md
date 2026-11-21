---
name: tech-diagram
description: 技术问题配图——解答电路、电子、控制系统、波形、系统结构类问题时，生成示意图并直接内嵌到对话。框图/流程/信号流/状态机用 Mermaid；需要真实电路符号（电阻、电容、三极管、运放、电源等）用 schemdraw 出 PNG；波形/曲线/频响/瞬态用 matplotlib 出 PNG。Use when explaining circuits, electronics, control systems, waveforms or system architecture, or when the user asks to draw/diagram a technical concept.
---

# Tech Diagram

给技术解答配图，并且把图**直接显示在对话里**，而不是只丢一个文件路径。

## 1. 选型

| 要画的内容 | 方案 |
|---|---|
| 框图、流程、信号流、状态机、时序图 | Mermaid（聊天里直接渲染，不需要出图文件） |
| 电路原理图（真实元件符号） | schemdraw → PNG |
| 波形、曲线、频响、Bode、瞬态 | matplotlib → PNG |

不确定时先试 Mermaid；用户反馈不渲染时，改用「出 PNG + 内嵌」路线。

## 2. 首次准备（每台机器执行一次）

在技能目录（本文件所在目录）下运行：

```powershell
powershell -ExecutionPolicy Bypass -File ".\setup.ps1"
```

脚本会依次：检查 uv → 安装 Python 3.12 → 在技能目录创建 `venv` → 用清华镜像安装 schemdraw 和 matplotlib。
成功时输出 `SETUP_OK`。之后不需要重复执行。

## 3. 出图与内嵌流程

1. 把绘图脚本写到**当前会话工作区**（不要写进技能目录），文件名用英文数字。
2. 用技能自带的解释器运行：

   ```powershell
   & "<技能目录>\venv\Scripts\python.exe" "<脚本路径>" "<输出png路径>"
   ```

3. 确保图片服务在跑（幂等，可重复执行）：

   ```powershell
   powershell -ExecutionPolicy Bypass -File "<技能目录>\scripts\ensure_imgserver.ps1" -ServeDir "<图片所在目录>" -Port 18080
   ```

4. 回复中**同时**给出两样东西：
   - 文件路径（用户要保存/编辑时用）
   - 内嵌图片：`![说明](http://127.0.0.1:18080/<文件名>.png)`

## 4. 硬性规则（都是踩过的坑）

1. **schemdraw 存 PNG 前必须** `schemdraw.use("matplotlib")`，否则报
   `SVG backend only supports saving SVG format figures.`
2. **中文标注必须设字体**，否则显示成方框：
   ```python
   plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
   plt.rcParams["axes.unicode_minus"] = False
   ```
3. **垂直元件的 `.label(loc=...)` 会锚到元件起点**，不是中点。要精确摆位用锚点算坐标：
   ```python
   p = el.absanchors["center"]      # Point 对象，取 p[0], p[1]
   d += elm.Label().at((p[0] + 0.6, p[1])).label("C")
   ```
4. **并联的竖直元件横向间距至少 1 英寸**，否则符号会视觉重叠。把布局坐标集中写成变量，调间距只改一处。
5. **图片文件名用英文/数字**，避免中文导致 URL 编码问题。
6. **慢网装包走清华镜像**：`--index-url https://pypi.tuna.tsinghua.edu.cn/simple`
7. **`file://` 图片在 Cherry Studio 对话里不生效**，必须通过本地 HTTP 服务内嵌。
8. **一个图片服务进程只服务一个目录**。换输出目录时，要么统一用同一个目录，要么先停掉旧进程再启动新的。

## 5. 示例脚本

- `examples/circuit_buck.py`：BUCK 电路原理图（元件、布局、标注的完整写法）
- `examples/waveform_buck.py`：CCM 波形图（驱动 / SW 电压 / 电感电流，含模态底色与标注）

复制到工作区后改参数即可，两个脚本都支持 `python xxx.py <输出路径>`。

## 6. 标注排版建议

- 标签不要压在曲线/导线上：先看空白区，再用绝对坐标放。
- 波形图给关键量加辅助线（平均线、峰值线）和双箭头标纹波。
- 电路图每个节点用 `elm.Dot()` 标出连接点。
- 图标题里写清工作点参数，避免读者猜。

## 7. 安全边界

`scripts/imgserver.py` 只绑定 `127.0.0.1`，只返回图片后缀，关闭目录列表。
不要把绑定地址改成 `0.0.0.0`。

## 8. 排障

| 现象 | 处理 |
|---|---|
| 图不显示 | `Invoke-WebRequest http://127.0.0.1:18080/_ping` 应返回 `ok` |
| 中文变方框 | 没设置字体，见规则 2 |
| 找不到 matplotlib | 没跑 `setup.ps1` |
| 图重影/符号重叠 | 元件间距不够，见规则 4 |
| 端口被占用 | 换 `-Port 18081`，并在内嵌链接里同步改端口 |
