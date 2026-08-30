---
name: Localhost has no unauthenticated state (Elitea dev topology)
description: Any "logged out / unauthenticated user" case is unproducible on localhost:5173 — the Vite proxy injects the dev token server-side
type: project
aliases: [unauthenticated, logged out, forward-auth, login redirect, VITE_DEV_TOKEN, no login page]
tags: [area/auth, type/environment-limit]
created: 2026-08-30
updated: 2026-08-30
---

## The fact

On `http://localhost:5173` there is **no session and no login page**, so no case whose subject
is an unauthenticated or logged-out user can be executed there.

- `EliteaUI/vite.config.js:106,123,…` — the dev proxy sets `Authorization: Bearer ${VITE_DEV_TOKEN}`
  **on the proxy side**, so the browser's own credentials are irrelevant. `src/api/eliteaApi.js:80`
  and `src/common/utils.jsx:331,389,462` attach the same token client-side in `DEV`.
- `document.cookie` is `""` locally — no `centry_main_session` exists to expire.
- The SPA has **no `/login` route** (`src/routes.js`); its only auth code is the session-expiry
  handler in `src/api/eliteaApi.js:24-67`, which reacts to an *infrastructure* redirect by opening
  a re-auth popup.
- Verified live 2026-08-30 (ELITEA-2248): cleared localStorage + sessionStorage + all cookies, then
  navigated to `/settings/secrets` → no redirect, `settings-content` present, 12 nav items,
  no `input[name="username"]`.

## Where the behaviour really lives

```
curl -s -o /dev/null -D - "https://dev.elitea.ai/app/settings/secrets"
→ 302, location: https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=<JWT of original URL>
```

forward-auth redirects **before the SPA is served**. Same 302 for API paths.

## What to do with such a case

`blocked`, routed to question card **#1781** (OPEN — covers ELITEA-2253/2254/2248). Never simulate
the logged-out state (stubbed 302, cleared storage, injected store): terminal substitution.

⚠️ Clearing `sessionStorage` under a mounted Settings page throws React `Maximum update depth
exceeded` at `SecretsContent.jsx:35`. A clean navigation is 0 console errors — self-inflicted, not
a defect.

Related: [[settings_navigation_surface]]
