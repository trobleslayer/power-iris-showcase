Power-IRIS V3 交互式展示层
将本目录所有文件（包括 .streamlit）复制到现有 Power-IRIS 根目录，先备份旧 app.py。
python -m pip install -r requirements_ui.txt
python -m streamlit run app.py
浏览器 http://localhost:8501，左侧选择历史成果目录。
07 自主科研工作台可配置并启动 live/replay，使用现有 run.py --config 接口。
Live 需在启动界面的同一终端设置已有 API 环境变量；不在界面保存密钥。
Replay 需要完全匹配的缓存，修改参数可能导致缓存缺失。
停止任务保留已写入的文件，但不是断点续跑。任务控制依赖当前浏览器会话。
03 科研空间支持框选或点击候选点，联动详情及原文证据，也可下拉选择。
PPT 可设置 http://localhost:8501 超链接。展示模式不调用 API。
尚未实现单条假设定向再生成、实时逐次 API 事件、证据双向网络；现有监控读取真实日志。
内部评分不是独立验证，参考引导是事后重构。不要覆盖原 run.py/core.py/config.json。
