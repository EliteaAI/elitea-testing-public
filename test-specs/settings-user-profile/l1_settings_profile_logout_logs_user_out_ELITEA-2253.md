# Test Case: Log out button successfully logs the user out

## Metadata
- **TMS ID**: ELITEA-2253
- **Priority**: l1 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: **blocked** — the case's observable cannot be produced on the project's
  primary test target. Not a product defect; an environment/scope decision for a human.
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: no new bug. The drift half is covered by clarification **#1772**; the
  blocker itself is routed to the lead for a `question` card (see § Blocked Steps).
- **Cluster**: dispatched with ELITEA-2252 and ELITEA-2254 (one live session).

---

## Why this is blocked (executed, then observed — not assumed)

The case's whole subject is the *effect* of the Log out button: a redirect to the
login page, and a browser-history back that does not restore the session. Both were
executed live against `http://localhost:5173` on 2026-08-24. What actually happens:

1. `Profile.jsx:20-23` — `onLogout` dispatches the redux `logout()` action and then
   sets `window.location.href = window.location.origin + '/forward-auth/logout'`.
   Logout is therefore **not an in-app transition at all** — it is a hard browser
   navigation to an *infrastructure* endpoint fronted by the reverse proxy /
   forward-auth layer on deployed environments.
2. On localhost that endpoint **does not exist**. The Vite dev server's SPA fallback
   serves `index.html` for any unmatched path (`curl -o /dev/null -w %{http_code}
   http://localhost:5173/forward-auth/logout` → **200**, and the body is the SPA
   shell). The request never reaches Keycloak.
3. Observed result of the real click: the URL becomes
   `http://localhost:5173/forward-auth/logout`, and the app renders its global
   **"Page not found. Try Home page"** view — **inside the still-authenticated app
   shell** (sidebar present, page title still `project_user_659`).
4. Navigating back to `/settings/profile` immediately afterwards: **still fully
   authenticated** — `Test Bot` / `testbot@elitea.ai` / user id `659` rendered, the
   Log out button present again. `document.cookie` is empty throughout; localhost auth
   is the `VITE_DEV_TOKEN` dev path (`auth_state` skips login entirely on localhost),
   so there is **no session to end and no login page to be redirected to**.

So on the primary target there is no login page in existence, and the "session ended"
observable cannot be produced by the system. Fabricating it — stubbing
`/forward-auth/logout`, clearing storage by hand, or asserting against an injected
"logged out" state — would be a **terminal substitution**: the test would prove its own
payload, not the product (`.agents/testing.md` § Fidelity policy;
`.agents/role-overrides.md` § Analyst slot: *"convenience never converts into
`ready-for-automation`"*). This AFS therefore does **not** specify one.

---

## Blocked Steps

| Case step | What is needed to unblock |
|---|---|
| Step 3 — "Verify the user is redirected to the login page" | A run against an environment where `/forward-auth/logout` is served by the real auth layer, i.e. a **deployed env** (`dev.elitea.ai` / `next.elitea.ai`, Keycloak-backed). `.agents/profile.md` says deployed envs are **CI's job — the local pipeline never targets them for verification**, so this is a scope decision, not something the analyst or implementer settles. |
| Step 4 — "Verify navigating back via browser history does NOT restore the authenticated session" | Same environment requirement, **plus** session isolation: the suite's `auth_state` storage state is shared across the whole run, and a genuine logout invalidates the Keycloak session for every spec that follows. This test needs its own browser context **and** its own credential (a dedicated logout-only user, or the `TEST_USER_B` pattern PR #1577 built: `TEST_USER_B_EMAIL` / `auth_state_user_b`). Neither exists for this purpose today. |

**Decision for a human (lead → `question` card):** does this case get
(a) a CI-only spec on a deployed env with a dedicated logout user and its own context,
(b) a reduced local spec asserting only what localhost can honestly produce (below), or
(c) `un-automatable` / manual?

---

## What COULD be asserted honestly on localhost (option (b) — for the human's decision only)

Recorded so the decision is informed. **Do not implement this without an explicit
ruling** — it drops the case's Expected Final State, and per
`.agents/role-overrides.md` § declared-improvisation protocol a declaration cannot
authorise dropping or weakening a case's observable.

- Click `settings-profile-logout-button`.
- **Verify**: `expect(page).to_have_url(f"{BASE_URL}/forward-auth/logout")` — the app
  really did perform the logout navigation. This value IS produced by the system
  (`Profile.jsx:22`), so it is honest; it just is not what the case asked for.
- That is the entire honest surface. It proves the button is wired, nothing about the
  session actually ending.

Cost of doing even this in-suite: the click leaves the browser context on a
"Page not found" view outside the SPA routes, so the spec would need its own context
or a hard re-navigation in teardown. Flag that in whatever ruling comes back.

---

## Preconditions (for whichever form is eventually implemented)
- User logged in.
- **Isolated browser context** — never the shared `auth_state` session.
- A **dedicated credential** if run against a real auth layer, so no other spec loses
  its session.

## Test Data
### reuse-existing / needs-new-user
No entity data. What is missing is an *identity*: a logout-safe user. See the
`TEST_USER_B` precedent in PR #1577 and the § Suite-health pointer in
`.agents/testing.md` (the shared-single-test-user problem, `#1082`).

---

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-24) | Notes |
|---|---|---|---|
| Log out button | `settings-profile-logout-button` | **needs-adding** | `Profile.jsx:73`; `BaseBtn` spreads props to `MuiButton`, so a plain attribute add. Full rationale in ELITEA-2252's AFS. |
| Profile page container | `settings-profile-page` | **needs-adding** | `Profile.jsx` root `<Box sx={styles.container}>` |
| Post-click URL | `${BASE_URL}/forward-auth/logout` | n/a (URL assertion) | the only system-produced observable available locally |
| Login page (deployed only) | Keycloak `input[name="username"]` | pre-existing, used by `auth_state` on deployed envs (`conftest.py`) | **not reachable on localhost** — there is no login page there |

No testid work is unblocked by this case on its own; `settings-profile-logout-button`
is added by ELITEA-2252's implementation anyway.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | — | covered (setup) |
| Step 1 — Log in and navigate to Settings | authenticated, lands on expected page | reachable locally (proven by ELITEA-2252) | — | covered elsewhere |
| Step 2 — Click "Log out" in the PERSONAL section | control responds; expected next state shown | executed live; the app navigates to `<origin>/forward-auth/logout` | — | **blocked** — the "expected next state" is unobservable locally (SPA fallback → "Page not found", user still authenticated) |
| Step 3 — user is redirected to the login page | condition holds | — | — | **blocked** — no login page exists on the local target |
| Step 4 / Expected Final State — browser back does NOT restore the authenticated session | condition holds | — | — | **blocked** — the session was never ended, so back-navigation trivially restores it; asserting otherwise would require fabricating the logged-out state |

Nothing in this case is silently dropped: every element is either covered elsewhere or
carries a `blocked` disposition mirrored in § Blocked Steps.

### Axis 2 — observables asserted beyond the case
None — the case is blocked; no spec is specified.

---

## Known Defects
None. The product behaves correctly; `/forward-auth/logout` is an infrastructure
endpoint that simply is not present in the localhost dev-server topology. This is an
**environment limitation**, not a defect, and must not be filed as one.

## Relationship to the sibling cases
- **ELITEA-2252** — presence of the button. `ready-for-automation`; carries the testid work.
- **ELITEA-2254** — reachability from an arbitrary Settings sub-page. `blocked` for the
  same terminal reason (its step 3 is this case's step 3), and its premise additionally
  fails live.
