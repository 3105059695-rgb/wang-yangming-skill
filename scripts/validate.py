"""Validate artifacts and evidence identity; does not score understanding or comfort."""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import sys
from build import outputs, sha

ROOT = Path(__file__).resolve().parents[1]
errors=[]
required=['SKILL.md','README.md','LICENSE','references/source-cards.json','references/runtime-sources.md',
          'prompts/直接开始.txt','prompts/完整指南.md','prompts/完整指南.txt','docs/reading-coverage.json',
          'docs/evaluation.md','docs/material-use.md','docs/build-manifest.json','templates/我的记录.md']
for rel in required:
    if not (ROOT/rel).is_file():
        errors.append('Missing: '+rel)
files=[p for p in ROOT.rglob('*') if p.is_file() and not {'.git','__pycache__'}.intersection(p.parts)]
links=0
for path in files:
    if path.suffix.lower() in {'.pdf','.mobi','.epub','.zip'}:
        errors.append('Unexpected book/archive: '+str(path.relative_to(ROOT)))
    if path.suffix not in {'.md','.txt','.json'}:
        continue
    text=path.read_text(encoding='utf-8-sig')
    if re.search(r'[A-Za-z]:[\\/]Users[\\/]|D:[\\/]蒸馏',text):
        errors.append('Private machine path: '+str(path.relative_to(ROOT)))
    if path.suffix!='.md':
        continue
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if target.startswith(('https://','http://','#','mailto:')):
            continue
        dest=(path.parent/unquote(target.split('#',1)[0].strip('<>'))).resolve()
        links+=1
        if not dest.is_relative_to(ROOT) or not dest.exists():
            errors.append(f'Broken link: {path.relative_to(ROOT)} -> {target}')
try:
    generated=outputs()
    for rel,expected in generated.items():
        if (ROOT/rel).read_text(encoding='utf-8')!=expected:
            errors.append('Outdated generated artifact: '+rel)
except Exception as e:
    errors.append('Build consistency: '+str(e))
cards=json.loads((ROOT/'references/source-cards.json').read_text(encoding='utf-8'))
if len(cards)!=18 or len({c['id'] for c in cards})!=18:
    errors.append('Expected 18 unique source cards')
for c in cards:
    if not c['uploaded_material_locators'] or not c['context'] or not c['reverse_or_limit']:
        errors.append('Missing context or provenance: '+c['id'])
manifest=json.loads((ROOT/'docs/build-manifest.json').read_text(encoding='utf-8'))
for rel,expected in manifest['sha256'].items():
    if sha((ROOT/rel).read_text(encoding='utf-8'))!=expected:
        errors.append('Build manifest mismatch: '+rel)
legacy=sha((ROOT/'evals/legacy/v2-prompt.txt').read_text(encoding='utf-8'))
current=sha((ROOT/'prompts/直接开始.txt').read_text(encoding='utf-8'))
initial_v3=sha((ROOT/'evals/legacy/v3-initial-prompt.txt').read_text(encoding='utf-8'))
checked=[]
for path in (ROOT/'evals/transcripts').glob('*.json'):
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    if path.name.startswith('candidate-') and data.get('candidate_prompt_sha256_lf')!=legacy:
        errors.append('v2 evidence mismatch: '+path.name)
    if path.name.startswith('v3-'):
        version=data.get('version')
        expected_prompt={'3.0.0':initial_v3,'3.0.1':sha((ROOT/'evals/legacy/v3.0.1-prompt.txt').read_text(encoding='utf-8'))}.get(version,current)
        if data.get('entry')=='copy':
            if data.get('candidate_prompt_sha256_lf')!=expected_prompt:
                errors.append('v3 copy prompt mismatch: '+path.name)
        elif data.get('entry')=='native':
            loaded=data.get('loaded_files',{})
            for rel in ['SKILL.md','references/runtime-sources.md']:
                if rel not in loaded:
                    errors.append('Missing required native source: '+rel)
            for rel,loaded_sha in loaded.items():
                source=ROOT/rel
                if version=='3.0.0' and rel=='SKILL.md':
                    source=ROOT/'evals/legacy/v3-initial-SKILL.txt'
                if loaded_sha!=sha(source.read_text(encoding='utf-8')):
                    errors.append('v3 native input mismatch: '+path.name+' '+rel)
        else:
            errors.append('Missing entry type: '+path.name)
        if version not in {'3.0.0','3.0.1','3.1.0'}:
            errors.append('Missing evidence version: '+path.name)
    messages=data.get('messages',[])
    if not messages or messages[-1].get('role')!='assistant':
        errors.append('Incomplete dialogue: '+path.name)
    checked.append(path.name)
coverage=json.loads((ROOT/'docs/reading-coverage.json').read_text(encoding='utf-8-sig'))
if coverage['total_chunks']!=coverage['read_chunks'] or coverage['errors']:
    errors.append('Outstanding reading coverage records')
template=(ROOT/'templates/我的记录.md').read_text(encoding='utf-8')
if '记录版本：0000' not in template or '尚无个人经历' not in template:
    errors.append('Personal template not blank')
print(json.dumps({'scope':'build identity, full source units and quote substrings, versioned evidence, links, blank template, coverage counts',
                  'files':len(files),'local_links_checked':links,'source_units':len(cards),
                  'transcript_files_checked':checked,'direct_sha256_lf':current,
                  'errors':errors,'passed':not errors},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
