---
name: frontend-design
description: "Use when building, modifying, or reviewing visual interfaces directly in HTML, CSS, Tailwind CSS, and vanilla JavaScript. Translate design principles into working responsive, accessible source code, including design tokens, layout, typography, components, interaction states, animation, and visual QA. Never require Figma or a design-editor workflow."
---

# Frontend Design — HTML, CSS, Tailwind CSS, JavaScript

This skill is **code-first**. Design is applied to the webpage itself, not produced as a separate mockup. Write real **semantic HTML**, **CSS or Tailwind CSS**, and **vanilla JavaScript**. The output must be functional source code. Do **not** use Figma, design-editor APIs, canvas layer tools, or a mockup-first process.

## Technology contract

- **HTML5** for semantic content, proper document structure, forms, landmarks, labels, and accessibility.
- **CSS3** for reusable design tokens, visual details, responsive layouts, states, animations, and motion preferences.
- **Tailwind CSS** when already installed or requested: use utility classes for layout and visual styling, centralize customization through the project's Tailwind theme and CSS variables. Tailwind is a **styling option**, not an extra framework to install blindly.
- **Vanilla JavaScript (ES modules)** for real interactions, events, state, DOM updates, galleries, menus, form validation, scroll behavior, and progressive enhancement.
- No required React, JSX, MUI, TypeScript, Vue, Angular, or other application framework. **Do not introduce these for a task governed by this skill.**
- Preserve the repo's actual Tailwind version. Tailwind v3 (`tailwind.config.js`) and v4 (CSS-first `@theme`) have different configuration patterns; inspect the installed version before editing configuration.
- Use existing packages and build tools when present. For a stand-alone page, prefer a minimal `index.html`, `styles.css`, `main.js` setup; avoid dependencies unless they solve a real need.
- Use provided branding, supplied content, and reference images as visual guidance to implement code. Never interpret images as an instruction to create Figma files.

## Working method

1. **Inspect** source files, current styling approach (CSS vs Tailwind), Tailwind version, current palette/fonts/tokens, assets, page structure, existing JS patterns, and responsive behavior. Reuse what exists rather than rebuilding a competing system.
2. **Plan the visible interface** in terms of semantic sections, responsive layout, behavior, loading/empty/error states, and keyboard interactions. For an existing page, preserve unaffected sections.
3. **Establish design tokens** in CSS custom properties or the active Tailwind configuration. Component styles refer to semantic tokens, not scattered raw brand hex codes or arbitrary utility values.
4. **Implement section by section**, starting with the primary visual hierarchy. Use HTML + CSS Grid/Flexbox or Tailwind utilities. Create interaction logic in JavaScript, without inline `onclick` handlers.
5. **Verify the running page**, not just the source text. Review desktop (~1440px), tablet (~768px), and mobile (~390px), plus keyboard use, both color modes if supported, and reduced motion. Fix overflow, alignment and state problems.
6. **Run checks that exist** (build, lint, local preview, browser checks). Report only checks actually performed, and explicitly flag any unavailable visual test.

## Rules to apply in code

### Semantic HTML and accessibility

- Start with valid HTML: `<!doctype html>`, `<html lang="..." dir="...">`, viewport meta, an appropriate page title, and recognizable `header`, `nav`, `main`, `section`, and `footer` landmarks.
- One logical `<h1>` per page in normal cases; heading order reflects content structure, not visual size. Choose real `<button>` for actions and `<a href>` for navigation. Use real `<label>` for form fields.
- Use native HTML behavior first; only add ARIA attributes when necessary. Update `aria-expanded`, `aria-selected`, etc. as JS state changes. Preserve visible focus and complete keyboard operation.
- All images have appropriate alt text; decorative images use `alt=""`. Videos have meaningful controls/captions where applicable, and never make essential content video-only.
- For Persian/Arabic content, set appropriate `lang` and `dir`, use CSS logical properties (`margin-inline`, `inset-inline-start`, etc.), and test that numerals, arrows, dates and mixed LTR text display correctly.

### Design tokens and CSS architecture

