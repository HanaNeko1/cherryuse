# cherryuse

个人 Cherry Studio Skill 仓库，用于在多台电脑之间共享自建技能。

## 技能列表

| 技能 | 用途 |
|---|---|
| [`tech-diagram`](skills/tech-diagram/SKILL.md) | 技术问题配图：Mermaid 框图、schemdraw 电路图、matplotlib 波形图，并内嵌显示在对话中 |

## 目录结构

```
cherryuse/
├── README.md
├── .gitignore
└── skills/
    └── tech-diagram/          ← 技能目录名必须与 SKILL.md 里的 name 一致
        ├── SKILL.md
        ├── setup.ps1
        ├── scripts/
        │   ├── imgserver.py
        │   └── ensure_imgserver.ps1
        └── examples/
            ├── circuit_buck.py
            └── waveform_buck.py
```

新增技能时，在 `skills/` 下建同名目录，放入 `SKILL.md` 即可。

## 在另一台电脑安装

**方式 A：通过 GitHub 链接安装（推荐）**

在目标机器的 Cherry Studio 里，对 Agent 说：

> 安装这个技能：https://github.com/HanaNeko1/cherryuse/blob/main/skills/tech-diagram/SKILL.md

然后在技能目录下执行一次环境初始化：

```powershell
powershell -ExecutionPolicy Bypass -File "<技能目录>\setup.ps1"
```

输出 `SETUP_OK ...` 即为成功。

**方式 B：手动拷贝**

把 `skills/tech-diagram` 整个文件夹复制到：

```
%APPDATA%\CherryStudio\Data\Skills\
```

重启 Cherry Studio，技能会被自动识别。Python 环境仍需运行 `setup.ps1` 生成。

## 更新

```powershell
cd <仓库目录>
git pull
```

技能文件更新后 Cherry 会自动同步。`venv` 不会被提交，也不需要重建，除非依赖变化。

## 说明

- `venv/` 是本机生成的 Python 环境，已在 `.gitignore` 中排除，不要提交
- 技能里的脚本全部使用相对路径，不绑定具体机器
- 图片服务只绑定 `127.0.0.1`，仅返回图片文件
