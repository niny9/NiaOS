"""Isolated workflow wiring/receipt tests; all financial inputs are synthetic."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "skills"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow = load("invest_workflow", ROOT / "invest-os/scripts/invest_workflow.py")
bridge = load("invest_bridge", ROOT / "invest-os/scripts/connect_existing.py")
MANIFEST = ROOT / "invest-os/references/workflow.json"
TIME = "2026-10-25T12:00:00+08:00"


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skills = self.root / "skills"
        self.results = self.root / "results"
        self.results.mkdir()
        stages = json.loads(MANIFEST.read_text())["stages"]
        names = {s["owner_skill"] for s in stages} | {x for s in stages for x in s["provider_skills"]}
        for name in names | {"invest-os"}:
            directory = self.skills / name
            directory.mkdir(parents=True)
            filename = "skill.md" if name == "investment-workflow" else "SKILL.md"
            (directory / filename).write_text(f"---\nname: {name}\ndescription: Synthetic fixture\n---\nOriginal content.\n")
        scriptdir = self.skills / "nia-wealth-holdings/scripts"
        scriptdir.mkdir()
        shutil.copy(ROOT / "nia-wealth-holdings/scripts/validate_snapshot.py", scriptdir)
        self.bindings = self.root / "bindings.json"
        self.bindings.write_text(json.dumps({"holdings_file": None, "goals_file": None, "risk_policy_file": None}))

    def prepare(self):
        return workflow.prepare(MANIFEST, [self.skills], self.bindings, TIME, 2)

    def receipts(self, plan, complete=False):
        for task in plan["tasks"]:
            sid = task["id"]
            status = "complete" if complete or sid == "brief" else "degraded"
            output = {"holdings": {"validation_ok": complete},
                      "risk": {"gate": "pass" if complete else "unknown", "policy_confirmed": complete},
                      "market": {"market_rules_verified": complete},
                      "trade_plan": {"plans": []}}.get(sid, {})
            record = {"schema_version": "invest.stage.v1", "run_id": plan["run_id"], "plan_hash": plan["plan_hash"],
                      "stage_id": sid, "status": status, "generated_at": TIME,
                      "summary": "Synthetic test result only", "consumed_stages": task["depends_on"],
                      "evidence": [{"source_ref": "synthetic-test", "source_as_of": TIME}] if status == "complete" else [],
                      "output": output}
            (self.results / (sid + ".json")).write_text(json.dumps(record))

    def mutate(self, stage, update):
        path = self.results / (stage + ".json")
        data = json.loads(path.read_text())
        update(data)
        path.write_text(json.dumps(data))

    def check(self, plan, time=TIME):
        return workflow.check_results(plan, self.results, time)

    def attach_snapshot(self):
        snapshot = {"schema_version":"wealth.snapshot.v1", "snapshot_id":"synthetic", "as_of":TIME,
                    "source_ref":"synthetic-only", "confirmed_by_user":True, "accounts_complete":True,
                    "pending_activity":False, "empty_positions_confirmed":True, "base_currency":"CNY",
                    "positions":[], "cash_cny":1000, "reported_investable_assets_cny":1000}
        (self.root / "snapshot.json").write_text(json.dumps(snapshot))
        self.bindings.write_text(json.dumps({"holdings_file":"snapshot.json"}))

    def test_all_fifteen_existing_and_new_modules_resolve(self):
        plan = self.prepare()
        self.assertTrue(plan["ready_for_agent"])
        self.assertEqual(len(plan["skills"]), 15)
        self.assertEqual(len(plan["tasks"]), 9)
        self.assertTrue(plan["skills"]["investment-workflow"]["path"].endswith("skill.md"))
        self.assertFalse(plan["research_executed"])
        self.assertFalse(plan["preflight"]["holdings"]["ok"])

    def test_prepare_never_calls_legacy_runner_or_notifier(self):
        before = sorted(str(p) for p in self.root.rglob("*"))
        with patch.object(workflow.subprocess, "run") as call:
            self.prepare()
            call.assert_not_called()
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))

    def test_probe_only_invokes_status(self):
        script = self.skills / "finance-quant-closed-loop/scripts/finance_quant_control.py"
        script.parent.mkdir()
        script.write_text("# synthetic stub, not executed\n")
        with patch.object(workflow.subprocess, "run") as call:
            call.return_value.stdout = json.dumps({"freshness":{"overall":"partial"},"closure":{"operational":False}})
            call.return_value.returncode = 0
            p = workflow.prepare(MANIFEST,[self.skills],self.bindings,TIME,2,True)
            self.assertIn("status",call.call_args.args[0])
            self.assertNotIn("--execute",call.call_args.args[0])
            self.assertNotIn("--send",call.call_args.args[0])
            self.assertFalse(p["preflight"]["quant"]["operational"])

    def test_missing_skill_and_bad_graph(self):
        (self.skills / "nia-wealth-risk/SKILL.md").unlink()
        self.assertFalse(self.prepare()["ready_for_agent"])
        manifest = json.loads(MANIFEST.read_text())
        manifest["stages"][0]["depends_on"] = ["brief"]
        with self.assertRaises(ValueError):
            workflow.validate_manifest(manifest)

    def test_missing_receipts_are_incomplete(self):
        result = self.check(self.prepare())
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "incomplete")

    def test_degraded_run_can_be_reported_but_not_full_success(self):
        plan = self.prepare()
        self.receipts(plan)
        result = self.check(plan)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["status"], "degraded")
        self.assertFalse(result["trade_authorized"])

    def test_numeric_trade_is_blocked_when_holdings_unknown(self):
        plan = self.prepare()
        self.receipts(plan)
        self.mutate("trade_plan", lambda r:r["output"].update(plans=[{"state":"proposed","executable":False,"quantity":100,"amount_cny":None}]))
        self.assertFalse(self.check(plan)["accepted"])

    def test_false_complete_is_rejected(self):
        plan = self.prepare()
        self.receipts(plan, complete=True)
        self.assertFalse(self.check(plan)["accepted"])

    def test_fully_evidenced_fixture_and_expired_snapshot(self):
        self.attach_snapshot()
        plan = self.prepare()
        self.receipts(plan, complete=True)
        self.mutate("trade_plan", lambda r:r["output"].update(plans=[{"state":"proposed","executable":False,"quantity":1,"amount_cny":None}]))
        self.assertTrue(self.check(plan)["accepted"])
        self.assertFalse(self.check(plan,"2026-10-25T15:00:00+08:00")["accepted"])

    def test_identity_version_and_input_changes_rejected(self):
        plan = self.prepare()
        self.receipts(plan)
        self.mutate("brief", lambda r:r.update(run_id="wrong-run"))
        self.assertFalse(self.check(plan)["accepted"])
        self.receipts(plan)
        self.bindings.write_text('{"holdings_file":null}')
        self.assertFalse(self.check(plan)["accepted"])

    def test_dependency_and_future_timestamp_rejected(self):
        plan = self.prepare()
        self.receipts(plan)
        self.mutate("diagnosis", lambda r:r.update(consumed_stages=[]))
        self.assertFalse(self.check(plan)["accepted"])
        self.receipts(plan)
        self.mutate("brief", lambda r:r.update(generated_at="2026-10-26T12:00:00+08:00"))
        self.assertFalse(self.check(plan)["accepted"])

    def test_bridge_is_idempotent_and_backed_up(self):
        target = self.skills / "finance-quant-closed-loop/SKILL.md"
        original = target.read_text()
        backup = self.root / "backups"
        dry = bridge.connect(self.skills,self.skills,backup,False)
        self.assertEqual(target.read_text(),original)
        self.assertFalse(dry["applied"])
        bridge.connect(self.skills,self.skills,backup,True)
        changed = target.read_text()
        again = bridge.connect(self.skills,self.skills,backup,True)
        self.assertEqual(target.read_text(),changed)
        self.assertTrue(all(x["status"]=="unchanged" for x in again["results"]))
        self.assertEqual(changed.count(bridge.START),1)
        self.assertIn(original.split('---\n')[-1].strip(),changed)
        self.assertIn(original,[p.read_text() for p in backup.glob('*.md')])


if __name__ == "__main__":
    unittest.main()
