# 设计稿：报告命题 ↔ 底稿证据 的支撑 / 不支持关系

> 状态：第一版（标准定义稿）
> 目标读者：本项目实现者、评估复核业务方
> 上游参考：`GSDJSense`（问题模型 + KG 抽取）、`GSDJWorkflowEdit/detail-check-judge`（报告/说明/Excel 核对）

## 1. 背景与目标

资产评估报告中的每一句实质性陈述——评估对象、价值类型、基准日、方法、参数取值、计算过程、结论金额、假设、限制——都应当在**评估底稿**（评估说明、计算表、附件）中有对应的支撑证据。

本项目要做的不是简单"全文对比"，而是：

1. 把报告拆成**可判定的原子命题**（ReportClaim）；
2. 对每条命题生成**定向追问**（Question / Task），去问底稿要证据；
3. 用底稿内容**回答**这些追问，形成带定位的证据片段（EvidenceSpan）；
4. 给出**判定**：支持 / 矛盾 / 底稿无对应（不支持）/ 证据不足 / 不适用；
5. 把上面四者固化成**关系图**：报告命题 ↔ 底稿证据 的支撑与不支持逻辑关系。

一句话：**以「追问」为驱动，把报告与底稿之间的支撑关系显式化、可追溯、可复核。**

## 2. 范围与非目标

### 在范围内
- 报告命题的抽取与归类
- 通用「追问问题集」（`questions/review_checklist.yaml`）与案例特化追问
- 通过 RAGFlow 检索底稿取证
- 逐命题判定矩阵
- 关系图（JSONL / Neo4j / mermaid 可视）

### 非目标（第一版不做）
- 不修改、不生成报告或底稿原文
- 不代替评估师签字确认；判定结果一律标注为"机器复核建议 + 人工复核状态"
- 不在第一版实现 Excel 公式链的完整确定性核验（作为可选增强，见 §5.3）
- 不追求"底稿无对应 = 命题错误"的结论；沉默只记为`missing`，不等于证伪

## 3. 输入：RAGFlow 数据集与案例清单

第一版输入统一走**已上传到 RAGFlow 的文档**，经 MCP `evaluation-review`（`http://10.1.1.230:9382/mcp`，工具 `ragflow_retrieval`）检索。

`ragflow_retrieval` 关键参数与返回：

| 参数 | 用途 |
| --- | --- |
| `question` | 检索问题（必填） |
| `dataset_ids[]` | 限定数据集 |
| `document_ids[]` | 限定文档——**区分"报告"与"底稿"的关键手段** |
| `page_size` / `page` | 分页 |
| `similarity_threshold` | 相似度阈值 |
| `vector_similarity_weight` | 向量权重 |
| `keyword` | 是否启用关键词检索 |

返回字段 `content / document_name / similarity / positions / dataset_name / dataset_id / document_metadata`，其中 `positions`（页码坐标）是证据定位的基础。

**检索接口的约束**：它是"按问题召回"，不是"取全量 chunk"。因此：

- **报告命题抽取**：用一个案例级的**章节探针问题表**（`report_probe_questions`）定向召回报告各章节 chunk，再交给 LLM 抽命题；案例若另附报告 markdown，则优先直接抽取（见 §5.1）。
- **底稿取证**：对每条追问，用 `document_ids` 限定到底稿文档召回；报告文档不参与取证，避免"用报告证明报告"。

上述映射写入 **案例清单** `cases/<case>/case.yaml`，模板见 `cases/_template/case.yaml`。

准则依据（`ground`）通过单独的准则数据集检索，当前为 `评估法及准则`（`d6edbed44e7a11f18ee0afe6a78982c3`），用于给追问补"应当问什么、依据哪条准则"。

## 4. 核心概念与数据模型

四元组：

```
报告命题 ReportClaim
    │  ASKED
    ▼
追问 Question（图模型中复用 GSDJSense 的 Task 节点）
    │  ANSWERED_BY
    ▼
底稿证据 EvidenceSpan（RAGFlow chunk / 定位）
```

判定关系直接落在**命题与证据/追问之间**（边属性携带 verdict / question_id / confidence / rationale）：

