"""External academic discovery via Crossref; no extra key required."""
import json, re, hashlib, urllib.request, urllib.parse, time, html
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import math, os, tempfile

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,s): self.parts.append(s)
def clean(s):
    p=Plain(); p.feed(str(s or '')); return ' '.join(html.unescape(' '.join(p.parts)).split())
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=p.parent,delete=False) as f:
        json.dump(v,f,ensure_ascii=False,indent=2); tmp=f.name
    os.replace(tmp,p)
def fetch(url,cache,mode):
    p=cache/('academic_'+hashlib.sha256(url.encode()).hexdigest()+'.json')
    if p.exists(): return json.loads(p.read_text(encoding='utf-8'))
    if mode=='replay': raise RuntimeError('缺少学术检索缓存: '+p.name)
    for i in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Power-IRIS/4.0 academic research','Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=40) as r: v=json.load(r)
            write(p,v); time.sleep(.3); return v
        except Exception:
            if i==2: raise
            time.sleep(2**i)
def norm(s):
    return ''.join(c for c in s.casefold() if c.isalnum())

def discover(client,cfg,cache,out,mode,rows):
    opt=cfg['academic_search']; limit=int(opt.get('results_per_query',50)); seed={r['paper'] for r in rows}
    if seed != {f'E{i:03d}' for i in range(1,7)}: raise RuntimeError('核心文献不完整')
    cap=int(opt.get('target_total_papers',200))-len(seed)
    if cap<0: raise ValueError('目标规模小于核心库')
    from reference_control import seed_metadata
    seeds=seed_metadata(Path(__file__).resolve().parent/'data')
    titles={norm(p['title']) for p in seeds}; dois={p['doi'] for p in seeds if p['doi']}
    found={}; approved={}; logs=[]; seen_queries=set(); raw_count=0; screened=set()
    directions=cfg['directions']; nq=int(opt.get('queries_per_direction',4)); threshold=float(opt.get('min_relevance_score',7))
    search_workers=max(1,min(8,int(opt.get('search_workers',4))))
    llm_workers=max(1,min(8,int(opt.get('llm_workers',4))))
    batch_size=max(1,min(30,int(opt.get('review_batch_size',16))))
    cache=Path(cache); cache.mkdir(parents=True,exist_ok=True)
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    for rnd in range(int(opt.get('max_search_rounds',5))):
        if len(approved)>=cap: break
        tasks=[]
        def query_job(direction):
            prior=[x['query'] for x in logs if x['direction']==direction]
            return client.ask('生成指定数量的不同英文电力系统学术检索短语，避免重复既有查询。返回 {"queries":["..."]}',{'goal':cfg['goal'],'direction':direction,'count':nq,'round':rnd+1,'previous_queries':prior})
        with ThreadPoolExecutor(max_workers=llm_workers) as ex:
            results=list(ex.map(query_job,directions))
        for direction,q in zip(directions,results):
            for query in q.get('queries',[])[:nq]:
                if not isinstance(query,str) or not query.strip() or norm(query) in seen_queries: continue
                seen_queries.add(norm(query)); query=query.strip()
                url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.bibliographic':query,'rows':limit,'filter':'type:journal-article,from-pub-date:2010-01-01'})
                tasks.append((direction,query,url))
        def search_job(task):
            direction,query,url=task
            try: return fetch(url,cache,mode)['message']['items'],None
            except Exception as e:
                if mode=='replay': raise
                return [],str(e)
        with ThreadPoolExecutor(max_workers=search_workers) as ex:
            for (direction,query,url),(items,error) in zip(tasks,ex.map(search_job,tasks)):
                if error:
                    logs.append({'direction':direction,'query':query,'error':error}); continue
                raw_count+=len(items); logs.append({'direction':direction,'query':query,'returned':len(items),'url':url})
                for item in items:
                    doi=str(item.get('DOI','')).lower().strip(); title=clean((item.get('title') or [''])[0]); abstract=clean(item.get('abstract'))
                    if not doi or not title or len(abstract)<150: continue
                    if doi in found:
                        if direction not in found[doi]['directions']: found[doi]['directions'].append(direction)
                        continue
                    if doi in dois or norm(title) in titles: continue
                    titles.add(norm(title)); dois.add(doi)
                    found[doi]={'doi':doi,'title':title,'abstract':abstract,'authors':', '.join(' '.join([a.get('given',''),a.get('family','')]).strip() for a in item.get('author',[])),'year':(item.get('published',{}).get('date-parts') or [[None]])[0][0],'venue':(item.get('container-title') or [''])[0],'url':'https://doi.org/'+doi,'directions':[direction]}
        print(f'[Academic] retrieved {raw_count} records; {len(found)} unique abstracts',flush=True)
        pool=[p for d,p in found.items() if d not in screened]
        # Local BM25 ranking over English queries; never treats local rank as LLM approval.
        def tok(s): return re.findall(r'[a-z0-9]+',s.lower())
        docs=[Counter(tok(p['title']+' '+p['title']+' '+p['abstract'])) for p in pool]
        df=Counter(t for d in docs for t in d); avg=sum(map(lambda d:sum(d.values()),docs))/max(1,len(docs))
        queries={d:set(tok(' '.join(x['query'] for x in logs if x['direction']==d))) for d in directions}
        def rank(i):
            d=docs[i]; q=set().union(*(queries[x] for x in pool[i]['directions']))
            return sum(math.log(1+(len(docs)-df[t]+.5)/(df[t]+.5))*2.2*d[t]/(d[t]+1.2*(.25+.75*sum(d.values())/max(avg,1))) for t in q if d[t])
        pool=[pool[i] for i in sorted(range(len(pool)),key=lambda i:(-rank(i),pool[i]['doi']))]
        budget=max(batch_size,int(opt.get('screen_per_round',360)))
        pool=pool[:budget]
        def review_job(batch):
            allowed={p['doi'] for p in batch}
            result=client.ask('逐篇评价电力系统科研相关性。6分表示有明确可迁移技术参考价值，8分表示直接相关，低于6分表示无关。必须为每个输入DOI返回一个0-10数字评分，不得遗漏或创造DOI。JSON: {"papers":[{"doi":"...","score":8}]}',{'goal':cfg['goal'],'papers':[{'doi':p['doi'],'title':p['title'],'abstract':p['abstract'][:1200],'directions':p['directions']} for p in batch]})
            scores={x['doi']:x['score'] for x in result.get('papers',[]) if isinstance(x,dict) and x.get('doi') in allowed and type(x.get('score')) in (int,float) and 0<=x['score']<=10}
            if set(scores)!=allowed: raise ValueError('文献评价遗漏DOI，未将该批次标记为完成')
            return scores
        # Bounded waves avoid submitting all API calls after the target is met.
        with ThreadPoolExecutor(max_workers=llm_workers) as ex:
            for offset in range(0,len(pool),batch_size*llm_workers):
                wave=pool[offset:offset+batch_size*llm_workers]
                for scores in ex.map(review_job,[wave[i:i+batch_size] for i in range(0,len(wave),batch_size)]):
                    screened.update(scores); approved.update({d:v for d,v in scores.items() if v>=threshold})
                print(f'[Academic] screened {len(screened)} | {len(approved)}/{cap} qualified',flush=True)
                if len(approved)>=cap: break
        print(f'[Academic] round {rnd+1}: {raw_count} records | {len(found)} unique abstracts | {len(approved)} qualified',flush=True)
        if not opt.get('adaptive_query_expansion',True): break
    ranked=sorted((found[d] for d in approved),key=lambda p:(-approved[p['doi']],p['doi']))
    selected=[]; seen=set(); groups=[[p for p in ranked if d in p['directions']] for d in directions]
    while len(selected)<cap and any(groups):
        for g in groups:
            while g and g[0]['doi'] in seen: g.pop(0)
            if g and len(selected)<cap:
                p=g.pop(0); seen.add(p['doi']); selected.append(p)
    extra=[]; metadata=[]
    for i,p in enumerate(selected,7):
        eid=f'E{i:03d}'; p.update(id=eid,score=approved[p['doi']],source_type='abstract'); s=p['abstract']
        for j,k in enumerate(range(0,len(s),1000),1): extra.append({'id':f'{eid}-p0-c{j}','paper':eid,'file':p['title'],'text':s[max(0,k-150):k+1000],'source_type':'abstract','doi':p['doi'],'url':p['url']})
        metadata.append(f"{eid}\n文献名称：{p['title']}\n作者：{p['authors']}\n来源：{p['venue']}\n年份：{p['year']}\nDOI或公开链接：{p['url']}\n证据范围：公开摘要")
    write(out/'academic_search.json',{'queries':logs,'raw_count':raw_count,'unique_with_abstract':len(found),'qualified_count':len(approved),'screened_count':len(screened),'selected':selected,'external_count':len(selected),'seed_count':len(seed),'target_total':cap+len(seed),'target_met':len(selected)==cap})
    if len(selected)<cap and opt.get('strict_target',True): raise RuntimeError(f'外部合格文献仅{len(selected)}/{cap}，已保存检索记录；请扩大检索预算或调整配置')
    return extra,'\n'.join(metadata)
