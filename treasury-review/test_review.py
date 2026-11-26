import json
from pathlib import Path
import unittest

from review import reconcile

ROOT = Path(__file__).resolve().parent


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((ROOT / "case.json").read_bytes())
        self.logs = json.loads((ROOT / "logs.json").read_bytes())

    def report(self):
        return reconcile(self.case, self.logs)

    def test_balanced_batch_wrong_payee(self):
        rows = self.report()["findings"]
        self.assertEqual(sum(int(r["expected_units"]) for r in rows),
                         sum(int(r["observed_units"]) for r in rows))
        self.assertEqual([r["status"] for r in rows],
                         ["matched", "unobserved_payment", "unlisted_transfer"])
        self.assertEqual(rows[0]["evidence_rows"], [1, 2])

    def test_filter_decisions(self):
        self.assertEqual([e["decision"] for e in self.report()["audit"]],
                         ["counted"] * 3 + ["duplicate", "other_block_hash", "untracked_contract"])

    def test_conflicting_evidence(self):
        self.logs[3]["data"] = self.logs[0]["data"]
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.report()

    def test_missing_reference(self):
        self.case["blocks"].clear()
        with self.assertRaisesRegex(ValueError, "reference"):
            self.report()

    def test_removed_payment(self):
        self.logs[2]["removed"] = True
        self.assertEqual(self.report()["audit"][2]["decision"], "removed")

    def test_integer_precision(self):
        self.logs[2]["data"] = "0x" + "f" * 64
        self.assertEqual(self.report()["findings"][2]["observed_units"], str(2**256 - 1))

    def test_correct_recipient(self):
        self.logs[2]["topics"][2] = self.logs[4]["topics"][2]
        self.assertEqual([r["status"] for r in self.report()["findings"]], ["matched"] * 2)

    def test_short_payment(self):
        self.logs.pop(0)
        self.assertEqual(self.report()["findings"][0]["status"], "amount_mismatch")
