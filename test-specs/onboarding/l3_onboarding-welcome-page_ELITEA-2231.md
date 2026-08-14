---
case_id: ELITEA-2231
title: "Onboarding — Welcome to Elitea page is displayed on first login with Sure lets go button and no project loading yet"
priority: 3
module: onboarding
status: ready-for-automation
analyst: qa-engineer
analysis_date: 2026-08-14
afs_path: test-specs/onboarding/l3_onboarding-welcome-page_ELITEA-2231.md
test_path: automation/tests/ui/onboarding/test_onboarding_welcome.py
page_object: automation/pages/onboarding_page.py
batch: onboarding-w1
---

# AFS — ELITEA-2231: Onboarding Welcome Page (First Login)

## Status: `ready-for-automation`

### Classification note — declared improvisation

**Mechanism**: The first-login Welcome state is reached by intercepting
`**/social/author/` (the `authorDetails` RTK Query endpoint,
`src/api/social.js:5,122`), fetching the real backend response via
`route.fetch()`, and re-fulfilling it with `personal_project_id: null` while
leaving all other fields byte-identical. All other fields (user name, email,
id, etc.) are real backend values.

**Why this is the right mechanism**: Option A (dedicated fresh-user credential
with reset) was rejected — `automation/routines/setup_test_users.py` targets
deployed envs only, reads `personal_project_id` from `GET /api/v2/auth/user`
(`:102-113`), and errors when the user has none (`:319`). The suite's own user
tooling assumes the post-onboarding state; a reset mechanism does not exist.
Option B (route interception) was chosen.

**Sanctioned precedent**: Response stubbing via `page.route()` /
`route.fulfill()` is already in production in `generate_entity_modal_page_base.py:100-144`
(`mock_generate_failure()` / `mock_generate_success()`) — including
`route.fulfill(status=…, content_type=…, body=…)` inside a page-object base
class with the route pattern as an `UPPER_CASE` class-level constant. 23 total
`\.route\(|fulfill` hits across `automation/**/*.py`.

**New application of sanctioned mechanism** (the declared improvisation per
`.agents/role-overrides.md` § Declared-improvisation protocol): prior uses
control timing or force an error state. This use establishes an
auth/onboarding **precondition** — a new shape. Precedent exists, but this
specific application is novel. Declaring it here so the reviewer verifies the
reasoning rather than treating it as a violation.

**Coverage boundary** (must appear verbatim in the test docstring):
> This test does NOT verify that the backend genuinely returns
> `personal_project_id: null` for a brand-new user. That is a separate
> API-level case. The assertion scope is the Welcome UI rendering when Redux
> state carries `personal_project_id: null`.

**Confirmed structure (lead ruling D2)**:
- Test file: `automation/tests/ui/onboarding/test_onboarding_welcome.py`
- Page object: `automation/pages/onboarding_page.py`
- Markers: `p3`, `onboarding` (new feature marker — register in `automation/pytest.ini`), `regression`
- Registering `onboarding` in `pytest.ini` is in scope for this case.

---

## Greenfield area

No existing coverage. No `automation/tests/ui/onboarding/` package, no
`automation/pages/onboarding_page.py`. Both paths are confirmed by the lead.
The implementer creates the package (`__init__.py`) and the page object.

---

## User Set

| Credential | Env-var key | Notes |
|---|---|---|
| Dev-token user (mocked) | `VITE_DEV_TOKEN` (in `EliteaUI/.env`) | `auth_state` bypass; user identity from real backend response; `personal_project_id` is mutated to `null` by the route mock |

No new credential is needed. The existing `auth_state` / `VITE_DEV_TOKEN` user
is reused. The user's real `name` field from the intercepted response provides
the greeting assertion value — the test must read it from the response, never
hardcode "Test Bot".

---

## Preconditions

1. **Route mock installed BEFORE the first navigation** (`page.route(...)` call
   comes before `page.goto('http://localhost:5173/')`), so the very first
   `authorDetails` call from `ProtectedRoutes.jsx`'s `getUserDetails()` is
   already intercepted.
2. **`sessionStorage.getItem('onboarding_state')` is absent or not `'true'`**
   (`Onboarding.jsx:36`). A fresh browser context (`browser.new_context()`)
   guarantees this — the test must NOT reuse a context that previously clicked
   "Sure, let's go!". Assert this at the start of the Welcome step rather than
   assume it.
