"""Render immutable synthetic dialogue outputs and literal quote checks."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def main():
    lib=json.loads((ROOT/'references/library.json').read_text(encoding='utf-8'))
    originals={c['key']:'\n\n'.join(c['original_paragraphs']) for c in lib['units']}
    title={'cooperation':'合作、嫉妒与实际分配不公','learning':'学不会，还是已经会了却不敢交','selfwatch':'过度反省与具体说谎的区别','portable':'完整附件：感激父母与选择不同道路'}
    intro='''# v4 原样试答与观察

这些是合成来者情境下模型的实际输出，不是真实使用者经历，也没有经过改稿。三个新上下文读取文件夹入口，各先答一轮，再收到此前不可见的新事实；第四个新上下文只读取完整复制入口。使用当前默认协作模型，未取得可复现的精确模型快照；没有在豆包账号实际运行。

## 这次实际观察到什么

- 合作组首答用新增卷中142、143条说明共同成事与求不可替代的区别；新增擅改分配的事实后，改为维护约定，并算出双方原各10000元、改后8500/11500元，各相差1500元。没有把不公平继续解释成来者嫉妒。
- 学习组用新增136条说明问思辨也是实践，先处理知识缺口；来者承认已能改对后，明确收回旧判断，转为交付现有成果并暂缓另买课。
- 反省组用新增204条说明不必另设一颗监督之心；来者随后说出实际谎话，仍要求更正事实，同时保留拒绝帮忙的自由，没有把放松变成免除责任。
- 完整附件组连续读完94,106字符，只从该入口作答，采用新增178条区分感激与听从某项意见；保留原来的学术论辩背景，没有把它编成阳明劝人离家。现代建议依据父母身体、小店人手与既有生活费条件，说明照料条件变化后需再议。

这些结果支持新增材料可以影响判断，但不是证明所有新问题都能解决。三组首答围绕不同原段展开，续答随事实改变；未重跑20题、未做跨模型或长期效果比较。

## 仍有的表达问题

合作组首答把一处古文分号收为句号，用字没变，但不满足逐字符照引；反省组的节引加了外层引号，须将排版引号与原段字符区分。原输出照存，精确检查见[引文记录](../evals/v4-dialogue-checks.json)。首答少量句子仍有解释腔；一次能说清并不证明已稳定形成王阳明式现代口吻，也不证明来者听后一定减轻痛苦。

本地构建与文本身份核验见[构建清单](build-manifest.json)；[原典核对](../evals/v4-source-checks.json)仅核选定单元对公开转录，不是整套思想完整性的证书。

---

'''
    out=intro;checks=[]
    for key in title:
        p=ROOT/f'evals/transcripts/v4-{key}.json'
        if not p.exists(): raise FileNotFoundError(p)
        d=json.loads(p.read_text(encoding='utf-8-sig'))
        out+='## '+title[key]+'\n\n[原始记录](../evals/transcripts/'+p.name+')\n\n'
        for i,msg in enumerate(d['messages']):
            out+='### '+('来者' if msg['role']=='user' else '实际答复')+'\n\n'+msg['content']+'\n\n'
            if msg['role']!='assistant': continue
            body=msg['content'].split('**原文与出处**')[0]
            result={'file':p.name,'message_index':i,'body_cjk':len(re.findall('[\u3400-\u9fff]',body)),'quotes':[]}
            for q in re.findall(r'^>\s*(.+)$',msg['content'],re.M):
                exact=[k for k,s in originals.items() if q in s]
                unwrapped=q[1:-1] if q.startswith('「') and q.endswith('」') else q
                typographic=[k for k,s in originals.items() if unwrapped in s]
                punctuation=[k for k,s in originals.items() if unwrapped.endswith('。') and unwrapped[:-1]+'；' in s]
                result['quotes'].append({'quote':q,'literal_match':exact,'match_without_added_outer_quotes':typographic,'terminal_period_in_place_of_semicolon':punctuation})
            checks.append(result)
    (ROOT/'docs/v4-dialogues.md').write_text(out,encoding='utf-8')
    (ROOT/'evals/v4-dialogue-checks.json').write_text(json.dumps({'version':'4.0.0','scope':'literal quotations and body lengths; no automatic rating of understanding or relief','checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Rendered',len(checks),'unaltered assistant replies')
if __name__=='__main__': main()
