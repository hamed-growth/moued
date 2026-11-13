# Home design system handoff

The first implementation target is the Django home page. Its primary action is opening the active missions for signed-in members and registration for visitors.

## Added

- `apps/web/static/css/variables.css`: `--ui-*` color, surface, type, spacing, radius, and motion tokens, with light and dark mappings.
- `apps/web/static/css/home.css`: home hero, daily question link, mission card, empty state, and responsive layout.
- The existing `game-button`, `game-chip`, `game-card`, and SVG mascot primitives are reused. Their usage is visible in `apps/web/templates/missions/home.html`.

## Next migration work

The older sections of the home template, the shared navigation, and the other pages still contain legacy Bootstrap styles and hardcoded values. Move them onto the shared tokens before treating the design system as enforced across the project. The existing Django templates remain the application stack; Tailwind and GSAP have not been installed.
