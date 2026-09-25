# 知识图谱模型（参考）

> 机器可读版 schema/kg_schema.yaml。

## 节点类型

| 节点 | 说明 | 虚拟 | 示例 |
| --- | --- | --- | --- |
| Document | RAGFlow 文档虚拟节点（原始报告 / 底稿文档） | 是 | 资产评估报告；资产评估说明；Excel 计算底稿；权属与附件资料 |
| Chunk | RAGFlow 文档块虚拟节点（语义段落） | 是 | 文档分块后的单个文本块 |
| EvidenceSpan | 底稿证据片段 — 为回答某条追问而从底稿检索到的可定位证据 | 否 | 说明"收益法"章节中的折现率测算段落；计算表某 sheet 的合计行；附件中的评估明细表 |
| ReportClaim | 报告命题 — 从资产评估报告中抽取的、可被底稿支撑或证伪的最小陈述单元 | 否 | 评估基准日为 2021 年 6 月 30 日；采用收益法评估股东全部权益价值；折现率取 10.5%；股东全部权益评估值为 12,345.67 万元；假设被评估单位持续经营 |
| Task | 追问 / 审计检查项 — 针对报告命题向底稿提出的问题（来自 review_checklist.yaml 或案例特化生成） | 否 | 折现率 10.5% 的测算依据与构成明细是什么？；基准日与报告摘要是否一致？ |
| Conclusion | 结论/判断/建议 — 评估师的最终判断或结论性陈述 | 否 | 最终评估值、价值区间；资产状况良好 |
| Evidence | 数据/事实/引用 — 可验证的事实或证据来源 | 否 | 财务数据、市场数据、审计报告；合同条款、访谈记录 |
| Reasoning | 推理过程 — 从证据到结论的逻辑论证 | 否 | 为什么选某方法；为什么参数合理；计算步骤和公式推导 |
| Assumption | 前提假设 — 论证中的未验证前提条件 | 否 | 一般假设、特别假设；预测前提、市场条件假设 |
| Rebuttal | 反驳/挑战 — 对结论或证据的质疑、反证或不确定性说明 | 否 | 敏感性分析对参数的挑战；风险提示、不确定性说明；与其他数据源的矛盾 |
| Parameter | 评估参数 — 评估过程中使用的关键参数 | 否 | 折现率 10.5%；长期增长率 3%；加权平均资本成本（WACC）；资本化率、成新率 |
| Method | 评估方法 — 评估中采用的方法论或模型 | 否 | 收益法-DCF 模型；市场法-可比交易案例法；成本法-重置成本法 |
| Data | 市场/财务数据 — 可验证的外部或内部数据来源 | 否 | 市场利率数据；行业平均收益率；被评估单位财务报表数据 |
| CalculationStep | 计算步骤 — 从参数到结论的具体计算过程 | 否 | WACC 计算过程；折现现金流量计算；资产评估增减值计算 |

## 边类型

| 边 | 方向 | 说明 |
| --- | --- | --- |
| ASKED | ReportClaim → Task | 报告命题触发的追问 |
| ANSWERED_BY | Task → EvidenceSpan | 追问在底稿中定位到的证据（无命中的追问没有该边） |
| SUPPORTED_BY | ReportClaim ／ Conclusion ／ Method ／ Parameter ／ Data ／ Reasoning ／ Assumption ／ Rebuttal → EvidenceSpan ／ Evidence | 底稿证据支持该报告命题（或任一底稿实体由证据支撑） |
| CONTRADICTED_BY | ReportClaim → EvidenceSpan | 底稿证据与报告命题矛盾（金额/口径/基准日/方法不一致；同一文档内数字与大小写矛盾） |
| INSUFFICIENTLY_SUPPORTED_BY | ReportClaim → EvidenceSpan | 有部分或间接证据但不足以支撑命题（缺计算过程、缺来源、证据不可读） |
| MISSING_EVIDENCE | ReportClaim → Task | 按追问检索后底稿无对应证据（沉默，不等于证伪） |
| FROM_DOCUMENT | Chunk → Document | Chunk 来源于某个文档（系统自动添加） |
| EXTRACTED_FROM | ReportClaim ／ Conclusion ／ Evidence ／ Reasoning ／ Assumption ／ Rebuttal ／ Parameter ／ Method ／ Data ／ CalculationStep → Chunk | 实体从某个 Chunk 中提取（系统自动添加） |
| BELONGS_TO | Chunk → Document | Chunk 属于文档 |
| DERIVED_BY | Conclusion → Method | 结论由某种评估方法推导而来 |
| DEPENDS_ON | Method → Parameter | 评估方法依赖参数 |
| CALCULATED_FROM | Parameter → Data | 参数由数据项计算得出 |
| SOURCED_FROM | Data → Evidence | 数据项来源于证据文件 |
| CONDITIONED_ON | Conclusion ／ Method ／ Parameter → Assumption | 结论/方法/参数在假设成立前提下有效 |
| LIMITED_BY | Conclusion ／ Method → Rebuttal | 结论/方法受限制条件约束 |
| ANSWERS_WITH | Task → Parameter ／ Method ／ Conclusion ／ Data | 追问与底稿解答实体的关联（保留自 GSDJSense） |
| APPLIES_TO | Method → Conclusion | 方法适用性关系 |
