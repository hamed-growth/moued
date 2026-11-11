# Unresolved technical debt

This refactoring preserves these issues; none is declared fixed.

| Issue | Consequence / next decision |
| --- | --- |
| Competition answer admission races finalization | Define strict cutoff versus admitted-answer completion before changing transactions |
| Suspended mission reopening and reward reversal | Product decision plus historical reconciliation required |
| Treasure replay without request idempotency key | A repeated funded request can create another purchase |
| Incomplete historical reward attribution | Existing ledgers lack an unambiguous mission-request reference |
| Staff account activation policy | Define which accounts ordinary staff may activate/deactivate |
| Jalali monthly reporting | Existing naive datetime warnings and Gregorian grouping semantics preserved |
| SQLite writer concurrency | Tested races preserve invariants; real contention can still fail with the existing 503 response |
| Production settings | DEBUG, hosts, secret, mail, HTTPS/cookies and media serving are not deployment-ready |
| Admin competition finalization action | Previously proven view-only permission gap remains; no authorization changes in this task |
| Login `next` redirect | Existing external redirect behavior remains |
| Default login redirect | `/accounts/login/` has no configured route |
| Archive template | Existing authenticated archive rendering lacks `missions/archive.html` |
| Daily question template | Synthetic question fixture reproduces `NoReverseMatch` for `leaderboard`, before and after modernization |
| Daily answer reward save hook | Insert and reward writes are not one newly hardened service; preserve until separately covered/reviewed |
| Direct administrative balance/model editing | Not all writes flow through a shared wallet; do not claim a centralized ledger |
| Duplicate treasure route | Preserved deliberately as part of the external URL inventory |

## Performance evidence and opportunities

The same synthetic fixture (three users, one team, global/team/private missions, a pending request, one daily question and one active contest) was rendered before and after. Query counts include authentication, context processors and template rendering. All 39 role/page snapshots matched exactly.

| Page / role | Before | After |
| --- | ---: | ---: |
| Homepage / ordinary user | 11 | 11 |
| Profile / ordinary user | 20 | 20 |
| League / ordinary user | 10 | 10 |
| Competition list / ordinary user | 6 | 6 |
| Treasure / ordinary user | 7 | 7 |
| Dashboard home / staff | 24 | 24 |

No performance improvement is claimed. These small-fixture measurements are not capacity tests. Pending mission reward calculations can fetch per-request teams/overrides; dashboard has seven per-day counts and separate aggregates. Rankings read all teams/members; some dashboard lists are capped but not paginated. Consider measured aggregation and pagination work separately, preserving visibility, ordering, tie behavior and calendar semantics. Redis, Celery, PostgreSQL and caching were not added.