| 关系边 | 方向 | 含义 |
| --- | --- | --- |
| `ASKED` | ReportClaim → Task | 该命题触发了哪条追问 |
| `ANSWERED_BY` | Task → EvidenceSpan | 追问在底稿中定位到的证据（无证据则无此边） |
| `SUPPORTED_BY` | ReportClaim → EvidenceSpan | 底稿证据支持该命题 |
| `CONTRADICTED_BY` | ReportClaim → EvidenceSpan | 底稿证据与该命题矛盾 |
| `INSUFFICIENTLY_SUPPORTED_BY` | ReportClaim → EvidenceSpan | 有部分证据但不足以支撑 |
| `MISSING_EVIDENCE` | ReportClaim → Task | 按追问检索后底稿无对应证据（沉默） |

### ReportClaim 最小字段
`claim_id, case_id, doc_role, section, text, proposition, claim_type, value, unit, currency, locator(chunk_id/document_name/positions), confidence`

### Question 最小字段
`question_id, claim_id, claim_type, ask, targets[实体类型], expect_evidence, rule, severity, ground, source(template|generated)`

### EvidenceSpan 最小字段
`evidence_id, question_id, source_dataset_id, document_name, doc_role, content, positions[], similarity, cell(sheet/address, 可选), retrieved_at`

完整字段与枚举见 `schema/`。

## 5. 六阶段管线

```
S0 输入装配 → S1 命题抽取 → S2 追问生成 → S3 底稿取证 → S4 判定 → S5 建图 → S6 产出
```

### S0 输入装配
读取 `case.yaml`，校验 RAGFlow 连通性，解析报告/底稿的 `document_ids`，加载准则数据集 ID。

### S1 报告命题抽取（ReportClaim）
1. 用 `report_probe_questions` 按章节探针召回报告 chunk（或直接读报告 markdown）；
2. 按 `schema/claim.yaml` 的 `claim_types` 做结构化抽取：一条命题 = 一个可判定陈述；
3. 数值命题强制携带 `value / unit / currency`；无法定值的进 `insufficient` 前置标记；
4. 命题必须可定位回 `chunk_id + positions`；
5. 去重：同一命题在报告摘要/正文重复出现时合并，保留全部 locator。

### S2 追问生成
三类来源，按优先级叠加：

1. **模板追问**：按 `claim_type` 从 `questions/review_checklist.yaml` 展开（静态、可审计、稳定）；
2. **特化追问**：针对具体数值/方法生成定向问题，如"报告中折现率 10.5% 的测算依据与构成明细是什么？"；
3. **准则追问**（可选）：用命中的准则条款补"应当披露/说明什么"。

要求：每条追问必须写明 `expect_evidence`（期望的底稿证据形态）与 `rule`（判定规则），否则该追问不可判定，不允许生成。

### S3 底稿取证（RAGFlow）
- 追问 → `ragflow_retrieval(question=ask, dataset_ids=[案例数据集], document_ids=底稿文档, keyword=true)`
- 过滤：低于阈值的丢弃；同一证据被多条追问命中时按 `evidence_id` 复用
- 报告文档不进入底稿检索域
- `positions` + `document_name` 作为可点击定位

### S3b（可选增强）确定性核验
若案例另附 Excel 计算表，对数值类命题复用 `GSDJWorkflowEdit` 的 `excel-summary-checker` / `detail-sheet-stats` / `formula-island` 做公式链与合计核对，产生高置信度的 `contradicted` / `supported`。第一版可暂缓。

### S4 判定
判定优先级（先确定性、后 LLM）：

1. 确定性规则命中（数值不等、基准日不同、方法不适用）→ 直接定 `contradicted` / `not_applicable`；
2. 检索为空且已按 `rule` 扩大召回 → `missing`；
3. 有证据但缺关键要素（无计算过程、无来源、不可读）→ `insufficient`；
4. 其余交 LLM judge，按 `schema/verdict.yaml` 的规则输出 verdict + 引用证据 + 理由 + 置信度。

**关键不变量**：不得把"没检索到"读成"支持"；`missing` 与 `contradicted` 必须区分开。

### S5 建图
- 每案例一个 Neo4j database（沿用 GSDJSense 的 `kg-<dataset>` 约定）或独立 label 空间；
- 写入 `ReportClaim / Task / EvidenceSpan` 节点与 §4 的关系边；
- 边属性：`verdict, question_id, confidence, rationale`；
- 同时落 JSONL，保证不依赖 Neo4j 也可复核。

### S6 产出
1. **关系图**（主产出）：mermaid + 可交互 HTML；底稿证据按`支持/矛盾/缺失/不足`着色；
2. **支撑矩阵**：命题 × 追问 × verdict × 证据定位 × 置信度；
3. **复核问题清单**：复用 GSDJSense 的 `IssueDocument` 结构（`title/description/severity/evidence_items/category/source/run_id...`），可直接对接 `report_issue`；
4. **复核纪要**：按`矛盾 > 缺失 > 不足`分级排序，附原文引用。

