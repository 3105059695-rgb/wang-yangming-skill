"""Render v4 native source files and a self-contained portable knowledge book."""
from pathlib import Path
import hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
VERSION='4.0.0'
def sha(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def unlink_local(text): return re.sub(r'\[([^\]]+)\]\((?!https?://)[^)]+\)',r'\1',text)
def read(rel): return (ROOT/rel).read_text(encoding='utf-8')
def source_text(c):
    text=f"# {c['key']} {c['title']}\n\n[固定公开原文]({c['source_url']})\n\n"
    text+=c.get('scope_note','固定公开版本完整编号单元。')+'\n\n'
    if sha('\n\n'.join(c['original_paragraphs']))!=c['original_sha256']: raise ValueError('Source changed: '+c['key'])
    text+='## 完整原文\n\n'+'\n\n'.join(c['original_paragraphs'])+'\n\n## 编者解读与运用\n\n'
    for key,label in [('context','原问与处境'),('distinction','帮助分清什么'),('decision_use','如何参与判断'),('counter_case','反用与限制'),('voice_note','语气与教法')]:
        if c.get(key): text+=f"**{label}：**{c[key]}\n\n"
    for item in c.get('additional_readings',[]):
        parts=[item.get(k,'') for k in ['distinction','counter_case','voice_note'] if item.get(k)]
        if parts: text+='**同一原段的补充解读：**'+'\n\n'.join(parts)+'\n\n'
    text+='## 对读定位与文字说明\n\n'
    evidence=c.get('uploaded_evidence',[])
    if not evidence: text+='本单元来自另外补充的公开原典；不冒称由上传 PDF 提取。\n\n'
    for e in evidence:
        loc=e.get('unit_or_page',e.get('locator',''))
        text+=f"- {e.get('book','')} {loc}；核对状态：{'已核记录' if e.get('checked') else '待核'}。"
        if e.get('anchor'): text+='古文定位短语：'+e['anchor']+'。'
        text+=e.get('note','')+'\n'
    for e in c.get('external_evidence',[]): text+=f"\n[补充版本]({e['url']})：{e.get('note','')}\n"
    for note in c.get('textual_notes',[]): text+='\n'+note+'\n'
    if c.get('legacy_crosscheck'): text+='\n早期对读说明：'+json.dumps(c['legacy_crosscheck'],ensure_ascii=False)+'\n'
    if c.get('recorder_afterword'): text+='\n## 钱德洪后跋（记录者文字，非王阳明自述）\n\n'+c['recorder_afterword']+'\n'
    return text
def outputs():
    lib=json.loads(read('references/library.json')); units=lib['units']; topics=lib['topics']
    generated={f"references/units/{c['key']}.md":source_text(c) for c in units}
    idx='# 资料入口：先辨问题，再读主题与原段\n\n'
    idx+=f"本库含{len(topics)}篇原创主题综合、{len(units)}个去重原典单元。包括《传习录》上中下卷选段和《大学问》完整六问；卷中单元是完整编号分段，不能称完整书信。它不是王阳明全集，也不宣称思想已被穷尽。\n\n"
    idx+='首次读思想全体，再选最相关的一两主题，读完所选原段与反用条件；不用把全库一次塞进来者的回答。主题中的 CX 编号是本库索引，B01–B08 是上传材料定位。单元去重，一段兼属几个主题仍只计一次。\n\n'
    order=['system','foundations','knowing','emotions','cultivation','relationships','voice','history']
    topicby={t['id']:t for t in topics}
    cues={'system':'初次使用；理解全体关系，避免只讲放下或立刻行动','foundations':'善意与有效、诚实与自我辩护、心意知物的关系','knowing':'学不会、缺知识、空想或盲动、质疑权威','emotions':'焦虑、悲伤、越省察越紧张、静坐与忙乱','cultivation':'立志、学不久、进退、对自己或别人要求过量','relationships':'照护、合作、嫉妒、亲近者不同意、责任冲突','voice':'如何追问、解释、承认未知、调整语气','history':'阅读来源、思想变化、小说对白及史实分歧'}
    idx+='| 眼前问题 | 读取主题 | 重点原段 |\n|---|---|---|\n'
    for k in order:
        t=topicby[k]
        links='、'.join(f"[{u}](units/{u}.md)" for u in t['source_keys'] if any(c['key']==u for c in units))
        idx+=f"| {cues[k]} | [{t['title']}](topics/{k}.md) | {links} |\n"
    idx+='\n## 全部原典定位\n\n'
    for c in units: idx+=f"- [{c['key']} {c['title']}](units/{c['key']}.md)"+('（旧号 '+c['legacy_id']+'）' if c.get('legacy_id') else '')+'\n'
    idx+='\n## 引用与判断的限度\n\n原文采用固定公开转录，上传古文用于对读；它们不是影印校勘定本。遇疑字依版本说明，避免拿疑字作权威断语。每次古人部分标白话转述，现代做法另说，短引与出处放文末。若主题与原段不支持当前问题，承认这个缺口，不添造古人问答。\n'
    generated['references/library-index.md']=idx
    core=re.sub(r'^---\n.*?\n---\n','',read('SKILL.md'),count=1,flags=re.S).strip()
    portable_reading='''## 开始前实际读取的材料

本文件已包含八个主题和全部52个去重原典单元，不依赖仓库外部文件。先读后面的“思想全体与一事中的条理”，再按“资料入口”选择相关主题和完整原段；已读且仍在上下文中的内容不重复读。改变话题或条件时查看反用条件。若平台截断、仅能检索局部，必须实际取到所需完整原段；取不到就说明，不假称已经看全。

主题说明、原问条件和完整回答要先参与判断，再取一处向来者讲透。原文可按 CX 编号或 DQ-FULL 查找；引用本文件实际文字及固定出处。新问题不限于已有20例。正文示例均为虚构，历史证据的现代运用不冒称古人已有。

选择道路另有本文件“辨事与抉择”，语气见“语气与教法证据”，接续本人经历见“记忆规则”及其实际提供的记录。单个完整编号分段不等于整封信，公开转录也不等于完成影印校勘。

'''
    start=core.index('## 开始前实际读取的材料'); end=core.index('### 原典怎样真正参与这次回答')
    core=core[:start]+portable_reading+core[end:]
    core=unlink_local(core)
    direct='请按以下材料与我交谈，直接回应我的事，不要只总结或点评文件。\n\n'+core+'\n\n---\n\n'+unlink_local(idx)
    for k in order:
        t=topicby[k]; body=read(f'references/topics/{k}.md').strip()
        if not body.startswith('# '): body='# '+t['title']+'\n\n'+body
        direct+='\n\n---\n\n'+unlink_local(body)
    for c in units: direct+='\n\n---\n\n'+generated[f"references/units/{c['key']}.md"]
    for rel in ['references/judgment.md','references/memory.md','templates/我的记录.md']:
        direct+='\n\n---\n\n'+unlink_local(read(rel).strip())
    direct+='\n\n收到后接我的话；我尚未讲事时，只问眼下最想谈的一件事。不汇报准备过程。\n'
    full='# 王阳明：完整指南 v4.0\n\n这是可直接上传的完整材料包。内容与“直接开始”一致；篇幅较长，平台是否完整读取需在使用时核实，不宣称豆包已实机验证。\n\n'+direct
    generated.update({'prompts/直接开始.txt':direct,'prompts/完整指南.md':full,'prompts/完整指南.txt':full,'prompts/启动提示词.txt':'请读取我上传的《王阳明：完整指南 v4.0》，按其中的开导方式回应我的具体困惑。先读思想全体，再按问题读相关主题和完整原典；不要只靠摘要。正文的古人部分标“白话转述”，现代建议另说，古文和出处放文末。一次讲清一个核心区别，给一个优先可做的行动；保留真实条件，不把困难都归因于心态。若没有读到需要的原段，请直说。现在我想谈的是：\n【在这里写你的事】\n'})
    return generated
def main():
    generated=outputs()
    for rel,text in generated.items():
        p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    lib=json.loads(read('references/library.json'))
    inputs=['SKILL.md','references/library.json','references/judgment.md','references/memory.md']+[f"references/topics/{t['id']}.md" for t in lib['topics']]
    manifest={'version':VERSION,'hash_normalization':'UTF-8; universal-newline text read (LF)','source_units':len(lib['units']),'topics':len(lib['topics']),'original_characters':sum(len('\n\n'.join(c['original_paragraphs'])) for c in lib['units']),'sha256':{rel:sha(read(rel)) for rel in inputs+list(generated)}}
    (ROOT/'docs/build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'version':VERSION,'source_units':manifest['source_units'],'topics':manifest['topics'],'direct_chars':len(generated['prompts/直接开始.txt']),'original_characters':manifest['original_characters']},ensure_ascii=False))
if __name__=='__main__': main()