- Create a two-layer color system: **core palettes** (`--core-primary-500`, `--core-grayscale-870`, etc.) and **semantic interface roles** (`--surface-primary`, `--text-primary`, `--action-primary`, `--border-primary`, `--icon-default`, `--overlay-md`). Components consume semantic tokens, never raw palette tokens.
- Support light/dark by changing semantic aliases with `:root`, `[data-theme="light"]`, `[data-theme="dark"]` when themes are in scope. Respect existing theme behavior; do not bolt on a theme toggle unless requested.
- Use spacing values **0, 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96px** and radius values **0, 2, 4, 6, 8, 12, 16, 24px, full** unless brand or existing system dictates otherwise.
- Use `box-sizing: border-box`, fluid layout techniques, `minmax()`, `clamp()`, `min()` and `max()` as appropriate. Fixed token scales govern spacing; content can still size fluidly.
- Prefer classes and reusable component patterns over repeated inline `style=` strings. Tailwind utility composition is appropriate for visual rules; keep repeated complex patterns in reusable templates or well-scoped component classes.
- Make CSS specificity predictable; avoid gratuitous `!important`, global overrides of all buttons, and arbitrary values when a token fits.

### Tailwind CSS (when used)

- Preserve the installed Tailwind syntax. Use existing `@import "tailwindcss"` / `@theme` in v4, or `@tailwind` / `tailwind.config.js` in v3, depending on the repository.
- **Do not mix v3 and v4 setup instructions.** Never add an unnecessary Tailwind CDN in a production project.
- Configure theme colors to resolve to semantic CSS variables; enable classes such as `bg-surface-primary`, `text-text-primary`, `border-border-primary` if the project uses semantic theme naming. Prefer readable spacing/type/radius utilities over arbitrary brackets.
- Use responsive variants such as `sm:`, `md:`, `lg:` based on the project's configured breakpoints. Use `focus-visible:`, `disabled:`, `group-*`, `aria-*`, and `motion-reduce:` where relevant, not only `hover:`.
- Avoid dynamically concatenating class fragments in JavaScript (`'bg-' + color`) that Tailwind's scanner may not detect; use a static lookup of complete classes, explicit templates, or CSS variables.
- Dynamic state such as open/closed/active should be represented via JS-managed attributes, e.g. `data-state="open"`, `[aria-expanded="true"]`, or explicitly toggled known classes.

### Typography

- Use the brand font and genuine loaded weights. Default to one typeface; a monospace face for data/code is fine. In Persian UI use a Persian-capable font.
- Follow the type scale **12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72, 96, 128px** and the semantic families **Heading, Title, Body, Button, Caption** in the reference section.
- Apply styles as named CSS classes / design variables or Tailwind type utilities. Avoid one-off `font-size` decisions for every section.
- Headline wrapping should be intentional. Avoid orphaned final words, keep hero heading/subheading around 680px max width by default, and use natural Persian line-breaking in RTL pages.
- Default to no italics and no weights above bold. User reference/brand overrides these defaults.

### Color and composition

- Prefer flat UI surfaces. For a dark neutral system, default reference colors are `#000000`, `#181818`, `#1F1F1F`, `#272727`, `#313131`, `#131209`.
- Restrict strong accent color to a limited purpose. UI surfaces should not become generic multicolor gradients. A subtle **text-only** gradient on a hero heading can be used when fitting the brand (dark `#fff`→`#9b9b9b`; light `#000`→`#666`). Image/video/3D content can have its own rich visual treatment.
- Body text must meet contrast **≥4.5:1**; large text, focus indicators, and essential interface boundaries **≥3:1**. Do not communicate success/error/active state by color alone.
- Use all-around borders for cards or no card border; use separate 1px row dividers for lists. Do not auto-generate uniform three-card grids for every section. Prefer hierarchy and appropriate asymmetry.
- Align repeating card headings/actions, use whitespace deliberately, and avoid decorative details that obscure product content.

### Layout, breakpoints, mobile

- Build mobile-friendly layouts from the start. Check at **390 / 768 / 1440px** even if the CSS breakpoints differ. A common desktop marketing container is **1200–1280px max** inside a 1440px viewport.
- Use CSS Grid for two-dimensional composition and Flexbox for one-dimensional alignment. In Tailwind, use corresponding `grid`, `flex`, `gap-*`, `max-w-*`, `mx-auto` utilities with consistent tokens.
- Avoid hardcoded `100vw` width in padded containers, fixed heights that clip text, awkward mobile carousels, and horizontal overflow. Use `max-width: 100%` for media and suitable `object-fit` for thumbnails.
- Mobile tap targets are at least **44×44px**, with unobscured focus and labels.
- Buttons commonly start with 8px vertical / 12px horizontal padding; expand hit area to 44px where needed.
- For nested corners within <32px spacing, a useful heuristic is **inner radius = outer radius - gap**, snapped to the radius token scale where result >2px.

