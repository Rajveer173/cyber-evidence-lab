"""Replay expected canaries against the collector's receipt ledger."""
import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def instant(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"Missing timezone in {value}")
    return dt.astimezone(timezone.utc)


def analyze(plan, receipts, as_of):
    ledger = {}
    duplicates = 0
    for row in receipts:
        key = (row["feed"], row["slot"])
        arrival = instant(row["received"])
        if arrival > as_of:
            continue
        if key in ledger:
            duplicates += 1
            ledger[key] = min(ledger[key], arrival)
        else:
            ledger[key] = arrival

    windows = []
    counts = dict(on_time=0, late=0, missing=0, pending=0)
    for feed, config in sorted(plan.items()):
        slot = instant(config["start"])
        stop = instant(config["end"])
        step = timedelta(minutes=config["interval_minutes"])
        grace = timedelta(minutes=config["grace_minutes"])
        if step <= timedelta(0) or grace < timedelta(0) or stop <= slot:
            raise ValueError(f"Invalid schedule for {feed}")
        window = None
        while slot < stop and slot <= as_of:
            key = (feed, slot.isoformat())
            arrival = ledger.pop(key, None)
            deadline = slot + grace
            if arrival and arrival < slot:
                raise ValueError(f"Receipt predates slot {key}")
            if arrival:
                state = "on_time" if arrival <= deadline else "late"
            else:
                state = "pending" if as_of < deadline else "missing"
            counts[state] += 1
            if state in ("missing", "late"):
                if window is None:
                    window = dict(feed=feed, first_deadline=deadline.isoformat(), slots=[])
                    windows.append(window)
                window["slots"].append(dict(expected=slot.isoformat(), state=state,
                                            received=arrival.isoformat() if arrival else None))
            else:
                window = None
            slot += step
    return dict(as_of=as_of.isoformat(), counts=counts, duplicates=duplicates,
                unexpected=[dict(feed=f, slot=s) for f,s in sorted(ledger)], windows=windows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("receipts", type=Path)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    with args.receipts.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["slot"] = instant(row["slot"]).isoformat()
    print(json.dumps(analyze(json.loads(args.plan.read_text()), rows, instant(args.as_of)), indent=2))


if __name__ == "__main__":
    main()
