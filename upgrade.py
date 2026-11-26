from pathlib import Path
import json, shutil
root=Path(__file__).resolve().parent
p=root/'run.py'; c=root/'config.json'
s=p.read_text(encoding='utf-8-sig'); cfg=json.loads(c.read_text(encoding='utf-8-sig'))
if 'from literature_search import discover' in s: raise SystemExit('已升级，无需重复执行')
anchor='    rows = corpus(data)'
meta="    metadata = '\\n'.join(line.strip() for line in materials.splitlines() if re.match(r'^(E\\d+|文献名称：|作者：|来源：|年份：|DOI或公开链接：)',line.strip()))"
if s.count(anchor)!=1 or s.count(meta)!=1: raise SystemExit('run.py版本不匹配，未修改任何文件，请提供当前run.py')
s=s.replace('from power_iris.core import *','from power_iris.core import *\nfrom literature_search import discover',1)
s=s.replace(anchor,anchor+'''\n    external_metadata = ''\n    if cfg.get('academic_search', {}).get('enabled', False) and args.mode in ('live','replay'):\n        external_rows, external_metadata = discover(Client(cfg['retrieval'], cache, args.mode), cfg, cache, out, args.mode, rows)\n        rows.extend(external_rows)''',1)
s=s.replace(meta,meta+"\n    if external_metadata:\n        metadata += '\\n' + external_metadata",1)
# distinguish abstract evidence in generation and evaluation without replacing user rubric
s=s.replace('result = checked(a,EVIDENCE_PROMPT,','result = checked(a,EVIDENCE_PROMPT + "\\np0或source_type=abstract表示仅有公开摘要，不得推断全文细节。",',1)
s=s.replace('review = checked(b,REVIEW_PROMPT,','review = checked(b,REVIEW_PROMPT + "\\n摘要证据不得冒充全文或实验验证。",',1)
compile(s,str(p),'exec')
for f in (p,c):
    backup=f.with_name(f.name+'.pre_v4')
    if not backup.exists(): shutil.copy2(f,backup)
cfg.update(refinements=20,early_stop=False,academic_search={'enabled':True,'results_per_query':20,'max_external_papers':40})
p.write_text(s,encoding='utf-8'); c.write_text(json.dumps(cfg,ensure_ascii=False,indent=4),encoding='utf-8')
print('V4升级成功；原文件备份为 *.pre_v4')
