# Test Case: History restore — open previous session and continue messaging

## Metadata
- **TMS ID**: ELITEA-1800
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/support-assistant/ELITEA-1800_history-restore-and-continue-messaging.md`
- **Linked Story**: https://github.com/EliteaAI/elitea-testing-public/issues/177
- **Priority**: l2 (case priority `high`; existing coverage lives in the `smoke` marker tier)
- **Environment Explored**: local (`http://localhost:5173/chat`, EliteaUI `automation/testids`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token — no explicit login step needed; on deployed envs, `auth_state` fixture pre-loads via `TEST_USER_EMAIL`/`TEST_USER_PASSWORD`)
- **Analyst**: qa-engineer (Sage)
- **Status**: extend-existing

## Board Search Confirmation (Rule-6 traceability check)

Per the precedent set on `lextend_launcher-visible-widget-opens-and-closes_ELITEA-1796.md`
(a human-reviewer ruling on this same module, reaffirmed on ELITEA-1798/1799/1801/1802):
behavioral equivalence to an existing test is not sufficient by itself to classify
`already-covered` — the correct test is whether this case's own tracked board task
has ever reached completion with delivered traceability. This case was pre-flagged
by the orchestrator (issue #177 comment) as a candidate `already-covered` given the
existing test's near-identical steps and identical test-data strings — but the same
gap the reviewer found on ELITEA-1796 applies here too:

- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-1800" --state all` →
  only **#177** — `[Automate][ELITEA-1800][support-assistant] History restore —
  open previous session and continue messaging`, state **OPEN**, board status
  **`In Progress`** (this very analyst task). No prior issue, closed or open,
  ever targeted ELITEA-1800.
- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-0641" --state all` →
  only **#177** (fuzzy text match on this issue's own body, not a dedicated
  issue). ELITEA-0641 is the *legacy* onetest-ai case
  (`tests/elitea-platform/elitea-chat-bot/ELITEA-0641_clicking-new-chat-opens-a-clean-session-without-affecting-the-previous.md`)
  currently cited by the existing test's `@allure.issue` decorator — it predates
  this repo's board-driven pipeline and was never tracked as a board task either.
- `env -u GITHUB_TOKEN gh issue list --search "ELITEA-0643" --state all` →
  same result, only **#177**. ELITEA-0643
  (`tests/elitea-platform/elitea-chat-bot/ELITEA-0643_conversation-is-retained-when-the-support-assistant-panel-is-closed-an.md`)
  is the second legacy case the existing test cites — also never tracked.

**Conclusion:** the behavioral coverage that exists for all 15 steps of this flow
is real and confirmed correct against the live product (see Live Execution
Evidence below), but — same as every other case in this module — it was never
delivered as the outcome of a tracked task for ELITEA-1800 specifically.
Traceability from ELITEA-1800 to its automation is missing. That gap is a
single, well-defined code change (one `@allure.issue` line), not a rewrite —
hence `extend-existing`, not `already-covered` and not `ready-for-automation`,
consistent with the module-wide precedent.

## Covering Test (behavioral proof)

- **File**: `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`
- **Class**: `TestSupportAssistantHistory` (line 299)
- **Test**: `test_history_restore_and_continue` — **line 310** (existing
  `@allure.issue` decorators at lines 308–309, pointing only at legacy cases
  ELITEA-0641 and ELITEA-0643)
- **Page object**: `automation/pages/support_assistant_page.py` —
  `open_widget()` (L161), `wait_for_widget_ready()` (L466), `send_message()`
  (L193), `wait_for_response()` (L223), `start_new_chat()` (L319),
  `open_history()` (L332), `get_history_session_count()` (L344),
  `select_history_session()` (L361), `get_assistant_message_count()` (L281)

