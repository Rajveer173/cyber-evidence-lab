import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent


def run(project, *args):
    output = subprocess.check_output([sys.executable, project + ".py", *args],
                                     cwd=ROOT / project, text=True)
    return json.loads(output)


class ReplayTests(unittest.TestCase):
    def feed(self, time):
        return run("feedwatch", "plan.json", "receipts.csv", "--as-of", "2026-10-01T" + time + "Z")

    def test_early(self):
        report = self.feed("09:12:00")
        self.assertEqual(report["counts"], dict(on_time=4, missing=2, late=0, pending=0))
        self.assertEqual(report["duplicates"], 0)

    def test_pending(self):
        self.assertEqual(self.feed("09:00:00")["counts"]["pending"], 2)

    def test_backfill(self):
        report = self.feed("09:30:00")
        self.assertEqual(report["counts"], dict(on_time=9, late=2, missing=1, pending=0))
        self.assertEqual(report["duplicates"], 1)
        self.assertEqual(len(report["windows"]), 1)

    def test_alternate_path(self):
        report = run("exitgraph", "snapshot.json", "--remove", "narrow-cut.json")
        self.assertEqual(len(report["residual"]), 2)
        self.assertEqual(report["residual"][0]["after_path"], ["mira", "rotation", "finance"])
        self.assertEqual(report["residual"][1]["after_path"], ["mira"])

    def test_collateral(self):
        report = run("exitgraph", "snapshot.json", "--remove", "shared-cut.json")
        self.assertEqual([entry["user"] for entry in report["active_access_lost"]], ["dev"])
