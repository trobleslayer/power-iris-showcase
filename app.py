import json, sys, subprocess, os, html, math
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from studio import studio

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Power-IRIS | 自主科研工作台',layout='wide',page_icon='⚡')
st.markdown("""<style>
.stApp{background:radial-gradient(ellipse at 60% 0%,#163653 0%,#091828 38%,#07111e 85%);color:#dceaf6} [data-testid=stSidebar]{background:#0a1828;border-right:1px solid #28465c} [data-testid=stHeader]{background:transparent} .block-container{padding-top:1.8rem;max-width:1800px} h1,h2,h3{color:#e8f5ff!important} [data-testid=stMetric]{background:#10243a;border:1px solid #294861;border-radius:8px;padding:14px} [data-testid=stMetricValue]{color:#77dfef} .hero{position:relative;overflow:hidden;border:1px solid #315b78;border-radius:12px;padding:24px 30px;background:linear-gradient(110deg,#102c46,#0c2035 65%,#153c52);margin-bottom:18px}.hero:after{content:'';position:absolute;right:-40px;top:-95px;width:370px;height:370px;border:1px solid #3a7c99;border-radius:50%;box-shadow:0 0 0 22px #4da4bc12,0 0 0 48px #4da4bc0b,0 0 0 75px #4da4bc08;pointer-events:none}.eyebrow{color:#72d4e9;letter-spacing:3px;font-size:11px}.hero h1{font-size:34px;margin:8px 0}.hero p{color:#a9bfd5;margin:0}.kpi{background:linear-gradient(145deg,#142e45,#0d2033);border:1px solid #284b65;border-top:2px solid #53c9dc;border-radius:8px;padding:13px 15px;min-height:105px}.kpi small{color:#91adc4;font-size:12px}.kpi strong{display:block;color:#a1edfa;font-size:32px;font-family:Arial,sans-serif;line-height:1.4}.kpi em{font-style:normal;font-size:10px;color:#6e91aa;letter-spacing:1px}.panel{border:1px solid #294a62;border-radius:9px;background:#0c1e30;padding:16px;margin:8px 0}.panelhead{color:#a9d7ed;font-size:13px;letter-spacing:1px;border-bottom:1px solid #27465c;padding-bottom:10px;margin-bottom:12px}.stage{display:flex;align-items:center;gap:10px;padding:13px 0;border-bottom:1px solid #20384d}.stage b{color:#d6eafa;font-size:13px}.stage small{display:block;color:#819eb5;font-size:11px}.num{color:#65cfe5;font:16px Arial;min-width:26px}.result{border-bottom:1px solid #274459;padding:10px 0;color:#d9eaf6;font-size:13px}.result small{color:#87a9c1}.score{float:right;color:#f2c77e;font:bold 17px Arial}.stButton button{border:1px solid #3b7996;border-radius:7px} .foot{color:#86a1b8;font-size:11px;margin:12px 0}.stApp [data-testid=stSidebar] label{font-size:14px}
</style>""",unsafe_allow_html=True)

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return default

def download(p):
    if p.is_file():st.download_button(p.name,p.read_bytes(),file_name=p.name,key=str(p))

labels=dict(novelty='创新性',physics='物理合理性',feasibility='可行性',falsifiability='可证伪性',evidence='证据支撑',relevance='任务契合',latency='时效性',accuracy='准确性',generalization='泛化性',interpretability='可解释性')
fields=dict(Scenario='应用场景',Research_Object='研究对象',Key_Variables='关键变量',Method='技术方法',Mechanism='科学机制',Conditions='适用条件',Prediction='可检验预测',Evidence='文献依据',Innovation='创新点',Verification='验证设计',Feasibility='实施可行性')
with st.sidebar:
    st.title('⚡ Power-IRIS')
    st.caption('RESEARCH INTELLIGENCE SYSTEM')
    dirs=sorted([p for p in (ROOT/'outputs').glob('*') if p.is_dir() and (p/'tree.json').exists()],key=lambda p:p.stat().st_mtime,reverse=True)
    path=st.selectbox('成果运行记录',dirs,format_func=lambda p:p.name) if dirs else ROOT/'outputs'/'v3_relaxed_mcts12'
    page=st.radio('科研工作台',['01 任务总览','02 知识与证据','03 科研空间探索','04 假设评价','05 科研成果库','06 运行与复现','07 自主科研工作台'])
    st.caption('匿名竞赛展示 · 本地部署')
