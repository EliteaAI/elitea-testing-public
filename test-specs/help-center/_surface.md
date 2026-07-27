# Help Center — exploration digest

Seeded 2026-07-23 (ELITEA-2219, first case to touch this surface). A handle
*cache*, not a substitute for execution — verify each handle live as you use it.

## Surface map

- **Entry point**: sidebar "?" icon, bottom-left, next to "Support Bot" label.
  Source: `EliteaUI/src/[fsd]/widgets/sidebar-root/ui/button/ResourcesButton.jsx`.
  Two render branches — `fullWidth` (expanded sidebar, icon + "Help Center" text
  label) vs non-`fullWidth` (collapsed sidebar, icon only + tooltip). **The
  non-`fullWidth` branch (lines 57-65) is what actually renders** in the default
  sidebar state observed live — confirm which branch is active before assuming.
- **Route**: `/help-center` (`RouteDefinitions.HelpCenter` in `EliteaUI/src/routes.js:77`),
  real SPA navigation via `react-router-dom`'s `useNavigate` (not a modal).
- **Page component**: `EliteaUI/src/[fsd]/pages/resources/index.jsx` (`ResourcesPage`)
  — note the FSD folder is `pages/resources`, NOT `pages/help-center`; the route/URL
  says "help-center" but the source folder and internal naming say "resources"
  throughout (`RESOURCES_TOUR_TARGET_IDS`, `useGetResourcesConfigQuery`, etc.) —
  don't search for "help-center" in `EliteaUI/src` and conclude the page doesn't
  exist; search "resources" instead.
- **Sub-components**: `pages/resources/ui/ResourceCard.jsx` (one card, reused 5×),
  `pages/resources/ui/ResourceVersionInfo.jsx` (header title + version info + "i" icon).
- **Project-independent**: both backing API calls are `admin`/`prompt_lib`-scoped,
  not `project_id`-scoped — confirmed live the page renders identically across
  different active projects. No `${ELITEA_PROJECT_ID}` dependency for any Help
  Center case.

## Confirmed content (as of this run — versions/dates WILL change per release)

- Page header title: exactly `"Help Center"` (top-left).
- Version info (top-right): `"Version: 2.0.3 (28-May-2026)"` — format is
  `Version: X.X.X (DD-Mon-YYYY)`; **assert by regex
  `^Version: \d+\.\d+\.\d+ \(\d{2}-[A-Za-z]{3}-\d{4}\)$`, never the literal value.**
  An "i" info icon sits next to it — hovering/clicking opens a tooltip listing
  per-plugin versions + a copy-to-clipboard button (not needed unless a future
  case tests the tooltip itself).
- Intro subtitle: `"Explore Help Center"`. Description:
  `"Guides, documentation, and release notes to support your work."`
- **Five** resource cards render by default (all `enabledKey`s default-enabled;
  none disabled in the current `resources` plugin config): Documentation,
  Release Notes, Video Library, Tutorials, Interactive Tours. **Case ELITEA-2219's
  own text says "four" — this is a confirmed case-text typo (CLARIFICATION
  [#998](https://github.com/EliteaAI/elitea-testing-public/issues/998)), not a
  product defect.** Don't re-litigate this on a future case that also touches
  card count.
- Card titles render visually ALL-CAPS via CSS `text-transform`, but the DOM
  text node itself is mixed-case (`"Documentation"`, not `"DOCUMENTATION"`) —
  **assert the DOM value**, not the rendered-visual string.
- Interactive Tours card's links: `"Sidebar Interactive Tour"` →
  `/app/chat?tour=sidebar`, `"Chat Interactive Tour"` → `/app/chat?tour=chat`.
  Other cards' links point to `docs.elitea.ai` / `videoportal.epam.com` /
  `learn.epam.com` (external — don't click through in automation, just assert
  visibility/text/href).

## Testid status — ZERO exist (confirmed via full-file read + `git grep` on both
`main` and `automation/testids`, fresh-fetched)

This entire surface has **no `data-testid` attributes anywhere** as of this run —
only `data-tour` attributes (wired for the interactive-tours feature). Every
Help Center case will need `testid needed:` work orders until the first
implementer pass adds them. **Reuse opportunity**: the existing `data-tour`
constants (`RESOURCES_TOUR_TARGET_IDS` in
`EliteaUI/src/[fsd]/features/interactive-tours/lib/constants/resourcesTourTargets.constants.js`)
already carry well-formed, unique, stable slugs for the page root
(`resources-page`) and each of the 5 cards (`resources-documentation-card`,
`resources-release-notes-card`, `resources-video-library-card`,
`resources-tutorials-card`, `resources-interactive-tours-card`) — the cheapest
fix is `data-testid={tourTargetId}` / `data-testid={RESOURCES_TOUR_TARGET_IDS.page}`
alongside the existing `data-tour`, not inventing new slugs. Full testid plan
(11 handles) is in `l3_page-loads-via-sidebar-icon_ELITEA-2219.md` § Concrete
Handles — read that AFS before re-deriving from scratch.

## Wait / timing quirks

- URL becomes `/help-center` **before** the `plugin_config_values/prompt_lib/resources`
  fetch resolves — the page root testid (once added) or the fetch response itself
  is the real "page ready" signal, not URL alone.
- Cards render MUI `Skeleton` placeholders while `isConfigLoading` is true — don't
  assert card title/subtitle/links immediately after navigation; wait on the
  response or on the first card's title testid having non-empty text.

## Network calls (both admin/prompt_lib-scoped, not project-scoped)

- `GET /api/v2/admin/system_info/prompt_lib` → 200 — plugin list for the version
  tooltip only.
- `GET /api/v2/admin/plugin_config_values/prompt_lib/resources` → 200 — drives
  card titles/descriptions/links/enabled-flags + the version label.

## Operational note

The shared lane-0 Playwright MCP browser was observed being navigated by a
concurrent process during this run (jumped to `/settings/personalization`,
`/credentials` mid-analysis without this analyst driving it). Didn't corrupt this
run's evidence (captured atomically per-action before interference), but future
Help Center analysts on a shared lane 0 should re-verify current URL/state before
trusting a `browser_console_messages(all=true)` call — it returns session-wide
messages, not scoped to your own navigation.
