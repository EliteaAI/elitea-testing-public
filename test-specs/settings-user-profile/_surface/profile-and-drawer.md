## `/settings/profile` — Profile page + the ONLY Log out control (ELITEA-2252/2253/2254, 2026-08-24)

Confirmed live at both 1366×768 (the framework's headless viewport, `conftest.py:310`)
and 1728×861. Source: `src/[fsd]/features/settings/ui/profile/Profile.jsx`.

**Where logout lives — and where it does not.**
- The Log out button is a `BaseBtn` in the **content pane of `/settings/profile`**,
  the last control of the Profile card: `Profile.jsx:73-80`,
  `<BaseBtn variant="secondary" startIcon={<LogoutIcon/>} onClick={onLogout}>Log out</BaseBtn>`.
  Label is `Log out` **with a space**.
- **There is no Log out item in the Settings drawer.** PERSONAL ends at
  **Notifications** (`SettingsDrawer.jsx` renders only `SETTINGS_TABS_CONFIG` tabs).
  A whole-document text scan on `/settings/tokens` returned **0** `Log out` nodes.
- **There is no user/profile menu in the app-shell sidebar.**
  `src/[fsd]/widgets/sidebar-root/ui/button/UserButton.jsx` has a DotMenu with
  `Preferences` + `Logout`, but it is **dead code** — `grep -rn "UserButton" src/`
  finds no importer, and no `data-tour` user node renders live. Do not target it, do
  not add testids to it. This is the #1 thing that misleads a source read for
  "where is logout".
- ⇒ From any Settings sub-page, logging out costs **one drawer click** (→ Profile),
  then the button. This is why ELITEA-2254's "no extra navigation" premise fails.

**Geometry / scroll facts (asserted as relations, never as coordinates).**
- Log out is in-viewport with `window.scrollY == 0` at both viewports
  (1366×768 → `(525, 392) 112×28`; 1728×861 → `(706, 392)`).
- The settings **content pane is not scrollable** on this page
  (`scrollHeight == clientHeight`).
- The drawer **menu container is not scrollable** at 768px height
  (`617 == 617`) — so "visible without scrolling" holds for both panes.
- The icon is an inline `<svg width="16" height="16" viewBox="0 0 16 16"
  fill="currentColor">` in MUI's `startIcon` slot. Scope it off the button's testid;
  wiring a testid onto the icon itself would need a new DOM node (zero-functional-impact
  check forbids it).
- ⚠️ "Log out is the last focusable element in the pane" read `true` live but is **not**
  a safe assertion — `FieldWithCopy` rows can add copy affordances on hover.

**Clicking Log out is destructive and unobservable on localhost.**
`onLogout` dispatches redux `logout()` then sets
`window.location.href = origin + '/forward-auth/logout'` (`Profile.jsx:20-23`) — a hard
browser navigation to an **infrastructure** endpoint, not an in-app route. On localhost
that path is answered by the Vite SPA fallback (`curl … /forward-auth/logout` → **200**,
body = the SPA shell), so the app renders its global **"Page not found. Try Home page"**
view *inside the still-authenticated shell*, and a subsequent `/settings/profile` load is
**still logged in** (`Test Bot` / id 659 rendered, `document.cookie` empty throughout —
localhost auth is the `VITE_DEV_TOKEN` dev path, there is no Keycloak session and no
login page in existence locally).
⇒ **Never click Log out in a spec that shares a browser context.** It parks the context
outside the SPA routes. The only honest local observable of the click is
`expect(page).to_have_url(f"{BASE_URL}/forward-auth/logout")`.
The same `onLogout` shape is in the dead `UserButton.jsx:32`.

**Testids on this page — all `needs-adding` as of 2026-08-24**
(re-verified against `origin/main` and `origin/automation/testids` with `git fetch`):

| Testid | Where | Notes |
|---|---|---|
| `settings-profile-page` | `Profile.jsx` root `<Box sx={styles.container}>` | pure attribute add |
| `settings-profile-logout-button` | `Profile.jsx:73` `<BaseBtn>` | `BaseBtn` spreads `...restProps` onto `MuiButton` (`shared/ui/button/BaseBtn.jsx:31-40`), so `data-testid` passes straight to the `<button>` — no prop plumbing, no new node, no new hook |

Pre-existing and reusable: `personal-tokens-page-title` (**on `main` ✓ and
`automation/testids` ✓** — one of the few fully promoted handles in this area);
`sidebar-settings-button` (`automation/testids` only).
Still unadded anywhere as of this run: `settings-drawer`, `settings-content`,
`settings-nav-item-{tabId}` (requested by the ELITEA-2242/2243/2244 AFS too — whoever
lands first adds them).

**Console:** 0 errors across every load of `/settings/profile` and `/settings/tokens`
in this session, including the logout click. Neither the **#1771** (AI Personality
`disableUnderline`) nor the **#1203** (Secrets "Maximum update depth exceeded") filter
belongs on specs for this page — adding one would be masking.

