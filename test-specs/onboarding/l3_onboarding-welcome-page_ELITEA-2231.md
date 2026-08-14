---
case_id: ELITEA-2231
title: "Onboarding — Welcome to Elitea page is displayed on first login with Sure lets go button and no project loading yet"
priority: 3
module: onboarding
status: needs-escalation
analyst: qa-engineer
analysis_date: 2026-08-14
afs_path: test-specs/onboarding/l3_onboarding-welcome-page_ELITEA-2231.md
intended_test_path: automation/tests/ui/onboarding/test_onboarding_welcome.py  # recommendation — lead confirms
intended_page_object: automation/pages/onboarding_page.py  # recommendation — lead confirms
batch: onboarding-w1
---

# AFS — ELITEA-2231: Onboarding Welcome Page (First Login)

## Summary

**Status: `needs-escalation`**

The Welcome screen requires `user.personal_project_id = null` in Redux state, which
means the user must not yet have a personal project provisioned by the backend. The
current test setup (`VITE_DEV_TOKEN` / `auth_state` bypass) uses a user who is long
past onboarding — `personal_project_id` is set. Navigating directly to `/onboarding`
with this user renders the OnboardingTour slide deck (not the Welcome component),
and the sidebar IS visible. The first-login Welcome state is not reachable locally
without a framework-architecture decision from the lead.

**The lead must choose between the two options laid out in § Escalation Options
before this case can advance to implementation.**

---

## Greenfield area

No existing coverage. No `automation/tests/ui/onboarding/` package, no
`automation/pages/onboarding_page.py`, no prior AFS. Confirmed by lead intake.
Intended paths are **recommendations** — the lead confirms the structure.

---

## User Set

| Credential | Env-var key | Notes |
|---|---|---|
| Fresh-user (DOES NOT EXIST YET) | `ONBOARDING_USER_EMAIL` / `ONBOARDING_USER_PASSWORD` | Needed for Option A — see § Escalation Options |
| Existing dev-token user | `VITE_DEV_TOKEN` (in `EliteaUI/.env`) | Current `auth_state` user — NOT usable for this case |

---

## Preconditions

- User has authenticated for the **first time** — backend has not yet provisioned
  `personal_project_id` for this user.
- `sessionStorage.getItem('onboarding_state')` is `null` or empty (user has not
  previously clicked "Sure, let's go!" in this browser session).
- User `id` is set (authenticated via Keycloak).

---

## Test Data Inventory

**Stable existing data (no setup needed):**
- Static UI copy: "Welcome to Elitea!", "Hello, [Username]!", body/secondary text,
  "Sure, let's go!" button — all hardcoded in `Welcome.jsx`.

**Test-generated / per-run data:**
- Fresh user account with `personal_project_id = null` — either a dedicated
  credential (Option A) or an API-intercepted mock response (Option B).

**Data to clean up:**
- If Option A: the onboarding state must be reset after each test run so the user
  can go through the Welcome flow again. Reset mechanism is TBD (no known API
  endpoint observed; requires lead/backend investigation).
- If Option B (API mock): no persistent state change; mock is session-scoped.

---

## Step-by-Step Observations

All steps were analysed against source code and a live browser observation on
`http://localhost:5173/onboarding` with the `VITE_DEV_TOKEN` user (past onboarding).
The Welcome screen was NOT observed live — the evidence below is source-code-grounded.

### Step 1 — First login with new user account

**Gate mechanism** (`IndexRoute.jsx:15`):
```jsx
if (!user.personal_project_id)
  return <Navigate to={RouteDefinitions.Onboarding} replace />;
```
When `user.personal_project_id` is falsy after `getUserDetails()` API response,
React Router navigates to `/onboarding`. With the current `VITE_DEV_TOKEN` user,
`personal_project_id` IS set → redirect goes to `/chat`, not `/onboarding`.

