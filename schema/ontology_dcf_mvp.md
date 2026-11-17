# 资产评估底稿本体（极小闭环 MVP —— 收益法 DCF）

> 机器可读版：`schema/ontology_dcf_mvp.yaml`；设计背景见 `docs/底稿本体设计（极小闭环）.md`。
>
> 目标：用 **6 个核心类 + 4 条关系 + 4 条校验规则**，先跑通收益法（DCF）的「参数—计算—结论」逻辑闭环，回答“底稿到底够不够支撑报告结论”。

---

## 1. 核心类（6 个节点）

| 类名 | 中文名 | 核心作用 | 关键属性 |
| --- | --- | --- | --- |
| `Engagement` | 项目基准 | 锚定全局口径与时间边界 | `case_id`、`valuation_base_date`、`valuation_purpose`、`target_entity` |
| `ReportClaim` | 报告结论与关键披露 | 报告里写出来的结论值或核心量化指标 | `claim_kind`、`value`、`unit`、`locator` |
| `ValuationModel` | 测算底稿模型 | DCF 汇总表、WACC 表、预测分表 | `sheet_name`、`base_date`、`output_value`、`output_cell` |
| `Parameter` | 关键评估参数 | 必须留痕的核心输入与调整项（6 类必查） | `category`、`name`、`value`、`cell` |
| `SourceEvidence` | 支撑资料证据 | 原始底稿与外部数据，**区分来源性质** | `source_kind`（客观外部 / 历史审定 / 委托人提供）、`document_name`、`data_date` |
| `AnalysisNote` | 分析判断记录 | 评估师对参数合理性、差异原因的核查分析 | `summary`、`locator` |

### `Parameter` 的 6 类必查参数

1. `revenue_growth`：收入增长率 / 销量 / 单价
2. `gross_margin`：毛利率 / 成本率
3. `capex_depreciation`：资本性支出与折旧摊销
4. `working_capital`：营运资金及期末回收
5. `discount_rate_components`：折现率各构成（Rf、ERP、Beta、特定风险、债务成本、资本结构）
6. `non_operating_surplus`：非经营性资产/负债与溢余资产

---

## 2. 核心关系（4 条边）

| 关系 | 方向 | 含义 |
| --- | --- | --- |
| `DERIVED_FROM` | `ReportClaim → ValuationModel` | 报告结论或关键披露来自哪张测算表 |
| `USES_PARAM` | `ValuationModel → Parameter` | 测算表使用了哪些关键参数与调整项 |
| `SOURCED_FROM` | `Parameter → SourceEvidence` | 参数的数据来源是什么 |
| `JUSTIFIED_BY` | `Parameter → AnalysisNote` | 参数取值的分析判断与核查验证过程在哪 |

---

## 3. 闭环校验规则（4 条硬约束）

| 规则 | 名称 | 判定逻辑 | 映射问题集 | 对应处罚主题 |
| --- | --- | --- | --- | --- |
| `R-01` | 数值双向闭合 | `ReportClaim.value == ValuationModel.output_value` | `Q-SB-005` | `T-RP-02`、`T-VA-09` |
| `R-02` | 参数双链约束（防形式挂靠） | 关键 `Parameter` 不能只有 `client_provided` 来源，必须同时有客观/历史证据 **或** `AnalysisNote` | `Q-SB-001`、`Q-DCF-005/006/015/016` | `T-VA-01`（262条）、`T-VA-04`、`T-VA-03` |
| `R-03` | DCF 关键要素完备性 | `ValuationModel` 必须覆盖 6 类 `required_for_dcf` 参数，不得漏项 | `Q-DCF-008/012/017/018`、`Q-SB-007` | `T-VA-08` |
| `R-04` | 基准日口径一致 | `ValuationModel.base_date == Engagement.valuation_base_date` | `Q-RE-010` | `T-BM-01` |
