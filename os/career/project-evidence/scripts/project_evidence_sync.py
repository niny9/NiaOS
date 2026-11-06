"""Merge reviewed project progress and compile project facts + atomic evidence together.

No background watcher and no raw-OCR auto approval. Career OS calls this after reading
new user evidence. Future batches must provide an exact prior value for replacement.
Stdlib only; private paths remain private. Run --help for usage.
"""
from pathlib import Path
import argparse, csv, json, hashlib, copy, tempfile, os, re
STAGES = {'documented_design': '方案已见', 'reported_milestone': '周报里程碑', 'verified_release': '已核实发布', 'verified_result': '已核实效果'}

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.nia-')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(raw)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def validate(db):
    if not db['projects']:
        raise ValueError('empty portfolio')
    source_ids = [s['id'] for s in db['sources']]
    if not len(source_ids) == len(set(source_ids)):
        raise ValueError('duplicate source id')
    project_ids = [p['project_id'] for p in db['projects']]
    if not len(project_ids) == len(set(project_ids)):
        raise ValueError('duplicate project id')
    for p in db['projects']:
        if not re.fullmatch('[A-Za-z0-9_-]+', p['project_id']):
            raise ValueError('unsafe project id')
        if not p['streams']:
            raise ValueError('project needs workstreams')
        if not p['capabilities']:
            raise ValueError('project progress requires atomic capability mapping')
        ids = [s['id'] for s in p['streams']]
        if not len(ids) == len(set(ids)):
            raise ValueError('invalid input')
        caps = [c['id'] for c in p['capabilities']]
        if not len(caps) == len(set(caps)):
            raise ValueError('invalid input')
        for row in p['streams'] + p['capabilities']:
            if not (row['source_ids'] and set(row['source_ids']) <= set(source_ids)):
                raise ValueError('unknown/missing source')
        if not all((c.get('project_id') == p['project_id'] for c in p['capabilities'])):
            raise ValueError('wrong capability project')
        if not all((c['level_change'] == 0 for c in p['capabilities'])):
            raise ValueError('evidence ingestion cannot increase levels')
        if not all((c['stage'] in STAGES for c in p['capabilities'])):
            raise ValueError('unsupported evidence stage')

