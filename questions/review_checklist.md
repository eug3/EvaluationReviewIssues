# 准则追问问题集（参考）

> 早期按准则视角整理的「报告命题 -> 底稿证据」追问集；当前主问题集是 questions/底稿问题集.md。
>
> 机器可读版 questions/review_checklist.yaml。

## object_scope 评估对象与范围（claim_type: object_scope）

- [ ] **Q-OBJ-001** 报告对评估对象与评估范围的界定，在底稿（评估说明/评估明细表）中是否有与之一致的表述？
      - 期望证据：评估说明的评估对象章节、评估明细表的资产/负债清单
      - 判定规则：两侧的对象名称、资产类型、数量必须一致；底稿只出现同类但不同对象不算支撑
      - 缺失判定：missing（severity: high）
      - 依据：资产评估执业准则——资产评估程序
- [ ] **Q-OBJ-002** 报告中申报的账面未记录资产/表外资产，底稿中是否有对应的申报表或核查记录？
      - 期望证据：表外资产申报表、权属或核查记录
      - 判定规则：报告列示的表外资产必须在底稿中有逐项对应；底稿未提及即为无对应
      - 缺失判定：missing（severity: medium）
- [ ] **Q-OBJ-003** 评估范围内的资产/负债构成与数量，能否在底稿明细表中逐一对应？
      - 期望证据：资产评估明细表
      - 判定规则：按资产类型逐类核对数量与金额；不一致记 contradicted，缺项记 missing
      - 缺失判定：missing（severity: high）

## value_type 价值类型（claim_type: value_type）

- [ ] **Q-VAL-001** 报告选取价值类型「{{claim.text}}」的依据（经济行为、报告使用人、市场条件），底稿中是否有对应说明？
      - 期望证据：评估说明中价值类型的选择理由
      - 判定规则：需有与经济行为相匹配的选择理由；只重复价值类型名称不算支撑
      - 缺失判定：insufficient（severity: medium）
      - 依据：资产评估准则术语
- [ ] **Q-VAL-002** 价值类型的定义与本次经济行为是否匹配，底稿是否引用了对应准则？
      - 期望证据：价值类型定义引用与适用分析
      - 判定规则：定义与准则一致且与评估目的匹配；不匹配记 contradicted
      - 缺失判定：missing（severity: medium）

## base_date 评估基准日（claim_type: base_date）

- [ ] **Q-BAS-001** 报告的评估基准日「{{claim.text}}」与报告摘要、评估说明、汇总表是否一致？
      - 期望证据：报告摘要、说明结论、汇总表
      - 判定规则：任一文档基准日不一致即 contradicted；缺失一侧记 missing
      - 缺失判定：missing（severity: high）
- [ ] **Q-BAS-002** 评估基准日的选取理由及基准日后重大事项的处理，底稿中是否有说明？
      - 期望证据：基准日选择说明、期后事项说明
      - 判定规则：需有明确说明；报告提及但底稿无内容记 missing
      - 缺失判定：missing（severity: medium）
- [ ] **Q-BAS-003** 底稿所引用的财务数据、市场价格数据的截止日是否与评估基准日一致？
      - 期望证据：财务报表、市场数据来源与截止日
      - 判定规则：数据截止日与基准日不一致且未调整记 contradicted；未注明记 insufficient
      - 缺失判定：insufficient（severity: high）

## purpose 评估目的与委托人（claim_type: purpose）

- [ ] **Q-PUR-001** 报告所述评估目的对应的经济行为文件（受让协议/决议/批复），底稿中是否有对应依据？
      - 期望证据：经济行为文件、委托人提供的资料清单
      - 判定规则：需定位到具体文件；底稿无记录记 missing
      - 缺失判定：missing（severity: medium）
- [ ] **Q-PUR-002** 报告列示的委托人、被评估单位与报告使用人，与底稿记载是否一致？
      - 期望证据：营业执照、委托合同、承诺函
      - 判定规则：名称必须逐字一致；不一致记 contradicted
      - 缺失判定：missing（severity: medium）

## method 评估方法与适用性（claim_type: method）