### Vanilla JavaScript and interactive states

- Use `addEventListener`, ES modules, `classList`, `dataset`, native dialogs/details where appropriate, and functions with clear responsibilities. Avoid inline event handlers, unrelated global variables, and extra dependencies.
- Interactions must work: tabs update content, thumbnails change the active preview, menus open/close including Escape/outside interactions, modals trap/restore focus where appropriate, and forms validate before submit.
- Keep HTML and visual states synchronized (`aria-expanded`, `aria-hidden`, active class, `hidden` attribute, accessible labels). Keyboard behavior is not optional.
- Provide **default, hover, pressed, focus, disabled** states for buttons, **filled/error** states for inputs, and meaningful **loading, empty, error** views when there is data fetching.
- Use real content or clearly marked sample content. Do not fabricate a working backend; if data is unavailable, implement a graceful UI and state the integration point.
- For animations, prefer simple CSS transitions when sufficient. Use GSAP or Three.js only if the project has them or the requested effect justifies them. Avoid unbounded scroll handlers; use `requestAnimationFrame` or observers where suitable and clean up event listeners on dynamic teardown.
- Respect `prefers-reduced-motion`, especially for parallax/scroll/3D, and keep reading/navigation functional without JavaScript wherever feasible.
- For scroll-driven effects, treat the visual as progressive enhancement; content must remain accessible when animations or WebGL fail.

### Copy and media

- Use concise, product-specific content rather than lorem ipsum, invented customer praise, or generic buzzwords like “revolutionize,” “supercharge,” and “world class.”
- Respect the actual aspect ratio, focal point, and quality of supplied media. Use `loading="lazy"` for suitable below-the-fold images and avoid lazy loading the primary hero image when it hurts first paint.
- Do not add generic eyebrow pills and stock icons to every layout. Icon usage should have a consistent visual style; do not install an icon set just for decoration.

## Minimal implementation patterns

### Plain HTML (semantic, interactive)

```html
<section class="showcase" aria-labelledby="showcase-title">
  <div class="showcase__content">
    <h2 id="showcase-title" class="heading-2">Selected projects</h2>
    <p class="body-3">A closer look at our recent work.</p>
    <button class="button button--primary" type="button" id="show-more"
            aria-controls="more-projects" aria-expanded="false">
      Explore projects
    </button>
  </div>
  <div class="showcase__media">
    <img src="assets/project.jpg" alt="Installed industrial equipment" />
  </div>
</section>
<section id="more-projects" hidden aria-label="More projects">
  <!-- Render real project content here. -->
</section>
```

### Plain CSS (semantic token usage)

```css
:root {
  --core-neutral-0: #fff;
  --core-neutral-900: #181818;
  --core-accent-500: #477bc8; /* example only: replace with actual brand palette */
  --space-75: 8px;
  --space-100: 12px;
  --space-300: 24px;
  --radius-8: 8px;
  --radius-16: 16px;
  --surface-primary: var(--core-neutral-0);
  --text-primary: var(--core-neutral-900);
  --action-primary: var(--core-accent-500);
}
[data-theme="dark"] {
  --surface-primary: var(--core-neutral-900);
  --text-primary: var(--core-neutral-0);
}
.showcase {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  gap: var(--space-300);
  padding-block: var(--space-300);
  color: var(--text-primary);
  background: var(--surface-primary);
}
.showcase__media img { display: block; width: 100%; height: auto; border-radius: var(--radius-16); }
.button { min-height: 44px; padding: var(--space-75) var(--space-100); border-radius: var(--radius-8); }
.button:focus-visible { outline: 2px solid currentColor; outline-offset: 3px; }
@media (max-width: 768px) { .showcase { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; } }
```

### Tailwind CSS version-aware integration

Tailwind v4, when that version is installed, can expose semantic tokens in a CSS theme:

