import json
from pathlib import Path
import unittest

from review import reconcile
from verify_receipt import verify

ROOT = Path(__file__).parent / "public-case"


class ArchivedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((ROOT / "case.json").read_bytes())
        self.logs = json.loads((ROOT / "logs.json").read_bytes())
        self.block = self.logs[0]["blockHash"]
        self.height = self.logs[0]["blockNumber"]
        self.receipt = dict(transactionHash=self.logs[0]["transactionHash"], status="0x1",
                            blockNumber=self.height, blockHash=self.block, logs=self.logs)

    def rpc(self, method, params):
        if method == "eth_chainId":
            return "0x1"
        if method == "eth_getTransactionReceipt":
            return self.receipt
        return dict(number=self.height, hash=self.block)

    def test_full_public_receipt(self):
        self.assertEqual(verify(self.case, self.logs, self.rpc), 13)
        rows = reconcile(self.case, self.logs)["findings"]
        self.assertEqual([entry["status"] for entry in rows], ["matched"] * 7)

    def test_dropped_row(self):
        with self.assertRaisesRegex(ValueError, "sequence"):
            verify(self.case, self.logs[:-1], self.rpc)

    def test_also_verifies_unlisted_transaction(self):
        extra_tx = "0x" + "ef" * 32
        extra_log = dict(self.logs[0], transactionHash=extra_tx, logIndex="0xff")
        def batch_rpc(method, params):
            if method == "eth_getTransactionReceipt" and params == [extra_tx]:
                return dict(self.receipt, transactionHash=extra_tx, logs=[extra_log])
            return self.rpc(method, params)
        self.assertEqual(verify(self.case, [extra_log, *self.logs], batch_rpc), 14)
        with self.assertRaisesRegex(ValueError, "sequence"):
            verify(self.case, [dict(extra_log, data="0x"), *self.logs], batch_rpc)

    def test_unfinalized_height(self):
        def behind(method, params):
            if params == ["finalized", False]:
                return dict(number="0x1")
            return self.rpc(method, params)
        with self.assertRaisesRegex(ValueError, "finalized"):
            verify(self.case, self.logs, behind)
