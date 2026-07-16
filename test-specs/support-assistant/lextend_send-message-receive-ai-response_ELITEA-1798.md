# Test Case: Send message and receive AI response via Send button

## Metadata
- **TMS ID**: ELITEA-1798
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-1798_send-message-and-receive-ai-response.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/108
- **Priority**: l2 (case priority `high`; existing coverage lives in the `smoke` marker tier)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step needed; on deployed envs, `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- **Analyst**: qa-engineer (Sage)
- **Status**: extend-existing

## Board Search Confirmation (Rule-6 traceability check)

Per the precedent set on `lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`
(a human-reviewer ruling on this same module): behavioral equivalence to an
existing test is not sufficient by itself to classify `already-covered` — the
correct test is whether this case's own tracked board task has ever reached
completion with delivered traceability.

- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-1798" --state all` →
  only **#108** — `[Automate][ELITEA-1798][support-assistant] Send message
  and receive AI response via Send button`, state **OPEN**, board status
  **`In Progress`** (this very analyst task). No prior issue, closed or open,
  ever targeted ELITEA-1798.
- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-0647"` → **zero
  results**. ELITEA-0647 is the *legacy* onetest-ai case
  (`tests/elitea-platform/elitea-chat-bot/ELITEA-0647_user-sends-a-message-via-the-send-button-and-receives-a-complete-assis.md`)
  that the existing test currently cites via `@allure.issue` — it predates
  this repo's board-driven pipeline (part of "Initial commit — public
  release") and was never tracked as a board task either.

**Conclusion:** the behavioral coverage that exists for this exact flow is
real and currently passing (see Live Execution Evidence below), but it was
never delivered as the outcome of a tracked task for ELITEA-1798
specifically — traceability from ELITEA-1798 to its automation is missing.
That gap is a small, well-defined code change (one `@allure.issue` line),
not a rewrite — hence `extend-existing`, not `ready-for-automation` and not
`already-covered`.

## Covering Test (behavioral proof)

- **File**: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
- **Class**: `TestSupportAssistantMessaging` (line 125)
- **Test**: `test_send_message_and_receive_response` — **line 135**
  (existing `@allure.issue` decorator at line 134, currently pointing only
  at legacy case ELITEA-0647)
- **Page object**: `automation/pages/support_assistant_page.py` —
  `open_widget()` (L142), `wait_for_widget_ready()`, `send_message()` (L175),
  `wait_for_response()` (L204), `get_assistant_message_count()` (L268),
  `is_input_empty()`

**Behavioral-equivalence argument.** The covering test performs, in order:
open the Support Assistant widget on `/chat` → wait for it to be ready →
capture `initial_count = get_assistant_message_count()` → send the literal
message `"Hello, what is Elitea?"` (character-for-character identical to
the case's Test Data) via `send_message()`, which fills the input, waits
for the Send button to become enabled, then clicks it → `wait_for_response()`
polls (up to `AI_RESPONSE_TIMEOUT = 60_000` ms, matching the case's 60 s
budget) for either a new `button[aria-label="Copy to clipboard"]` or a new
assistant-message wrapper with no active spinner, then adds a 1 s
stabilisation wait — this is exactly the case's Step 7 mechanism → asserts
`final_count > initial_count` (case Step 8) → asserts
`support_page.is_input_empty()` (case Step 9). Every one of the case's 9
steps maps onto an executed action or assertion in the covering test; no
case step is left unexercised.

## Live Execution Evidence (this pass, 2026-07-16)

Ran the covering test fresh, in isolation, against the live local stack
(`http://localhost:5173`, dev backend), to confirm current behavior before
classifying (case text can drift from a live product — verified live, not
assumed from prior passes):

```
cd automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantMessaging::test_send_message_and_receive_response \
  -v -p no:cacheprovider
```
Result: **1 passed in 62.10s**. JUnit: `automation/reports/archive/junit_20260716_195104.xml`.
HTML: `automation/reports/archive/report_20260716_195104.html`.

Also drove the widget manually via Playwright MCP (`browser_navigate` to
`/chat`, `browser_snapshot`) to cross-check the case's guessed selectors
against the live DOM before trusting the covering test's locators:

- The case's guessed selectors (`textbox[placeholder*="Type a message"]`,
  `button[aria-label="Send message"]`) are **not what the accessibility
  snapshot exposes** for the launcher — the "Support Assistant" launcher
  button renders outside the normal DOM flow (a portal) with no stable
  `ref` in the a11y tree, confirming the memory note "native click times
  out on launcher (MUI overlay intercept)". The covering page object
  already works around this correctly: `open_widget()` uses
  `page.evaluate()` with a JS `querySelector` + `.click()` rather than a
  native Playwright click. This is **not a new finding** — it's documented
  in `.agents/memory/qa-engineer/support_assistant_launcher_click_quirk.md`
  from a prior pass; re-confirmed live here, not fixed (out of scope for a
  traceability-only extend).
- No console errors observed during the send/receive cycle; one pre-existing
  console warning at page load (unrelated to Support Assistant, not
  investigated further — out of scope for this case).

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; other
  envs: `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`).
- Support Assistant feature is enabled — confirmed live: launcher renders
  unconditionally on `/chat`.

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured
  `APP_PREFIX`-aware base URL)
