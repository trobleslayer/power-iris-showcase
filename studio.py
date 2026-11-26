import json, os, sys, subprocess, re, uuid
from pathlib import Path
import streamlit as st

@st.fragment(run_every=2)
def monitor(root):
    job=st.session_state.get('job')
    if not job: return
    proc,out=job; code=proc.poll(); log=out/'run.log'
    text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
    try: nodes=[n for n in json.loads((out/'tree.json').read_text(encoding='utf-8')) if n.get('hypothesis')]
    except (OSError,ValueError): nodes=[]
    a,b,c=st.columns(3); a.metric('任务状态','执行中' if code is None else ('完成' if code==0 else '已退出')); b.metric('已完成候选',len(nodes)); c.metric('已校验证据批次',len(re.findall(r'\[Evidence\] \d+ verified',text)))
    rounds=re.findall(r'\[Academic\] round (\d+): (\d+) records \| (\d+) unique abstracts \| (\d+) qualified',text)
    if rounds:
        rnd,raw,unique,qualified=rounds[-1]
        a,b,c,d=st.columns(4)
        a.metric('检索轮次',rnd); b.metric('累计召回',raw); c.metric('去重有效摘要',unique); d.metric('合格外部文献',qualified)
    st.caption('Agent A · 查询与证据提取  /  Agent B · 假设生成与评价；以下为真实后台日志，不模拟进度。')
    st.code(text[-14000:] or '等待后台输出…',language='text')
    if nodes:
        n=nodes[-1]; st.markdown('**最新完成：** '+n['hypothesis'].get('Hypothesis_Title','')); st.write(n.get('review',{}).get('feedback',''))
    if code is None and st.button('停止任务',key='stop_job'):
        proc.terminate(); st.warning('已请求停止；已保存的成果及缓存保留。')
    if code is not None:
        st.caption(f'退出码 {code} · {out.name}')
        if st.button('刷新成果目录'): st.rerun()

def studio(root,base):
    st.subheader('自主科研工作台 / Research Studio')
    st.caption('任务配置独立保存，不覆盖原 config.json。Replay 仅在请求与历史缓存完全匹配时成功。')
    mode=st.radio('运行模式',['showcase','replay','live'],horizontal=True,format_func=lambda x:{'showcase':'成果展示','replay':'缓存复现','live':'实时科研'}[x])
    if mode=='showcase':
        st.info('请在左侧选择历史运行记录，并进入总览、证据或科研空间页面。无需API。'); monitor(root); return
    ref = st.checkbox(
        '科学机制约束引导',
        value=bool(base.get('reference_guided', True)),
        help='利用已有科研假设的核心科学机制引导科研探索。'
    )
    goal=st.text_area('科研问题',base.get('goal',''),height=110,disabled=ref)
    original=base.get('directions',[])
    raw=st.text_area('科研方向（每行一个）','\n'.join(original),disabled=ref)
    directions=list(dict.fromkeys(x.strip() for x in raw.splitlines() if x.strip()))
    if ref: st.caption('参考模式固定原任务与方向顺序，避免参考假设编号错配。')
    a,b,c=st.columns(3)
    initial=a.number_input('每方向初始候选',1,10,int(base.get('initial_candidates_per_direction',3)))
    refinements=b.number_input('额外搜索预算',0,200,int(base.get('refinements',48)))
    depth=c.number_input('最大深度',1,10,int(base.get('max_depth',5)))
    a,b,c=st.columns(3)
    chunks=a.number_input('文献召回数量',1,100,int(base.get('top_chunks',20)))
    target=b.number_input('综合目标',0.,10.,float(base.get('target_score',8.5)),.1)
    minimum=c.number_input('最低单项评分',0.,10.,float(base.get('min_dimension_score',7)),.1)
    early=st.checkbox('达标提前停止',value=base.get('early_stop',True))
    cfg={**base,'goal':goal,'directions':directions,'reference_guided':ref,'initial_candidates_per_direction':initial,'refinements':refinements,'max_depth':depth,'top_chunks':chunks,'target_score':target,'min_dimension_score':minimum,'early_stop':early}
    opt=dict(base.get('academic_search',{}))
    opt['enabled']=st.checkbox('外部学术检索',value=opt.get('enabled',True))
    opt['target_total_papers']=st.number_input('知识库目标篇数',6,500,int(opt.get('target_total_papers',200)))
    if not opt['enabled']: opt['target_total_papers']=6
    opt['target_external_papers']=opt['target_total_papers']-6
    a,b,c=st.columns(3)
    opt['results_per_query']=a.number_input('每查询召回上限',10,100,int(opt.get('results_per_query',50)),disabled=not opt['enabled'])
    opt['max_search_rounds']=b.number_input('最大检索轮数',1,20,int(opt.get('max_search_rounds',5)),disabled=not opt['enabled'])
    opt['min_relevance_score']=c.number_input('文献相关性阈值',0.,10.,float(opt.get('min_relevance_score',7)),.1,disabled=not opt['enabled'])
    st.caption(f"核心文献6篇；外部文献目标{opt['target_external_papers']}篇。实际数量以检索记录为准。")
    cfg['academic_search']=opt
    st.metric('候选数量上限',len(directions)*initial+refinements)
    st.download_button('导出任务配置',json.dumps(cfg,ensure_ascii=False,indent=2),'task_config.json')
    job=st.session_state.get('job'); busy=bool(job and job[0].poll() is None)
    if st.button('启动科研任务',type='primary',disabled=busy or not goal.strip() or not directions):
        missing=[k for k in ('retrieval','ideation') if not cfg.get(k,{}).get('key_env') or (mode=='live' and not os.getenv(cfg[k]['key_env']))]
        if missing: st.error('模型配置或API环境变量缺失：'+', '.join(missing))
        elif not (root/'run.py').exists(): st.error('缺少 run.py')
        else:
            out=root/'outputs'/('studio_'+uuid.uuid4().hex[:12]); out.mkdir(parents=True); p=out/'task_config.json'; p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
            with (out/'run.log').open('w',encoding='utf-8') as f:
                proc=subprocess.Popen([sys.executable,'-u',str(root/'run.py'),'--mode',mode,'--config',str(p),'--out',str(out)],cwd=root,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            st.session_state['job']=(proc,out)
    monitor(root)
