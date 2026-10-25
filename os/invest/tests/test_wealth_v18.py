"""Synthetic fixtures only: no account credentials, private holdings or market access."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import date,timedelta

ROOT=Path(__file__).resolve().parents[1]/'skills'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
records=load('records_v18',ROOT/'invest-os/scripts/validate_record.py')
journal=load('journal_v18',ROOT/'nia-invest-trade-journal/scripts/journal.py')
evaluate=load('evaluate_v18',ROOT/'nia-invest-strategy-evaluator/scripts/evaluate.py')
TIME='2026-10-25T15:30:00+08:00'
SOURCE={'source_ref':'synthetic-fixture','source_as_of':TIME,'retrieved_at':TIME}
SECURITY={'name':'Synthetic only','code':'000000','venue':'TEST','share_class':None,'product_type':'stock'}

def actual():
    return {'schema_version':'invest.actual-trade.v1','trade_id':'synthetic-fill-1','account_alias':'test','security':SECURITY.copy(),'executed_at':TIME,'side':'buy','price':10,'quantity':100,'fees_cny':5,'cash_delta_cny':-1005,'currency':'CNY','status':'filled','confirmed_by_user':True,'source':SOURCE.copy(),'motive':None,'emotion':None,'user_statement_ref':None,'ai_signal_id':None,'ai_alignment':'no_signal','supersedes':None}

def signal():
    return {'schema_version':'invest.ai-signal.v1','signal_id':'synthetic-signal','strategy_version':'test-only','security':SECURITY.copy(),'signal_at':TIME,'expires_at':'2026-10-26T15:30:00+08:00','direction':'wait','basis':'Synthetic','trigger':'Synthetic','invalidation':'Synthetic','no_trade_condition':'Synthetic','risk':'Synthetic','sources':[SOURCE.copy()],'discipline_check':{'gate':'unknown','reminder':'Test','evidence_refs':[],'recheck_condition':'Test'},'state':'proposed','supersedes':None}

def handoff():
    r=json.loads((ROOT/'nia-invest-tonghuashun-bridge/assets/handoff.template.json').read_text())
    r.update(report_id='test',data_as_of=TIME,generated_at=TIME)
    r['accounts']=[{'account_alias':'test','currency':'CNY','as_of':TIME,'source_ref':'synthetic','cash_total_cny':1000,'cash_available_cny':900,'reported_total_cny':1000,'cash_management_counted_as':'none','positions':[],'performance':[]}]
    r['data_quality'].update(status='verified',accounts_complete=True,confirmed_by_user=True,pending_activity=False,issues=[])
    return r

class RecordTests(unittest.TestCase):
    def test_verified_handoff_not_ledger_authorization(self):
        r=records.validate('handoff',handoff(),TIME,2)
        self.assertTrue(r['ok']);self.assertFalse(r['ledger_update_authorized'])
    def test_cash_is_not_available_plus_total(self):
        r=handoff();r['accounts'][0]['reported_total_cny']=1900
        self.assertFalse(records.validate('handoff',r,TIME,2)['ok'])
    def test_duplicate_accounts_rejected(self):
        r=handoff();r['accounts']*=2
        self.assertFalse(records.validate('handoff',r,TIME,2)['ok'])
    def test_stale_or_future_verified_data_rejected(self):
        r=handoff()
        self.assertFalse(records.validate('handoff',r,'2026-10-26T15:30:00+08:00',2)['ok'])
        self.assertFalse(records.validate('handoff',r,'2026-10-25T14:00:00+08:00',2)['ok'])
    def test_empty_is_unknown_not_empty_portfolio(self):
        r=handoff();r['accounts']=[]
        self.assertFalse(records.validate('handoff',r,TIME,2)['ok'])
    def test_auto_connection_requires_evidence(self):
        r=handoff();r['mode']='verified_export'
        self.assertFalse(records.validate('handoff',r,TIME,2)['ok'])
    def test_manual_unavailable_template_can_explain_gaps(self):
        r=json.loads((ROOT/'nia-invest-tonghuashun-bridge/assets/handoff.template.json').read_text())
        self.assertTrue(records.validate('handoff',r,TIME,2)['ok'])
    def test_real_fill_reconciles_fees_both_directions(self):
        r=actual();self.assertTrue(records.validate('actual',r)['ok'])
        r.update(side='sell',cash_delta_cny=995);self.assertTrue(records.validate('actual',r)['ok'])
        r['cash_delta_cny']=1000;self.assertFalse(records.validate('actual',r)['ok'])
    def test_orders_and_missing_fees_are_not_fills(self):
        for changes in ({'status':'open'},{'fees_cny':None},{'confirmed_by_user':False},{'quantity':True}):
            r=actual();r.update(changes);self.assertFalse(records.validate('actual',r)['ok'])
    def test_emotion_cannot_be_inferred(self):
        r=actual();r['emotion']='anxious';self.assertFalse(records.validate('actual',r)['ok'])
        r['user_statement_ref']='user explicitly said this';self.assertTrue(records.validate('actual',r)['ok'])
    def test_signal_expiry_and_lookahead(self):
        r=signal();self.assertTrue(records.validate('signal',r)['ok'])
        r['expires_at']=TIME;self.assertFalse(records.validate('signal',r)['ok'])
        r=signal();r['sources'][0]['retrieved_at']='2026-10-26T15:30:00+08:00';self.assertFalse(records.validate('signal',r)['ok'])
    def test_non_finite_json(self):
        r=actual();r['price']=float('nan');self.assertFalse(records.validate('actual',r)['ok'])
    def test_behavior_confirmed_needs_fill_and_corroboration(self):
        r=json.loads((ROOT/'nia-invest-behavior-guardian/assets/behavior-profile.template.json').read_text())
        self.assertTrue(records.validate('behavior',r)['ok'])
        t=r['labels'][0];t.update(status='Confirmed',evidence=[{'kind':'chart_marker','evidence_ref':'B/S'}])
        self.assertFalse(records.validate('behavior',r)['ok'])
        t['evidence']=[{'kind':'actual_trade','evidence_ref':'test-fill'},{'kind':'market_evidence','evidence_ref':'test-series'}]
        self.assertTrue(records.validate('behavior',r)['ok'])
    def test_journals_idempotent_and_separate(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'actual.jsonl';r=actual()
            self.assertTrue(journal.append('actual',r,path)['appended'])
            self.assertTrue(journal.append('actual',r,path)['duplicate'])
            r['source']['source_ref']='changed'
            with self.assertRaises(ValueError):journal.append('actual',r,path)
            with self.assertRaises(ValueError):journal.append('signal',signal(),path)
            self.assertEqual(len(path.read_text().splitlines()),1)
    def test_unknown_fill_template_rejected(self):
        r=json.loads((ROOT/'nia-invest-trade-journal/assets/actual-trade.template.json').read_text())
        self.assertFalse(records.validate('actual',r)['ok'])

class EvaluationTests(unittest.TestCase):
    def test_horizons_use_provided_sessions_not_calendar_days(self):
        c={'verified':True,'source_ref':'SYNTHETIC CALENDAR','retrieved_at':TIME,'coverage_start':'2026-10-23','coverage_end':'2026-11-30','sessions':['2026-10-23','2026-10-26','2026-10-27','2026-10-29','2026-10-30','2026-11-02']}
        r=evaluate.horizons(c,'2026-10-23')
        self.assertEqual(r,{'1':'2026-10-26','5':'2026-11-02','20':None})
        c['verified']=False
        with self.assertRaises(ValueError):evaluate.horizons(c,'2026-10-23')
    def test_all_three_horizons_on_synthetic_complete_calendar(self):
        days=[(date(2026,10,1)+timedelta(days=i)).isoformat() for i in range(25)]
        c={'verified':True,'source_ref':'SYNTHETIC EVERY-DAY TEST CALENDAR','retrieved_at':TIME,'coverage_start':days[0],'coverage_end':days[-1],'sessions':days}
        self.assertEqual(evaluate.horizons(c,days[0]),{'1':days[1],'5':days[5],'20':days[20]})
    def test_fees_slippage_and_benchmark(self):
        r=evaluate.compare(100,110,100,105,.002,.001)
        self.assertAlmostEqual(r['hypothetical_net_return'],.097);self.assertAlmostEqual(r['excess_return'],.047)
        self.assertIsNone(r['actual_trade_return'])
        with self.assertRaises(ValueError):evaluate.compare(100,110,100,105,None,.001)
    def test_schemas_are_valid(self):
        from jsonschema import Draft202012Validator
        for p in (ROOT/'invest-os/assets/schemas').glob('*.json'):Draft202012Validator.check_schema(json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
