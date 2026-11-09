# Phase 3.3 — Mission Review Service Extraction

Before extraction, dashboard staff POSTs and Django Admin bulk actions called MissionRequest.approve or reject. Those model methods claimed pending status and handled the transaction directly. Approval created MissionCompletion, whose save method calculated and issued the reward. Admin form status was read-only, existing form edits saved only changed fields, and MissionRequest.save guarded review metadata against stale saves. Standalone completion creation issued its own reward and did not review a request.

The call graph is now dashboard or Admin → existing MissionRequest method → missions.services.mission_review → persisted claim and, on approval, MissionCompletion.save. The service functions can also be called directly by an authorized domain caller. Their signatures are approve_mission_request(mission_request, admin_user=None, admin_note=None) and reject_mission_request with the same arguments. A successful review returns True and synchronizes the supplied instance. A no-op returns False without refreshing the instance. Local imports in the model wrappers avoid a module import cycle. The service never invokes the wrappers.

The transaction still starts with the persisted pending-only update and checks the affected row count. Reviewer, timestamp and any nonempty note are written with the claim. Approval refreshes the claimed request, creates the completion, and copies the completion's actual award amounts. All writes share the approval transaction. Completion still owns the team override, balance and streak updates, and ledger insert. Database failures propagate after rollback. Dashboard generic HTTP 503 and Admin's per-request transaction and failure handling are preserved. Dashboard and Admin source files were not edited.

## Verification

The same synthetic fixture ran before and after extraction. Normalized snapshots matched exactly for dashboard approval and rejection, repeated POSTs, Admin approval and rejection actions and model-method success and stale retries. The comparison included status and redirect, Persian messages, persisted state, reviewer identity, timestamp presence, notes, award amounts, balances, completion records, ledger entries and wrapper return values. The existing failure and authorization assertions remained intact.

| Verification | Result |
| --- | --- |
| Pre-edit suite | 65 passed |
| Focused run | 14 passed, including the external comparison probe, 3 new service tests and 10 existing mission tests |
| Concurrent approval attempts | One committed claim and one reward |
| Approval competing with rejection | One committed claim with matching metadata and balances |
| Full suite | 68 passed, zero failures and skips |
| Django system check and pip check | Zero system check issues and no broken requirements |

Tests used offline CPython 3.12.14 from Phase 1.7 in phase33-check. The safety check verified a memory-only normal database, new file-backed SQLite test database inside the isolated copy and locmem email. The runner removed its disposable databases. Before and after JSON snapshots and the probe are retained there. No production database was copied into this test environment.

```powershell
python -B -m pip check
python -B manage.py check --settings=mouod.phase33_settings
python -B manage.py test missions.review_probe missions.test_mission_review_service missions.test_mission_rewards --settings=mouod.phase33_settings -v 1
python -B manage.py test --settings=mouod.phase33_settings -v 1
```

## Source integrity and rollback

Modified missions/models.py and ARCHITECTURE.md. Added missions/services/mission_review.py, missions/test_mission_review_service.py and this report. Only the review methods changed in the existing application source. The Phase 1, 2.3 and 3.2 backup manifests were verified before editing.

Independent originals and SHA256.txt are in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase33-backup`.

| Original file | SHA-256 |
| --- | --- |
| missions/models.py | 447bc701b5290d0aa17a00ea31feb6ac8e9d3e75a2b914a8b6a029538f0b53ee |
| ARCHITECTURE.md | ada486637baff89cededf9f84dd7160621bf82fe2ea4e1d498581ce584513698 |

For rollback, verify SHA256.txt, restore both files to their matching project paths, and remove the new review service and service test from the reverted code. This report may be retained. No database restore is needed. Original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c. Media inventory and hashes and migration inventory and bytes matched the Phase 1 backup.

## Limits and next step

Mission reopening remains suspended and historical payouts cannot be attributed to requests with certainty. SQLite writer contention can still fail a review. Competition late answers, treasure request replay and the existing monthly timezone warnings remain open. For a later approved extraction, inventory competition finalization callers and treat payout extraction and late-answer policy as separate changes. The Phase 2.5 preview remains a separate copy.
