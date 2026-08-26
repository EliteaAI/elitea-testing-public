# Test Case: Log out is accessible from any Settings sub-page without extra navigation

## Metadata
- **TMS ID**: ELITEA-2254
- **Priority**: l1 (case priority `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: **blocked** — two independent walls: (a) the case's premise is false
  against the live product, and (b) its Expected Final State is the same
  environment-blocked observable as ELITEA-2253.
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: no new issue — the drift is already tracked by clarification **#1772**
  (row 4); this case's occurrence was added as a comment there rather than re-filed.
- **Cluster**: dispatched with ELITEA-2252 and ELITEA-2253 (one live session).

---

## Wall 1 — the premise is false live (case-text drift, verified)

The case asserts that from `Settings → Personal Tokens`, **without clicking any other
sidebar item**, a "Log out" control is visible **in the sidebar**.

Executed live 2026-08-24 on `/settings/tokens` (framework viewport 1366×768 and
1728×861):

- The Settings drawer renders exactly: `Settings` / **PROJECT** — General, AI Providers,
  Project Context, Secrets, Analytics, Usage / **PERSONAL** — Profile, Preferences,
  AI Personality, Memory, Personal Tokens, Notifications. **No Log out entry.**
- A whole-document scan for any element whose trimmed text is `Log out` returned
  **0 matches** on that page. It is not merely missing from the drawer — there is no
  logout control **anywhere** on a Settings sub-page other than Profile.
- The app-shell left sidebar has **no user/profile menu**. `UserButton.jsx`
  (`src/[fsd]/widgets/sidebar-root/ui/button/UserButton.jsx`) does contain a DotMenu
  with a `Logout` item — but it is **dead code**: `grep -rn "UserButton" src/` finds no
  importer anywhere, and live there is no `data-tour="…user…"` node in the rendered
  sidebar (the 17 sidebar tour targets present do not include one). So that menu is not
  an alternative entry point.
- **The only Log out control in the entire application is the button on the content
  pane of `Settings → Profile`** (`Profile.jsx:73`).

Consequence: logging out from `Settings → Personal Tokens` **requires one navigation** —
clicking the drawer's **Profile** item. The case's "without extra navigation" premise
does not hold. Interaction-discovery ladder was exhausted before concluding
(`.agents/role-overrides.md`): no hidden/collapsed control, no hover affordance, no
overflow menu — and the decisive step, reading the source, states the intended design
as fact.

This is **case-text drift, not a product defect** — placing Log out on the Profile page
is a deliberate design (the drawer config has no logout tab, and the old user-menu
logout was removed, leaving `UserButton.jsx` orphaned). Filing it as a `bug` would
create false red. Clarification #1772 already covers this exact divergence.

## Wall 2 — the Expected Final State is environment-blocked

Case step 3 / Expected Final State is *"Click Log out and verify the user is redirected
to the login page"* — byte-for-byte the observable ELITEA-2253 is blocked on. On
localhost the click navigates to `<origin>/forward-auth/logout`, which the Vite dev
server answers with the SPA shell (HTTP 200) → the app renders "Page not found" while
the user stays authenticated. There is no login page on the local target at all. Full
evidence in `l1_settings_profile_logout_logs_user_out_ELITEA-2253.md` § Why this is
blocked.

---

## Blocked Steps

| Case step | Wall | What is needed to unblock |
|---|---|---|
| Step 2 — "Without clicking any other sidebar item, verify Log out is visible in the sidebar" | 1 (premise false) | A **TMS case-text decision by a human**: either amend the case to the live UX (logout is one drawer click away from any sub-page, via Profile) or accept that the described behaviour does not exist. Re-writing the assertion myself would change *what is being verified*, which the declared-improvisation protocol explicitly does not authorise (`.agents/role-overrides.md`, ceiling limit 1). |
| Step 3 / Expected Final State — "Click Log out and verify redirect to the login page" | 2 (environment) | Same unblock as ELITEA-2253: a deployed, Keycloak-backed environment **plus** an isolated context and a dedicated logout-safe credential. |

**Decision for a human (lead → `question` card):** amend the case text to the live
reachability contract and re-scope it as a local, click-free spec (option (b) below),
or route it to CI-on-deployed together with ELITEA-2253, or mark it manual.

---

## What COULD be asserted honestly on localhost (option (b) — for the human's decision only)

Recorded so the ruling is informed. **Do not implement without an explicit ruling** —
it replaces the case's stated observable with a different one.

An intent-preserving, fully honest local spec would be: *"from an arbitrary Settings
sub-page, the Log out control is at most one drawer click away, with no navigation
outside Settings."*

1. Navigate to `Settings → Personal Tokens` (`/settings/tokens`).
   - **Verify**: `personal-tokens-page-title` visible (a real sub-page, not the default tab)
     and `[data-testid="settings-nav-item-tokens"]` has `data-active="true"`.
2. **Verify (absence)**: no `Log out` control exists on this sub-page —
   `expect(page.get_by_text(re.compile(r"^\s*log\s*out\s*$", re.I))).to_have_count(0)`.
   This is the drift, test-enforced: if logout is ever added to the drawer or shell,
   the spec goes red and the case text gets revisited.
3. **Verify**: the drawer offers `settings-nav-item-profile` **without any prior
   interaction** — visible immediately on the sub-page, drawer menu not scrollable
   (`scrollHeight == clientHeight`, observed 617 == 617).
4. Click `settings-nav-item-profile` — **exactly one click, no navigation outside
   Settings**.
   - **Verify**: URL becomes `${BASE_URL}/settings/profile`.
   - **Verify**: `settings-profile-logout-button` is visible, enabled, and
     `to_be_in_viewport()`.
5. **Axis 2**: zero console errors (0 observed live on both `/settings/tokens` and
   `/settings/profile`; **no** `#1771` / `#1203` filter — this path visits neither
   AI Personality nor Secrets).

