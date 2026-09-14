"""Render saved model outputs for reading; never edits the underlying transcripts."""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
titles={'relationship':'分手、悲伤与尚未归还的欠款','decision':'转行机会与现实余量','knowledge':'知行、工作条件与诚实','recheck':'3.0.1复试：已完成部分、余量与原典用字'}
parts=['# v3.0系列历史试答全文\n\n以下答复属于3.0.0/3.0.1，不是3.1版测试，也不作为新版排版示范。它们由新上下文执行者按当时入口实际生成，未润色或删句。情境为虚构，不能作为使用者经历或真实效果反馈。来源JSON保留输入文件摘要；这份页面只改善阅读排版。\n']
stats=[]
for name,title in titles.items():
    p=ROOT/f'evals/transcripts/v3-{name}.json'
    data=json.loads(p.read_text(encoding='utf-8-sig'))
    parts.append(f"## {title}\n\n受测版本：{data['version']}。[原始记录](../evals/transcripts/v3-{name}.json)\n")
    n=0
    counts=[]
    for m in data['messages']:
        if m['role']=='user':
            n+=1
            parts.append(f'### 第{n}轮\n\n**虚构用户：**\n\n'+m['content']+'\n')
        elif m['role']=='assistant':
            parts.append('**实际答复：**\n\n'+m['content']+'\n')
            counts.append(len(re.findall(r'[\u3400-\u9fff]',m['content'])))
    stats.append({'case':name,'assistant_turns':len(counts),'cjk_chars_per_answer_including_citation':counts})
(ROOT/'docs/actual-dialogues.md').write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))
