# Test Case: Attach button is present and opens file picker in Support Assistant

## Metadata
- **TMS ID**: ELITEA-1802
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-1802_attach-button-present-and-opens-file-picker.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/110
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step needed; on deployed envs, `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- **Analyst**: qa-engineer (Sage)
- **Status**: extend-existing

## Board Search Confirmation (Rule-6 traceability check)

Same check as the precedent set on `lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`
and repeated on `lextend_send-message-receive-ai-response_ELITEA-1798.md`: behavioral
equivalence to an existing test is not sufficient by itself to classify
`already-covered` — the test is whether *this case's own* tracked board task
has ever reached completion with delivered traceability.

- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-1802" --state all --repo EliteaAI/elitea-testing-public`
  → only **#110** — `[Automate][ELITEA-1802][support-assistant] Attach button
  is present and opens file picker in Support Assistant`, state **OPEN**,
  board status **`In Progress`** (this very analyst task). No prior issue,
  closed or open, ever targeted ELITEA-1802.
- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-0577" --state all --repo EliteaAI/elitea-testing-public`
  → **zero results**. ELITEA-0577 is the *legacy* onetest-ai case
  (`tests/elitea-platform/elitea-chat-bot/ELITEA-0577_support-assistant-files-can-be-attached-via-click-to-browse-drag-and-d.md`)
  that the existing test currently cites via `@allure.issue` — it predates
  this repo's board-driven pipeline and was never tracked as a board task
  either.

**Conclusion:** the behavioral coverage for this exact flow (attach button
visible → click → native file-chooser opens → file selected → network
settles) is real and currently passing (see Live Execution Evidence below),
but it was never delivered as the outcome of a tracked task for ELITEA-1802
specifically — traceability from ELITEA-1802 to its automation is missing.
That gap is a small, well-defined addition (one `@allure.issue` line), not a
rewrite — hence `extend-existing`, not `ready-for-automation` and not
`already-covered`.

## Covering Test (behavioral proof)

- **File**: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
- **Class**: `TestSupportAssistantAttachments` (line 302)
- **Test**: `test_attach_button_present_and_opens_picker` — **line 312**
  (existing `@allure.issue` decorator at line 311, currently pointing only
  at legacy case ELITEA-0577)
- **Page object**: `automation/pages/support_assistant_page.py` —
  `open_widget()` (L143), `wait_for_widget_ready()` (L448),
  `attach_button` `LocatorDescriptor` (L94), `attach_file()` helper (L432,
  unused by this particular test — the test drives `expect_file_chooser`
  inline instead; see Stable Handles below)

