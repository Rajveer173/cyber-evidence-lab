"""Explain residual access and replay candidate membership removals offline."""
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path


def inspect(snapshot, removals=()):
    edges = set(map(tuple, snapshot["memberships"]))
    cuts = set(map(tuple, removals))
    if cuts - edges:
        raise ValueError(f"Unknown membership removals: {sorted(cuts - edges)}")
    graph = defaultdict(list)
    for child, parent in sorted(edges - cuts):
        graph[child].append(parent)
    grants = defaultdict(list)
    for principal, resource, role in snapshot["grants"]:
        grants[principal].append((resource, role))
    findings = {}
    for user in sorted(snapshot["people"]):
        queue = deque([user])
        predecessor = {user: None}
        while queue:
            node = queue.popleft()
            for resource, role in grants[node]:
                access = (user, resource, role)
                if access not in findings:
                    path = [node]
                    while predecessor[path[-1]] is not None:
                        path.append(predecessor[path[-1]])
                    findings[access] = list(reversed(path))
            for parent in graph[node]:
                if parent not in predecessor:
                    predecessor[parent] = node
                    queue.append(parent)
    return findings


def compare(snapshot, removals):
    before = inspect(snapshot)
    after = inspect(snapshot, removals)
    report = dict(residual=[], resolved=[], active_access_lost=[])
    for key, path in sorted(before.items()):
        user, resource, role = key
        status = snapshot["people"][user]
        if status not in ("active", "departed"):
            raise ValueError(f"Unknown status {status}")
        if status == "active" and key in after:
            continue
        category = "active_access_lost" if status == "active" else "residual" if key in after else "resolved"
        report[category].append(dict(user=user, resource=resource, role=role,
                                     before_path=path, after_path=after.get(key)))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--remove", type=Path)
    args = parser.parse_args()
    cuts = json.loads(args.remove.read_text()) if args.remove else []
    print(json.dumps(compare(json.loads(args.snapshot.read_text()), cuts), indent=2))
