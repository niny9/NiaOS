#!/usr/bin/env python3
"""Trading-session review dates and explicitly costed simple interval comparisons."""
import argparse
from datetime import date, datetime
import json
import math


def horizons(calendar, signal_date):
    signal=date.fromisoformat(signal_date)
    if calendar.get('verified') is not True or not calendar.get('source_ref') or not calendar.get('retrieved_at'):
        raise ValueError('verified calendar source required')
    retrieved=datetime.fromisoformat(calendar['retrieved_at'].replace('Z','+00:00'))
    if retrieved.tzinfo is None: raise ValueError('calendar retrieval timezone required')
    start=date.fromisoformat(calendar['coverage_start']);end=date.fromisoformat(calendar['coverage_end'])
    days=[date.fromisoformat(x) for x in calendar['sessions']]
    if days!=sorted(set(days)) or any(d<start or d>end for d in days) or not start<=signal<=end:
        raise ValueError('invalid calendar order, coverage or duplicate session')
    later=[d for d in days if d>signal]
    return {str(n):later[n-1].isoformat() if len(later)>=n else None for n in (1,5,20)}


def compare(entry, exit_price, benchmark_entry, benchmark_exit, fee_rate, slippage_rate):
    values=(entry,exit_price,benchmark_entry,benchmark_exit,fee_rate,slippage_rate)
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
        raise ValueError('finite numeric inputs required')
    if min(entry,exit_price,benchmark_entry,benchmark_exit)<=0 or min(fee_rate,slippage_rate)<0 or fee_rate+slippage_rate>=1:
        raise ValueError('invalid prices or total round-trip costs')
    net=exit_price/entry-1-fee_rate-slippage_rate; benchmark=benchmark_exit/benchmark_entry-1
    return {'hypothetical_net_return':net,'benchmark_return':benchmark,'excess_return':net-benchmark,
            'cost_basis':'total round-trip rates relative to initial notional','actual_trade_return':None}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True)
    h=s.add_parser('horizons');h.add_argument('--calendar',required=True);h.add_argument('--signal-date',required=True)
    c=s.add_parser('compare')
    for k in ('entry','exit-price','benchmark-entry','benchmark-exit','fee-rate','slippage-rate'):c.add_argument('--'+k,type=float,required=True)
    a=p.parse_args()
    try:
        if a.mode=='horizons':
            with open(a.calendar) as f:result=horizons(json.load(f),a.signal_date)
        else: result=compare(a.entry,a.exit_price,a.benchmark_entry,a.benchmark_exit,a.fee_rate,a.slippage_rate)
        print(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as e:p.exit(2,str(e)+'\n')