manifest=load(path/'manifest.json',{}); cfg=manifest.get('config') or load(ROOT/'config.json',{}); report=load(path/'optimization_report.json',{}); tree=load(path/'tree.json',[]); nodes=[n for n in tree if n.get('hypothesis')]; selected=load(path/'selected_reviews.json',[]); chunks=load(path/'chunks.json',[]); refs=load(path/'reference_analysis.json',{}); directions=cfg.get('directions',[]); chosen={n['id'] for n in selected}; lookup={c['id']:c for c in chunks}
st.markdown('<div class="hero"><div class="eyebrow">POWER SYSTEM · SCIENTIFIC DISCOVERY</div><h1>新型电力系统自主科研工作台</h1><p>知识增强 / 科学机制推理 / 多维评价 / 证据溯源</p></div>',unsafe_allow_html=True)
if not dirs:st.warning('未发现运行成果。请将本文件放入原 Power-IRIS 根目录，并保留 outputs 文件夹。当前不展示虚构数据。')
if page.startswith('07'):
    studio(ROOT,load(ROOT/'config.json',{}))
elif page.startswith('01'):
    def esc(x): return html.escape(str(x))
    def panel(title,body): st.markdown(f'<div class="panel"><div class="panelhead">{title}</div>{body}</div>',unsafe_allow_html=True)
    vals=[('入库文献',len({c['paper'] for c in chunks}) if chunks else '—','DOCUMENTS'),('知识片段',len(chunks) if chunks else '—','KNOWLEDGE'),('候选假设',len(nodes) if nodes else '—','CANDIDATES'),('入选成果',len(selected) if selected else '—','DISCOVERIES'),('模型综合评分',f"{report['final_mean']:.2f}" if 'final_mean' in report else '—','MODEL SCORE / 10'),('实际优化次数',report.get('completed_refinements','—'),'REFINEMENTS')]
    for col,(k,v,en) in zip(st.columns(6),vals):col.markdown(f'<div class="kpi"><small>{k}</small><strong>{v}</strong><em>{en}</em></div>',unsafe_allow_html=True)
    st.markdown('<div class="foot">MISSION / '+esc(cfg.get('goal','尚未加载科研任务'))+'</div>',unsafe_allow_html=True)
    left,mid,right=st.columns([1.05,2.2,1.35],gap='medium')
    with left:
        stages=[('问题理解','任务目标与方向划分'),('知识构建','BM25召回 · LLM证据提取'),('机制推理','参考引导 · 假设生成'),('评价筛选','十维评价 · 搜索策略'),('成果输出','结构化假设 · 证据链')]
        panel('01 / 科研执行链',''.join(f'<div class="stage"><span class="num">{i:02d}</span><div><b>{t}</b><small>{d}</small></div></div>' for i,(t,d) in enumerate(stages,1)))
        panel('双智能体协同','<div class="stage"><span class="num">A</span><div><b>知识检索智能体</b><small>'+esc(cfg.get('retrieval',{}).get('model','—'))+'</small></div></div><div class="stage"><span class="num">B</span><div><b>科研生成与评价</b><small>'+esc(cfg.get('ideation',{}).get('model','—'))+'</small></div></div>')
    with mid:
        st.markdown('#### 02 / 科研空间 · Research landscape')
        ds=list(dict.fromkeys([*directions,*(n.get('direction','') for n in nodes)]))
        short=['实时安全','极端天气','拓扑迁移','区域协同','安全边界','可信解释']
        fig=go.Figure()
        # Use data coordinates for all geometry; marker sizes stay small.
        for r in [1.05,2.35,3.45]:
            fig.add_shape(type='circle',x0=-r,y0=-r,x1=r,y1=r,line=dict(color='#294c65',dash='dot',width=1),layer='below')
        for i,d in enumerate(ds):
            a=math.pi/2-2*math.pi*i/max(len(ds),1)
            x,y=2.35*math.cos(a),2.35*math.sin(a)
            fig.add_trace(go.Scatter(x=[0,x],y=[0,y],mode='lines',line=dict(color='#428da6',width=2),hoverinfo='skip',showlegend=False))
            ns=[n for n in nodes if n.get('direction')==d]
            for j,n in enumerate(ns):
                spread=min(.64, 4.6/max(len(ds),1))
                aa=a+((j/(len(ns)-1)-.5)*spread if len(ns)>1 else 0)
                rr=3.45 if len(ns)<=5 else 3.45+.23*(j%3)
                xx,yy=rr*math.cos(aa),rr*math.sin(aa)
                gold=n['id'] in chosen
                fig.add_trace(go.Scatter(x=[x,xx],y=[y,yy],mode='lines',line=dict(color='#b99758' if gold else '#355b74',width=1.5 if gold else 1),hoverinfo='skip',showlegend=False))
                fig.add_trace(go.Scatter(x=[xx],y=[yy],mode='markers',marker=dict(size=13 if gold else 8,color='#f2c77e' if gold else '#5084a5',symbol='diamond' if gold else 'circle',line=dict(color='#fce1a8' if gold else '#80b5d1',width=1)),text=[n['hypothesis'].get('Hypothesis_Title','')],hovertemplate='%{text}<extra></extra>',showlegend=False))
            fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers',marker=dict(size=12,color='#76dbe9'),hovertext=[d],hoverinfo='text',showlegend=False))
            name=short[i] if len(ds)==6 and ds==directions else d
            fig.add_annotation(x=x,y=y,text=f'<b>{html.escape(name)}</b><br>{len(ns)} 项候选',showarrow=False,bgcolor='#14354c',bordercolor='#56a9c2',borderwidth=1,borderpad=5,font=dict(size=12,color='#d9f2fa'),yshift=0)
        fig.add_shape(type='circle',x0=-.88,y0=-.88,x1=.88,y1=.88,fillcolor='#17465e',line=dict(color='#81e0ed',width=2),layer='above')
        fig.add_annotation(x=0,y=0,text='<b>断面潮流</b><br>智能调控',showarrow=False,font=dict(size=14,color='#eafaff'))
        fig.update_layout(height=490,margin=dict(l=8,r=8,t=8,b=8),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(visible=False,range=[-4.15,4.15],fixedrange=True,constrain='domain'),yaxis=dict(visible=False,range=[-4.15,4.15],scaleanchor='x',scaleratio=1,constrain='domain',fixedrange=True),dragmode=False,showlegend=False)
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
        st.caption('青蓝：研究方向及候选节点 · 金色菱形：入选成果（方向归类图，非MCTS父子树）')
    with right:
        body=''
        for i,d in enumerate(ds,1):
            ns=[n for n in selected if n.get('direction')==d]; n=ns[0] if ns else {}; score=f"{n['reward']*10:.2f}" if n else '—'; title=n.get('hypothesis',{}).get('Hypothesis_Title','暂无入选记录');body+=f'<div class="result"><span class="score">{score}</span><small>H{i:03d} / {esc(d)}</small><br>{esc(title)}</div>'
        panel('03 / 入选科研成果',body or '尚未加载成果')
    st.markdown('#### 04 / 科研质量画像')
    if selected:
        a,b=st.columns([1,2]); keys=list(labels); means=[sum(float(n.get('review',{}).get('scores',{}).get(k,0)) for n in selected)/len(selected) for k in keys if all(k in n.get('review',{}).get('scores',{}) for n in selected)]; ks=[k for k in keys if all(k in n.get('review',{}).get('scores',{}) for n in selected)]
        if means:
            f=go.Figure(go.Scatterpolar(r=means+means[:1],theta=[labels[k] for k in ks]+[labels[ks[0]]],fill='toself',fillcolor='rgba(87,204,222,.18)',line=dict(color='#70d9e8')));f.update_layout(height=330,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',margin=dict(l=45,r=45,t=25,b=25),polar=dict(bgcolor='#102438',radialaxis=dict(range=[0,10],gridcolor='#34536b')));a.plotly_chart(f,use_container_width=True,config={'displayModeBar':False})
        z=[[n.get('review',{}).get('scores',{}).get(k) for k in keys] for n in selected];f=go.Figure(go.Heatmap(z=z,x=[labels[k] for k in keys],y=[f'H{i:03d}' for i in range(1,len(z)+1)],zmin=0,zmax=10,colorscale=[[0,'#102339'],[.7,'#255d79'],[1,'#77d8d9']],text=z,texttemplate='%{text}',showscale=False));f.update_layout(height=330,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=45,r=10,t=25,b=60),yaxis=dict(autorange='reversed'));b.plotly_chart(f,use_container_width=True,config={'displayModeBar':False})
