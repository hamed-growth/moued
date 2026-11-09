# Phase 2.4 — Competition Finalization & Reward Integrity

**PARTIALLY COMPLETED.** Supported finalization and participant finishing commit their payouts atomically and claim each transition once. Late answers can still change a registration after winner selection. A permanent reconciliation or reopening policy is pending.

## Workflow and findings

- The dashboard finalization POST and Django Admin bulk finalization call Competition.finalize. Legacy code saved finished first, selected three registrations by descending total_correct and ascending finished_at, and wrote each balance, ledger entry and rank separately. A failure could strand a finished competition with incomplete prizes. Two stale objects could both pass the Python status check. Django Admin also let the competition form set finished without paying prizes, and its activation action could reset finished to active.
- The play page finishes expired or exhausted registrations. Answer submission can finish after time expiration, a reached cap or the accepted answer that reaches the cap. The manual finish POST also calls CompetitionRegistration.finish. It can run after competition finalization. Legacy finish saved completion first and then separately paid the positive stored answer score and positive participation bonus. The Django Admin registration form could reset is_completed.
- CompetitionQuestion supplies the existing question override or competition default. CompetitionAnswer records correctness, and answer submission updates score and counts before invoking finish when applicable. Finishing uses the stored score, with no score recomputation. Registration eligibility, time checks and scoring remain as before.
- Winner selection still considers only the first three rows, including unfinished registrations. It skips rows with zero correct answers, without backfilling. SQLite sorts NULL finish times first for ascending order. Exact ties have no explicit tertiary order. Prize amounts and ledger descriptions remain the same. Winner prizes can include zero, preserving the existing rank and ledger behavior.

## Changes and transaction boundaries

Competition.finalize conditionally updates the persisted row to finished only if it was not finished. The affected-row count gates the payout. The transaction then reads current prizes, ranks participants and writes balances and ledger entries before committing. The dashboard returns a generic 503 on a database error after rollback. Admin action errors surface as failures. Bulk operations commit each competition independently.

CompetitionRegistration.finish conditionally claims an incomplete persisted row, records the finish timestamp, refreshes the stored score and pays both existing reward components within one transaction. A loser in a duplicate manual POST gets the existing already-finished response. Competition payouts use one shared helper within this domain, with database-side point and activity updates and a matching ledger entry. Coins, mission reward code, treasure purchase code and daily question rewards were preserved.

Answer counter saves now limit their writes to scoring fields so an in-flight answer cannot overwrite rank or completion metadata. Answer creation and scoring are still separate writes. The Admin form now requires the finalization action to set finished, preserves a finished status on stale form saves, and activation excludes finished competitions. Registration completion status is read-only in Admin, and existing registration edits write only changed form fields. These narrow restrictions close the supported Admin bypasses pending a permanent correction policy. Other Admin edits and authorization rules retain their prior scope. Raw ORM updates, raw SQL and manual edits to scoring fields do not acquire payout attribution or permanent database enforcement.

## Verification

Used the Phase 1.7 offline Python 3.12.14 environment and the external phase24-check project copy. Before tests, assertions verified a single SQLite alias, memory-only default NAME, an unused disposable file-backed TEST.NAME under the isolated copy, and locmem email. All fixtures were synthetic. The runner created and removed its test database.

```powershell
python -B -m pip check
python -B manage.py check
python -B manage.py test --settings=mouod.phase24_settings -v 1
```

- **PASS** before editing. pip reported “No broken requirements found.” Django reported “System check identified no issues (0 silenced).” All 42 baseline tests passed.
- **PASS** after editing. Both checks returned the same results. The full suite reported “Ran 56 tests” and “OK”, with 0 failures and 0 skipped. The original 42 tests and their assertions were preserved.
- **PASS** nine new sequential tests covering ranking by correct count, unfinished and finish-time order, three prizes and zero-correct eligibility, stale and repeated finalization, failure after status claim, failure during a later ledger insert after an earlier prize, persisted participant score and repeated finish, rollback during participation payout, unauthorized POST, Admin finalization/activation and status form restrictions.
- **PASS** five new file-backed concurrency tests. Two finalizers yielded one committed winner payout. Two finishers yielded one answer payout and one participation payout. Concurrent finish and finalization both committed their distinct payouts without losing rank, completion or balance in the tested single-registration case. A real SQLite writer lock produced HTTP 503 and no payout, rank or finished status. Only the disposable worker connection used zero busy timeout.
- **PASS as characterization, unresolved as policy.** An answer paused after its eligibility checks and resumed after finalization still returned 200 and changed the correct count, while the already selected rank and prize stayed unchanged. The test confirms the existing late-answer window. It does not establish that ranking and answer admission are serialized.
- **NOT TESTED** sustained SQLite contention, cross-domain stale absolute balance writes, or exact tie ordering beyond the existing database sort. SQLite serializes writers and can reject a request under contention.

