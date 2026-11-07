"""Merge reviewed project progress and compile project facts + atomic evidence together.

No background watcher and no raw-OCR auto approval. Career OS calls this after reading
new user evidence. Future batches must provide an exact prior value for replacement.
Stdlib only; private paths remain private. Run --help for usage.
"""
from pathlib import Path
import argparse, csv, json, hashlib, copy, tempfile, os, re, io, fcntl
from contextlib import contextmanager
STAGES = {'documented_design': '方案已见', 'reported_milestone': '周报里程碑', 'verified_release': '已核实发布', 'verified_result': '已核实效果'}

def safe_destination(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('destination must stay inside configured root')
    dest = root / rel
    for node in [dest, *dest.parents]:
        if node == root:
            break
        if node.is_symlink():
            raise ValueError('symlink destination rejected: ' + str(node))
    if not dest.resolve().is_relative_to(root):
        raise ValueError('destination escapes root')
    return dest

def atomic_text(path, text, root=None):
    path = Path(path)
    lexical_root = Path(root).absolute() if root else path.parent.absolute()
    path = safe_destination(lexical_root, path.absolute().relative_to(lexical_root))
    root = lexical_root.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.nia-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        safe_destination(root, path.relative_to(root))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def dump(path, obj):
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

@contextmanager
def store_lock(store):
    store = Path(store).absolute()
    lock = safe_destination(store.parent, store.name + '.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('store is busy; retry after current sync completes') from exc
        yield
    finally:
        os.close(fd)

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
    if not batch.get('updates'):
        raise ValueError('empty updates')
    changes = []
    for u in batch['updates']:
        if not u.get('capabilities'):
            raise ValueError('every project update must include atomic evidence')
        if u['project_id'] not in projects:
            raise ValueError('unknown project: ' + u['project_id'])
        p = projects[u['project_id']]
        update_sources = u.get('source_ids')
        if update_sources is None:
            if len(batch['updates']) != 1:
                raise ValueError('multi-project batch needs per-update source_ids')
            update_sources = batch['source_ids']
        if not update_sources or not set(update_sources) <= set(batch['source_ids']):
            raise ValueError('update sources must come from reviewed batch')
        for k, change in u.get('fields', {}).items():
            if not k in {'status', 'baseline', 'actions', 'result', 'retrospective'}:
                raise ValueError('unsupported field')
            if not p[k] == change['previous']:
                raise ValueError('stale/conflicting scalar; resolve explicitly')
            changes.append({'project_id': p['project_id'], 'field': k, 'old': p[k], 'new': change['value']})
            p[k] = change['value']
        for stream_update in u.get('streams', []):
            s = next((x for x in p['streams'] if x['id'] == stream_update['id']), None)
            if s is None:
                raise ValueError('unknown stream: ' + stream_update['id'])
            stream_sources = stream_update.get('source_ids')
            if stream_sources is None:
                if len(u.get('streams', [])) > 1 and len(update_sources) > 1:
                    raise ValueError('multi-source streams need explicit source_ids')
                stream_sources = update_sources
            if not stream_sources or not set(stream_sources) <= set(update_sources):
                raise ValueError('stream source outside project update')
            for k, change in stream_update['fields'].items():
                if not k in {'status', 'target', 'dependency', 'acceptance'}:
                    raise ValueError('invalid input')
                if not s[k] == change['previous']:
                    raise ValueError('stale stream state')
                changes.append({'project_id': p['project_id'], 'stream': s['id'], 'field': k, 'old': s[k], 'new': change['value']})
                s[k] = change['value']
            s['source_ids'] = list(dict.fromkeys(s['source_ids'] + stream_sources))
        oldcaps = {c['id']: c for c in p['capabilities']}
        added = 0
        for cap in u['capabilities']:
            if not cap.get('source_ids') or not set(cap['source_ids']) <= set(update_sources):
                raise ValueError('capability source outside reviewed project update')
            cap = dict(cap, project_id=p['project_id'], level_change=0)
            if cap['id'] in oldcaps:
                if not cap == oldcaps[cap['id']]:
                    raise ValueError('new evidence needs a new dated capability evidence id')
            else:
                p['capabilities'].append(cap)
                oldcaps[cap['id']] = cap
                added += 1
        if not added:
            raise ValueError('progress needs new capability evidence')
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
    out = ['# {}｜当前事实与能力'.format(p['name']), '记录更新：{}；事实时点：{}'.format(p['recorded_at'], p['as_of']), '## 当前判断\n\n{}'.format(p['status']), '业务目标：{}'.format(p['purpose']), '个人责任：{}'.format(p['owner']), '## 工作流与验收', table(['工作流', '当前状态', '目标节点', '依赖与验收'], [[s['name'], s['status'], s['target'], s['dependency'] + '；' + s['acceptance'] + ' [' + '、'.join(s['source_ids']) + ']'] for s in p['streams']]), '## 业务基线与行动\n\n{}\n\n{}'.format(p['baseline'], p['actions']), '## 阶段结果与复盘\n\n{}\n\n{}'.format(p['result'], p['retrospective']), '## 自动计入的原子能力证据', table(['原子能力', '当前证据', '证据阶段'], [[c['name'], c['evidence'] + ' [' + '、'.join(c['source_ids']) + ']', STAGES[c['stage']]] for c in p['capabilities']]), '新增证据不自动提升能力等级；上线、效果、个人归因分别验收。']
    return '\n\n'.join(out) + '\n'

def compile_views(db, out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    validate(db)
    weekly = []
    caps = []
    outputs = {}
    for p in db['projects']:
        outputs[p['project_id'] + '.md'] = project_md(p)
        for s in p['streams']:
            weekly.append({'项目': p['name'], 'project_id': p['project_id'], '工作流': s['name'], 'workstream_id': s['id'], '事实时点': p['as_of'], '当前状态': s['status'], '目标节点': s['target'], '依赖': s['dependency'], '验收': s['acceptance'], '来源': '、'.join(s['source_ids'])})
        for c in p['capabilities']:
            caps.append({'项目': p['name'], 'project_id': p['project_id'], '原子能力': c['name'], 'evidence_id': c['id'], 'Career_OS能力': c['macro'], '证据': c['evidence'], '阶段': c['stage'], '等级调整': 0, '来源': '、'.join(c['source_ids'])})
    for name, rows in [('周进度表.csv', weekly), ('原子能力证据.csv', caps)]:
        f = io.StringIO(newline='')
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        for row in rows:
            safe = {}
            for key, value in row.items():
                text = str(value)
                safe[key] = "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')) else value
            w.writerow(safe)
        outputs[name] = '\ufeff' + f.getvalue()
    outputs['项目总览.md'] = '# 当前项目总览\n\n' + table(['项目', '当前状态', '原子能力证据'], [[p['name'], p['status'], len(p['capabilities'])] for p in db['projects']]) + '\n'
    for name in outputs:
        safe_destination(out, name)
    for name, text in outputs.items():
        atomic_text(out / name, text, root=out)
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
            old = '# {}｜项目事实底稿\n\n'.format(p['name']) + block + '\n'
    if old.startswith('---\n'):
        front, body = old[4:].split('\n---\n', 1)
        for k, v in {'as_of': p['as_of'], 'status': p['status'], 'result_boundary': p['result']}.items():
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
        dest = safe_destination(vault, rel)
        if not dest.resolve().is_relative_to(vault):
            raise ValueError('invalid input')
        before = dest.read_text(encoding='utf-8') if dest.exists() else ''
        after = managed_note(before, p)
        if before != after:
            updates.append((dest, before, after))
    backup = safe_destination(vault, '数据/项目更新备份')
    backup.mkdir(parents=True, exist_ok=True)
    for dest, before, after in updates:
        if before:
            atomic_text(backup / (hashlib.sha256(before.encode()).hexdigest() + '.md'), before, root=vault)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if (dest.read_text(encoding='utf-8') if dest.exists() else '') != before:
            raise ValueError('note changed concurrently: ' + str(dest))
        atomic_text(dest, after, root=vault)
    return len(updates)

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--store', required=True)
    a.add_argument('--input')
    a.add_argument('--out', required=True)
    a.add_argument('--vault')
    a.add_argument('--dry-run', action='store_true')
    args = a.parse_args()
    with store_lock(args.store):
        db = json.loads(Path(args.store).read_text(encoding='utf-8'))
        changed = False
        if args.input:
            db, changed = merge(db, json.loads(Path(args.input).read_text(encoding='utf-8')))
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
    try:
        main()
    except (ValueError, KeyError) as exc:
        raise SystemExit('Invalid evidence: ' + str(exc))