**Behavioral-equivalence argument.** The covering test performs, in order:
open the Support Assistant widget on `/chat` → wait for it to be ready
(title + input visible, `wait_for_widget_ready()`) → assert
`button[aria-label="Attach file"]` is visible (case Step 4) → create a
temp file (`tmp_path/test_attachment.txt`, content `"Test attachment
content"` — byte-for-byte identical to the case's Test Data) → open a
`page.expect_file_chooser()` context manager and click the attach button
inside it (case Step 5) → assert the resulting `FileChooser` object is not
`None` (case Step 6) → call `file_chooser.set_files(str(test_file))` (case
Step 7) → wait for network idle via `support_page.wait_for_network()` (case
Step 8, same `WIDGET_TIMEOUT` budget the case's 10 000 ms Network idle
timeout data row specifies). Every one of the case's 8 steps maps onto an
executed action or assertion in the covering test; no case step is left
unexercised.

## Live Execution Evidence (this pass, 2026-07-16)

Ran the covering test fresh, in isolation, against the live local stack
(`http://localhost:5173`, dev backend), to confirm current behavior before
classifying (case text can drift from a live product — verified live, not
assumed from prior passes):

```
cd automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/support_assistant/test_support_assistant_smoke.py::TestSupportAssistantAttachments::test_attach_button_present_and_opens_picker \
  -v -p no:cacheprovider
```
Result: **1 passed in 9.46s**. JUnit: `automation/reports/archive/junit_20260716_205738.xml`.
HTML: `automation/reports/archive/report_20260716_205738.html`.

Cross-checked the guessed case selector against the live source before
trusting it: `grep -rn 'aria-label="Attach file"' ../EliteaUI/src` returns
**nothing** — the Support Assistant widget is not first-party EliteaUI
source. It ships as the third-party npm package
`@eliteaai/elitea-assistant` (`../EliteaUI/node_modules/@eliteaai/elitea-assistant`,
mounted once at `[fsd]/app/root.jsx` via
`[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx`). This confirms
and sharpens the prior memory note
(`.agents/memory/qa-engineer/support_assistant_launcher_click_quirk.md`):
**every** Support Assistant DOM handle — not just the launcher — lives
inside a package this repo's `EliteaAI/EliteaUI` team does not own or build
from source. The `data-testid` locator policy's remediation path
(`add-data-testid` edits JSX files in the EliteaUI repo) **does not apply**
here — there is no first-party JSX to edit. Raw `aria-label` selectors are
not a policy violation to fix in this repo; they are the only handle this
external widget currently exposes. Flagging this as a scope exception, not
a to-do, so a future analyst doesn't re-open `add-data-testid` work against
a package outside this team's control.

No console errors observed during the attach flow. One pre-existing console
warning at page load (unrelated to Support Assistant, not investigated
further — out of scope for this case, matches the note already on
`lextend_send-message-receive-ai-response_ELITEA-1798.md`).

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; other
  envs: `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`).
- A temporary test file (`test_attachment.txt`, content `"Test attachment
  content"`) is created by the `tmp_path` pytest fixture — already how the
  covering test builds it.
- Support Assistant feature is enabled — confirmed live: launcher renders
  unconditionally on `/chat`.

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured
  `APP_PREFIX`-aware base URL)
- Page under test: `/chat`
- Test file name/content: `test_attachment.txt` / `"Test attachment
  content"` (matches case Test Data exactly; already hardcoded via
  `tmp_path` in the covering test — no new data needed)
- Network idle timeout: 10 000 ms (matches `WIDGET_TIMEOUT` already used by
  the covering test)

(No generate-per-test or generate-shared-with-cleanup data needed — the
`tmp_path` fixture is function-scoped and self-cleaning; see Postconditions.)

## Coverage Map

### Axis 1 — case elements → disposition

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precond | User authenticated | dev-token auth works | `auth_state` fixture / `VITE_DEV_TOKEN` on localhost | conftest.py | covered |
| Precond | Temp test file created | `test_attachment.txt` exists with expected content | `tmp_path` pytest fixture | test L329-330 | covered |
| Precond | Support Assistant enabled | launcher renders | live observation this pass | manual verification, `/chat` | covered |
| 1 | Navigate to `/chat` | page loads | `chat_page.navigate_to_chat()` | test L319 | covered |
| 2 | Open Support Assistant widget | widget panel opens, title visible | `support_page.open_widget()` | test L321, page object L143 | covered |
| 3 | Wait for widget fully ready | title + message input visible | `support_page.wait_for_widget_ready()` | test L322, page object L448 | covered |
| 4 | Assert Attach file button visible | `attach_btn.is_visible()` True | inline `page.locator('button[aria-label="Attach file"]').first` + assert | test L325-326 | covered |
| 5 | Click Attach button inside `expect_file_chooser` | file-chooser context active, click executed | `page.expect_file_chooser(timeout=WIDGET_TIMEOUT)` wrapping `attach_btn.click()` | test L331-332 | covered |
| 6 | Assert file-chooser dialog opened | `fc_info.value` is not `None` | explicit assert | test L335-336 | covered |
| 7 | Select test file in chooser | `set_files()` sets the temp file | `file_chooser.set_files(str(test_file))` | test L337 | covered |
| 8 | Wait for network idle after upload (≤10s) | `networkidle` reached | `support_page.wait_for_network(timeout=WIDGET_TIMEOUT)` | test L338 | covered |
| — | Traceability: this test is the delivered outcome of a tracked ELITEA-1802 automation task | `@allure.issue` references ELITEA-1802's own case file | **not yet present** — only ELITEA-0577 (legacy, untracked) is referenced | test L311 | **gap — see below** |

