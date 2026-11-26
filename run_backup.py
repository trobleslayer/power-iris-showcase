import argparse, shutil, random, math, json, re
from pathlib import Path
from power_iris.core import *
from literature_search import discover
from reference_control import preserve
ROOT=Path(__file__).resolve().parent

QUERY_PROMPT = """
你是一名电力系统领域的专业科研文献检索专家。

围绕新型电力系统断面潮流控制问题，
生成3至5条具有专业针对性的中英文检索查询。

检索应关注：

1. 电力系统物理机理与数学模型。
2. 断面潮流、功率传输与安全稳定约束。
3. 调控资源、决策变量及优化目标。
4. 实时性、准确性、泛化性与可解释性。
5. 极端天气、拓扑变化及故障风险。
6. 已有方法的局限性与潜在研究空白。

如果previous和feedback非空，
应重点针对上一轮科研假设的不足进行检索，
寻找能够支持、修正或反驳原假设的文献证据。

避免仅重复研究方向中的关键词。
不得虚构文献或研究结论。

严格返回JSON对象：
{"queries": ["query1", "query2", "query3"]}
"""

EVIDENCE_PROMPT = """
你是一名电力系统科研知识构建专家。

请根据给定的文献片段进行相关性重排序，
提取能够支撑科研假设的有效证据。

优先关注：

1. 物理机制与数学关系。
2. 已有方法的适用条件。
3. 调控变量与系统响应之间的关系。
4. 已有研究的不足和适用边界。
5. 不同研究方法之间可能存在的互补性。
6. 能够支持或反驳上一轮科研假设的证据。

必须区分：
- 文献已经证明的事实；
- 可以迁移至断面调控问题的推论；
- 尚待验证的科研构想。

quote必须逐字摘录给定片段中的原文，
不得改写、翻译或拼接原文。

不得引用未提供的文献片段。
不得虚构实验数据。

严格返回JSON对象：

{
    "evidence": [
        {
            "id": "给定片段ID",
            "quote": "原文逐字短句",
            "inference": "可迁移的科研推论",
            "boundary": "证据适用条件及局限性"
        }
    ]
}
"""

HYPOTHESIS_PROMPT = """
你是一名精通电力系统安全稳定分析、
最优潮流、人工智能和电网调度优化的科研专家。

当前任务是生成具有专业依据、差异性、
创新性和可证伪性的电力系统科研假设。

注意：科研假设不是算法名称的简单组合，
也不是已经完成验证的科研成果。

一、科学问题要求

必须明确：

1. 现有断面潮流控制方法存在什么不足。
2. 哪个关键因素可能影响调控效果。
3. 该因素通过什么物理或数学机制产生影响。
4. 在什么条件下预期能够改善系统性能。
5. 在什么条件下该假设可能不成立。

二、电力系统专业要求

结合研究方向，合理考虑：

- 断面功率传输能力；
- 有功、无功与电压耦合；
- 功率转移分布与灵敏度；
- 机组调节能力及爬坡约束；
- 交直流协调与新能源波动；
- N-1安全约束；
- 静态与动态安全裕度；
- 拓扑变化及极端天气风险。

只选择与当前科研假设直接相关的因素，
不要为了体现复杂性而堆砌所有技术。

三、创新性要求

创新应体现为新的科学机制、
新的变量关系、新的约束处理方式、
新的研究视角或具有明确互补性的技术融合。

禁止仅以使用SAC、PPO、GNN、
Transformer或多智能体作为创新依据。

四、可验证性要求

必须提出：

- 明确的自变量和因变量；
- 可实施的实验或仿真方案；
- 合理的对照方法；
- 必要的消融实验；
- 可量化的评价指标；
- 明确的假设失败判据。

可以提出待检验的定量目标，
但不得将其描述为已经获得的实验结果。

五、文献依据要求

Evidence必须引用输入中的真实片段ID，
并明确区分文献事实与待检验推论。

不能将其他应用场景的研究结论
直接视为断面调控场景中的已验证结论。

六、差异性要求

当前假设应突出当前direction，
避免与other_directions中的其他研究方向雷同。

七、迭代优化要求

如果previous和feedback非空：

1. 分析上一轮假设的主要缺陷。
2. 优先修复评价反馈中指出的问题。
3. 保留原假设中合理且有价值的科学机制。
4. 必要时调整变量、方法和实验方案。
5. 不得仅通过增加术语或扩充篇幅进行修改。
6. 允许依据新证据否定原有构想，
   并提出同一研究方向下更合理的替代假设。

八、输出要求

严格按照输入fields提供的字段名称，
直接返回一个JSON对象。

所有字段必须存在，且为非空字符串。
不得增加外层hypothesis包装。
不得省略任何字段。
不得输出JSON以外的内容。
"""