3. **Navigate to the app root `/`** (`http://localhost:5173/`), not directly to
   `/onboarding`. Landing on `/onboarding` must be **observed as the product's
   own routing decision** (`IndexRoute.jsx:15` checks `!user.personal_project_id`
   and navigates to `RouteDefinitions.Onboarding`). Navigating directly to
   `/onboarding` would bypass the gate under test.
4. Wait for URL to become `**/onboarding` before asserting (the redirect is
   asynchronous — `IndexRoute` renders only after `getUserDetails()` resolves
   and Redux state updates).

**Scope boundary**: this case asserts the **pre-click** Welcome state only. The
test must NOT click "Sure, let's go!" — that action and its consequences belong
to ELITEA-2232. The test ends after asserting all Welcome-screen elements and
confirming no provisioning UI is active.

---

## Test Data Inventory

**Stable existing data (no setup/teardown needed):**
- Static UI copy: all text strings are hardcoded in `Welcome.jsx` (title, body,
  secondary text, button label).
- Logo and welcome illustration: SVG asset `logo.svg` and PNG asset
  `chat-welcome.png`, served statically.

**Test-generated / per-run data:**
- User identity from the intercepted `authorDetails` response. The test reads
  `user.name` from the mocked response to build the expected greeting string.
  Do not hardcode the name — the test user's display name is "Test Bot"
  (observed live 2026-08-14), but this may change.

**Data to clean up:**
- Route mock on `**/social/author/` — call `page.unroute(...)` in test teardown
  (or scope the mock to the test via `page.route()` which auto-expires at
  context close).
- No persistent state is created (the user never advances past the Welcome screen).
- `sessionStorage` is clean at the Welcome step; no key is set by the test.

---

## Step-by-Step Observations

Live observation performed 2026-08-14 using Playwright MCP with route mock
installed on `**/social/author/` (real response + `personal_project_id: null`).
App navigated from root; routed itself to `/onboarding`. No console errors.

Evidence screenshots:
- `test-results/screenshots/ELITEA-2231-step-01-onboarding-current-state.png`
  — baseline: current VITE_DEV_TOKEN user at `/onboarding` WITHOUT mock;
  shows OnboardingTour + sidebar (Welcome screen NOT reachable without mock)
- `test-results/screenshots/ELITEA-2231-step-02-welcome-screen-live.png`
  — WITH mock active; Welcome screen renders correctly; sidebar absent

### Step 1 — Navigate from root; product routes to `/onboarding`

**Gate** (`IndexRoute.jsx:15`):
```jsx
if (!user.personal_project_id)
  return <Navigate to={RouteDefinitions.Onboarding} replace />;
```
With route mock setting `personal_project_id: null`, Redux state has
`personal_project_id: null` after the first `getUserDetails()` call →
`IndexRoute` navigates to `/onboarding`.

**Live result**: Root navigation → URL became `http://localhost:5173/onboarding`.
Network: `GET /api/v2/social/author/` → 200 OK (mocked).

### Step 2 — Full-screen welcome page with ELITEA logo at top centre

**Layout** (`Onboarding.jsx:135-143`):
- `<Box sx={styles.page}>` — `width:100%, height:100vh` — full screen
- `<Box sx={styles.logo}><Logo /></Box>` — Elitea wordmark SVG **above** the card

**Distinction between two images**:
- The `<Logo />` SVG (`Onboarding.jsx:142`) is the Elitea brand wordmark at the
  very top of the page. It renders as an inline SVG with no `role="img"` or
  `alt` — it does NOT appear as an `img` element in the accessibility tree.
  Needs `testid needed: onboarding-page-logo` on its container
  `<Box sx={styles.logo}>`.
- The `img "Elitea"` visible in the accessibility snapshot is the
  `WelcomeImage` (`chat-welcome.png`, `Welcome.jsx:13-18`,
  `alt="Elitea"`) — a welcome illustration **inside the card**, not the
  brand logo.

**Live result**: Full-screen layout confirmed (screenshot). Logo SVG confirmed
present by source and screenshot — not in accessibility tree (no testid yet).

### Step 3 — Title "Welcome to Elitea!"

**Source** (`Welcome.jsx:19-25`):
```jsx
<Typography component="div" variant="headingMedium" sx={styles.title}>
  Welcome to Elitea!
</Typography>
```

**Live result** (accessibility snapshot): `generic [ref=e25]: Welcome to Elitea!`
— exact string confirmed.

