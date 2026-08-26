# Test Case: Clicking each Settings sidebar item navigates to its dedicated page

## Metadata
- **TMS ID**: ELITEA-2243
- **Linked Story**: none
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost),
  project `Private`
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-26
- **Status**: ready-for-automation (**case-text drift on step 6 — asserts the LIVE
  contract; known-defect soft-assert for #1771**)
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: step 6's drift is already tracked by clarification
  **EliteaAI/elitea-testing-public#1772** (row 4). The console error hit while
  executing this case's own click-through is already filed as
  **EliteaAI/elitea-testing-public#1771** (MINOR, filed specifically for
  ELITEA-2243). Neither is re-filed here.
- **Cluster**: dispatched with ELITEA-2242 and ELITEA-2244 (one live session). The
  three differ in **steps**, not in data, so each has its own AFS.

---

## ⚠️ Case-text drift — read this before implementing

Case step 6 ("Log out is visible as the last PERSONAL item and does NOT navigate
to a settings sub-page") assumes a Log out drawer item that does not exist. Per
the reverse-masking guard, this spec asserts the absence instead of a stale
presence check. Full root cause: `test-specs/settings-navigation/_surface.md` §
Case-text drift, and EliteaAI/elitea-testing-public#1772.

The rest of the case (steps 1-5, clicking every PROJECT and PERSONAL item and
verifying content updates) executes exactly as written and passes live — this is
**not** a wholesale drift case like ELITEA-2242, only step 6 is affected.

## ⚠️ Known defect — expect it, don't chase it

Clicking `settings-nav-item-ai-personality` (step 4, item 3 of PERSONAL)
deterministically fires one React console error — a `disableUnderline` prop
leaking onto a DOM node. Filed as **EliteaAI/elitea-testing-public#1771** (MINOR,
OPEN), single-cause, confirmed live. Per `.agents/testing.md` § Merge gate
sanctioned-RED / known-defect pattern, this spec asserts the console-error count
for the AI Personality click as `expect.soft(..., "# Known defect: #1771")`
rather than a hard zero — every OTHER tab's click asserts a **strict** zero.

---

