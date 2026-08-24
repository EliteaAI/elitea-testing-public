# Test Case: Log out button is visible in the PERSONAL area of Settings (Profile page)

## Metadata
- **TMS ID**: ELITEA-2252
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: ready-for-automation (**case-text drift — asserts the LIVE contract**)
- **Implemented**: `automation/tests/ui/settings/test_settings_profile_logout_button_visible.py`
  + `automation/pages/settings_profile_page.py` (ELITEA-2252). Amendments made during
  implementation are marked *"amended at implementation"* inline below.
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: no new issue — the drift is already tracked by clarification **#1772**
  (row 4: "There is no Log out item anywhere in the Settings drawer"); this case's
  occurrence was added as a comment there rather than filed again (profile.md
  § Bug filing — a real duplicate found before filing is commented, not re-filed).
- **Cluster**: dispatched with ELITEA-2253 and ELITEA-2254 (one live session). The
  three differ in **steps**, not in data, so each has its own AFS — see
  § Relationship to the sibling cases.

---

## ⚠️ Case-text drift — read this before implementing

The case says the Log out button is **"the last item in the PERSONAL section of the
Settings sidebar"**. The live product does not render it there, and never did in the
code on `automation/testids`:

| Case text | Live product (verified 2026-08-24, localhost:5173) |
|---|---|
| Log out is the **last item of the PERSONAL section in the Settings drawer** | The drawer's PERSONAL section ends at **Notifications**. `SettingsDrawer.jsx` renders only `sections[].tabs[]` from `SETTINGS_TABS_CONFIG` — there is no Log out entry in that config and no Log out node in the drawer at all. |
| — | The Log out control lives in the **content pane of Settings → Profile** (`/settings/profile`), as the last control of the Profile card: `src/[fsd]/features/settings/ui/profile/Profile.jsx:73-80` (`<BaseBtn variant="secondary" startIcon={<LogoutIcon/>} onClick={onLogout}>Log out</BaseBtn>`). |

**Profile IS the first item of the PERSONAL section**, so the case's *intent* — "log
out is reachable in the PERSONAL area of Settings, visible without scrolling or
expanding" — is satisfiable; only its stated location is wrong. Per the
reverse-masking guard (`test-automation-workflow` § Reverse-masking guard, and
`.agents/testing.md`), this spec asserts the **live** contract and does **not**
assert the stale case text. The clarification is #1772.

The absence half of the drift is asserted too (step 2 below): a negative assertion
that no Log out control exists in the drawer. That turns "the case text is wrong" from
a comment into a test-enforced invariant — if the UI team ever moves Log out into the
drawer, this spec goes red and the case text gets revisited, instead of the drift
silently reversing.

---

## Preconditions
- User logged in (`auth_state` — on localhost login is skipped entirely via `VITE_DEV_TOKEN`).
- Selected project is the user's personal project (`Private`) — the default. The
  Profile page is not project-scoped, so this only matters for the drawer inventory
  assertion in step 2 (see § Known traps).
- **This spec must NOT click the Log out button.** Clicking it navigates the browser
  away from the SPA to `<origin>/forward-auth/logout` and leaves the context on the
  app's "Page not found" view — a teardown hazard for any spec that follows in the
  same context. The click is ELITEA-2253's subject, and that case is `blocked`
  (see its AFS).

## Test Data
### reuse-existing
None. The Profile page renders the authenticated user's own identity
(`state.user`: name / avatar / email / id / last_login). Nothing is seeded, nothing
is written, no cleanup.

---

## Test Steps

1. **Navigate to Settings → Profile.**
   - Click `BasePage.sidebar_settings_button` (`sidebar-settings-button`) — lands on
     `/settings/project-general` (the Settings entry point hardcodes the default tab,
     `SettingsButton.jsx:18`), then click the drawer's **Profile** item
     (`[data-testid="settings-nav-item-profile"]`).
   - *Alternative if `settings-nav-item-*` is still unadded when this is implemented:*
     `page.goto` the bare path `/settings/profile` via the page object's `navigate()`
     helper. Direct navigation is legitimate transit here — the case's observable is
     the button's presence on the page, not the route that got you there. Prefer the
     sidebar click when the testid exists, because it also proves Profile is a drawer
     item (which is what makes "in the PERSONAL section" true).
   - **Verify**: URL is `${BASE_URL}/settings/profile`.
   - **Verify**: the Profile content rendered — `settings-profile-page` visible.