**Evidence screenshot**: `test-results/screenshots/ELITEA-2231-step-01-onboarding-current-state.png`
— shows the app with the current user navigating to `/onboarding`: the OnboardingTour
slide deck is rendered (not Welcome), sidebar IS present. Confirms the DEV_TOKEN user
is past onboarding.

### Step 2 — Full-screen welcome page with ELITEA logo top-centre

**Source** (`Onboarding.jsx:129-148`):
```jsx
<Box sx={styles.page}>       {/* full-screen container */}
  <Box sx={styles.body}>
    <Box sx={styles.logo}>
      <Logo />                {/* SVG logo, top-centre */}
    </Box>
    <Box sx={styles.gradientBorder}>
      <Box sx={styles.mainPanel}>
        {!showTour && !user.personal_project_id && user.id && (
          <Welcome name={user.name || user.email} onShowTour={handleShowTour} />
        )}
```
The `styles.page` sets `width: 100%, height: 100vh` — full screen. Logo is rendered
above the main panel at top-centre.

### Step 3 — Title "Welcome to Elitea!"

**Source** (`Welcome.jsx:19-25`):
```jsx
<Typography component="div" variant="headingMedium" sx={styles.title}>
  Welcome to Elitea!
</Typography>
```

### Step 4 — Card with greeting "Hello, [Username]!"

**Source** (`Welcome.jsx:29-34`):
```jsx
<Typography variant="bodyMedium" component="div" sx={styles.message}>
  {`Hello, ${name}!`}
</Typography>
```
`name` prop = `user.name || user.email` (passed from `Onboarding.jsx:154`).

### Step 5 — Card body text

**Source** (`Welcome.jsx:36-43`):
```jsx
<Typography variant="bodyMedium" component="div" sx={styles.message}>
  We&apos;re setting up your personal workspace — it&apos;ll be ready in about
  5 minutes. While we work our magic, take a quick tour through our onboarding slides!
</Typography>
```
Exact text: "We're setting up your personal workspace — it'll be ready in about 5
minutes. While we work our magic, take a quick tour through our onboarding slides!"

### Step 6 — Secondary text

**Source** (`Welcome.jsx:44-49`):
```jsx
<Typography variant="bodyMedium" component="div" sx={styles.message}>
  Ready to explore Elitea&apos;s smart tools and tips?
</Typography>
```
Exact text: "Ready to explore Elitea's smart tools and tips?"

### Step 7 — "Sure, let's go!" button

**Source** (`Welcome.jsx:51-58`):
```jsx
<Button.BaseBtn
  variant="elitea"
  color="primary"
  sx={styles.button}
  onClick={onShowTour}
>
  Sure, let&apos;s go!
</Button.BaseBtn>
```
Button text: "Sure, let's go!" — calls `handleShowTour` from `Onboarding.jsx`.

### Step 8 — No sidebar navigation visible

**Source** (`MainSidebar.jsx:42`):
```jsx
if (isOnboardingPage && !user.personal_project_id) return null;
```
When on `/onboarding` AND `user.personal_project_id` is falsy, `MainSidebar` returns
`null` — sidebar is completely absent from the DOM. This is a definitive code-grounded
assertion: sidebar element (nav `aria-label="side-bar"`) will not be present.

**Live confirmation**: With the current `VITE_DEV_TOKEN` user (who has
`personal_project_id` set), the sidebar IS present at `/onboarding` — consistent with
the `MainSidebar.jsx:42` condition (falsy check fails → sidebar renders).

**Assertion shape**: `expect(locator("nav[aria-label='side-bar']")).to_have_count(0)`
using the `sidebar-nav` testid once added. This is a first-class absence assertion
per canon ruling #511-extension.

### Step 9 — Project provisioning has NOT yet started

