# Full source layout migration

The root `missions/` and `dashboard/` packages were consolidated into `apps/`. Seven domains now define their own models. Public views, staff views, forms and Admin classes live in the domain that owns each feature. Tests live in `tests/` and use the domain imports.

| Integration | Python package | Django label |
| --- | --- | --- |
| Public routing, model registration, Admin discovery and migration history | `apps.web` | `missions` |
| Staff routing, decorators and shared templates | `apps.backoffice` | `dashboard` |

The `missions` label and URL namespace are compatibility identifiers. Code imports models from their domain, such as `apps.accounts.models.User` or `apps.missions.models.MissionRequest`. Historical imports under the removed root Python packages are replaced by those domain imports. Existing URLs, including Admin paths, continue to use their current names.

## Verification

- All 88 regression and architecture tests passed before and after the move using a disposable SQLite database.
- The architecture tests verified 19 domain model locations, original serialized model fields and table names, Admin registrations and the complete route inventory.
- All 39 normalized HTTP snapshots matched, including status, redirect, template context and query count.
- All 5,782 moved template, static and migration files matched their prior bytes. Django found the templates and static assets at their existing names.
- Django's migration dry run reported no model changes. Applying the migration command to a read-only-source SQLite backup copy found no pending migrations and changed none of its 29 tables. SQLite integrity and foreign-key checks passed on the copy.
- The original database and media matched their pre-edit SHA-256 hashes.

Known pre-existing defects are tracked separately in [technical debt](TECHNICAL_DEBT.md). The migration preserved the existing behavior of those routes.

## Rollback

The independent source archive, original file hashes, isolated tests and SQLite backup are stored in the external `layout-migration` evidence directory. Its rollout manifest lists paths to restore or remove when reverting the source layout. Verify the manifest and check for subsequent edits before restoring source files. Data restoration is unnecessary for reverting this layout change.
