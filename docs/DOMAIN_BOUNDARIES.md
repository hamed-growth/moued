# Domain boundaries

These are Python packages, not newly registered Django apps. `missions` owns every domain model and migration. `AUTH_USER_MODEL` remains `missions.User`. Database tables, content types, permissions and relationships are unchanged.

| Package | Implemented responsibility | Remaining legacy responsibility |
| --- | --- | --- |
| `apps.accounts` | Profile rank, history and profile overview selectors | Authentication/registration forms and views; custom User |
| `apps.teams` | Membership lookup, profile/team rankings, monthly league context | Membership writes and dashboard team operations |
| `apps.missions` | Pending review services, eligibility selectors, homepage read model | Request HTTP validation and creation; completion reward save hook; stale-save guard |
| `apps.questions` | Today's questions and user-specific answered IDs | Daily answer validation, creation and reward save hook |
| `apps.competitions` | Atomic finishing/finalization and competition list selector | Answer admission, scoring, registration/start and time limits |
| `apps.wallet` | Existing monthly ledger history query | No centralized writer: User balances, PointTransaction, domain payouts and legacy daily reward writes remain authoritative |
| `apps.treasure` | Atomic checkout, typed purchase errors and storefront queries | Fulfillment through the existing purchase model and staff interfaces |
| `apps.backoffice` | Dashboard overview statistics and queues | Staff decorators, request parsing, messages and operation authorization |
| `common.calendar` | Existing Jalali names and month boundaries | Naive boundaries intentionally preserve existing timezone behavior |

## Dependency direction

Views → domain selectors/services → Django ORM and `missions.models`.

Accounts overview uses team selectors, wallet history and calendar utilities. Team overview uses wallet history and calendar utilities. Mission homepage uses team membership and the existing daily-question models. Backoffice reads models across domains; it owns no reward rules.

Domain code does not import views, dashboard, templates, HTTP helpers or the legacy service/selector exports. A static contract test examines top-level and nested imports and checks domain import cycles. `missions.models` has four intentional local imports into mission/competition services. This runtime delegation returns to already-loaded models; no service calls the model wrapper that invoked it.

## Authorization and transactions

Services receive explicit model instances or IDs, not requests. Callers must authorize the subject and operation first. Selectors assume the supplied user is an authorized subject; they are not a substitute for permission checks. Dashboard overview is staff data and must never be exposed by an unguarded API.

Treasure checkout retains its active-item read before the atomic block, conditional F-expression debit, price/stock recheck, inventory reservation, ledger and purchase. It returns `(purchase, point_balance)`; insufficient points includes `shortfall`, stock errors are distinct, and database exceptions propagate after rollback. Coins are unchanged.

Mission review claims persisted pending status before creating a completion. The completion save hook still owns reward calculation, balance/streak and ledger writes inside the transaction. Successful review synchronizes the instance; a lost claim returns false. Reopening is not introduced.

Competition finish and finalization retain conditional write claims and atomic payouts. Finish refreshes the registration even after a lost claim; finalization updates the supplied competition on success. Ranking remains correct-count descending, finish-time ascending; unfinished eligibility is unchanged.

Legacy `missions.services.*` and `missions.selectors.*` explicitly re-export the same function and exception objects. There is one authoritative implementation per moved operation. Historical view helpers remain importable as aliases. New internal callers use domain paths directly.