- [ ] **Q-MET-001** 报告采用「{{claim.text}}」，底稿中是否说明了该方法适用性判断过程与不采用其他方法的理由？
      - 期望证据：评估说明的方法选择与适用性分析章节
      - 判定规则：需有适用性分析（收益可预测性/可比案例/资料完整性）；只罗列方法名称记 insufficient
      - 缺失判定：insufficient（severity: high）
      - 依据：资产评估执业准则——资产评估方法
- [ ] **Q-MET-002** 报告判定不适用或未采用的方法，底稿中是否有支撑该判断的依据？
      - 期望证据：不适用的理由说明
      - 判定规则：需给出具体理由；无理由记 missing
      - 缺失判定：missing（severity: medium）
- [ ] **Q-MET-003** 所选评估方法要求的前提条件（持续经营、可预测收益、可比案例充分性等），底稿中是否有对应支撑？
      - 期望证据：方法前提的核实记录
      - 判定规则：前提未落实记 contradicted；未说明记 missing
      - 缺失判定：missing（severity: high）

## parameter 评估参数（claim_type: parameter）

- [ ] **Q-PAR-001** 报告中参数取值「{{claim.text}}」的测算过程、取值区间与数据来源，底稿中是否有对应？
      - 期望证据：参数取值表、测算过程、来源数据（市场数据/可比公司）
      - 判定规则：必须定位到具体测算或来源；只重复报告数值记 insufficient
      - 缺失判定：missing（severity: high）
      - 依据：资产评估专家指引第 12 号（收益法评估企业价值中折现率的测算）
- [ ] **Q-PAR-002** 参数取值与市场/行业可比数据是否具有可比性，底稿中是否有对比分析？
      - 期望证据：可比公司/可比案例数据与对比分析
      - 判定规则：需有可比性分析；数值明显偏离且无说明记 contradicted
      - 缺失判定：insufficient（severity: medium）
- [ ] **Q-PAR-003** 各参数之间的口径是否一致（税前/税后、名义/实际、母公司/合并、元/万元）？
      - 期望证据：参数口径说明与计算表
      - 判定规则：口径混用记 contradicted；未注明记 insufficient
      - 缺失判定：insufficient（severity: high）

## calculation 计算过程与公式（claim_type: calculation）

- [ ] **Q-CAL-001** 报告披露的计算过程/公式，底稿中是否有对应计算表且结果可复算？
      - 期望证据：计算表（含公式）、复算结果
      - 判定规则：复算结果一致记 supported；不一致记 contradicted；无计算表记 missing
      - 缺失判定：missing（severity: high）
- [ ] **Q-CAL-002** 底稿计算口径与报告披露口径是否一致？
      - 期望证据：计算口径说明
      - 判定规则：口径不一致记 contradicted
      - 缺失判定：insufficient（severity: medium）
- [ ] **Q-CAL-003** 底稿计算表中引用的参数与报告正文披露的参数是否一致？
      - 期望证据：计算表中的参数单元格、报告正文参数
      - 判定规则：逐参数比对；不一致记 contradicted
      - 缺失判定：missing（severity: high）

## conclusion 评估结论与金额（claim_type: conclusion）

- [ ] **Q-CON-001** 报告结论金额「{{claim.value}} {{claim.unit}}」在底稿（评估说明/评估汇总表/明细表）中是否有对应且金额一致？
      - 期望证据：评估说明结论、评估汇总表、明细表合计
      - 判定规则：换算到同一单位后比对；差异超过 0.01 记 contradicted；无对应记 missing
      - 缺失判定：missing（severity: high）
- [ ] **Q-CON-002** 报告结论金额的小写与大写是否一致？
      - 期望证据：报告结论章节
      - 判定规则：大小写不一致记 contradicted
      - 缺失判定：insufficient（severity: high）
- [ ] **Q-CON-003** 报告结论与报告摘要、评估说明结论在金额、币种、单位、评估对象上是否一致？
      - 期望证据：报告摘要、报告结论、说明结论
      - 判定规则：任一关键字段冲突记 contradicted；缺失一侧记 missing
      - 缺失判定：missing（severity: high）
