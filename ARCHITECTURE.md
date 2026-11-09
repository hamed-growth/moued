# Architecture

The project runs as one Django monolith. Phase 3.1 introduced read-only selectors inside missions. Phase 3.2 added the Treasure checkout service. Phase 3.3 added the Mission Review service. Phase 3.4 added the Competition service. The logical domains below describe responsibilities within the current codebase.

| Component | Current responsibility |
| --- | --- |
| mouod | Project settings, root URL routing, Django entry points, SQLite and media configuration |
| missions | Registered Django app containing the custom User model, domain models, public views, forms, Admin registrations, templates and static assets |
| dashboard | Registered Django app containing staff views, role checks, context processors and templates. It uses missions models directly. |
| Django contrib apps | Authentication, Admin, content types, sessions, messages and static files |

| Logical domain | Current model and rule ownership |
| --- | --- |
| Accounts | missions.User and registration/login forms and views. Django sessions and permissions implement authentication. |
| Teams | Team and TeamMember define membership. TeamMission connects teams to missions. League views combine team membership with monthly points. |
| Missions | MissionCategory, Mission, TeamMission, MissionRequest and MissionCompletion. The Mission Review service owns review. MissionCompletion.save owns completion reward writes. |
| Questions | Question, DailyQuestion and DailyQuestionAnswer. Daily answer writes and rewards use the existing view/model path. |
| Competitions | Competition, CompetitionRegistration, CompetitionQuestion and CompetitionAnswer. The Competition service owns participant completion and finalization payouts through model compatibility methods. |
| Wallet | User stores point and coin balances. PointTransaction stores deltas. The current reward issuers and purchase flow coordinate writes with their domain operation. |
| Treasure | TreasureCategory, TreasureItem and TreasurePurchase. The Treasure service owns the atomic debit, stock reservation and purchase. Dashboard and Admin handle fulfillment. |
| Dashboard | Staff authorization and operational presentation across the missions domains. |

## Dependency map

| Category | Current dependencies and boundary |
| --- | --- |
| HTTP presentation | mouod URLs → missions/dashboard URLs → views → templates. Views parse GET filters and select templates. |
| Authorization | missions uses Django login_required. dashboard uses staff_required and operation-specific checks. Django Admin uses model permissions and the privilege restrictions established in Phase 2.1. Selectors receive the user from an authorized caller and do not interpret credentials or request data. |
| Read-only data access | Profile and league views → missions.selectors → explicit missions model imports. Financial summaries and Jalali month selection still run in the views. Dashboard reads models directly. |
| Business operation | Dashboard, public views and Admin call mission review and competition completion/finalization methods. The storefront purchase view calls the Treasure service to coordinate the write transaction. |
| Persistence rule | Model methods include side effects such as balance and ledger writes during completion. Moving a call to a generic save, update or bulk API can bypass or duplicate those effects. |
| Cross-domain coordination | Team rankings read point totals by member. Mission, question and competition rewards update User and PointTransaction. Treasure also writes inventory and purchase records. |

Selectors depend on domain models and should remain below the HTTP layer. Views can call selectors and explicit application services. Neither lower layer should import a view or dashboard code. The inspected model compatibility methods import Mission Review and Competition services locally. Those services import models at module scope, so the runtime dependency returns to the model layer without a module initialization cycle. The inspected model and service paths do not import dashboard or selectors.

The implemented selectors retrieve active-user rank, completion and registration history, and team/member rankings. Ranking selectors accept already aggregated monthly point totals. They use eager loading for team/member collections and preserve existing row ordering, tie handling and context shapes. Future write services should own transaction boundaries, persisted transitions and financial coordination. They should reuse one authorized entry point across public, dashboard and Admin callers where the business policy permits.

Keep new reads scoped to an authorized subject or an existing public data contract. Put request parsing and presentation in views. Document deliberate changes to ordering or visibility and verify counts on realistic fixtures. Preserve lazy queryset behavior where templates rely on it. Write-side changes require their own transaction, retry and concurrency tests.