**Behavioral-equivalence argument.** The covering test performs, in order:
open the Support Assistant widget on `/chat` → wait for it to be ready →
capture `initial_count = get_assistant_message_count()` (case Step 4) → send
the literal message `"History test message - distinctive content 12345"`
(character-for-character identical to the case's Test Data, case Step 5) via
`send_message()` → `wait_for_response(timeout=AI_RESPONSE_TIMEOUT)` where
`AI_RESPONSE_TIMEOUT = 60_000`, matching the case's 60 s budget exactly (case
Step 6) → `start_new_chat()` (case Step 7) → `page.wait_for_timeout(1000)`
(case Step 8, literal 1 s wait) → `open_history()`, which internally waits
500 ms for the panel transition (case Step 9) → `assert session_count >= 1`
via `get_history_session_count()` (case Step 10 — the first of the two
count-based assertions the orchestrator flagged) → `select_history_session(index=0)`,
which internally waits for skeleton rows to clear and calls
`self.wait_for_network()` (networkidle), matching case Step 11's "network
idle is reached" expected result exactly → `assert restored_count > 0` via
`get_assistant_message_count()` (case Step 12 — the second flagged
count-based assertion) → send the literal follow-up
`"Follow-up message after restore"` (case Step 13, exact string match) →
`wait_for_response(initial_count=restored_count, timeout=AI_RESPONSE_TIMEOUT)`
(case Step 14) → `assert final_count > restored_count` (case Step 15 — the
third flagged assertion). Every one of the case's 15 steps maps onto an
executed action or assertion in the covering test; no case step is left
unexercised, and both negative/count-based assertions the orchestrator asked
me to specifically verify (Steps 10, 12, 15) are present and match the case's
own Expected Result wording exactly.

## Live Execution Evidence (this pass, 2026-07-18)

Ran the case fresh, end-to-end, against the live local stack
(`http://localhost:5173/chat`, dev backend), via Playwright MCP — not
assumed from the covering test's code, actually driven:

1. Navigated to `/chat` (case Step 1) — page loaded successfully.
2. Opened the Support Assistant widget via the documented
   `page.evaluate()` JS-click workaround (native click intercepted by a MUI
   overlay — same quirk already on file from prior passes on this module,
   `.agents/memory/qa-engineer/support_assistant_launcher_click_quirk.md`).
   Widget opened onto an existing conversation from prior QA runs
   ("ELITEA-1799 post-newchat probe message" thread) — baseline
   `assistantWrapperCount: 19` captured (case Steps 2–4).
3. Sent `"History test message - distinctive content 12345"` (case Step 5).
   Polled `.elitea-assistant-message-wrapper--assistant` count +
   `.elitea-assistant-status-chip--active` (condition-based, no fixed
   sleep) — response completed in ~26 s (within the 60 s budget).
   `assistantCount` 19 → 20, `copyButtonCount` 18 → 19. **Case Step 6
   confirmed.** Screenshot: `test-results/screenshots/ELITEA-1800-step5-6-waiting-response.png`.
4. Clicked "New Chat" (case Step 7). Waited 1 s (case Step 8). Verified via
   `evaluate()` that the widget reset to a single welcome-message wrapper
   (`totalCount: 1`) — matches the fresh-session behavior already documented
   for ELITEA-1799.