elif page.startswith('02'):
    st.subheader('文献知识库与证据链')
    academic=load(path/'academic_search.json',{})
    if academic:
        cols=st.columns(4)
        for col,key,label in zip(cols,['raw_count','unique_with_abstract','qualified_count','external_count'],['初步召回','有效摘要去重','相关性合格','外部入库']): col.metric(label,academic.get(key,'—'))
        download(path/'academic_search.json')
    if chunks:
        papers={c['paper']:c['file'] for c in chunks}; st.dataframe(pd.DataFrame([{'编号':k,'文献':v,'片段数':sum(c['paper']==k for c in chunks)} for k,v in papers.items()]),hide_index=True,use_container_width=True)
    if nodes:
        n=st.selectbox('选择候选假设',nodes,format_func=lambda n:f"{n['id']:03d} | {n['hypothesis']['Hypothesis_Title']}")
        r=load(path/f"candidate_{n['id']:03d}_retrieval.json",{}); st.write('检索查询',r.get('queries',[]))
        for e in n.get('sources',[]):
            c=lookup.get(e['id'],{}); verified=bool(c and e.get('quote') and e['quote'] in c.get('text',''))
            with st.expander(f"{e['id']} · {'原文匹配' if verified else '未核验'}",expanded=True):
                st.caption(c.get('file','')); st.write(e.get('quote','')); st.write('推理：',e.get('inference','')); st.write('适用边界：',e.get('boundary',''))
        with st.expander('查看召回片段'):
            for c in r.get('hits',[]):st.markdown('**'+c['id']+'**');st.write(c['text'])
