# Power-IRIS
面向断面潮流控制科研假设生成。独立轻量实现，原始IRIS代码保留在 upstream/，不依赖其Web服务。参考 https://arxiv.org/html/2504.16728v2 （三智能体、UCT、反馈迭代）。本实现使用局部全文BM25召回+LLM重排，而非原论文ScholarQA在线检索；不等价于原论文完整复现。方向由初赛主题确定，不把初赛假设文本传入生成器。

## Windows PowerShell / Python 3.11 或 3.12
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py --mode index --out outputs/index
python run.py --mode baseline --out outputs/baseline
```
基准模式逐字节复制原初赛结果，只用于核对格式，绝非模型生成。
在 config.json 中填写 retrieval 和 ideation 的 base_url（兼容 OpenAI Chat Completions 接口，一般以 /v1 结尾）及实际购买的 model 名称。供应商必须支持 JSON object 响应格式。然后在当前 PowerShell 设置：
```
$env:RETRIEVAL_API_KEY='你的第一个key'
$env:IDEATION_API_KEY='你的第二个key'
python run.py --mode live --out outputs/live
python run.py --mode replay --out outputs/replay
```
Linux/macOS 使用 export 设置同名环境变量。不要提交密钥。默认配置 6 个初始节点+12次细化，每节点2次检索调用、1次生成、1次评审，另最多6次材料总结，共最多78个逻辑调用（重试另计）。先将 refinements 改为0测试。cache/ 保存成功的响应，重复请求复用；replay 必须保持相同配置及缓存，否则报错，不会调用网络。温度0并不保证供应商重新生成完全一致，缓存才提供响应级重放。更改配置可改变结果。没有API key不能验证实际生成质量。

## 文件
- data/：原始6篇PDF、初赛JSON、初赛TXT。原始TXT只提取书目元数据进入生成。
- power_iris/core.py：PDF抽取、BM25、API缓存、树节点。
- run.py：两模型三角色编排、证据逐字核验、UCT树搜索（每节点两种细化分支、按方向选优）、输出。
- outputs/live/：chunks.json、tree.json、selected_reviews.json、科研假设提交.json、科研材料提交.txt、manifest.json。
- upstream/：原始上传代码，仅供参考。

## 局限与验证
仅检索固定本地全文，不进行开放互联网新论文检索；新增论文需扩展 corpus() 的编号映射和书目元数据。中文PDF抽取质量需要人工复核。引用逐字存在不表示支持推论。评审默认复用生成模型，不是独立专家；分数不是仿真性能。按六方向选优减少主题重叠，但不保证语义不重复。尚未接入潮流仿真及动态仿真，不宣称实验已完成。真实API调用未测试。原始数据按用户提供保留，外发前核查版权及竞赛规则。
