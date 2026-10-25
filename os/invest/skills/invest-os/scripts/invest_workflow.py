#!/usr/bin/env python3
"""Discover and prepare an Agent-executed Invest OS workflow; verify its receipts.

No scheduler, broker, notifier, arbitrary command runner or autonomous LLM runtime.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone, timedelta

SKILL = Path(__file__).resolve().parents[1]
MANIFEST = SKILL / "references/workflow.json"
SHANGHAI = timezone(timedelta(hours=8))


def read_json(path):
    def reject(value):
        raise ValueError(f"non-finite JSON value: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def iso(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("time must include timezone")
    return result


def validate_manifest(manifest):
    if manifest.get("schema_version") != "invest.workflow.v2":
        raise ValueError("unsupported workflow manifest")
    seen = set()
    for stage in manifest["stages"]:
        sid = stage["id"]
        if sid in seen or not sid.replace("_", "").isalnum():
            raise ValueError("duplicate or invalid stage ID")
        if any(dep not in seen for dep in stage["depends_on"]):
            raise ValueError("dependency missing, cyclic or out of order")
        if stage["execution"] != "agent_skill":
            raise ValueError("only agent_skill stages are supported")
        seen.add(sid)
    return manifest["stages"]


def discover(names, roots):
    found = {}
    for name in sorted(names):
        candidates = []
        for root in roots:
            directory = root / name
            entries = {p.name: p for p in directory.iterdir()} if directory.is_dir() else {}
            for filename in ("SKILL.md", "skill.md"):
                path = entries.get(filename)
                if path is None:
                    continue
                path = path.resolve()
                if path.is_file() and str(path) not in candidates:
                    candidates.append(str(path))
        selected = candidates[0] if candidates else None
        found[name] = {"path": selected, "sha256": digest(selected) if selected else None,
                       "available": bool(selected), "alternate_paths": candidates[1:]}
    return found


def binding_files(binding_path):
    if binding_path is None:
        return {}, {}, {}
    binding_path = Path(binding_path).resolve()
    raw = read_json(binding_path)
    if not isinstance(raw, dict):
        raise ValueError("bindings must be an object")
    metadata = {str(binding_path): digest(binding_path)}
    files = {}
    for key in ("holdings_file", "goals_file", "risk_policy_file", "historical_baseline_file",
                "handoff_file", "behavior_profile_file", "ai_signal_journal_file", "actual_trade_journal_file",
                "unreconciled_updates_file", "trading_calendar_file"):
        value = raw.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{key} must be a path or null")
        path = Path(value).expanduser() if value else None
        if path and not path.is_absolute():
            path = binding_path.parent / path
        path = path.resolve() if path else None
        exists = bool(path and path.is_file())
        files[key] = {"path": str(path) if path else None, "exists": exists,
                      "sha256": digest(path) if exists else None}
        if exists:
            metadata[str(path)] = digest(path)
    return raw, files, metadata


def validate_holdings(file, available, as_of, max_age):
    if not file or not file.get("exists"):
        return {"ok": False, "state": "unavailable", "errors": ["no confirmed holdings input"]}
    owner = available.get("nia-wealth-holdings", {}).get("path")
    if not owner:
        return {"ok": False, "state": "unavailable", "errors": ["holdings skill missing"]}
    script = Path(owner).parent / "scripts/validate_snapshot.py"
    try:
        spec = importlib.util.spec_from_file_location("invest_snapshot_gate", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.validate(read_json(file["path"]), as_of, max_age)
    except (OSError, ValueError, TypeError, AttributeError, ImportError) as exc:
        return {"ok": False, "state": "invalid", "errors": [type(exc).__name__]}


def probe_quant(available, bindings, max_age):
    owner = available.get("finance-quant-closed-loop", {}).get("path")
    if not owner:
        return {"state": "unavailable", "executed": False}
    script = Path(owner).parent / "scripts/finance_quant_control.py"
    if not script.is_file():
        return {"state": "unavailable", "executed": False}
    command = [sys.executable, str(script)]
    for key, flag in (("claw_root", "--claw-root"), ("quant_out_dir", "--out-dir")):
        if bindings.get(key):
            command += [flag, str(bindings[key])]
    command += ["status", "--max-age-hours", str(max_age)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("invalid status response")
        return {"executed": True, "operation": "status_only", "returncode": result.returncode,
                "state": "checked" if result.returncode == 0 else "failed",
                "freshness": payload.get("freshness"), "truth_level": payload.get("truth_level"),
                "risk_gate_ok": payload.get("risk_gate", {}).get("ok"),
                "operational": payload.get("closure", {}).get("operational", False)}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"executed": True, "operation": "status_only", "state": "failed",
                "error": "status unavailable; raw output withheld"}


def prepare(manifest_path, roots, binding_path, as_of, max_age, probe=False):
    iso(as_of)
    if not math.isfinite(max_age) or max_age <= 0:
        raise ValueError("max-age-hours must be finite and positive")
    manifest_path = Path(manifest_path).resolve()
    stages = validate_manifest(read_json(manifest_path))
    names = {s["owner_skill"] for s in stages} | {p for s in stages for p in s["provider_skills"]}
    available = discover(names, roots)
    bindings, files, input_fingerprints = binding_files(binding_path)
    fingerprints = {str(manifest_path): digest(manifest_path), **input_fingerprints}
    for info in available.values():
        if info["path"]:
            # Pin helper/reference changes as well as entrypoint text.
            for p in Path(info["path"]).parent.rglob("*"):
                if p.is_file() and p.suffix in (".py", ".md", ".json", ".yaml") and "__pycache__" not in p.parts and not any(part.startswith(".") for part in p.relative_to(Path(info["path"]).parent).parts):
                    fingerprints[str(p.resolve())] = digest(p)
    tasks = []
    for s in stages:
        owner = available[s["owner_skill"]]
        tasks.append({**s, "skill_file": owner["path"],
                      "provider_files": {p: available[p]["path"] for p in s["provider_skills"]},
                      "orchestration_context": "invest-os.stage",
                      "status": "pending_agent" if owner["available"] else "missing_skill",
                      "output_file": s["id"] + ".json"})
    preflight = {"holdings": validate_holdings(files.get("holdings_file"), available, as_of, max_age),
                 "quant": probe_quant(available, bindings, max_age) if probe else {"state": "not_probed", "executed": False}}
    identity = object_digest({"as_of": as_of, "fingerprints": fingerprints, "max_age": max_age})
    plan = {"schema_version": "invest.work-order.v1", "run_id": "invest-" + identity[:16],
            "as_of": as_of, "max_age_hours": max_age, "ready_for_agent": all(s["status"] != "missing_skill" for s in tasks),
            "research_executed": False, "skills": available, "inputs": files,
            "fingerprints": fingerprints, "preflight": preflight, "tasks": tasks,
            "scheduler_changed": False, "broker_order_placed": False}
    plan["plan_hash"] = object_digest(plan)
    return plan


def check_results(plan, directory, now=None):
    errors, receipts = [], {}
    now = iso(now) if now else datetime.now(SHANGHAI)
    original = {k: v for k, v in plan.items() if k != "plan_hash"}
    if plan.get("plan_hash") != object_digest(original):
        errors.append("work order hash mismatch")
    for path, sha in plan["fingerprints"].items():
        if not Path(path).is_file() or digest(path) != sha:
            errors.append("input or skill changed: " + path)
    for task in plan["tasks"]:
        sid = task["id"]
        try:
            r = read_json(Path(directory) / task["output_file"])
            if not isinstance(r, dict):
                raise ValueError("receipt must be an object")
            if (r.get("schema_version"), r.get("run_id"), r.get("plan_hash"), r.get("stage_id")) != (
                    "invest.stage.v1", plan["run_id"], plan["plan_hash"], sid):
                raise ValueError("receipt identity mismatch")
            if r.get("status") not in ("complete", "degraded", "blocked", "skipped"):
                raise ValueError("invalid stage status")
            if r["status"] == "skipped" and sid != "reconciliation":
                raise ValueError("only conditional reconciliation may be skipped")
            if not isinstance(r.get("summary"), str) or not r["summary"].strip():
                raise ValueError("missing result or degradation reason")
            generated = iso(r["generated_at"])
            if generated < iso(plan["as_of"]) or generated > now:
                raise ValueError("receipt timestamp outside run interval")
            if (now - generated).total_seconds() > plan["max_age_hours"] * 3600:
                raise ValueError("stale receipt")
            if r.get("consumed_stages") != task["depends_on"]:
                raise ValueError("upstream stages do not match dependency order")
            evidence = r.get("evidence")
            if not isinstance(evidence, list) or (r["status"] == "complete" and not evidence):
                raise ValueError("complete stage requires evidence")
            if any(not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e[k].strip()
                   for k in ("source_ref", "source_as_of")) for e in evidence):
                raise ValueError("invalid evidence reference")
            if not isinstance(r.get("output"), dict):
                raise ValueError("output must be an object")
            if task["status"] == "missing_skill" and r["status"] == "complete":
                raise ValueError("missing skill cannot be complete")
            receipts[sid] = r
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            errors.append(sid + ": " + str(exc))
    def out(sid):
        return receipts.get(sid, {}).get("output", {})
    for sid, field in (("holdings", "validation_ok"), ("risk", "gate"), ("market", "market_rules_verified")):
        if sid in receipts and field not in out(sid):
            errors.append(sid + ": missing " + field)
    if "risk" in receipts and out("risk").get("gate") not in ("pass", "warn", "block", "unknown"):
        errors.append("risk: invalid gate")
    if "behavior" in receipts and out("behavior").get("gate") not in ("pass", "warn", "block", "unknown"):
        errors.append("behavior: missing or invalid discipline gate")
    if "handoff" in receipts and out("handoff").get("connection_status") not in ("manual_copy", "verified_export", "unavailable"):
        errors.append("handoff: missing connection status")
    if out("handoff").get("connection_status") == "verified_export" and out("handoff").get("connection_evidence_verified") is not True:
        errors.append("handoff: automatic connection is not evidenced")
    for field in ("signals_reviewed", "trades_reviewed"):
        value = out("journal").get(field)
        if "journal" in receipts and (field not in out("journal") or value is not None and (type(value) is not int or value < 0)):
            errors.append("journal: missing or invalid " + field)
    if "evaluation" in receipts and not isinstance(out("evaluation").get("reviews"), list):
        errors.append("evaluation: missing reviews array")
    required_categories = {"a_share_stock", "broad_etf", "sector_etf", "otc_fund", "bond_or_cash_management", "hold_cash"}
    comparisons = out("opportunities").get("comparisons")
    reallocations = out("opportunities").get("reallocation")
    if "opportunities" in receipts:
        if not isinstance(comparisons, list) or not isinstance(reallocations, list):
            errors.append("opportunities: missing comparison/reallocation arrays")
        elif receipts["opportunities"]["status"] == "complete" and (
                {c.get("category") for c in comparisons if isinstance(c, dict)} != required_categories
                or any(not isinstance(c, dict) or not c.get("conclusion") for c in comparisons)):
            errors.append("opportunities: six alternatives need a comparison conclusion")
    snapshot_now = validate_holdings(plan.get("inputs", {}).get("holdings_file"), plan["skills"],
                                     now.isoformat(), plan["max_age_hours"])
    if receipts.get("holdings", {}).get("status") == "complete" and (out("holdings").get("validation_ok") is not True or snapshot_now.get("ok") is not True):
        errors.append("holdings: failed current validation cannot be complete")
    if receipts.get("risk", {}).get("status") == "complete" and (out("risk").get("gate") == "unknown" or out("risk").get("policy_confirmed") is not True):
        errors.append("risk: unknown or unconfirmed policy cannot be complete")
    if receipts.get("diagnosis", {}).get("status") == "complete" and any(receipts.get(s, {}).get("status") != "complete" for s in ("holdings", "market")):
        errors.append("diagnosis: missing holdings or market evidence cannot be complete")
    quantitative = (snapshot_now.get("ok") is True and out("holdings").get("validation_ok") is True
                    and out("risk").get("gate") == "pass" and out("risk").get("policy_confirmed") is True
                    and out("market").get("market_rules_verified") is True
                    and out("behavior").get("gate") == "pass"
                    and all(receipts.get(s, {}).get("status") == "complete"
                            for s in ("holdings", "market", "diagnosis", "risk", "behavior")))
    plans = out("trade_plan").get("plans")
    if "trade_plan" in receipts:
        if not isinstance(plans, list):
            errors.append("trade_plan: plans must be an array")
        else:
            for item in plans:
                if not isinstance(item, dict):
                    errors.append("trade_plan: invalid item")
                    continue
                if item.get("state") != "proposed" or item.get("executable") is not False:
                    errors.append("trade_plan: only non-executable proposed plans allowed")
                for field in ("id", "security_name", "code", "market_assessment", "direction", "trigger", "thesis", "invalidation", "no_trade_condition", "horizon"):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        errors.append("trade_plan: missing " + field)
                if item.get("direction") not in ("buy", "add", "sell", "reduce", "exit", "hold", "wait"):
                    errors.append("trade_plan: invalid direction")
                for field in ("risks", "sources"):
                    if not isinstance(item.get(field), list) or not item[field]:
                        errors.append("trade_plan: missing " + field)
                for source in item.get("sources", []) if isinstance(item.get("sources"), list) else []:
                    try:
                        if not source.get("source_ref"): raise ValueError("missing source")
                        if iso(source["source_as_of"]) > now: raise ValueError("future source")
                    except (KeyError, ValueError, AttributeError, TypeError):
                        errors.append("trade_plan: invalid source timestamp/reference")
                discipline = item.get("discipline_check", {})
                if not isinstance(discipline, dict): discipline = {}
                if discipline.get("gate") not in ("pass", "warn", "block", "unknown") or not discipline.get("reminder") or not discipline.get("recheck_condition"):
                    errors.append("trade_plan: missing personal discipline check")
                item_numeric = quantitative and discipline.get("gate") == "pass"
                if item.get("direction") in ("sell", "reduce", "exit"):
                    matches = [r for r in reallocations or [] if isinstance(r, dict) and r.get("id") == item.get("reallocation_id") and r.get("source_plan_id") == item.get("id")]
                    if not matches or not matches[0].get("destination") or not matches[0].get("conditions"):
                        errors.append("trade_plan: sale needs a funded reallocation or explicit cash plan")
                for field in ("quantity", "amount_cny"):
                    if field not in item:
                        errors.append("trade_plan: missing " + field)
                    value = item.get(field)
                    if value is not None:
                        if not item_numeric:
                            errors.append("trade_plan: numerical action blocked by missing/failed upstream gate")
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                            errors.append("trade_plan: invalid numeric " + field)
                for field in ("quantity_range", "amount_range_cny"):
                    if field not in item: errors.append("trade_plan: missing " + field)
                    value = item.get(field)
                    if value is not None:
                        if not item_numeric: errors.append("trade_plan: numerical range blocked")
                        if not isinstance(value, list) or len(value) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in value) or value[0] > value[1]:
                            errors.append("trade_plan: invalid " + field)
    degraded = [sid for sid, r in receipts.items() if r["status"] in ("blocked", "degraded")]
    return {"schema_version": "invest.acceptance.v1", "run_id": plan["run_id"],
            "accepted": not errors, "status": "incomplete" if errors else ("degraded" if degraded else "complete"),
            "errors": errors, "degraded_stages": degraded, "stage_count": len(receipts),
            "broker_order_placed": False, "trade_authorized": False,
            "note": "Receipt structure and dependencies checked; source authenticity still requires evidence review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--bindings", type=Path)
    prep.add_argument("--as-of", required=True)
    prep.add_argument("--max-age-hours", type=float, required=True)
    prep.add_argument("--skill-root", type=Path, action="append")
    prep.add_argument("--probe-quant", action="store_true")
    check = sub.add_parser("check-results")
    check.add_argument("--plan", type=Path, required=True)
    check.add_argument("--results-dir", type=Path, required=True)
    check.add_argument("--as-of")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            roots = args.skill_root or [SKILL.parent, Path(os.environ.get("CODEX_HOME", Path.home()/".codex"))/"skills", Path.home()/".agents/skills"]
            report = prepare(MANIFEST, roots, args.bindings, args.as_of, args.max_age_hours, args.probe_quant)
            code = 0 if report["ready_for_agent"] else 2
        else:
            report = check_results(read_json(args.plan), args.results_dir, args.as_of)
            code = 0 if report["accepted"] else 2
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        report, code = {"status": "error", "error": str(exc), "broker_order_placed": False}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
