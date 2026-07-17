# Test Case: New Chat button creates fresh session and moves previous to history

## Metadata
- **TMS ID**: ELITEA-1799
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-1799_new-chat-creates-fresh-session.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/148
- **Priority**: l2 (case priority `high`; existing coverage lives in the `smoke` marker tier)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step needed; on deployed envs, `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- **Analyst**: qa-engineer (Sage)
- **Status**: defect-found

## Board Search Confirmation (Rule-6 traceability check)

Per the precedent set on `lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`
(a human-reviewer ruling on this same module): behavioral equivalence to an
existing test is not sufficient by itself to classify `already-covered` — the
correct test is whether this case's own tracked board task has ever reached
completion with delivered traceability.

- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-1799" --state all` →
  only **#148** — `[Automate][ELITEA-1799][support-assistant] New Chat button
  creates fresh session and moves previous to history`, state **OPEN**, board
  status **`In Progress`** (this very analyst task). No prior issue, closed or
  open, ever targeted ELITEA-1799.
- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-0641"` → **zero
  results**. ELITEA-0641 is the *legacy* onetest-ai case
  (`tests/elitea-platform/elitea-chat-bot/ELITEA-0641_clicking-new-chat-opens-a-clean-session-without-affecting-the-previous.md`)
  that the existing test currently cites via `@allure.issue` — it predates
  this repo's board-driven pipeline and was never tracked as a board task
  either.

**Conclusion:** the behavioral coverage that exists for steps 1–9 of this
flow is real (see Live Execution Evidence below) but was never delivered as
the outcome of a tracked task for ELITEA-1799 specifically — traceability is
missing, same gap shape as ELITEA-1796/1798/1801/1802. That alone would route
to `extend-existing`. However, this pass also surfaced a genuine product
defect against the case's own "Expected Final State" clause (previous session
preserved in history, not lost) — see Known Defects below — which takes
precedence for the overall classification per test-case-analysis SKILL.md §
Classify findings ("defect-found ... Automation paused until fix").

## Live Execution Evidence (this pass, 2026-07-17)

Ran the case manually end-to-end against the live local stack
(`http://localhost:5173/chat`, dev backend), fresh context, via Playwright MCP:

1. Navigated to `/chat`. Opened the Support Assistant widget via the
   documented JS-click workaround (`.agents/memory/qa-engineer/support_assistant_launcher_click_quirk.md`
   — native click on the launcher times out due to a MUI overlay
   intercept; `page.evaluate(...)` JS click works and is what
   `SupportAssistantPage.open_widget()` already does).
2. Widget opened onto a large, ever-accumulating conversation ("HI Chat",
   `uuid f53736b2-e54a-4c95-926d-318cc4483181`, backend `id 503`) — 100
   message wrappers visible (47 assistant / 53 user), spanning 2026-07-06
   through 2026-07-10, the residue of many prior QA passes on this same
   dev-token test user. Captured baseline: `assistantWrapperCount: 47`.