elif page.startswith('03'):
    st.subheader('科研空间探索 · 实际搜索记录')
    st.caption(f"实际优化次数：{report.get('completed_refinements','—')}；初始候选与迭代节点均来自运行文件。")
    if nodes:
        pos={0:(0,0)}; groups={d:[] for d in directions}
        for n in nodes:groups.setdefault(n['direction'],[]).append(n)
        for i,(d,ns) in enumerate(groups.items()):
            for j,n in enumerate(ns):pos[n['id']]=(i+1,j+1)
        fig=go.Figure()
        for n in nodes:
            x,y=pos[n['id']]; px,py=pos.get(n.get('parent'),(0,0));fig.add_trace(go.Scatter(x=[px,x],y=[py,y],mode='lines',line=dict(color='#36536c',width=1),hoverinfo='skip',showlegend=False))
        fig.add_trace(go.Scatter(x=[pos[n['id']][0] for n in nodes],y=[pos[n['id']][1] for n in nodes],mode='markers+text',text=[str(n['id']) for n in nodes],textposition='top center',hovertext=[n['hypothesis']['Hypothesis_Title'] for n in nodes],marker=dict(size=15,color=['#6ce2c2' if n['id'] in chosen else '#5e9ecb' for n in nodes]),showlegend=False));fig.add_trace(go.Scatter(x=[0],y=[0],mode='markers+text',text=['ROOT'],textposition='top center',marker=dict(size=20,color='#e5bb70'),showlegend=False));fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',height=480,xaxis=dict(tickvals=list(range(1,len(groups)+1)),ticktext=list(groups),tickangle=-15),yaxis_title='方向内候选序号');event=st.plotly_chart(fig,use_container_width=True,on_select='rerun',selection_mode='points',key='search_tree')
        points=event.selection.points
        picked=next((int(p['text']) for p in points if str(p.get('text','')).isdigit()),None)
        idx=next((i for i,n in enumerate(nodes) if n['id']==picked),0)
        n=st.selectbox('查看节点',nodes,index=idx,format_func=lambda n:f"{n['id']} | {n['hypothesis']['Hypothesis_Title']}",key=f'node_{picked}')
        a,b=st.columns([2,1]); a.markdown('### '+n['hypothesis']['Hypothesis_Title']); a.write(n['hypothesis']); b.metric('内部评分',f"{n['reward']*10:.2f}"); b.write(n.get('review',{}))
        st.markdown('### 原文证据链')
        for e in n.get('sources',[]):
            c=lookup.get(e['id'],{}); st.caption(e['id']+' · '+c.get('file','')); st.write(e.get('quote','')); st.write(e.get('inference','')); st.caption('原文匹配' if e.get('quote') and e['quote'] in c.get('text','') else '未核验')