2. **Verify the PERSONAL section of the drawer, and that Log out is NOT in it.**
   *(This is the drift assertion — see the banner above.)*
   - **Verify**: `[data-testid="settings-nav-item-profile"]` is visible and carries
     `data-active="true"` — Profile is the selected PERSONAL item.
   - **Verify**: `[data-testid="settings-nav-item-notifications"]` is visible — the
     live last item of the PERSONAL section.
   - **Verify (absence)**: `settings-drawer` contains **no** control whose accessible
     text is `Log out` —
     `expect(settings_drawer.get_by_text(re.compile(r"^\s*log\s*out\s*$", re.I))).to_have_count(0)`.
     *Locator-policy note:* this negative assertion is scoped **inside** the
     `settings-drawer` testid parent. An absence assertion cannot use a testid for a
     thing that does not exist, so a text-scoped child handle is the only shape
     available; it satisfies the `#579` discipline (real app testid on the parent,
     raw handle chained off it, declared in the method docstring). Declare it in the
     page-object method docstring exactly that way.
   - **Verify**: the drawer's menu container is **not scrollable** —
     `scrollHeight == clientHeight`. This is the drawer half of the case's
     "without additional scrolling" requirement.
     *Amended at implementation (ELITEA-2252):* the scrolling element is the inner
     `menuContainer` (the only node carrying `overflow: auto`), not the drawer root,
     so it needed its own handle — `settings-drawer-menu`, added with the rest of
     this case's testids. The read is `SettingsProfilePage.is_scrollable()`
     (`el.scrollHeight > el.clientHeight`): a browser-computed layout measurement of
     the product's own DOM, i.e. a read, not an injection.

3. **Verify the Log out button is present, labelled and enabled.**
   - **Verify**: `settings-profile-logout-button` is visible.
   - **Verify**: its text is exactly `Log out` (`to_have_text("Log out")` — note the
     space; the dead `UserButton.jsx` uses `Logout` without one, do not copy that).
   - **Verify**: it is enabled (`to_be_enabled()`).

4. **Verify it carries a recognizable log-out icon** (case step 4).
   - The icon is an inline SVG rendered by `LogoutIcon` (`@/assets/logout-icon.svg?react`)
     via MUI's `startIcon` slot, so it lands in
     `.MuiButton-startIcon > svg` inside the button.
   - **Verify**: exactly one icon element inside the button, and it is visible:
     `expect(logout_button_icon).to_have_count(1)` / `.to_be_visible()`.
     Observed live: `<svg width="16" height="16" viewBox="0 0 16 16"
     fill="currentColor" data-testid="settings-profile-logout-icon">`.
   - *Locator-policy note — **amended at implementation (ELITEA-2252)**.* The AFS
     originally specced a scoped raw `svg` handle under the #579 exception, on the
     reading that `startIcon` is a MUI slot and a testid there would need a new DOM
     node. That turned out to be avoidable: **svgr (`vite-plugin-svgr`) spreads props
     onto the generated `<svg>` root**, so the call site can name the icon directly —
     `startIcon={<LogoutIcon data-testid="settings-profile-logout-icon" />}` — with no
     wrapper node, no shared-asset edit, and no raw handle. Verified live (the
     attribute lands on the rendered `<svg>`), and it matches two existing precedents
     in EliteaUI (`catalog-skills-tab-icon`, `version-option-pin-icon`). The compliant
     testid-only shape wins over the exception whenever it is reachable.
   - Do **not** assert the SVG path data or a specific asset filename — that is
     implementation, not behaviour.

