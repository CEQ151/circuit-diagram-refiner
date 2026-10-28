# Circuit Diagram Refiner — 电路图反复优化 Agent Skill

**用途：** 为可调用终端、可读取图片的 Agent 添加电路图制作流程：Netlist 整理 → TikZ/CircuiTikZ 绘图 → LaTeX 编译 → PDF 转 PNG → 视觉复核 → 修改源码 → 循环迭代 → 交付 TEX/PDF/PNG。

支持数字组合逻辑、DFF/计数器、模拟电路、混合信号、基础电力电路等。无需预先安装 KiCad / Graphviz 或额外神经网络。

## 1. 安装 Skill

将整个 `circuit-diagram-refiner/` 文件夹解压到 Agent 可以读取的 Skills 目录（具体路径因客户端而异）：

```text
项目专用：  <your-project>/.agents/skills/circuit-diagram-refiner/
Codex 示例： ~/.codex/skills/circuit-diagram-refiner/
Claude Code 示例：~/.claude/skills/circuit-diagram-refiner/
```

**关键：** 目录内必须直接存在 `SKILL.md`，不应形成多余的一层嵌套。重新启动/重新加载 Agent 后，可要求它使用 `circuit-diagram-refiner`。部分客户端不会自动发现 Skills，此时让 Agent 直接读取 `SKILL.md` 并按其执行。

## 2. 环境依赖

- 已装好的 TeX Live/MacTeX（`pdflatex` 或 `lualatex`）
- LaTeX 宏包：`tikz`、`circuitikz`、`standalone`
- Python >= 3.9（系统环境一般已有）
- 推荐 Poppler 的 `pdftoppm`：macOS `brew install poppler`
- 可选（不是必须）：`python3 -m pip install -r requirements-optional.txt`

在 Skill 根目录执行：

```bash
python3 scripts/doctor.py
```

## 3. 快速体验：真实编译示例

```bash
python3 scripts/validate_netlist.py assets/netlist.example.json
python3 scripts/render.py assets/logic.tex --out /tmp/circuit-logic --dpi 220
python3 scripts/render.py assets/analog.tex --out /tmp/circuit-analog --dpi 220
python3 scripts/audit_pdf.py /tmp/circuit-logic/logic.pdf --out /tmp/circuit-logic
```

脚本会生成同名 PDF/PNG、编译日志和 JSON 报告。`audit_pdf.py` 需要可选的 PyMuPDF；即使没有它，主要工作流仍可使用。

## 4. 给 Agent 的示例任务

> 使用 circuit-diagram-refiner Skill，将我提供的数字逻辑/模拟电路重绘成教材级别的 TikZ/CircuiTikZ 电路图。先建立完整引脚与网络对应关系，再进行分区布局和正交布线。每轮必须编译 LaTeX，将 PDF 渲染成 PNG，并真正查看图片检查导线与文字是否碰撞、连接是否准确、布局是否均匀。修复后继续编译与检查，直到达到审核标准。交付一致的 TEX、PDF、PNG，无法确认的环节必须如实说明。

还可以打开 `references/PROMPT_TEMPLATE.md` 直接复制完整提示词。

## 5. 六个关键事实

1. **无需额外 EDA 软件**就能画大多数课程电路图；复杂电路是否需要辅助布局视情况而定。
2. Netlist JSON 仅验证**声明内部一致性**，不能证明源图功能、电气正确或 TikZ 实际连线正确。
3. `audit_pdf.py` 是基于 PDF 几何数据的启发式检查，有假阳性与漏检，不能取代视觉审查。
4. Agent 必须能**真的查看**图片，才能满足视觉检查要求；只会跑 Python 的 CLI Agent 不一定有视觉能力。
5. **不会自动调用云端多模态模型**，不需 API Key。本 Skill 用指令让现有 Agent 的视觉能力介入迭代，避免虚构“已检查”。
6. 不能保证“任何电路”都能自动完成出版级绘图；不完整的电气需求、专有器件缺失或复杂走线需进一步输入或专业审查。

## 6. 目录说明

```text
circuit-diagram-refiner/
├── SKILL.md                     Agent 主流程与强制验收门槛
├── README.md                    中文安装与使用说明
├── scripts/
│   ├── cycle.py                 管理多轮渲染、视觉审查记录和最终验收
│   ├── doctor.py                检查 LaTeX/渲染环境
│   ├── render.py                编译并生成 PDF/PNG + 日志
│   ├── audit_pdf.py             可选 PDF 几何重叠审查
│   ├── validate_netlist.py      检查 JSON Netlist 的结构一致性
│   └── compare_images.py       可选前后版本差异可视化
├── assets/
│   ├── logic.tex                时序数字逻辑示例
│   ├── analog.tex               RC 低通模拟电路示例
│   ├── netlist.example.json     Netlist 数据格式示例
│   └── review.template.json     Agent 填写的逐轮审查模板
├── references/
│   ├── REVIEW_STANDARD.md       100 分审核规则与硬性条件
│   ├── LAYOUT_PLAYBOOK.md       图论式布局与正交走线策略
│   ├── CIRCUIT_CONVENTIONS.md   各类电路特殊规则
│   ├── PROMPT_TEMPLATE.md       可复用中文提示词
│   └── TROUBLESHOOTING.md       常见错误排查
└── examples/                    已编译的 PDF/PNG 示例
```

## 7. 安全说明

- 此工具使用 `-no-shell-escape`，但 **LaTeX 仍不属于安全沙箱**。不要在有敏感数据的系统中直接编译来源未知或不可信的 TeX 文件。必要时在容器内执行。
- PDF 审核与图片差异工具均不提供电路仿真/ERC 功能；最终正确性需基于题目核对或独立仿真。
- 不要对外宣称“获得 IEEE 认证”；本项目提供的是面向学术发表风格的绘图审核规范，而非第三方认证。

## 许可

MIT License。第三方 LaTeX/Python 依赖遵守各自许可证，未捆绑字体或外部 LaTeX 宏包。

## 8. 推荐：用 `cycle.py` 管理多轮迭代（避免将未经复核的产物当成最终版本）

```bash
# 一轮编译 + 渲染 + 可选审计；输出需要 Agent 亲自查看的 PNG
python3 scripts/cycle.py render assets/logic.tex --workspace /tmp/circuit-review --max-rounds 6

# Agent 查看 /tmp/circuit-review/round01/logic.png 后，填写一份 review JSON
cp assets/review.template.json /tmp/circuit-review/my-review.json
# Agent 根据真正的审查结果填写布尔门槛、分数、缺陷和 notes
python3 scripts/cycle.py review --workspace /tmp/circuit-review --file /tmp/circuit-review/my-review.json

# 未通过：Agent 修改原始 .tex 后，再次运行 render → 真正查看新图 → review。
# 通过：自动复制当前对应的 TEX/PDF/PNG 到 /tmp/circuit-review/final/
python3 scripts/cycle.py status --workspace /tmp/circuit-review
```

`cycle.py` 通过源码和渲染图片的 SHA-256 绑定审查记录，防止用旧图的通过结论替换新源码；不过它**无法独立判断 Agent 是否真的看过图片或审查是否正确**，必须依赖具备视觉能力的 Agent 如实填写记录。
