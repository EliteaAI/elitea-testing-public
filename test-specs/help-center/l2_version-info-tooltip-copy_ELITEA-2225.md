# Test Case: Help Center — version info tooltip displays component versions and can be copied

## Metadata
- **TMS ID**: ELITEA-2225
- **Linked Story**: none
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (localhost bypasses Keycloak via
  `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture; localhost skips login via `VITE_DEV_TOKEN`).
- No seeded state required — the version/component data is app config + backend
  `systemInfo`, not user data.

## Test Data
### reuse-existing
- (none required) — the version label and component versions come from
  `useGetResourcesConfigQuery`/`useGetSystemInfoQuery` (backend-served, not test-seeded).

## Test Steps
1. Navigate to `${BASE_URL}/help-center`.
   - **Verify**: `help-center-page-header` testid visible, text "Help Center".
2. Locate the version label in the header (`help-center-version-label`).
   - **Verify**: visible, text matches `Version: X.Y.Z (DD-Mon-YYYY)` (live-confirmed:
     "Version: 2.0.3 (28-May-2026)").
3. Hover the info icon (`help-center-version-info-icon`) next to the version label.
   - MUI `Tooltip` mounts its content on hover — confirmed live via `page.hover()`.
4. Verify the tooltip content panel (`help-center-version-info-tooltip`) becomes visible
   and its text contains a `name: version` line for each of the 6 components the case
   names: `elitea_core`, `admin`, `notifications`, `configurations`, `sdk_plugin`,
   `indexer_worker` — **live-confirmed exact match** to the case's enumerated list, no
   drift.
5. Verify each component's version number is present within the same tooltip text
   (live-confirmed: `elitea_core: 0.673`, `admin: 0.77`, `notifications: 0.21`,
   `configurations: 0.160`, `sdk_plugin: 0.9.13`, `indexer_worker: 0.854`) — asserted as
   one substring check per component against the tooltip's aggregate text content (no
   per-row testid; see Automation Hints for why a single container testid is sufficient
   here per canon #511 scope discipline).
6. Verify a copy icon/button (`help-center-version-info-copy-button`) is present at the
   bottom of the tooltip.
7. Click the copy button.
8. Verify a success toast appears — **live-confirmed text**: "The version information
   has been copied to the clipboard." (generic app-wide toast, `toast-alert`/
   `toast-message` testids, reused per existing repo precedent — same component as
   `AgentDetailPage`/`ChatPage`).
9. Read the OS clipboard (`navigator.clipboard.readText()`, permission pre-granted on the
   browser context per `conftest.py`) and verify it contains the version line AND all 6
   component `name: version` pairs — i.e. the same content the tooltip displayed,
   confirming the copy is a faithful representation, not just "some notification fired."
   Format confirmed from source (`ResourceVersionInfo.jsx`):
   `Version: 2.0.3 (28-May-2026)\nelitea_core: 0.673\nadmin: 0.77\n...`.

## Expected Results
- The version label renders the backend-configured version + upgrade date.
- Hovering the info icon opens a tooltip listing all 6 components with their versions,
  matching the case's enumerated list exactly.
- The copy button copies a plain-text block (version line + one `name: version` line per
  component) to the OS clipboard, confirmed by a success toast AND by reading the
  clipboard back.

## Coverage Map

**Axis 1 — Case coverage**
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate the version label | UI state produced | step 2 | step 2: label visible, text pattern | asserted |
| 3 Click the "i" info icon | control responds | step 3 | step 3: hover opens tooltip (live product: hover-triggered, not click — see Automation Hints) | asserted *(interaction-mode clarified, not a defect — see below)* |
| 4 Tooltip shows elitea_core, admin, notifications, configurations, sdk_plugin, indexer_worker | condition holds | step 4 | step 4: tooltip visible + contains all 6 names | asserted |
| 5 Each component shows its version number | condition holds | step 5 | step 5: tooltip text contains each `name: version` pair | asserted |
| 6 Copy icon present at bottom of tooltip | condition holds | step 6 | step 6: copy button visible | asserted |
| 7 Click the copy icon | control responds | step 7 | step 7: click | asserted |
| 8 Success notification appears | condition holds | step 8 | step 8: toast visible with live-confirmed text | asserted |
| 9 Paste clipboard contents, verify all component version details included | field accepts input, displays value | step 9 | step 9: `navigator.clipboard.readText()` contains version line + all 6 component lines | asserted *(clipboard read via API — see Automation Hints for why this is the honest equivalent of "paste into a text editor")* |

**Axis 2 — Analyst additions:**
- Interaction-mode note (step 3) — *added: the case text says "Click the 'i' (info)
  icon"; live product opens the tooltip on HOVER (MUI `Tooltip` default trigger), not
  click. Per the interaction-discovery ladder (`.agents/role-overrides.md`), this is
  case-text drift, not a defect — clicking also works incidentally (MUI Tooltip stays
  open while the pointer is over the trigger or the tooltip itself, and a click doesn't
  dismiss it), but the AUTOMATED interaction uses `hover()` as the intended,
  code-confirmed trigger (`ResourceVersionInfo.jsx`'s `<Tooltip>` has no
  `disableHoverListener`/click-only wiring). Not filed as a CLARIFICATION ticket — this
  is a one-line automation-hint note, not a product-facing discrepancy worth a tracked
  issue (the tooltip DOES open on click too, so the case text is not actually wrong for
  a human user, just imprecise about the mechanism).*
- Clipboard read-back (step 9) — *added: the case's own success criterion is "paste the
  clipboard contents into a text editor and verify all component version details are
  included" — the honest automated equivalent is reading `navigator.clipboard` directly
  (same OS clipboard a paste would read from), not literally opening an editor
  application.*
- Content-fidelity cross-check (step 9) — *added: asserts the clipboard text is not just
  non-empty but contains the SAME version + component data the tooltip displayed,
  catching a "toast lied, nothing useful was copied" regression class.*

## Cleanup
- None required — no test data created; the toast auto-dismisses; hovering away closes
  the tooltip (no explicit close step needed for a fresh test to start clean next run).

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance |
|---|---|---|
| Help Center page header | `help-center-page-header` | on `main` ✓ / on `automation/testids` ✓ (pre-existing, ELITEA-2227) |
| Version label | `help-center-version-label` | **added THIS session** — `EliteaAI/EliteaUI@bc82bc32` on `automation/testids`; NOT yet on `main` (human cherry-pick pending) |
| Info icon (tooltip trigger) | `help-center-version-info-icon` | **added THIS session** — `EliteaAI/EliteaUI@bc82bc32` on `automation/testids`; NOT yet on `main` |
| Tooltip content panel | `help-center-version-info-tooltip` | **added THIS session** — `EliteaAI/EliteaUI@bc82bc32` on `automation/testids`; NOT yet on `main` |
| Copy button | `help-center-version-info-copy-button` | **added THIS session** — `EliteaAI/EliteaUI@bc82bc32` on `automation/testids`; NOT yet on `main` |
| App-wide toast alert/message | `toast-alert` / `toast-message` | on `main` ✓ / on `automation/testids` ✓ (pre-existing, `src/components/Toast.jsx`; reused per existing per-page-object-field precedent, e.g. `AgentDetailPage`, `ChatPage`) |

```python
# help_center_page.py — new LocatorDescriptor fields
version_label = LocatorDescriptor(testid="help-center-version-label")
version_info_icon = LocatorDescriptor(testid="help-center-version-info-icon")
version_info_tooltip = LocatorDescriptor(testid="help-center-version-info-tooltip")
version_info_copy_button = LocatorDescriptor(testid="help-center-version-info-copy-button")
toast_alert = LocatorDescriptor(testid="toast-alert")
toast_message = LocatorDescriptor(testid="toast-message")
```

## Network Behavior
- No new XHR — version/component data arrives via the page's existing
  `useGetResourcesConfigQuery`/`useGetSystemInfoQuery` calls (already resolved by the
  time the header renders the version label). The copy action is entirely
  client-side (`navigator.clipboard.writeText()`), no network call.

## Known Defects Found During Exploration
None. The tooltip content, copy behavior, and toast text all match the case's intent
exactly (component list, notification, clipboard content). The click-vs-hover trigger
difference is documented above as case-text imprecision, not a defect (interaction-
discovery ladder step 6 — the source (`ResourceVersionInfo.jsx`'s bare `<Tooltip>`) is
decisive: hover is the intended and only wired trigger; no separate click handler exists
on the icon, so nothing is "broken" for a user who clicks — the tooltip opens because
hover fires on/before the click, not because of a click handler).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest.
- Reuses `automation/pages/help_center_page.py` — new locators + two new action methods:
  `open_version_info_tooltip()` (hover, per the interaction-discovery finding above) and
  `copy_version_info()` (click copy, wait for toast, poll clipboard non-empty via
  `page.wait_for_function`, return `get_clipboard_text()` — mirrors the pattern in
  `test_agent_copy_version_link.py`'s `_copy_link_via_menuitem()`).
- Clipboard permissions are already granted globally in `conftest.py`'s
  `context` fixture (`permissions=["clipboard-read", "clipboard-write"]`) — no
  per-test grant needed.
- New pytest marker: none — `help_center` + priority `p2` (high→l2) + `regression`.
- Scope discipline (canon #511): the tooltip's 6 component rows are NOT individually
  testid'd — the case only requires verifying their presence/values, which a single
  `help-center-version-info-tooltip` container testid + text-content assertions
  satisfies without adding per-row handles the test doesn't need to disambiguate
  anything (no click/selection target on an individual row).
- Wait strategy: `hover()` + `wait_for(state="visible")` on the tooltip (MUI mounts the
  Tooltip content on hover — no fixed delay), `wait_for(state="visible")` on the toast,
  `page.wait_for_function()` polling the clipboard for non-empty — no `sleep`.
