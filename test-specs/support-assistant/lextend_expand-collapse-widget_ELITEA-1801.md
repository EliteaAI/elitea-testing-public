# Test Case: Expand widget to full-view mode and collapse back

## Metadata
- **TMS ID**: ELITEA-1801
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/114
- **Priority**: l3 (case priority = medium; `l1` critical / `l2` high / `l3` medium / `l4` low per spec-format.md)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step needed)
- **Analyst**: qa-engineer (Sage)
- **Status**: extend-existing

## Board Search Confirmation

Existing automation (`test_expand_collapse_fullview`,
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py:274-299`)
already executes this exact flow — open widget → click expand → assert open →
click again to collapse → assert open — but its only `@allure.issue` link
targets the legacy onetest case `ELITEA-0624`, never `ELITEA-1801`. Searched
for any completed automation task that ever delivered ELITEA-1801 traceability:

```
env -u GITHUB_TOKEN gh issue list --search "ELITEA-1801 OR ELITEA-0624" --state all
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json
```

- **#114** `[Automate][ELITEA-1801][support-assistant] Expand widget to
  full-view mode and collapse back` — **OPEN**, board status **`In Progress`**
  (this very task). No `Ready`/`Done` state was ever reached.
- No other issue in the repo references ELITEA-1801 or ELITEA-0624.

**Conclusion: no board task has ever completed automation for ELITEA-1801 (or
its legacy predecessor ELITEA-0624).** The behavioral coverage that exists is
inherited from pre-pipeline history (same pattern as the ELITEA-1796 re-do,
`test-specs/support-assistant/lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`),
not a delivered outcome of this case's own tracked task — hence
`extend-existing`, not `already-covered`.

## Preconditions
- User is authenticated (on localhost this is satisfied automatically by `VITE_DEV_TOKEN`; in other environments the `page` fixture pre-loads `auth_state`).
- Support Assistant feature is enabled — confirmed live: launcher renders unconditionally on `/chat`.
- Widget is in compact (default) mode when opened — confirmed live (see Test Steps step 1).

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured `APP_PREFIX`-aware base URL)
- Page under test: `/chat`

(No generate-per-test or generate-shared-with-cleanup data — this case only exercises the widget's own view-mode toggle, no messages are sent, no entities are created.)

## Test Steps
1. Navigate to `${BASE_URL}/chat` and open the Support Assistant widget (JS-evaluated click on the launcher — see Known Limitations)
   - **Verify**: widget panel opens in compact mode; `.elitea-assistant-header-title` (`<h2>ELITEA Support</h2>`) is visible; `.elitea-assistant-window` container is `460×480`px, class `elitea-assistant-window` (no `--expanded` modifier)
2. Click the Expand/Collapse toggle button (`aria-label="Expand chat"`, header action button — **no `data-testid` exists live**, see Known Limitations)
   - **Verify**: click succeeds with a native Playwright click (no MUI-overlay workaround needed for this button — unlike the launcher)
3. Wait 500 ms for the expand animation
   - **Verify**: animation settles
4. Assert full-view mode reached
   - **Verify**: `.elitea-assistant-window` container gains class `elitea-assistant-window--expanded`; geometry changes to `720×678`px; `.elitea-assistant-header-title` still shows "ELITEA Support" and is visible
5. Click the same toggle button again (same element, same aria-label — confirmed live it is a true toggle, not two separate buttons)
   - **Verify**: click succeeds
6. Wait 500 ms for the collapse animation
   - **Verify**: animation settles
7. Assert compact mode restored
   - **Verify**: `.elitea-assistant-window` container loses the `--expanded` modifier class, reverts to class `elitea-assistant-window` only; geometry reverts to `460×480`px; `.elitea-assistant-header-title` still shows "ELITEA Support" and is visible
8. Check console for errors across the whole flow
   - **Verify**: no new console errors introduced by expand/collapse (baseline dev warnings — React DevTools notice, ASCII banner, `stream` externalization warning — are pre-existing and unrelated)

## Expected Results
- Widget starts in compact mode (`460×480`px, no `--expanded` class).
- Clicking the toggle button expands to full-view mode (`720×678`px, `--expanded` class added); widget stays open, title stays visible.
- Clicking the same toggle button again collapses back to compact mode (`460×480`px, `--expanded` class removed); widget stays open, title stays visible.
- No console errors during the cycle.

## Coverage Map

**Axis 1 — Case coverage** (ELITEA-1801 steps 1–9, re-walked live against
`http://localhost:5173/chat` in a fresh browser context this session,
2026-07-16):

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to `/chat` | page loads successfully | AFS step 1 | `test_expand_collapse_fullview` L280-282 (`chat_page.navigate_to_chat()`) | extend-existing |
| 2 Open widget | compact mode, title visible | AFS step 1 | L283-285 (`support_page.open_widget()`, `wait_for_widget_ready()`) — live-reconfirmed: `class: "elitea-assistant-window"`, rect `460×480`, title "ELITEA Support" | extend-existing |
| 3 Wait for widget ready | title + input visible | AFS step 1 | L285 (`wait_for_widget_ready`) | extend-existing |
| 4 Click Expand button (`data-testid="support-assistant-expand"` per case text) | expand triggered, 0.5s wait | AFS steps 2-3 | L287-289 (`support_page.expand_to_fullview()`) — **live-reconfirmed the testid does NOT exist**; real handle is `aria-label="Expand chat"` on `button.elitea-assistant-header-action`, matching `expand_button` LocatorDescriptor fallback in `support_assistant_page.py:65-68`. Case-text drift, not a product defect — see Known Limitations. | extend-existing *(with clarification, not a fresh bug — see below)* |
| 5 Wait 500ms for expand animation | animation finishes | AFS step 3 | L289 (`page.wait_for_timeout(ANIMATION_WAIT)`) | extend-existing |
| 6 Assert widget open in full-view; `is_widget_open()` True, title visible | full-view mode confirmed | AFS step 4 | L291-292 (`assert support_page.is_widget_open()`) — **gap: existing assertion is mode-insensitive** (`is_widget_open()` checks only title visibility, which is true in BOTH compact and full-view — it does not actually prove full-view was reached). Live-observed the real, mode-specific signal: `.elitea-assistant-window` gains class `elitea-assistant-window--expanded` and resizes `460×480` → `720×678`. See Gap assertions below. | extend-existing *(gap — see Gap assertions)* |
| 7 Click toggle again to collapse; same button acts as toggle | toggle confirmed, 0.5s wait | AFS step 5 | L294-296 (`support_page.collapse_to_widget()` — internally re-clicks `expand_button`, documented in its own docstring as "the expand/collapse button is a toggle") — live-reconfirmed: same DOM button, `aria-label` stays `"Expand chat"` in both states (only the browser tooltip text changes to "Collapse" — see Known Limitations), single click toggles state both ways | extend-existing |
| 8 Wait 500ms for collapse animation | animation finishes | AFS step 6 | L296 | extend-existing |
| 9 Assert widget open in compact mode; `is_widget_open()` True, title visible | compact mode confirmed | AFS step 7 | L298-299 (`assert support_page.is_widget_open()`) — same mode-insensitivity gap as step 6. Live-observed real signal: `--expanded` class removed, geometry reverts to `460×480`. | extend-existing *(gap — see Gap assertions)* |