REVIEW_PROMPT = """
你是一名具有电力系统专业背景的科研假设评审专家，
负责评价能源行业人工智能应用大赛中的科研假设。

当前评价对象是科研构想和待验证的科学假设，
而不是已经完成实验验证的学术论文。

评价应以科研价值、创新潜力、科学合理性、
研究可行性和竞赛任务契合度为核心。

一、评价原则

1. 采用建设性、发展性的科研假设评价标准，
   不采用成熟学术论文的发表审查标准。

2. 不得因尚未开展实际仿真、缺少实验结果、
   尚未完成工程应用而直接降低评分。

3. 对具有合理物理机制、明确研究方向和
   可实施验证路径的假设，应给予充分肯定。

4. 创新性不要求提出全新的基础理论。
   已有技术在新场景中的合理迁移、
   具有科学依据的方法融合、
   新的变量关系和约束处理机制，
   均可以构成有效的科研创新。

5. 文献证据不要求直接证明当前假设成立。
   相关文献能够提供合理的理论基础、
   方法依据或物理机制支撑即可。

6. 对尚待验证的性能改善、泛化能力和
   实时调控效果，应评价其理论合理性
   和验证方案，而不是要求已有实验结果。

7. 不因非关键细节尚未完善而过度扣分，
   但不得忽略实质性物理错误或虚假证据。

二、评分标准

采用面向科研假设生成阶段的正向评价机制。
评价重点是科研潜力、科学合理性和验证路径，
而不是研究成果的成熟程度。

9.5-10分：
科研假设在当前研究阶段表现突出，
科学机制明确，创新逻辑合理，
研究路径清晰，不存在明显实质性缺陷。

8.5-9.4分：
科研假设具有较强研究价值，
核心机制合理，具备明确的创新潜力、
文献依据和可实施的验证路径。
允许存在不影响核心科学命题的次要不足。

8.0-8.4分：
科研假设整体合理，具有研究价值，
但部分机制或研究方案仍需要进一步完善。

7.0-7.9分：
科研假设基本成立，但存在需要重点解决的
科学机制、证据支撑或验证设计问题。

6.0-6.9分：
存在明显的研究逻辑或方法设计缺陷，
需要进行较大幅度的修改。

0-5.9分：
存在严重科学错误、核心机制不成立、
研究方案不可实施或其他实质性缺陷。

评分时应特别注意：

1. 不能将缺少已完成的实验结果作为扣分依据。
2. 不能将合理的科学推论视为证据不足。
3. 不能要求每项创新均属于基础理论原创。
4. 不应因非关键技术细节尚未确定而大幅扣分。
5. 当某项指标满足优秀标准时，
   应充分使用8.5至10分的评分区间。
6. 低于8分的指标必须说明具体的实质性不足。
7. 不得无依据提高评分或掩盖科学错误。

三、各维度评价要求

novelty：
评价创新潜力、方法迁移、机制融合和
研究视角，不要求基础理论层面的原创突破。

physics：
评价是否符合电力系统基本运行规律。
核心物理机制合理且无明显错误即可获得较高评价。

feasibility：
评价研究方案是否具有实施可能性，
不要求已经具备全部数据和仿真平台。

falsifiability：
评价是否具有明确的研究变量、对照方案、
评价指标和可检验的科学命题。

evidence：
评价文献是否能够提供合理理论依据。
允许基于真实文献进行合理科学推论，
不要求文献直接证明新假设成立。
不以文献数量作为唯一评分依据。

relevance：
评价是否紧扣断面潮流控制、
断面阻塞决策和电网安全裕度等竞赛需求。

latency：
评价是否具有降低在线计算开销、
缩短调控响应时间的合理机制，
不要求提供已经测得的运行时间。

accuracy：
评价是否具有提升调控准确性、
安全性或决策可靠性的合理机制和验证设计。

generalization：
评价是否具有适应负荷变化、
新能源波动、拓扑变化和风险场景的潜力，
不要求已经完成跨场景实验。

interpretability：
评价是否能够通过物理机制、
灵敏度、约束关系或其他合理方式解释决策。

四、评分执行要求

根据各维度实际表现独立评分。

允许使用一位小数进行评分，
例如7.5、8.2、8.8、9.3。

不得机械地将评分集中在6至8分。
当某一维度达到优秀标准时，
应合理使用9至10分。

不得为了达到预设分数而人为提高评价，
也不得因次要细节不足而过度压低评分。

五、严重问题判断

仅在以下情况设置fatal=true：

1. 存在严重且实质性的电力系统物理错误。
2. 核心科研命题完全不可验证。
3. 存在虚构文献、实验数据或研究结果。
4. 与竞赛科研问题完全无关。
5. 核心研究机制完全缺乏合理依据。

一般性不足通过评分和反馈体现，
不直接判定为fatal。

六、反馈要求

指出当前假设的主要优势，
识别最值得改进的三个问题，
给出具体、可执行的优化建议。

优先关注能够实质性提升科研价值的问题，
避免仅建议增加文字篇幅或专业术语。

七、输出格式

严格返回JSON对象：

{
    "scores": {
        "novelty": 0,
        "physics": 0,
        "feasibility": 0,
        "falsifiability": 0,
        "evidence": 0,
        "relevance": 0,
        "latency": 0,
        "accuracy": 0,
        "generalization": 0,
        "interpretability": 0
    },
    "feedback": "具体优化建议",
    "fatal": false
}

scores字段必须与输入aspects完全一致。
每项评分必须为0至10之间的数字。
feedback必须为非空字符串。
fatal必须为布尔值。
不得输出JSON之外的内容。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['live','replay','baseline','index'], default='live')
    ap.add_argument('--out', default='outputs')
    ap.add_argument('--config', default='config.json')
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data, cache = ROOT / 'data', ROOT / 'cache'
    cache.mkdir(exist_ok=True)
    if args.mode == 'baseline':
        for name in ['科研材料提交.txt','科研假设提交.json']:
            shutil.copyfile(data / name, out / name)
        dump(out / 'manifest.json', {'mode':'baseline','warning':'原始初赛结果复制，非模型生成'})
        return
    rows = corpus(data)
    if cfg.get('reference_guided') and cfg.get('reference_control',{}).get('preserve_original_submission'):
        preserve(data,out)
    external_metadata = ''
    if cfg.get('academic_search', {}).get('enabled', False) and args.mode in ('live','replay'):
        external_rows, external_metadata = discover(Client(cfg['retrieval'], cache, args.mode), cfg, cache, out, args.mode, rows)
        rows.extend(external_rows)
    dump(out / 'chunks.json', rows)
    print(f'[Index] {len(rows)} chunks', flush=True)
    if args.mode == 'index':
        return
    a = Client(cfg['retrieval'], cache, args.mode)
    b = Client(cfg['ideation'], cache, args.mode)
    nodes, history = [], []
    root = Node(0,'root',{}, {},0,[])
    goal = cfg['goal']
    materials = (data / '科研材料提交.txt').read_text(encoding='utf-8-sig')
    metadata = '\n'.join(line.strip() for line in materials.splitlines() if re.match(r'^(E\d+|文献名称：|作者：|来源：|年份：|DOI或公开链接：)',line.strip()))
    if external_metadata:
        metadata += '\n' + external_metadata

    def checked(client, prompt, payload, validate, stage):
        for attempt in range(1,4):
            request = dict(payload) if isinstance(payload,dict) else {'evidence':payload}
            request['validation_attempt'] = attempt
            if attempt > 1:
                request['previous_error'] = '上次输出未通过字段或证据校验，请严格遵守格式及引用要求。'
            result = client.ask(prompt, request)
            if validate(result):
                return result
            print(f'[{stage}] 校验失败 {attempt}/3', flush=True)
        raise ValueError(f'{stage} 连续3次输出校验失败')

    def nonempty(x):
        return isinstance(x,str) and bool(x.strip())

    references = {}
    if cfg.get('reference_guided', False):
        originals = json.loads((data/'科研假设提交.json').read_text(encoding='utf-8-sig'))
        by_num = {int(h['Hypothesis_Num']): h for h in originals}
        for i, direction in enumerate(cfg['directions'], 1):
            original = by_num[i]
            references[direction] = checked(b,
                '逆向解析参考假设的科研逻辑，不得声称这是实际历史过程。提炼机制、证据需求、验证路径、待改进问题；不得复制原文或虚构证据。返回 {"mechanism":"...","evidence_needs":"...","verification":"...","gaps":"..."}',
                {'direction':direction,'reference':original},
                lambda r:isinstance(r,dict) and all(nonempty(r.get(k)) for k in ('mechanism','evidence_needs','verification','gaps')), 'Reference')
        dump(out/'reference_analysis.json',references)

    def generate(direction,parent,action):
        print(f'\n[Candidate {len(nodes)+1}] {direction} | {action}',flush=True)
        context = {'goal':goal,'direction':direction,'action':action,'previous':parent.hypothesis,'feedback':parent.review}
        context['candidate_id'] = len(nodes)+1
        context['reference_logic'] = references.get(direction, {})
        if references and cfg.get('reference_control',{}).get('lock_core_mechanisms'):
            context['core_mechanism_constraint'] = by_num[cfg['directions'].index(direction)+1]['Mechanism']
        context['existing_titles'] = [n.hypothesis['Hypothesis_Title'] for n in nodes if n.direction == direction]
        if parent.review:
            context['weakest_aspects'] = sorted(ASPECTS,key=lambda k:parent.review['scores'][k])[:3]
        if action == 'refine_review':
            context['priority'] = '优先修复评价指出的机制和验证设计缺陷。'
        elif action == 'refine_retrieval':
            context['priority'] = '优先寻找不同证据、反例及替代科学机制。'
        q = checked(a,QUERY_PROMPT,context,lambda r: isinstance(r,dict) and isinstance(r.get('queries'),list) and 3<=len(r['queries'])<=5 and all(nonempty(x) for x in r['queries']),'Query')
        hits = retrieve_layered(rows,q['queries'],cfg['top_chunks'])
        lookup = {x['id']:x for x in hits}
        def valid_evidence(r):
            if not isinstance(r,dict) or not isinstance(r.get('evidence'),list):
                return []
            return [e for e in r['evidence'] if isinstance(e,dict) and all(nonempty(e.get(k)) for k in ('id','quote','inference','boundary')) and e['id'] in lookup and e['quote'] in lookup[e['id']]['text']]
        dump(out/f'candidate_{len(nodes)+1:03d}_retrieval.json',{'context':context,'queries':q['queries'],'hits':hits})
        result = checked(a,EVIDENCE_PROMPT + "\np0或source_type=abstract表示仅有公开摘要，不得推断全文细节。",{'context':context,'chunks':hits},lambda r:bool(valid_evidence(r)),'Evidence')
        valid = valid_evidence(result)
        allowed = {e['id'] for e in valid}
        print(f'[Evidence] {len(valid)} verified excerpts',flush=True)
        def hypothesis_valid(h):
            if not isinstance(h,dict) or not all(nonempty(h.get(f)) for f in FIELDS):
                return False
            ids = set(re.findall(r'E\d{3}-p\d+-c\d+',h['Evidence']))
            return bool(ids) and ids <= allowed
        h = checked(b,HYPOTHESIS_PROMPT + "\n参考逻辑仅作引导，必须由本轮证据独立支撑。若提供core_mechanism_constraint，保持其核心机制，候选差异体现在验证设计和实现路径；否则初始候选应有实质差异；迭代候选优先修复weakest_aspects。",{**context,'evidence':valid,'metadata':metadata,'fields':FIELDS,'other_directions':[d for d in cfg['directions'] if d!=direction]},hypothesis_valid,'Hypothesis')
        h = {f:h[f] for f in FIELDS}
        cited = set(re.findall(r'E\d{3}-p\d+-c\d+',h['Evidence']))
        sources = [e for e in valid if e['id'] in cited]
        def review_valid(r):
            return isinstance(r,dict) and isinstance(r.get('scores'),dict) and all(type(r['scores'].get(k)) in (int,float) and 0<=r['scores'][k]<=10 for k in ASPECTS) and type(r.get('fatal')) is bool and nonempty(r.get('feedback'))
        review = checked(b,REVIEW_PROMPT + "\n摘要证据不得冒充全文或实验验证。",{'goal':goal,'hypothesis':h,'evidence':sources,'aspects':ASPECTS},review_valid,'Review')
        avg = sum(review['scores'][k] for k in ASPECTS)/len(ASPECTS)
        reward = 0 if review['fatal'] else avg/10
        print(f"[Review] {avg:.2f}/10 | fatal={review['fatal']}",flush=True)
        for k in ASPECTS:
            print(f'  {k}: {review["scores"][k]}',flush=True)
        n = Node(len(nodes)+1,direction,h,review,reward,sources,parent)
        nodes.append(n)
        parent.children.append(n)
        n.update(reward)
        dump(out/'tree.json',[root.record()]+[x.record() for x in nodes])
        return n

    initial = {}
    for d in cfg['directions']:
        candidates = [generate(d,root,'generate') for _ in range(cfg.get('initial_candidates_per_direction',1))]
        initial[d] = max(n.reward*10 for n in candidates)

    def meets_target(n):
        return (not n.review['fatal'] and n.reward*10 >= cfg.get('target_score',8.5)
                and min(n.review['scores'][k] for k in ASPECTS) >= cfg.get('min_dimension_score',7))

    def selection_key(n):
        return (meets_target(n), n.reward)

    dump(out/'initial_scores.json',initial)
    def expandable(n):
        return n.depth()<cfg['max_depth'] and (len(n.children)<2 or any(expandable(c) for c in n.children))
    def uct(n):
        return n.total/n.visits+cfg['exploration']*math.sqrt(math.log(max(2,n.parent.visits))/n.visits) if n.visits else float('inf')
    for i in range(cfg['refinements']):
        unmet = {d for d in cfg['directions'] if not any(n.direction==d and meets_target(n) for n in nodes)}
        if cfg.get('early_stop',False) and not unmet:
            print('[MCTS] 全部方向达到内部评分目标',flush=True)
            break
        choices = [n for n in root.children if expandable(n)]
        if cfg.get('early_stop',False):
            choices = [n for n in choices if n.direction in unmet] or choices
        if not choices:
            break
        missing = {d for d in cfg['directions'] if not any(n.direction==d and not n.review['fatal'] for n in nodes)}
        n = max([n for n in choices if n.direction in missing] or choices,key=uct)
        while len(n.children)>=2:
            n = max([c for c in n.children if expandable(c)],key=uct)
        print(f'[MCTS] {i+1}/{cfg["refinements"]}',flush=True)
        child = generate(n.direction,n,'refine_review' if not n.children else 'refine_retrieval')
        history.append({'iteration':i+1,'direction':n.direction,'parent_id':n.id,'child_id':child.id,'parent_score':n.reward*10,'child_score':child.reward*10,'improvement':(child.reward-n.reward)*10})
        dump(out/'optimization_history.json',history)
    dump(out/'optimization_history.json',history)
    selected = []
    for d in cfg['directions']:
        options = [n for n in nodes if n.direction==d and not n.review['fatal']]
        if not options:
            raise RuntimeError('方向没有合格假设: '+d)
        selected.append(max(options,key=selection_key))
    selected.sort(key=lambda n:-n.reward)
    dump(out/'科研假设提交.json',[{'Hypothesis_Num':i,**n.hypothesis,'Rank':i} for i,n in enumerate(selected,1)])
    dump(out/'selected_reviews.json',[n.record() for n in selected])
    before = sum(initial.values())/len(initial)
    after = sum(n.reward*10 for n in selected)/len(selected)
    dump(out/'optimization_report.json',{'initial_mean':before,'final_mean':after,'improvement':after-before,'candidate_count':len(nodes),'completed_refinements':len(history),'comparison':[{'direction':n.direction,'initial_score':initial[n.direction],'final_score':n.reward*10} for n in selected],'targets_met':sum(meets_target(n) for n in selected),'note':'初始分为各方向初始候选最高奖励；参考引导属于逆向重构，搜索内评分不等于独立验证'})
    blocks = []
    lines = metadata.splitlines()
    for eid in sorted({e['id'].split('-')[0] for n in selected for e in n.sources}):
        start = lines.index(eid)
        end = next((j for j in range(start+1,len(lines)) if re.fullmatch(r'E\d+',lines[j])),len(lines))
        ev = {e['id']:e for n in selected for e in n.sources if e['id'].startswith(eid+'-')}
        summary = checked(a,'基于给定原文片段撰写中文摘要和关键内容，区分直接支撑、迁移推论、证据边界。返回 {"abstract":"...","key_content":"..."}。不得声称已阅读未提供内容。',list(ev.values()),lambda r:isinstance(r,dict) and all(nonempty(r.get(k)) for k in ('abstract','key_content')),'Summary')
        blocks.append('\n'.join(lines[start:end])+'\n文献摘要：'+summary['abstract']+'\n关键内容：'+summary['key_content'])
    (out/'科研材料提交.txt').write_text('\n\n'.join(blocks),encoding='utf-8')
    dump(out/'manifest.json',{'mode':args.mode,'config':cfg,'nodes':len(nodes),'reference_guided':cfg.get('reference_guided',False),'note':'参考引导为事后重构，不是原始过程证明；模型评分不是物理仿真或专家验证'})
    print(f'[Done] {len(nodes)} candidates | {before:.2f} -> {after:.2f} | {out.resolve()}',flush=True)

if __name__ == '__main__':
    main()
