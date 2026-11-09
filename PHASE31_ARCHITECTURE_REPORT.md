# Phase 3.1 — Profile and League Selectors

## Scope and analysis

The profile view originally combined session-scoped access, active-user rank, financial summaries, pending reward projections, mission completion and registration history, and team rankings. The league view combined Jalali month selection, monthly point aggregation, team member ranking and presentation. Both views queried missions models directly. The league repeated the all-team ranking query group for a member's team rank and for the full list.

The current dependency map and domain categories are in [ARCHITECTURE.md](ARCHITECTURE.md). Dashboard still reads missions models and uses its own authorization boundary. The inspected model completion and review methods have write side effects. They were outside this extraction.

## Implemented changes

- missions/selectors/profiles.py supplies active-user rank and private completion/registration history. A filtered aggregate computes rank and active-user count together. The completion count and newest 10 rows and registration order use the original filters and eager loading.
- missions/selectors/leagues.py supplies the profile team leaderboard and league rankings. Both selectors take precomputed monthly point totals. League rank lookup and the full list reuse the same prefetched ranking.
- missions/views.py imports the selectors and delegates only profile and league reads. The former private ranking helper moved to the league module. Financial summaries, pending reward projections, date handling and authentication stay in the views.
- missions/selectors/__init__.py, missions/test_selectors.py, ARCHITECTURE.md and this report were added. No existing tests were edited.

HTTP methods, URLs, template names, context keys, user scoping, completion and pending limits, score ordering and month fallback were preserved. The before/after probe compared the actual status, chosen template and normalized context including ordered results and model IDs for the same authenticated synthetic fixture. The comparisons matched. Focused tests also assert guest redirects, empty states, valid and invalid month handling, and private history isolation.

## Performance and verification

Full rendered GETs were measured with CaptureQueriesContext, including session and template queries, using two teams with one member and one dated transaction each. The same fixture and probe were used before and after. All captured statements were SELECTs.

| GET | Before | After | Change |
| --- | ---: | ---: | --- |
| /profile/ | 20 | 19 | Combined active-user and ahead counts |
| /leagues/ | 14 | 11 | Removed repeated team, membership and member queries |

The league retains its separate own-team membership query and eager loads the all-team list. The profile history reads count, completions and registrations in three queries when both result sets are evaluated. Existing per-request lookups for pending team reward projections can still grow with the pending list. The probe does not measure that path at scale. No caching was added. Both runs also emitted the existing timezone warning for naive transaction month boundaries. The date semantics were preserved.

Using the Phase 1.7 Python 3.12.14 interpreter and isolated phase31-check copy, pip check and Django check passed before and after. Before editing, all 56 baseline tests passed. Five focused tests passed after extraction. The complete post-change suite ran **61 tests with zero failures and zero skips**. Settings assertions confirmed the normal database was memory-only, TEST.NAME was a new disposable SQLite file inside the isolated copy, and email used locmem. No original database was used for the test runner.

```powershell
python -B -m pip check
python -B manage.py check
python -B manage.py test missions.test_selectors --settings=mouod.phase31_settings -v 1
python -B manage.py test --settings=mouod.phase31_settings -v 1
```

The isolated copy also contains selector_probe.py inside missions and before.json and after.json with synthetic context and SQL measurements. It uses the external-only mouod/phase31_settings.py copied from the Phase 2.4 file-backed test configuration.

## Integrity and rollback

Before editing, the Phase 1 archive comparison found four previously changed existing files from Phase 2.4 and earlier. They were dashboard/views.py, missions/admin.py, missions/models.py and missions/views.py. The original database SHA-256 was cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c before and after. The media inventory and hashes matched the backup. Migration inventory and bytes matched the original archive. The Phase 2.4 source comparison confirmed only missions/views.py changed among existing app files. A function AST comparison confirmed that only profile, league_list and the relocated private ranking helper differed. Models, URL configuration, settings, write paths and UI assets were preserved.

The independent backup is at `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase31-backup`. Original missions/views.py SHA-256 is af6f5888cd111628db32db622bf68196d1340511c40200ce8f84a1828925a90e. Verify SHA256.txt, restore the backup views.py to missions/views.py and remove the three added selector files and new selector test from the reverted source. Documentation may be retained as a record. No data restoration is required.

## Open risks and Phase 3.2

The late competition answer race, suspended mission reopening and treasure request replay policy remain open. For an approved Phase 3.2, pick one write workflow with a settled product policy, record all dashboard, public and Admin entry points, and verify rollback and concurrency behavior before moving code. Keep schema changes and app splitting separate. The previously running preview uses its existing isolated copy.
