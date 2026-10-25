#!/usr/bin/env python3
"""Append validated records to separate private journals. POSIX locking; no ledger edits."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path

helper=Path(__file__).resolve().parents[2]/'invest-os/scripts/validate_record.py'
spec=importlib.util.spec_from_file_location('invest_records',helper)
records=importlib.util.module_from_spec(spec);spec.loader.exec_module(records)


def append(kind, record, path):
    result=records.validate(kind,record)
    if not result['ok']: raise ValueError('; '.join(result['errors']))
    key='signal_id' if kind=='signal' else 'trade_id'
    path=Path(path)
    if path.is_symlink(): raise ValueError('journal cannot be symlink')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_APPEND|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'a+',encoding='utf-8') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        f.seek(0)
        for line in f:
            old=json.loads(line)
            if old.get('schema_version')!=record['schema_version']:
                raise ValueError('AI signal and actual-trade journals must be separate')
            if old.get(key)==record[key]:
                if old!=record: raise ValueError('ID conflict; preserve old record and use a revision ID')
                return {'appended':False,'duplicate':True,'ledger_updated':False}
        f.seek(0,os.SEEK_END)
        f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
    return {'appended':True,'duplicate':False,'ledger_updated':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--kind',choices=['signal','actual'],required=True)
    p.add_argument('--record',required=True);p.add_argument('--journal',required=True);a=p.parse_args()
    try: print(json.dumps(append(a.kind,records.read_json(a.record),a.journal)))
    except (OSError,ValueError) as e: p.exit(2,str(e)+'\n')