### Step 4 — Card with greeting "Hello, [Username]!"

**Source** (`Welcome.jsx:29-34`, `Onboarding.jsx:154`):
```jsx
<Welcome name={user.name || user.email} onShowTour={handleShowTour} />
// → {`Hello, ${name}!`}
```

**Live result**: `generic [ref=e29]: Hello, Test Bot!` — "Test Bot" is the real
`user.name` from the intercepted response. The assertion must read the expected
name from the response / a configured identity, never a hardcoded literal.

### Step 5 — Card body text

**Source** (`Welcome.jsx:36-43`):
```
"We're setting up your personal workspace — it'll be ready in about 5 minutes.
While we work our magic, take a quick tour through our onboarding slides!"
```

**Live result**: `generic [ref=e30]: We're setting up your personal workspace…`
— exact match confirmed.

### Step 6 — Secondary text

**Source** (`Welcome.jsx:44-49`):
```
"Ready to explore Elitea's smart tools and tips?"
```

**Live result**: `generic [ref=e31]: Ready to explore Elitea's smart tools and tips?`
— exact match confirmed.

### Step 7 — "Sure, let's go!" button

**Source** (`Welcome.jsx:51-58`):
```jsx
<Button.BaseBtn variant="elitea" color="primary" onClick={onShowTour}>
  Sure, let's go!
</Button.BaseBtn>
```

**Live result**: `button "Sure, let's go!" [ref=e32]` — confirmed present and
clickable. NOT clicked in this test (belongs to ELITEA-2232).

### Step 8 — No sidebar navigation; no project dropdown

**Source** (`MainSidebar.jsx:42`):
```jsx
if (isOnboardingPage && !user.personal_project_id) return null;
```
When `isOnboardingPage && !user.personal_project_id`, the entire sidebar
(`<Box component="nav" aria-label="side-bar">`) is NOT rendered.

**Live result** (accessibility snapshot WITHOUT mock): sidebar present,
`navigation "side-bar"` visible, `sidebar-toggle` button present.
**WITH mock active**: accessibility snapshot shows NO `navigation` element,
NO `sidebar-toggle`, NO `project-selector-trigger` — sidebar is completely
absent from the DOM.

**Assertion targets (absence)**:
- `sidebar-toggle` testid → `to_have_count(0)` — confirms no sidebar at all
- `project-selector-trigger` testid → `to_have_count(0)` — confirms no project
  dropdown specifically (case step 8 names it explicitly)

### Step 9 — Personal/private project NOT yet loading

**Source** (`Onboarding.jsx:65-87` and `167`):
The progress footer and polling only start AFTER `handleShowTour()` is called
(button click sets `showTour = true`). At the Welcome state:
```jsx
{showTour && !thePrivateProjectIsReady && (
  <Box sx={styles.footer}>...</Box>  // only visible post-click
)}
```

**Live result**:
- No `LinearProgress` / "Configuring Personal project..." text visible in
  snapshot or screenshot
- `sessionStorage.getItem('onboarding_state') === null` (confirmed via
  `page.evaluate()`, 2026-08-14)
- No `showTour=true` state → no polling interval started within Onboarding.jsx

**Observation window**: these assertions are made immediately at the Welcome
state, before any user interaction. The 5-minute `ProtectedRoutes.jsx` timer
(`PERSONAL_SPACE_PERIOD_FOR_NEW_USER = 5 * 60 * 1000`) is outside the test's
execution window and is not assertable.

**Case text note (clarification, NOT a product defect)**: The case says
"provisioning does not begin until the user clicks 'Sure, let's go!'". Code
shows the button click only starts client-side POLLING — no "start provisioning"
API call is made. The backend provisioning trigger is not visible in UI source.
The automatable assertion is the absence of the progress UI, not a backend-state
check. The case text describes the UX intent (the user's action gates the
loading UX) accurately from a product perspective.
PENDING — clarification issue not filed (local-only run).

---

## Coverage Map

### Axis 1 — Every original case element

