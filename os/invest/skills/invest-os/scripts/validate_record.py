#!/usr/bin/env python3
"""Validate private Invest OS records. No imports, holdings writes or broker calls."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[1] / 'assets/schemas'


def read_json(path):
    def reject(value):
        raise ValueError('non-finite JSON: ' + value)
    return json.loads(Path(path).read_text(), parse_constant=reject)


def iso(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('timezone required')
    return d


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('non-finite number')
    if isinstance(value, dict):
        for v in value.values(): finite(v)
    elif isinstance(value, list):
        for v in value: finite(v)


def validate(kind, record, as_of=None, max_age_hours=None):
    errors = []
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return {'ok': False, 'errors': ['jsonschema dependency unavailable; no validation performed'], 'ledger_update_authorized': False}
    try:
        if kind not in ('handoff', 'actual', 'signal', 'behavior'):
            raise ValueError('unsupported record kind')
        finite(record)
        schema = read_json(SCHEMAS / (kind + '.schema.json'))
        errors = [str(e.json_path) + ': ' + e.message for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)]
        if errors:
            return {'ok': False, 'errors': errors, 'ledger_update_authorized': False}
        if kind == 'actual':
            expected = (-1 if record['side'] == 'buy' else 1) * record['price'] * record['quantity'] - record['fees_cny']
            if abs(expected - record['cash_delta_cny']) > .02:
                errors.append('cash delta does not reconcile to price, quantity and fees')
            if (record['emotion'] is not None or record['motive'] is not None) and not record['user_statement_ref']:
                errors.append('emotion/motive requires user statement')
            if record['ai_alignment'] in ('aligned', 'deviated') and not record['ai_signal_id']:
                errors.append('alignment requires AI signal ID')
            if iso(record['source']['source_as_of']) < iso(record['executed_at']):
                errors.append('source predates execution')
        elif kind == 'signal':
            if iso(record['expires_at']) <= iso(record['signal_at']):
                errors.append('signal expiry must follow issue time')
            if not record['sources']:
                errors.append('signal requires evidence')
            if any(iso(s['source_as_of']) > iso(record['signal_at']) or iso(s['retrieved_at']) > iso(record['signal_at']) for s in record['sources']):
                errors.append('signal cannot use future evidence')
        elif kind == 'behavior':
            expected = set(schema['properties']['labels']['items']['properties']['tag']['enum'])
            tags = [x['tag'] for x in record['labels']]
            if set(tags) != expected or len(tags) != len(expected):
                errors.append('each behavior tag must occur exactly once')
            for item in record['labels']:
                kinds = {e['kind'] for e in item['evidence']}
                if item['status'] != 'Unknown' and not kinds:
                    errors.append(item['tag'] + ': evidence required')
                if item['status'] == 'Confirmed' and ('actual_trade' not in kinds or not kinds.intersection({'market_evidence', 'prior_plan', 'user_statement'})):
                    errors.append(item['tag'] + ': Confirmed requires actual fills and corroboration')
                if item['status'] == 'Confirmed' and item['tag'] in ('spike_impulse','emotional_trading','loss_aversion_delay','year_end_recovery_pressure') and 'user_statement' not in kinds:
                    errors.append(item['tag'] + ': motive cannot be inferred')
        elif kind == 'handoff':
            if as_of is None or max_age_hours is None or isinstance(max_age_hours, bool) or not math.isfinite(max_age_hours) or max_age_hours <= 0:
                raise ValueError('handoff requires as-of and positive max-age-hours')
            now = iso(as_of)
            verified = record['data_quality']['status'] == 'verified'
            def check_time(value, label, required=False):
                if value is None:
                    if required: errors.append(label + ': missing time')
                    return
                age = (now - iso(value)).total_seconds()/3600
                if age < 0: errors.append(label + ': future time')
                if required and age > max_age_hours: errors.append(label + ': stale data')
            check_time(record['data_as_of'], 'handoff', verified)
            check_time(record['generated_at'], 'generated', verified)
            if record['data_as_of'] and record['generated_at'] and iso(record['data_as_of']) > iso(record['generated_at']):
                errors.append('data timestamp after report generation')
            if record['mode'] == 'verified_export' and (record['capabilities']['export'] != 'supported' or not record['capability_evidence']):
                errors.append('export connection not evidenced')
            aliases = [a['account_alias'] for a in record['accounts']]
            if len(aliases) != len(set(aliases)): errors.append('duplicate account alias')
            for a in record['accounts']:
                check_time(a['as_of'], a['account_alias'], verified)
                positions = a['positions']
                keys = [(p['security']['code'], p['security']['venue'], p['security']['share_class']) for p in positions]
                if len(keys) != len(set(keys)): errors.append('duplicate security in account')
                cash, available, total = a['cash_total_cny'], a['cash_available_cny'], a['reported_total_cny']
                if cash is not None and available is not None and available > cash: errors.append('available cash exceeds total cash')
                for p in positions:
                    check_time(p['price_as_of'], 'price', verified)
                    if p['quantity'] is not None and p['available_quantity'] is not None and p['available_quantity'] > p['quantity']:
                        errors.append('available quantity exceeds holding')
                    if verified and (p['quality'] != 'verified' or any(p[k] is None for k in ('quantity','available_quantity','unit_price','market_value_cny','source_ref'))):
                        errors.append('unverified or incomplete position')
                    if all(p[k] is not None for k in ('quantity','unit_price','market_value_cny')) and abs(p['quantity']*p['unit_price']-p['market_value_cny']) > 1:
                        errors.append('position valuation mismatch')
                if a['cash_management_counted_as'] == 'cash' and any(p['security']['product_type'] == 'cash_management' for p in positions):
                    errors.append('cash management counted twice')
                if verified:
                    if None in (cash, available, total) or not a['source_ref'] or a['cash_management_counted_as'] == 'unknown':
                        errors.append('verified account lacks cash, total, source or counting basis')
                    elif all(p['market_value_cny'] is not None for p in positions) and abs(sum(p['market_value_cny'] for p in positions)+cash-total) > 1:
                        errors.append('account total mismatch; available cash must not be added twice')
            ids = [t['trade_id'] for t in record['actual_trades']]
            if len(ids) != len(set(ids)): errors.append('duplicate actual trade')
            for t in record['actual_trades']:
                errors.extend('trade: ' + e for e in validate('actual', t)['errors'])
                check_time(t['executed_at'], 'trade')
                if t['account_alias'] not in aliases: errors.append('trade references unknown account')
                if record['data_as_of'] and iso(t['executed_at']) > iso(record['data_as_of']): errors.append('trade after data cutoff')
            for o in record['open_orders']:
                if o['filled_quantity'] >= o['quantity']: errors.append('open order must have unfilled quantity')
                if o['account_alias'] not in aliases: errors.append('order references unknown account')
                check_time(o['submitted_at'], 'order')
            if verified:
                q = record['data_quality']
                if not q['accounts_complete'] or not q['confirmed_by_user'] or q['pending_activity'] or q['issues']:
                    errors.append('verified status conflicts with quality flags')
                if record['open_orders']: errors.append('pending orders prevent executable snapshot')
                if not record['accounts'] and not q['empty_accounts_confirmed']: errors.append('empty account list is not confirmed empty')
                if not record['report_id']: errors.append('verified report needs ID')
        # Source chronology applies to all nested evidence, even in partial handoffs.
        def sources(value):
            if isinstance(value, dict):
                if all(k in value for k in ('source_ref','source_as_of','retrieved_at')):
                    if iso(value['source_as_of']) > iso(value['retrieved_at']): errors.append('source time after retrieval')
                    if as_of and iso(value['retrieved_at']) > iso(as_of): errors.append('future evidence retrieval')
                for v in value.values(): sources(v)
            elif isinstance(value,list):
                for v in value: sources(v)
        sources(record)
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        errors.append(str(exc))
    return {'ok': not errors, 'errors': errors, 'ledger_update_authorized': False,
            'note': 'Structure checked; source authenticity and snapshot reconciliation require review.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind',choices=['handoff','actual','signal','behavior']); p.add_argument('input')
    p.add_argument('--as-of'); p.add_argument('--max-age-hours',type=float)
    a=p.parse_args()
    try: result=validate(a.kind,read_json(a.input),a.as_of,a.max_age_hours)
    except (OSError, ValueError) as exc: result={'ok':False,'errors':[str(exc)]}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if result['ok'] else 2

if __name__=='__main__': raise SystemExit(main())