- [ ] **Q-CON-004** 报告披露的增减值、增值率能否由底稿的账面值与评估值复算得出？
      - 期望证据：账面价值、评估价值、增减值表
      - 判定规则：复算一致记 supported；不一致记 contradicted；数据缺失记 missing
      - 缺失判定：missing（severity: high）

## change_analysis 评估值与账面值变动分析（claim_type: change_analysis）

- [ ] **Q-CHG-001** 报告对评估值与账面值变动的分析，底稿中是否有量化依据？
      - 期望证据：账面值/评估值对比表、变动原因说明
      - 判定规则：有量化依据记 supported；仅定性描述记 insufficient；无依据记 missing
      - 缺失判定：missing（severity: medium）
- [ ] **Q-CHG-002** 报告所述重大增值/减值科目，在底稿明细表中是否有对应科目与金额？
      - 期望证据：评估明细表对应科目
      - 判定规则：科目或金额不一致记 contradicted；无对应科目记 missing
      - 缺失判定：missing（severity: medium）

## assumption 评估假设与前提（claim_type: assumption）

- [ ] **Q-ASM-001** 报告假设「{{claim.text}}」在底稿中是否有对应前提说明或核实记录？
      - 期望证据：评估假设章节、核实记录
      - 判定规则：假设未落实或无核实记 missing；与事实冲突记 contradicted
      - 缺失判定：missing（severity: medium）
- [ ] **Q-ASM-002** 报告假设与所选评估方法、参数取值是否相互匹配？
      - 期望证据：假设与方法/参数的对应说明
      - 判定规则：假设与方法前提冲突记 contradicted
      - 缺失判定：insufficient（severity: medium）

## limitation 限制条件与特别事项（claim_type: limitation）

- [ ] **Q-LIM-001** 报告特别事项说明中提到的权属瑕疵/限制/未决事项，底稿中是否有对应记录或替代程序？
      - 期望证据：权属资料、法律意见、替代程序记录
      - 判定规则：无对应记录记 missing；记录与报告矛盾记 contradicted
      - 缺失判定：missing（severity: high）
- [ ] **Q-LIM-002** 报告的使用限制说明是否与评估目的、经济行为匹配？
      - 期望证据：评估目的章节、限制条件章节
      - 判定规则：不匹配记 contradicted
      - 缺失判定：insufficient（severity: low）

## disclosure 披露一致性（claim_type: disclosure）

- [ ] **Q-DIS-001** 报告摘要、报告结论、说明结论在评估对象/基准日/价值类型/金额/币种单位/方法/限制条件上是否一致？
      - 期望证据：报告摘要、报告结论、说明结论三处原文
      - 判定规则：逐字段比对；任一冲突记 contradicted；缺一处原文记 insufficient
      - 缺失判定：insufficient（severity: high）
- [ ] **Q-DIS-002** 报告正文披露的关键字段，是否都能在评估说明中找到对应披露？
      - 期望证据：评估说明对应章节
      - 判定规则：报告有说明无 = 说明缺要素，记 missing
      - 缺失判定：missing（severity: medium）
- [ ] **Q-DIS-003** 仅在报告或仅在说明出现的结论性表述，是否有独立依据？
      - 期望证据：依据文件或说明
      - 判定规则：无依据记 missing
      - 缺失判定：missing（severity: medium）

## legal_basis 评估依据与权属（claim_type: legal_basis）

- [ ] **Q-LEG-001** 报告引用的权属资料、经济行为文件，底稿中是否有对应原件或复印件？
      - 期望证据：权属证书、合同、决议、批复
      - 判定规则：逐项核对；缺失记 missing
      - 缺失判定：missing（severity: high）
- [ ] **Q-LEG-002** 报告引用的评估依据（准则/法规）是否现行有效，版本是否正确？
      - 期望证据：准则/法规名称与文号
      - 判定规则：引用已废止版本记 contradicted；无引用记 insufficient
      - 缺失判定：insufficient（severity: low）
      - 依据：评估法及准则数据集
