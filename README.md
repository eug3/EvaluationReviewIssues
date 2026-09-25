# EvaluationReviewIssues

**本项目只做一件事：整理「电子底稿编制 / 送审 / 复核」要问的问题。** 不做报告抽取、图谱构建、自动判定等管线。

仓库里所有数据文件都是「**YAML（机器可读）+ 同名 .md（人可读）**」成对出现，改了 YAML 后运行 `scripts/render-yaml-docs.py` 重新生成 .md。

## 主产出：问题集

| 文件 | 内容 | 规模 |
| --- | --- | --- |
| [`questions/底稿问题集.yaml`](questions/底稿问题集.yaml) / [`questions/底稿问题集.md`](questions/底稿问题集.md) | 主问题集，11 组：送审前置 / 管理类 GL / 综合类 CZ / 财务类通用 / 财务类重点科目 / 非财务类 / 收益法 / 市场法 / 报告说明低级错误 / 明细表低级错误 / 档案检查要点 | **180 条问题** |
| [`questions/步骤复核表.yaml`](questions/步骤复核表.yaml) / [`questions/步骤复核表.md`](questions/步骤复核表.md) | 各科目《评估步骤及复核表》的操作步骤与要求，按科目归并去重 | **72 科目 / 736 条步骤** |

整理思路与来源说明见 [`docs/底稿问题整理.md`](docs/底稿问题整理.md)；指引原文见 [`docs/底稿编制指引.md`](docs/底稿编制指引.md)。

## 资料来源

《华信电子底稿编制指引（征求意见稿）》及附件：

| 路径 | 说明 |
| --- | --- |
| `华信电子底稿编制指引（征求意见稿）/电子底稿编制指引（征求意见稿）.docx` | 主指引（纸质/电子底稿范围、送审要求、各类底稿操作指引）；原文 markdown 版 [`docs/底稿编制指引.md`](docs/底稿编制指引.md) |
| `.../附件1：资产评估申报表（新会计报表-小助手V3.0）.xlsm` | 「评估小助手」申报表工具（98 张表） |
| `.../附件2：评【2025】-000 电子底稿/1管理类底稿/` | 归档管理类底稿模板（含档案检查要点、报告/说明/明细表低级错误定义表） |
| `.../附件2：评【2025】-000 电子底稿/2操作类底稿/` | 操作类底稿目录、综合类 CZ、资产基础法各科目、收益法 DCF、市场法模板 |

## 工具脚本

| 脚本 | 说明 |
| --- | --- |
| `scripts/extract-step-tables.py` | 从附件2各 .xls/.xlsx 抽取《步骤及复核表》→ `questions/步骤复核表.yaml`（依赖 xlrd / openpyxl / pyyaml） |
| `scripts/render-yaml-docs.py` | 把仓库所有数据 YAML 渲染成同目录同名 .md 可读版 |
| `scripts/ragflow-retrieval.py` | RAGFlow MCP 检索辅助脚本（准则查证用） |

```bash
python3 scripts/extract-step-tables.py   # 抽取/更新步骤表
python3 scripts/render-yaml-docs.py      # 重新生成所有 .md 可读版
```

## 参考（历史设计稿，非当前重点）

| 路径 | 可读版 |
| --- | --- |
| `docs/report-structure.md` | 评估报告准则结构 + 报告章节→底稿支撑矩阵（调研稿） |
| `docs/design.md` | 早期「命题→追问→取证→判定→建图」管线设计（暂缓） |
| `docs/datasets.md` | RAGFlow 准则数据集清单（53 份）与检索说明 |
| `questions/review_checklist.yaml` | 早期按准则整理的追问集 → `questions/review_checklist.md` |
| `schema/claim.yaml` | 报告命题类型 → `schema/claim.md` |
| `schema/verdict.yaml` | 判定枚举与规则 → `schema/verdict.md` |
| `schema/kg_schema.yaml` | 知识图谱模型 → `schema/kg_schema.md` |
| `schema/report_section.yaml` | 报告章节与底稿支撑 → `schema/report_section.md` |
| `.vscode/mcp.json` | RAGFlow MCP 配置（`http://10.1.1.230:9382/mcp`） |

## 相关项目

- `GSDJSense`：问题清单模型与工作流问题上报（`report_issue`）
- `GSDJWorkflowEdit/detail-check-judge`：报告/说明/Excel 交叉核对工作流
