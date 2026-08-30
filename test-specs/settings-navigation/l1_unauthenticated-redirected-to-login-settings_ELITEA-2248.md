# Test Case: Unauthenticated user is redirected to login when accessing Settings directly

## Metadata
- **TMS ID**: ELITEA-2248
- **Priority**: l1 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend) **plus** an out-of-band unauthenticated HTTP probe of `https://dev.elitea.ai`
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost) — and, for the
  case's actual subject, **no user at all**
- **Analyst**: qa-engineer (Sage), batch `settings-w12`, 2026-08-30
- **Status**: **blocked** — the case's observable (an unauthenticated session) **cannot exist** on the
  project's primary test target. Not a product defect: the product does exactly what the case says,
  one layer below the SPA, on environments that have an auth layer.
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: no new card. Same underlying decision as the OPEN question card
  **#1781** ("[QUESTION][ELITEA-2253/2254] Real logout cannot be produced on localhost:5173 — needs a
  scope decision"); this case's evidence was commented there rather than filed again.
- **Related blocked sibling**: `test-specs/settings-user-profile/l1_settings_profile_logout_logs_user_out_ELITEA-2253.md`

---

## Why this is blocked (executed and probed, not assumed)

The case asks for a state — *unauthenticated* — that the local target has no way to enter, because
localhost authentication is not session-based at all.

### 1. The product's real behaviour IS what the case describes — on a deployed env

An unauthenticated HTTP GET of a Settings deep link on DEV, run live 2026-08-30:

```
$ curl -s -o /dev/null -D - "https://dev.elitea.ai/app/settings/secrets"
HTTP/2 302
location: https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=eyJhbGciOiJIUzI1NiIs…
          (target_to is a JWT whose payload is {"url":"https://dev.elitea.ai/app/settings/secrets"})
set-cookie: centry_main_session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/
```

Same 302 for an API path (`/api/v1/auth/permissions/prompt_lib/1`). So the redirect-to-login is issued
by the **forward-auth / reverse-proxy layer, before the SPA is ever served** — the browser never
downloads app JS, which is also why "no Settings content is visible" is trivially true there. The SPA
has **no `/login` route of its own** (`src/routes.js`); its only auth code is the session-expiry
handler in `src/api/eliteaApi.js:24-67`, which reacts to that same infrastructure redirect by opening
a re-auth popup.

### 2. On localhost there is no session to lack

- `EliteaUI/vite.config.js:106,123,…` — the dev proxy sets `Authorization: Bearer ${VITE_DEV_TOKEN}`
  **on the proxy side** for every API path. The browser's own credentials are irrelevant.
- `src/api/eliteaApi.js:80` and `src/common/utils.jsx:331,389,462` — in `DEV` the client attaches the
  same bearer token to every request.
- Live, this session, on `/settings/project-general`: `document.cookie` is **`""`** (no cookies at all —
  there is no `centry_main_session` locally to expire or delete).

### 3. Executed: the closest honest approximation of "logged out", and it changes nothing

With the page mounted, cleared **all** browser-held state (`localStorage.clear()`,
`sessionStorage.clear()`, expired every cookie → verified `document.cookie === ""`,
`localStorage.length === 0`, `sessionStorage.length === 0`), then navigated directly to
`http://localhost:5173/settings/secrets`:

| Observation | Value |
|---|---|
| Final URL | `http://localhost:5173/settings/secrets` — **no redirect** |
| Page title | `Settings: secrets - Private` |
| `[data-testid="settings-content"]` present | **true** — the Secrets page rendered its content |
| `[data-testid^="settings-nav-item-"]` count | **12** — the full Settings drawer |
| `input[name="username"]` (the Keycloak login field the suite uses on deployed envs) | **absent** |
| `document.cookie` | `""` |

Evidence: `.playwright-mcp/page-2026-08-30T01-19-39-714Z.yml`,
`.playwright-mcp/console-2026-08-30T01-19-39-060Z.log`.