elif page.startswith('04'):
    st.subheader('十维科研质量评价');st.caption('内部大模型评分，非独立专家或仿真验证。')
    if selected:
        n=st.selectbox('入选假设',selected,format_func=lambda n:n['hypothesis']['Hypothesis_Title']); scores=n.get('review',{}).get('scores',{}); keys=[k for k in labels if k in scores]; theta=[labels[k] for k in keys]; values=[scores[k] for k in keys]; a,b=st.columns([2,1]);fig=go.Figure(go.Scatterpolar(r=values+values[:1],theta=theta+theta[:1],fill='toself',line=dict(color='#65d4e9')));fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',polar=dict(radialaxis=dict(range=[0,10])),height=450);a.plotly_chart(fig,use_container_width=True);b.metric('综合内部评分',f"{n['reward']*10:.2f}");b.write(n.get('review',{}).get('feedback',''));st.dataframe(pd.DataFrame([{'研究方向':x['direction'],**{labels.get(k,k):v for k,v in x.get('review',{}).get('scores',{}).items()}} for x in selected]),hide_index=True,use_container_width=True)

elif page.startswith('05'):

    # ==================================================
    # 05 科研成果库
    # ==================================================

    st.markdown("""
    <div style="
        font-size:12px;
        letter-spacing:2px;
        color:#83BBD5;
        margin-bottom:8px;">
        POWER-IRIS / RESEARCH DISCOVERIES
    </div>
    """, unsafe_allow_html=True)

    st.title('科研成果库')

    st.caption(
        '科研假设生成 · 多维质量评价 · 优选成果输出'
    )

    # --------------------------------------------------
    # 1. 读取实际运行统计
    # --------------------------------------------------

    candidate_count = len(nodes)
    selected_count = len(selected)

    mean_score = (
        sum(float(n['reward']) * 10 for n in selected)
        / selected_count
        if selected_count else None
    )

    # --------------------------------------------------
    # 2. 顶部统计卡片
    # --------------------------------------------------

    st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background: linear-gradient(
            135deg, #16364F, #10283E
        );
        border: 1px solid #31546E;
        border-radius: 12px;
        padding: 20px;
    }

    [data-testid="stMetricValue"] {
        color: #83D4E9;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #B5D1E4;
    }

    [data-testid="stExpander"] {
        border: 1px solid #34546B;
        border-radius: 10px;
        margin-bottom: 12px;
    }

    [data-testid="stDownloadButton"] button {
        border: 1px solid #416B86;
        border-radius: 8px;
        min-height: 48px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        '科研候选假设',
        candidate_count
    )

    col2.metric(
        '优选科研成果',
        selected_count
    )

    col3.metric(
        '内部平均评分',
        f'{mean_score:.2f}' if mean_score is not None else '—'
    )

    st.divider()

    # --------------------------------------------------
    # 3. 优选科研假设集合
    # --------------------------------------------------

    st.subheader('优选科研假设集合')

    st.caption(
        '基于文献证据、科研空间搜索及多维质量评价形成'
    )

    if not selected:
        st.warning('当前运行记录暂无入选科研成果。')

    for i, n in enumerate(selected, 1):

        h = n['hypothesis']

        title = h.get(
            'Hypothesis_Title',
            '未命名科研假设'
        )

        direction = n.get('direction', '')

        score = float(n.get('reward', 0)) * 10

        # 每项成果采用可展开卡片
        with st.expander(
            f'H{i:03d}  |  {title}',
            expanded=False
        ):

            a, b = st.columns([3, 1])

            a.markdown('**研究方向**')
            a.write(direction)

            b.metric(
                '综合内部评分',
                f'{score:.2f}'
            )

            st.divider()

            # 展示完整科研假设
            for key, label in fields.items():

                value = h.get(key)

                if value:
                    st.markdown(f'**{label}**')
                    st.write(value)

            # 科研质量评价
            scores = n.get(
                'review', {}
            ).get('scores', {})

            if scores:

                st.divider()

                st.markdown('**科研质量评价**')

                score_cols = st.columns(2)

                for j, (key, value) in enumerate(
                    scores.items()
                ):

                    score_cols[j % 2].progress(
                        max(0.0, min(float(value) / 10, 1.0)),
                        text=(
                            f'{labels.get(key, key)}'
                            f'  {float(value):.1f}/10'
                        )
                    )

    # --------------------------------------------------
    # 4. 科研成果下载
    # --------------------------------------------------

    st.divider()

    st.subheader('科研成果下载')

    hypothesis_file = path / '科研假设提交.json'
    material_file = path / '科研材料提交.txt'

    col1, col2 = st.columns(2)

    with col1:

        if hypothesis_file.is_file():

            st.download_button(
                label='下载科研假设成果',
                data=hypothesis_file.read_bytes(),
                file_name='科研假设成果.json',
                mime='application/json',
                use_container_width=True,
                key='download_research_hypotheses'
            )

        else:
            st.caption('暂无科研假设研创文件')

    with col2:

        if material_file.is_file():

            st.download_button(
                label='下载科研文献材料',
                data=material_file.read_bytes(),
                file_name='科研文献材料.txt',
                mime='text/plain',
                use_container_width=True,
                key='download_research_materials'
            )

        else:
            st.caption('暂无科研材料研创文件')

    st.caption(
        '本页展示本轮实际入选的科研成果。'
        '评分为大模型内部科研质量评价，'
        '科学假设仍需后续仿真与实验验证。'
    )


