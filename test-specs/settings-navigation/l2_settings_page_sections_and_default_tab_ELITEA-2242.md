# Test Case: Settings page loads and displays correct PROJECT and PERSONAL sections

## Metadata
- **TMS ID**: ELITEA-2242
- **Linked Story**: none
- **Priority**: l2 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost),
  project `Private`
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-26
- **Status**: ready-for-automation (**case-text drift — asserts the LIVE contract**)
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: no new issue — the drift is already tracked by clarification
  **EliteaAI/elitea-testing-public#1772** (rows 1-3); this occurrence is covered by
  the existing comment thread, not re-filed (`.agents/profile.md` § Bug filing).
- **Cluster**: dispatched with ELITEA-2243 and ELITEA-2244 (one live session). The
  three differ in **steps**, not in data, so each has its own AFS.

---

## ⚠️ Case-text drift — read this before implementing

The case describes a Settings drawer inventory and default tab that do not exist in
the live product. Per the reverse-masking guard, this spec asserts the **live**
contract, not the stale case text. Full comparison + root cause:
`test-specs/settings-navigation/_surface.md` § Case-text drift, and
EliteaAI/elitea-testing-public#1772.

| Case text (steps 5, 6, 7) | Live product |
|---|---|
| PROJECT = "AI Configuration, Project Params, Secrets, Users, Analytics" | PROJECT = **General, AI Providers, Project Context, Secrets, Analytics, Usage** (Users hidden on the `Private` project) |
| PERSONAL = "Personalization, Personal Tokens, Notifications, Log out" | PERSONAL = **Profile, Preferences, AI Personality, Memory, Personal Tokens, Notifications** — no Log out item |
| "AI Configuration is selected and active by default" | Default active tab is **General** (`project-general`) |
| "main content area loads the AI Configuration page" (step 8) | Main content area loads the **General** page (Project identity + AI Configurations accordion) |

---

## Preconditions
- User logged in (`auth_state` — login skipped entirely on localhost via
  `VITE_DEV_TOKEN`).
- Selected project is `Private` — the PROJECT list is project-dependent (see
  § Known traps); this spec asserts the Private-project inventory.

## Test Data
### reuse-existing
None. Read-only navigation/inventory check.

---

## Test Steps

1. **Navigate to Settings.**
   - Click `BasePage.sidebar_settings_button` (`sidebar-settings-button`).
   - **Verify**: URL is `${BASE_URL}/settings/project-general` (the sidebar button
     hardcodes this tab — see § Automation Hints).
   - **Verify**: `settings-drawer` is visible.
   - **Verify**: `settings-content` is visible and its text content is non-empty
     (`textContent.trim().length > 0`) — the "loads without error or blank state"
     assertion (case step 3).

2. **Verify the drawer shows two labelled groups.**
   - **Verify**: the drawer contains a group header with text `PROJECT`.
   - **Verify**: the drawer contains a group header with text `PERSONAL`.

3. **Verify the PROJECT section inventory (live contract, not case text).**
   - **Verify** each of these `settings-nav-item-{id}` testids is visible inside
     `settings-drawer`, in this order: `project-general` ("General"),
     `ai-providers` ("AI Providers"), `project-context` ("Project Context"),
     `secrets` ("Secrets"), `analytics` ("Analytics"), `usage` ("Usage").
   - Do **not** assert `settings-nav-item-users` — it is conditionally absent on
     the `Private` project (see § Known traps). Do not assert a literal PROJECT
     item *count* either, for the same reason.

4. **Verify the PERSONAL section inventory (live contract, not case text).**
   - **Verify** each of these `settings-nav-item-{id}` testids is visible inside
     `settings-drawer`, in this order: `profile` ("Profile"), `preferences`
     ("Preferences"), `ai-personality` ("AI Personality"), `memory` ("Memory"),
     `tokens` ("Personal Tokens"), `notifications` ("Notifications").
   - **Verify (absence)**: no control whose accessible text is `Log out` exists
     inside `settings-drawer` —
     `expect(settings_drawer.get_by_text(re.compile(r"^\s*log\s*out\s*$", re.I))).to_have_count(0)`.
     This is the drift's absence half, turning "the case text is wrong" into a
     test-enforced invariant (same pattern as ELITEA-2252's spec for the sibling
     drift on the Profile page).

5. **Verify General is selected and active by default (live contract).**
   - **Verify**: `settings-nav-item-project-general` carries `data-active="true"`.
   - **Verify**: every other visible `settings-nav-item-*` carries
     `data-active="false"`.

6. **Verify the main content area loads the General page without blank or error
   state (case step 8, corrected target).**
   - **Verify**: `settings-content` contains visible text naming the General
     section (the "General" accordion header, "AI Configurations" accordion
     header) — not merely non-empty, but recognizably the General page.
   - **Verify**: zero console errors (this route does not visit AI Personality, so
     the known #1771 warning does not fire here — assert **strict** zero, no
     filter).

---

