import re, shutil
from pathlib import Path

def seed_metadata(data):
    text=(data/'科研材料提交.txt').read_text(encoding='utf-8-sig')
    result=[]
    for block in re.split(r'(?m)^E\d+\s*$',text)[1:]:
        title=re.search(r'(?m)^文献名称：(.+)$',block)
        doi=re.search(r'https?://(?:dx\.)?doi\.org/([^\s]+)',block)
        if title: result.append({'title':title.group(1).strip(),'doi':doi.group(1).lower() if doi else ''})
    if len(result)!=6: raise ValueError('原始材料须包含6篇文献')
    return result

def preserve(data,out):
    for name in ('科研材料提交.txt','科研假设提交.json'):
        shutil.copyfile(data/name,out/('原始'+name))
