# Incremental migration — staff team reads

Completed the first incremental step after the initial modernization: moved dashboard team-list and team-detail query construction into apps/teams/selectors/staff.py. Staff authorization, object lookup/404, route names, templates and context keys remain in dashboard views unchanged. No write operations or financial policy changed.

Baseline: 78 tests passed. Three new HTTP characterization tests passed before extraction; the final complete suite passed 81 tests with no system-check issues using mouod.test_settings and its temporary database/media. Coverage includes counts, ordering, empty teams, member/assignment scoping, inactive missions, unauthorized users and missing teams. Original database, media and migration hashes remained identical.

Created: apps/teams/selectors/staff.py, dashboard/test_team_reads.py, docs/INCREMENTAL_MIGRATION.md.
Modified: dashboard/views.py and ARCHITECTURE.md (progress reference).
Independent pre-edit views backup and protected-file manifest: external incremental-teams directory beside modernization evidence. Restore its views.py to dashboard/views.py and remove the two added Python files to roll back this extraction, after checking for later edits. No data restoration is needed.

Remaining sequence: staff account/history selectors; remaining staff reporting selectors; then separately characterized nonfinancial operations. Financial model save hooks and competition answer admission need dedicated behavioral/transaction coverage and must not silently change policies. Model ownership remains missions. Initial modernization reports are historical snapshots; current test total is 81 and there are now 13 selector implementation modules.
