# Phase 3.4 — Competition Services Extraction

## Call graph and scope

| Entry point | Original operation | After extraction |
| --- | --- | --- |
| Public competition play | Calls CompetitionRegistration.finish on expiration or exhausted questions | Same model method delegates to the service |
| Answer submission | Validates eligibility and writes answer and score, calls finish on expiration or when the cap is reached | Same path and validation |
| Manual finish POST | Calls CompetitionRegistration.finish and maps the result to JSON | Same wrapper and JSON |
| Dashboard finalization POST | Staff-authorized call to Competition.finalize with existing messages and 503 on database error | Same wrapper and error handling |
| Django Admin bulk finalization | Calls Competition.finalize separately for each contest | Same wrapper and bulk scope |
| Admin form and activation action | Can change supported nonfinal status. Finalization is a separate action and activation excludes finished contests. | Same form and action |
| Direct model callers | Use Competition.finalize or CompetitionRegistration.finish | Same signatures, booleans, exceptions and instance synchronization |

No existing competition service was present. The extracted functions are finalize_competition(competition) and finish_competition_registration(registration) in missions/services/competitions.py. The model wrappers import them locally. The service imports models and ORM tools and never calls the wrappers. View, URL, Admin and permission code retain their existing paths. Neither operation uses a template or an HTTP object.

## Transactions and rules

Finishing claims is_completed=False, sets the timestamp and refreshes the instance. The same transaction pays the positive stored score and positive participation bonus. On a lost claim the instance is refreshed and the operation returns False. Finalization claims a persisted nonfinished contest, reads current prize values and selects the first three registrations by descending correct count and ascending finish timestamp. Only rows with positive correct counts receive their existing slot prize and rank. Unfinished registrations still participate and exact ties retain the existing database ordering. The supplied competition status changes on success only.

The single payout helper moved alongside both operations. It preserves the F-expression point increment, activity date and streak rules and exact ledger text. Coins are unaffected. The conditional write remains the first database operation inside each atomic block. An exception rolls back the status or completion claim and all affected ranks, balances and ledger rows. No model save override or signal was added.

## Comparison and tests

An isolated fixture ran before and after the extraction. JSON snapshots matched for public finish and repeat, stale model results, dashboard finalization, dashboard payout failure, Admin retry and final state. Comparison included HTTP status, redirect, JSON and messages, timestamp presence, rank, completion flags, point and coin totals, ledger descriptions and rollback state. Generated timestamps were normalized to presence. No observed difference required acceptance.

| Verification | Result |
| --- | --- |
| Pre-edit full suite | 68 passed |
| Focused run | 18 passed, including 14 existing competition tests, 3 new direct service tests and 1 external comparison probe |
| Full final suite | 71 passed, zero failures and skips |
| pip check and manage.py check | No broken requirements and zero Django system check issues |

Before and after, the existing concurrency tests ran with disposable file-backed SQLite and independent connections. Two finalizers produced one payout, and two participant finishers produced one set of completion rewards. A finish racing with finalization preserved both distinct payouts in the tested case. The SQLite writer-lock test still returned HTTP 503 with no prize, rank or final status written. The late-answer characterization test still passed with its original expectation.

The verified Phase 1.7 Python ran from the external phase34-check copy. The safety check confirmed a single SQLite alias with a memory-only default, a new file-backed test database path under the isolated copy and locmem email. The runner removed the disposable databases. The comparison probe and before.json and after.json are in that isolated copy.

```powershell
python -B -m pip check
python -B manage.py check --settings=mouod.phase34_settings
python -B manage.py test missions.competition_probe missions.test_competition_services missions.test_competition_integrity --settings=mouod.phase34_settings -v 1
python -B manage.py test --settings=mouod.phase34_settings -v 1
```

## Open policy and Phase 3.5 readiness

submit_answer can pass eligibility checks before finalization and persist afterward, while the winner ranking has already been selected. Service extraction does not put answer admission and finalization under a shared transaction. A later product decision must choose whether finalization rejects in-flight answers at a strict cutoff or waits for admitted answers. Reopening, historical prize correction, exact ties and eligibility of unfinished registrations also remain undecided. These tested SQLite outcomes do not establish behavior under sustained contention.

The extracted entry points and passing regression suite are available for the Phase 3.5 architecture review. Any future API caller must enforce authorization and input validation at its boundary. Existing reporting timezone warnings appeared during the full suite. The preview remains a separate copy.

## Files, hashes and rollback

Modified missions/models.py and ARCHITECTURE.md. Added missions/services/competitions.py, missions/test_competition_services.py and this report. The model AST comparison confirmed only the two compatibility methods and the moved payout helper differed. The Phase 3.3 source comparison found no other existing application file changes. The Phase 1, 2.4 and 3.3 backup manifests were verified before editing.

Originals and SHA256.txt are in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase34-backup`.

| Original file | SHA-256 |
| --- | --- |
| missions/models.py | 24857db10977706bce802d848dfbd62058bab947f2c383ae6654374ac49c4054 |
| ARCHITECTURE.md | 5da7a28d693b12592e914c22e26604dba706984e2778ca82284d7c10430b1b28 |

To roll back, verify SHA256.txt, restore both original files and remove the added service and test module from the reverted source. Retain this report if needed. There is no data rollback.

Original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c. Media inventory and hashes and migration inventory and bytes matched the Phase 1 backup.
