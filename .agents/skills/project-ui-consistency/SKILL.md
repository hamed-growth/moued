---
name: project-ui-consistency
description: Keep the Moud Club Django frontend visually consistent when creating or editing pages, buttons, forms, cards, tables, navigation, and interaction states in this repository.
---

# Moud Club UI consistency

Use this skill for frontend implementation or visual review in this repository. Its purpose is to make each new or changed interface element look and behave like the same product. Apply the user's current design request when it is more specific.

## Source of truth

- Read `apps/web/static/css/variables.css` before choosing visual values. The `--ui-*` tokens are the intended shared theme. Add a missing reusable value there, with light and dark mappings where relevant.
- Read `apps/web/static/css/game-foundation.css` before adding a primitive. Reuse or extend `game-button`, `game-card`, `game-chip`, `game-status`, `game-option`, `game-progress`, `game-empty`, `game-skeleton`, `game-toast`, `game-modal`, and `game-sheet` where suitable.
- The current frontend uses Django templates, Bootstrap RTL, local CSS, and local JavaScript. Keep the server-side URLs, form names, template conditions, and request flows intact. Tailwind and GSAP are not installed; do not assume their classes or APIs work.
- `apps/web/templates/parents/base.html` is the user-facing shell. `apps/backoffice/templates/dashboard/base.html` is the management shell. Inspect both when a shared change could affect both areas.

## Work on a page or component

1. Inspect the target template, its CSS and JavaScript, the shared shell, and a comparable existing component. Identify existing states and functional hooks before editing.
2. Choose one clear primary action. Reuse the same button, card, input, status, and feedback patterns across the page. Avoid creating page-specific copies of an existing primitive.
3. Use `--ui-*` tokens for new colors, spacing, radius, typography, surfaces, borders, and motion. Prefer CSS classes over inline styles. When editing legacy markup, migrate the touched element rather than adding another visual convention.
4. Keep the interface Persian, RTL, mobile-first, and touch-friendly. Use Vazirmatn, logical CSS properties, readable Persian copy, and a 48px minimum target for primary controls.
5. Cover relevant idle, hover, focus, pressed, disabled, loading, empty, success, and error states. Feedback must contain text or an icon as well as color. Use `aria-busy`, live regions, labels, and visible keyboard focus where appropriate.
6. For tables, use one consistent header, row spacing, border, status badge, and action-button pattern. Preserve semantic `<table>`, `<th scope>`, and captions or accessible names. On narrow screens, provide a deliberate scroll container or card layout without hiding essential data or actions.
7. Keep motion short and purposeful. Animate transform and opacity, respect `prefers-reduced-motion`, and avoid movement that blocks the next action. Introduce GSAP only when the task calls for animation that CSS cannot handle cleanly.
8. Check the changed page at mobile and desktop widths, including RTL alignment, long Persian labels, keyboard navigation, contrast, and empty/error data. Run `manage.py check` and relevant existing tests when templates or behavior change.

## Existing migration boundary

The project still contains older Bootstrap button classes, hardcoded values, and dashboard table styles. Treat them as migration targets, not as a second design system. Do not claim project-wide consistency until all user and dashboard pages have been audited and migrated. Keep changes scoped to the requested page or component unless a shared primitive needs a small compatible fix.

When reporting work, name the tokens and primitives added or reused, the pages verified, and any remaining legacy styles that affect the result.
