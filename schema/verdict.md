# 判定枚举与规则（verdict）

> 机器可读版 schema/verdict.yaml。

## 判定结果

| id | 名称 | 严重度 | 入问题清单 | 报告措辞 | 定义 |
| --- | --- | --- | --- | --- | --- |
| supported | 支撑 | info | 否 | 底稿已支撑 | 底稿中找到了明确证据，且与报告命题相符 |
| contradicted | 矛盾 / 反证 | high | 是 | 底稿与报告不一致 | 底稿存在明确证据，但与报告命题冲突（金额、口径、基准日、方法、主体等） |
| missing | 底稿无对应（不支持） | medium | 是 | 底稿未见对应依据 | 按追问要求检索后，底稿中找不到支撑该命题的证据（沉默，不等于命题为假） |
| insufficient | 证据不足 | medium | 是 | 证据不足以支撑 | 有部分或间接证据，但不足以支撑命题（缺计算过程、缺取值来源、证据不可读、多版本无法确定） |
| not_applicable | 不适用 | info | 否 | 不适用 | 该命题/追问对本案不适用（如未采用的方法、空表无披露且非必填） |

## 判定规则（按 order 顺序执行）

1. **deterministic_contradiction**（deterministic）：数值不相等（金额/比例/基准日/单位换算后仍不一致）、方法明确不适用、同一文档内数字与大小写矛盾 -> contradicted
2. **deterministic_support**（deterministic）：数值一致、字段逐字一致、汇总链勾稽通过 -> supported
3. **empty_after_escalation**（retrieval）：按 rule 规定的召回范围（同义关键词、扩大 page_size、去掉 document_ids 限制）检索后仍无命中 -> missing
4. **partial_evidence**（rule）：有命中但缺关键要素（无计算过程、无取值来源、证据不可读、多版本冲突） -> insufficient
5. **llm_judge**（llm）：以上均未命中，且存在可用证据 -> supported | contradicted | insufficient
6. **na_rule**（rule）：命题属于未采用的方法，或空表无披露且非必填 -> not_applicable

## 严重度覆盖

| 命题类型 | 判定为 | 严重度 |
| --- | --- | --- |
| conclusion | contradicted，missing | high |
| parameter | contradicted，missing | high |
| base_date | contradicted，missing | high |
| method | contradicted，missing | high |