## Preconditions
- User logged in (`auth_state`).
- Selected project is `Private` (drives which PROJECT items are visible — see
  ELITEA-2242's § Known traps, same digest).
- Start already on `/settings/project-general` (reuse ELITEA-2242's step 1, or
  navigate independently — both are legitimate entry points; this case's
  observable begins at step 1 below regardless of how Settings was reached).

## Test Data
### reuse-existing
None. Read-only navigation check.

---

## Test Steps

1. **Navigate to Settings.**
   - **Verify**: `settings-drawer` visible, `settings-nav-item-project-general`
     carries `data-active="true"` (starting state, matches ELITEA-2242's default).

2. **Click each PROJECT item one by one; verify the content area updates each
   time (case steps 2-3).**
   For each of `ai-providers`, `project-context`, `secrets`, `analytics`,
   `usage` (in this order — `project-general` is already active from step 1,
   skip it as a click target but it still counts as "verified" via step 1):
   - Click `settings-nav-item-{id}`.
   - **Verify**: URL becomes `${BASE_URL}/settings/{id}`.
   - **Verify**: `settings-nav-item-{id}` carries `data-active="true"` and the
     PREVIOUSLY active item now carries `data-active="false"` — proves the
     content area updated to THIS section, not stuck on the previous one (the
     case's explicit "not blank, not the previous section" requirement).
   - **Verify**: `settings-content`'s text content changed from the prior
     tab's content (a simple "text snapshot differs from the last captured
     snapshot" check is sufficient — this AFS does not require asserting each
     page's specific content, only that it visibly changed).
   - **Verify**: zero **new** console errors (strict — none of the PROJECT
     tabs are known to produce any).

3. **Click each PERSONAL item one by one; verify the content area updates each
   time (case steps 4-5).**
   For each of `profile`, `preferences`, `ai-personality`, `memory`, `tokens`,
   `notifications` (in this order):
   - Click `settings-nav-item-{id}`.
   - **Verify**: URL becomes `${BASE_URL}/settings/{id}` (`tokens` →
     `/settings/tokens`, matching the tab id, not the label "Personal Tokens").
   - **Verify**: `settings-nav-item-{id}` carries `data-active="true"`, prior
     item `data-active="false"`.
   - **Verify**: `settings-content` text content changed from the prior tab.
   - **Verify console errors**:
     - For `ai-personality` specifically: `expect.soft()` exactly one error
       matching the `disableUnderline` warning text, `# Known defect: #1771`.
     - For every other PERSONAL tab (`profile`, `preferences`, `memory`,
       `tokens`, `notifications`): strict zero new console errors.

4. **Verify Log out is NOT a drawer item and does not receive a click target
   (case step 6, corrected).**
   - **Verify (absence)**: no control whose accessible text is `Log out` exists
     inside `settings-drawer` —
     `expect(settings_drawer.get_by_text(re.compile(r"^\s*log\s*out\s*$", re.I))).to_have_count(0)`.
   - **Verify**: `settings-nav-item-notifications` is the LAST `settings-nav-item-*`
     element rendered inside `settings-drawer-menu` (proves Notifications, not a
     nonexistent Log out, is genuinely the last PERSONAL entry) —
     `page.locator('[data-testid="settings-drawer-menu"] [data-testid^="settings-nav-item-"]').last`
     resolves to the `notifications` testid.
   - Do **not** attempt to click a Log out drawer item — there is nothing to
     click. Do not confuse this with the real Log out control on the Settings →
     Profile page content pane (`settings-profile-logout-button`, out of scope
     for this case — see `test-specs/settings-user-profile/` for that surface).

---

## Expected Results
- Every PROJECT item (General already active; AI Providers, Project Context,
  Secrets, Analytics, Usage) and every PERSONAL item (Profile, Preferences, AI
  Personality, Memory, Personal Tokens, Notifications) navigates to its own
  distinct URL and re-renders `settings-content` on click.
- No item is a dead click and no click leaves the content area on the previous
  section.
- No Log out drawer item exists; Notifications is confirmed the last PERSONAL
  entry.
- Console stays clean except the single known #1771 warning on the AI
  Personality click.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Navigate to Settings | target page loads | step 1 | step 1 | asserted |
| Step 2 — Click each PROJECT item one by one | control responds, next state shown | step 2 | step 2 | asserted |
| Step 3 — For each click, content area updates to that section (not blank, not previous) | action completes, expected UI state | step 2 | step 2 (`data-active` swap + content-text-changed check) | asserted |
| Step 4 — Click each PERSONAL item one by one | control responds, next state shown | step 3 | step 3 | asserted |
| Step 5 — For each click, content area updates to that section | action completes, expected UI state | step 3 | step 3 | asserted |
| Step 6 — "Log out" visible as last PERSONAL item, does NOT navigate to a sub-page | condition holds | step 4 | step 4 | **clarification (#1772)** — asserted as Log out **absent** from the drawer entirely (not clickable, not navigable, not present), and Notifications confirmed the true last item |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| Known `#1771` console warning soft-asserted (not silently ignored, not hard-failed) on the AI Personality click | Confirmed live, deterministic, single-cause, filed and OPEN — per the merge-gate sanctioned-RED / known-defect pattern this must be visible in the test (`# Known defect: #1771`), not masked, and not allowed to hard-fail an otherwise-passing spec. |
| Strict zero console errors on every OTHER tab | Establishes the honest per-tab baseline so a future regression on any non-AI-Personality tab is caught, rather than being hidden behind a blanket filter. |
| `settings-nav-item-notifications` confirmed as the literal last child in `settings-drawer-menu` | Turns "Notifications is the true last PERSONAL item" from an assumption into a DOM-order assertion — catches a future reorder that silently reintroduces or hides the drift. |

---

## Cleanup
None — read-only navigation, no state mutated. **Do not click any Log out
control in this spec** (none exists in the drawer, and the real Profile-page
Log out button is out of scope — see `test-specs/settings-user-profile/_surface.md`
§ `/settings/profile` for why clicking it is destructive to a shared browser
context).

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-26) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | `automation/testids` only | Pre-existing |
| Settings drawer root | `settings-drawer` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | |
| Drawer menu container | `settings-drawer-menu` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | Used for the "last child" DOM-order check in step 4 |
| Drawer nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | Class constant `SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'` |
| Settings content pane | `settings-content` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | Two `<main>` elements exist on the page — never use a bare `main` selector |

No new testids needed — see `_surface.md` § Testids for full provenance.

## Network Behavior
- Each nav click is a client-side route change (React Router), not a full page
  navigation — no new network calls are required by this case beyond what each
  tab's own content already fetches on mount (out of scope for this
  navigation-only spec; see each surface's own AFS, e.g.
  `test-specs/settings-ai-providers/`, for that tab's fetch behavior).

## Known Defects Found During Exploration
- **[MINOR]** `/settings/ai-personality` fires a React console warning
  (`disableUnderline` prop leak) on every mount — filed as
  EliteaAI/elitea-testing-public#1771 (already OPEN, filed for this case).
  Automation uses `expect.soft()` with `# Known defect: #1771` on that one
  click only.

## Blocked Steps
None.

## Known traps
- **`tokens` is the route id for "Personal Tokens"**, not `personal-tokens` —
  clicking the item labelled "Personal Tokens" lands on `/settings/tokens`.
- **The PROJECT list is project-dependent** (see ELITEA-2242's § Known traps in
  the shared digest) — this spec clicks only the items visible on the `Private`
  project; do not hardcode a 5-click PROJECT loop that would silently skip
  `users` if run against a Team/Public project where it's visible.
- **The AI Personality console error is per-mount, not per-session** — if a test
  re-visits AI Personality more than once, expect the soft-assert to fire again
  each time; don't assume it's a one-shot.

## Automation Hints
- Framework: pytest + Playwright.
- Page object: same `SettingsDrawerPage` recommended in ELITEA-2242's AFS —
  this case is the natural home for a `click_nav_item(tab_id)` helper that
  returns the new `settings-content` text for the "content changed" diff.
- Wait strategy: after each click, wait for `settings-nav-item-{id}` to reach
  `data-active="true"` (a real product signal) rather than a fixed timeout —
  `expect(locator).to_have_attribute("data-active", "true")` is a built-in
  Playwright poll.
- Console capture: use `utils/console_errors.collect_console_errors(page)`
  (`.agents/testing.md` § Known issues) and filter the AI Personality click's
  capture window specifically for the `disableUnderline` text before soft-
  asserting; every other click's capture window asserts empty.
