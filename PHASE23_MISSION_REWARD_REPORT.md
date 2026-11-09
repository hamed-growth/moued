# Phase 2.3 — Mission Reward Integrity

## Historical baseline

Before code changes, all 32 Phase 2.2 tests passed on disposable file-backed SQLite. The historical test `test_mission_approval_rejection_and_reapproval` asserted that dashboard approval awarded 10 points and 4 coins, rejection changed the approved status without reversing that reward, and reapproval left 20 points, 8 coins and two identical mission ledger entries. The latter assertions represent the defect. This phase suspends cross-terminal transitions pending a product decision and retains the first reward and same-state retry assertions.

## Status

**PARTIALLY COMPLETED.** The current-schema pending-review workflow is atomic and single-winner. Historical per-request attribution and a permanent reversal or reopening policy require additional decisions.

## Legacy workflow and entry points

- Dashboard approval and rejection are staff-only POSTs in dashboard/views.py. Both call MissionRequest model methods. The legacy methods checked the Python instance state, saved reviewer and status, then approval created a MissionCompletion. Completion.save issued the points, coins and mission ledger entry in separate writes.
- Django Admin bulk actions in missions/admin.py already filtered pending requests and used those methods. Its regular request form exposed status directly, so it could save approved without issuing rewards or reopen a previously reviewed record. Status is now read-only there and the actions require the existing model change permission. No dashboard role was changed.
- The standalone MissionCompletion Admin add form creates a completion and rewards independently of a request. It retains that capability with atomic reward writes. There is no reliable request identity at that entry point. Editing an existing completion retains its previous behavior and does not reissue the reward.

| Transition | Legacy | Safe behavior in this phase | Financial and compatibility effect | Product decision |
| --- | --- | --- | --- | --- |
| pending → approved | Created completion and reward with separate writes | One conditional claim, followed by atomic completion, balances, ledger and reviewer data | Same amount and team override; partial writes roll back | Covered by this phase |
| pending → rejected | Saved rejection metadata, no reward | One conditional claim and no reward | First reviewer and note are retained | Covered by this phase |
| approved → approved | Usually returned false, but stale pending copies could award again | No-op based on persisted status | No extra reward | Covered by this phase |
| rejected → rejected | Usually returned false, but stale copies could overwrite metadata | No-op based on persisted status | No reward or reviewer overwrite | Covered by this phase |
| approved → rejected | Dashboard could reject without reversing reward | Suspended pending decision | No reversal, existing reviewed status retained. May affect operators using rejection as a correction | Required to define reversal, retained reward or a compensating adjustment |
| rejected → approved | Dashboard could approve, including after a prior approval and rejection | Suspended pending decision | No new reward, including for never-rewarded legacy rejected requests. Manual reopening workflow is unavailable | Required to define reopening and identify or reconcile any prior reward |

A permanent reopening policy needs reliable attribution. MissionRequest, MissionCompletion and PointTransaction have no per-request relation. A mission and user can legitimately recur, completion timestamp need not equal request timestamp, and transaction title is descriptive. Zero reward amounts cannot distinguish never rewarded from a legitimate zero-value reward. No schema change, historical repair or permanent policy was inferred.

## Implementation

- MissionRequest.approve and reject begin with a conditional UPDATE against the request primary key and persisted pending status, then verify the affected-row count. The first writer claims the transition. Approval refreshes the claimed record, creates a completion, and copies the actual awarded amounts from that completion to the request. All writes, including reviewer metadata, are in the outer transaction.
- MissionCompletion.save remains the only reward issuer for completion creation. Creation computes the existing base or team rewards once. Completion, F-expression balance increments, existing UTC-date activity streak logic and ledger insert are atomic, including standalone completion creation. Competition and daily-question reward methods were preserved.
- Ordinary saves of an existing MissionRequest omit workflow fields so a stale object cannot restore pending or overwrite review status, reviewer, date or award amounts. An unqualified save also omits the review note. Django Admin saves only the form fields actually changed, which still permits explicit note edits.
- Dashboard database errors during the review operation are logged and return generic HTTP 503 after rollback. Admin action exceptions surface as failed requests, and each selected request has its own transaction. Earlier successful requests in a bulk action can remain committed if a later request fails. No failure is treated as a successful review.
- SQLite writers still serialize and lock errors remain possible under contention. No global setting changed. The mission concurrency tests exercised independent connections with concurrent approval and approval/rejection, and did not force a real mission-specific lock timeout. The dashboard failure response was verified with injected DatabaseError. Raw SQL, direct QuerySet.update outside the review methods, and independent manual completions do not gain per-request attribution from this fix.

