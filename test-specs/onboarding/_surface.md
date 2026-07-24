# Surface digest: Onboarding (first-login Welcome/Tour flow)

First written 2026-07-24 (ELITEA-2232 analysis). Onboarding is a brand-new
surface for this suite — no page object, no testids, no prior AFS existed
before this session. Read this before exploring any `module: onboarding`
case (this batch's cluster: ELITEA-2232/2233/2234/2235/2240); update it
after your own run.

## The core problem: this surface requires a "never-onboarded user"

`Welcome.jsx` (the "Sure, let's go!" card) and the tour's provisioning UI
(`Onboarding.jsx`) only render when `!user.personal_project_id`. On
localhost, **every** request carries the fixed `VITE_DEV_TOKEN`
unconditionally (`EliteaUI/src/api/eliteaApi.js:61` + 7 other call sites) —
there's no way to log in as a different/fresh account through the browser
locally, and there's no in-app signup route
(`grep -rn "signup\|register" EliteaUI/src` → 0 hits). The dev-token
account's `personal_project_id` is already set (`399`, project `Private`),
so the Welcome/first-tour state is **structurally unreachable** via the
suite's normal `auth_state` fast-path.

**Solution, confirmed live (ELITEA-2232): route-level interception of the
ONE endpoint that feeds this field.**

- `state.user.personal_project_id` is populated **exclusively** by
  `EliteaUI/src/slices/user.js`'s `authorDetails.matchFulfilled` matcher —
  i.e. by the response body of `GET /api/v2/social/author/` (confirmed via
  `git grep personal_project_id EliteaUI/src`: every OTHER hit either reads
  the field, doesn't write `state.user`, or is an unrelated `projectList`
  matcher for a DIFFERENT redux key).
- Mock **only this GET**, keep every other field from a real (unmocked)
  first call, force `personal_project_id: null` for the "not yet onboarded"
  phase, then flip it back to the real value to simulate provisioning
  completing.
- This exercises the REAL app code path (real RTK-Query matcher, real
  conditional render) — not a `page.evaluate()` state injection.

```
GET /api/v2/social/author/  →  { ..., "personal_project_id": null | <real-id> }
```

Full example route + response-body shape: see
`test-specs/onboarding/l2_sure-lets-go-triggers-provisioning-and-onboarding-tips_ELITEA-2232.md`
§ Declared Improvisation / § Automation Hints. **Recommended for all 4
sibling cases**: a shared `automation/fixtures/onboarding_fixtures.py` with a
`fresh_user_route(page)` fixture (capture real body once → mock null →
`.mark_provisioning_complete()` flips it back). Build it once, reuse across
the cluster.

## Entry point

Navigate to `${BASE_URL}/` (bare root), **not** `/onboarding` directly.
`IndexRoute.jsx` redirects `/` → `/onboarding` when `!personal_project_id`,
else → `/chat`. This matches how a real user actually arrives (post-login
landing), so use the redirect, don't shortcut to the target route.

## `sessionStorage['onboarding_state']` gotcha

`Onboarding.jsx` checks `sessionStorage.getItem('onboarding_state') === 'true'`
to decide `hasClickedGetStarted`. If a test context/storage-state is EVER
reused across onboarding tests, a stale `'true'` here makes the component
skip straight past the Welcome screen. Use a fresh browser context per test
(the suite default) rather than sharing storage state across this cluster.

## Poll timing (for wait strategies — no fixed sleeps)

- Once the tour is showing (post-click), `handleShowTour` starts a
  **5000ms `setInterval`** re-checking `GET /api/v2/social/author/` until
  `personal_project_id` is truthy. This is the fastest path to the "ready"
  state — wait on the observable UI change
  (`expect(...).to_be_visible(timeout=10000)`), not a raw sleep.
- `ProtectedRoutes.jsx` ALSO runs an independent **one-shot 5-minute
  `setTimeout`** (`PERSONAL_SPACE_PERIOD_FOR_NEW_USER = 5 * 60 * 1000`)
  polling the same endpoint, regardless of onboarding-page interaction — out
  of any reasonable test's execution window, but exists (don't be surprised
  by an extra `GET /social/author/` if a test runs long/retries).
- Neither the click nor any front-end code issues a distinct "start
  provisioning" API call — only this one read-only status-check endpoint is
  ever visible to the browser. Don't expect (or try to assert against) a
  discrete "provisioning started" network event; see ELITEA-2232's AFS
  Coverage Map for how that case's step 9 was handled given this constraint.

## Testid inventory (all NEW as of 2026-07-24 — zero pre-existing)

`grep -rn "data-testid" EliteaUI/src/[fsd]/features/onboarding/
EliteaUI/src/pages/Onboarding/` → 0 hits before ELITEA-2232. Testids
proposed/added by ELITEA-2232 (verify against `automation/testids` before
reusing — they may already exist by the time a sibling case runs):

| Testid | Element | File |
|---|---|---|
| `onboarding-welcome-card` | Welcome card container | `Welcome.jsx` |
| `onboarding-welcome-get-started-button` | "Sure, let's go!" button | `Welcome.jsx` |
| `onboarding-tour-logo` | Top-center ELITEA logo (tour view) | `Onboarding.jsx` |
| `onboarding-tour-content` | Tip title + description + Quick Action (ONE testid — markdown-rendered block, assert via `.to_contain_text()`) | `TourContent.jsx` |
| `onboarding-tour-slide-counter` | "N / 48" counter | `TourContent.jsx` |
| `onboarding-tour-progress-footer` | "Configuring Personal project..." + "about 5 min" | `Onboarding.jsx` |
| `onboarding-tour-progress-bar` | MUI `LinearProgress` | `Onboarding.jsx` |

Reused (NOT onboarding-specific, already exist elsewhere in the suite):

| Testid | Realized as | Provenance (checked 2026-07-24) |
|---|---|---|
| `sidebar-toggle` | `ChatPage.sidebar_toggle` | **on-main ✓** |
| `project-selector-trigger` | `ChatPage.project_selector_trigger` = `project-selector-trigger-combobox` | **on-automation/testids only** (not yet on `main`) |

## Related components (not yet touched by any case — FYI only)

- `WorkspaceIsReady.jsx` — "Your Elitea workspace is ready!" panel + "Jump in
  now!" button, renders once `personal_project_id` is confirmed. No case in
  this batch's onboarding cluster clicks it (ELITEA-2232 stops at "sidebar +
  project appear"); if a future case does, it has zero testids yet either —
  budget for `add-data-testid` work there too.
- `OnboardingTour.jsx`'s fullscreen dialog (expand icon, top-right) and
  `ArrowLeftIcon`/`ArrowRightIcon` slide-navigation buttons — untouched by
  ELITEA-2232 (case only asserts slide 1, doesn't navigate slides). No
  testids exist on these either.

## Zero product defects found (ELITEA-2232 session)

Live execution was clean: 0 console errors, 0 non-2xx network responses,
exact text match on every asserted string against
`onboardingTips.constants.js` source and the rendered DOM.
