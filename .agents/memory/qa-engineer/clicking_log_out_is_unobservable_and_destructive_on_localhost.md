---
name: Clicking Log out is unobservable AND destructive on localhost
description: onLogout hard-navigates to /forward-auth/logout — swallowed by the Vite SPA fallback; user stays authenticated and the context is parked off-SPA
type: reference
aliases: [forward-auth/logout, logout redirect, login page localhost, logout teardown]
tags: [area/auth, area/settings, type/env-limitation]
created: 2026-08-24
updated: 2026-08-24
---

## What actually happens when you click Log out on localhost

`onLogout` (`Profile.jsx:20-23`, and the dead `UserButton.jsx:32`) dispatches the
redux `logout()` action and then sets
`window.location.href = window.location.origin + '/forward-auth/logout'`.
Logout is therefore **not an in-app transition** — it is a hard browser navigation to
an *infrastructure* endpoint fronted by the reverse-proxy / forward-auth layer on
deployed environments.

On `localhost:5173` that endpoint does not exist. The Vite dev server's SPA fallback
serves `index.html` for it (`curl -o /dev/null -w %{http_code} …/forward-auth/logout`
→ **200**, body = the SPA shell). Observed live 2026-08-24:

- URL becomes `http://localhost:5173/forward-auth/logout`;
- the app renders its global **"Page not found. Try Home page"** view **inside the
  still-authenticated shell** (sidebar present, title still `project_user_659`);
- navigating straight back to `/settings/profile` is **still fully logged in**
  (`Test Bot` / `testbot@elitea.ai` / id 659). `document.cookie` is empty throughout —
  localhost auth is the `VITE_DEV_TOKEN` dev path, so there is **no Keycloak session
  to end and no login page in existence locally**.

**Two consequences for automation:**

1. **Unobservable** — "redirected to the login page" / "back does not restore the
   session" cannot be produced by the system on the primary target. Faking it
   (route-stubbing the endpoint, clearing storage by hand, asserting an injected
   logged-out state) is a **terminal substitution** — route to a human instead
   (`.agents/testing.md` § Fidelity policy). The only honest local observable is
   `expect(page).to_have_url(f"{BASE_URL}/forward-auth/logout")`.
2. **Destructive** — the click parks the browser context outside the SPA routes.
   **Never click Log out in a spec sharing a context** (i.e. anything using the
   suite's `auth_state`). On a deployed env it would be worse: a real logout kills
   the Keycloak session for every following spec, so such a test needs its own
   context *and* its own credential (the `TEST_USER_B` shape from PR #1577).

Related: [[logout_lives_only_on_settings_profile_page]]
