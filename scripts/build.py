"""Build portable entries from the same core and 18 complete source units."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def unlink_local(text):
    return re.sub(r'\[([^\]]+)\]\((?!https?://)[^)]+\)', r'\1', text)

def outputs():
    cards = json.loads((ROOT/'references/source-cards.json').read_text(encoding='utf-8'))
    runtime = """# 本次对话可直接使用的原典

这是18则完整原典单元，不是八本现代书的全文。古文使用公开转录以便分发，上传书页用于对读；现代译注不随包复制。条号依本包固定公开版本，不同版本编次可能不同。每则的处境、现代运用及换方条件是编者提炼，并非古人原话。

先匹配眼前事实，再读完整问答；不能只抽一句话。选定的古代指点若不适合现在的人，就换方。下列卡号只用于核对，不必在普通回答中显示。

"""
    for c in cards:
        original='\n\n'.join(c['original_paragraphs'])
        if sha(original)!=c['original_sha256']:
            raise ValueError('Original changed: '+c['id'])
        if any(e not in original for e in c['excerpts']):
            raise ValueError('Unmatched quotation: '+c['id'])
        runtime += f"## {c['id']} {c['title']}\n\n《传习录》{c['volume']}第{c['number']}条。[固定原文]({c['source_url']})\n\n"
        runtime += '### 完整原典单元\n\n'+original+'\n\n'
        runtime += f"**原问处境：**{c['context']}\n\n**现代运用：**{c['modern_application']}\n\n**何时换方或停用：**{c['reverse_or_limit']}\n\n"
        runtime += '**上传材料对读定位：**'+'；'.join(c['uploaded_material_locators'])+'。页号为PDF物理页，电子书另标单元。\n\n'
        if c['id'] in {'S09','S13','S16','S18'}:
            runtime += '**版本差异：**'+c['uploaded_crosscheck']['variant_note']+'\n\n'
    source=(ROOT/'SKILL.md').read_text(encoding='utf-8')
    core=re.sub(r'^---\n.*?\n---\n','',source,count=1,flags=re.S).strip()
    core=core.replace('首次回应一个完整困境前，读取[运行原典](references/runtime-sources.md)。','首次回应一个完整困境前，读本文件后半部已附的“本次对话可直接使用的原典”。')
    core=core.replace('读取失败，明确说当前未读到依据，不把通用知识包装成已经核过原文。','如果平台截断使你未读到所需原典，明确说明，不把通用知识包装成已经核过原文。')
    core=core.replace('接续经历时读取[记忆规则](references/memory.md)及实际记录，查资料来历时看[来源说明](references/source-map.md)。','接续经历以本文件的“接续个人记录”规则及本人实际给出的记录为准；其他材料在完整指南中可查。')
    core=unlink_local(core)
    direct='请按以下方式与我交谈，直接回应我的事，不要只总结或点评这些文字。\n\n'+core+'\n\n---\n\n'+runtime
    direct+='\n收到后直接接我的话；若我尚未讲事，只问我眼下最想谈的一件事。不汇报准备过程。\n'
    full='# 王阳明：完整指南 v3.1\n\n核心规则和18则原典与“直接开始”完全相同。补充材料用于进一步查证、择路和接续记录。演示均为虚构情境。\n\n'+direct
    for name in ['philosophy.md','judgment.md','voice.md','primary-dialogues.md','long-dialogues.md','memory.md','source-map.md']:
        full+='\n\n---\n\n'+unlink_local((ROOT/'references'/name).read_text(encoding='utf-8').strip())
    full+='\n\n---\n\n'+(ROOT/'templates/我的记录.md').read_text(encoding='utf-8')
    return {'references/runtime-sources.md':runtime,'prompts/直接开始.txt':direct,'prompts/完整指南.md':full,'prompts/完整指南.txt':full}

if __name__=='__main__':
    generated=outputs()
    for rel,body in generated.items():
        (ROOT/rel).parent.mkdir(exist_ok=True,parents=True)
        (ROOT/rel).write_text(body,encoding='utf-8')
    manifest={'version':'3.1.0','hash_normalization':'UTF-8; universal-newline text read (LF)',
              'source_units':18,'sha256':{rel:sha((ROOT/rel).read_text(encoding='utf-8')) for rel in ['SKILL.md','references/source-cards.json',*generated]}}
    (ROOT/'docs/build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'version':'3.1.0','source_units':18,'direct_chars':len(generated['prompts/直接开始.txt']),'direct_sha256_lf':manifest['sha256']['prompts/直接开始.txt']},ensure_ascii=False))
