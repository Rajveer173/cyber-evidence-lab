# FeedWatch | Investigating missing telemetry

At 09:12 UTC the identity collector appears to have missed two scheduled canaries. Should the SOC declare a collector outage? Replay the same synthetic receipt ledger at two investigation times. Run these commands from this folder with Python 3.11.

```powershell
python feedwatch.py plan.json receipts.csv --as-of 2026-10-01T09:12:00Z
python feedwatch.py plan.json receipts.csv --as-of 2026-10-01T09:30:00Z
```

At 09:12 the 09:05 and 09:10 identity slots are missing. All three endpoint receipts arrived within the two-minute allowance. By 09:30 two identity slots have arrived late, one is still missing and nine slots across both sources met deadline. A duplicate delivery of the 09:05 receipt counts once toward coverage.

**Triage decision.** Scope the investigation to the identity feed first. Retrieve the sender's acknowledgement for 09:10 and compare it with the collector queue and ingestion errors. The ledger establishes when data was visible. It cannot distinguish a failed sender from a dropped message. Canaries measure pipeline availability and give no assurance that every production event arrived.

**Bring your own export.** Define each feed's inclusive start, exclusive end, positive interval and nonnegative grace in the plan. Supply a CSV with the same three columns as the example. Slot is the scheduled emission time and received is the collector timestamp. Both require UTC or an explicit offset. The tool tolerates unordered rows, uses the first observed delivery, lists unmatched slots and ignores future arrivals during historical replay. The batch implementation holds the ledger in memory.
