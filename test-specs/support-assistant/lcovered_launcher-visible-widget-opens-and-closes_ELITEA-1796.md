# Test Case: Launcher is visible and Support Assistant widget opens and closes

## Metadata
- **TMS ID**: ELITEA-1796
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/17
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step was needed)
- **Analyst**: qa-engineer (Sage)
- **Status**: already-covered

## Preconditions
- User is authenticated (on localhost this is satisfied automatically by `VITE_DEV_TOKEN`; in other environments the `page` fixture pre-loads `auth_state`).
- Support Assistant feature is enabled for the current deployment — confirmed: launcher renders unconditionally on `/chat`.

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured `APP_PREFIX`-aware base URL)
- Page under test: `/chat`

(No generate-per-test or generate-shared-with-cleanup data — this case only exercises open/close, no messages are sent.)

## Test Steps
1. Navigate to `${BASE_URL}/chat`
   - **Verify**: page loads, DOM ready (sidebar, chat input all rendered)
2. Assert the Support Assistant launcher button is visible
   - **Verify**: `button.elitea-assistant-button` (`aria-label="Support Assistant"`) is visible
3. Click the launcher to open the widget
   - **Verify**: widget panel opens; `.elitea-assistant-header-title` (rendered as `<h2>ELITEA Support</h2>`) becomes visible
4. Re-assert widget open state
   - **Verify**: `is_widget_open()`-equivalent check (`.elitea-assistant-header-title` visible) returns true
5. Click the Close (X) button (`aria-label="Close chat"`)
   - **Verify**: widget title element is removed from the DOM
6. Assert widget no longer open
   - **Verify**: `is_widget_open()`-equivalent check returns false
7. Assert launcher button is still visible
   - **Verify**: `button.elitea-assistant-button` visible again

## Expected Results
- Launcher visible before and after the open/close cycle.
- Widget opens on launcher click (`.elitea-assistant-header-title` → "ELITEA Support") and closes on Close (X) click.
- No console errors during the flow (0 errors observed; 1 pre-existing unrelated warning re: `stream` module externalization, present before any interaction).

## Coverage Map

**Axis 1 — Case coverage** (ELITEA-1796 steps 1–7, walked live against `http://localhost:5173/chat`):

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to `/chat` | page loads, DOM ready | AFS step 1 | `test_launcher_visible_and_opens_widget` L64-65 (`chat_page.navigate_to_chat()`) | already-covered |
| 2 Launcher button visible | `button[data-testid="support-assistant-launcher"]` (or fallback `button.elitea-assistant-button` / `button[aria-label="Support Assistant"]`) visible | AFS step 2 | L68-71 (`assert support_page.is_launcher_visible()`) | already-covered — see note below re: `data-testid` |
| 3 Click launcher opens widget | widget panel opens, `data-testid="support-assistant-title"` (or `h2:has-text("ELITEA Support")`) visible | AFS step 3 | L73-74 (`support_page.open_widget(...)` — internally JS-clicks the launcher and waits for `widget_title`) | already-covered |
| 4 Assert widget open | widget title visible; `is_widget_open()` returns True | AFS step 4 | L75-77 (`assert support_page.is_widget_open()`) | already-covered |
| 5 Click Close (X) | `button[data-testid="support-assistant-close"]` (or `button[aria-label="Close chat"]`) clicked, title becomes hidden | AFS step 5 | L79-80 (`support_page.close_widget(...)`) | already-covered |
| 6 Assert widget no longer open | `is_widget_open()` returns False; title not visible | AFS step 6 | L81-83 (`assert not support_page.is_widget_open()`) | already-covered |
| 7 Assert launcher still visible | launcher remains visible after close | AFS step 7 | L85-87 (`assert support_page.is_launcher_visible()`) | already-covered |

**Behavioural-equivalence proof:** `TestSupportAssistantLauncher.test_launcher_visible_and_opens_widget` at
`automation/tests/ui/support_assistant/test_support_assistant_smoke.py:50-88` executes the exact same
sequence this case specifies — navigate to chat, assert launcher visible, open widget via
`SupportAssistantPage.open_widget()`, assert `is_widget_open()` True, close via `close_widget()`, assert
`is_widget_open()` False, assert launcher visible again — with one assertion per case step, in the same
order, against the same underlying elements. Live execution against `http://localhost:5173/chat` in this
session (fresh browser context, no prior widget interaction) reproduced every expected result the case
specifies:
- Launcher: `<button type="button" aria-label="Support Assistant" class="elitea-assistant-button">` — visible pre- and post-cycle.
- Widget open: `.elitea-assistant-header-title` renders `<h2>ELITEA Support</h2>`, matching the case's own documented fallback (`h2:has-text("ELITEA Support")`).
- Widget close: title element removed from DOM entirely (stronger than merely hidden) after clicking `button[aria-label="Close chat"]`.
- No console errors introduced by the interaction (0 errors before/after).

