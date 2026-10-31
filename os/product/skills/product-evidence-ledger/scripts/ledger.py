"""Versioned evidence records. Python 3.9+, standard library only."""
import argparse
import csv
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if "id" not in fields or len(set(fields)) != len(fields):
            raise ValueError(f"{path.name}: unique columns including id required")
        seen = set()
        for line, row in enumerate(reader, 2):
            key = row["id"]
            if not key or key.strip() != key or key in seen or None in row or None in row.values():
                raise ValueError(f"{path.name}:{line}: invalid or repeated key / column count")
            seen.add(key)
            yield key, json.dumps(row, ensure_ascii=False, sort_keys=True)


def sync(database, files):
    changes = 0
    with closing(sqlite3.connect(database, timeout=30)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS history (
          dataset TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,
          observed_at TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(dataset,id,revision))""")
        db.execute("""CREATE VIEW IF NOT EXISTS current AS SELECT h.* FROM history h
          WHERE revision=(SELECT max(revision) FROM history x WHERE x.dataset=h.dataset AND x.id=h.id)""")
        now = datetime.now(timezone.utc).isoformat()
        for file in files:
            dataset = file.stem
            if not re.fullmatch(r"[a-z][a-z0-9_]*", dataset):
                raise ValueError("dataset name must use lowercase ASCII identifiers")
            for key, payload in read_rows(file):
                last = db.execute("SELECT revision,payload FROM current WHERE dataset=? AND id=?", (dataset,key)).fetchone()
                if last and last[1] == payload:
                    continue
                db.execute("INSERT INTO history VALUES(?,?,?,?,?)", (dataset,key,last[0]+1 if last else 1,now,payload))
                changes += 1
    return changes


def review_queue(database):
    with closing(sqlite3.connect(f"{Path(database).resolve().as_uri()}?mode=ro", uri=True)) as db:
        for key, payload in db.execute("SELECT id,payload FROM current WHERE dataset='market' ORDER BY id"):
            row = json.loads(payload)
            if row.get("复核结论") != "核心陈述获一手支持":
                yield [key,row.get("平台",""),row.get("复核结论","待复核"),row.get("核验边界",""),row.get("来源URL","")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("sync")
    ingest.add_argument("database", type=Path)
    ingest.add_argument("files", type=Path, nargs="+")
    queue = commands.add_parser("queue")
    queue.add_argument("database", type=Path)
    args = parser.parse_args()
    if args.command == "sync":
        print(f"changed records: {sync(args.database, args.files)}")
    else:
        import sys
        writer = csv.writer(sys.stdout)
        writer.writerow(["id","平台","复核结论","核验边界","来源URL"])
        writer.writerows(review_queue(args.database))