## Historical read-only findings

The isolated backup copy was opened read-only and immutable. It contained one active competition, one registration and one competition ledger entry. No completion flag/timestamp mismatches, ranked unfinished rows, invalid or duplicate ranks, or positive ranked candidates missing a rank in finished competitions were observed. There were no finished competitions in this snapshot. One account balance differed from summed ledger deltas, which can reflect opening balances or adjustments and does not establish a competition error. The schema does not link ledger rows to a competition, registration or payout purpose. Missing and duplicate historical payouts cannot be attributed by title alone. No records were repaired.

## Product decisions still required

| Question | Current behavior and risk | Alternative and compatibility impact |
| --- | --- | --- |
| Unfinished eligibility | Included in top three and NULL finish times sort first on SQLite | Exclude unfinished rows or define a separate rule. Either changes winners. |
| Finish during finalization | Both writes serialize, and winner order uses the finish timestamps visible at finalization | Define a cutoff, grace period or snapshot rule. This changes who can qualify and when payouts occur. |
| Answer during finalization | An answer already past its checks may still land after rank selection | Recheck admission under a write transaction for a strict cutoff, or drain admitted answers before ranking. Either changes late-request behavior. |
| Reopen and rerun | Ordinary retries are no-ops and Admin reopening is suspended | Define whether a reopened competition is a new payout round or only a correction. This affects existing operators and payment history. |
| Correct prior prizes | No reconciliation applied and historical payout ownership is uncertain | Use reviewed compensating entries after attribution. Retroactive balance or rank changes require approval. |
| Exact ties | No tertiary sort key | Add a stable tiebreaker or shared rank and define how prize slots are consumed. Either can change payouts. |
| Permanent identity | Persisted flags protect supported transitions, with no per-payout key | A durable unique key scoped to contest or registration and reward type would need schema and historical migration approval. |

All alternatives in this table require explicit product approval before implementation. Existing concurrent legacy scoring and non-competition absolute balance writes remain outside this phase.

## Files, integrity and rollback

Modified missions/models.py, missions/admin.py, missions/views.py and dashboard/views.py. Added missions/test_competition_integrity.py and this report. Outside the project, phase24-backup contains originals and SHA256.txt. phase24-check contains source copies, the backup database and isolated mouod/phase24_settings.py. The previously running Phase 2.5 preview is a separate copy and was not refreshed by this verification.

Before edits, verified backup manifests from Phase 1 and Phases 2.1–2.3, SQLite integrity and archive CRC. Independent originals were backed up here:

`C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase24-backup`

| Original file | SHA-256 |
| --- | --- |
| missions/models.py | ca00e4f28f5eba5d4110b383040b46e038803351e0dbbb660dd3ffafeea3a597 |
| missions/admin.py | 702da941a2f1fec66110e79d5fb5372fcf007fdd31e499ed07574fbe7bdd7c8f |
| missions/views.py | c419c3eeda7cb70b9941a19401efa03b592619a58d10432f0d523ec9d16d685f |
| dashboard/views.py | ea722914fa8f55d388bfdafe7eb996f2f960f4a223caf19fcf265a716757481a |

To roll back, verify SHA256.txt, copy the four original files back to their matching paths and remove the added competition test from the reverted suite. Keep this report. No database restore is needed for code rollback. Reverting the code reopens the original payout risks.

The original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c. Media inventory and bytes and archived migrations matched the backup. Byte comparison with the Phase 2.3 copy confirmed only the four listed existing source files differed. No migration was created or required.
