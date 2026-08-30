# Test Case: Admin role has access to all PROJECT settings sections

## Metadata
- **TMS ID**: ELITEA-2245
- **Linked Story**: none
- **Priority**: l3 (case frontmatter `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (`testbot@elitea.ai`, user id 659) — **acting as
  `admin`** on project **400 "UI Testing"** (see § The admin vantage is real)
- **Analyst**: qa-engineer (Sage), batch `settings-w12`, 2026-08-30
- **Status**: ready-for-automation (**case-text drift on the section names — asserts
  the LIVE contract**)
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: nothing new — the section-name drift is already tracked by the OPEN
  clarification **EliteaAI/elitea-testing-public#1772**; a new occurrence was
  commented there rather than re-filed (`.agents/profile.md` § Bug filing).
- **Cluster**: dispatched with ELITEA-2246 and ELITEA-2247 (one live session). The
  three differ in **steps** (admin PROJECT walk vs viewer Secrets-absence vs
  cross-role PERSONAL walk), not only in data, so each has its own AFS.
- **surface_key**: `settings-drawer-role-access`

---

## The admin vantage is real — no second identity, no substitution

Elitea roles are **PROJECT-scoped**, and the shared `${TEST_USER}` genuinely holds
different roles in different projects. Verified live 2026-08-30 via
`GET /api/v2/admin/users/prompt_lib/{project_id}` and
`GET /api/v2/auth/permissions/prompt_lib/{project_id}` (Bearer `ELITEA_API_TOKEN`):

| Project | id | `testbot@elitea.ai` role | permission count | `*secret*` permissions |
|---|---|---|---|---|
| UI Testing | **400** | **`admin`** | 360 | 8 |
| Private (personal project) | 399 | `editor` + `viewer` | 299 | 6 |
| Elitea Testing Team | 471 | `viewer` | 158 | 0 |
| Bugs & Features | 406 | `viewer` | 158 | 0 |
| Elitea Development | 25 | `viewer` | 158 | 0 |

⇒ Selecting project **400** in the sidebar project selector puts the app in a real,
product-computed **admin** state. Nothing is injected, stubbed or forced — this is
the case's "log in as a user with Admin role" satisfied honestly
(`.agents/testing.md` § Fidelity policy). **No `page.route`, no `evaluate`-injected
state, no fabricated permission payload appears anywhere in this spec.**

`elitea_project_id` = 399 and `elitea_team_project_id` = 471 are already in
`config.py`; **the admin project 400 is NOT** — the implementer adds a settings key
(e.g. `elitea_admin_project_id`, default `400`), the same shape as the two existing
ids. See § Automation Hints — *amended 2026-08-30: the `config.py` default is
sufficient and no `.env.test` entry was added.*

---

## ⚠️ Case-text drift — read this before implementing

The case's step 3 names PROJECT sections that do not all exist. Per the
reverse-masking guard this spec asserts the **live** contract, not the case text.
Tracked by clarification EliteaAI/elitea-testing-public#1772 (OPEN) — do not re-file.

| Case text (step 3) | Live product (project 400, admin, verified 2026-08-30) |
|---|---|
| "AI Configuration, Project Params, Secrets, Users, Analytics" | **General, AI Providers, Project Context, Secrets, Users, Analytics, Usage** (7 items) |
| "AI Configuration" | No such section. The AI Configurations accordion lives *inside* **General**; the model/provider settings are their own **AI Providers** section |
| "Project Params" | No such section. Nearest equivalents: **General** + **Project Context** |

**Users is present here and absent on the Private project** — it renders only when
`projectId != user.personal_project_id` (digest § Case-text drift). Project 400 is
not the personal project, so the admin walk covers 7 items, one more than the
ELITEA-2242/2243 walks on project 399.

---

## Preconditions
- User logged in (`auth_state` — login skipped entirely on localhost via
  `VITE_DEV_TOKEN`).
- Active project switched to **400 ("UI Testing")**, where the acting user is
  `admin`. **Must be restored** to `settings.elitea_project_id` (399) in a `finally`
  — the active project is app state shared with every other spec
  (`.agents/testing.md` § Teardown-guard ordering; the `#1082` pollution class).

## Test Data
### reuse-existing
None created, edited or deleted. **Read-only** walk: navigation + state reads only.
`to_be_enabled()` / `to_be_editable()` are product-state reads, not mutations — the
spec must NOT type into, toggle, or submit anything on these pages.

---

## Test Steps

1. **Enter Settings as admin.**
   - `SettingsDrawerPage.ensure_project_selected(settings.elitea_admin_project_id)`
     → 400. *(Amended 2026-08-30, implementer: `ensure_project_selected`, not
     `switch_project` — the latter settles on `wait_for_network()` + a fixed
     1 s pause, which is the `#1847` mechanism this AFS's own Automation Hints
     forbid. `ensure_project_selected` waits on the two project-scoped GETs the
     switch actually fires, and no-ops when the project is already active.)*
   - `navigate("/settings/project-general")` (or `open_via_sidebar()`).
   - **Verify**: `settings-drawer` and `settings-drawer-menu` are visible
     (drawer-health guard — without it every later absence/-content read is vacuous).
   - **Verify**: `settings-section-header-project` and
     `settings-section-header-personal` are visible.

2. **Verify the admin PROJECT inventory (live contract).**
   - **Verify**: `nav_item_ids_in_order()` starts with exactly, in this order:
     `project-general`, `ai-providers`, `project-context`, `secrets`, `users`,
     `analytics`, `usage`.
   - **Verify (the admin-distinguishing one)**: `settings-nav-item-users` **and**
     `settings-nav-item-secrets` are both visible — the two permission-gated PROJECT
     entries. On the viewer project 471 `secrets` is absent (ELITEA-2348's spec
     proves that half), so this presence is the role-driven observable, not chrome.

3. **Click each PROJECT section in drawer order and verify it loads (case steps 3+4).**
   For each of the 7 tab ids above, via `click_nav_item(tab_id)`:
   - **Verify**: URL is `/settings/{tab_id}`.
   - **Verify**: that nav item carries `data-active="true"`.
   - **Verify**: `settings-content` is visible and its trimmed text is non-empty.
   - **Verify (no access denial — case step 4)**: `settings-content` text does **not**
     match `/access denied|forbidden|403|not authorized|no permission/i`.
   - **Verify (no access denial at the transport layer — case step 4)**: no response
     with status `403` was observed while that section loaded. Capture with a
     `page.on("response")` collector filtered to `/api/v2/`; assert the collected
     4xx/5xx list for the section is empty. Observed live: **zero** 4xx/5xx across
     all 7 sections on project 400.
   - **Verify**: zero console errors for that section, captured via
     `utils.console_errors.collect_console_errors(page)` (URL-bearing form —
     `.agents/testing.md` § 404/500 flavor entries). Observed live: **zero** console
     errors across all 7 sections on project 400.

4. **Verify editable fields are interactive, not read-only (case step 5).**
   One named, permission-gated control per section that has one — asserted with
   `expect(...).to_be_enabled()` / `to_be_editable()`, never by typing:
   | Section | Assert |
   |---|---|
   | `project-general` | `project-general-edit-icon-button` **visible and enabled**; `default-modules-section` **visible** |
   | `ai-providers` | `ai-providers-section-llms-default-selector-combobox` **visible and enabled** |
   | `project-context` | both empty-state CTAs — `project-context-create-button` and `project-context-build-with-ai-button` — **enabled** (see § Known traps) |
   | `secrets` | `secrets-add-button` **enabled** AND `secrets-search-input` **editable** |
   | `users` | `users-invite-button` **enabled** AND `users-search-input` **editable** AND `user-row-edit-button` + `user-row-delete-button` are **present and enabled** (these render for `admin` only — on the viewer projects the Users page renders no row action icons at all, digest § Gotchas) |
   | `analytics` | read-only dashboard — assert content loaded only (no editable-field claim) |
   | `usage` | read-only dashboard — assert content loaded only (no editable-field claim) |
   > **Amended during ELITEA-2245 implementation (2026-08-30, implementer).**
   > The first three rows above originally named the sections' *accordion*
   > testids. Those testids sit on `BasicAccordion` **containers** (`<div>`),
   > and Playwright's `to_be_enabled()` is **vacuously true** on any non-form
   > element with no `aria-disabled` — so the original rows would have passed
   > without observing anything. Each was replaced by a real interactive
   > control inside the same section, which is a strictly stronger form of the
   > same observable ("this section's controls are interactive"):
   >
   > * `project-general` — the section's ONLY editable control is the
   >   project-icon edit `IconButton`, and it is genuinely permission-gated
   >   (`ProjectParamsHeader.jsx` renders it only when
   >   `checkPermission('models.project_context.edit')` holds; the acting user
   >   holds that permission on 400 and 399 but NOT on 471 — live-verified).
   >   It had no testid, so one was **added**: `project-general-edit-icon-button`
   >   (EliteaAI/EliteaUI@e1f40532, attribute-only). This corrects the
   >   "No new testid is required by this AFS" line below.
   >   `default-modules-section` keeps a *visible* assertion — its module
   >   switches carry no individual testids, and this AFS deliberately asserts
   >   none (unchanged).
   > * `ai-providers` — MUI renders a select trigger as a `role=combobox` node
   >   and marks it `aria-disabled` when disabled, which IS what
   >   `to_be_enabled()` reads, so the already-declared
   >   `AIProvidersPage.llms_default_selector_combobox` is a real check.
   > * `project-context` — on project 400 this section renders its **empty
   >   state**, whose entire testid inventory is the two CTAs named above.
   >   There is **no `project-context-page-title` testid in that state**
   >   (live-verified 2026-08-30), so the two CTAs are both the content anchor
   >   and the interactivity assertion.
   - Do **not** assert a global "every input is enabled" count. Live on project 400
     the Secrets page has 1 legitimately-disabled control (`secrets-pagination-prev-button`,
     first page) and Users has 2 (`users-header-edit-button` /
     `users-header-delete-button`, disabled until a row is selected). A blanket
     "0 disabled" assertion would be false-red on correct product behaviour.

5. **Restore the active project (teardown).**
   - `finally:` `switch_project(settings.elitea_project_id)` — unconditional, never
     guarded on the element under test, exceptions logged not raised (the exact
     pattern already written in `test_viewer_role_cannot_access_secrets.py`'s
     `restore_active_project`).

---

## Expected Results
- On project 400 the acting user is `admin`; the drawer offers all 7 PROJECT
  sections including the two permission-gated ones (Secrets, Users).
- Every PROJECT section loads its own route and non-empty content pane.
- No section shows an access-denied/403 state, and no `/api/v2/` request returns
  4xx/5xx while any of them loads.
- Zero console errors across the whole walk.
- Each section that owns editable controls exposes at least one that is enabled /
  editable, including the admin-only Users row Edit/Delete actions.
- The active project is restored to 399.

---

## Handles Reference (testid-only — `.agents/testing.md` § Locator policy)

PROVENANCE verified with `cd ../EliteaUI && git fetch origin` on 2026-08-30, then
the two-stage grep from `.agents/workflow.md` § Closure record.

| Element | Testid | On `main`? | On `automation/testids`? |
|---|---|---|---|
| Settings drawer root | `settings-drawer` | no | **YES** |
| Drawer menu container | `settings-drawer-menu` | no | **YES** |
| Group headers | `settings-section-header-{project\|personal}` | no | **YES** |
| Nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | no | **YES** |
| Content pane | `settings-content` | no | **YES** |
| Project selector trigger | `project-selector-trigger` (+ `-combobox`) | YES | YES |
| Project option (dynamic) | `select-option-{projectId}` | YES | YES |
| General accordion | `project-general-section` | YES | YES |
| Default modules accordion | `default-modules-section` | YES | YES |
| AI Providers LLMs section | `ai-providers-section-llms` | YES | YES |
| Secrets add | `secrets-add-button` | YES | YES |
| Secrets search | `secrets-search-input` | no | **YES** |
| Users invite | `users-invite-button` | YES | YES |
| Users search | `users-search-input` | YES | YES |
| Users row edit / delete | `user-row-edit-button` / `user-row-delete-button` | YES | YES |
| General project-icon edit (permission-gated) | `project-general-edit-icon-button` | no | **YES** — added by this case, EliteaAI/EliteaUI@e1f40532 |

**One new testid was required after all** — see the amendment note in step 4:
`project-general-edit-icon-button`, an attribute-only addition to the
already-permission-gated `IconButton` in `ProjectParamsHeader.jsx`. The
original "no new testid" claim rested on asserting the General accordion
container instead, which would have been a vacuous assertion. Two further
notes for the implementer:
- The AI-Providers per-section *selector* inputs carry runtime-**composed** testids
  (`${sectionTestId}-default-selector`, e.g.
  `ai-providers-section-llms-default-selector`) built inside the shared section
  component — a bare `git grep` of the literal string finds nothing on either
  branch even though the attribute is live in the DOM (observed 2026-08-30). If a
  spec needs one, it is a class-level template constant
  (`'[data-testid="ai-providers-section-{}-default-selector"]'`), not a
  missing testid.
- The `default-modules-section` / `midturn-injection-section` **module checkboxes**
  have **no individual testids**. This AFS deliberately does not assert an
  individual module toggle, so none is needed. If a future case needs one, that is
  `add-data-testid` work, not a rung down.

Existing page object to extend: `automation/pages/settings_drawer_page.py`
(`SettingsDrawerPage`) — already carries `nav_item()`, `click_nav_item()`,
`nav_item_ids_in_order()`, `section_header()`, `open_via_sidebar()`, and inherits
`switch_project()` from `BasePage`. Per-section controls belong on their own existing
page objects (`admin_users_page.py`, `secrets_page.py`,
`settings_project_general_page.py`) — do not re-declare them on the drawer.

---

## Automation Hints
- **New config key.** `settings.elitea_admin_project_id` (default `400`) in
  `automation/config.py`. Do not hardcode `400` in the spec.
  *Amended 2026-08-30 (implementer):* **no `.env.test` entry is needed or was
  added.** The default in `config.py` is sufficient, which is exactly how the
  two existing project-id preconditions with the same default work
  (`users_team_project_id`, `ai_providers_seeded_project_id`) — and `.env.test`
  is a symlink to the master secrets file outside this repo, so a key that
  needs no secret does not belong there. The key is deliberately DISTINCT from
  those two despite sharing a value today, for the reason their own comments
  already state about each other.
- Markers: `ui`, `admin`, `p3`, `regression`.
- Every step wrapped in `with allure.step("Step N — …")`.
- Waits: `click_nav_item()` already waits on the product's own `data-active="true"`
  signal — no sleeps, and do **not** add a `wait_for_network()` (persistent
  `/socket.io/` polling makes `networkidle` a race — issue #1847,
  `.agents/testing.md`).
- Console capture: `utils.console_errors.collect_console_errors(page)` (the
  URL-bearing collector), asserted **strict zero** — this walk never visits
  `ai-personality` (#1771) and never visits Secrets on a project without the
  permission (#1773/#1203), so no filter is warranted.

## Known traps
- **Restore the project or poison the suite.** Leaving the session on project 400
  changes what every later spec sees (Users section present, different secrets,
  different agents). Teardown is not optional and its flag/finally ordering follows
  `.agents/testing.md` § Teardown-guard ordering.
- **Project Context on project 400 was empty** ("Still no Project Context") at
  analysis time — assert the section renders and its CTA is enabled, never a
  particular body text.
- Do not assert literal *counts* of controls; assert named ones.
- Do not visit `/settings/secrets` on a viewer project inside this spec — that is
  #1773 + #1203 territory and belongs to ELITEA-2348's spec, not here.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — user is logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Log in as a user with Admin role | authenticated, lands on expected page | step 1 (switch to project 400, where the user's role IS `admin`, verified live via the permissions/users APIs) | step 1 | asserted |
| Step 2 — Navigate to Settings | target page loads | step 1 | step 1 | asserted |
| Step 3 — Click each PROJECT section: AI Configuration, Project Params, Secrets, Users, Analytics | control responds, next state shown | steps 2+3 — **live section set** (General, AI Providers, Project Context, Secrets, Users, Analytics, Usage); "AI Configuration"/"Project Params" do not exist | steps 2, 3 | asserted against the live contract (**case-text drift**, #1772) |
| Step 4 — each section loads without "Access Denied" or 403 | condition holds | step 3 — text-level denial regex **and** transport-level "no 4xx/5xx" per section | step 3 | asserted |
| Step 5 — editable fields are interactive (not read-only) | condition holds | step 4 — one named enabled/editable control per section that owns one, incl. the admin-only Users row actions | step 4 | asserted |
| Expected final state — editable fields interactive | — | step 4 | step 4 | asserted |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why (grounded) |
|---|---|
| Drawer-health guard (`settings-drawer-menu` visible, >1 nav item) before any inventory read | Without it, a failed drawer render makes every presence/absence read vacuous — the pattern already codified in `test_viewer_role_cannot_access_secrets.py` |
| Nav item ORDER, not just presence | The drawer order is `SETTINGS_TABS_CONFIG`'s; an order regression is invisible to a set-membership assert and the digest already records the expected order |
| `data-active="true"` on the clicked item | The product's own selection signal — it is what `click_nav_item()` waits on, so asserting it costs nothing and catches a click that navigated without selecting |
| Zero console errors per section | `.agents/testing.md` — silent console errors are the ones that ship; measured **zero** on this walk, so a strict assert is honest here |
| Users row Edit/Delete present + enabled | The single strongest *admin-specific* observable on this surface: the digest records these icons are permission-gated **out entirely** on projects where the user is `viewer`. Turns "admin has access" from a chrome check into a role-driven one |
| Active-project restore in `finally` | `#1082` shared-state pollution class — a green spec that moves the project selection damages every later spec |

## Blocked Steps
None.

## Known Defects (observed, not caused by this case)
- None on project 400. All 7 sections loaded clean: zero console errors, zero
  4xx/5xx (verified live 2026-08-30).
