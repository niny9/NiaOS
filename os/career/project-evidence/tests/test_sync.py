"""Portable ingestion checks. All new events are synthetic and stay in temp directories."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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
  self.assertEqual([len(self.db['projects']),sum(len(p['streams']) for p in self.db['projects']),sum(len(p['capabilities']) for p in self.db['projects'])],[6,12,14])
  self.assertEqual([s['id'] for s in self.db['projects'][1]['streams']],['instant_use','my_jd_mindshare'])
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
   self.assertEqual(sync.sync_vault(self.db,vault),6);self.assertEqual(sync.sync_vault(self.db,vault),0)
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

if __name__=='__main__':unittest.main()
