#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从《2024年处罚监管数据》抽取问题事实，按主题聚类并映射到底稿问题集，
输出 questions/处罚问题映射.yaml。

源文件为保密文件，已由 .gitignore 排除、不入库；本脚本输出**已脱敏**：
抹去评估机构名、企业与委托方名称（含简称）、人员姓名、执业登记编号、
报告号/处罚文号，只保留问题事实表述、金额与准则引用。

依赖：openpyxl、pyyaml
用法：python3 scripts/extract-penalty-issues.py
"""
import collections
import os
import re
import sys

import openpyxl
import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(
    REPO,
    "华信电子底稿编制指引（征求意见稿）",
    "20251112 2024年处罚监管数据 (保密）.xlsx",
)
SHEET = "表4.评估报告信息表"
OUT = os.path.join(REPO, "questions", "处罚问题映射.yaml")
QBANK = os.path.join(REPO, "questions", "底稿问题集.yaml")

# 八大基本程序（取自源文件「下拉菜单」sheet，即《资产评估执业准则——资产评估程序》口径）
PROCEDURES = [
    ("P1", "明确业务基本事项方面"),
    ("P2", "订立业务委托合同方面"),
    ("P3", "编制资产评估计划方面"),
    ("P4", "进行现场调查方面"),
    ("P5", "收集整理评估资料方面"),
    ("P6", "评定估算形成结论方面"),
    ("P7", "编制出具评估报告方面"),
    ("P8", "整理归集评估档案方面"),
]
PROC_NAME = dict(PROCEDURES)
# 源表问题类型的几种写法归一（「进行评估现场调查方面」等）
PROC_ALIAS = {
    "明确业务基本事项方面": "P1",
    "订立业务委托合同方面": "P2",
    "编制资产评估计划方面": "P3",
    "进行评估现场调查方面": "P4",
    "进行现场调查方面": "P4",
    "收集整理评估资料方面": "P5",
    "评定估算形成结论方面": "P6",
    "评定估算形成评估结论方面": "P6",
    "编制出具评估报告方面": "P7",
    "整理归集评估档案方面": "P8",
}

# ---------------------------------------------------------------- 脱敏
# 占位符先以 Unicode 私用区哨兵写入，避免被后续规则二次匹配（级联替换），最后统一还原
PLACE_ORG = "某评估机构"
PLACE_ENT = "某企业"
PLACE_UNIT = "某单位"
PLACE_PERSON = "某某"
PLACE_REG = "（登记编号略）"
PLACE_REPORT = "某评报字号"
PLACE_PROJECT = "某项目"
PLACE_LISTED = "某上市公司"
PLACE_ID = "（证件号略）"
PLACE_NO_REPORT = "某号报告"
SENTINELS = {
    "\ue000": PLACE_ORG,
    "\ue001": PLACE_ENT,
    "\ue002": PLACE_UNIT,
    "\ue003": PLACE_PERSON,
    "\ue004": PLACE_REG,
    "\ue005": PLACE_REPORT,
    "\ue006": PLACE_PROJECT,
    "\ue007": PLACE_LISTED,
    "\ue008": PLACE_ID,
    "\ue009": PLACE_NO_REPORT,
}
S_ORG, S_ENT, S_UNIT, S_PERSON, S_REG, S_REPORT, S_PROJECT, S_LISTED, S_ID, S_NO_REPORT = SENTINELS

# 准则/法规等公开文号前缀，属公共信息，保留不脱敏
PUBLIC_DOC_PREFIX = re.compile(
    r"^(法释|法办|中评协|财资|财会|财税|国资|证监|银保监|证监会|国务院|国资发|评估协)"
)
# 评估报告号/处罚文号：前缀 + 〔年份〕 + （资/评/咨）字 + 第N号（允许内部空格与「、」枚举号）
RE_REPORT_NO = re.compile(
    r"[\u4e00-\u9fa5A-Za-z]{2,14}"
    r"\s*[〔\[（(]\s*\d{4}\s*[〕\]）)]"
    r"(?:\s*[（(]?[资评咨]*[）)]?字)?"
    r"\s*第?\s*[0-9A-Za-z\s\-—、]{1,24}?\s*号"
    r"(?:\s*、\s*第?\s*[0-9A-Za-z\s\-—]{1,12}?\s*号)*"
)
RE_REPORT_TAIL = re.compile(r"第\s*[0-9A-Za-z\-—]{2,12}\s*号报告")
# 评估机构全称（含空格断字、可带括号地域名，如「坤疆资产评估（北京）有限公司」）
RE_ORG_FULL = re.compile(
    r"[\u4e00-\u9fa5A-Za-z（）()·]{2,30}?"
    r"(?:资产评估|不动产土地资产评估|房地产估价|土地估价|评估咨询|评估)"
    r"(?:\s*[（(][\u4e00-\u9fa5A-Za-z]{2,8}[）)])?"
    r"(?:有限公司|有限责任公司|事务所|公司|分公司|评估所)"
)
RE_ENT_FULL = re.compile(
    r"《?[\u4e00-\u9fa5A-Za-z（）()·]{2,30}?"
    r"(?:股份有限公司|有限责任公司|集团有限公司|集团公司|有限公司)"
)
RE_ENT_FOREIGN = re.compile(
    r"[A-Za-z0-9&.,\- ]{2,40}?"
    r"(?:[（(][A-Za-z]{1,4}[）)]\s*)?"
    r"(?:Limited|Ltd\.?|Inc\.?|LLC|Corp\.?|GmbH|Holdings|Company)"
)
# 上市公司简称 + 股票代码（可比公司）；名称限 6 字内避免吞掉前文
RE_LISTED = re.compile(r"[\u4e00-\u9fa5A-Za-z]{2,6}?\s*[（(]\s*\d{6}\s*\.\s*[A-Z]{2}\s*[）)]")
RE_STOCK_CODE = re.compile(r"[（(]\s*\d{6}\s*\.\s*[A-Z]{2}\s*[）)]")
# 政府/委托单位（仅机构名脱敏；省市区等地名不单独识别）
RE_GOV = re.compile(
    r"[\u4e00-\u9fa5]{2,16}?"
    r"(?:公安局|自然资源局|财政局|住房和城乡建设局|工业和信息化局|市场监督管理局|民政局|税务局"
    r"|发展和改革局|水务局|交通运输局|林业局|农业农村局|教育局|卫生健康局|人民政府|管理委员会|管委会|指挥部|管理局)"
)
# 项目/楼盘名（含间隔号）
RE_PROJECT_NAME = re.compile(r"[\u4e00-\u9fa5A-Za-z0-9]{2,16}·[\u4e00-\u9fa5A-Za-z0-9]{1,12}")
RE_REG_NO = re.compile(r"（?登记编号[:：]?\s*\d{5,}）?")
RE_ID_NO = re.compile(r"\d{17}[\dXx]")

# 人名上下文规则：每条给 (regex, replacer)。仅替换姓名，保留职业称谓等前缀。
def _p1(m):  # 整个匹配即姓名；末尾功能词回退
    name = m.group(0)
    while name and name[-1] in NAME_FUNC_TAIL:
        name = name[:-1]
    if len(name) < 2 or name in NAME_STOP_AFTER or name in NAME_STOP_WORD:
        return m.group(0)
    return S_PERSON + m.group(0)[len(name):]


def _keep1(m):  # 组1保留 + 组2姓名；姓名末尾若为功能词则回退保留，防止吞掉「未/不」等改变语义
    name = m.group(2)
    while name and name[-1] in NAME_FUNC_TAIL:
        name = name[:-1]
    if len(name) < 2 or name in NAME_STOP_AFTER or name in NAME_STOP_WORD:
        return m.group(0)
    rest = m.group(2)[len(name):]
    return m.group(1) + S_PERSON + rest


def _sub_maoyong(m):
    name = _name_trim(m.group(0)[2:])
    tail = m.group(0)[2:][len(name):]
    if len(name) < 2:
        return m.group(0)
    return "冒用" + S_PERSON + tail


RE_NAME_RULES = [
    # 特定上下文规则优先，避免通用规则贪婪吞掉前缀字
    (re.compile(r"冒用[\u4e00-\u9fa5]{2,3}(?=名义)"), lambda m: "冒用" + S_PERSON),
    (re.compile(r"冒用[\u4e00-\u9fa5]{2,4}"), _sub_maoyong),
    (re.compile(r"[「“][\u4e00-\u9fa5]{2,4}[」”]名义"), lambda m: "「" + S_PERSON + "」名义"),
    (re.compile(r"(评估助理|签字评估师|评估师)([\u4e00-\u9fa5]{2,3})"), _keep1),
    (re.compile(r"(股东|合伙人|法定代表人|实际控制人|的)([\u4e00-\u9fa5]{2,3})(?=专门负责|持有|未取得|负责)"), _keep1),
    (re.compile(r"(委托人|产权持有人|负责人)([\u4e00-\u9fa5]{2,3})(?=[，。；、为系])"), _keep1),
    (re.compile(r"(?<=[，。；：])\s*[\u4e00-\u9fa5]{2,3}(?=持有|名下|出资)"), _p1),  # 句首人名+持股语境
    (re.compile(r"[\u4e00-\u9fa5]{2,3}(?=伪造|提供虚假)"), _p1),
    (re.compile(r"[\u4e00-\u9fa5]{2,3}(?=\ue004)"), _p1),  # 姓名 + （登记编号略）哨兵
]
# 姓名末尾的功能词：若被当人名的一部分匹配到，须回退保留（如「未取得」的「未」）
NAME_FUNC_TAIL = set("未不有没为系与和及或等且已将被对由在自其该")
# 句法词不视为人名（防止「经查持有」等被误抹）
NAME_STOP_WORD = {
    "经查", "其中", "上述", "前述", "该公司", "该机构", "本机构", "你公司", "你单位",
    "并且", "同时", "另外", "此外", "但是", "如果", "由于", "根据", "按照", "通过",
    "存在", "发现", "显示", "表明", "证明", "涉及", "属于", "作为", "认为", "要求",
    "未持", "已持", "共持", "均持", "分别", "合计", "累计",
    "机构", "股东", "公司", "企业", "本人", "单位", "合伙", "协会", "部门", "小组",
}
# 「资产评估师资格」等职业称谓后的普通词，不得当人名抹掉
NAME_STOP_AFTER = {
    "资格", "证书", "名义", "签名", "签字", "登记", "职称", "执业", "人员", "助理", "声明",
    "承诺", "编号", "信息", "情况", "报告", "意见", "记录", "程序", "结论", "价值", "机构",
    "公司", "企业", "单位", "协会", "部门", "负责", "专职", "兼职", "名册", "印章", "时间",
    "日期", "姓名", "考试", "注册", "职业", "专业", "本人", "等人", "等", "的",
}

# 「XX公司」式简称：命中后按停用词过滤；前缀含动词/虚词时从最后一个停用字符之后起算，防吞前文
RE_ENT_SHORT = re.compile(r"[\u4e00-\u9fa5A-Za-z·]{2,8}公司")
SHORT_STOP_CHAR = set("的该这其有和与及或为是于经查持有出具涉及作为被将把对从向在")


def _sub_ent_short(m):
    full = m.group(0)
    prefix = full[:-2]
    pos = [prefix.rfind(c) for c in SHORT_STOP_CHAR if c in prefix]
    cut = max(pos) if pos else -1
    head, tail = prefix[: cut + 1], prefix[cut + 1:] + "公司"
    if not tail or len(tail) < 3 or tail in ENT_SHORT_STOP:
        return full
    return head + S_ENT


def _name_trim(name: str) -> str:
    """剥掉误入姓名部分的尾部普通词（如「他人名义」中的「名义」）。"""
    while True:
        for w in NAME_STOP_AFTER:
            if len(w) >= 2 and name.endswith(w) and len(name) > len(w):
                name = name[: -len(w)]
                break
        else:
            return name


ENT_SHORT_STOP = {
    "你公司", "该公司", "本公司", "母公司", "子公司", "分公司", "上市公司", "新公司", "小公司",
    "集团公司", "控股公司", "目标公司", "被评估公司", "关联公司", "可比公司", "合作公司",
    "房地产公司", "物业公司", "建筑公司", "科技公司", "投资公司", "租赁公司", "担保公司",
    "证券公司", "基金公司", "保险公司", "银行公司", "信托公司", "期货公司", "酒店公司",
    "旅游公司", "文化公司", "传媒公司", "网络公司", "软件公司", "电子公司", "通信公司",
    "医药公司", "国际公司", "实业公司", "农业公司", "林业公司", "矿业公司", "水利公司",
    "电力公司", "燃气公司", "供水公司", "交通公司", "运输公司", "物流公司", "贸易公司",
    "商业公司", "两家公司", "多家公司", "各公司", "几家公司", "同公司", "系公司", "壳公司",
    "被投资公司", "标的公司", "项目公司", "持股公司", "运营公司", "开发公司", "建设公司",
    "全资子公司", "控股子公司", "参股公司", "被评估单位", "被投资企业", "拟上市公司",
}
RE_ALIAS_DEF = re.compile(r"[（(](?:以下简称|以下称|下称|简称)[「“\"']?([^）)「」\"']{2,14})[」”\"']?[）)]")
# 源文件中出现的机构简称（同文件另有全称，简称本身无法由规则推导），全局替换
KNOWN_ABBR = {
    "中为所": S_ORG,
}
# 源文件由 PDF 抽取，专名常被空格断开（如「旅游开 发有限公司」），先合并 CJK 间空格
RE_CJK_SPACE = re.compile(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])")
# 机构/企业全称误伤保护：匹配文本含这些词则不替换（如「资产评估协会…公司」跨段误连）
ORG_GUARD = ("协会", "学会", "中评协", "财政部", "证监会", "网址", "网站")


def _sub_org(m):
    return m.group(0) if any(g in m.group(0) for g in ORG_GUARD) else S_ORG


def _sub_ent(m):
    return m.group(0) if any(g in m.group(0) for g in ORG_GUARD) else S_ENT


# 全局别名表：「以下简称XX」的定义与使用常分散在不同事实条目，
# 先全量收集再逐条脱敏，防止别名在其他条目中漏抹
GLOBAL_ALIASES = set()


def collect_aliases(texts) -> None:
    for t in texts:
        for m in RE_ALIAS_DEF.finditer(re.sub(r"\s+", " ", t or "")):
            a = m.group(1).strip()
            if 2 <= len(a) <= 14 and not any(k in a for k in ("公司名义", "评估", "报告")):
                GLOBAL_ALIASES.add(a)


def desensitize(text: str) -> str:
    """抹去机构/企业名（含简称、别名、项目名）、人名、登记编号、报告号/处罚文号；
    保留金额、比例、准则名称与条款号。所有占位先写哨兵，最后统一还原，避免级联替换。"""
    s = re.sub(r"\s+", " ", text or "").strip()
    while True:
        s2 = RE_CJK_SPACE.sub("", s)
        if s2 == s:
            break
        s = s2
    # 1) 别名：本条内定义 + 全局收集（「以下简称XX」），统一替换
    aliases = set(GLOBAL_ALIASES)
    for m in RE_ALIAS_DEF.finditer(s):
        a = m.group(1).strip()
        if 2 <= len(a) <= 14 and not any(k in a for k in ("公司名义", "评估", "报告")):
            aliases.add(a)
    # 2) 报告号/文号（保留准则法规类公开文号）
    s = RE_REPORT_NO.sub(
        lambda m: m.group(0) if PUBLIC_DOC_PREFIX.match(m.group(0).strip()) else S_REPORT, s
    )
    s = RE_REPORT_TAIL.sub(S_NO_REPORT, s)
    s = RE_REG_NO.sub(S_REG, s)
    s = RE_ID_NO.sub(S_ID, s)
    # 3) 机构/企业/项目全称（先机构后企业；上市公司简称+代码优先）
    s = RE_LISTED.sub(S_LISTED, s)
    s = RE_STOCK_CODE.sub("", s)
    s = RE_ORG_FULL.sub(_sub_org, s)
    s = RE_ENT_FULL.sub(_sub_ent, s)
    s = RE_ENT_FOREIGN.sub(S_ENT, s)
    s = RE_GOV.sub(S_UNIT, s)
    s = RE_PROJECT_NAME.sub(S_PROJECT, s)
    for a, ph in KNOWN_ABBR.items():
        s = s.replace(a, ph)
    for a in sorted(aliases, key=len, reverse=True):
        s = s.replace(a, S_ENT)
    # 4) XX公司 简称
    s = RE_ENT_SHORT.sub(_sub_ent_short, s)
    # 5) 人名（仅明确上下文；职业称谓后的普通词不动）
    for rx, fn in RE_NAME_RULES:
        s = rx.sub(fn, s)
    # 6) 还原哨兵，折叠重复占位符
    for k, v in SENTINELS.items():
        s = s.replace(k, v)
    for p in (PLACE_ORG, PLACE_ENT, PLACE_UNIT, PLACE_PERSON, PLACE_REPORT, PLACE_REG, PLACE_PROJECT):
        s = re.sub(re.escape(p) + r"(?:\s*" + re.escape(p) + r")+", p, s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def clip(text: str, limit: int = 170) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("。", "；", "，"):
        i = cut.rfind(sep)
        if i > limit * 0.5:
            return cut[: i + 1].rstrip("，；") + "…"
    return cut + "…"


# ---------------------------------------------------------------- 主题词典
# proc 为主题归属的八大程序（None=跨程序/红线）；gap=True 表示现有问题集未覆盖或覆盖不足；
# redline=True 属合规红线；scope_out=True 不属底稿复核范围。
# 顺序即优先级：越具体的主题放前面（主主题按源表问题类型锚定，见 assign）。
THEMES = [
    # --- 红线（最优先，避免被泛主题吞并） ---
    dict(id="T-XX-01", proc=None, name="冒签/代签报告、伪造证明材料（合规红线）",
         kw=["冒签", "代签", "伪造", "冒用", "虚假材料"],
         covered_by=[], gap=True, redline=True),
    dict(id="T-XX-02", proc=None, name="签字评估师未实际参与评估程序（合规红线）",
         kw=["并非签字评估师", "未实际参与", "签字评估师未", "未到现场", "未到现场"],
         covered_by=[], gap=True, redline=True),
    dict(id="T-XX-03", proc=None, name="评估报告未在备案系统备案（非底稿事项）",
         kw=["备案系统", "备案信息管理系统", "未按规定在备案"],
         covered_by=[], gap=False, scope_out=True,
         scope_note="机构行政合规事项，与底稿编制/送审/复核无关，不纳入问题集"),
    dict(id="T-XX-04", proc=None, name="机构质控体系未有效实施、质控人员无资格、不配合检查（合规红线）",
         kw=["未能有效实施内部质量控制", "内部质量控制", "质量控制混乱", "未取得资产评估师资格",
             "不如实提供检查资料", "仍未提供", "以你公司名义出具"],
         covered_by=[], gap=True, redline=True),
    # --- P6 评定估算 ---
    dict(id="T-VA-07", proc="P6", name="无评定估算过程/无评估计算底稿即形成结论",
         kw=["无评定估算", "无任何形式的工作底稿", "未见现场调查、评估测算", "无评估计算",
             "缺少评估计算过程", "未履行资产评估基本程序", "操作类底稿不支持评估结论",
             "无测算", "未见测算", "计算过程底稿缺失"],
         covered_by=[], gap=True),
    dict(id="T-WP-01", proc=None, name="管理类/操作类工作底稿整体缺失或内容不规范（程序未履行）",
         kw=["无管理类工作底稿", "无操作类工作底稿", "工作底稿内容缺失", "工作底稿内容规范性不足",
             "底稿规范性不足", "部分底稿缺失", "底稿内容不规范", "评估程序履行不充分",
             "评估程序执行不到位", "评估程序严重缺失", "程序严重缺失", "底稿不完整",
             "工作底稿缺失", "底稿缺失"],
         covered_by=["Q-SR-004", "Q-AR-006"], gap=True),
    dict(id="T-VA-02", proc="P6", name="评估方法选取不当或未论证适用性",
         kw=["评估方法选取", "方法选取", "方法选用", "两种评估方法", "单一方法", "方法适用",
             "方法的适用性", "一种评估方法", "评估模型选用", "技术思路", "未根据评估准则要求选取评估方法",
             "未根据相关条件恰当选择评估方法", "评估方法选择不当", "方法选择", "方法运用",
             "比较因素修正体系", "遗漏出租", "收益法评估中遗漏"],
         covered_by=[], gap=True),
    dict(id="T-VA-01", proc="P6", name="重要参数选取缺少依据与形成过程记录",
         kw=["选取依据", "取值依据", "形成过程", "确定过程", "分析、判断过程", "分析测算",
             "缺少必要的分析", "取价依据", "修正因素", "费率取值", "测算过程", "计算过程",
             "取值无依据", "依据不充分", "合理性依据不足", "无计算依据", "取值不合理",
             "取价参数", "确定相应的取价参数", "未合理分析", "证明材料"],
         covered_by=["Q-DCF-006"], gap=True),
    dict(id="T-VA-09", proc="P6", name="计算公式、勾稽或汇总错误",
         kw=["计算错误", "公式错误", "公式或参数等计算错误", "勾稽关系汇总", "加总错误",
             "汇总处理错误", "数据错误", "计算有误", "现值系数计算公式", "测算有误",
             "数据引用错误", "计算模型错误", "公式选取错误", "预先设定的价值"],
         covered_by=["Q-DE-012", "Q-DE-019"], gap=True),
    dict(id="T-VA-03", proc="P6", name="折现率及收益法参数取值错误",
         kw=["折现率", "资本化率", "无风险报酬", "风险报酬率", "贝塔", "β", "Beta", "永续",
             "预测期", "所得税税率", "资本结构", "wacc", "WACC", "折现年限"],
         covered_by=["Q-DCF-009", "Q-DCF-010", "Q-DCF-011"], gap=False),
    dict(id="T-VA-04", proc="P6", name="收入/销量/单价等预测依据不充分",
         kw=["收入增长率", "预测收入", "销售收入", "销量", "销售单价", "增长率", "营业收入预测",
             "预测现金流量", "收入分成", "入住率", "产能"],
         covered_by=["Q-DCF-005", "Q-DCF-006"], gap=False),
    dict(id="T-VA-05", proc="P6", name="重置成本、成新率、造价等成本法取值不合理",
         kw=["成新率", "重置成本", "重置全价", "造价", "建安", "前期费用", "贬值", "倍加系数"],
         covered_by=["Q-NF-001", "Q-NF-006"], gap=True),
    dict(id="T-VA-06", proc="P6", name="可比公司/交易案例不具可比性或选取过程未披露",
         kw=["可比公司", "可比企业", "交易案例", "可比案例", "比准", "修正系数",
             "选取标准和选取过程", "参照物"],
         covered_by=["Q-MK-003", "Q-MK-004", "Q-MK-005", "Q-MK-006"], gap=True),
    dict(id="T-VA-08", proc="P6", name="减值测试、非经营性资产负债、营运资金等要素处理错误",
         kw=["可收回金额", "商誉", "减值", "资产组", "营运资金", "资本性支出", "折旧摊销",
             "公允价值减处置费用", "非经营性资产", "非经营性", "溢余资产", "递延收益"],
         covered_by=["Q-FG-011", "Q-FG-012", "Q-DCF-012"], gap=True),
    # --- P7 编制出具报告 ---
    dict(id="T-RP-02", proc="P7", name="报告/说明/明细表与工作底稿不一致",
         kw=["与底稿不一致", "与工作底稿不一致", "与评估报告不一致", "现场调查资料与评估报告不一致",
             "申报表与评估报告不一致", "与明细表不一致", "此数据与明细表不一致"],
         covered_by=["Q-AR-018"], gap=True),
    dict(id="T-RP-04", proc="P7", name="评估假设无依据、不合理或披露不齐",
         kw=["评估假设", "假设无", "假设不合理", "前提假设", "假设披露"],
         covered_by=[], gap=True),
    dict(id="T-RP-05", proc="P7", name="特别事项、期后事项、权属瑕疵等披露不到位",
         kw=["特别事项", "期后事项", "期后发生", "重大事项披露", "披露不到位", "披露错误",
             "未完整披露", "信息披露不准确", "披露信息不清晰", "未披露"],
         covered_by=["Q-FG-010", "Q-RE-011"], gap=True),
    dict(id="T-RP-06", proc="P7", name="评估结论有效期、报告日、签署要素不合规",
         kw=["有效期", "报告日", "缺少签字盖章", "未规范披露评估结果"],
         covered_by=["Q-RE-007", "Q-RE-012"], gap=True),
    dict(id="T-RP-01", proc="P7", name="报告评估依据缺失或引用准则错误",
         kw=["评估依据部分", "引用的准则依据", "关键准则依据", "依据错误混乱", "评估依据引用",
             "缺少重要内容", "缺项严重", "规范要求撰写评估报告", "内容规范性和一致性欠缺",
             "缺少资产评估师签名"],
         covered_by=["Q-RE-011"], gap=True),
    dict(id="T-RP-03", proc="P7", name="报告附件缺失（承诺函、备案证明、执照、资格登记卡）",
         kw=["承诺函", "备案证明", "营业执照", "职业资格", "登记卡", "附件中缺少"],
         covered_by=["Q-RE-013", "Q-RE-017", "Q-RE-021"], gap=False),
    dict(id="T-RP-07", proc="P7", name="国有资产/司法/征收等特殊类别报告要求未执行",
         kw=["企业国有资产评估报告指南", "经济行为文件", "核准", "备案表", "司法执行财产处置",
             "房屋征收", "拆迁补偿", "矿产资源", "森林资源", "林木", "生物资产"],
         covered_by=["Q-RE-014", "Q-RE-022"], gap=True),
    # --- P8 整理归集档案 ---
    dict(id="T-AR-04", proc="P8", name="三级复核/内部审核流于形式、无实质内容",
         kw=["三级复核", "三级审核", "内部审核", "内部复核", "流于形式", "无实质性内容",
             "复核不到位", "审核表", "报告签发表", "修改回复", "复核意见"],
         covered_by=["Q-MG-008", "Q-SR-007", "Q-AR-001"], gap=True),
    dict(id="T-AR-01", proc="P8", name="无归档目录、未注明文档介质形式或归档时间",
         kw=["归档目录", "介质形式", "归档时间", "档案目录", "底稿目录", "档案编号", "保管年限", "档案盒"],
         covered_by=[], gap=True),
    dict(id="T-AR-03", proc="P8", name="初步评估报告未归档、正式报告/底稿未装订成册",
         kw=["初步评估报告", "初步资产评估报告", "单独装订", "未装订", "装订成册", "散装放置"],
         covered_by=[], gap=True),
    dict(id="T-AR-02", proc="P8", name="未建立索引号或索引未反映底稿间勾稽关系",
         kw=["索引号", "索引未能反映", "勾稽关系", "未建立必要的索引"],
         covered_by=["Q-SR-008", "Q-AR-020", "Q-FG-002"], gap=False),
    dict(id="T-AR-05", proc="P8", name="底稿归档不完整或未按规定归档",
         kw=["未按时归档", "归档不全", "未归档", "归档资料", "档案管理缺失", "未按照规定进行档案管理"],
         covered_by=["Q-AR-015", "Q-AR-001"], gap=False),
    # --- P5 收集整理资料 ---
    dict(id="T-DC-01", proc="P5", name="申报表/《企业关于进行资产评估有关事项的说明》缺失",
         kw=["申报表", "有关事项的说明", "申报明细表", "申报评估", "情况说明资料"],
         covered_by=["Q-AR-002", "Q-AR-021", "Q-CZ-005"], gap=False),
    dict(id="T-DC-02", proc="P5", name="权属证明资料缺失",
         kw=["权属证明", "权属依据", "权证", "产权证明", "不动产权证", "所有权手续", "权属资料",
             "股权证明", "协议、章程", "机动车辆登记证"],
         covered_by=["Q-NF-002", "Q-RE-016", "Q-AR-003", "Q-CZ-007"], gap=False),
    dict(id="T-DC-03", proc="P5", name="市场询价/市场调查记录缺失",
         kw=["询价", "市场调查", "市场询价", "挂牌价", "查询记录", "取价来源", "市场价格", "定价依据"],
         covered_by=["Q-NF-009", "Q-AR-005", "Q-AR-017", "Q-FF-007"], gap=False),
    dict(id="T-DC-04", proc="P5", name="历史财务数据、行业数据等基础资料收集不完备",
         kw=["历史数据", "行业数据", "收集不完备", "财务资料", "无相关财务资料", "数据资料",
             "历史沿革", "经营管理结构", "产权架构", "经营计划", "发展规划", "收益预测等资料"],
         covered_by=["Q-CZ-001", "Q-DCF-002"], gap=True),
    dict(id="T-DC-06", proc="P5", name="负债类及账外资产负债识别、核实底稿缺失",
         kw=["负债类", "表外", "各项资产、负债", "应付", "其他应付款", "借款", "递延", "账外"],
         covered_by=["Q-CZ-001"], gap=True),
    dict(id="T-DC-05", proc="P5", name="访谈/询问记录缺失",
         kw=["访谈", "询问记录", "管理层", "洽谈", "会计调查表", "出纳员声明书"],
         covered_by=["Q-AR-007", "Q-AR-017", "Q-DCF-007"], gap=False),
    # --- P4 现场调查 ---
    dict(id="T-FI-02", proc="P4", name="盘点/监盘程序缺失或盘点表未签字盖章",
         kw=["盘点", "监盘", "清点", "盘点表"],
         covered_by=["Q-FF-001", "Q-FF-008"], gap=False),
    dict(id="T-FI-03", proc="P4", name="未对使用资料核查验证（函证、核对原件不到位）",
         kw=["核查验证", "核查、验证", "原件", "复印件与原件", "未核对", "函证"],
         covered_by=["Q-SR-010", "Q-SR-011", "Q-NF-002", "Q-FG-004"], gap=False),
    dict(id="T-FI-01", proc="P4", name="现场调查/实地勘察记录缺失或不完整",
         kw=["现场调查", "实地勘察", "勘查", "勘察", "调查记录", "现状和使用状况", "清查",
             "现场勘察表"],
         covered_by=["Q-NF-003", "Q-AR-019", "Q-NF-008"], gap=False),
    # --- P3 计划 / P2 合同 / P1 基本事项 ---
    dict(id="T-PL-01", proc="P3", name="评估计划缺失、流于形式或无针对性技术方案",
         kw=["评估计划", "工作计划", "技术方案", "时间进度及人员安排"],
         covered_by=["Q-MG-007", "Q-AR-016", "Q-AR-025"], gap=False),
    dict(id="T-CT-01", proc="P2", name="委托合同/业务约定书缺失、未签章或订立不规范",
         kw=["委托合同", "业务约定书", "约定书", "委托协议", "合同订立"],
         covered_by=["Q-MG-001", "Q-AR-012", "Q-RE-019"], gap=False),
    dict(id="T-BM-02", proc="P1", name="专业能力/独立性/风险分析评价记录缺失",
         kw=["专业能力", "专业胜任能力", "独立性", "风险分析", "风险评价", "业务承接",
             "综合分析", "利用专家工作"],
         covered_by=["Q-MG-003", "Q-MG-006"], gap=False),
    dict(id="T-BM-01", proc="P1", name="业务基本事项要素不全或与实际经济行为不一致",
         kw=["基本事项", "价值类型", "报告使用人", "使用范围", "评估收费", "支付方式",
             "经济行为", "评估目的", "评估对象和评估范围", "追溯评估"],
         covered_by=["Q-MG-002", "Q-CZ-004"], gap=False),
]
THEME_BY_ID = {t["id"]: t for t in THEMES}


def match_themes(text):
    return [t["id"] for t in THEMES if any(k in text for k in t["kw"])]


def assign_primary(ids, proc_raw):
    """主主题：优先取与本条源表问题类型同程序的命中主题，否则取词典顺序首个。"""
    pid = PROC_ALIAS.get(proc_raw)
    if pid:
        for tid in ids:
            if THEME_BY_ID[tid]["proc"] == pid:
                return tid
    return ids[0] if ids else None


# ---------------------------------------------------------------- 读取
def read_facts():
    wb = openpyxl.load_workbook(SRC, data_only=True, read_only=True)
    ws = wb[SHEET]
    rows = list(ws.iter_rows(min_row=1, values_only=True))
    hdr = list(rows[0])
    out, seen = [], set()
    for r in rows[1:]:
        if not any(v not in (None, "") for v in r):
            continue
        d = dict(zip(hdr, r))
        doc_seq = d.get("对应处罚文件序号")
        report_no = d.get("评估报告号")
        for i in range(1, 9):
            t = d.get(f"问题类型{i}")
            f = d.get(f"问题事实{i}")
            if f in (None, "") and t in (None, ""):
                continue
            fact = str(f or "").strip()
            # 同一处罚文件常把同一段事实复用到多份报告行（批量案），
            # 按「处罚文件序号+事实文本」去重，频次反映问题种类而非报告份数
            key = (doc_seq, re.sub(r"\s+", "", fact)[:120])
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(
                doc_seq=doc_seq,
                report_no=report_no,
                prov=(str(d.get("监管省份")).strip() if d.get("监管省份") else ""),
                biz=(str(d.get("评估业务分类2")).strip() if d.get("评估业务分类2") else ""),
                proc_raw=(str(t).strip() if t else ""),
                fact=fact,
            ))
    return out


RE_STANDARD = re.compile(r"《([^》]{2,45}(?:准则|指南|办法|意见|规定)[^》]{0,10})》(第[一二三四五六七八九十百\d]+条)?")


def main():
    if not os.path.exists(SRC):
        sys.exit(f"未找到源文件：{SRC}")
    uniq = read_facts()  # 读取时已按「处罚文件序号+事实文本」去重
    collect_aliases(f["fact"] for f in uniq)  # 全量收集「以下简称」别名，再逐条脱敏

    # 主题归类
    theme_hits = collections.defaultdict(list)
    unclassified = []
    std_count = collections.Counter()
    for f in uniq:
        for m in RE_STANDARD.finditer(f["fact"]):
            std_count[m.group(1) + (m.group(2) or "")] += 1
        ids = match_themes(f["fact"])
        if not ids:
            unclassified.append(f)
            continue
        primary = assign_primary(ids, f["proc_raw"])
        f["themes"] = ids
        f["primary"] = primary
        for tid in ids:
            theme_hits[tid].append(f)

    # 现有问题集 id -> 组
    qb = yaml.safe_load(open(QBANK, encoding="utf-8"))
    q_group = {}
    for g in qb["groups"]:
        for q in g["questions"]:
            q_group[q["id"]] = g["id"]
    # 主题 -> 本轮为覆盖该缺口新增的问题集条目（见 questions/底稿问题集.yaml）
    ADDED_BY = {
        "T-VA-01": ["Q-SB-001"],
        "T-VA-02": ["Q-SB-002"],
        "T-VA-07": ["Q-SB-003"],
        "T-VA-09": ["Q-SB-004"],
        "T-VA-05": ["Q-SB-006"],
        "T-VA-06": ["Q-MK-011", "Q-MK-012"],
        "T-VA-08": ["Q-SB-007", "Q-DCF-018", "Q-DCF-019"],
        "T-VA-03": ["Q-DCF-015"],
        "T-VA-04": ["Q-DCF-016"],
        "T-RP-02": ["Q-SB-005"],
        "T-RP-01": ["Q-RE-026"],
        "T-RP-04": ["Q-RE-027"],
        "T-RP-05": ["Q-RE-028"],
        "T-RP-06": ["Q-RE-029"],
        "T-RP-07": ["Q-RE-030"],
        "T-AR-01": ["Q-AR-030", "Q-AR-031", "Q-AR-032"],
        "T-AR-03": ["Q-AR-028", "Q-AR-029"],
        "T-AR-04": ["Q-MG-008", "Q-MG-009"],
        "T-WP-01": ["Q-AR-033"],
        "T-DC-04": ["Q-CZ-022"],
        "T-DC-06": ["Q-FF-014"],
    }
    ADDED_BY = {k: [i for i in v if i in q_group] for k, v in ADDED_BY.items()}
    ADDED_BY = {k: v for k, v in ADDED_BY.items() if v}

    prov_count = collections.Counter(f["prov"] for f in uniq if f["prov"])
    biz_count = collections.Counter(f["biz"] for f in uniq if f["biz"])
    proc_count = collections.Counter(f["proc_raw"] or "（未标注）" for f in uniq)

    doc = {}
    doc["version"] = 1
    doc["title"] = "2024年处罚监管问题映射（底稿复核视角）"
    doc["purpose"] = (
        "把 2024 年监管处罚/自律惩戒中的问题事实，按八大基本程序与主题聚类，"
        "映射到 questions/底稿问题集.yaml，标出覆盖缺口与建议新增条目，"
        "为问题集提供「监管实际处罚」这一负向清单依据。"
    )
    doc["source"] = {
        "file": "华信电子底稿编制指引（征求意见稿）/20251112 2024年处罚监管数据 (保密）.xlsx",
        "sheet": SHEET,
        "confidential": ("源文件保密，已加入 .gitignore 不入库；本文件内容已脱敏"
                         "（评估机构名、企业与委托方名称含简称、人名、登记编号、报告号/处罚文号均抹去，"
                         "保留金额、比例与准则条款引用）"),
        "extracted_by": "scripts/extract-penalty-issues.py",
    }
    doc["scope"] = {
        "reports": len({f["report_no"] for f in uniq if f["report_no"]}),
        "penalty_docs": len({f["doc_seq"] for f in uniq if f["doc_seq"]}),
        "facts_dedup": len(uniq),
        "note": ("事实条目按「处罚文件序号+事实文本」去重：批量案中同一段事实被复用到多份报告行时只计一次，"
                 "频次反映问题种类而非报告份数。源表备注已说明部分处罚文件仅列前 2 项问题事实，故本表非全量"),
    }
    doc["summary"] = {
        "procedures": len(PROCEDURES),
        "themes": len(THEMES),
        "themes_gap": sum(1 for t in THEMES if t.get("gap")),
        "facts_classified": len(uniq) - len(unclassified),
        "facts_unclassified": len(unclassified),
        "facts_with_standard_citation": sum(1 for f in uniq if RE_STANDARD.search(f["fact"])),
    }

    # 程序级统计
    plist = []
    for pid, pname in PROCEDURES:
        n_theme = sum(1 for f in uniq if f.get("primary") and THEME_BY_ID[f["primary"]]["proc"] == pid)
        plist.append({
            "id": pid,
            "name": pname,
            "count_by_source_type": sum(v for k, v in proc_count.items() if PROC_ALIAS.get(k) == pid),
            "count_primary_theme": n_theme,
            "themes": [t["id"] for t in THEMES if t["proc"] == pid],
        })
    n_px = sum(1 for f in uniq if f.get("primary") and THEME_BY_ID[f["primary"]]["proc"] is None)
    plist.append({
        "id": "PX",
        "name": "跨程序/合规红线/非底稿事项",
        "count_by_source_type": proc_count.get("（未标注）", 0),
        "count_primary_theme": n_px,
        "themes": [t["id"] for t in THEMES if t["proc"] is None],
    })
    doc["procedures"] = plist

    doc["distribution"] = {
        "by_regulator": [{"name": k, "count": v} for k, v in prov_count.most_common()],
        "by_business_type": [{"name": k, "count": v} for k, v in biz_count.most_common()],
    }

    doc["standards_cited_top"] = [
        {"name": k, "count": v} for k, v in std_count.most_common(15)
    ]

    # 主题明细
    tlist = []
    for t in THEMES:
        fs = theme_hits.get(t["id"], [])
        primary_n = sum(1 for f in fs if f.get("primary") == t["id"])
        seen_head, examples = set(), []
        for f in sorted(fs, key=lambda x: (x.get("primary") != t["id"], x["prov"], len(x["fact"]))):
            clean = desensitize(f["fact"])
            head = re.sub(r"[^\u4e00-\u9fa5]", "", clean)[:24]
            if not head or head in seen_head:
                continue
            seen_head.add(head)
            examples.append(clip(clean))
            if len(examples) >= 3:
                break
        ent = {
            "id": t["id"],
            "name": t["name"],
            "procedure": t["proc"] or "跨程序/红线",
            "hits": len(fs),
            "primary_hits": primary_n,
            "share": round(len(fs) / max(len(uniq), 1) * 100, 1),
            "covered_by": t["covered_by"],
            "covered_groups": sorted({q_group[q] for q in t["covered_by"] if q in q_group}),
            "gap": bool(t.get("gap")),
        }
        if ADDED_BY.get(t["id"]):
            ent["added_by"] = ADDED_BY[t["id"]]
        if t.get("redline"):
            ent["redline"] = True
        if t.get("scope_out"):
            ent["scope_out"] = True
            ent["scope_note"] = t["scope_note"]
        if examples:
            ent["examples"] = examples
        tlist.append(ent)
    tlist.sort(key=lambda e: -e["hits"])
    doc["themes"] = tlist

    if unclassified:
        samp, seen_head = [], set()
        for f in sorted(unclassified, key=lambda x: -len(x["fact"])):
            clean = desensitize(f["fact"])
            head = re.sub(r"[^\u4e00-\u9fa5]", "", clean)[:20]
            if head in seen_head:
                continue
            seen_head.add(head)
            samp.append(clip(clean, 120))
            if len(samp) >= 10:
                break
        doc["unclassified_samples"] = samp

    doc["how_to_use"] = [
        "gap=True 的主题是现有问题集的缺口，对应新增条目已并入 questions/底稿问题集.yaml（substance 组及各组扩充项）",
        "redline=True 的主题属违法线索（冒签、伪造、未实际参与），应作合规红线单独管理，不作常规勾选项",
        "scope_out=True 的主题不在底稿复核范围内，仅保留计数以说明数据口径",
        "covered_by 列出扩充前即可拦截该问题的现有条目 id；added_by 列出本轮为覆盖该缺口新增到 questions/底稿问题集.yaml 的条目 id",
        "hits/share 为监管处罚频次（一条事实可命中多个主题），primary_hits 为按源表问题类型锚定后的主主题计数，可作复核条目的风险权重",
        "standards_cited_top 为处罚决定高频引用的准则条款，可补进问题条目的 check 字段",
    ]

    with open(OUT, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100)
    print(f"write  {os.path.relpath(OUT, REPO)}")
    print(f"  事实条目（去重后）{len(uniq)}，已归类 {len(uniq) - len(unclassified)}，未归类 {len(unclassified)}")
    print(f"  主题 {len(THEMES)} 个，其中缺口 {sum(1 for t in THEMES if t.get('gap'))} 个")
    print("  TOP10 主题（hits/primary）：")
    for e in tlist[:10]:
        print(f"    [{e['hits']:>4}/{e['primary_hits']:>4}] {e['id']} {e['name']}{'  ← 缺口' if e['gap'] else ''}")


if __name__ == "__main__":
    main()
