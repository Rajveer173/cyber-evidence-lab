"""Reconcile a treasury settlement manifest with an offline eth_getLogs export."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def fixed(value, size):
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{%d}" % (size * 2), value):
        raise ValueError(f"Expected {size}-byte hex data")
    return value.lower()


def quantity(value):
    if not isinstance(value, str) or not re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)", value):
        raise ValueError("Invalid JSON-RPC quantity")
    return int(value, 16)


def participant(word):
    value = fixed(word, 32)
    if value[2:26] != "0" * 24:
        raise ValueError("Invalid indexed address padding")
    return "0x" + value[26:]


def reconcile(case, logs):
    treasury = fixed(case["treasury"], 20)
    tokens = {fixed(token, 20) for token in case["tokens"]}
    blocks = {int(height): fixed(h, 32) for height, h in case["blocks"].items()}
    expected = defaultdict(int)
    tickets = defaultdict(list)
    used = set()
    for order in case["payments"]:
        key = fixed(order["tx"], 32), fixed(order["token"], 20), fixed(order["to"], 20)
        ticket = order["ticket"]
        if key[1] not in tokens or ticket in used or not re.fullmatch("[1-9][0-9]*", order["units"]):
            raise ValueError("Invalid or repeated payment in manifest")
        expected[key] += int(order["units"])
        tickets[key].append(ticket)
        used.add(ticket)

    observed = defaultdict(int)
    sources = defaultdict(list)
    seen = {}
    audit = []
    for row, event in enumerate(logs, 1):
        height = quantity(event["blockNumber"])
        block = fixed(event["blockHash"], 32)
        idx = quantity(event["logIndex"])
        tx = fixed(event["transactionHash"], 32)
        token = fixed(event["address"], 20)
        topics = [fixed(t, 32) for t in event["topics"]]
        if type(event["removed"]) is not bool:
            raise ValueError("Expected boolean removed flag")
        if event["removed"]:
            reason = "removed"
        elif height not in blocks:
            raise ValueError(f"Missing trusted block reference for height {height}")
        elif block != blocks[height]:
            reason = "other_block_hash"
        elif token not in tokens:
            reason = "untracked_contract"
        elif topics[:1] != [TRANSFER]:
            reason = "other_event"
        else:
            if len(topics) != 3:
                raise ValueError("Malformed transfer topics")
            sender, recipient = map(participant, topics[1:])
            units = int(fixed(event["data"], 32), 16)
            identity = block, idx
            payload = tx, token, sender, recipient, units
            if identity in seen and seen[identity] != payload:
                raise ValueError(f"Conflicting transfer at height {height}, index {idx}")
            if identity in seen:
                reason = "duplicate"
            elif sender != treasury:
                reason = "other_sender"
            else:
                key = tx, token, recipient
                observed[key] += units
                sources[key].append(row)
                reason = "counted"
            seen[identity] = payload
        audit.append(dict(row=row, height=height, index=idx, tx=tx, decision=reason))

    findings = []
    for key in sorted(set(expected) | set(observed)):
        planned, actual = expected.get(key, 0), observed.get(key, 0)
        status = "matched"
        if key not in expected:
            status = "unlisted_transfer"
        elif key not in observed:
            status = "unobserved_payment"
        elif actual != planned:
            status = "amount_mismatch"
        findings.append(dict(tx=key[0], token=key[1], recipient=key[2], tickets=tickets[key],
                             expected_units=str(planned), observed_units=str(actual),
                             evidence_rows=sources[key], status=status))
    return dict(chain_id=case["chain_id"], findings=findings, audit=audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("logs", type=Path)
    args = parser.parse_args()
    inputs = {"case": args.case.read_bytes(), "logs": args.logs.read_bytes()}
    report = reconcile(json.loads(inputs["case"]), json.loads(inputs["logs"]))
    report["input_sha256"] = {k: hashlib.sha256(v).hexdigest() for k, v in inputs.items()}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as err:
        sys.exit(f"Review incomplete: {err}")