def merge(db, batch):
    result = copy.deepcopy(db)
    digest = hashlib.sha256(json.dumps(batch, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if any((h.get('batch_hash') == digest for h in result['history'])):
        return (result, False)
    if not batch.get('reviewed') is True:
        raise ValueError('read source before merge')
    if not (batch.get('date') and batch.get('source_ids')):
        raise ValueError('dated source required')
    sources = {s['id']: s for s in result['sources']}
    for src in batch.get('sources', []):
        if src['id'] in sources:
            if not src == sources[src['id']]:
                raise ValueError('source id collision')
        else:
            result['sources'].append(src)
            sources[src['id']] = src
    if not set(batch['source_ids']) <= sources.keys():
        raise ValueError('invalid input')
    projects = {p['project_id']: p for p in result['projects']}
    changes = []
    for u in batch['updates']:
        if not u.get('capabilities'):
            raise ValueError('every project update must include atomic evidence')
        p = projects[u['project_id']]
        for k, change in u.get('fields', {}).items():
            if not k in {'status', 'baseline', 'actions', 'result', 'retrospective'}:
                raise ValueError('unsupported field')
            if not p[k] == change['previous']:
                raise ValueError('stale/conflicting scalar; resolve explicitly')
            changes.append({'project_id': p['project_id'], 'field': k, 'old': p[k], 'new': change['value']})
            p[k] = change['value']
        for stream_update in u.get('streams', []):
            s = next((x for x in p['streams'] if x['id'] == stream_update['id']))
            for k, change in stream_update['fields'].items():
                if not k in {'status', 'target', 'dependency', 'acceptance'}:
                    raise ValueError('invalid input')
                if not s[k] == change['previous']:
                    raise ValueError('stale stream state')
                changes.append({'project_id': p['project_id'], 'stream': s['id'], 'field': k, 'old': s[k], 'new': change['value']})
                s[k] = change['value']
            s['source_ids'] = list(dict.fromkeys(s['source_ids'] + batch['source_ids']))
        oldcaps = {c['id']: c for c in p['capabilities']}
        for cap in u['capabilities']:
            cap = dict(cap, project_id=p['project_id'], level_change=0)
            if cap['id'] in oldcaps:
                if not cap == oldcaps[cap['id']]:
                    raise ValueError('new evidence needs a new dated capability evidence id')
            else:
                p['capabilities'].append(cap)
        p['recorded_at'] = batch['date']
        p['as_of'] = batch.get('as_of', p['as_of'])
    result['history'].append({'date': batch['date'], 'batch_hash': digest, 'source_ids': batch['source_ids'], 'changes': changes})
    result['updated_at'] = batch['date']
    validate(result)
    return (result, True)

def table(headers, rows):

    def cell(x):
        return str(x).replace('|', '／').replace('\n', ' ')
    return '\n'.join(['|' + '|'.join(headers) + '|', '|' + '|'.join(('---' for _ in headers)) + '|'] + ['|' + '|'.join((cell(x) for x in row)) + '|' for row in rows])

def project_md(p):
    out = [f'# {p['name']}｜当前事实与能力', f'记录更新：{p['recorded_at']}；事实时点：{p['as_of']}', f'## 当前判断\n\n{p['status']}', f'业务目标：{p['purpose']}', f'个人责任：{p['owner']}', '## 工作流与验收', table(['工作流', '当前状态', '目标节点', '依赖与验收'], [[s['name'], s['status'], s['target'], s['dependency'] + '；' + s['acceptance'] + ' [' + '、'.join(s['source_ids']) + ']'] for s in p['streams']]), f'## 业务基线与行动\n\n{p['baseline']}\n\n{p['actions']}', f'## 阶段结果与复盘\n\n{p['result']}\n\n{p['retrospective']}', '## 自动计入的原子能力证据', table(['原子能力', '当前证据', '证据阶段'], [[c['name'], c['evidence'] + ' [' + '、'.join(c['source_ids']) + ']', STAGES[c['stage']]] for c in p['capabilities']]), '新增证据不自动提升能力等级；上线、效果、个人归因分别验收。']
    return '\n\n'.join(out) + '\n'

def compile_views(db, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    validate(db)
    weekly = []
    caps = []
    for p in db['projects']:
        (out / f'{p['project_id']}.md').write_text(project_md(p))
        for s in p['streams']:
            weekly.append({'项目': p['name'], 'project_id': p['project_id'], '工作流': s['name'], 'workstream_id': s['id'], '事实时点': p['as_of'], '当前状态': s['status'], '目标节点': s['target'], '依赖': s['dependency'], '验收': s['acceptance'], '来源': '、'.join(s['source_ids'])})
        for c in p['capabilities']:
            caps.append({'项目': p['name'], 'project_id': p['project_id'], '原子能力': c['name'], 'evidence_id': c['id'], 'Career_OS能力': c['macro'], '证据': c['evidence'], '阶段': c['stage'], '等级调整': 0, '来源': '、'.join(c['source_ids'])})
    for name, rows in [('周进度表.csv', weekly), ('原子能力证据.csv', caps)]:
        with (out / name).open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
    (out / '项目总览.md').write_text('# 当前项目总览\n\n' + table(['项目', '当前状态', '原子能力证据'], [[p['name'], p['status'], len(p['capabilities'])] for p in db['projects']]) + '\n')
    return {'projects': len(db['projects']), 'workstreams': len(weekly), 'atomic_evidence': len(caps)}

def managed_note(old, p):
    start = '<!-- NIA_PROJECT_CURRENT_START -->'
    end = '<!-- NIA_PROJECT_CURRENT_END -->'
    block = start + '\n' + project_md(p).split('\n', 1)[1] + '\n' + end
    if start in old:
        if not old.count(start) == old.count(end) == 1:
            raise ValueError('invalid input')
        old = re.sub(re.escape(start) + '.*?' + re.escape(end), lambda m: block, old, flags=re.S)
    else:
        match = re.search('^# .+$', old, re.M)
        if match:
            old = old[:match.end()] + '\n\n' + block + '\n\n## 历史记录（保留原始版本，当前状态见上方）\n' + old[match.end():]
        else:
            old = f'# {p['name']}｜项目事实底稿\n\n' + block + '\n'
    if old.startswith('---\n'):
        front, body = old[4:].split('\n---\n', 1)
        for k, v in {'as_of': p['recorded_at'], 'status': p['status'], 'result_boundary': p['result']}.items():
            if re.search('^' + k + ':', front, re.M):
                front = re.sub('^' + k + ':.*$', lambda m: k + ': ' + json.dumps(v, ensure_ascii=False), front, flags=re.M)
            else:
                front += '\n' + k + ': ' + json.dumps(v, ensure_ascii=False)
        old = '---\n' + front + '\n---\n' + body
    return old

def sync_vault(db, vault):
    vault = Path(vault).resolve()
    updates = []
    for p in db['projects']:
        rel = Path(p['vault_note'])
        if not (not rel.is_absolute() and '..' not in rel.parts):
            raise ValueError('invalid input')
        dest = vault / rel
        if not dest.resolve().is_relative_to(vault):
            raise ValueError('invalid input')
        before = dest.read_text() if dest.exists() else ''
        after = managed_note(before, p)
        if before != after:
            updates.append((dest, before, after))
    backup = vault / '数据/项目更新备份'
    backup.mkdir(parents=True, exist_ok=True)
    for dest, before, after in updates:
        if before:
            (backup / (hashlib.sha256(before.encode()).hexdigest() + '.md')).write_text(before)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(after)
    return len(updates)

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--store', required=True)
    a.add_argument('--input')
    a.add_argument('--out', required=True)
    a.add_argument('--vault')
    a.add_argument('--dry-run', action='store_true')
    args = a.parse_args()
    db = json.loads(Path(args.store).read_text())
    changed = False
    if args.input:
        db, changed = merge(db, json.loads(Path(args.input).read_text()))
    validate(db)
    if args.dry_run:
        print(json.dumps({'valid': True, 'would_change': changed}))
        return
    if changed:
        dump(args.store, db)
    stats = dict(compile_views(db, args.out), changed=changed)
    if args.vault:
        stats['vault_notes_updated'] = sync_vault(db, args.vault)
    print(json.dumps(stats))
if __name__ == '__main__':
    main()
