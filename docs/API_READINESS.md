# Future API integration

No REST framework, REST endpoints, React code or dependency additions were implemented.

A future `/api/v1/` transport can validate input and authorization, call the existing domain operations and serialize results. Keep Django sessions/permissions authoritative until a separately reviewed authentication design is approved.

| Future operation | Reusable implementation | Boundary obligation |
| --- | --- | --- |
| Purchase treasure | `apps.treasure.services.checkout.purchase_treasure_item` | Authenticated subject, validate item ID, map typed errors and database failures |
| Review mission | `apps.missions.services.review` | Staff/object-operation authorization and validated review note |
| Finish registration | `apps.competitions.services.rewards.finish_competition_registration` | Registration belongs to the authenticated user and current completion policy is enforced |
| Finalize contest | `apps.competitions.services.rewards.finalize_competition` | Explicit operation permission, not view-only access |
| Profile/league | Accounts/team overview selectors | Authorized subject, existing visibility and ordering |
| Daily questions | Questions daily selector | Never serialize the model's correct answer before submission |
| Storefront | Treasure storefront selector | User-scoped purchase history and allowlisted product fields |
| Staff overview | Backoffice overview selector | Staff authorization before query/serialization |

Selector dictionaries are reusable read models, not public JSON schemas. They contain Django instances and lazy querysets; serializers must explicitly allowlist fields. Never serialize all User fields or expose private ledger/history data. Templates still consume the original keys.

Financial operations must have one service implementation shared by all transports. Do not duplicate payouts in serializers, signals or API views. Mission completion still has an intentional model save side effect; calling it again can issue another independent completion reward. Daily answers and competition admission remain legacy workflows and need separate design/coverage before API exposure.

API readiness is structural, not approval to deploy. Request idempotency, late-answer/finalization coordination, daily reward atomicity and operation-specific permissions require separate policy/security work. Existing login redirect and Admin permission defects remain tracked.