```css
@import "tailwindcss";
@theme inline {
  --color-surface-primary: var(--surface-primary);
  --color-text-primary: var(--text-primary);
  --color-action-primary: var(--action-primary);
}
```

Use `bg-surface-primary text-text-primary` and `bg-action-primary` in HTML. For **Tailwind v3**, instead extend `theme.colors` in the existing `tailwind.config.js`, e.g. `surface: { primary: 'var(--surface-primary)' }`. Maintain the same semantic CSS variables in either case. **Do not simultaneously add v3 and v4 configuration.**

### Vanilla JavaScript (real button behavior)

```js
const showMoreButton = document.querySelector('#show-more');
showMoreButton?.addEventListener('click', () => {
  const projects = document.querySelector('#more-projects');
  if (!projects) return;
  const willShow = projects.hidden;
  projects.hidden = !willShow;
  showMoreButton.setAttribute('aria-expanded', String(willShow));
  showMoreButton.textContent = willShow ? 'Show fewer projects' : 'Explore projects';
});
```

The HTML snippet includes the corresponding initially hidden section and `aria-controls`; replace the sample media and content with actual supplied assets before shipping.

## Validation checklist

- [ ] Output is **real HTML + CSS/Tailwind CSS + vanilla JavaScript**, not design editor work, React, MUI, or TS.
- [ ] Semantic HTML structure, alt text, labels, heading order, keyboard behavior, and visible focus are correct.
- [ ] Styles use **named tokens** and keep a coherent spacing, typography, radius, and semantic color system.
- [ ] Tailwind version and configuration were inspected; no conflict or unnecessary dependency added.
- [ ] CSS and Tailwind responsibilities are clear; arbitrary values and duplicate conflicting rules are minimized.
- [ ] Responsive layouts work near 390px, 768px, 1440px without horizontal overflow.
- [ ] Contrast, disabled/error/active states, and accessible tap target sizes meet stated rules.
- [ ] JavaScript interactions work, DOM state matches ARIA state, and UI degrades gracefully if JavaScript fails.
- [ ] Motion honors reduced-motion and does not block content; media loads and has appropriate fallback.
- [ ] Any available build, lint, browser, and visual checks were honestly reported.

## Token reference

Preserve these token names and numeric scales when adding or changing a design system. Brand colors may change. In CSS, normalize names to kebab-case, e.g. `Surface/Primary-Hover` → `--surface-primary-hover` and `spacing/300` → `--space-300`.

### Spacing

Values are CSS pixels. Implement as CSS custom properties or Tailwind theme values. Use them for `gap`, `padding`, `margin`, and layout spacing.

| Token | Value |
|---|---|
| spacing/0 | 0 |
| spacing/25 | 2 |
| spacing/50 | 4 |
| spacing/75 | 8 |
| spacing/100 | 12 |
| spacing/200 | 16 |
| spacing/300 | 24 |
| spacing/400 | 32 |
| spacing/500 | 40 |
| spacing/600 | 48 |
| spacing/700 | 64 |
| spacing/800 | 80 |
| spacing/900 | 96 |

### Radius

Values are CSS pixels; `full` is a pill radius. Apply through tokens to `border-radius`.

| Token | Value |
|---|---|
| radius/0 | 0 |
| radius/2 | 2 |
| radius/4 | 4 |
| radius/6 | 6 |
| radius/8 | 8 |
| radius/12 | 12 |
| radius/16 | 16 |
| radius/24 | 24 |
| radius/full | 9999 |

### Text styles

Use the project's brand typeface and define the styles as reusable CSS classes, Tailwind utility mappings. Keep their logical group names (`Heading / Heading 1`, etc.). Letter spacing is 0 unless the product defines otherwise.