**AFS files from this run:**
`l2_settings_profile_logout_button_visible_ELITEA-2252.md` (ready-for-automation),
`l1_settings_profile_logout_logs_user_out_ELITEA-2253.md` (**blocked** — env),
`l1_settings_logout_reachable_from_any_subpage_ELITEA-2254.md` (**blocked** — premise + env).
Drift consolidated onto clarification **#1772**.

## `/settings/profile` + the Settings drawer — testids added during ELITEA-2252 implementation

**Added/resolved during ELITEA-2252 implementation (2026-08-24, test-automation-engineer).**
The Settings shell had **zero** testids before this case; all seven below are new,
pure attribute additions on `automation/testids`, **none on `main` yet** (human
cherry-pick pending).

| Testid | Element | Commit |
|---|---|---|
| `settings-drawer` | `SettingsDrawer.jsx` root `<Box sx={styles.drawer}>` | EliteaAI/EliteaUI@e1e031a1 |
| `settings-drawer-menu` | the inner `<Box sx={styles.menuContainer}>` | EliteaAI/EliteaUI@e1e031a1 |
| `settings-nav-item-{tabId}` (+ `data-active`) | per-tab `<Box onClick=…>` in `section.tabs.map` | EliteaAI/EliteaUI@e1e031a1 |
| `settings-content` | `<Box component="main">` in `src/[fsd]/pages/settings/index.jsx` | EliteaAI/EliteaUI@e1e031a1 |
| `settings-profile-page` | `Profile.jsx` root container | EliteaAI/EliteaUI@e1e031a1 |
| `settings-profile-logout-button` | `Profile.jsx` `<BaseBtn>Log out</BaseBtn>` | EliteaAI/EliteaUI@e1e031a1 |
| `settings-profile-logout-icon` | the `LogoutIcon` `<svg>` in the button's `startIcon` slot | EliteaAI/EliteaUI@67194ed1 |

Page object: `automation/pages/settings_profile_page.py` (`SettingsProfilePage`) —
drawer + content-pane + Profile handles, `nav_item(tab_id)`, `open_from_sidebar()`,
`drawer_logout_controls()` (absence handle), `is_scrollable(container)`.

### Facts worth reusing

- **svgr spreads props onto the generated `<svg>` root.** `@/assets/*.svg?react`
  components (`vite-plugin-svgr` 4.5.0) accept `data-testid` at the **call site** —
  `startIcon={<LogoutIcon data-testid="…" />}` lands the attribute on the rendered
  `<svg>`. Verified live. So an inline SVG icon is **not** a #579 "testid can't be
  placed" case: name it at the call site (feature-scoped, no wrapper node, no shared
  `.svg` asset edit). Existing precedents: `catalog-skills-tab-icon`,
  `version-option-pin-icon`. Prefer this over a scoped raw `svg` handle.
- **`BaseBtn` (`src/[fsd]/shared/ui/button/BaseBtn.jsx`) spreads `...restProps` onto
  `MuiButton`** — `data-testid` passes straight through to the rendered `<button>`.
  No prop plumbing needed for any `BaseBtn` call site.
- **`data-active={isActive}` renders as `data-active="false"`, not as an absent
  attribute** — React stringifies booleans on `data-*` attributes, so
  `to_have_attribute("data-active", "true"/"false")` works on both states.
- **Two `<main>` elements exist on a `/settings/*` route** (app shell + settings
  content). Never use a bare `main` selector — use `settings-content`.
- **The Settings drawer has no Log out entry** and never did: `SettingsDrawer.jsx`
  renders only `SETTINGS_TABS_CONFIG` tabs, and PERSONAL ends at Notifications. Log
  out is the last control of the **Profile page** content pane. Clarification
  EliteaAI/elitea-testing-public#1772 row 4. ELITEA-2252 pins this as an invariant
  (absence assertion scoped inside `settings-drawer`).
- **Never click the Profile Log out button from an unrelated spec.** `onLogout` sets
  `window.location.href = origin + '/forward-auth/logout'`, leaving the context
  outside the SPA — a teardown hazard for whatever runs next.
- **Dev-server HMR lag after adding a testid**: a pytest run started ~1 min after
  pushing a new testid found 0 elements for it, while a direct probe moments later
  saw it rendered. If a brand-new testid resolves to 0, re-check the live DOM before
  suspecting the JSX — the fix is to re-run, not to change the locator.

