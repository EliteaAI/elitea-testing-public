# Test Case: Navigating away from Settings and back restores the default landing tab

## Metadata
- **TMS ID**: ELITEA-2244
- **Linked Story**: none
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost),
  project `Private`
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-26
- **Status**: ready-for-automation (**minor case-text drift on the default-tab
  label only — the restore mechanism itself matches the case exactly**)
- **Surface digest**: `test-specs/settings-navigation/_surface.md`
- **Filed**: no new issue — the "AI Configuration" vs "General" label drift is
  the same root cause already tracked by clarification
  **EliteaAI/elitea-testing-public#1772** (row 3); this case doesn't name "AI
  Configuration" explicitly in its steps (unlike ELITEA-2242), so no additional
  comment was needed.
- **Cluster**: dispatched with ELITEA-2242 and ELITEA-2243 (one live session). The
  three differ in **steps**, not in data, so each has its own AFS.

---

## Case-text note — mechanism confirmed correct, only the label needs pinning

This case's title says "restores the default landing tab" — it does **not** name
"AI Configuration" anywhere in its own steps or expected results (unlike
ELITEA-2242/2243). Confirmed live: clicking "Settings" in the app sidebar always
hardcodes the destination to `project-general` ("General"), regardless of which
Settings sub-tab was last viewed. This IS "restoring the default landing tab" —
the mechanism the case describes is exactly what the product does. The only thing
worth pinning explicitly in this spec (since the case doesn't) is which tab that
default actually is, so a future reader doesn't assume it means "the previously
viewed tab" (it does not — see § Known traps).

---

## Preconditions
- User logged in (`auth_state`).
- Selected project is `Private`.

## Test Data
### reuse-existing
None. Read-only navigation check.

---

## Test Steps

1. **Navigate to Settings → Secrets (case step 1).**
   - Navigate to Settings (`sidebar_settings_button`), then click
     `settings-nav-item-secrets`.
   - **Verify**: URL is `${BASE_URL}/settings/secrets`.
   - **Verify**: `settings-nav-item-secrets` carries `data-active="true"`.
   - **Verify**: `settings-content` is non-blank (Secrets table/empty-state
     rendered).

2. **Click "Agents" in the left sidebar to navigate away (case step 2).**
   - Click `BasePage.sidebar_menu_item("agents")` (pre-existing testid-only
     handle, `sidebar-menu-item-agents` — see § Concrete Handles).
   - **Verify**: URL is `${BASE_URL}/agents/all` — confirms the navigation away
     genuinely left `/settings/*`.

3. **Click "Settings" again (case step 3).**
   - Click `sidebar_settings_button` again.
   - **Verify**: URL is `${BASE_URL}/settings/project-general` — **not**
     `/settings/secrets`. This is the case's core assertion: re-entering Settings
     does not resume the last-viewed sub-tab, it always lands on the default.

4. **Verify the Settings page loads without error and content area is not
   blank (case step 4 / Expected Final State).**
   - **Verify**: `settings-drawer` visible.
   - **Verify**: `settings-nav-item-project-general` carries `data-active="true"`
     — the live default tab is General (case-text says "AI Configuration"; see
     § header note — asserting the live label per the reverse-masking guard).
   - **Verify**: `settings-content` text content is non-empty AND recognizably
     the General page (same content check as ELITEA-2242 step 6 — the "General"
     / "AI Configurations" accordion headers).
   - **Verify**: zero console errors (this path visits Secrets then General —
     neither is AI Personality, so the known #1771 warning does not apply here;
     assert **strict** zero).

---

## Expected Results
- Settings → Secrets loads normally.
- Navigating to Agents genuinely leaves the Settings routes.
- Re-entering Settings via the sidebar button lands back on `/settings/project-general`
  (General) — the hardcoded default — regardless of Secrets having been the last
  tab viewed.
- The re-entered Settings page is non-blank, error-free, with General correctly
  marked active.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | asserted (setup) |
| Step 1 — Navigate to Settings → Secrets | target page/section loads | step 1 | step 1 | asserted |
| Step 2 — Click "Agents" to navigate away | control responds, next state shown | step 2 | step 2 | asserted |
| Step 3 — Click "Settings" again | control responds, next state shown | step 3 | step 3 | asserted |
| Step 4 / Expected Final State — Settings page loads without error, content area not blank | condition holds | step 4 | step 4 | **clarification (#1772)** — the *mechanism* (default tab restored) matches the case exactly; only the *label* is corrected from "AI Configuration" to the live "General" |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| URL is explicitly `/settings/project-general`, NOT `/settings/secrets` | The case's title implies "restores the DEFAULT tab" as distinct from "resumes the LAST tab" — asserting the URL explicitly (not just "not blank") is what actually proves the distinction rather than a weaker "some settings page loaded" check. |
| `data-active="true"` on `project-general` specifically | Confirms General, not merely "a" tab, is marked selected — catches a regression where the content loads correctly but the drawer's selection indicator desyncs. |
| Strict zero console errors | This path never visits AI Personality, so a genuinely clean baseline is expected and worth guarding (contrast with ELITEA-2243's necessary soft-assert). |

---

## Cleanup
None — read-only navigation, no state mutated.

## Concrete Handles

| Element | Primary handle (testid-only) | Provenance (verified `git fetch origin` 2026-08-26) | Notes |
|---|---|---|---|
| Sidebar "Settings" entry | `sidebar-settings-button` | `automation/testids` only | `BasePage.sidebar_settings_button` |
| Sidebar "Agents" entry | `sidebar-menu-item-agents` (dynamic, via `BasePage.sidebar_menu_item("agents")`) | pre-existing (`SidebarBody.jsx` passes `testId={\`sidebar-menu-item-${value}\`}`) | Class constant `BasePage.SIDEBAR_MENU_ITEM = '[data-testid="sidebar-menu-item-{}"]'`. Confirmed live via `getByRole('button', {name: 'Agents'})` during exploration transit, then cross-checked against this pre-existing page-object handle — no new testid needed. |
| Settings drawer root | `settings-drawer` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | |
| Drawer nav item (dynamic) | `settings-nav-item-{tabId}` + `data-active` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | |
| Settings content pane | `settings-content` | `automation/testids` only — `EliteaAI/EliteaUI@e1e031a1` | |

## Network Behavior
- No mutating requests. Route changes are client-side (React Router); no
  additional network behavior to document for this navigate-away-and-back case.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Known traps
- **"Restores the default landing tab" ≠ "resumes the last-viewed tab."** The
  product does the former, not the latter — confirmed live (Secrets was NOT
  restored; General was). Do not weaken step 3's assertion to merely "some
  Settings page loaded" — the whole point of this case is that it is
  specifically `project-general`, not `secrets`.
- **The live default tab is "General," not "AI Configuration."** See
  `test-specs/settings-navigation/_surface.md` and clarification #1772 — do not
  copy the case's original wording into the implemented assertion text/comments.

## Automation Hints
- Framework: pytest + Playwright.
- Page object: reuse the `SettingsDrawerPage` recommended in ELITEA-2242/2243's
  AFS for steps 1, 3, 4; step 2 uses the pre-existing
  `BasePage.sidebar_menu_item("agents")`.
- Wait strategy: after step 3's click, wait on the URL change
  (`page.wait_for_url("**/settings/project-general")`) rather than a fixed
  timeout, then assert `data-active` and content as in step 4.