| Folder / Style | Scale step | Size / line height | Weight |
|---|---|---|---|
| Heading / Heading 1 | `text-6xl` | 60 / 60 | Regular |
| Heading / Heading 2 | `text-5xl` | 48 / 48 | Regular |
| Heading / Heading 3 | `text-4xl` | 36 / 40 | Regular |
| Heading / Heading 4 | `text-3xl` | 30 / 36 | Regular |
| Heading / Heading 5 | `text-2xl` | 24 / 32 | Regular |
| Heading / Heading 6 | `text-xl` | 20 / 28 | Regular |
| Title / Title 1 | `text-xl` | 20 / 28 | Medium |
| Title / Title 2 | `text-lg` | 18 / 28 | Medium |
| Title / Title 3 | `text-base` | 16 / 24 | Medium |
| Title / Title 4 | `text-sm` | 14 / 20 | Medium |
| Title / Title 5 | `text-xs` | 12 / 16 | Medium |
| Body / Body 1 | `text-base` | 16 / 24 | Semibold |
| Body / Body 2 | `text-base` | 16 / 24 | Medium |
| Body / Body 3 | `text-base` | 16 / 24 | Regular |
| Body / Body 4 | `text-sm` | 14 / 20 | Semibold |
| Body / Body 5 | `text-sm` | 14 / 20 | Medium |
| Body / Body 6 | `text-sm` | 14 / 20 | Regular |
| Button / Button-lg | `text-lg` | 18 / 28 | Semibold |
| Button / Button-md | `text-base` | 16 / 24 | Semibold |
| Button / Button-sm | `text-sm` | 14 / 20 | Semibold |
| Button / Button-Xsm | `text-xs` | 12 / 16 | Semibold |
| Caption / Caption 1 | `text-sm` | 14 / 20 | Medium |
| Caption / Caption 2 | `text-sm` | 14 / 20 | Regular |
| Caption / Caption 3 | `text-xs` | 12 / 16 | Semibold |
| Caption / Caption 4 | `text-xs` | 12 / 16 | Medium |
| Caption / Caption 5 | `text-xs` | 12 / 16 | Regular |

Confirm each font weight is actually loaded in the app. Do not rely on synthesized weights when a real font file or web font variant is available.

### Color

#### Layer 1: `Core Colors`

Raw brand palette CSS variables (`--core-*`) are the only place for hardcoded brand color values.

