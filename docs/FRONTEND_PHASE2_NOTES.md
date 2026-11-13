# Frontend Phase 2 foundation

The foundation adds original warm indigo, clay and gold tokens, shared component classes, a five-expression inline SVG mascot, four-item mobile navigation, reduced-motion support and a DEBUG-only `/dev/styleguide` page. Existing page layouts and business flows remain for later phases.

## Definitions and data boundaries

- `User.total_points` is the current spendable point balance. `User.total_coins` is displayed as a separate balance without assigning it a new spending role.
- Earned points for progress/rank come from the existing profile selector (`total_earned`) and must be labeled separately from `total_points` when the Today/Profile pages are rebuilt. The global base header shows only current balances because it has no earned-total context.
- “Remaining tasks” on Today means `unanswered_daily` plus currently available home missions that are not already requested today. This is a presentational count of the existing home data, not a promise about every possible activity. Competitions are excluded until a started-registration selector exists. The count is not implemented in Phase 2.
- Streak is omitted until the update semantics of `activity_streak` are verified.
- `TODO(decision-1)`: the future approved-mission celebration may use a localStorage unseen-approved marker; no server read state is introduced in Phase 2.
- `cancelled` purchase status exists and has a component style.
- Competition answer JSON uses `score`; per-answer delta may be displayed as the difference between successive server scores. Expiry closes attendance on the server.
- Navigation and read-only content work without JavaScript. Answer and purchase interactions may require JavaScript under the current JSON contracts.

## Correct-answer exposure audit

The daily and competition templates do not interpolate `correct_option` or `is_correct` into the initial DOM. Both reference these fields only after a POST response in JavaScript. The server-side question models include the correct answer, so future template edits must continue to avoid rendering that field before submission.

## Verification boundary

The local shell did not expose a working Python or `py` launcher, so Django check and page rendering were not executable in this environment. Static inspection confirmed the added URL is DEBUG-gated and the template uses existing URL names. Browser, accessibility and responsive checks remain for the polish phase.