5. Clicked "Chat history" (case Step 9) — panel opened, 500 ms transition
   observed live. Queried `button.elitea-assistant-history-item` — **20
   sessions**, index 0 = `"ELITEA-1799 post-newchat probe message"` (the
   session just pushed to history by this pass's own New Chat click).
   **Case Step 10 confirmed** (`session_count >= 1`, actual 20). Screenshot:
   `test-results/screenshots/ELITEA-1800-step9-10-history-panel-open.png`.
6. Selected index 0 (case Step 11). Waited for skeleton rows to clear
   (0 skeleton rows post-load) and confirmed via `browser_network_requests`
   that `GET /api/v2/support_assistant/conversation/4f4c45e2-...` fired and
   returned `200 OK` (networkidle reached, matching the case's Step 11
   expected result). Restored session showed `assistantCount: 20`,
   `totalCount: 40` — **case Step 12 confirmed** (`restored_count > 0`).
   Cross-checked content integrity: the restored session's last paragraph
   (`"I don't retain prior turns unless their content is included again in
   the current message, so I can only use what's pasted here."`) is
   byte-identical to the response captured live in step 3 above — the
   restore is NOT truncated for this conversation (see Known Defects → GH#607
   relevance check below). Screenshot: `test-results/screenshots/ELITEA-1800-step11-12-restored-session.png`.
7. Sent `"Follow-up message after restore"` in the restored session (case
   Step 13). Polled the same way as step 3 — response completed in ~18 s.
   `assistantCount` 20 → 21, spinner cleared. **Case Steps 14–15 confirmed**
   (`final_count (21) > restored_count (20)`). Screenshot:
   `test-results/screenshots/ELITEA-1800-step13-15-followup-response.png`.

**All 15 case steps executed and confirmed passing against the live
product**, matching exactly what the covering test already asserts.

### GH#607 relevance check (known defect, per orchestrator's explicit ask)

Checked whether [GH#607](https://github.com/EliteaAI/elitea-testing-public/issues/607)
("Support Assistant conversation restore truncates to the oldest 100 message
groups") is relevant to this case. **Re-verified live during the PR #626
fix-only round** (2026-07-18) after review flagged the original version of
this subsection as reversing GH#607's truncation direction and
self-contradicting on session size. Both are corrected below, backed by a
fresh live reproduction — not just re-worded.

**The session this case restores is a shared, cross-run, ever-growing
dev-token conversation — not bounded to a single run's own sends — but
ELITEA-1800's own assertions are still safe from GH#607, for a verified
structural reason, not because the session stays small:**

- The session `select_history_session(index=0)` restores is whatever
  conversation was already active/default when the widget opened for this
  run — the same shared dev-token conversation reused across every automated
  pass against this module (no per-test creation, no cleanup — consistent
  with this AFS's own § Cleanup: "nothing persists that needs teardown"). It
  is **not** bounded to "this run's own 1–2 message pairs": confirmed live
  the day of the original pass it already held 20 assistant messages: during
  this fix-only round it has grown to **50 message groups** (id 548, uuid
  `4f4c45e2-…`) — climbing toward, not safely under, GH#607's ~100-group
  threshold, and it will keep growing with every future run against this
  module. Any safety argument resting on "the session is too small to
  trigger GH#607" is therefore false on its face and was removed.
- **GH#607's actual failure direction** (re-verified live this round
  directly against the exact conversation the issue documents — id 503, uuid
  `f53736b2-e54a-4c95-926d-318cc4483181`, 218 total message groups):
  `GET /api/v2/support_assistant/conversation/{uuid}` returns exactly the
  **oldest** 100 message groups (`created_at` ascending; last returned item
  dated 2026-07-10, stale relative to the 2026-07-18 probe) and silently
  drops every group after that. **It drops the newest groups and keeps the
  oldest ~100** — matching the issue's own title exactly. (A prior version of
  this bullet had this backwards — "dropping the oldest groups, keeping the
  newest ~100" — directly contradicting this section's own opening line;
  corrected here.)
- **Why the delta assertion survives truncation anyway (verified, not
  assumed):** `select_history_session()` fires the truncating GET exactly
  once, to establish whatever `restored_count` ends up being — truncated or
  not doesn't matter here, because Step 15 never checks that count against an
  absolute floor or exact content, only that a *later* count exceeds it. The
  follow-up send (`send_message()` + `wait_for_response()`) does **not**
  re-fire that GET — confirmed via a live network capture during this
  fix-only round (zero additional `GET .../conversation/{uuid}` calls during
  or after the send); the new user message and AI response are appended
  directly to the already-rendered DOM instead. **Directly reproduced against
  the real GH#607-truncated conversation** (id 503 above) to remove doubt:
  force-restored it via the widget's own history panel, observed the DOM
  render exactly 100 truncated message wrappers (`restored_count` = 47
  assistant messages — GH#607 reproducing live, as expected), sent a
  follow-up message through the real UI, and watched the count settle at
  `final_count` = 48 — `final_count > restored_count` (48 > 47) **held true**
  under genuine, currently-reproducing truncation, with no re-fetch of the
  conversation occurring at any point after the initial restore.
- This safety is an implementation detail of the current widget (appends on
  send, never re-fetches), verified today — not an inherent property of a
  count-based assertion shape alone. If the widget is ever changed to
  re-fetch the full conversation after every send, this reasoning would need
  re-verification, since a re-fetch would reapply the same fixed oldest-100
  window and could leave `final_count` unchanged (no such re-fetch was
  observed in the current implementation).

GH#607 remains open and unresolved; this finding does not change that — it
only establishes that ELITEA-1800's specific assertions are, today, verified
safe from it, including once the shared session it restores eventually
crosses the truncation threshold.

### Additional findings during this pass

1. **[MINOR, filed]** A React "Cannot update a component (`ChatWindow`) while
   rendering a different component (`AnimatedMessage`)" console error fired
   once, at the moment the first AI response finished rendering (did not
   recur on the second response in the same session). Traced to the
   third-party `@eliteaai/elitea-assistant` package, not first-party EliteaUI
   code. No functional impact observed — filed as
   [GH#625](https://github.com/EliteaAI/elitea-testing-public/issues/625)
   per this project's "file every finding" policy; does not block this
   case's classification (cosmetic, third-party, no assertion in this case
   or the covering test touches console state).
2. **[Automation-code note, not a product defect — flagging for the team,
   not filed as a tracker bug]** `SupportAssistantPage.get_last_message_text()`
   (page object L305-317) queries `.elitea-assistant-widget p`, but the live
   DOM's actual container class is `.elitea-assistant-window` —
   `.elitea-assistant-widget` matches **zero** elements. Verified live via
   `document.querySelector('.elitea-assistant-widget p')` → 0 results, vs.
   `document.querySelector('.elitea-assistant-window').querySelectorAll('p')`
   → 25 results with the expected last-paragraph text. This method always
   returns `""`. It is **not called** by `test_history_restore_and_continue`
   (this case's covering test only uses `get_assistant_message_count()`), so
   it does not affect ELITEA-1800. It **is** called by
   `test_new_chat_creates_fresh_session` (ELITEA-1799's covering test) inside
   the `soft_failures` GH#607 regression-net check
   (`restored_last_message != response_before_new_chat`) — since both sides
   of that comparison always evaluate to `""`, the text-comparison half of
   that check is permanently inert (`"" != ""` is always `False`), leaving
   only the count-based half (`restored_message_count < total_count_before`)
   actually functional. This does not change ELITEA-1799's current
   pass/fail outcome (the count-based half is unaffected and already carries
   the real signal), but it is a latent gap in that test's defect-detection
   power worth a follow-up fix (correct the selector to
   `.elitea-assistant-window p`, scoped the same way this AFS's own
   verification did). Surfacing this to the orchestrator/lead directly
   rather than filing a tracker bug, since it's an automation-code
   correctness issue, not a product defect, and out of this case's own
   scope to fix.
3. Cosmetic-only: the restored message's timestamp render differs from what
   was shown live immediately before New Chat (`"9:40 PM"` live →
   `"6:40 PM"` after restore, for the same message) — a timezone/formatting
   artifact in how the widget re-renders history timestamps, not covered by
   any assertion in this case or its covering test. Noted for awareness
   only, not investigated further (out of scope for a traceability-only
   extend).

No console errors were introduced by the History flow's own actions beyond
finding #1 above; the pre-existing "Module 'stream' externalized" warning
(unrelated third-party bundling notice) was also present, consistent with
prior passes on this module.

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
- Initial message: `"History test message - distinctive content 12345"`
  (matches case Test Data exactly; already hardcoded in the covering test)
- Follow-up message: `"Follow-up message after restore"` (matches case Test
  Data exactly; already hardcoded in the covering test)

(No generate-per-test or generate-shared-with-cleanup data — this flow only
sends transient chat messages; nothing persists that needs cleanup beyond
what the browser context already discards.)

## Coverage Map

### Axis 1 — case elements → disposition

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Precond | User authenticated | dev-token auth works | `auth_state` fixture / `VITE_DEV_TOKEN` on localhost | conftest.py | covered |
| Precond | Support Assistant enabled | launcher renders | live observation this pass | manual snapshot, `/chat` | covered |
| 1 | Navigate to `/chat` | page loads | `chat_page.navigate_to_chat()` | test L316-317 | covered |
| 2 | Open Support Assistant widget | widget opens, title visible | `support_page.open_widget()` | test L319, page object L161 | covered |
| 3 | Wait for widget ready | title + input visible | `support_page.wait_for_widget_ready()` | test L320 | covered |
| 4 | Record baseline assistant message count | count captured | `get_assistant_message_count()` | test L321 | covered |
| 5 | Send initial message | text submitted | `send_message(distinctive_message)` | test L325, page object L193-221 | covered |
| 6 | Wait up to 60s for AI response | new assistant message appears | `wait_for_response(timeout=AI_RESPONSE_TIMEOUT)` | test L326, page object L223-267 | covered |
| 7 | Click New Chat | session pushed to history, new session starts | `support_page.start_new_chat()` | test L329, page object L319-330 | covered |
| 8 | Wait 1s for session transition | transition completes | `page.wait_for_timeout(1000)` | test L330 | covered |
| 9 | Click History button | history panel opens, 0.5s transition | `support_page.open_history()` | test L333, page object L332-342 | covered |
| 10 | Assert history session count >= 1 | `get_history_session_count() >= 1` | explicit assert | test L334-337 | covered |
| 11 | Select session index 0 | session loads, network idle reached | `select_history_session(index=0)` | test L340, page object L361-399 | covered |
| 12 | Assert restored assistant message count > 0 | `get_assistant_message_count() > 0` | explicit assert | test L343-346 | covered |
| 13 | Send follow-up message | text submitted in restored session | `send_message("Follow-up message after restore")` | test L349 | covered |
| 14 | Wait up to 60s for new AI response | new assistant message beyond restored count | `wait_for_response(initial_count=restored_count, timeout=AI_RESPONSE_TIMEOUT)` | test L350 | covered |
| 15 | Assert restored session count increases | `get_assistant_message_count() > restored_count` | explicit assert | test L351-353 | covered |
| — | Traceability: existing test's `@allure.issue` decorators only point at legacy ELITEA-0641/ELITEA-0643, never ELITEA-1800 | `@allure.issue` should reference ELITEA-1800's own case file | not yet present | test L308-309 | **gap** — same shape as ELITEA-1796/1798/1799/1801/1802 |

### Axis 2 — assertions beyond the case

None new. The covering test asserts exactly the case's Pass/Fail criteria
(session count ≥ 1, restored session non-empty, follow-up count increase) —
no additional observables were added, and none are proposed here; the GH#607
relevance check above confirms no regression-net assertion is warranted for
this specific case (see reasoning there).

## Gap assertions (what the implementer must add)

Single addition to `automation/tests/ui/support_assistant/test_support_assistant_smoke.py`,
immediately above line 308 (or joining the existing decorator stack for
`test_history_restore_and_continue`):

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-1800_history-restore-and-continue-messaging.md",
    "onetest-ai Test Case link",
)
```

Keep the existing two `@allure.issue(..., "ELITEA-0641_..."/"ELITEA-0643_...")`
decorators in place (the legacy cases are still valid, if untracked,
ancestors) — this is additive, not a replacement. No changes to test logic,
page object, or selectors are required; the live run this pass confirms the
existing implementation is correct and passing as-is for all 15 steps.

Per `.agents/testing.md` § Coverage tagging, the implementer should also
back-write `automation_test_id =
tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantHistory.test_history_restore_and_continue`
to the ELITEA-1800 TMS case if the project's TMS adapter is wired for that
sync (see `.agents/test-automation.yaml`).

**Separately (not part of this gap, flagged for the lead's own backlog):**
consider a follow-up fix to `SupportAssistantPage.get_last_message_text()`
(L312) — selector `.elitea-assistant-widget p` should be
`.elitea-assistant-window p` (see Additional findings #2 above). Not part of
ELITEA-1800's own scope (the method isn't used by this case's covering
test) — surfaced here only because it was discovered during this pass's live
verification.

## Stable Handles (as currently implemented — informational, not new work)

All handles below are **existing, tech-debt raw locators** (predate the
testid-only policy; tracked as tech debt per `.agents/testing.md` § Locator
policy, issues #25/#42; the Support Assistant widget is the third-party npm
package `@eliteaai/elitea-assistant` — no first-party EliteaUI JSX to attach
a `data-testid` to). **No new locators are introduced by this extend**, so no
testid work is in scope here per the "scope is load-bearing" rule (testids
go only on elements a test newly touches; this extend touches zero new
elements).

| Element | Current handle | Type | Verified live this pass |
|---|---|---|---|
| Launcher button | `button.elitea-assistant-button, button[aria-label="Support Assistant"]` (JS-evaluate click, MUI overlay intercepts native click) | CSS + JS-evaluate | yes |
| Widget title | `.elitea-assistant-header-title` | CSS | yes |
| Message input | `.elitea-assistant-input` / `textbox[placeholder*="Type a message"]` fallback | CSS / accessible-placeholder | yes |
| Send button | `button[aria-label="Send message"]` | ARIA label | yes |
| New Chat button | `button[aria-label="New chat"], button:has-text("New chat")` | ARIA label / text | yes |
| Chat history button | `button[aria-label="Chat history"], button:has-text("Chat history")` | ARIA label / text | yes |
| History session item | `button.elitea-assistant-history-item` | CSS | yes — 20 sessions observed, index 0 = most recently archived |
| Skeleton loading row | `.elitea-assistant-skeleton-row` | CSS | yes — 0 present post-load (load was fast enough not to render skeleton) |
| Assistant message count | `.elitea-assistant-message-wrapper--assistant` (falls back to `button[aria-label="Copy to clipboard"]` count) | CSS | yes |
| Total message count | `.elitea-assistant-message-wrapper` | CSS | yes |
| Active response spinner | `.elitea-assistant-status-chip--active` | CSS | yes |

## Network Behavior
- Widget open / message send: `GET /api/v2/support_assistant/config/`,
  `GET /api/v2/support_assistant/conversations/` (list).
- New Chat click: no network request (client-side reset), consistent with
  ELITEA-1799's documented finding.
- History session select (case Step 11): `GET
  /api/v2/support_assistant/conversation/{uuid}` → `200 OK` — confirmed live
  this pass (`.../conversation/4f4c45e2-0e82-45d1-928f-76579df8cbde`).
- Follow-up message send (case Step 13): AI response streamed over the
  widget's own channel; no new conversation `POST` (follow-up reuses the
  already-active restored conversation, unlike a fresh New Chat send).

## Cleanup
None required — this flow sends transient chat messages within an existing
shared dev-token conversation; nothing persists that needs teardown beyond
what the browser context already discards.

## Known Defects Found During Exploration

**[MINOR, filed as GH#625]** React "setState during render" console error
(`ChatWindow`/`AnimatedMessage`) — see Additional findings #1 above. Does
not block this case's classification.

**GH#607** (Support Assistant conversation restore truncation) — checked for
relevance per the orchestrator's explicit ask. The shared session this case
restores has not yet crossed the ~100-group truncation threshold (50 groups
as of this fix-only round, growing every run) — but even once it does,
GH#607 cannot block this case's Pass/Fail criteria, verified by direct live
reproduction against the actual GH#607-truncated conversation from the issue
itself, not by assuming the session stays small. See the dedicated "GH#607
relevance check" subsection above. GH#607 itself remains open and
unresolved; no action needed against it from this case.

No other product defects found. All 15 case steps + both flagged
count-based assertions (Steps 10, 12, 15) executed and passed against the
live product.

## Blocked Steps
None. All 15 case steps executed to completion this pass.

## Automation Hints
- **Safe to proceed now:**
  1. Add the third `@allure.issue(...)` decorator (see Gap assertions above)
     to `TestSupportAssistantHistory.test_history_restore_and_continue` —
     same "coverage tag chain" mechanic used for
     ELITEA-1796/1798/1799/1801/1802.
  2. No test-logic, page-object, or selector changes needed — this pass's
     live execution confirms the existing implementation is fully correct
     for all 15 steps.
- Framework/page object: no new locators needed and none added; existing
  `SupportAssistantPage` methods already cover everything this case's 15
  steps require.
- **TMS back-write** (orchestrator, post-merge, per `.agents/testing.md` §
  Coverage tagging): once this PR merges, back-write `automation_test_id:
  tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantHistory.test_history_restore_and_continue`
  to ELITEA-1800, `status: ready` (the case's own Expected Final State is
  fully verified true against the live product — no open defect blocks it,
  unlike ELITEA-1799).