- Page under test: `/chat`
- Test message: `"Hello, what is Elitea?"` (matches case Test Data exactly;
  already hardcoded in the covering test — no new data needed)

(No generate-per-test or generate-shared-with-cleanup data — this flow only
sends a transient chat message; nothing persists that needs cleanup.)

## Coverage Map

### Axis 1 — case elements → disposition

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precond | User authenticated | dev-token auth works | `auth_state` fixture / `VITE_DEV_TOKEN` on localhost | conftest.py | covered |
| Precond | Support Assistant enabled | launcher renders | live observation this pass | manual snapshot, `/chat` | covered |
| 1 | Navigate to `/chat` | page loads | `chat_page.navigate_to_chat()` | test L138 | covered |
| 2 | Open Support Assistant widget | widget opens, title visible | `support_page.open_widget()` | test L139, page object L142 | covered |
| 3 | Wait for widget ready (title + input) | both visible | `support_page.wait_for_widget_ready()` | test L140 | covered |
| 4 | Record baseline assistant message count | count captured | `get_assistant_message_count()` | test L141 | covered |
| 5 | Type test message | text appears in input | `send_message()` fill step | page object L175-191 | covered |
| 6 | Wait for Send enabled, click | button not disabled, click performed | `send_message()` wait_for_function + click | page object L194-202 | covered |
| 7 | Wait up to 60s for AI response (new Copy button, 1s stabilisation) | response rendered | `wait_for_response(timeout=60_000)` | test L147, page object L204-233 | covered |
| 8 | Assert assistant message count increased | `final_count > initial_count` | explicit assert | test L150-153 | covered |
| 9 | Assert input field is empty | `is_input_empty()` True | explicit assert | test L155 | covered |
| — | Traceability: this test is the delivered outcome of a tracked ELITEA-1798 automation task | `@allure.issue` references ELITEA-1798's own case file | **not yet present** — only ELITEA-0647 (legacy, untracked) is referenced | test L134 | **gap — see below** |

### Axis 2 — assertions beyond the case

None. The covering test asserts exactly the case's two pass criteria
(message-count increase, input cleared) — no additional observables were
added, and none are proposed here; the case's Pass/Fail criteria are fully
satisfied by the existing assertions.

## Gap assertions (what the implementer must add)

Single addition to `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`,
immediately above line 134 (or replacing/joining the existing decorator
stack for `test_send_message_and_receive_response`):

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1798_send-message-and-receive-ai-response.md",
    "onetest-ai Test Case link",
)
```

Keep the existing `@allure.issue(..., "ELITEA-0647_...")` decorator in place
(the legacy case is still a valid, if untracked, ancestor) — this is
additive, not a replacement. No changes to test logic, page object, or
selectors are required; the live run this pass confirms the existing
implementation is correct and passing as-is.

Per `.agents/testing.md` § Coverage tagging, the implementer should also
back-write `automation_test_id =
tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantMessaging.test_send_message_and_receive_response`
to the ELITEA-1798 TMS case if the project's TMS adapter is wired for that
sync (see `.agents/test-automation.yaml`).

## Stable Handles (as currently implemented — informational, not new work)

All handles below are **existing, tech-debt raw locators** (predate the
testid-only policy; tracked as tech debt per `.agents/testing.md` § Locator
policy, issues #25/#42) — cited for traceability only. **No new locators are
introduced by this extend**, so no testid work is in scope here per the
"scope is load-bearing" rule (testids go only on elements a test newly
touches; this extend touches zero new elements).

| Element | Current handle | Type | Verified live this pass |
|---|---|---|---|
| Launcher button | `button.elitea-assistant-button, button[aria-label="Support Assistant"]` (clicked via `page.evaluate` JS click, not native Playwright click) | CSS + JS-evaluate | yes — native click intercepted by MUI overlay, JS click required (confirms prior memory note) |
| Widget title | `.elitea-assistant-header-title` | CSS | yes — 1 passed run this pass |
| Message input | `.elitea-assistant-input` (page object field); `send_message()` internally also tries `textbox[placeholder*="Type a message"]` then falls back to `get_by_placeholder("Type a message...")` | CSS / accessible-placeholder | yes |
| Send button | `button[aria-label="Send message"]` | ARIA label | yes — case's guessed selector matches this one exactly |
| Response-complete signal | `button[aria-label="Copy to clipboard"]` (new instance) OR `.elitea-assistant-message-wrapper--assistant` count increase with no `.elitea-assistant-status-chip--active` | CSS / ARIA label | yes |
| Assistant message count | `.elitea-assistant-message-wrapper--assistant` (falls back to Copy-to-clipboard button count) | CSS | yes |

## Cleanup

None required — the flow sends one transient chat message in a fresh
Support Assistant session; nothing persists beyond the browser context,
which pytest/Playwright tears down automatically at test end.

## Known Defects Found

None. The flow works end-to-end on the live product right now (fresh run
this pass: 1 passed in 62.10s, response received, message count increased,
input cleared). The only gap identified is a traceability/documentation gap
in test metadata (missing `@allure.issue` link to ELITEA-1798's own case
file), not a product defect — no ticket filed per `.agents/profile.md` §
Bug filing (that policy covers product defects; this is an automation
metadata gap, tracked directly via the Gap assertions section above and
issue #108 itself).