5. **Verify it is visible without any additional scrolling or expanding** (case step 5,
   and the case's Expected Final State).
   - **Verify**: `expect(logout_button).to_be_in_viewport()` — Playwright's own
     viewport check, no manual rect maths.
   - **Verify**: nothing was scrolled to make that true — the settings content pane is
     not scrollable. Assert on the pane the button lives in:
     `settings-content` `scrollHeight == clientHeight` (observed live: content pane
     **not** scrollable at both 1366×768 and 1728×861).
   - **Verify**: no expansion step was needed — the button is a direct child of the
     Profile card, not behind an accordion. Covered by the fact that steps 3-5 run
     immediately after navigation with no intervening click.
   - Live geometry for reference (do NOT hardcode coordinates in the test):
     at 1366×768 the button is at `(525, 392) 112×28`, `window.scrollY == 0`,
     `document.documentElement` not scrollable; at 1728×861 it is at `(706, 392)`.
     Only the *relations* above are asserted.

6. **Axis 2 — no unexpected console errors.**
   - **Verify**: zero console errors across the whole run.
   - Observed live: **0 console errors** on `/settings/profile` (two separate loads,
     both viewports). This path does **not** visit AI Personality or Secrets, so
     neither the **#1771** (`disableUnderline` prop leak) nor the **#1203** (Secrets
     "Maximum update depth exceeded") filter is needed — **do not add either**; a
     filter here would be masking, not noise handling.
   - Use `utils/console_errors.collect_console_errors(page)` (URL-carrying capture,
     `.agents/testing.md` § Known issues) rather than a hand-rolled listener.