## 6. 图模型与 Neo4j 映射

扩展 `GSDJSense/config/kg_schema.yaml`：

- **新增节点**：`ReportClaim`（报告命题）、`EvidenceSpan`（检索到的证据片段）
- **复用节点**：`Task`（问题/检查项）、来源层 `Document/Chunk`、实体层 `Conclusion/Evidence/Reasoning/Assumption/Rebuttal/Parameter/Method/Data/CalculationStep`
- **新增边**：`ASKED / ANSWERED_BY / CONTRADICTED_BY / INSUFFICIENTLY_SUPPORTED_BY / MISSING_EVIDENCE`
- **扩展边**：`SUPPORTED_BY` 的 source 增加 `ReportClaim`

完整定义见 `schema/kg_schema.yaml`。

## 7. 目录结构

```
EvaluationReviewIssues/
├── README.md
├── docs/
│   ├── design.md                 # 本文件
│   └── datasets.md               # RAGFlow 数据集清单
├── schema/
│   ├── kg_schema.yaml            # 图模型（扩展自 GSDJSense）
│   ├── claim.yaml                # 报告命题类型
│   └── verdict.yaml              # 判定枚举与规则
├── questions/
│   └── review_checklist.yaml     # 通用「追问问题集」
└── cases/
    ├── _template/case.yaml       # RAGFlow 案例清单模板
    └── <case>/
        ├── case.yaml
        └── out/                  # claims/questions/evidence/verdicts/graph
            └── .gitkeep
```

## 8. 复用清单

| 来源 | 复用内容 |
| --- | --- |
| `GSDJSense/src/lib/issues.ts`、`report-issue-tool.ts` | 问题清单数据结构与上报入口 |
| `GSDJSense/config/kg_schema.yaml` | 论证五要素 / 评估实体 / 关系，以及 `Task` + `ANSWERS_WITH` 挂点 |
| `GSDJSense/src/lib/kg-langgraph.ts`、`kg.ts` | 结构化抽取 / 归一化 / 向量 / Neo4j 落库范式 |
| `GSDJWorkflowEdit/detail-check-judge` | 报告-说明-Excel 核对流程、`task-lists` 原子检查项范式 |
| `GSDJWorkflowEdit/*/tools` | `docx-to-md`、`excel-summary-checker`、`detail-sheet-stats`、`extract-conclusion-chapters` |
| `.vscode/mcp.json` + `docs/datasets.md` | RAGFlow 检索通道 |

## 9. 实施路线

| 里程碑 | 内容 | 验收 |
| --- | --- | --- |
| M0（本次） | 设计稿 + schema + 问题集骨架 + 案例模板 | 标准可评审，字段完整 |
| M1 | 命题抽取 + 追问生成（离线，吃报告 markdown） | 对南京七伙案例产出 claims/questions JSONL |
| M2 | RAGFlow 取证 + 判定 | 逐命题 verdict，support/contradicted/missing 均可复现定位 |
| M3 | 建图 + 产出（mermaid/矩阵/问题清单） | 一张可点击定位的关系图 |
| M4 | 接入 GSDJSense（落 Mongo/Neo4j/UI） | 图与问题清单在现有界面可查 |

## 10. 关键不变量与风险

**不变量**
- 每个 verdict 必须能追溯到 `question` 与 `evidence`（或显式 `missing`）；
- 报告文档不得作为底稿证据来源；
- `missing`（沉默）≠ `contradicted`（反证）≠ `supported`（相符）；
- 未检索到的部分不得计入"通过"，结论中须写明未核对范围。

**风险**
- RAGFlow 只有检索、没有"取全量"接口 → 用章节探针表缓解，但可能漏命题；需接受召回率上限。
- 底稿实体抽取质量决定判定质量 → 沿用 GSDJSense 的窗口抽取 + 置信度门限。
- LLM judge 幻觉 → 强制引用原文 + 确定性规则优先 + 人工复核状态位。

## 11. 待定问题

1. 案例数据集是否按"一案例一 dataset"组织？还是共用 dataset 靠 `document_ids` 区分？
2. 关系图的可视化是自建 HTML，还是直接复用 GSDJSense 的 `kg-viewer`？
3. `missing` 的严重度默认取 `medium` 还是按命题类型分级（结论金额类取 `high`）？
4. 是否需要把准则条款也建成节点（`Criterion`）以支撑"依据哪条准则"的追溯？
