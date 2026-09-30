# Test Case: Help Center — page loads successfully via sidebar icon

## Metadata
- **TMS ID**: ELITEA-2219
- **Linked Story**: none (tracking issue: elitea-testing-public#2382)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  @ `956d1fa3`, 0 behind `origin/main`; DEV backend)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (localhost bypasses Keycloak
  via `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

### Why `ready-for-automation` and not `extend-existing`
Three merged specs exist in `automation/tests/ui/help_center/`
(`test_help_center_resource_links.py`, `test_help_center_sidebar_tour.py`,
`test_help_center_version_info.py`). **All three reach the page by URL** via
`HelpCenterPage.navigate()` → `/help-center`. Verified: `grep -rn "ELITEA-2219"
automation/ test-specs/` → 0 hits, and no spec references the sidebar Help Center
control at all (every "sidebar" match in `tests/ui/help_center/` is the
*interactive-tour resource card*, not the sidebar button).

This case's distinctive observable is the **sidebar-icon entry path** (Steps 1–3) plus
**whole-page composition** (Steps 5–8: intro title/description and all five cards' icon,
title, subtitle, links) — none of which any merged spec asserts. Overlap with ELITEA-2225
is incidental only (that case *hovers* the info icon and asserts tooltip contents +
clipboard; this one asserts the version label's **format** and the icon's **presence**
after arriving via the sidebar). The gap is a new flow plus ~25 new assertions — a
near-rewrite if bolted onto a covering spec — so per `test-case-analysis` § Classify
findings' boundary call this is a fresh spec: **new file
`automation/tests/ui/help_center/test_help_center_page_loads.py`**.

## Preconditions
- User is authenticated (`auth_state` fixture; localhost skips login via `VITE_DEV_TOKEN`).
- **The navigation sidebar must be EXPANDED.** This is the default on every page load and
  needs no action — but it is load-bearing, see § Automation Hints "Sidebar-expanded
  precondition". The Help Center control does **not render at all** when the sidebar is
  collapsed.
- The test must start on a page **other than** `/help-center`, so that Step 2's click is a
  real navigation. `ResourcesButton` early-returns (`if (isOnResources) return;`) when
  already on the page, so clicking it from `/help-center` is a no-op.
- No seeded state required — every observable is app config + backend-served CMS data
  (`useGetResourcesConfigQuery` / `useGetSystemInfoQuery`), never user data.

## Test Data
### reuse-existing
- (none required) — card titles/descriptions fall back to hardcoded defaults in
  `RESOURCE_CARD_CONFIGS`; link sets and the version string are backend-CMS-served.

### generate-per-test
- (none) — the case is read-only: no creation, no mutation, no cleanup.

### generate-shared-with-cleanup
- (none)

## Test Steps

1. **Transit** — navigate to a non-Help-Center page (`/chat`) and wait for the sidebar to
   render.
   - **Verify**: `sidebar-help-center-button` is visible.
2. Click `sidebar-help-center-button`.
3. **Verify** the Help Center page opened.
   - URL path is `/help-center` (assert the path, not the full URL — see § Automation Hints).
   - `help-center-page-header` is visible.
4. **Verify** the page title in the top-left header.
   - `help-center-page-header` has text exactly `Help Center`.
5. **Verify** the intro subtitle and description.
   - `help-center-intro-title` has text exactly `Explore Help Center`.
   - `help-center-intro-description` has text exactly
     `Guides, documentation, and release notes to support your work.`
6. **Verify** all **five** resource cards are visible, each with its title.
   - For each `(category, title)` in the table below: `help-center-card-{category}` is
     visible and `help-center-card-{category}-title` has that exact text.
   - Assert the card count is exactly 5 (`help-center-card-` prefix yields 5 elements).
7. **Verify** each card displays its links.
   - For each of the five cards: it contains **at least one** link, and every link in it
     has a non-empty `href` and `target="_blank"`.
   - The Interactive Tours card additionally shows **exactly** the two links the case
     names: `help-center-tour-link-sidebar-interactive-tour` ("Sidebar Interactive Tour")
     and `help-center-tour-link-chat-interactive-tour` ("Chat Interactive Tour").
   - Link *titles/URLs of the other four cards are NOT frozen as literals* — they are
     backend-CMS data that legitimately changes per release (§ Automation Hints).
8. **Verify** each card shows its icon, title, and subtitle description.
   - For each of the five categories: `help-center-card-{category}-icon` is visible,
     `-title` has the expected title, `-description` has the expected description
     (table below).
9. **Verify** the application version and the "i" info icon in the top-right corner.
   - `help-center-version-label` is visible and its text matches
     `^Version: \d+\.\d+\.\d+ \(\d{2}-[A-Za-z]{3}-\d{4}\)$`.
   - `help-center-version-info-icon` is visible.
   - Relational "top right vs top left": the version label's bounding-box `x` is greater
     than `help-center-page-header`'s `x` (Step 4's title is top-left, this is top-right),
     and the info icon's `x` is greater than the version label's `x` ("near it", to its
     right).
   - **Presence only — do NOT open or assert the tooltip's contents.** Tooltip content +
     copy-to-clipboard is ELITEA-2225's scope
     (`l2_version-info-tooltip-copy_ELITEA-2225.md`), already merged.

### The five cards — expected titles and descriptions (live-confirmed 2026-09-30)

| `{category}` | Title | Description |
|---|---|---|
| `documentation` | Documentation | API reference, guides, and platform concepts |
| `release-notes` | Release Notes | Product updates, improvements, and fixes |
| `video-library` | Video Library | Product walkthroughs and recorded sessions |
| `tutorials` | Tutorials | Step-by-step guides and use cases |
| `interactive-tours` | Interactive Tours | Guided tours to explore key features and workflows |

`{category}` values are **not invented** — they are the existing `testidCategory` field
already present on every `RESOURCE_CARD_CONFIGS` entry in `ResourcesPage.jsx` (added by the
ELITEA-2223/2224 collision fix). Reuse that field; do not add a parallel mapping.

## Expected Results
- Clicking the sidebar Help Center control navigates to `/help-center`.
- Header `Help Center`; intro title `Explore Help Center`; intro description
  `Guides, documentation, and release notes to support your work.`
- Exactly 5 resource cards, each rendering an icon, its title, its description, and ≥1 link.
- Interactive Tours card shows exactly the two named tour links.
- Version label matches `Version: X.Y.Z (DD-Mon-YYYY)`; info icon visible immediately to
  its right, in the top-right of the header.
- **No console errors** throughout (observed: zero, across 4 independent live runs).

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective / Expected Final State: version `Version: X.X.X (DD-Mon-YYYY)` shown top-right with "i"-in-circle icon near it | version + icon present, top-right | step 9 | `step 9`: regex on `help-center-version-label`, `help-center-version-info-icon` visible, relational x-ordering vs header | asserted |
| Precondition: user logged in to Elitea | authenticated session | § Preconditions | `auth_state` fixture (localhost: `VITE_DEV_TOKEN`) | asserted *(setup — not re-asserted)* |
| 1 Locate the "?" (Help Center) icon at the bottom of the left sidebar next to "Support Bot" | control present | steps 1 | `step 1`: `sidebar-help-center-button` visible | asserted *(the "next to Support Bot" phrase is an environment-gated location hint, NOT asserted — see Axis 2 note + § Automation Hints "Two mutually-exclusive sidebar renders")* |
| 2 Click the "?" icon | control responds, navigates | step 2 | `step 2`: click | asserted |
| 3 Verify the Help Center page opens | page opened | step 3 | `step 3`: URL path `/help-center` + `help-center-page-header` visible | asserted |
| 4 Page title "Help Center" in the top-left header | title displayed | step 4 | `step 4`: exact text on `help-center-page-header` | asserted |
| 5 Subtitle "Explore Help Center" + description "Guides, documentation, and release notes to support your work." | both displayed | step 5 | `step 5`: exact text on `help-center-intro-title` / `-intro-description` | asserted |
| 6 "four resource cards" then names **five**: DOCUMENTATION, RELEASE NOTES, VIDEO LIBRARY, TUTORIALS, INTERACTIVE TOURS | all visible | step 6 | `step 6`: 5 card roots visible + exact titles + count == 5 | asserted *(the word "four" is a known case-text typo — already tracked as `question` #998; the live contract is FIVE, re-confirmed in source: `RESOURCE_CARD_CONFIGS` has exactly 5 entries, and live: 5 cards rendered. Not re-filed.)* |
| 7 All cards visible with their links (e.g. INTERACTIVE TOURS → "Sidebar Interactive Tour", "Chat Interactive Tour") | links displayed | step 7 | `step 7`: ≥1 link per card + non-empty href + `target=_blank`; Interactive Tours card asserts exactly the two named links literally | asserted *(decomposed — other four cards' link titles/URLs deliberately not frozen; see § Automation Hints "CMS-driven link data")* |
| 8 Each card shows its icon, title, and subtitle description | icon + title + subtitle per card | step 8 | `step 8`: `-icon` visible, `-title` / `-description` exact text, ×5 | asserted |
| 9 Version "Version: X.X.X (DD-Mon-YYYY)" top-right with "i" icon near it | as stated | step 9 | see row 1 | asserted |

**Axis 2 — Analyst additions.**

- `step 3` asserts the URL **path** (not the full URL) — *added: the app is served under
  `APP_PREFIX` (`""` on localhost, `/app` on deployed envs), so a full-URL assertion would
  false-red in CI. Confirmed in source: `routes.js:160` returns `''` as the router base in
  DEV, `VITE_BASE_URI` otherwise.*
- `step 6` asserts the card **count is exactly 5** — *added: guards the #998 "four vs five"
  ambiguity from silently becoming true in either direction (a dropped card OR a sixth one
  appearing would otherwise pass a per-card-visible-only check).*
- `step 7` asserts every link's `target="_blank"` and non-empty `href` — *added: observed
  live that all 19 links carry `target="_blank"` + a resolvable href; a link rendering with
  no URL degrades silently to a plain `(undefined)` `<Typography>` instead of an `<a>`
  (`ResourcesPage.jsx` `link.url ? <Link> : <Typography>{title} (undefined)</Typography>`),
  which a text-only check would not catch.*
- `step 9` asserts the version string by **regex, not literal** — *added: the live value is
  `Version: 2.0.3 (28-May-2026)`, which is backend deploy metadata (`configValues
  .resources_information_version` / `_upgrade_date`) and legitimately changes on the next
  release. Same reasoning already established for this surface in
  `test_help_center_version_info.py` (see `.agents/memory/qa-engineer/
  version_number_literals_are_flaky_assertions.md`).*
- `step 9` asserts **relational x-ordering** (label right of header, icon right of label)
  — *added: the case says "top right corner" and "near it"; presence alone would pass even
  if the layout collapsed the label to the left. Rects observed at 1600×1000: header
  x=240, label x=1362 (w=194), icon x=1562.*
- All steps assert **no console errors** — *added: observed zero console errors across four
  independent live runs, so a clean baseline genuinely exists to guard. Use
  `utils/console_errors.collect_console_errors()` (URL-bearing) per `.agents/testing.md`,
  not the URL-less `page.on("console", …)` shape.*
- **NOT asserted: adjacency to "Support Bot"** — *the case's Step-1 phrase describes the
  layout that appears only when the Support Assistant is enabled at build time. Two
  mutually-exclusive sidebar renders exist (§ Automation Hints); asserting adjacency would
  bind the spec to one build configuration for a reason unrelated to the behaviour under
  test. Step 1's substantive observable — the control is present and opens the page — is
  fully asserted. Declared, not dropped: raised to the lead as a scope/canon question.*

## Cleanup
- **None.** The case is entirely read-only: no entity is created, edited, or deleted, and
  no org/project-level default is touched. Nothing is left behind, so the
  `.agents/testing.md` § Teardown-guard ordering rule has no subject here.

## Concrete Handles (discovered during exploration)

Provenance verified 2026-09-30 with a fresh `git fetch origin` in `../EliteaUI`, using the
two-stage grep from `.agents/workflow.md` § Closure record (`-i` + `[:=]` flags).

| Element | Testid | Provenance |
|---|---|---|
| Sidebar Help Center control | `sidebar-help-center-button` | **needs-adding** — `ResourcesButton.jsx`, BOTH returns (see below) |
| Help Center page header | `help-center-page-header` | **on-main ✓** (also on `automation/testids` ✓) |
| Intro title ("Explore Help Center") | `help-center-intro-title` | **needs-adding** — `ResourcesPage.jsx` |
| Intro description | `help-center-intro-description` | **needs-adding** — `ResourcesPage.jsx` |
| Resource card root ×5 | `help-center-card-{category}` | **needs-adding** — `ResourceCard.jsx` via new `testId` prop |
| Resource card title ×5 | `help-center-card-{category}-title` | **needs-adding** — `ResourceCard.jsx` (composed) |
| Resource card description ×5 | `help-center-card-{category}-description` | **needs-adding** — `ResourceCard.jsx` (composed) |
| Resource card icon ×5 | `help-center-card-{category}-icon` | **needs-adding** — `ResourcesPage.jsx` call site |
| Resource card links (19 live) | `help-center-tour-link-{slug}` | **on-main ✓** (runtime-composed — see caveat below) |
| Version label | `help-center-version-label` | **on-`automation/testids` only** (awaiting human promotion to `main`) — `EliteaAI/EliteaUI@bc82bc32` |
| Version info "i" icon | `help-center-version-info-icon` | **on-`automation/testids` only** (awaiting human promotion to `main`) — `EliteaAI/EliteaUI@bc82bc32` |
| *(not used by this case)* Support Bot button | `sidebar-support-assistant-button` | **on-`automation/testids` only** (awaiting human promotion to `main`) — corrects the intake note that assumed otherwise |

**Runtime-composed caveat.** `help-center-tour-link-{slug}` and every
`help-center-card-{category}*` value are built by template at render time, so a bare
substring grep for a *full* testid value cannot find them on either ref — stage 1 of the
closure-record grep sees only the literal prefix. Verify these by diffing the component
file, not by grepping the composed value (`.agents/workflow.md` § Closure record,
"Runtime-composed" bullet). Live-verified instead: all 19 link testids render, with **zero
duplicates** (`document.querySelectorAll('[data-testid^="help-center-tour-link-"]')` → 19
elements, 0 repeated values).

### `testid needed:` — the implementer's work order

All four edits are **direct attributes on existing JSX nodes** or a single new prop: no new
DOM node, no new hook, no replaced MUI built-in, no product state frozen into `useState` —
i.e. they pass `add-data-testid` § Step 5.5's zero-functional-impact greps by construction.

1. **`testid needed: sidebar-help-center-button`** —
   `src/[fsd]/widgets/sidebar-root/ui/button/ResourcesButton.jsx`.
   Add `data-testid="sidebar-help-center-button"` to the outer `<Box>` of **BOTH** `return`
   statements (each already carries `data-tour={SIDEBAR_TOUR_TARGET_IDS.resources}`) — the
   `fullWidth` branch (line ~40) and the collapsed-icon branch (line ~58). **Same value on
   both**; rationale and the declared-improvisation note are in § Automation Hints "Two
   mutually-exclusive sidebar renders". Naming: `{section}-{element}-{type}` where the
   section is the **sidebar** (the call site), matching the sibling family already on that
   surface (`sidebar-settings-button`, `sidebar-agent-hub-button`,
   `sidebar-notifications-button`, `sidebar-support-assistant-button`).

2. **`testid needed: help-center-intro-title`** and
   **`testid needed: help-center-intro-description`** —
   `src/[fsd]/pages/resources/ResourcesPage.jsx`, the two `<Typography>` nodes inside
   `<Box sx={styles.intro}>` (`variant="headingLarge"` → title,
   `variant="bodyMedium"` → description). Direct attributes.

3. **`testid needed: help-center-card-{category}` + `-title` + `-description`** —
   `src/[fsd]/pages/resources/ui/ResourceCard.jsx`. Add a `testId` prop (documented prop
   name per `.agents/testing.md` § Locator policy — **never** a `data` prefix) to the
   destructure, then:
   - root `<Box sx={styles.card}>` → `data-testid={testId}`
   - title `<Typography variant="subtitle">` → `data-testid={`${testId}-title`}`
   - description `<Typography variant="bodySmall">` → `data-testid={`${testId}-description`}`

   Wire it at the call site in `ResourcesPage.jsx`:
   `testId={`help-center-card-${config.testidCategory}`}`.
   `ResourceCard` lives in the resources page's own `ui/` folder with exactly one consumer,
   so it is **not** a shared component under the `src/components/` ·
   `src/[fsd]/shared/` rule — but the caller-supplied `testId` prop is used anyway because
   the card is parameterised per-card and the category belongs to the call site.
   In-repo precedent for the prop shape: `SidebarMenuItem`'s
   `testId={`sidebar-menu-item-${i.value}`}`.

4. **`testid needed: help-center-card-{category}-icon`** —
   `src/[fsd]/pages/resources/ResourcesPage.jsx`, on the existing `<config.Icon
   width="1.5rem" height="1.5rem" />` element:
   `data-testid={`help-center-card-${config.testidCategory}-icon`}`.
   **Do NOT touch `GradientIconWrapper`** — it is a genuinely shared component
   (`src/[fsd]/shared/ui/icon/`) and it destructures only `{children, size, sx}` with no
   rest-spread, so it would need a new prop. Unnecessary: these icons are
   `vite-plugin-svgr` `?react` components which **do** spread unknown props onto the
   rendered `<svg>`. Live proof captured this session — `ResourcesButton`'s
   `<HelpCenterIcon sx={styles.icon} />` renders as
   `<svg width="14" height="14" … sx="[object Object]">`, i.e. a prop the component never
   consumes reached the DOM node verbatim. `data-testid` will land the same way (and, being
   a valid `data-*` attribute, more cleanly).

**No blanket-adding.** Every one of the 23 values above is referenced by a locator on this
test's executed code path (Steps 1, 5, 6, 7, 8) — 5 categories × 4 (root/icon/title/
description) = 20, plus the sidebar button and the two intro nodes. Sibling elements in the
same JSX (the card `<Divider>`, the body `<Box>`, the `iconWrapper`) get **nothing** — canon
ruling #511.

### Page-object changes — `automation/pages/help_center_page.py` (extend, don't duplicate)

`HelpCenterPage` already exists with `page_header`, `version_label`, `version_info_icon`,
`version_info_tooltip`, `version_info_copy_button`, `toast_alert`, `toast_message`,
`TOUR_LINK`, and the methods `navigate()`, `resource_link()`,
`open_resource_link_in_new_tab()`, `open_version_info_tooltip()`, `copy_version_info()`.
**Reuse all of it.** Additions only:

```python
# help_center_page.py — new class-level fields/constants (dynamic testids follow the
# UPPER_CASE class-constant template pattern; inline get_by_test_id(f"…") is NOT compliant)
intro_title = LocatorDescriptor(testid="help-center-intro-title")
intro_description = LocatorDescriptor(testid="help-center-intro-description")

CARD = '[data-testid="help-center-card-{}"]'
CARD_ICON = '[data-testid="help-center-card-{}-icon"]'
CARD_TITLE = '[data-testid="help-center-card-{}-title"]'
CARD_DESCRIPTION = '[data-testid="help-center-card-{}-description"]'
CARD_ANY = '[data-testid^="help-center-card-"]'          # for the count == 5 assertion
CARD_LINK_ANY = '[data-testid^="help-center-tour-link-"]'
```

The sidebar control is app-shell chrome, not Help Center page content. It belongs on the
**sidebar** page object, not `HelpCenterPage` — `automation/pages/sidebar_header_page.py`
already owns `sidebar-toggle` and the socket indicator, so add there:

```python
help_center_button = LocatorDescriptor(testid="sidebar-help-center-button")
```

…plus a `click_help_center()` action that clicks it and waits for the `/help-center` URL.
Implementer: confirm `sidebar_header_page.py` is the right home (it is the existing sidebar
object); if its scope is narrower than expected, the alternative is a small
`SidebarPage`/`BasePage` field — either way the locator is a class-level
`LocatorDescriptor`, never built in a method body.

## Network Behavior
- `GET …/resources/config` (`useGetResourcesConfigQuery`) — supplies card titles,
  descriptions, link sets, and the version/date strings.
- `GET …/system_info` (`useGetSystemInfoQuery`) — supplies the 6 component versions (only
  the *tooltip* needs these; this case never opens the tooltip).
- Both resolve before the header renders — **no loading-state race was observed live**
  across four runs (consistent with ELITEA-2225's finding on the same surface). Waiting on
  `help-center-page-header` visible is a sufficient page-ready gate; `ResourcesPage` renders
  `<Skeleton>` placeholders while `isConfigLoading`, so asserting a card's title implicitly
  waits past the skeleton via Playwright's auto-retry.
- **No mutation.** Nothing is POSTed/PUT/DELETEd by this case.

## Known Defects Found During Exploration
**None found.** All 9 steps behaved exactly as the case describes (modulo the two
pre-tracked case-text items below), with **zero console errors** across four independent
live runs.

Pre-existing, already tracked — **do not re-file**:
- **#998** (`question`, `case-text-drift`, OPEN) — Step 6 says "four resource cards" then
  names five. Re-confirmed in source (`RESOURCE_CARD_CONFIGS` = 5 entries) and live (5
  cards rendered). The live contract is FIVE; "four" is the typo. This AFS specs five.
- **#1492** (`bug`, OPEN) — the Release Notes "latest" link target 404s
  (`docs.elitea.ai/release-notes/rn-2-0-2`). **Out of scope here**: this case only verifies
  links are *displayed*, never that a target loads. Step 7 asserts the `href` is non-empty,
  not that it resolves — so #1492 cannot turn this spec red.

Not a defect, recorded so nobody re-triages it:
- Help Center resource links hardcode an `/app` prefix from backend CMS config
  (`href="/app/chat?tour=sidebar"`), correct on deployed envs and 404-ing the main content
  area on localhost. Already triaged (`.agents/memory/qa-engineer/
  interactive_tours_feature_shared_surface_and_help_center_app_prefix.md`). Irrelevant to
  this case — Step 7 never clicks a link.

## Blocked Steps
**None.** All 9 steps were executed end-to-end against the live system.

⚠️ One **environment** (not case) blocker was hit and resolved before execution — it is an
infrastructure finding for the lead, not a product defect, and it is reported in the
analyst's return rather than filed: the EliteaUI dev server served HTTP 200 but the app
could not boot, rendering only `EnvMissingPage` ("System env missing: `VITE_BASE_URI`,
`VITE_PUBLIC_PROJECT_ID`"). See § Automation Hints "Dev-server env prerequisites".

## Automation Hints

- **Framework**: Playwright 1.61 + pytest (`automation/`). New spec file
  `automation/tests/ui/help_center/test_help_center_page_loads.py`.
  Markers: `ui`, `help_center`, `p3`, `regression` (case priority medium → `p3`; the three
  existing help-center specs use `p2`/`p3` file-level `pytestmark`, so a new file sets its
  own without the marker-stacking tension noted for ELITEA-2229).
- **Wrap every step in `with allure.step("Step N — …"):`** — mandatory
  (`.agents/testing.md` § Step reporting). One `allure.step` per AFS step; assertions live
  inside their step's block.
- **Fidelity**: no substitution of any kind is needed or permitted here. Every observable
  is read off the real rendered page, driven by real clicks, with the DEV backend producing
  the card/version data. There is **no `page.route`, no `route.fulfill`, no
  `page.evaluate`-injected state, and no API seeding** in this spec. The case does not ask
  for simulation, so a terminal substitution would be `CHANGES_REQUESTED`.

### Two mutually-exclusive sidebar renders — read before adding the testid

`ResourcesButton.jsx` has **two `return` statements**, and `SidebarBody.jsx` (lines ~292–314)
picks between them with a ternary on `onToggleAssistant`:

| Condition | Footer renders | The Help Center control |
|---|---|---|
| Support Assistant **enabled** + sidebar expanded | `sidebar-support-assistant-button` ("Support Bot") **then** `<ResourcesButton />` | icon-only, `aria-label="Help Center"`, `innerText=""` — rect x=164 y=948 52×52 |
| Support Assistant **disabled** + sidebar expanded | `<ResourcesButton fullWidth />` alone, no Support Bot anywhere | icon **+ "Help Center" label**, `aria-label=""` — rect x=16 y=960 184×32 |
| sidebar **collapsed** (either flag state) | Support Bot only (if enabled) | **absent entirely** |

Both were **observed live this session** (I toggled `VITE_ELITEA_ASSISTANT` to reach each),
and **clicking either one navigates to `/help-center`**. The gate is
`showEliteaAssistant` ← `ELITEA_ASSISTANT_ENABLED` ← the build-time env var
`VITE_ELITEA_ASSISTANT` (`SupportAssistant.jsx:22-33`, `constants.js:20`) — so **which
branch renders is an environment/build property, not a per-run UI state**, and it can
differ between localhost and CI-on-DEV.

**⚠️ DECLARED IMPROVISATION** (`.agents/role-overrides.md` § declared-improvisation
protocol — first encounter with this shape; the lead is asked to turn it into a canon card):

The canon shapes for conditional testids assume the branch choice is knowable at authoring
time. Canon ruling #277 covers `data-testid={cond ? A : B}` on a **single JSX node** with a
**per-mount data prop**, permitting either (a) only the used branch named, or (b) both named
**and** both referenced, the untested one via an absence assertion. Neither maps here:

- This is **two separate JSX nodes in two separate `return`s**, not a ternary on one node.
- "Which branch is used" is decided by a **build-time env flag**, so shape (a) is not
  determinable when the testid is written — picking one branch yields a spec that passes in
  one deployment configuration and fails in the other, for a reason unrelated to the
  behaviour under test.
- Shape (b)'s absence assertion is **structurally vacuous** here: the two branches can
  never coexist, so `to_have_count(0)` on the unrendered one is satisfied trivially in every
  run and proves nothing (exactly the failure mode `.agents/testing.md`'s `networkidle`
  entries call a "vacuous wait").

**Chosen shape, and why it is spirit-compliant:** the **same testid value on both
returns**.
- **Collision-safe by construction**, not by convention — one component, two mutually
  exclusive `return` paths on the same prop, each additionally gated on `!sideBarCollapsed`.
  Live-verified in both configurations: `[data-tour="sidebar-resources"]` count == **1**.
- **#511 satisfied**: in whatever environment the test runs, the element carrying that
  testid is the one the test clicks — the value is referenced on the executed code path.
- **Coverage metric stays honest**: the presence-based metric counts the *value*, and
  exactly one element ever bears it at runtime. It does not light up untested UI, because
  both nodes are the *same logical control* — the only control that opens the Help Center.
- **Not a state-switched testid**: the PR #581 anti-pattern is a testid whose value flips on
  the same live element as state changes. Here the value is **constant**; only which node
  mounts varies, and it varies per *build*, not per interaction.

**Proposed canon addition** (for the lead's `question` card): when one logical control is
rendered through two or more mutually-exclusive JSX branches selected by a **build-time or
deployment-time** flag, the compliant shape is the *same* testid value on every branch —
because collision is structurally impossible, exactly one branch is ever on the executed
path, and an absence assertion on the others is vacuous rather than protective.

### Sidebar-expanded precondition (verified, no action needed)

The Help Center control is gated on `!sideBarCollapsed` in **both** branches, so it does
**not render** when the sidebar is collapsed. Verified live: expanded → 1 element;
collapsed → **0** elements (Support Bot stays visible); after a reload → back to 1.

**Collapse state never persists**, so the default on every page load is expanded and the
test needs no setup: `settings.sideBarCollapsed` initialises to the hardcoded `''`
(`src/slices/settings.js:93`) and localStorage is only ever **written**, never read back —
verified by grep: no `getItem('sideBarCollapsed')` anywhere in `src/`. (Contrast `mode`,
two lines above, which *is* rehydrated via `safeGet`.)

The implementer should nonetheless let the locator's own auto-retrying visibility assertion
carry Step 1 rather than adding a defensive toggle — and if a future run ever finds the
control missing, the cause is a collapsed sidebar, not a missing testid.

### CMS-driven link data — assert structure, not frozen literals

All 19 links are backend-CMS-served (`useGetResourcesConfigQuery`), not EliteaUI source.
Titles and URLs legitimately change per release — the digest already records the Release
Notes list shifting and `tutorials-more` re-pointing. So Step 7 asserts the **invariant**
(≥1 link per card, each with a non-empty `href` and `target="_blank"`) plus the two
**case-named** tour links literally. Do **not** hardcode the other 17.

Full inventory observed 2026-09-30 (for reference only — not assertions):

| Card | Links (slug) |
|---|---|
| Documentation | `getting-started`, `how-to-guides`, `integrations`, `migration-update` |
| Release Notes | `release-2-0-2-latest`, `release-2-0-1`, `release-2-0-0`, `release-2-0-0b2` |
| Video Library | `self-service-agent-publishing`, `clearer-shared-credential-setup`, `indexing-completion-summary-report`, `notification-center-inbox-style-management`, `video-library-more` |
| Tutorials | `course-ai-based-elitea-platform`, `how-to-create-an-agent`, `how-to-create-a-pipeline`, `tutorials-more` |
| Interactive Tours | `sidebar-interactive-tour`, `chat-interactive-tour` |

The `-more` slugs stay category-prefixed (`video-library-more` / `tutorials-more`) — the
ELITEA-2223/2224 collision fix. Re-verified: **0 duplicate link testids** page-wide.

### Console-error capture

Use `automation/utils/console_errors.py` → `collect_console_errors(page)` (URL-bearing),
**not** the URL-less `page.on("console", lambda msg: …f"{msg.type}: {msg.text}")` shape that
~230 older specs still hand-roll. A clean baseline was observed (zero errors, four runs), so
no `exclude_known_defect_urls()` filter is needed. If the recurring
unrelated-background-resource noise class fires (`.agents/testing.md` § Known issues — the
socket.io 500/502/503 and project-id-less 404 flavours), the URL-bearing message is what
lets it be identified rather than guessed.

### Dev-server env prerequisites (infrastructure, for the lead)

The target initially served HTTP 200 while the **app could not boot** — React rendered only
`EnvMissingPage`: *"System env missing: `VITE_BASE_URI`, `VITE_PUBLIC_PROJECT_ID`"*
(`constants.js:34-41` gates on `null`/`undefined`). `EliteaUI/.env` held only 4 of the 12
keys in `.env.example`, and the documented master `<workspace>/.env` symlink target does not
exist in this environment. **A 200 on `/` proves the vite server is up, never that the app
booted** — assert a real app element (e.g. `[data-testid]` count > 0) instead.

Resolved locally by appending to the git-ignored, untracked `EliteaUI/.env`:
`VITE_BASE_URI=` (empty — the gate rejects only `null`/`undefined`, and `routes.js:160`
returns `''` as the router base in DEV regardless of this var's value, so it is
behaviourally inert on localhost and leaves `APP_PREFIX=""` semantics intact) and
`VITE_PUBLIC_PROJECT_ID=1` (this environment's value, independently recorded twice in
project memory/AFS). `VITE_ELITEA_ASSISTANT=true` was then added to reach the
case-text-described footer layout. Backup at `/tmp/hc/env.backup`. The durable fix is the
lead's/human's call — this is provisioning, not test design.

## Evidence

- `test-results/screenshots/ELITEA-2219-step-01-sidebar-entry.png` — sidebar control,
  assistant **disabled** (fullWidth "Help Center" label variant)
- `test-results/screenshots/ELITEA-2219-step-01-sidebar-entry-assistant-on.png` — sidebar
  footer, assistant **enabled**: "Support Bot" + the icon-only "?" control beside it (the
  case's literal Step 1)
- `test-results/screenshots/ELITEA-2219-step-03-help-center-open.png` — page after the click
- `test-results/screenshots/ELITEA-2219-step-06-resource-cards.png` — full-page, all 5 cards
- `test-results/screenshots/ELITEA-2219-step-09-version-top-right.png` — version label +
  info icon, top-right

Observed strings, verbatim:
- Step 4 header: `Help Center`
- Step 5 subtitle: `Explore Help Center`
- Step 5 description: `Guides, documentation, and release notes to support your work.`
- Step 9 version label: `Version: 2.0.3 (28-May-2026)`
