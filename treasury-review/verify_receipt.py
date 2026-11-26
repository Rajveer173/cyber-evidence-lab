"""Cross-check the archived case against a separately selected Ethereum RPC node."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from urllib.request import Request, urlopen

from review import fixed, quantity

FIELDS = ("blockHash", "blockNumber", "transactionHash", "logIndex", "address", "topics", "data", "removed")


def ethereum(endpoint, method, params):
    body = json.dumps(dict(jsonrpc="2.0", id=1, method=method, params=params)).encode()
    req = Request(endpoint, body, {"Content-Type": "application/json", "User-Agent": "TreasuryReview/1"})
    with urlopen(req, timeout=20) as response:
        reply = json.load(response)
    if "error" in reply or reply.get("result") is None:
        raise ValueError(f"{method} returned no usable result")
    return reply["result"]


def verify(case, archive, rpc):
    if quantity(rpc("eth_chainId", [])) != case["chain_id"]:
        raise ValueError("Chain ID mismatch")
    archives = defaultdict(list)
    for event in archive:
        archives[fixed(event["transactionHash"], 32)].append(event)
    transactions = set(archives) | {fixed(row["tx"], 32) for row in case["payments"]}
    if not transactions:
        raise ValueError("No transactions to verify")
    finalized = rpc("eth_getBlockByNumber", ["finalized", False])
    for tx in sorted(transactions):
        verify_transaction(case, archives[tx], tx, rpc, quantity(finalized["number"]))
    return len(archive)


def verify_transaction(case, archive, tx, rpc, finalized_height):
    receipt = rpc("eth_getTransactionReceipt", [tx])
    if receipt["transactionHash"] != tx or quantity(receipt["status"]) != 1:
        raise ValueError("Expected a successful receipt for the selected transaction")
    height = receipt["blockNumber"]
    canonical = rpc("eth_getBlockByNumber", [height, False])
    pinned = case["blocks"][str(quantity(height))]
    if not (canonical["hash"] == pinned == receipt["blockHash"]) or finalized_height < quantity(height):
        raise ValueError("Receipt block failed canonical or finalized-height check")

    def project(rows):
        return [{key: row[key] for key in FIELDS} for row in rows]

    if project(archive) != project(receipt["logs"]):
        raise ValueError("Archived log sequence differs from receipt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--case-dir", type=Path, default=Path(__file__).parent / "public-case",
                        help="Directory containing case.json and complete receipt logs in logs.json")
    args = parser.parse_args()
    directory = args.case_dir
    try:
        count = verify(json.loads((directory / "case.json").read_bytes()),
                       json.loads((directory / "logs.json").read_bytes()),
                       lambda method, params: ethereum(args.rpc, method, params))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Verification incomplete: {error}\n")
    print(f"Verified {count} archived logs against finalized transaction receipts.")