## Read-only historical analysis

Queries ran on the isolated SQLite backup copy with mode=ro and immutable=1. The copy had three pending and three approved requests, no rejected requests, three completion records and three mission ledger entries. None of the approved requests lacked a candidate completion by user, mission, team and completion time at or after submission. None of the pending requests showed reviewer metadata or nonzero award fields. There were no rejected requests with nonzero award fields or candidate completions.

These are aggregate and candidate counts. Duplicate transactions and missing rewards per request remain uncertain because the tables lack a reliable request link. One user had at least one balance that differed from the sum of ledger deltas. This is a reconciliation signal and does not establish an error because administrative adjustments or opening balances may exist. No records were altered.

## Verification

Used Phase 1.7 env-a on the external phase23-check copy. The safety check confirmed a single SQLite alias, memory-only default database, fresh disposable file-backed test database under the isolated copy, and locmem email. The test runner created and destroyed its database.

| Result | Count |
| --- | --- |
| Pre-change Phase 2.2 baseline | 32 PASS |
| Post-change baseline with one intentional mission assertion update | 32 PASS |
| New sequential mission tests | 8 PASS |
| New independent-connection mission races | 2 PASS |
| Final total | 42 PASS, 0 failures, 0 skipped |

The two approval threads produced exactly one successful transition, completion and ledger entry. The approval/rejection race also produced exactly one winner, with matching reviewer metadata and balances. The tests cover dashboard submission and unauthorized approval, base and team rewards, stale saves, repeat approvals and rejections, the temporary freeze, Django Admin actions and direct form edits, plus rollback after completion, balance and ledger writes. Both pip check and manage.py check passed.

```powershell
python -B -m pip check
python -B manage.py check
python -B manage.py test missions.test_behavioral_baseline missions.test_authorization missions.test_treasure_transactions missions.test_mission_rewards --settings=mouod.phase23_settings -v 2
```

## Files, hashes and rollback

Changed missions/models.py, missions/admin.py, dashboard/views.py and missions/test_behavioral_baseline.py. Added missions/test_mission_rewards.py and this report. Outside source, phase23-check contains an isolated source/database copy and a copied file-backed test settings module. phase23-backup contains original files and SHA256.txt.

| Original path | SHA-256 |
| --- | --- |
| missions/models.py | 38e5cf9373bcbb71cfaf8c49ca1a09eaf390ec5a12f09f696c05dcaaf1993ca6 |
| missions/admin.py | e504765cd6e47fa8c84721c627b6e6f64852c2090710eddfed681d2097fe158e |
| dashboard/views.py | d31b79017dd07cba5e2abfcf37ccee722c3bde3a7dd62f316cc05d36f48b7db9 |
| missions/test_behavioral_baseline.py | 61573d662068b3c3ba40372edb96ca3cc0ab5934f47a0846398c2e15e6e64a52 |

Before editing, hashes in the Phase 1 and Phase 2.2 backups were verified and each of the four files was independently backed up. To roll back, verify SHA256.txt and restore the four paths from `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase23-backup`. Remove the new mission test module from the reverted suite and retain this report. No database restore is needed for a code rollback. Rollback reopens the original duplicate and partial reward paths.

Original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c. The media inventory and bytes match the backup, archived migration files match byte for byte, and purchase code and its tests match the Phase 2.2 verification copy. No migration is required. Work stopped at Phase 2.3.