**Source analysis** (`Onboarding.jsx:65-87`):
```jsx
const handleShowTour = useCallback(() => {
  sessionStorage.setItem(ONBOARDING_STORAGE_KEY, 'true');
  if (!user.personal_project_id) {
    progressIntervalIdRef.current = setInterval(() => { /* progress */ }, 1000);
    queryStatusIntervalIdRef.current = setInterval(async () => {
      const result = await getUserDetails().unwrap();
      if (result.personal_project_id) { /* handle ready */ }
    }, 5000);
  }
  setShowTour(true);
}, [...]);
```
The polling interval (`queryStatusIntervalIdRef`, every 5 seconds calling
`getUserDetails()`) is started ONLY when `handleShowTour` is called (user clicks
"Sure, let's go!"). Before that click, no polling interval runs within `Onboarding.jsx`.

**Background activity from `ProtectedRoutes.jsx`**: Note that `ProtectedRoutes.jsx`
has its own timer (`PERSONAL_SPACE_PERIOD_FOR_NEW_USER = 5 * 60 * 1000` = 5 minutes,
`ProtectedRoutes.jsx:157-163`) that calls `getUserDetails()` once after 5 minutes
when `!user.personal_project_id`. This runs in the background regardless of the
Welcome screen state — but it is NOT provisioning; it checks for provisioning
completion. The backend provisioning trigger is separate.

**Observable for step 9** (what is UI-assertable before the button click):
1. The linear progress bar footer is NOT visible:
   `Onboarding.jsx:167`: `{showTour && !thePrivateProjectIsReady && <Box sx={styles.footer}>...}` —
   only renders when `showTour = true`, which is only true after button click.
2. "Configuring Personal project..." text NOT visible — same condition.
3. `sessionStorage.getItem('onboarding_state')` is `null` — not yet set.

**Observation window**: These assertions can be made immediately upon page load (at the
Welcome screen step, before any interaction). The 5-minute ProtectedRoutes timer is
not observable as a UI state change during the test's execution window.

**Step 9 caveat — case text vs. code**: The case states "provisioning does not begin
until the user clicks 'Sure, let's go!'". The UI code does NOT make any "start
provisioning" API call on button click — it only begins polling `getUserDetails()` to
detect when the backend has finished provisioning. The backend provisioning trigger is
not visible in the UI source code. The automatable assertion is: no progress/polling
UI state is shown, not that the backend has not started provisioning.

---

## Coverage Map

### Axis 1 — Every original case element

| # | Case element | Expected | Disposition | Assertion notes |
|---|---|---|---|---|
| 1 | First login with new user | Authenticated, lands on onboarding page | **blocked — unreachable locally** | `IndexRoute.jsx:15` gates on `!user.personal_project_id`; current `VITE_DEV_TOKEN` user has it set |
| 2 | Full-screen welcome page, ELITEA logo top-centre | Condition holds | Ready (pending reachability) | `Onboarding.jsx:129-140` — logo SVG above main panel; `styles.page: height:100vh` |
| 3 | Title "Welcome to Elitea!" | Condition holds | Ready (pending reachability) | `Welcome.jsx:19-25` — `Typography` with exact string |
| 4 | Card: "Hello, [Username]!" | Condition holds | Ready (pending reachability) | `Welcome.jsx:29-34` — `{Hello, ${name}!}` with user.name or user.email |
| 5 | Card body text (workspace setup) | Condition holds | Ready (pending reachability) | `Welcome.jsx:36-43` — exact string verified |
| 6 | Secondary text "Ready to explore…?" | Condition holds | Ready (pending reachability) | `Welcome.jsx:44-49` — exact string verified |
| 7 | "Sure, let's go!" button | Condition holds | Ready (pending reachability) | `Welcome.jsx:51-58` — Button.BaseBtn |
| 8 | No sidebar navigation visible | Condition holds | Ready (pending reachability) | `MainSidebar.jsx:42` — returns `null` when `isOnboardingPage && !user.personal_project_id`; absence assertion on sidebar nav |
| 9 | Personal/private project NOT yet loading | Condition holds | Ready (pending reachability) | Observable: no linear progress footer (`Onboarding.jsx:167`), no polling started; see step 9 notes above |

