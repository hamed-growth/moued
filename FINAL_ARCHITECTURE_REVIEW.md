# Final Architecture Review

## Decision

**Phase 3 architecture refactoring is complete for the agreed scope.** The project has working read and write boundaries for the selected operations, the 71-test baseline passed, and closing this scope requires neither a database migration nor an API migration. **API design is ready for review.** Public production deployment is **not ready**. Deployment checks, a confirmed Django Admin authorization gap and a confirmed open redirect are release blockers. See [the risk register](TECHNICAL_RISK_REGISTER.md).

## Implemented architecture and dependencies

This is one Django monolith with two project apps, missions and dashboard, and the mouod project package. Django loaded eight installed app configs and 24 models. Nineteen models belong to missions and dashboard has no models. AUTH_USER_MODEL resolves to missions.User.

| Domain | Ownership and current boundaries |
| --- | --- |
| Accounts | User, Django authentication/session middleware, registration and login forms. Dashboard staff checks and Django Admin privilege protections live at their entry points. |
| Teams | Team, TeamMember and TeamMission. Membership and per-team configuration feed mission and league reads. |
| Missions | Mission, MissionCategory, MissionRequest, MissionCompletion and TeamMission. Eligibility and submission still involve public views. Review service claims a persisted pending request. MissionCompletion.save owns completion rewards. |
| Questions | Question, DailyQuestion and DailyQuestionAnswer. The daily answer path and model reward side effect remain in place. |
| Competitions | Competition, CompetitionRegistration, CompetitionQuestion and CompetitionAnswer. Public views own admission and scoring orchestration. The service owns finishing and finalization. |
| Wallet | User balances and PointTransaction ledger. Each domain still coordinates its own ledger and balance writes. |
| Treasure | TreasureItem, TreasureCategory and TreasurePurchase. The checkout service owns debit and reservation. Dashboard and Admin deliver purchases. |
| Dashboard | Staff operations and reporting over missions models, with a separate URL namespace and role checks. |

Root URL configuration dispatches to public views, staff views and Admin. Views use forms, selectors, services and sometimes models directly. Forms and selectors import models. Checkout uses the service directly. Mission and competition callers use model compatibility methods, which import services locally. This forms a deliberate runtime model-to-service-to-model dependency. Service modules import models at the top level, and wrappers import services only when invoked. The service never calls its own wrapper. Startup and wrapper execution passed. No service or selector imports views, Admin, templates or frontend code in the inspected modules.

Direct ORM access is still used in dashboard reads, public eligibility, reporting, question answering and portions of competition scoring. Model save hooks for mission completions and daily answers can write rewards. Calling QuerySet.update, bulk_create or model saves directly has distinct semantics. Admin actions and model forms also use ORM writes outside the extracted services. These are material exceptions to a purely layered diagram. The extracted operations have one authoritative implementation each. Other balance writers and ledger insertions still exist and must not be treated as a unified wallet API.

## Service and selector inventory

| Interface | Transaction, errors and caller boundary |
| --- | --- |
| purchase_treasure_item(user, item_id) | Returns purchase and remaining points. Active item lookup precedes the atomic block. Conditional debit, stock reservation at the same price, negative ledger and pending purchase commit together. Missing item, insufficient points, stock conflicts and database failures are distinct. The view supplies the authenticated buyer and maps failures, including generic 503. |
| approve_mission_request / reject_mission_request | Accept an existing request, reviewer and optional note. Return True for a persisted pending claim and False for a no-op. Approval creates the completion and rewards in the same transaction. Caller must authorize reviewer and target. Dashboard and Admin use compatibility methods. |
| finish_competition_registration / finalize_competition | Accept a registration or contest and return a boolean claim result. Status, payouts, ledger and rank roll back together. ORM errors propagate. Public views scope the registration to the authenticated user. Staff and Admin entry points are responsible for action authorization. |
| get_profile_rank / get_profile_history | Active-user rank plus owner-filtered completion and competition histories. Completion count is eager, while the sliced completion and registration querysets are lazy. The caller must bind the subject to the authenticated user or another explicitly authorized scope. |
| get_profile_team_leaderboard / get_league_rankings / get_ranked_teams | Read team and member records using prefetch/select_related. Monthly totals come from the caller. Lists are materialized. Sorting is by existing point order. Equal values inherit source order without an explicit database tie-break. Model objects returned in the structures need field allowlists before serialization. |

Read-only behavior is supported by the selector source, query-capture tests and earlier normalized GET probes. Phase 3.1 recorded 20 → 19 SQL statements for profile and 14 → 11 for leagues on its synthetic fixture. This phase did not benchmark wider workloads. Pending team reward projections can still query per request. Expanding API serializers to uncached relations can also introduce N+1 queries. Existing completion and registration date sorts do not guarantee a unique order for exact ties.

## Authorization and integrity evidence

The full suite retained its staff escalation denials and authorized superuser changes. The dedicated smoke check also confirmed that an ordinary staff user with only view_competition permission can post the Admin finalization action and persist finished. That is a specific Admin action gap. A separate login probe confirmed an external next redirect. These risks are tracked for release without changing the audit scope.

The suite covered checkout rollback, concurrent stock and balance claims, SQLite lock failures, pending-only mission review, stale review saves, competition payout rollback and winner and participant races. It preserves the characterization that an admitted answer can land after rank selection. No claim is made about sustained write contention or PostgreSQL behavior.

## Verification

- Phase 1.7 offline CPython 3.12.14 and Django 6.1.2. pip check reported no broken requirements. Django's normal system check reported zero issues. Full suite passed **71 of 71**, zero failures and skips, including the transaction and independent-connection concurrency tests.
- The fresh isolated audit copy contained a disposable file-backed test database, a memory-only default database, locmem mail and temporary media outside the project. The original database was only opened read-only to create a SQLite Backup API copy. Reviewed tests used local fixtures and Django clients, with no external production calls observed.
- A dry-run migration state check reported no changes. The read-only database copy and a fresh in-memory schema had the same 22 applied migration records and 28 Django tables. SQLite column metadata, foreign keys and index shapes matched. Integrity check returned ok and foreign key check found zero violations. This comparison did not inspect every CHECK expression or prove PostgreSQL compatibility.
- Deployment check against the copied default settings reported mail.E001 and seven security warnings covering HSTS, HTTPS redirect, secret configuration, session/CSRF cookies, DEBUG and hosts. Existing Jalali month timezone warnings appeared in the test run.
- Original database SHA-256 matched the baseline. Media hashes and migration inventory and bytes matched the backup. Application source matched the isolated audit copy. Only the four requested documents and the dependency-direction correction in ARCHITECTURE.md changed in the project.

PostgreSQL is a separate decision. Rehearse data migration, schema and constraint comparison, collation and NULL/tie ordering, isolation and lock behavior, and rerun the payout and concurrency suite on the target backend. See [the API plan](API_READINESS_PLAN.md) and [development guide](DEVELOPMENT_GUIDE.md).