This is Rule-6 full behavioural-equivalence dedup, not partial overlap — every case step maps 1:1 to an
existing assertion, so `already-covered` (not `extend-existing`) applies.

**Note on `data-testid`:** the case's own Test Data table lists `data-testid="support-assistant-launcher"`,
`data-testid="support-assistant-title"`, `data-testid="support-assistant-close"` as primary selectors. None
of these attributes exist in the live DOM — confirmed via live `document.querySelector` during this session.
Only the case's own documented *fallback* selectors exist and were used: `button.elitea-assistant-button`
/ `button[aria-label="Support Assistant"]`, `.elitea-assistant-header-title` (renders as `h2:has-text("ELITEA Support")`),
and `button[aria-label="Close chat"]`. This is case-text drift (reverse-masking guard), not a product defect —
the existing test and page object (`SupportAssistantPage`) already correctly use the fallback-only selectors
via `LocatorDescriptor(fallback=...)`, so no gap exists for automation purposes. It is, however, a genuine
divergence from `.claude/rules/page-objects.md` ("all locators must use `LocatorDescriptor` with a testid and
strictly NO fallback") — `support_assistant_page.py` uses fallback-only locators throughout with no testids
at all. That is a pre-existing framework-conformance debt in `automation/pages/support_assistant_page.py`,
separate from this case's coverage question; flagging for the `add-data-testid` skill / a follow-up cleanup,
not blocking this AFS.

**Axis 2 — Analyst additions:** none beyond the case. The existing test's assertions map exactly onto the
case's 7 steps; no additional observable was asserted during this exploration that the case didn't already
ask for.

## Cleanup
None required — this case performs no data-mutating actions (no messages sent, no sessions created).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Live-confirmed |
|---|---|---|---|
| Launcher button | `getByRole('button', { name: 'Support Assistant' })` | `button.elitea-assistant-button` | yes — `aria-label="Support Assistant"` |
| Widget title (open indicator) | `getByRole('heading', { level: 2, name: 'ELITEA Support' })` | `.elitea-assistant-header-title` | yes — renders `<h2>ELITEA Support</h2>` |
| Close button | `getByRole('button', { name: 'Close chat' })` | `button[aria-label="Close chat"]` | yes |

**Launcher click gotcha (confirmed live, not just in code):** a native Playwright `.click()` /
`getByRole('button', { name: 'Support Assistant' }).click()` times out — a MUI overlay
(`div[data-tour="sidebar-support-assistant"][data-mui-internal-clone-element="true"]`) intercepts pointer
events on the launcher. `SupportAssistantPage.open_widget()` already works around this via
`page.evaluate(...)` doing a raw `btn.click()`, bypassing Playwright's actionability check. Confirmed this
is necessary, not incidental — a plain role-based click reproducibly fails with the exact overlay-intercept
error. The Close button did **not** need the same workaround — a native `getByRole('button', { name: 'Close chat' }).click()` succeeded directly.

## Network Behavior
None relevant — open/close is a pure client-side UI state toggle, no network calls fire on either action.

## Known Defects Found During Exploration
None found. The case-text/DOM `data-testid` mismatch documented in the Coverage Map note is classified as
CLARIFICATION (case-text drift), not a defect — the product behaves correctly against its own documented
fallback selectors.

## Blocked Steps
None.

## Automation Hints
- No new test needed. Existing coverage: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py:50` — `TestSupportAssistantLauncher.test_launcher_visible_and_opens_widget`.
- Page object: `automation/pages/support_assistant_page.py` — `SupportAssistantPage`.
- **TMS back-write correction needed:** ELITEA-1796's frontmatter currently declares
  `automation_test_id: tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantLauncher.test_launcher_is_visible_and_opens_widget`
  (method name `test_launcher_is_visible_and_opens_widget`) — this method does not exist. The real, matching
  test is `test_launcher_visible_and_opens_widget` (no "is_"). `status: draft` is also stale — should become
  `ready` / equivalent "already automated" status once the ID is corrected.
- **Allure traceability gap (note, not an edit made here):** the covering test's `@allure.issue` decorators
  (L48-49) link only to the older onetest cases ELITEA-0625 and ELITEA-0626, not to ELITEA-1796. Since
  ELITEA-1796 supersedes/duplicates that same observable, consider adding a third `@allure.issue` link to
  ELITEA-1796 so Allure reports trace back to the currently-active TMS case, not only the historical ones.