### Axis 2 — Assertions beyond the case

| Observable | Reason |
|---|---|
| No console errors on the Welcome page | Defensive check for JS/API errors |
| `sessionStorage.getItem('onboarding_state')` is null at Welcome screen | Confirms polling/tour-start state is clean |

---

## Handles Reference

All handles are **`needs-adding`** — zero testids exist anywhere in the onboarding
feature (confirmed by `git grep` on both `origin/main` and `origin/automation/testids`).

PROVENANCE verification command (run 2026-08-14):
```bash
cd ../EliteaUI && git fetch origin  # fresh fetch performed above
git grep -iE "(data-testid|testid[[:space:]]*[:=])" origin/main -- src/ 2>/dev/null | grep -i "onboard\|welcome-page\|welcome-to-elitea" | head -20
git grep -iE "(data-testid|testid[[:space:]]*[:=])" origin/automation/testids -- src/ 2>/dev/null | grep -i "onboard\|welcome-page\|welcome-to-elitea" | head -20
```
Result on both: **0 hits** for onboarding/welcome-page testids. (Note: hits for
`welcome-message` are for the agent WelcomeMessage component — unrelated.)

| Handle | Element | Source file:line | Proposed testid | PROVENANCE |
|---|---|---|---|---|
| Onboarding page outer wrapper | `<Box sx={styles.page}>` | `Onboarding.jsx:135` | `testid needed: onboarding-page-container` | needs-adding |
| Logo image | `<Box sx={styles.logo}><Logo /></Box>` | `Onboarding.jsx:140-143` | `testid needed: onboarding-logo` | needs-adding |
| Welcome component root | `<Welcome ...>` / `<Box sx={styles.container}>` | `Welcome.jsx:12` | `testid needed: onboarding-welcome-card` | needs-adding |
| Title "Welcome to Elitea!" | `<Typography>Welcome to Elitea!</Typography>` | `Welcome.jsx:19-25` | `testid needed: onboarding-welcome-title` | needs-adding |
| Greeting text "Hello, [name]!" | First `<Typography>` in card body | `Welcome.jsx:29-34` | `testid needed: onboarding-welcome-greeting` | needs-adding |
| Body text (workspace setup) | Second `<Typography>` in card body | `Welcome.jsx:36-43` | `testid needed: onboarding-welcome-body-text` | needs-adding |
| Secondary text "Ready to explore…" | Third `<Typography>` in card body | `Welcome.jsx:44-49` | `testid needed: onboarding-welcome-secondary-text` | needs-adding |
| "Sure, let's go!" button | `<Button.BaseBtn onClick={onShowTour}>` | `Welcome.jsx:51-58` | `testid needed: onboarding-welcome-get-started-button` | needs-adding |
| Sidebar nav (absence assertion) | `<Box component="nav" aria-label="side-bar">` | `MainSidebar.jsx:44-47` | Check existing testid for sidebar nav | needs-adding (or check existing) |
| Progress footer (absence assertion) | `<Box sx={styles.footer}>` | `Onboarding.jsx:167` | `testid needed: onboarding-progress-footer` | needs-adding |

**Handle count summary: 0 on `main`, 0 on `automation/testids`, 10 `needs-adding`.**

Note on the sidebar testid: the sidebar nav element (`<Box component="nav" aria-label="side-bar">`) may already have a testid — check `automation/pages/base_page.py` or `MainSidebar.jsx` for an existing testid before adding a new one. The key assertion for step 8 is an absence assertion on whatever stable testid identifies the sidebar.

---

## Escalation Options

The lead must choose one approach before dispatching the implementer.

### Option A — Dedicated fresh-user onboarding account (Recommended)

