# ExitGraph | Offboarding access review

Finance says Mira's billing membership was removed after departure. Does the invoice archive remain reachable? This offline reviewer joins an HR roster, directed membership edges and resource grants. It emits a shortest witness path per entitlement, recomputes reachability after proposed changes and flags active employees losing access.

Run from this folder with Python 3.11.

```powershell
python exitgraph.py snapshot.json
python exitgraph.py snapshot.json --remove narrow-cut.json
python exitgraph.py snapshot.json --remove shared-cut.json
```

**Review decision.** The first proposal removes Mira's billing membership. Rotation still grants archive access. The shared proposal also leaves that route intact and costs Dev access to the archive. Reject the shared change. Removing both of Mira's memberships would close her group-derived access. The support-export owner grant requires separate review and transfer to an accountable owner.

**Data contract.** People map unique principal IDs to active or departed. Membership pairs point from member to containing group. Grants contain principal, resource and role. Direct grants and cycles are supported. The simulator changes membership edges only. Match stable IDs across exports and capture them at the same time. This additive model cannot represent exclusions, conditional policies, session revocation or enforcement at the application. Results describe the supplied snapshot.

**Implementation choice.** Breadth-first traversal records one predecessor per visited principal, bounding traversal per user by vertices plus edges. Recomputing after a cut exposes surviving alternate paths without enumerating every possible path.