### Axis 2 — assertions beyond the case

None. The covering test asserts exactly the case's two structural
observables (attach button visibility, file-chooser opened) plus performs
the file-selection and network-settle actions the case's remaining steps
describe — no additional observables were added, and none are proposed
here; the case's Pass/Fail criteria are fully satisfied by the existing
assertions.

## Gap assertions (what the implementer must add)

Single addition to `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`,
immediately above line 311 (or joining the existing decorator stack for
`test_attach_button_present_and_opens_picker`):

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1802_attach-button-present-and-opens-file-picker.md",
    "onetest-ai Test Case link",
)
```

Keep the existing `@allure.issue(..., "ELITEA-0577_...")` decorator in place
(the legacy case is still a valid, if untracked, ancestor) — this is
additive, not a replacement. No changes to test logic, page object, or
selectors are required; the live run this pass confirms the existing
implementation is correct and passing as-is.

Per `.agents/testing.md` § Coverage tagging, the implementer should also
back-write `automation_test_id =
tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantAttachments.test_attach_button_present_and_opens_picker`
to the ELITEA-1802 TMS case if the project's TMS adapter is wired for that
sync (see `.agents/test-automation.yaml`).

## Stable Handles (as currently implemented — informational, not new work)

All handles below are **existing raw locators**, and unlike other tech-debt
raw locators in this repo, they are **not remediable** via `add-data-testid`
— the Support Assistant widget renders from the third-party npm package
`@eliteaai/elitea-assistant`, not from first-party EliteaUI JSX source (see
Live Execution Evidence above). Cited for traceability only; **no new
locators are introduced by this extend**, so no testid work is in scope
here regardless.

| Element | Current handle | Type | Verified live this pass |
|---|---|---|---|
| Widget launcher | `button.elitea-assistant-button, button[aria-label="Support Assistant"]` (opened via `page.evaluate` JS click in `open_widget()`, not native Playwright click — MUI overlay intercept, see memory note) | CSS + JS-evaluate | yes — widget opened successfully this run |
| Widget title | `.elitea-assistant-header-title` | CSS | yes — `wait_for_widget_ready()` passed |
| Message input | `textbox[placeholder*="Type a message"]` / `get_by_placeholder("Type a message...")` fallback | Accessible-placeholder | yes |
| Attach file button | `button[aria-label="Attach file"]` (first) | ARIA label | yes — visible, clickable, native file-chooser opened |
| File-chooser event | `page.expect_file_chooser()` (Playwright native browser event, not app-specific) | Playwright API | yes — `FileChooser` object returned non-`None` |

## Cleanup

None required beyond pytest's automatic teardown. The temp file
(`tmp_path/test_attachment.txt`) is removed by pytest's `tmp_path` fixture
at test end (matches the case's own Postconditions). No chat/attachment
state persists server-side beyond the fresh Support Assistant session the
test opens and never returns to — no explicit cleanup call is present or
needed in the covering test.

## Known Defects Found

None. The flow works end-to-end on the live product right now (fresh run
this pass: 1 passed in 9.46s — attach button visible, native file-chooser
opened, file selected, network settled). The only gap identified is a
traceability/documentation gap in test metadata (missing `@allure.issue`
link to ELITEA-1802's own case file), not a product defect — no ticket
filed per `.agents/profile.md` § Bug filing (that policy covers product
defects; this is an automation metadata gap, tracked directly via the Gap
assertions section above and issue #110 itself).
