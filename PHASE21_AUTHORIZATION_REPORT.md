# Phase 2.1 — Authorization Hardening

## Historical baseline

Phase 1.7 recorded 10 PASS and one known authorization FAIL before the fix. In missions/test_behavioral_baseline.py, test_dashboard_redirects_regular_user_and_allows_staff_role_toggle expected HTTP 302 and target.is_staff=True after an ordinary staff POST. That staff-success assertion describes the vulnerability and will be replaced by HTTP 403 and target.is_staff=False. The ordinary-user redirect assertion and unrelated behavioral assertions are preserved. The separate ExpectedSecureBehavior assertion remains intact.

## Confirmed paths and policy

- Dashboard `POST /dashboard/users/<user_id>/toggle-staff/` uses the URL target and toggles the stored flag. It consumes no privilege fields from the body. Previously staff_required plus the self-target guard allowed an ordinary staff actor to grant or revoke staff on another account. Now the view returns HTTP 403 for ordinary staff before fetching or saving the target. Anonymous and non-staff redirects, POST-only behavior, CSRF, superuser success redirect and the existing self-target redirect are preserved.
- Django Admin UserAdmin exposed is_staff, is_superuser, groups and user_permissions to staff with the corresponding add/change model permission. GroupAdmin exposed permissions to staff with group add/change permission. Those fields are read-only for ordinary staff and a POST including any such key is rejected with HTTP 403 before saving any part of the form. Superusers can still use the fields. Group deletion requires superuser because deleting a group removes its permission assignments.
- UserAdmin also exposes password and username fields. Staff with change_user can still edit ordinary accounts, but cannot edit other accounts carrying staff, superuser, group membership or direct permissions through this form. This prevents credential edits from serving as an alternate privilege path. Ordinary staff can still edit their own permitted non-privilege fields.
- is_team_manager is separate from is_staff and is_superuser. staff_required does not accept it as an admin role. The team-manager and account-activation toggles retain their existing business behavior. In particular the dashboard activation toggle still permits staff to deactivate another account, including a privileged account. The policy for account availability was left open. The dashboard still displays the staff toggle to staff, who now receive a server-side 403.

## Changes and compatibility

| File | Change |
| --- | --- |
| dashboard/views.py | Superuser authorization in user_toggle_staff. |
| missions/admin.py | System privilege POST guards, read-only presentation, protection against editing another privileged account and superuser-only group deletion. |
| missions/test_behavioral_baseline.py | Replace historical staff-success assertion with denial. Registration/login test now exercises the existing logout URL and checks that the authenticated session was cleared. Other behavioral assertions and the separate secure expectation are preserved. |
| missions/test_authorization.py | Ten synthetic regression tests. |
| PHASE21_AUTHORIZATION_REPORT.md | Findings, verification and rollback. |

No schema or migration change is required. Dashboard URLs and templates are preserved. Delegated Admin users retain valid ordinary user edits and group renames. Delegated group deletion and edits of other privileged accounts now require superuser.

## Verification

Phase 1.7 env-a, CPython 3.12.14. Django ran from phase21-check against a copy of the Phase 1 backup. Before tests, the only database alias, in-memory NAME and TEST.NAME, and locmem email backend were asserted. The test runner reported an in-memory SQLite database.

| Check | Result |
| --- | --- |
| `python -B -m pip check` | PASS |
| `python -B manage.py check` | PASS, zero issues or silenced checks |
| Existing behavioral baseline | 10 PASS, including registration/logout/login, team membership, missions, competitions, questions, wallet and purchase |
| Previously failing ExpectedSecureBehavior | 1 PASS |
| New authorization tests | 10 PASS |
| Total | 21 PASS, 0 failures |

New cases cover anonymous and team manager access, staff revocation and self-target denial, superuser grant/revoke and self-target handling, GET and direct POST, CSRF rejection and success with token, retained manager/active toggles, atomic rejection of each injected user privilege field, injection on account creation, credential edits against a privileged target, authorized Admin privilege editing and group permission injection versus rename.

```powershell
python -B manage.py test missions.test_behavioral_baseline missions.test_authorization --settings=mouod.baseline_settings -v 2
```

## Backup and rollback

Before edits, all Phase 1 backup hashes matched, the backup database returned integrity_check ok and source.zip passed its ZIP integrity check. Independent copies and hashes of the three existing edited files were stored in:

`C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase21-backup`

| Original file | SHA-256 |
| --- | --- |
| dashboard/views.py | ce32161c4328781d7bb26b236067027cfe21863ac400e64226b0041be1a56e2f |
| missions/admin.py | 98f855443211f4c38fba3eba1d4ddf617df757a209051389a1b94b24da20152d |
| missions/test_behavioral_baseline.py | 3ae44875c2fdcea15509390edfb1ca74a24610285b43892af03220231b65d441 |

To roll back, verify SHA256.txt, copy those three backup files over their matching project paths, and remove the newly added missions/test_authorization.py from the reverted test suite. Keep this report as a record. No database restore is needed for code rollback. Reverting the production code would reopen the documented privilege paths.

The isolated phase21-check folder contains copies of missions, dashboard, mouod, manage.py and the backup database. Final byte comparison against the Phase 1 source snapshot found only dashboard/views.py and missions/admin.py changed among archived files. The media file inventory and bytes matched the backup. Original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c.

## Remaining scope

Account-activation policy for privileged targets and unrelated deployment and business risks remain open. No wallet, mission, competition or architecture changes were made.
