"""Cross-check the archived case against a separately selected Ethereum RPC node."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

from review import quantity

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
    tx, = {row["tx"] for row in case["payments"]}
    receipt = rpc("eth_getTransactionReceipt", [tx])
    if receipt["transactionHash"] != tx or quantity(receipt["status"]) != 1:
        raise ValueError("Expected a successful receipt for the selected transaction")
    height = receipt["blockNumber"]
    canonical = rpc("eth_getBlockByNumber", [height, False])
    finalized = rpc("eth_getBlockByNumber", ["finalized", False])
    pinned = case["blocks"][str(quantity(height))]
    if not (canonical["hash"] == pinned == receipt["blockHash"]) or quantity(finalized["number"]) < quantity(height):
        raise ValueError("Receipt block failed canonical or finalized-height check")

    def project(rows):
        return [{key: row[key] for key in FIELDS} for row in rows]

    if project(archive) != project(receipt["logs"]):
        raise ValueError("Archived log sequence differs from receipt")
    return len(archive)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", required=True)
    args = parser.parse_args()
    directory = Path(__file__).parent / "public-case"
    try:
        count = verify(json.loads((directory / "case.json").read_bytes()),
                       json.loads((directory / "logs.json").read_bytes()),
                       lambda method, params: ethereum(args.rpc, method, params))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Verification incomplete: {error}\n")
    print(f"Verified {count} archived logs against the finalized receipt.")
