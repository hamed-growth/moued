# Incremental migration — staff team reads

> Historical checkpoint. The [current layout and verification](LAYOUT_MIGRATION.md) supersede its package paths.


Completed the first incremental step after the initial modernization: moved dashboard team-list and team-detail query construction into apps/teams/selectors/staff.py. Staff authorization, object lookup/404, route names, templates and context keys remain in dashboard views unchanged. No write operations or financial policy changed.

Baseline: 78 tests passed. Three new HTTP characterization tests passed before extraction; the final complete suite passed 81 tests with no system-check issues using mouod.test_settings and its temporary database/media. Coverage includes counts, ordering, empty teams, member/assignment scoping, inactive missions, unauthorized users and missing teams. Original database, media and migration hashes remained identical.

Created: apps/teams/selectors/staff.py, dashboard/test_team_reads.py, docs/INCREMENTAL_MIGRATION.md.
Modified: dashboard/views.py and ARCHITECTURE.md (progress reference).
Independent pre-edit views backup and protected-file manifest: external incremental-teams directory beside modernization evidence. Restore its views.py to dashboard/views.py and remove the two added Python files to roll back this extraction, after checking for later edits. No data restoration is needed.

Remaining sequence: staff account/history selectors; remaining staff reporting selectors; then separately characterized nonfinancial operations. Financial model save hooks and competition answer admission need dedicated behavioral/transaction coverage and must not silently change policies. Model ownership remains missions. Initial modernization reports are historical snapshots; current test total is 81 and there are now 13 selector implementation modules.

## Staff account reads

Moved the dashboard user list and activity history queries into `apps/accounts/selectors/staff.py`. The views parse filters, enforce staff access, look up the target user and render the existing templates. Two HTTP tests cover combined filters, user history scope, the 50-row transaction limit and staff access. All 83 tests passed with isolated settings. Database, media and migration hashes match the prior checkpoint. Remaining read extractions include dashboard reports for missions, competitions, questions, treasure and transactions.

## Staff reports

Moved seven report queries into the missions, competitions, questions, treasure and wallet staff selectors. The dashboard views pass request filters to these selectors and render their results. Three HTTP tests cover report access, request status filtering and filtered transaction totals. The isolated suite passed all 86 tests.

## Remaining public reads and domain workflows

Account role and activation changes, team mission assignment and purchase delivery now use domain services. The purchase model retains its delivery entry point for Dashboard and Admin callers. Mission requests and daily and competition answers call services from their public routes. Competition registration, start and play use the participation service, and selectors build competition details, select remaining questions, load archive data and count staff menu badges.

Mission completion and daily answer model hooks delegate reward writes to their services. The wallet service handles the existing balance and activity update. Model hooks still govern when the effects run, and the mission completion transaction includes its reward writes.

All 88 tests passed on disposable SQLite. The two new tests exercise entering competition play and preserving the original start time on repeated starts. The schema dry run reported no changes, and the original SQLite file SHA-256 matched its pre-edit value. Competition answer admission and finalization still use their existing concurrency policy. The archive template and Jalali timezone issues remain tracked as separate defects.
