# API Readiness Plan

**Design proposal for review.** The current application serves Django templates and some operation-specific JSON. The proposed /api/v1/ boundary would be introduced alongside the current UI in a separate approved phase.

React → versioned Django REST Framework view → authentication, input validation and subject authorization → selector or service → explicitly serialized JSON.

| Domain | Proposed /api/v1/ categories | Reuse and authorization requirements |
| --- | --- | --- |
| Accounts | session/login, session/logout, me and me/profile | Reuse Django authentication and form rules. Owner identity comes from the session. Reuse profile rank and history selectors. Privilege fields are excluded from account serializers. |
| Teams | teams, leagues and membership reads | Reuse league selectors after bounded month parsing and monthly totals. Define member name visibility and manager scopes before exposing a list. |
| Missions | eligible missions, own requests and privileged approve/reject actions | Reuse eligibility rules and Mission Review services. Scope member queries to request.user. Require action permission and authorized review scope independently of supplied IDs. |
| Questions | daily question and submit answer | Reuse existing daily eligibility and reward semantics after a dedicated boundary review. Exclude correct options and explanations before reveal is authorized. |
| Competitions | contests, own registration, start, answers, finish and privileged finalize | Reuse finish and finalization services. Scope registration to the caller and competition. Audit existing admission and scoring for a single reusable path before exposing writes. Resolve cutoff policy before exposing concurrent public answer and finalization writes. |
| Wallet | me/wallet and me/transactions | Owner-only, read-only projection of the two balances and ledger. Scope before filtering or paginating. Changes belong to authorized domain operations. |
| Treasure | catalog, checkout and own purchases | Reuse checkout with the authenticated buyer and an authorized active item. Define staff fulfillment separately. Avoid automatic replay until durable idempotency is specified and implemented. |

Serializers should allowlist fields, validate request shape, types and ranges, and return ISO 8601 timestamps with offsets. Keep Jalali presentation separate from machine timestamps and define explicit month formats and boundaries. Use integers for points and coins. Validate relationships such as question membership and object ownership against the authenticated subject. Derive balances, reward values, rank, review actor and state on the server. Keep concurrency-sensitive eligibility and transactional writes in the domain operation. Map service results at the HTTP boundary without adding duplicate reward code.

Build an action permission matrix for anonymous, authenticated owner, another member, team manager, staff with delegated permissions and superuser. Require explicit list-query scoping as well as object checks on detail and custom actions. Test forbidden cross-user IDs, request-body ownership injection, management actions and creation constraints. DRF object checks alone do not filter list querysets or authorize creation. [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/)

Start with same-origin React and Django sessions if the deployment topology permits. Use a CSRF-protected login and require CSRF on unsafe cookie-authenticated requests. Same-origin routing avoids cross-origin cookie configuration. If separate origins are required, decide the exact origin allowlist, credential settings, trusted CSRF origins and cookie policy together. If multiple clients need bearer credentials, design token issuance, expiry, revocation and storage before selecting the mechanism. Do not assume DRF will emit 401 under every authentication configuration. [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/)

Use bounded pagination for collections and allowlisted filters. Agree stable secondary keys before using cursor pagination. Preserve existing business ordering where a contract depends on it. Publish an OpenAPI contract and examples covering fields, pagination, auth, error codes and replay semantics. The proposed error envelope is:

```json
{"code":"insufficient_points","message":"Purchase could not be completed","field_errors":{}}
```

Use consistent 400 for malformed or invalid input, 403 for denied actions, 404 for absent or concealed objects, 409 for documented business conflicts and 503 for transient database failure. Authentication status follows the selected mechanism. Define which responses can be retried and avoid exposing internal exception text, answer keys or private records.

1. Approve the boundary, role matrix and frontend deployment topology. Address confirmed release blockers and document permissions.
2. Add DRF and versioned read-only endpoints in a separately approved phase. Start with current-user profile and catalog projections, schema and contract tests.
3. Pilot React against those reads with the existing Django UI available. Verify cookie or bearer auth and error handling in integration tests.
4. Introduce write endpoints one workflow at a time after permission, rollback, concurrency and replay tests. Track the competition cutoff and mission reopen decisions separately.
5. Validate production settings, observability, static/media delivery, backup recovery and load before public rollout.