⇒ On the primary target, **an unauthenticated user does not exist**, there is **no login page to be
redirected to**, and Settings content is visible to anyone who can reach the dev server. Nothing here
is a defect — it is the deliberate localhost dev-token topology (`.agents/profile.md`,
`.agents/testing.md` § Hooks & fixtures).

### 4. Why no substitution is specced

Producing the case's observable locally would require stubbing the forward-auth redirect
(`page.route` + `route.fulfill`), forcing a "logged out" store, or asserting against a hand-authored
302 — each of which reads the case's own observable off the test's payload. That is a **terminal
substitution**, forbidden by `.agents/testing.md` § Fidelity policy; the case text asks for a real
logout, not a simulated one. Per `.agents/role-overrides.md` § Analyst slot ("convenience never
converts into `ready-for-automation`"), this AFS specifies none and routes the decision to a human.

---

## Blocked Steps

| Case step | What is needed to unblock |
|---|---|
| Step 1 — "Log out of the platform" | An environment with a real session. Locally, logout is a hard navigation to `<origin>/forward-auth/logout`, which the Vite SPA fallback answers with `index.html` (200) — the user stays authenticated (proven in ELITEA-2253's AFS, same session topology). |
| Step 2 — "Attempt to navigate directly to the Settings URL" | Executable locally, but as an **authenticated** user — which is the opposite of the precondition. |
| Step 3 — "Verify the user is redirected to the login page" | An environment fronted by forward-auth (`dev.elitea.ai` / `next.elitea.ai`). `.agents/profile.md`: deployed envs are **CI's job — the local pipeline never targets them for verification**. Scope decision, not an analyst call. |
| Step 4 / Expected Final State — "no Settings content is visible" | Same env requirement. Locally the content **is** visible and correctly so; asserting otherwise would assert a fabricated state. |

**Decision for a human (lead → comment on question card #1781):** does ELITEA-2248 get
**(a)** a CI-only spec on a deployed env (browser, unauthenticated context, assert the Keycloak login
page and the absence of `settings-content`), **(b)** a transport-level spec in `tests/api/` asserting
the 302 + `Location` contract shown above (honest, deterministic, credential-free — but it swaps the
case's surface from UI to HTTP and its environment from localhost to DEV, which per
`.agents/role-overrides.md` § declared-improvisation ceiling is a human decision, not a declaration),
or **(c)** `un-automatable` / manual?

---

## What COULD be asserted honestly — recorded for the human's decision only

**Do not implement without an explicit ruling.**

*Option (b), sketch — `tests/api/`, no browser, no session, no credentials:*

```python
resp = requests.get("https://dev.elitea.ai/app/settings/secrets", allow_redirects=False, timeout=20)
assert resp.status_code == 302
loc = resp.headers["Location"]
assert "/forward-auth/" in loc and "/login" in loc          # redirected to the login flow
assert "settings/secrets" in base64_payload_of(target_to)   # the deep link is preserved for post-login
```

Every value is produced by the system. What it does **not** prove: that a *browser* lands on a
rendered login page, and that no Settings UI is painted — i.e. the case's UI wording. It also pins the
suite to a deployed env, which the seed reserves for CI.

*Option (a), cost:* needs a browser context with **no** `auth_state` (the suite's shared storage state
must not be reused), and it must run where Keycloak is reachable — so it is a CI-only spec by
construction. It cannot go green in the local loop, i.e. it violates the project's own local
verification gate (`.agents/testing.md` § Run commands: "a test must run green locally against
`http://localhost:5173` before its PR").

---

## Preconditions (for whichever form is eventually ruled)
- **No authenticated session** — a browser context created without `auth_state`, or a plain HTTP client.
- Target environment must have the forward-auth layer (deployed only).

## Test Data
### reuse-existing
None. The case needs the *absence* of an identity, not a new one.

---

## Concrete Handles

| Element / observable | Primary handle | Provenance (verified `git fetch origin` 2026-08-30) | Notes |
|---|---|---|---|
| Settings content pane | `settings-content` | on `automation/testids` (`EliteaAI/EliteaUI@e1e031a1`), **not on `main`** | Used only for the *absence* half on a deployed env — where it would not exist anyway, since the SPA is never served |
| Settings drawer nav items | `settings-nav-item-{tabId}` | on `automation/testids` (`EliteaAI/EliteaUI@e1e031a1`), **not on `main`** | 12 rendered live on the Private project |
| Login page field (deployed only) | `input[name="username"]` (Keycloak) | pre-existing — `conftest.py` / `session_fixtures.py` use it for deployed-env login | **Not reachable on localhost** — no login page exists there |
| Unauthenticated redirect (transport) | `HTTP 302` + `Location: …/forward-auth/auth_oidc/login?target_to=…` | live-probed 2026-08-30 against `dev.elitea.ai` | The only place this case's observable actually exists |

No testid work is unblocked by this case — nothing new is needed until the scope ruling lands.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — "User is logged in" | — | `auth_state` (localhost: `VITE_DEV_TOKEN`) | — | covered (setup) — but note it **contradicts** the case's own subject, which needs a logged-*out* user |
| Step 1 — Log out of the platform | completes, produces expected UI state | executed in ELITEA-2253: locally lands on the SPA "Page not found" view, still authenticated | — | **blocked** — no session to end locally |
| Step 2 — Navigate directly to the Settings URL | completes, produces expected UI state | executed live (`/settings/secrets`, all browser state cleared) | — | **blocked** — executable, but only as an authenticated user |
| Step 3 — User is redirected to the login page | condition holds | proven to hold at the **infrastructure layer** on `dev.elitea.ai` (302 → `/forward-auth/auth_oidc/login`); does not occur locally | — | **blocked** — needs a deployed env (scope decision) |
| Step 4 / Expected Final State — no Settings content visible to the unauthenticated user | condition holds | locally the content **is** visible (12 nav items, `settings-content` present) because the request is authenticated by the dev proxy | — | **blocked** — asserting it locally would assert a fabricated state |
| Pass/Fail — "all steps complete without errors" | — | clean navigation to `/settings/secrets` produced **0 console errors** | — | covered (observation) |

Nothing is silently dropped: every element carries a `blocked` disposition mirrored in § Blocked Steps,
or is explicitly covered as setup/observation.

### Axis 2 — observables asserted beyond the case
None — the case is blocked; no spec is specified.

---

## Known Defects

None. Two things that look like defects and are not:

1. **Settings content visible without credentials on localhost** — the dev proxy injects the bearer
   token server-side by design (`vite.config.js`). An environment property, not a product bug. Do not
   file it.
2. **`Maximum update depth exceeded` at `SecretsContent.jsx:35`** — observed *only* after wiping
   `sessionStorage` (which holds `elitea_ui.project_permission` / `elitea_ui.project.id`) underneath a
   mounted Settings page. A clean navigation to the same URL produced **0 console errors** (verified
   immediately after). Self-inflicted by the exploration, therefore not filed — and a useful warning:
   "simulate logout by clearing storage" does not merely fail to reproduce the case, it destabilises
   the app.

---

## Relationship to the sibling cases

- **ELITEA-2253** (Log out button logs the user out) — `blocked` for the mirror-image reason: there is
  no session to *end*. This case is blocked because there is no session to *lack*. One root cause:
  localhost has no auth layer.
- **ELITEA-2254** (Log out reachable from any Settings subpage) — same family, covered by #1781.
- **ELITEA-2252** (Log out button visible) — the part of the family that *is* automatable locally, and
  is merged (`automation/tests/ui/settings/test_settings_profile_logout_button_visible.py`).

One ruling on #1781 should settle all of them.
