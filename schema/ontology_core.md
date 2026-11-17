# 资产评估底稿通用核心本体（Core + Profile）

> 机器可读版：`schema/ontology_core.yaml`；完整架构说明见 `docs/底稿本体架构设计.md`。
>
> 定义跨业务类型、跨评估方法通用的底稿支撑结构模具（**8 个核心类 + 7 条关系 + 5 类校验原语**），并通过声明式 Profile 挂载各项目专属规则。

---

## 1. 通用核心类（8 个）

| 类名 | 中文名 | 所属子域 | 覆盖程序 | 核心职责与关键属性 |
| --- | --- | --- | --- | --- |
| `Engagement` | 项目基准 | 全局与管理 | P1–P3 | 锚定业务分类（企业价值/单项/无形/财报目的）、监管标签（国资/司法/征收）、评估方法、基准日、报告日及签字/审核人员 |
| `SubjectAsset` | 评估对象与申报科目 | 对象与核查 | P1, P4, P5 | 被评估标的或 72 个申报科目；含索引号 `account_index`、账面值、经营/非经营/溢余属性、权属状态 `ownership_status`、所在地 |
| `ProcedureRecord` | 程序与合规留痕 | 对象与核查 | P3, P4, P8 | 现场勘察、盘点监盘、独立函证、原件核对签字、访谈纪要、三级审核实质意见与回复闭环记录 |
| `ValuationModel` | 测算底稿模型 | 模型与估值 | P6 | DCF 表组、市场法比较表、重置成本测算表或科目核实表；含文件索引、基准日、输出评估值、公式核验状态 |
| `Parameter` | 关键评估参数 | 模型与估值 | P6 | 驱动结论的重要参数、修正系数或调整项；含槽位编码 `slot_code`、取值、税前/税后及资本结构口径标签 |
| `SourceEvidence` | 支撑资料证据 | 支撑与论证 | P4, P5 | 原始底稿与外部数据；**强制按独立性分为 `external_independent`（外部客观）、`historical_audited`（历史审定/原件核对）、`client_provided`（委托方单方提供）** |
| `AnalysisNote` | 分析判断记录 | 支撑与论证 | P6, P7 | 方法适用性论证、参数取值合理性核查、历史差异原因分析、可比案例筛选剔除理由、增减值分析 |
| `ReportClaim` | 报告结论与披露 | 报告与披露 | P7 | 报告正文、评估说明、评估明细表载明的结论金额、核心参数陈述、评估假设、特别事项与有效期披露 |

---

## 2. 通用核心语义关系（7+1 条）

| 关系 | 方向 | 含义 |
| --- | --- | --- |
| `HAS_SUBJECT` | `Engagement → SubjectAsset` | 本次评估范围包含的评估对象、申报科目及表外资产负债 |
| `VERIFIED_BY` | `SubjectAsset → ProcedureRecord` | 对该评估对象或科目执行的勘察、盘点、函证、权属核验程序 |
| `VALUED_BY` | `SubjectAsset → ValuationModel` | 该对象或科目采用的评定估算模型 |
| `DERIVED_FROM` | `ReportClaim → ValuationModel` | 报告/说明/明细表结论数值来源于哪张测算模型 |
| `USES_PARAM` | `ValuationModel → Parameter` | 测算模型使用的关键评估参数与调整项 |
| `SOURCED_FROM` | `Parameter / ProcedureRecord → SourceEvidence` | 参数取值或程序核验所引用的支撑证据 |
| `JUSTIFIED_BY` | `ValuationModel / Parameter → AnalysisNote` | 方法适用性论证，或关键参数的核查验证与差异分析过程 |
| `DISCLOSES_FOR` | `ReportClaim → SubjectAsset` | 特别事项或评估说明针对对象权属瑕疵、受限或期后事项的披露 |

---

## 3. 五类通用校验原语

| 编号 | 原语编码 | 名称 | 核心校验逻辑 | 主要拦截处罚主题 |
| --- | --- | --- | --- | --- |
| `VP-01` | `SlotCompleteness` | 必查槽位完备性 | 按激活的 Profile 检查必查对象、程序、参数、分析记录槽位是否缺失 | `T-VA-02/07/08`、`T-FI-01/02`、`T-DC-06`、`T-WP-01` |
| `VP-02` | `DualLinkSubstantiation` | 参数双链防形式挂靠 | 关键参数不能仅连向 `client_provided` 证据，必须兼具客观/历史证据与 `AnalysisNote` | `T-VA-01`（262条）、`T-VA-03/04/05/06`、`T-DC-03` |
| `VP-03` | `CrossArtifactAlignment` | 跨载体口径与数值对齐 | 报告/说明/明细表与模型数值双向闭合、基准日与区域口径一致、索引号对齐、瑕疵必披露 | `T-RP-02/05`、`T-VA-09`、`T-BM-01`、`T-AR-02` |
| `VP-04` | `TimelineMonotonicity` | 程序时间线单调性 | 签约日 ≤ 现场勘察/盘点日 ≤ 程序完成日 ≤ 报告日 ≤ 归档日，经济行为文件日 ≤ 报告日 | `T-RP-06`、`T-AR-05` |
| `VP-05` | `RoleSegregationAndSignoff` | 职责分离与签署合规 | 签字评估师 ≠ 三级审核人、签字评估师实际参评、三级审核有实质意见闭环、原件核对与盘点签章齐备 | `T-AR-04`、`T-FI-03`、`T-CT-01`、`T-XX-01/02` |

---

## 4. 扩展规则包注册表（Profiles）

| Profile ID | 名称 | 触发条件 | 当前状态 |
| --- | --- | --- | --- |
| `profile_common_gl_archive` | 全项目通用管理、报告与归档包 | 所有项目默认加载（含国资/司法/征收开关） | 待细化 |
| `profile_dcf` | 收益法（DCF / 超额收益 / 减值测试）规则包 | `income_dcf` ∈ 采用方法 | 已有极小闭环（`schema/ontology_dcf_mvp.yaml`） |
| `profile_market` | 市场法规则包 | `market` ∈ 采用方法 | 待细化 |
| `profile_physical_intangible` | 单项实物与无形资产（成本法等）规则包 | 对象含不动产/设备/存货/无形资产 | 待细化 |
| `profile_financial_accounts` | 资产基础法财务类科目核验规则包 | 对象含财务类科目（对接 `步骤复核表.yaml`） | 待细化 |