| # | Case element | Expected | Source | Observation | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to app root; product routes to `/onboarding` | Authenticated, lands on `/onboarding` | `IndexRoute.jsx:15` — `if (!user.personal_project_id) → Navigate(/onboarding)` | URL changed to `/onboarding` after root navigation with mock active | **covered** |
| 2 | Full-screen welcome page with ELITEA logo top-centre | Condition holds | `Onboarding.jsx:135-143` — `styles.page: height:100vh`; `<Box sx={styles.logo}><Logo /></Box>` above card | Logo SVG present (screenshot); full-screen layout confirmed; logo NOT in a11y tree (no testid yet) | **covered** (testid needed: `onboarding-page-logo`) |
| 3 | Title "Welcome to Elitea!" | Exact text | `Welcome.jsx:19-25` | `generic: Welcome to Elitea!` confirmed live | **covered** (testid needed: `onboarding-welcome-title`) |
| 4 | Card: "Hello, [Username]!" with real user name | Greeting with user's display name | `Welcome.jsx:29-34`; `Onboarding.jsx:154` — `user.name \|\| user.email` | `generic: Hello, Test Bot!` — name from real intercepted response | **covered** (testid needed: `onboarding-welcome-greeting`; assertion reads name from response) |
| 5 | Body text: workspace setup copy | Exact text | `Welcome.jsx:36-43` | `generic: We're setting up your personal workspace…` — exact match | **covered** (testid needed: `onboarding-welcome-body-text`) |
| 6 | Secondary text: "Ready to explore…?" | Exact text | `Welcome.jsx:44-49` | `generic: Ready to explore Elitea's smart tools and tips?` — exact match | **covered** (testid needed: `onboarding-welcome-secondary-text`) |
| 7 | "Sure, let's go!" button visible | Button present | `Welcome.jsx:51-58` | `button "Sure, let's go!"` confirmed live | **covered** (testid needed: `onboarding-welcome-get-started-button`; NOT clicked in this test) |
| 8 | No sidebar navigation; no project dropdown | Both absent | `MainSidebar.jsx:42` — returns `null` when `isOnboardingPage && !user.personal_project_id` | Confirmed: `sidebar-toggle` absent, `project-selector-trigger` absent in live snapshot | **covered** (absence assertions on existing testids — no new testids needed) |
| 9 | Personal/private project NOT yet loading | No progress UI; no polling started | `Onboarding.jsx:167` — footer only when `showTour && !thePrivateProjectIsReady`; `sessionStorage` empty | Progress footer absent; `sessionStorage.onboarding_state = null` confirmed | **covered** (testid needed: `onboarding-progress-footer` for absence assertion; sessionStorage check) |

### Axis 2 — Assertions beyond the case

| Observable | Reason |
|---|---|
| No console errors on Welcome page | Defensive; route mock must not introduce JS errors |
| `sessionStorage.getItem('onboarding_state') === null` | Asserts clean state rather than assuming it; the test explicitly verifies before proceeding |
| `img "Elitea"` (welcome illustration, `alt="Elitea"`) visible inside card | The WelcomeImage is part of the card layout; confirms the correct component variant is rendered |

---

## Handles Reference

PROVENANCE verification run 2026-08-14:
```bash
cd ../EliteaUI && git fetch origin  # (fetch performed above — branch states were live)
FILTER='(data-testid|testid[[:space:]]*[:=])'
for t in sidebar-toggle project-selector-trigger; do
  printf "%-42s main:%-4s testids:%s\n" "$t" \
    "$(git grep -- "$t" origin/main -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)" \
    "$(git grep -- "$t" origin/automation/testids -- src/ 2>/dev/null | grep -qiE "$FILTER" && echo YES || echo no)"
done
```
**Output**:
```
sidebar-toggle                             main:YES  testids:YES
project-selector-trigger                  main:YES  testids:YES
```
Raw hits:
```
origin/main:src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:            data-testid="sidebar-toggle"
origin/main:src/[fsd]/widgets/sidebar-root/ui/SidebarProjectSelect.jsx:        data-testid="project-selector-trigger"
```

Onboarding components (Welcome.jsx, Onboarding.jsx) — 0 testids on either
branch (confirmed by git grep with the same filter — 0 hits for `onboard` or
`welcome-page` on both `origin/main` and `origin/automation/testids`).