3. Sent the case's literal test message `"Test message before new chat"`.
   Waited (condition-based polling on `button[aria-label="Copy to
   clipboard"]` count, no fixed sleep) — response arrived in ~38 s (within
   the case's 60 s budget). `assistantWrapperCount` → 48, `allWrapperCount`
   100 → 102. **Case steps 5–7 confirmed.** Screenshot:
   `test-results/screenshots/ELITEA-1799-step1-response-received.png`.
4. Clicked "New Chat" (`aria-label="New chat"`, tooltip "New conversation").
   Immediately: `allWrapperCount` dropped from 102 to **1** — a single
   auto-generated assistant welcome message, `"Hello! How can I help you
   today with Elitea?"`. Old messages are gone from the active view; the
   widget is in a usable, ready state (title + input visible, input
   empty). **Case steps 8–9 and Expected-Final-State clauses 1–2
   confirmed.** Screenshot:
   `test-results/screenshots/ELITEA-1799-step2-new-chat-fresh-state.png`.
   Confirmed via `browser_network_requests` that the New Chat click fires
   **zero** network requests — it is a purely client-side view reset; the
   prior conversation (id 503) is left untouched server-side at this point.
5. Verified Expected-Final-State clause 3 ("previous session is preserved
   in history and not lost") — a real, discoverable affordance exists
   (`aria-label="Chat history"` button → dropdown of
   `button.elitea-assistant-history-item` entries, one of which is titled
   "HI Chat" and corresponds to conversation id 503). Selected it — see
   **Known Defects** below: the restored content is stale/truncated, not
   the live conversation.
6. Cross-checked via a second, independent path (no history interaction at
   all): a plain full-page reload of `/chat` + reopen widget. Result was
   byte-identical to the History-restore path — same 100 wrappers, same
   cutoff at "Jul 10, 9:29 AM". This rules out the History-restore code
   path specifically as the cause; the defect is in how the conversation
   is fetched/rendered, not in history selection.
7. Confirmed the defect is scoped to *large* conversations only: clicked
   New Chat again, sent a fresh probe message
   (`"ELITEA-1799 post-newchat probe message"`) — this **did** fire
   `POST /api/v2/support_assistant/conversations/` → `201 Created` with a
   brand-new `uuid 4f4c45e2-0e82-45d1-928f-76579df8cbde` (lazy conversation
   creation on first send after New Chat, not at the click itself), and
   the round trip (send → AI response) rendered correctly, because this
   new conversation is well under the ~100-group threshold.

No console errors were introduced by any Support Assistant interaction
itself. Pre-existing, unrelated console noise (CORS-blocked `dev.elitea.ai`
socket.io polling, 502/503s) comes from the main Chat page's own websocket
reconnect loop, not from the Support Assistant widget — consistent with the
"one pre-existing console warning, unrelated" note already on file from the
ELITEA-1798 pass; not investigated further as out of scope for this case.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; other
  envs: `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`).
- Support Assistant feature is enabled — confirmed live: launcher renders
  unconditionally on `/chat`.
- (New, discovered this pass — not in the original case) for the
  Expected-Final-State clause-3 defect to reproduce, the account's Support
  Assistant conversation must already exceed ~100 message groups. This
  test account's primary conversation (id 503) has 218, purely from
  repeated QA runs — a condition any long-lived, actively-used account
  will eventually reach, not a contrived setup.

## Test Data
### reuse-existing
- `${BASE_URL}` = `http://localhost:5173` (or the project's configured
  `APP_PREFIX`-aware base URL)
- Page under test: `/chat`
- Test message: `"Test message before new chat"` (matches case Test Data
  exactly; already hardcoded in the covering test — no new data needed)

(No generate-per-test or generate-shared-with-cleanup data — this flow only
sends a transient chat message; nothing persists that needs cleanup.)

## Test Steps
Same 9 steps as the source case (see case file); all executed live this
pass, see Live Execution Evidence above for outcomes.

## Expected Results
1. Old conversation messages no longer displayed in the main chat area
   after New Chat — **confirmed working**.
2. Widget enters a fresh state (welcome message) — **confirmed working**.
3. The previous session is preserved in history and not lost — **fails**
   for any conversation that has grown past ~100 message groups; see
   Known Defects.

## Coverage Map

### Axis 1 — case elements → disposition

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precond | User authenticated | dev-token auth works | `auth_state` fixture / `VITE_DEV_TOKEN` on localhost | conftest.py | covered |
| Precond | Support Assistant enabled | launcher renders | live observation this pass | manual snapshot, `/chat` | covered |
| 1 | Navigate to `/chat` | page loads | `chat_page.navigate_to_chat()` | existing test L186-187 | covered |
| 2 | Open Support Assistant widget | widget opens, title visible | `support_page.open_widget()` | existing test L188-189, page object L161 | covered |
| 3 | Wait for widget ready (title + input) | both visible | `support_page.wait_for_widget_ready()` | existing test L190 | covered |
| 4 | Record baseline assistant message count | count captured | `get_assistant_message_count()` | existing test L191 | covered |
| 5 | Send test message | text submitted via Send | `send_message()` | existing test L194, page object L193-221 | covered |
| 6 | Wait up to 60s for AI response | response rendered | `wait_for_response(timeout=AI_RESPONSE_TIMEOUT)` | existing test L195, page object L223-267 | covered |
| 7 | Assert new assistant message appeared | `count_before > initial_count` | explicit assert | existing test L196-197 | covered |
| 8 | Click New Chat | New Chat triggered, 1s + networkidle wait | `support_page.start_new_chat()` | existing test L199-200, page object L319-330 | covered |
| 9 | Wait for widget ready again | fresh/welcome state | `wait_for_widget_ready()` | existing test L203-204 | covered — **but see gap below**: existing test does not assert the message *count* actually reset, only that title+input are visible again |
| EFS-1 | Old messages no longer displayed | main view clears | *no current assertion* | — | **gap** — safe to add now (verified live: count resets from N to 1) |
| EFS-2 | Fresh/welcome state shown | welcome message renders | *no current assertion* | — | **gap** — safe to add now (verified live: auto-welcome message appears) |
| EFS-3 | Previous session preserved in history, not lost | history entry exists AND shows full/current content | *no current assertion; no code can satisfy this correctly right now* | — | **defect** — GH#607 filed; automation of this clause paused until fixed |
| — | Traceability: existing test's `@allure.issue` decorator only points at legacy ELITEA-0641, never ELITEA-1799 | `@allure.issue` should reference ELITEA-1799's own case file | not yet present | existing test L179 | **gap** — same shape as ELITEA-1796/1798/1801/1802 |

### Axis 2 — assertions beyond the case

- Verified the New Chat click fires **zero** network requests (pure
  client-side reset) — *added: this is the mechanism that explains why
  the old conversation isn't immediately "committed" as a distinct new
  backend session at click time; useful context for whoever fixes GH#607,
  and rules out a race-condition explanation for the truncation defect.*
- Verified a fresh, small conversation created after New Chat (well under
  the ~100-group cap) round-trips correctly (send → 201 Created → AI
  response) — *added: isolates the defect to conversation size, not to
  New Chat / History mechanics in general.*

## Cleanup
None required — this flow sends transient chat messages; nothing persists
that needs teardown beyond what the browser context already discards.
The probe conversation created during defect investigation
(`uuid 4f4c45e2-0e82-45d1-928f-76579df8cbde`) is a normal, harmless
Support Assistant conversation — no cleanup API exists for these (same as
sibling cases), left as-is per established convention.

## Concrete Handles (as currently implemented — informational, not new work)

All handles below are **existing, tech-debt raw locators** (predate the
testid-only policy; the Support Assistant widget is the third-party npm
package `@eliteaai/elitea-assistant`, mounted via
`[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx` — there is no
first-party EliteaUI JSX to attach a `data-testid` to, confirmed in
`.agents/memory/qa-engineer/support_assistant_launcher_click_quirk.md`).
Per this project's testid-only locator policy, every element below is a
**permanent scope exception**, not open tech debt — `add-data-testid`
cannot remediate a third-party package. Listed here per
`testid needed: {section}-{element}-{type}` convention where a first-party
testid would otherwise be expected; none is obtainable for this widget.

| Element | Current handle | Type | Verified live this pass |
|---|---|---|---|
| Launcher button | `button.elitea-assistant-button, button[aria-label="Support Assistant"]` (clicked via `page.evaluate` JS click — native click intercepted by a MUI overlay) | CSS + JS-evaluate (testid needed: `support-assistant-launcher-button`, unobtainable — third-party widget) | yes |
| Widget title | `.elitea-assistant-header-title` | CSS (testid needed: `support-assistant-widget-title`, unobtainable) | yes |
| Message input | `.elitea-assistant-input` / `textbox[placeholder*="Type a message"]` fallback | CSS / accessible-placeholder (testid needed: `support-assistant-message-input`, unobtainable) | yes |
| Send button | `button[aria-label="Send message"]` | ARIA label (testid needed: `support-assistant-send-button`, unobtainable) | yes |
| New Chat button | `button[aria-label="New chat"], button:has-text("New chat")` | ARIA label / text (testid needed: `support-assistant-new-chat`, unobtainable) | yes — case's own Test Data cites `data-testid="support-assistant-new-chat"`; **confirmed NOT present in the live DOM**, same case-text-drift pattern already on file for this module (ELITEA-1796's launcher/title/close testids don't exist either) |
| Chat history button | `button[aria-label="Chat history"], button:has-text("Chat history")` | ARIA label / text (testid needed: `support-assistant-history-button`, unobtainable) | yes |
| History session item | `button.elitea-assistant-history-item` | CSS (testid needed: `support-assistant-history-item`, unobtainable) | yes |
| Assistant message count | `.elitea-assistant-message-wrapper--assistant` (falls back to `button[aria-label="Copy to clipboard"]` count) | CSS | yes |
| Total message count | `.elitea-assistant-message-wrapper` | CSS | yes |

## Network Behavior
- Widget open / message send: `GET /api/v2/support_assistant/config/`,
  `GET /api/v2/support_assistant/conversations/` (list), AI response over
  the widget's own channel (not the main chat websocket).
- **New Chat click: no network request at all** (confirmed via
  `browser_network_requests` before/after) — purely a client-side state
  reset.
- First message sent *after* New Chat:
  `POST /api/v2/support_assistant/conversations/` → `201 Created` with a
  brand-new conversation `uuid`/`id` — conversation creation is lazy
  (happens on first send, not on the New Chat click itself).
- Conversation restore (History select, or default-active on page load):
  `GET /api/v2/support_assistant/conversation/{uuid}` — **no
  `limit`/`offset`/pagination query params on this request** — see Known
  Defects.

## Known Defects Found During Exploration

**[MAJOR] Support Assistant conversation restore truncates to the oldest
100 message groups, hiding all recent activity — filed as
[GH#607](https://github.com/EliteaAI/elitea-testing-public/issues/607).**

Directly breaks this case's own Expected-Final-State clause 3 ("the
previous session is preserved in history and not lost"). Evidence:

- `GET /api/v2/support_assistant/conversations/` (list endpoint) correctly
  reports the conversation's `updated_at` advancing and
  `message_groups_count` incrementing immediately after a send — the
  message groups genuinely are persisted server-side.
- `GET /api/v2/support_assistant/conversation/{uuid}` (the endpoint the
  widget calls to render a conversation, list or restore) returns
  `message_groups_count: 218` but a `message_groups` array of only
  **100** items — and those 100 are the chronologically **oldest** ones
  (last array item dated 2026-07-10, five days stale relative to the
  2026-07-17 test run). No pagination params are sent on the request, so
  there is no way for the widget to reach the tail.
- Reproduced identically via two independent UI paths: (a) Chat History →
  select the affected entry, (b) a fresh full-page reload with zero
  history interaction. Both return byte-identical stale/truncated
  content, ruling out a History-selection-specific bug.
- Confirmed **scoped to large conversations only**: a brand-new
  conversation created after a New Chat click (well under the ~100-group
  cap) sends/receives correctly and shows all its own messages — the
  send→response round trip itself is not broken.
- Evidence files: `test-results/json/ELITEA-1799-conversation-f53736b2-truncated-response.json`
  (full captured response body), `test-results/screenshots/ELITEA-1799-step2-new-chat-fresh-state.png`,
  `test-results/screenshots/ELITEA-1799-step3-new-conversation-created-after-send.png`.

**Automation impact:** per test-case-analysis SKILL.md § Classify findings,
a confirmed product defect against the case's own contract routes the
whole case to `defect-found` (automation of the failing assertion paused
until fixed), even though the rest of the flow (steps 1–9) works and is
already behaviorally covered by the existing test. See Automation Hints
for what can safely proceed now vs. what must wait.

No other defects found. The case-text drift on the `New Chat` button's
`data-testid` (case cites `support-assistant-new-chat`, not present in
the live DOM — same pattern already on file for this module's launcher/
title/close testids) is CLARIFICATION-class, not a product defect: the
product's own fallback selector (`aria-label="New chat"`) works
correctly and is what the existing automation already uses.

## Blocked Steps
None outright blocked — every case step (1–9) executed to completion.
Expected-Final-State clause 3 could not be **asserted as passing**
(defect, not a blocker) — see Known Defects.

## Automation Hints
- **Safe to proceed now** (independent of GH#607):
  1. Add a third `@allure.issue(...)` decorator to
     `TestSupportAssistantNewSession.test_new_chat_creates_fresh_session`
     in `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
     (currently only L179, pointing at legacy ELITEA-0641), pointing at
     ELITEA-1799's own case file — same "coverage tag chain" mechanic used
     for ELITEA-1796/1798/1801/1802:
     ```python
     @allure.issue(
         "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1799_new-chat-creates-fresh-session.md",
         "onetest-ai Test Case link",
     )
     ```
  2. Strengthen Step 4-5's assertion (test L203-204) to also assert the
     message count actually reset (EFS-1/EFS-2 from the Coverage Map),
     e.g. `assert support_page.get_message_count() < count_before` (or
     `== 1` for the single welcome message) immediately after
     `wait_for_widget_ready()`. This is verified-passing behavior on the
     live product — safe to lock in now.
- **Paused pending GH#607**: do NOT add an assertion for "history
  preserves the full previous session" yet. Asserting the *current*
  (truncated) behavior would be reverse-masking a real defect; asserting
  the *correct* behavior would fail deterministically against today's
  product for any account whose Support Assistant conversation has grown
  past ~100 message groups (which real accounts, including this project's
  own shared test user, do reach). Once GH#607 lands, add: open History →
  select the session pushed there by New Chat → assert the message
  immediately preceding New Chat (and its AI response) are both visible
  in the restored view.
- Framework/page object: no new locators needed; existing
  `SupportAssistantPage` (`open_widget`, `send_message`, `wait_for_response`,
  `start_new_chat`, `open_history`, `get_history_session_count`,
  `select_history_session`, `get_assistant_message_count`,
  `get_message_count`) already covers everything steps 1–9 need.
- **TMS back-write** (orchestrator, post-merge, per `.agents/testing.md` §
  Coverage tagging): once the traceability gap-assertion above merges,
  back-write `automation_test_id:
  tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantNewSession.test_new_chat_creates_fresh_session`
  to ELITEA-1799 — but leave `status: draft` (not `ready`) until GH#607 is
  resolved and the history-preservation assertion is actually added,
  since the case's own Expected Final State is not yet fully verified
  true against the live product.