Moving existing models between apps could affect migration state, content types, permissions, foreign keys and references to missions.User. Keep the existing model locations and app labels until a separately approved migration plan verifies both fresh installation and an upgrade from a backup.

Implemented paths:

```text
missions/
  models.py
  views.py
  services/
    treasure.py
    mission_review.py
    competitions.py
  selectors/
    profiles.py
    leagues.py
dashboard/
  views.py
  decorators.py
mouod/
  settings.py
  urls.py
```

Future approved domain operations can be added to missions/services while models and migrations stay in their current app. Separate Django apps would be a later migration decision.

The competition answer/finalization race remains open. Mission reopening remains suspended pending a product decision. Treasure checkout remains transactional but can still accept a replay as a second purchase because the request contract has no idempotency key.

## Treasure purchase service

The authenticated storefront POST delegates to missions.services.treasure.purchase_treasure_item(user, item_id). It receives the caller's user instance and a routed item ID. It returns the persisted TreasurePurchase and the new point balance. The service imports Django ORM tools and missions models. The dashboard and Admin fulfillment operations still act on existing purchases through their prior paths.

The service checks the active item and its model-provided availability, then uses one atomic block for the conditional balance debit, stock update and ledger and purchase inserts. The item model still defines availability, including unlimited stock. The view handles authentication, POST enforcement, HTTP messages and exception mapping. Missing or inactive items raise TreasureItem.DoesNotExist, insufficient points carries the shortfall, and stock conflicts raise OutOfStock. A database exception reaches the view after rollback.

Wallet balances and ledger records remain on User and PointTransaction. The service coordinates only checkout. A replay can still create a second purchase because there is no request identity or idempotency key. SQLite can reject concurrent writes, and the view keeps the existing generic 503 response for database failures.

## Mission Review service

The public operations are approve_mission_request(mission_request, admin_user=None, admin_note=None) and reject_mission_request with the same arguments. They receive a MissionRequest instance and return True for a successful transition or False for a no-op. They synchronize the supplied instance on success. The existing MissionRequest.approve and reject methods delegate through local imports, so dashboard and Django Admin callers retain their existing interfaces and authorization. The service has no dependency on the HTTP or Admin layers.

Both operations claim a persisted pending row with a conditional update inside transaction.atomic. Approval creates MissionCompletion in that same transaction. MissionCompletion.save remains responsible for base and team reward selection, balance and activity updates, and ledger creation. An exception propagates after rollback. Dashboard error mapping and per-request Admin transactions retain their existing scope.

The stale-save guard stays on MissionRequest and status remains read-only in the Admin form. Cross-terminal reopening remains suspended. Historical reward attribution still lacks a per-request ledger link. The competition late-answer race, treasure replay behavior and monthly reporting timezone warning remain open.

## Competition service

finish_competition_registration(registration) and finalize_competition(competition) accept existing model instances. They return True when a persisted transition is claimed and completed, or False when no claim is made. The finish operation refreshes the supplied registration, including on a lost claim. The finalization operation sets the supplied competition status on success. Database exceptions propagate to the caller after rollback.

Public play, answer submission and manual finish call CompetitionRegistration.finish. Dashboard and Admin finalization call Competition.finalize. These methods import and delegate to the service locally. The service imports competition models, User and PointTransaction and uses Django ORM. It has one private payout function for points, activity streak and the matching ledger row. Registration validation, question scoring and authorization stay at their existing entry points.

Each operation starts with a conditional database write and keeps its claim and payouts in one atomic block. Finalization also ranks the first three registrations by correct count and finish timestamp, using the existing rules for unfinished participants and zero correct answers. The service preserves the existing rank, coin and prize semantics.

A future API caller must authenticate, authorize the operation for its subject and validate input before calling the service. The late-answer race still requires a shared admission and finalization design. Reopening, historical prize correction, unfinished eligibility and exact-tie policy remain open.
