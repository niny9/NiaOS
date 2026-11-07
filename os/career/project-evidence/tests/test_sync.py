"""Portable ingestion checks. All new events are synthetic and stay in temp directories."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import ast
import csv
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/project_evidence_sync.py'
spec=importlib.util.spec_from_file_location('sync',SCRIPT)
sync=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.db=json.loads((ROOT/'portfolio.redacted.json').read_text())
  p=self.db['projects'][0]
  cap=copy.deepcopy(p['capabilities'][0]);cap.update(id='SYNTHETIC-NEW',source_ids=['SYNTHETIC-SOURCE'],evidence='synthetic test only')
  self.batch={'reviewed':True,'date':'2026-11-06','as_of':'2026-10-20','source_ids':['SYNTHETIC-SOURCE'],'sources':[{'id':'SYNTHETIC-SOURCE','type':'synthetic'}],
   'updates':[{'project_id':p['project_id'],'fields':{'status':{'previous':p['status'],'value':'synthetic new state'}},
    'streams':[{'id':p['streams'][0]['id'],'fields':{'target':{'previous':p['streams'][0]['target'],'value':'synthetic target'}}}], 'capabilities':[cap]}]}
 def test_portfolio_coverage(self):
  sync.validate(self.db)
  self.assertEqual([len(self.db['projects']),sum(len(p['streams']) for p in self.db['projects']),sum(len(p['capabilities']) for p in self.db['projects'])],[8,22,28])
  self.assertEqual([s['id'] for s in self.db['projects'][1]['streams'][:2]],['instant_use','my_jd_mindshare'])
 def test_merge_history_and_unchanged_input(self):
  before=copy.deepcopy(self.db);db,changed=sync.merge(self.db,self.batch)
  self.assertTrue(changed);self.assertEqual(self.db,before)
  self.assertEqual(db['projects'][0]['status'],'synthetic new state')
  self.assertEqual(db['projects'][0]['capabilities'][-1]['level_change'],0)
  self.assertEqual(len(db['history'][-1]['changes']),2)
 def test_recording_does_not_fabricate_event_date(self):
  db,_=sync.merge(self.db,self.batch)
  self.assertEqual(db['projects'][0]['as_of'],'2026-10-20')
  self.assertEqual(db['projects'][0]['recorded_at'],'2026-11-06')
  del self.batch['as_of'];db,_=sync.merge(self.db,self.batch)
  self.assertEqual(db['projects'][0]['as_of'],self.db['projects'][0]['as_of'])
 def test_duplicate_idempotence(self):
  db,_=sync.merge(self.db,self.batch);again,changed=sync.merge(db,self.batch)
  self.assertFalse(changed);self.assertEqual(again,db)
 def test_conflicting_prior_value_rejected(self):
  self.batch['updates'][0]['fields']['status']['previous']='stale'
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_unreviewed_batch_rejected(self):
  self.batch['reviewed']=False
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_progress_without_capability_rejected(self):
  self.batch['updates'][0]['capabilities']=[]
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_unknown_source_rejected(self):
  self.batch['source_ids']=['missing']
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_invalid_evidence_stage_rejected(self):
  self.batch['updates'][0]['capabilities'][0]['stage']='business_success'
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_source_and_capability_collisions_rejected(self):
  self.batch['sources']=[dict(self.db['sources'][0],review='changed')]
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
  self.setUp();self.batch['updates'][0]['capabilities'][0]['id']=self.db['projects'][0]['capabilities'][0]['id']
  with self.assertRaises(ValueError):sync.merge(self.db,self.batch)
 def test_unsafe_project_id_rejected(self):
  self.db['projects'][0]['project_id']='../escape'
  with self.assertRaises(ValueError):sync.validate(self.db)
 def test_vault_path_escape_rejected(self):
  self.db['projects'][0]['vault_note']='../escape.md'
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):sync.sync_vault(self.db,tmp)
 def test_compilation_and_history_idempotence(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'views';vault=root/'vault';vault.mkdir()
   dest=vault/self.db['projects'][0]['vault_note'];dest.parent.mkdir();dest.write_text('# Old\n\nHistorical content.\n')
   sync.compile_views(self.db,out);before={f.name:f.read_bytes() for f in out.iterdir()}
   sync.compile_views(self.db,out);self.assertEqual(before,{f.name:f.read_bytes() for f in out.iterdir()})
   self.assertEqual(sync.sync_vault(self.db,vault),8);self.assertEqual(sync.sync_vault(self.db,vault),0)
   self.assertIn('Historical content.',dest.read_text());self.assertEqual(len(list((vault/'数据/项目更新备份').glob('*.md'))),1)
 def test_cli_dry_run_no_write(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=root/'db.json';batch=root/'batch.json';out=root/'out'
   store.write_text(json.dumps(self.db));batch.write_text(json.dumps(self.batch));old=store.read_bytes()
   subprocess.run([sys.executable,str(SCRIPT),'--store',str(store),'--input',str(batch),'--out',str(out),'--dry-run'],capture_output=True,check=True)
   self.assertEqual(old,store.read_bytes());self.assertFalse(out.exists())
 def test_validation_stays_enabled_under_optimization(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=root/'db.json';self.db['projects'][0]['capabilities']=[];store.write_text(json.dumps(self.db))
   p=subprocess.run([sys.executable,'-O',str(SCRIPT),'--store',str(store),'--out',str(root/'out'),'--dry-run'],capture_output=True)
   self.assertNotEqual(p.returncode,0)
 def test_python310_grammar(self):
  ast.parse(SCRIPT.read_text(),feature_version=(3,10))
 def test_frontmatter_keeps_fact_date(self):
  p=copy.deepcopy(self.db['projects'][0]);p['as_of']='2026-10-20';p['recorded_at']='2026-11-06'
  text=sync.managed_note('---\nas_of: old\n---\n# Test\n',p)
  self.assertIn('as_of: "2026-10-20"',text)
 def test_csv_formula_is_text(self):
  self.db['projects'][0]['streams'][0]['status']='=1+1'
  with tempfile.TemporaryDirectory() as tmp:
   sync.compile_views(self.db,tmp)
   with (Path(tmp)/'周进度表.csv').open(encoding='utf-8-sig') as f:row=next(csv.DictReader(f))
   self.assertEqual(row['当前状态'],"'=1+1")
 def test_output_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);out=root/'out';out.mkdir();external=root/'keep';external.write_text('original')
   (out/'周进度表.csv').symlink_to(external)
   with self.assertRaises(ValueError):sync.compile_views(self.db,out)
   self.assertEqual(external.read_text(),'original')
 def test_backup_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);vault=root/'vault';vault.mkdir();(vault/'数据').mkdir();outside=root/'outside';outside.mkdir()
   (vault/'数据/项目更新备份').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):sync.sync_vault(self.db,vault)
   self.assertEqual(list(outside.iterdir()),[])
 def test_atomic_replace_failure_preserves_original(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'note.md';p.write_text('原始历史')
   with patch.object(sync.os,'replace',side_effect=OSError('simulated interruption')):
    with self.assertRaises(OSError):sync.atomic_text(p,'new')
   self.assertEqual(p.read_text(),'原始历史')
 def test_busy_store_rejects_second_writer(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'db.json';p.write_text(json.dumps(self.db));before=p.read_bytes()
   with sync.store_lock(p):
    result=subprocess.run([sys.executable,str(SCRIPT),'--store',str(p),'--out',str(Path(tmp)/'out')],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('busy',result.stderr);self.assertEqual(p.read_bytes(),before)
 def test_unchanged_capability_cannot_justify_progress(self):
  cap=copy.deepcopy(self.db['projects'][0]['capabilities'][0]);self.batch['updates'][0]['capabilities']=[cap]
  self.batch['source_ids']=cap['source_ids'];self.batch['sources']=[]
  with self.assertRaisesRegex(ValueError,'new capability'):sync.merge(self.db,self.batch)
 def test_capability_must_cite_reviewed_project_sources(self):
  self.batch['updates'][0]['capabilities'][0]['source_ids']=self.db['projects'][1]['streams'][0]['source_ids']
  with self.assertRaisesRegex(ValueError,'outside reviewed'):sync.merge(self.db,self.batch)
 def test_multiple_projects_use_only_their_own_sources(self):
  other=copy.deepcopy(self.batch['updates'][0]);p=self.db['projects'][1]
  other.update(project_id=p['project_id'],source_ids=['SECOND-SOURCE'],fields={},streams=[{'id':p['streams'][0]['id'],'fields':{}}])
  other['capabilities']=[dict(p['capabilities'][0],id='SECOND-NEW',source_ids=['SECOND-SOURCE'])]
  self.batch['updates'][0]['source_ids']=['SYNTHETIC-SOURCE'];self.batch['updates'].append(other)
  self.batch['sources'].append({'id':'SECOND-SOURCE','type':'synthetic'});self.batch['source_ids'].append('SECOND-SOURCE')
  db,_=sync.merge(self.db,self.batch)
  self.assertNotIn('SECOND-SOURCE',db['projects'][0]['streams'][0]['source_ids'])
  self.assertNotIn('SYNTHETIC-SOURCE',db['projects'][1]['streams'][0]['source_ids'])
  del self.batch['updates'][0]['source_ids']
  with self.assertRaisesRegex(ValueError,'per-update'):sync.merge(self.db,self.batch)
 def test_unknown_stream_has_clear_error(self):
  self.batch['updates'][0]['streams'][0]['id']='missing-stream'
  with self.assertRaisesRegex(ValueError,'unknown stream: missing-stream'):sync.merge(self.db,self.batch)

 def test_workstream_dates_survive_unrelated_project_update(self):
  self.db['projects'][0]['streams'][1]['as_of']='2026-09-01'
  db,_=sync.merge(self.db,self.batch)
  self.assertEqual(db['projects'][0]['streams'][0]['as_of'],'2026-10-20')
  self.assertEqual(db['projects'][0]['streams'][1]['as_of'],'2026-09-01')
  with tempfile.TemporaryDirectory() as tmp:
   sync.compile_views(db,tmp)
   with (Path(tmp)/'周进度表.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
   self.assertEqual(rows[1]['事实时点'],'2026-09-01')

 def test_invalid_fact_dates_are_rejected_without_mutating_input(self):
  for invalid in [None, 123, [], {}, '', '2026-02-30']:
   b=copy.deepcopy(self.batch);b['as_of']=invalid;before=copy.deepcopy(self.db)
   with self.assertRaises(ValueError):sync.merge(self.db,b)
   self.assertEqual(self.db,before)
   b=copy.deepcopy(self.batch);b['updates'][0]['streams'][0]['as_of']=invalid
   with self.assertRaises(ValueError):sync.merge(self.db,b)
  d=copy.deepcopy(self.db);d['projects'][0]['streams'][0]['as_of']=None
  with self.assertRaises(ValueError):sync.validate(d)
 def test_older_source_keeps_newer_stream_date(self):
  self.db['projects'][0]['streams'][0]['as_of']='2026-11-01'
  db,_=sync.merge(self.db,self.batch)
  self.assertEqual(db['projects'][0]['streams'][0]['as_of'],'2026-11-01')
  self.assertNotEqual(db['projects'][0]['streams'][0]['target'],self.db['projects'][0]['streams'][0]['target'])
 def test_source_only_or_identical_fields_do_not_redate_stream(self):
  for fields in [{},{'target':{'previous':self.db['projects'][0]['streams'][0]['target'],'value':self.db['projects'][0]['streams'][0]['target']}}]:
   b=copy.deepcopy(self.batch);b['updates'][0]['streams'][0]['fields']=fields
   db,_=sync.merge(self.db,b)
   self.assertEqual(db['projects'][0]['streams'][0]['as_of'],self.db['projects'][0]['streams'][0]['as_of'])
 def test_stream_dates_can_differ_in_same_batch(self):
  b=copy.deepcopy(self.batch);b['updates'][0]['streams'][0]['as_of']='2026-11-02'
  st=self.db['projects'][0]['streams'][1]
  b['updates'][0]['streams'].append({'id':st['id'],'as_of':'2026-11-03','fields':{'target':{'previous':st['target'],'value':'synthetic second'}}})
  db,_=sync.merge(self.db,b)
  self.assertEqual([s['as_of'] for s in db['projects'][0]['streams'][:2]],['2026-11-02','2026-11-03'])
 def test_csv_keeps_stage_code_and_readable_label(self):
  with tempfile.TemporaryDirectory() as tmp:
   sync.compile_views(self.db,tmp)
   with (Path(tmp)/'原子能力证据.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
   self.assertTrue(any(r['阶段']=='reported_milestone' and r['阶段说明']=='材料/用户报告里程碑' for r in rows))

if __name__=='__main__':unittest.main()