**Behavioural-overlap argument (what's already proven):**
`TestSupportAssistantViewModes.test_expand_collapse_fullview` at
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py:274-299`
executes the identical sequence this case specifies — open widget (compact),
click expand, assert still open, click again (collapse), assert still open —
one assertion per case step, same order, same underlying toggle button.
Re-executed live in this session (fresh browser context, no prior widget
interaction) and the flow's structural shape reproduced exactly: same button
re-used as a true toggle, widget never closes at any point, title text never
changes. **The overlap is total on the flow-shape axis.**

**Why this is `extend-existing`, not `already-covered`:** two independent gaps
exist beyond pure behavioral-equivalence, per the ELITEA-1796 corrected
judgment criterion (tracked-task delivery, not just incidental test overlap):
1. **Traceability gap** — the existing test's only `@allure.issue` link is to
   the legacy `ELITEA-0624` case; ELITEA-1801 (this pipeline's actual target,
   confirmed via Board Search Confirmation above) has never been linked.
2. **Assertion-strength gap** — `is_widget_open()` is insensitive to
   compact-vs-full-view mode (it only checks title visibility, true in both
   states), so the existing test's step-4/step-5 assertions don't actually
   prove the expand/collapse toggle changed anything. This was only visible by
   re-executing the flow live and instrumenting the real DOM signal
   (`--expanded` class + geometry) — the existing test would pass identically
   even if the expand button silently did nothing.

**Gap assertions (what the implementer must add to
`test_expand_collapse_fullview`):**
1. Append a second `@allure.issue(...)` decorator for ELITEA-1801 (same
   convention as the existing `ELITEA-0624` link and the ELITEA-1796 precedent):
   ```python
   @allure.issue(
       "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1801_expand-to-full-view-and-collapse-back.md",
       "onetest-ai Test Case link",
   )
   ```
2. Add a real mode-specific assertion. Add an `is_fullview_mode()` method to
   `SupportAssistantPage` (see Automation Hints) and call it:
   - After Step 2 (expand): `assert support_page.is_fullview_mode()`
   - After Step 4 (collapse): `assert not support_page.is_fullview_mode()`
   These supplement, not replace, the existing `is_widget_open()` calls —
   both properties (open AND correct mode) matter per the case's own
   Pass/Fail criteria ("widget closes during expand or collapse" is listed as
   a Fail condition, so `is_widget_open()` stays; it's just not sufficient
   alone).

**Axis 2 — Analyst additions:**
- Step 8 (console-error check across the flow) — *added: not explicit in the
  case text, but the case's own Pass/Fail criteria say "Any step produces an
  error... = Fail"; a console check is the only way to catch a silent JS
  error that doesn't visibly break the UI.*
- Geometry assertions (`460×480` ↔ `720×678`) — *added: the case only asks
  for `is_widget_open()` + title-visible, which (per the Gap assertions
  above) doesn't actually distinguish the two modes. Geometry + class are the
  real, stable signals discovered live; recorded here so the implementer
  doesn't have to re-discover them.*

## Cleanup
None required — the widget's own state is not persisted between sessions;
navigating to a fresh page instance always starts back in compact mode. No
entities created, nothing to delete via UI or API.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Widget container (mode signal) | `page.locator('.elitea-assistant-window')` — assert `class` contains/excludes `elitea-assistant-window--expanded` | Bounding-box geometry: `460×480` (compact) vs `720×678` (full-view) at default viewport |
| Expand/Collapse toggle button | `getByRole('button', { name: 'Expand chat' })` — **confirmed live: same button both ways, aria-label never changes to "Collapse chat" despite the tooltip text changing** | `button.elitea-assistant-header-action[aria-label="Expand chat"]` (already the `expand_button` LocatorDescriptor in `support_assistant_page.py:65-68`) |
| Widget title | `.elitea-assistant-header-title` (`<h2>ELITEA Support</h2>`) | already the `widget_title` LocatorDescriptor, `support_assistant_page.py:74-77` |

**`data-testid="support-assistant-expand"` does NOT exist in the live DOM** —
confirmed via `page.evaluate` reading `getAttribute('data-testid')` on the
expand button (returns `null`). This is not a fresh defect: it is the same,
already-documented root cause as ELITEA-1802/ELITEA-1796 (memory entry
`support_assistant_launcher_click_quirk.md`) — the Support Assistant widget
ships as the third-party npm package `@eliteaai/elitea-assistant`, not
first-party EliteaUI JSX, so `add-data-testid` cannot remediate any selector
on this widget. Treated as a permanent scope exception per that established
precedent, not filed as a new bug. The case's Test Data table (`button[data-testid="support-assistant-expand"]`)
is stale case text; the case's own documented fallback
(`button[aria-label="Expand chat"]`) is the one real handle, and it is what
`support_assistant_page.py`'s `expand_button` already uses.

## Network Behavior
None — expand/collapse is a pure client-side CSS/layout state change; no
network request fires on toggle (confirmed via `browser_console_messages` /
no new requests observed in the evaluate-based checks during exploration).

## Known Defects Found During Exploration
None found that block automation. Two minor, non-blocking observations:

- **[INFO]** Case's Test Data table cites a non-existent `data-testid="support-assistant-expand"`.
  Not filed as a new issue — same established root cause as ELITEA-1802
  (third-party widget package, no first-party JSX to patch); see Concrete
  Handles above. Case text is stale, not a product defect (reverse-masking
  guard) — the case's own documented fallback selector is correct and live.
- **[INFO / cosmetic a11y]** The toggle button's `aria-label` stays literally
  `"Expand chat"` in both compact and full-view mode — only the native
  browser tooltip text changes to "Collapse" (confirmed via a hover-triggered
  tooltip snapshot after clicking to full-view). A screen-reader user would
  hear "Expand chat" even while already in full-view. This is inside the same
  third-party package boundary as the testid gap above (no first-party JSX to
  fix), so not filed as a separate ticket — noted here for visibility if the
  team ever escalates upstream to `@eliteaai/elitea-assistant`.

## Blocked Steps
None.

## Evidence

- `test-results/screenshots/ELITEA-1801-step-1-compact-mode.png` — widget open, compact mode (`460×480`)
- `test-results/screenshots/ELITEA-1801-step-4-fullview-mode.png` — after clicking the toggle, full-view mode (`720×678`, `--expanded` class)
- `test-results/screenshots/ELITEA-1801-step-7-compact-mode-restored.png` — after clicking the toggle again, compact mode restored

## Automation Hints
- Framework: Playwright + pytest (confirmed from `automation/pytest.ini`, existing `test_support_assistant_smoke.py`)
- Page object: `automation/pages/support_assistant_page.py` — extend, don't duplicate. Add:
  ```python
  widget_container = LocatorDescriptor(
      fallback=lambda page: page.locator('.elitea-assistant-window').first,
      description="Support Assistant widget container (mode signal via class)"
  )

  def is_fullview_mode(self) -> bool:
      """Check if the widget is currently in full-view (expanded) mode.

      Returns:
          True if the widget container has the --expanded modifier class.
      """
      try:
          class_attr = self.widget_container.get_attribute("class") or ""
          return "elitea-assistant-window--expanded" in class_attr
      except Exception:
          return False
  ```
  (`widget_container` already exists as a fallback-only locator per the
  pre-existing framework debt noted in memory — this repo's testid-only rule
  is a permanent scope exception for this widget, same as `launcher_button`,
  `close_button`, etc. already in the file.)
- Test to extend: `TestSupportAssistantViewModes.test_expand_collapse_fullview`,
  `automation/tests/ui/support_assistant/test_support_assistant_smoke.py:274-299`
  — do not create a new test file/class.
- Wait strategy: keep the existing `page.wait_for_timeout(ANIMATION_WAIT)` —
  this is a pure CSS transition with no network signal to wait on instead
  (confirmed no request fires on toggle).