## Expected Results
- Settings loads at `/settings/project-general` with no blank/error state.
- Drawer shows exactly two group headers, `PROJECT` and `PERSONAL`.
- PROJECT lists General, AI Providers, Project Context, Secrets, Analytics, Usage
  (Users omitted on the Private project).
- PERSONAL lists Profile, Preferences, AI Personality, Memory, Personal Tokens,
  Notifications — no Log out item anywhere in the drawer.
- General is the default active tab; its content pane is non-blank.
- Zero console errors.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Log in as admin role | authenticated, lands on expected page | `auth_state`; step 1 | step 1 | asserted |
| Step 2 — Click Settings in sidebar | control responds, next state shown | step 1 | step 1 | asserted |
| Step 3 — Settings page loads without error | condition holds | step 1 | step 1 (`settings-content` non-empty) | asserted |
| Step 4 — left panel shows two groups | condition holds | step 2 | step 2 (`PROJECT`/`PERSONAL` headers) | asserted |
| Step 5 — PROJECT: "AI Configuration, Project Params, Secrets, Users, Analytics" | action completes, expected UI state | step 3 | step 3 | **clarification (#1772)** — live inventory asserted (General, AI Providers, Project Context, Secrets, Analytics, Usage), not the stale list; Users omitted (project-dependent, not asserted either way) |
| Step 6 — PERSONAL: "Personalization, Personal Tokens, Notifications, Log out" | action completes, expected UI state | step 4 | step 4 | **clarification (#1772)** — live inventory asserted (Profile, Preferences, AI Personality, Memory, Personal Tokens, Notifications); Log out asserted **absent** from the drawer, not present |
| Step 7 — "AI Configuration" selected/active by default | condition holds | step 5 | step 5 | **clarification (#1772)** — asserted as **General** active by default, the live default tab |
| Step 8 / Expected Final State — main content loads AI Configuration page without blank/error | condition holds | step 6 | step 6 | **clarification (#1772)** — asserted as the **General** page loading non-blank, the live default page |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| Absence of `Log out` inside `settings-drawer` | Turns the #1772 drift into a test-enforced invariant — if Log out is ever added to the drawer, this spec goes red and the case text gets revisited, instead of the drift silently reversing (same pattern as ELITEA-2252's Profile-page spec). |
| Every non-General nav item carries `data-active="false"` | Confirms "General active by default" means exactly one selection, not a rendering bug where multiple items appear active. |
| Zero console errors | This route never visits AI Personality, so the baseline is genuinely clean — establishes the honest zero that lets a future regression be seen (contrast with ELITEA-2243, which legitimately expects the known #1771 warning). |

---

## Cleanup
None — read-only navigation and inventory assertions, no state mutated.

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-26) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | `automation/testids` only | `BasePage.sidebar_settings_button` (pre-existing) |
| Settings drawer root | `settings-drawer` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | `SettingsDrawer.jsx` root |
| Drawer nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | Class constant `SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'`. State on `data-active`, never in the testid value (PR #581). |
| Settings content pane | `settings-content` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | **Required** — two `<main>` elements exist on a Settings route; a bare `main` selector is ambiguous. |

No new testids needed — all four were added by a prior (not-yet-merged in this
repo) analyst/implementer session and are already live on `automation/testids`.
See `_surface.md` § Testids for the full provenance table.

## Network Behavior
- No mutating requests — this is a read-only navigation/inventory check. The
  drawer and each tab's initial content load via the same GET calls the app
  already fires on route entry; no new endpoint behavior to document for this
  case.

## Known Defects Found During Exploration
None new — see § Case-text drift above (already tracked as clarification #1772,
not a defect).

## Blocked Steps
None.

## Known traps
- **The PROJECT list is project-dependent.** `Users` is hidden on the `Private`
  project (`showUsersSection` guard); `Analytics`/`Usage` are hidden by platform
  feature flags; `Project Context`/`Service Prompts`/`Environment` differ between
  Private and Public projects. This spec asserts the Private-project inventory
  only — do not extend it into a PROJECT-list count assertion that would break
  when run against a different project type.
- **Two `<main>` elements** exist on every Settings route (app shell + settings
  content). Never use a bare `main` selector — use `settings-content`.
- **Do not conflate this case's "AI Configuration" with the actual "AI Providers"
  page.** They are different surfaces; see `test-specs/settings-ai-providers/_surface.md`
  § Page identity for the full case-text conflation this project has already hit
  once (ELITEA-2392).

## Automation Hints
- Framework: pytest + Playwright (project convention).
- Page object: none exists yet for the Settings drawer itself — recommend a new
  `SettingsDrawerPage` (or extend `SettingsProjectGeneralPage` if the implementer
  judges the drawer belongs there) exposing `nav_item(tab_id)` via the
  `SETTINGS_NAV_ITEM` class constant, and `active_nav_item()` for the `data-active`
  query.
- Wait strategy: `settings-content` becoming visible is the load signal; no
  network wait needed for this read-only case.
- `SettingsProjectGeneralPage.navigate()` (`automation/pages/settings_project_general_page.py`)
  already navigates to `/settings` and waits for `project-general-section` — reuse
  it for step 1 instead of duplicating the sidebar click + wait, if convenient.