elif page.startswith('06'):

    # ==================================================
    # 06 运行与复现
    # ==================================================

    st.markdown("""
    <div style="
        font-size:12px;
        letter-spacing:2px;
        color:#83BBD5;
        margin-bottom:8px;">
        POWER-IRIS / REPRODUCIBILITY
    </div>
    """, unsafe_allow_html=True)

    st.title('运行与复现')

    st.caption(
        '科研任务配置 · 算法运行记录 · 成果可追溯'
    )

    # --------------------------------------------------
    # 1. 实际运行统计
    # --------------------------------------------------

    a, b, c = st.columns(3)

    a.metric(
        '科研方向',
        len(cfg.get('directions', []))
    )

    b.metric(
        '科研候选假设',
        len(nodes)
    )

    history = load(
        path / 'optimization_history.json',
        []
    )

    c.metric(
        'MCTS实际迭代',
        len(history)
    )

    st.divider()

    # --------------------------------------------------
    # 2. 多智能体模型配置
    # --------------------------------------------------

    st.subheader('多智能体模型配置')

    retrieval_cfg = cfg.get('retrieval', {})
    ideation_cfg = cfg.get('ideation', {})

    a, b = st.columns(2)

    with a:
        st.markdown('**检索智能体**')
        st.write(
            retrieval_cfg.get('model', '未记录')
        )

    with b:
        st.markdown('**构思与评审智能体**')
        st.write(
            ideation_cfg.get('model', '未记录')
        )

    # --------------------------------------------------
    # 3. MCTS搜索配置
    # --------------------------------------------------

    st.subheader('科研空间搜索配置')

    search_config = {
        '每方向初始候选数':
            cfg.get('initial_candidates_per_direction'),

        'MCTS迭代预算':
            cfg.get('refinements'),

        '实际完成迭代':
            len(history),

        '最大搜索深度':
            cfg.get('max_depth'),

        'UCT探索系数':
            cfg.get('exploration'),

        '文献片段召回数':
            cfg.get('top_chunks'),

        '综合评分目标':
            cfg.get('target_score'),

        '最低单项评分':
            cfg.get('min_dimension_score')
    }

    st.table([
        {'配置参数': key, '参数值': value}
        for key, value in search_config.items()
    ])

    # --------------------------------------------------
    # 4. 评价口径及复现条件
    # --------------------------------------------------

    st.subheader('科研评价与复现条件')

    st.write(
        '采用创新性、物理合理性、可行性、'
        '可证伪性、证据支撑、任务契合度、'
        '时效性、准确性、泛化性及可解释性'
        '十个维度进行综合科研质量评价。'
    )

    with st.expander('运行模式与技术说明'):

        reference_guided = manifest.get(
            'reference_guided',
            cfg.get('reference_guided', False)
        )

        st.write(
            '运行模式：'
            + (
                '参考成果引导式科研探索'
                if reference_guided
                else '非参考引导式科研探索'
            )
        )

        if reference_guided:
            st.write(
                '本轮运行以已有科研成果作为机制参考，'
                '通过文献检索、假设生成、树搜索及评价'
                '开展科研思路重构与探索。'
            )

        st.write(
            '评价口径：大模型内部评分，'
            '不代表独立专家评价或物理仿真结果。'
        )

        st.write(
            '原始运行记录及参考输入保存在成果目录中。'
        )

    # --------------------------------------------------
    # 5. 运行成果与复现文件
    # --------------------------------------------------

    st.divider()

    st.subheader('运行记录下载')

    files = [
        'manifest.json',
        'optimization_report.json',
        'optimization_history.json',
        'selected_reviews.json',
        'tree.json'
    ]

    for name in files:
        download(path / name)

    st.info(
        '启动科研任务及查看实时运行日志，'
        '请进入自主科研工作台。'
    )