| Handle | Element | Source file:line | Testid | PROVENANCE |
|---|---|---|---|---|
| Page outer container | `<Box sx={styles.page}>` | `Onboarding.jsx:135` | `testid needed: onboarding-page-container` | needs-adding |
| Logo container (Elitea wordmark SVG) | `<Box sx={styles.logo}><Logo /></Box>` | `Onboarding.jsx:140-143` | `testid needed: onboarding-page-logo` | needs-adding |
| Welcome card root | `<Box sx={styles.container}>` in Welcome | `Welcome.jsx:12` | `testid needed: onboarding-welcome-card` | needs-adding |
| Welcome illustration image | `<Box component="img" alt="Elitea">` | `Welcome.jsx:13-18` | `testid needed: onboarding-welcome-illustration` | needs-adding |
| Title "Welcome to Elitea!" | `<Typography>Welcome to Elitea!</Typography>` | `Welcome.jsx:19-25` | `testid needed: onboarding-welcome-title` | needs-adding |
| Greeting "Hello, [name]!" | First `<Typography>` in card body | `Welcome.jsx:29-34` | `testid needed: onboarding-welcome-greeting` | needs-adding |
| Body text (workspace setup) | Second `<Typography>` in card body | `Welcome.jsx:36-43` | `testid needed: onboarding-welcome-body-text` | needs-adding |
| Secondary text "Ready to explore…" | Third `<Typography>` in card body | `Welcome.jsx:44-49` | `testid needed: onboarding-welcome-secondary-text` | needs-adding |
| "Sure, let's go!" button | `<Button.BaseBtn onClick={onShowTour}>` | `Welcome.jsx:51-58` | `testid needed: onboarding-welcome-get-started-button` | needs-adding |
| Sidebar toggle (absence assertion for step 8) | `data-testid="sidebar-toggle"` in `SidebarBody.jsx:221` | `src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:221` | `sidebar-toggle` | **on-main ✓** |
| Project dropdown trigger (absence assertion for step 8) | `data-testid="project-selector-trigger"` in `SidebarProjectSelect.jsx` | `src/[fsd]/widgets/sidebar-root/ui/SidebarProjectSelect.jsx:94` | `project-selector-trigger` | **on-main ✓** |
| Progress footer (absence assertion for step 9) | `<Box sx={styles.footer}>` | `Onboarding.jsx:167-177` | `testid needed: onboarding-progress-footer` | needs-adding |

**Handle count summary**: 2 `on-main ✓` (step 8 absence assertions — existing testids, no new adds needed), 0 `on-automation/testids only`, 10 `needs-adding`.

### Route mock handle (page-object class constant)

```python
# In OnboardingPage class (automation/pages/onboarding_page.py):
AUTHOR_DETAILS_ROUTE = '**/social/author/'   # matches GET /api/v2/social/author/
```

Pattern follows `generate_entity_modal_page_base.py:45` (`GENERATE_DRAFT_ROUTE`).
Method: `mock_fresh_user_state(self)` — fetch real response, set
`personal_project_id = None`, re-fulfill. Returns the real `user` dict so
the test can read `user['name']` for the greeting assertion.
Cleanup method: `clear_author_details_mock(self)` (calls `page.unroute(...)`).

---

## Options Considered

### Option A — Dedicated fresh-user credential + reset mechanism

Rejected on evidence. `automation/routines/setup_test_users.py` targets
deployed envs only (`ENV_URLS` = STAGE2/STAGE3/DEV/NEXT), reads
`personal_project_id` from `GET /api/v2/auth/user` at `:102-113`, and errors
when the user has none (`:319`). The suite's user tooling assumes the
post-onboarding state. No reset mechanism exists in the backend or suite. Would
require new backend capability — scoped to a future effort if needed.

### Option B — Playwright `page.route()` API interception (CHOSEN)

Real-response single-field mutation: intercept `**/social/author/`,
`route.fetch()` the genuine backend response, re-fulfill with
`personal_project_id: null`, all other fields byte-identical. Implemented as a
page-object `mock_*` method per the `generate_entity_modal_page_base.py` shape.
Confirmed working live (2026-08-14).

---

## Known Defects Found

None. All case elements matched the live UI exactly.

**Pending actions (local-only run)**:
- Clarification issue (case text / provisioning language): would file as a
  `question`-labelled issue on `EliteaAI/elitea-testing-public` with body:
  "Step 9 says 'provisioning does not begin until the user clicks [button]'. Code
  analysis shows the button click starts client-side polling only — no provisioning
  API call. The automatable assertion is absence of the progress UI. Case text
  clarification requested. Found while working ELITEA-2231."
  PENDING — not filed (local-only run).

---

## Cleanup

- `page.unroute('**/social/author/')` in test teardown (or context close).
- No persistent data created (user never advances past Welcome screen).
- `sessionStorage` starts clean (fresh context) and remains clean at test end.
