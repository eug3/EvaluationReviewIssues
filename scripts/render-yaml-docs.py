#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把仓库数据 YAML 渲染成同目录同名 .md 可读版。

用法：
    python3 scripts/render-yaml-docs.py             # 渲染全部
    python3 scripts/render-yaml-docs.py schema/claim.yaml  # 只渲染指定文件

渲染映射（YAML -> Markdown）：
    questions/底稿问题集.yaml       -> questions/底稿问题集.md
    questions/处罚问题映射.yaml     -> questions/处罚问题映射.md
    questions/步骤复核表.yaml       -> questions/步骤复核表.md
    questions/review_checklist.yaml -> questions/review_checklist.md
    schema/claim.yaml               -> schema/claim.md
    schema/verdict.yaml             -> schema/verdict.md
    schema/kg_schema.yaml           -> schema/kg_schema.md
    schema/report_section.yaml      -> schema/report_section.md
"""
import os
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NL = chr(10)


def load(rel):
    return yaml.safe_load(open(os.path.join(REPO, rel), encoding='utf-8'))


def emit(rel_yaml, lines):
    rel_md = rel_yaml[:-5] + '.md'
    open(os.path.join(REPO, rel_md), 'w', encoding='utf-8').write(NL.join(lines) + NL)
    print('render  ' + rel_yaml + '  ->  ' + rel_md + '  (' + str(len(lines)) + ' 行)')


def cell(v):
    s = str(v) if v is not None else ''
    return s.replace('|', '／').replace(NL, ' ')


def render_qbank():
    d = load('questions/底稿问题集.yaml')
    L = ['# ' + d['title'], '']
    L.append('> ' + d['purpose'])
    L.append('>')
    L.append('> 共 ' + str(d['summary']['groups']) + ' 组 / ' + str(d['summary']['questions']) + ' 条；机器可读版 questions/底稿问题集.yaml')
    L += ['', '来源：']
    L += ['- ' + s for s in d['sources']]
    legend = d.get('procedure_legend') or {}
    if legend:
        L += ['', '程序图例（每条问题标注所属基本程序）：']
        L += ['- **' + k + '** ' + v for k, v in legend.items()]
    L += ['', '各科目逐条操作步骤见 questions/步骤复核表.md。', '', '---']
    for i, g in enumerate(d['groups'], 1):
        L += ['', '## ' + str(i) + '. ' + g['name'] + '（' + str(len(g['questions'])) + '）', '', '来源：' + g['source'], '']
        for q in g['questions']:
            tag = ' `[' + q['procedure'] + ']`' if q.get('procedure') else ''
            L.append('- [ ] **' + q['id'] + '**' + tag + ' ' + q['ask'])
            if q.get('check'):
                L.append('      - 判定要点：' + q['check'])
    emit('questions/底稿问题集.yaml', L)


def render_penalty():
    d = load('questions/处罚问题映射.yaml')
    L = ['# ' + d['title'], '']
    L.append('> ' + d['purpose'])
    src = d.get('source') or {}
    sc = d.get('scope') or {}
    sm = d.get('summary') or {}
    L.append('>')
    L.append('> 源表：' + str(src.get('file', '')) + '（sheet：' + str(src.get('sheet', '')) + '）')
    L.append('>')
    L.append('> 范围：' + str(sc.get('reports', '')) + ' 份报告 / ' + str(sc.get('penalty_docs', ''))
             + ' 份处罚文件 / ' + str(sc.get('facts_dedup', '')) + ' 条去重事实；'
             + '主题 ' + str(sm.get('themes', '')) + ' 个（缺口 ' + str(sm.get('themes_gap', ''))
             + '），已归类 ' + str(sm.get('facts_classified', '')) + ' / 未归类 ' + str(sm.get('facts_unclassified', '')))
    L.append('>')
    L.append('> 抽取脚本：' + str(src.get('extracted_by', '')) + '；机器可读版 questions/处罚问题映射.yaml')
    if src.get('confidential'):
        L.append('>')
        L.append('> ⚠️ 保密说明：' + str(src['confidential']))
    if sc.get('note'):
        L += ['', '> 口径说明：' + str(sc['note'])]

    # 用途
    L += ['', '## 如何使用', '']
    L += ['- ' + s for s in (d.get('how_to_use') or [])]

    # 按八大程序 + 红线：主题表
    L += ['', '## 主题聚类（按监管处罚频次降序）', '',
          '| 主题 | 程序 | 名称 | 频次 | 主主题 | 缺口 | 扩充前覆盖 | 本轮新增 |',
          '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for t in d.get('themes') or []:
        flag = '🚩红线' if t.get('redline') else ('❌缺口' if t.get('gap') else '')
        cov = ', '.join(t.get('covered_by') or []) or '—'
        add = ', '.join(t.get('added_by') or []) or '—'
        L.append('| ' + t['id'] + ' | ' + str(t.get('procedure', '')) + ' | ' + cell(t['name'])
                 + ' | ' + str(t.get('hits', '')) + ' | ' + str(t.get('primary_hits', ''))
                 + ' | ' + flag + ' | ' + cell(cov) + ' | ' + cell(add) + ' |')

    # 各程序主题分组 + 示例
    L += ['', '## 各程序高频问题与脱敏示例', '']
    for p in d.get('procedures') or []:
        L += ['', '### ' + p['id'] + ' ' + p['name']
              + '（事实 ' + str(p.get('count_by_source_type', '')) + '，主主题锚定 '
              + str(p.get('count_primary_theme', '')) + '）', '']
        tmap = {t['id']: t for t in d.get('themes') or []}
        for tid in p.get('themes') or []:
            t = tmap.get(tid)
            if not t:
                continue
            head = '- **' + tid + '** ' + t['name'] + '（' + str(t.get('hits', '')) + '）'
            if t.get('gap'):
                head += ' ❌缺口'
            if t.get('redline'):
                head += ' 🚩红线'
            if t.get('covered_by'):
                head += ' 扩充前覆盖：' + ', '.join(t['covered_by'])
            if t.get('added_by'):
                head += ' 本轮新增：' + ', '.join(t['added_by'])
            L.append(head)
            for ex in (t.get('examples') or [])[:2]:
                L.append('      - 例：' + cell(ex))

    # 未归类样本
    if d.get('unclassified_samples'):
        L += ['', '## 未归类事实样本（供主题字典迭代）', '']
        L += ['- ' + cell(s) for s in d['unclassified_samples']]

    # 高频引用准则
    if d.get('standards_cited_top'):
        L += ['', '## 处罚决定高频引用准则条款', '',
              '| 准则/条款 | 引用次数 |', '| --- | --- |']
        for s in d['standards_cited_top']:
            L.append('| ' + cell(s.get('name', '')) + ' | ' + str(s.get('count', '')) + ' |')

    # 分布
    dist = d.get('distribution') or {}
    if dist.get('by_business_type'):
        L += ['', '## 处罚分布', '', '### 按评估业务分类', '', '| 业务分类 | 事实数 |', '| --- | --- |']
        for x in dist['by_business_type']:
            L.append('| ' + cell(x.get('name', '')) + ' | ' + str(x.get('count', '')) + ' |')
    if dist.get('by_regulator'):
        L += ['', '### 按监管机构/地区（TOP）', '', '| 机构/地区 | 事实数 |', '| --- | --- |']
        for x in dist['by_regulator'][:12]:
            L.append('| ' + cell(x.get('name', '')) + ' | ' + str(x.get('count', '')) + ' |')
    emit('questions/处罚问题映射.yaml', L)


def render_steps():
    d = load('questions/步骤复核表.yaml')
    L = ['# ' + d['title'], '']
    L.append('> 来源：' + d['source'])
    L.append('>')
    L.append('> 共 ' + str(d['summary']['subjects']) + ' 个科目 / ' + str(d['summary']['steps_total']) + ' 条步骤（由 ' + d['extracted_by'] + ' 抽取，可重复执行）')
    L.append('>')
    L.append('> ' + d['note'])
    LABEL = {'C3': '一、流动资产', 'C4': '二、非流动资产', 'C5': '三、流动负债', 'C6': '四、非流动负债', 'SY1': '五、收益法'}
    cur = None
    for s in d['subjects']:
        grp = (s['index'] or '-').split('-')[0]
        if grp != cur:
            cur = grp
            L += ['', '## ' + LABEL.get(grp, grp), '']
        L += ['', '### ' + s['subject'] + '【' + (s['index'] or '-') + '】（' + str(s['step_count']) + ' 步）', '']
        if s['variant_count'] > 1:
            L += ['> 模板有 ' + str(s['variant_count']) + ' 套，取最全的一套', '']
        for j, st in enumerate(s['steps'], 1):
            L.append('- [ ] ' + str(j) + '. ' + st)
    emit('questions/步骤复核表.yaml', L)


def render_checklist():
    d = load('questions/review_checklist.yaml')
    L = ['# 准则追问问题集（参考）', '']
    L.append('> 早期按准则视角整理的「报告命题 -> 底稿证据」追问集；当前主问题集是 questions/底稿问题集.md。')
    L.append('>')
    L.append('> 机器可读版 questions/review_checklist.yaml。')
    for g in d['groups']:
        head = '## ' + g['id'] + ' ' + g['name']
        if g.get('claim_type'):
            head += '（claim_type: ' + g['claim_type'] + '）'
        L += ['', head, '']
        for q in g['questions']:
            L.append('- [ ] **' + q['id'] + '** ' + q['ask'])
            if q.get('expect_evidence'):
                L.append('      - 期望证据：' + q['expect_evidence'])
            if q.get('rule'):
                L.append('      - 判定规则：' + q['rule'])
            va, se = q.get('verdict_if_absent'), q.get('severity')
            if va or se:
                L.append('      - 缺失判定：' + str(va or '-') + '（severity: ' + str(se or '-') + '）')
            if q.get('ground'):
                L.append('      - 依据：' + q['ground'])
    emit('questions/review_checklist.yaml', L)


def render_claim():
    d = load('schema/claim.yaml')
    cts = d['claim_types']
    L = ['# 报告命题类型（claim types）', '']
    L.append('> 报告中「可判定陈述」的分类，共 ' + str(len(cts)) + ' 类；机器可读版 schema/claim.yaml。')
    L += ['', '## 总览', '', '| id | 名称 | 对应追问组 |', '| --- | --- | --- |']
    for c in cts:
        L.append('| ' + c['id'] + ' | ' + cell(c['name']) + ' | ' + cell('，'.join(c.get('question_groups') or [])) + ' |')
    L.append('---')
    for c in cts:
        L += ['', '## ' + c['id'] + ' ' + c['name'], '', c.get('description', '')]
        if c.get('detect_hints'):
            L += ['', '**检测提示**：'] + ['- ' + str(x) for x in c['detect_hints']]
        if c.get('value_fields'):
            L += ['', '**取值字段**：'] + ['- ' + str(x) for x in c['value_fields']]
        if c.get('examples'):
            L += ['', '**示例**：'] + ['- ' + cell(x) for x in c['examples']]
    emit('schema/claim.yaml', L)


def render_verdict():
    d = load('schema/verdict.yaml')
    L = ['# 判定枚举与规则（verdict）', '']
    L.append('> 机器可读版 schema/verdict.yaml。')
    L += ['', '## 判定结果', '', '| id | 名称 | 严重度 | 入问题清单 | 报告措辞 | 定义 |', '| --- | --- | --- | --- | --- | --- |']
    for v in d['verdicts']:
        L.append('| ' + v['id'] + ' | ' + cell(v['name']) + ' | ' + str(v.get('severity', '')) + ' | ' + ('是' if v.get('in_issue_list') else '否') + ' | ' + cell(v.get('report_wording', '')) + ' | ' + cell(v.get('definition', '')) + ' |')
    L += ['', '## 判定规则（按 order 顺序执行）', '']
    for r in d['decision_rules']:
        L.append(str(r['order']) + '. **' + r['id'] + '**（' + r['kind'] + '）：' + r['when'] + ' -> ' + r['verdict'])
    if d.get('severity_overrides'):
        L += ['', '## 严重度覆盖', '', '| 命题类型 | 判定为 | 严重度 |', '| --- | --- | --- |']
        for s in d['severity_overrides']:
            L.append('| ' + cell(s['claim_type']) + ' | ' + cell('，'.join(s.get('when_verdict') or [])) + ' | ' + str(s['severity']) + ' |')
    emit('schema/verdict.yaml', L)


def render_kg():
    d = load('schema/kg_schema.yaml')
    L = ['# 知识图谱模型（参考）', '']
    L.append('> 机器可读版 schema/kg_schema.yaml。')
    L += ['', '## 节点类型', '', '| 节点 | 说明 | 虚拟 | 示例 |', '| --- | --- | --- | --- |']
    for k, v in d['node_types'].items():
        L.append('| ' + k + ' | ' + cell(v.get('description', '')) + ' | ' + ('是' if v.get('virtual') else '否') + ' | ' + cell('；'.join(v.get('examples') or [])) + ' |')
    L += ['', '## 边类型', '', '| 边 | 方向 | 说明 |', '| --- | --- | --- |']
    for k, v in d['edge_types'].items():
        L.append('| ' + k + ' | ' + cell(v.get('direction', '')) + ' | ' + cell(v.get('description', '')) + ' |')
    emit('schema/kg_schema.yaml', L)


def tax_block(L, key, v, indent):
    L.append(indent + '- **' + str(v.get('name', key)) + '**（' + key + '）')
    if v.get('standard'):
        L.append(indent + '  - 准则依据：' + str(v['standard']))
    for t in v.get('typical') or []:
        L.append(indent + '  - ' + str(t))
    for k2, v2 in v.items():
        if k2 in ('name', 'standard', 'typical'):
            continue
        if isinstance(v2, dict):
            tax_block(L, k2, v2, indent + '  ')
        elif isinstance(v2, list):
            L.append(indent + '  - ' + k2 + '：' + '；'.join(str(x) for x in v2))
        else:
            L.append(indent + '  - ' + k2 + '：' + str(v2))


def render_report_section():
    d = load('schema/report_section.yaml')
    L = ['# 评估报告章节与底稿支撑（参考）', '']
    L.append('> 机器可读版 schema/report_section.yaml。')
    md = d['mcp_dataset']
    L += ['', '## 准则数据集（RAGFlow MCP）', '']
    L += ['- dataset_id：' + md['dataset_id'], '- 名称：' + md['dataset_name'] + '（' + str(md['document_count']) + ' 份文档）', '- 检索工具：' + md['tool'], '- ' + md.get('notice', '')]
    L += ['', '## 依据准则', '', '| id | 名称 | 文号 | 施行 | 文档ID |', '| --- | --- | --- | --- | --- |']
    for k, v in d['standards'].items():
        L.append('| ' + k + ' | ' + cell(v.get('name', '')) + ' | ' + cell(v.get('ref', '')) + ' | ' + str(v.get('effective', '')) + ' | ' + str(v.get('dataset_document_id', '')) + ' |')
    L += ['', '## 底稿分类', '']
    for k, v in d['workpaper_taxonomy'].items():
        tax_block(L, k, v, '')
    L += ['', '## 报告章节与底稿支撑（' + str(len(d['report_sections'])) + ' 章）', '']
    for s in d['report_sections']:
        L += ['', '## ' + str(s['order']) + '. ' + s['name'] + '（' + s['id'] + '）', '']
        if s.get('standard_basis'):
            L.append('**标准依据**：' + '；'.join(s['standard_basis']))
        if s.get('report_must_state'):
            L += ['', '**报告应载**：'] + ['- ' + str(x) for x in s['report_must_state']]
        if s.get('claim_types'):
            L += ['', '**命题类型**：' + '，'.join(s['claim_types'])]
        if s.get('workpaper_support'):
            L += ['', '**底稿支撑**：', '', '| 支撑项 | 类型 | 期望内容 | 位置 | 追问组 | 缺则 |', '| --- | --- | --- | --- | --- | --- |']
            for w in s['workpaper_support']:
                ia = w.get('if_absent') or {}
                ias = (str(ia.get('verdict', '')) + ' / ' + str(ia.get('severity', ''))).strip(' /') if ia else ''
                L.append('| ' + w['id'] + ' | ' + str(w.get('workpaper_type', '')) + ' | ' + cell(w.get('expected', '')) + ' | ' + cell(w.get('where', '')) + ' | ' + str(w.get('question_group', '')) + ' | ' + ias + ' |')
    emit('schema/report_section.yaml', L)


ALL = [
    ('questions/底稿问题集.yaml', render_qbank),
    ('questions/处罚问题映射.yaml', render_penalty),
    ('questions/步骤复核表.yaml', render_steps),
    ('questions/review_checklist.yaml', render_checklist),
    ('schema/claim.yaml', render_claim),
    ('schema/verdict.yaml', render_verdict),
    ('schema/kg_schema.yaml', render_kg),
    ('schema/report_section.yaml', render_report_section),
]


def main():
    want = sys.argv[1:]
    for rel, fn in ALL:
        if not want or rel in want:
            fn()


if __name__ == '__main__':
    main()