---

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-24) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | **on `automation/testids` only** (not on `main`) | `BasePage.sidebar_settings_button` |
| Settings drawer root | `settings-drawer` | **added this case** — EliteaAI/EliteaUI@e1e031a1 on `automation/testids` (not on `main`) | `SettingsDrawer.jsx` root `<Box sx={styles.drawer}>`. Requested by the ELITEA-2242/2243/2244 AFS as well; whoever lands first adds it. |
| Drawer nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | **added this case** — EliteaAI/EliteaUI@e1e031a1 | the per-tab `<Box onClick=…>` in `section.tabs.map`, `SettingsDrawer.jsx`. `isActive` is already computed there — state goes on `data-active`, never in the testid value (PR #581 ruling). Class constant: `SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'`. |
| Settings content pane | `settings-content` | **added this case** — EliteaAI/EliteaUI@e1e031a1 | `<Box component="main" sx={styles.mainContent}>` in `src/[fsd]/pages/settings/index.jsx`. **Required** — a bare `main` selector matches TWO elements (app shell + settings content) and the app-shell one's text includes the drawer's, which silently green-lights content assertions. |
| Profile page container | `settings-profile-page` | **added this case** — EliteaAI/EliteaUI@e1e031a1 | `Profile.jsx` root `<Box sx={styles.container}>`. Pure attribute add. |
| **Log out button** | `settings-profile-logout-button` | **added this case** — EliteaAI/EliteaUI@e1e031a1 | `Profile.jsx:73` `<BaseBtn …>Log out</BaseBtn>`. `BaseBtn` spreads `...restProps` onto `MuiButton` (`src/[fsd]/shared/ui/button/BaseBtn.jsx:31-40`), so `data-testid="settings-profile-logout-button"` passes straight through to the rendered `<button>` — **no prop plumbing, no new DOM node, no new hook**. Zero-functional-impact check passes by construction. |
| Drawer menu container | `settings-drawer-menu` | **added this case** — EliteaAI/EliteaUI@e1e031a1 on `automation/testids` | **Added at implementation (ELITEA-2252).** `<Box sx={styles.menuContainer}>` in `SettingsDrawer.jsx` — the only node with `overflow: auto`, so it is the element whose scroll geometry answers step 2's "does the drawer need scrolling?". The drawer root would give a meaningless answer (`overflow: visible`). |
| Log out icon | `settings-profile-logout-icon` | **added this case** — EliteaAI/EliteaUI@67194ed1 on `automation/testids` | **Amended at implementation (ELITEA-2252):** a real testid, not the scoped raw `svg` handle originally specced — svgr spreads props onto the generated `<svg>` root, so `startIcon={<LogoutIcon data-testid="…" />}` needs no wrapper node. See step 4. |

**Testid additions this case needed — all LANDED (implementer, ELITEA-2252):**
`settings-drawer`, `settings-drawer-menu`, `settings-nav-item-{tabId}` (+ `data-active`),
`settings-content`, `settings-profile-page`, `settings-profile-logout-button`
(EliteaAI/EliteaUI@e1e031a1) and `settings-profile-logout-icon`
(EliteaAI/EliteaUI@67194ed1), all pushed to `automation/testids`; **none on `main`
yet — a human cherry-picks.** Every one is a pure attribute addition: the
zero-functional-impact greps produced no new DOM nodes, no new hooks, and no removals
(the only `-` lines are the same `<Box>` tags reflowed to multi-line by Prettier).

**Naming note:** `{section}-{element}-{type}` refers to the CALL SITE's section.
`Profile.jsx` is a feature file under `src/[fsd]/features/settings/ui/profile/`, not a
shared component, so a feature-scoped name is correct here.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered (setup) |
| Step 1 — Log in as any user role | authenticated, lands on expected page | `auth_state`; step 1 navigation | step 1 | covered |
| Step 2 — Navigate to Settings | target page loads | sidebar Settings click → drawer Profile click | step 1 | covered |
| Step 3 — "Log out" visible as **last item in the PERSONAL section** | condition holds | **drift** — asserted as: Log out is the last control of the **Profile page** (first PERSONAL item), *and* the drawer's PERSONAL section contains no Log out entry (ends at Notifications) | steps 2-3 | **clarification (#1772)** — live contract asserted, stale location not asserted |
| Step 4 — has a recognizable log-out icon | condition holds | exactly one visible `svg` inside the button (`LogoutIcon`, 16×16) | step 4 | covered |
| Step 5 / Expected Final State — visible without additional scrolling or expanding | condition holds | `to_be_in_viewport()` + content pane not scrollable + drawer menu not scrollable + no intervening interaction | step 5 (+ step 2 drawer half) | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| Absence of a `Log out` control inside `settings-drawer` | Turns the #1772 drift into a test-enforced invariant instead of a comment; if Log out ever moves into the drawer this goes red and the case text gets fixed. |
| Button label is exactly `Log out` (with the space) | The dead `UserButton.jsx` uses `Logout`; pinning the live string prevents a future copy-paste from silently changing the user-facing label. |
| Button is enabled | A visible-but-disabled logout would pass a bare visibility check while being useless — the case's intent is a usable control. |
| `settings-nav-item-profile` has `data-active="true"` | Proves the assertion was made on the Profile page reached through the drawer, not on some other route that happens to contain a button. |
| Zero console errors | Standard Axis-2 for this suite; also the honest baseline that lets a future regression on this page be seen. |

---

## Known traps
- **Do not click the button.** See § Preconditions. This spec is presence-only.
- **The drawer inventory is project-dependent** — `Users` / `Analytics` / `Usage` /
  `Project Context` are conditionally rendered (`index.jsx` `sections` filter). This
  spec only asserts PERSONAL items and an absence, so it is safe on any project; do
  not extend it with a PROJECT-section count assertion.
- **Two `<main>` elements** exist on a Settings route. Never use a bare `main`
  selector — use the `settings-content` testid.
- **`logoutIsLastFocusable` is NOT a safe assertion.** It read `true` live, but the
  `FieldWithCopy` rows can render copy affordances on hover, which would change the
  focusable order. Assert position semantically (the button is inside the Profile card,
  below the "Last login:" field) or simply assert presence — do not assert "last
  focusable".
- **Viewport**: the framework runs headless at 1366×768 (`conftest.py:310`) and headed
  with `no_viewport=True`. The button is in-viewport at both sizes tested; the
  assertion is `to_be_in_viewport()`, never a coordinate.

---

## Relationship to the sibling cases
- **ELITEA-2253** — the logout *effect* (redirect to login, back-navigation). `blocked`:
  its observable cannot be produced on localhost. See
  `l1_settings_profile_logout_logs_user_out_ELITEA-2253.md`.
- **ELITEA-2254** — logout *reachability from any Settings sub-page*. `blocked` for the
  same terminal reason, and its premise additionally fails live. See
  `l1_settings_logout_reachable_from_any_subpage_ELITEA-2254.md`.

This case is the only one of the three whose full observable is producible locally,
which is exactly why the three are separate specs rather than a family.
