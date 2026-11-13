# Domain boundaries

| Domain | Owns |
| --- | --- |
| Accounts | User, authentication forms and views, profile and staff account operations |
| Teams | Team, TeamMember, membership and rankings |
| Missions | MissionCategory, Mission, TeamMission, MissionRequest, MissionCompletion and request/review/reward flows |
| Questions | Question, DailyQuestion, DailyQuestionAnswer and daily submissions |
| Competitions | Competition, CompetitionQuestion, CompetitionRegistration, CompetitionAnswer, participation, prizes and staff status changes |
| Wallet | PointTransaction, balance writes, ledger entries and reporting |
| Treasure | TreasureCategory, TreasureItem, TreasurePurchase, checkout and fulfillment |
| Backoffice | Staff authorization, dashboard routing, shared operational reads and templates |
| Web | Django registry, migration history, public routing, Admin discovery and shared UI assets |

Views and Admin validate transport input and enforce access. Services receive explicit arguments and coordinate changes to model state. Selectors build reads for a caller that has already checked access. Domain models, services and selectors stay independent of the views and Admin modules. The architecture tests enforce these import boundaries.

Domain model classes use the existing Django label `missions` so that Python code ownership and database identity can evolve independently. Model hooks delegate to services through local imports when an operation has to run for both direct model callers and HTTP/Admin callers.

Checkout owns the transaction for conditional stock and point updates, the purchase and the ledger entry. Mission review owns the pending-only claim and calls completion inside the same transaction. Competition finish and finalization keep their conditional writes and prize logic. All four workflows delegate balance and ledger writes to the wallet. Daily answers use the existing instance-based balance update, while mission and competition rewards use SQL increments.

The completion and daily answer save hooks pass Django's base save to their services. The services decide when to grade or award a record. Competition registration methods delegate starting and recording a result to the participation service. Admin status edits and bulk actions use the competition management service.

The service refactor passed 90 tests before and after the change, including a stale Admin edit after finalization and a daily answer edit that regrades without paying again. The 39 HTTP snapshots matched, and Django's migration dry run found no schema changes. The [technical debt register](TECHNICAL_DEBT.md) tracks existing policy and concurrency issues.