The click on Log out itself is **not** performed — that is ELITEA-2253's subject and it
is blocked.

Note the overlap this would create: steps 4-5 duplicate ELITEA-2252's assertions. If
the ruling is "implement (b)", prefer `extend-existing` against ELITEA-2252's spec with
only steps 1-3 as the gap, rather than a second near-identical spec.

---

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-24) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | **on `automation/testids` only** | `BasePage.sidebar_settings_button` |
| Settings drawer root | `settings-drawer` | **needs-adding** | `SettingsDrawer.jsx` root `<Box sx={styles.drawer}>`; also the scope parent for the absence assertion |
| Drawer nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | **needs-adding** | `SettingsDrawer.jsx` `section.tabs.map`; state on `data-active`, never in the testid value. Class constant `SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'`. Needed values here: `tokens`, `profile`. |
| Personal Tokens page title | `personal-tokens-page-title` | **on `main` ✓ and `automation/testids` ✓** | the one pre-existing, fully promoted handle in this case |
| Log out button | `settings-profile-logout-button` | **needs-adding** | `Profile.jsx:73` — added by ELITEA-2252's implementation |
| Absent logout in drawer/sub-page | text-scoped absence assertion | n/a | an absence assertion cannot use a testid for a thing that does not exist; scope it inside `settings-drawer` / the page and declare it in the page-object docstring (`#579` discipline) |

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | — | covered (setup) |
| Step 1 — Log in and navigate to Settings → Personal Tokens | authenticated, lands on expected page | executed live; `/settings/tokens` reachable, `personal-tokens-page-title` present | — | executable (would be step 1 of option (b)) |
| Step 2 — without clicking any other sidebar item, "Log out" is visible in the sidebar | action completes, expected UI state | — | — | **blocked / clarification (#1772)** — live: 0 `Log out` nodes on the page; the only logout control is on `/settings/profile`; the sidebar user menu (`UserButton.jsx`) is dead code |
| Step 3 / Expected Final State — click "Log out", user is redirected to the login page | condition holds | — | — | **blocked** — same environment wall as ELITEA-2253 (no login page on localhost; `/forward-auth/logout` is served by the SPA fallback) |

No element is silently omitted: each is executable, or carries a `blocked` disposition
mirrored in § Blocked Steps.

### Axis 2 — observables asserted beyond the case
None — the case is blocked; no spec is specified. (Option (b) above lists what would be
added *if* a human re-scopes it.)

---

## Known Defects
None. Both walls are a stale case text and an environment topology, not product bugs.
Filing either as a `bug` would create false red — see the interaction-discovery ladder
ruling in `.agents/role-overrides.md` (#44 is the cautionary precedent).

## Note for whoever inherits `UserButton.jsx`
`src/[fsd]/widgets/sidebar-root/ui/button/UserButton.jsx` is unreferenced dead code
containing a `Preferences` + `Logout` user menu. It is **not** a rendering path, so no
test may target it and no testid should be added to it. Recorded here because it is the
single most likely thing to mislead the next person reading the source for "where is
logout".