**What it requires:**
1. A new user account on the DEV backend whose `personal_project_id` is `null` at
   the start of each test run (or whose onboarding state can be reset).
2. New env vars in `.env.test`: `ONBOARDING_USER_EMAIL`, `ONBOARDING_USER_PASSWORD`.
3. Keycloak login (not `auth_state`): test must navigate to Keycloak and log in with
   the fresh user. The existing `auth` fixture in `conftest.py` already handles
   Keycloak login (`input[name="username"]`); this test would use it instead of
   `auth_state`.
4. **Reset mechanism** (critical): After a test run, the user is past onboarding.
   Options:
   - Admin API to delete/reset `personal_project_id` for the test user (needs
     investigation — check if `/api/v2/social/author/` PATCH endpoint supports
     resetting this field, or if a Keycloak admin API can delete/recreate the user).
   - Pre-provisioned "pool" of fresh users, with a new account per run (expensive).
   - A backend fixture endpoint explicitly for QA (escalate to backend team).

**Trade-offs:**
- PROS: Tests the real first-login flow end-to-end; no mocks.
- CONS: Needs backend support for reset; adds Keycloak login overhead; test is
  stateful and brittle if reset fails.

**Owner**: Backend team + lead to add env vars and confirm reset mechanism.

### Option B — Playwright API interception (page.route())

**What it requires:**
1. Intercept the `GET /api/v2/social/author/` call (the `authorDetails` RTK Query
   endpoint, `social.js:120`).
2. Return a modified response with `personal_project_id: null` (and `id` set to a
   valid user id).
3. Navigate to `http://localhost:5173/onboarding`.
4. Redux state will see `personal_project_id: null` → `IndexRoute` redirects to
   `/onboarding` → `MainSidebar` returns `null` → `Onboarding` shows `Welcome`.
5. Assert steps 2-9. Stop before clicking "Sure, let's go!" (step 1 is mocked,
   not real first-login behavior).

**Trade-offs:**
- PROS: Self-contained; no backend changes; reset is automatic (mock is session-scoped);
  technically covers steps 2-9 accurately (the Welcome component's rendering is real).
- CONS: Step 1 (first-login navigation) is mocked; framework preference is "real
  dependencies over mocks where possible". Must document mock scope in the test.
- Playwright `page.route()` is a framework-native capability but is not used
  elsewhere in the suite (no existing precedent).

**Owner**: Lead to rule on whether API mocking is acceptable for this case.
Implement via `page.route()` in a `@pytest.fixture` scoped to the onboarding tests.

### Decision needed from the operator

Both options require a framework-architecture decision:
- Option A: New test credential type + reset strategy (backend scope)
- Option B: API mocking policy exception (existing "real deps preferred" guideline)

The case cannot proceed to automation until one option is chosen and the
prerequisite (reset mechanism OR mock policy) is in place.

---

## Known Defects Found

None — the Welcome screen could not be observed live (it requires the first-login
state). No product defects discovered during source analysis.

**Case text observation (not a defect)**:
Step 9 states "project provisioning does not begin until the user clicks 'Sure,
let's go!'". Source code analysis (`Onboarding.jsx:65-87`) shows the UI button
click only starts CLIENT-SIDE polling — it does not send a "start provisioning"
API request. The backend provisioning trigger mechanism is not visible in the UI
source. This may be case-text imprecision about the UX intent (the user's action
GATES the loading UX, even if backend provisioning is triggered at login). The
testable UI observable is: no progress bar shown before the button click. This
is NOT filed as a defect — classifying as a case-text clarification. Document
this in the AFS for the implementer.
PENDING — not filed (local-only run; would file as `question` label on
`EliteaAI/elitea-testing-public` if outward writes were enabled).

---

## Cleanup

No cleanup required — the Welcome screen cannot be reached and no test data was
created. If Option A is implemented with a real user, the test teardown must reset
the user's onboarding state (see § Escalation Options).