| Palette | Role | Shades |
|---|---|---|
| `Primary` | main brand hue | 00, 50, 100, 150, 200, 300, 350, 400, 450, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Secondary` | second brand hue | 00, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Accent` | accent hue | 00, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Grayscale` | neutrals | 00, 50, 100, 150, 200, 250, 300, 400, 450, 500, 600, 700, 750, 800, 850, 870, 900, 950, 1000 |
| `Red` | error | 00, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Green` | success | 00, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Yellow` | warning | 00, 50, 100, 150, 200, 300, 400, 500, 600, 700, 800, 850, 900, 950, 1000 |
| `Grayscale-Alpha` | see-through neutrals for overlays | 700-16, 700-24, 700-40, 700-64, 700-80 (the Grayscale/700 hex at 16%, 24%, 40%, 64%, 80% opacity, stored in the variable's own opacity field) |

- `00` is near white, `500` is the base hue and `1000` is near black.
- Keep the Grayscale dark steps on the allowed dark backgrounds: `1000` = #000000, `870` = #181818, `850` = #1F1F1F, `800` = #272727, `750` = #313131.

#### Layer 2: `Color System`

Provide both `[data-theme="light"]` and `[data-theme="dark"]` (or the existing CSS-theme equivalent). Each semantic token aliases a core palette token, such as `--surface-primary: var(--core-grayscale-870)`. The Dark column is the reference mapping. Create Light aliases by using corresponding light shades and verify contrast.

**Border**

| Token | Dark alias |
|---|---|
| Border/Primary | Grayscale/750 |
| Border/Primary-Disabled | Grayscale/800 |
| Border/Primary-light | Grayscale/700 |
| Border/Secondary | Grayscale/750 |
| Border/Tertiary | Grayscale/600 |
| Border/Action-Primary | Primary/400 |
| Border/Action-Disabled | Primary/600 |
| Border/Action-Secondary | Grayscale/500 |
| Border/Error | Red/400 |
| Border/Error-disabled | Red/700 |
| Border/Success | Green/400 |
| Border/Warning | Yellow/300 |
| Border/Warning - Disabled | Yellow/700 |

**Surface**

| Token | Dark alias |
|---|---|
| Surface/Primary | Grayscale/870 |
| Surface/Primary-Hover | Grayscale/800 |
| Surface/Primary-Selected | Grayscale/700 |
| Surface/Primary-subtle | Grayscale/850 |
| Surface/Secondary | Grayscale/800 |
| Surface/Secondary-Hover | Grayscale/700 |
| Surface/Secondary-Selected | Grayscale/700 |
| Surface/Secondary-Subtle | Grayscale/750 |
| Surface/Tertiary | Grayscale/600 |
| Surface/Tertiary-Hover | Grayscale/450 |
| Surface/Accent | Accent/500 |
| Surface/Accent-subtle | Accent/200 |
| Surface/Info | Primary/400 |
| Surface/Info-subtle | Primary/150 |
| Surface/Error | Red/500 |
| Surface/Error-subtle | Red/100 |
| Surface/Error - Darker | Red/700 |
| Surface/Inverted | Grayscale/00 |
| Surface/Inverted-Hover | Grayscale/250 |
| Surface/Inverted-Disabled | Grayscale/450 |
| Surface/Warning | Yellow/500 |
| Surface/Warning-subtle | Yellow/100 |
| Surface/Warning - Hover | Yellow/700 |
| Surface/Success | Green/500 |
| Surface/Success-Subtle | Green/100 |

**Action** (button and control fills)

| Token | Dark alias |
|---|---|
| Action/Primary | Primary/500 |
| Action/Primary-Hover | Primary/700 |
| Action/Primary-Click | Primary/600 |
| Action/Primary-Disabled | Primary/700 |
| Action/Secondary | Grayscale/600 |
| Action/Secondary-Hover | Grayscale/750 |
| Action/Secondary-Click | Grayscale/700 |
| Action/Error | Red/700 |
| Action/Error-Hover | Red/800 |
| Action/Error-Disabled | Red/800 |
| Action/Error-Subtle | Red/150 |
| Action/Warning | Yellow/500 |
| Action/Warning - Hover | Yellow/700 |
| Action/Warning - Disabled | Yellow/800 |
| Action/Warning - Subtle | Yellow/100 |

**Text**

| Token | Dark alias |
|---|---|
| Text/Primary | Grayscale/50 |
| Text/Primary-Disabled | Grayscale/750 |
| Text/Primary-Subtle | Grayscale/500 |
| Text/Secondary | Grayscale/200 |
| Text/Secondary-Disabled | Grayscale/500 |
| Text/Tertiary | Grayscale/400 |
| Text/Inverted | Grayscale/850 |
| Text/Error | Red/500 |
| Text/Error-Disabled | Red/800 |
| Text/Error-Inverted | Red/800 |
| Text/Error-Inverted-Disabled | Red/200 |
| Text/Success | Green/600 |
| Text/Success-Inverted | Green/700 |
| Text/Success-Inverted-Disabled | Green/300 |
| Text/Info | Primary/350 |
| Text/Info-Inverted | Primary/700 |
| Text/Info-Inverted-Disabled | Primary/200 |
| Text/Warning | Yellow/500 |
| Text/Warning - Disabled | Yellow/800 |
| Text/Warning-Inverted | Yellow/800 |
| Text/Warning-Inverted-Disabled | Yellow/300 |

**Icon**

| Token | Dark alias |
|---|---|
| Icon/Default | Grayscale/50 |
| Icon/Secondary | Grayscale/200 |
| Icon/Subtle | Grayscale/500 |
| Icon/Inverted | Grayscale/850 |
| Icon/Disabled | Grayscale/750 |
| Icon/Error | Red/500 |
| Icon/Error-Disabled | Red/800 |
| Icon/Error-Inverted-Disabled | Red/200 |
| Icon/Info | Primary/350 |
| Icon/Info-Disabled | Primary/200 |
| Icon/Warning | Yellow/500 |
| Icon/Warning-Inverted | Yellow/700 |
| Icon/Warning - Disabled | Yellow/800 |
| Icon/Warning-Inverted-Disabled | Yellow/300 |
| Icon/Success | Green/400 |
| Icon/Success-Inverted-Disabled | Green/300 |

**Overlay**

| Token | Value |
|---|---|
| Overlay/xs | Grayscale-Alpha/700-16 |
| Overlay/sm | Grayscale-Alpha/700-24 |
| Overlay/md | Grayscale-Alpha/700-40 |
| Overlay/lg | Grayscale-Alpha/700-64 |
| Overlay/xlg | Grayscale-Alpha/700-80 |

Put alpha in the core alpha color token (for example using `rgb(R G B / 0.16)`). Semantic `--overlay-*` tokens alias those alpha tokens; don't scatter one-off overlay opacity values in components.