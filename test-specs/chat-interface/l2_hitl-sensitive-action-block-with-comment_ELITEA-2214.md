# Test Case: Chat – HITL Authorization – Block with Comment Records the Reason and Blocks the Toolkit Action

## Metadata
- **TMS ID**: ELITEA-2214
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local for the toolkit-call/chip mechanics;
  source-verified (`BlockWithCommentControl.jsx`) for the comment control
  itself. See ELITEA-2211 § Preconditions for the shared environment note.
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: extend-existing (REWORKED 2026-08-27 — see § REWORK at the end of
  this file; the merged spec needs a corrected + reordered assertion set, two new
  assertions, and is sanctioned-RED on OPEN #1834 / #1835). The original
  2026-08-03 pass below is kept verbatim as the historical record; where it
  disagrees with § REWORK, **§ REWORK wins** — notably its step 5, whose
  assertion is UNREACHABLE as merged, and its claim that the LLM-response
  wording was merely "unverified" (there is no LLM response at all).

## Preconditions
Same as ELITEA-2213 — own fresh authorization-card instance.

## Test Data
- Same fixture shape as ELITEA-2211/2212/2213.
- Block comment: `"This action is too risky and could delete important data"`
  (case's literal text) — source-confirmed the control caps input at 2000
  chars (`BlockWithCommentControl.jsx:9`, `MAX_COMMENT_LENGTH`), so this
  string is well within range, no truncation risk.

## Test Steps
1. Reach the authorization card (own fresh conversation).
2. Click "Block with Comment" (collapsed-state trigger — source:
   `BlockWithCommentControl.jsx:71-82`, `variant="secondary"` = gray, **no
   testid today**).
   - **Verify**: an inline textarea + Cancel/submit-"Block with Comment"
     button pair appears IN PLACE on the card (source: the component swaps
     its OWN return branch on `open` state — this is NOT the
     conditional-testid-pair pattern from canon ruling #277, since these are
     two entirely separate DOM subtrees on different `open` states of the
     SAME component, not a same-element ternary; each needs its own testid).
3. Type the comment into the textarea.
   - **Verify**: textarea value updates (React-controlled — use `.fill()`
     then confirm via the input's own value, or `press_sequentially` per
     `.claude/rules/mui-patterns.md` if `.fill()` doesn't register — this
     is a plain MUI `TextField`, same pattern as other MUI form fields in
     this project).
4. Click Submit (the expanded-state's own "Block with Comment" button,
   `BlockWithCommentControl.jsx:110-118` — **note: SAME visible label text
   as the collapsed trigger from step 2, but a DIFFERENT DOM element** —
   disambiguate by testid, not text, once both have one).
   - **Verify**: `handleSubmit` fires only when `trimmedComment` is
     non-empty (`BlockWithCommentControl.jsx:51-56`) — calls
     `onSubmit(trimmedComment)` which the parent wires to
     `onHitlResume({action: 'block_with_comment', value: comment, toolCallId, interruptId})`
     (`ChatHitlActions.jsx:111-116`); textarea + comment-input UI collapses
     back (`setOpen(false)`).
5. Verify the toolkit tool does NOT execute.
   - **Verify**: file still present in the bucket (`ArtifactAPI.list_bucket_files`)
     — same backend-verified non-execution pattern as ELITEA-2213.
6. Verify the LLM response acknowledges the block.
   - **Verify**: same loose non-empty/non-success signal as ELITEA-2213
     step 4 — exact wording unverified live (precondition unreachable
     locally).

## Expected Results
- Block with Comment records the typed reason, sends it as
  `denial_reason` (per `BlockWithCommentControl.jsx`'s own docstring,
  line 18-19) and prevents execution.
- File remains present (backend-verified).
- LLM response acknowledges the block.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click Block with Comment | modal/input appears | step 2 | step 2 | asserted |
| 2 Type comment | comment entered | step 3 | step 3 | asserted |
| 3 Click Submit/Confirm | modal closes, card updates, blocked | step 4 | step 4 | asserted |
| 4 Tool does NOT execute | no execution | step 5 | step 5 (backend file-listing) | asserted |
| 5 LLM response acknowledges block | response about block | step 6 | step 6 (loose signal, see ELITEA-2213's equivalent note) | asserted *(clarification: exact wording unverified, see note)* |

**Axis 2 — Analyst additions:**
- Same backend-verified non-execution rationale as ELITEA-2213 — *added:
  ground-truth proof beats a UI-only "card closed" signal.*
- Note the case's own text calls this a "Modal" — source confirms it's an
  INLINE expansion on the same card (`BlockWithCommentControl.jsx`'s
  `Collapse`-free conditional render, not an MUI `Dialog`/`role="dialog"`)
  — *added: flagging so the implementer doesn't hunt for a `[role="dialog"]`
  that doesn't exist here; this is case-text imprecision, not a defect
  (the observable — "an input appears, submitting blocks the action" — is
  unaffected).*

## Cleanup
Same as ELITEA-2211/2212/2213.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Block with Comment (collapsed trigger) | **testid needed**: `sensitive-action-block-with-comment-button` — `BlockWithCommentControl.jsx:73` (`!open` branch) | none |
| Comment textarea | **testid needed**: `sensitive-action-block-comment-input` — `BlockWithCommentControl.jsx:87` `TextField` | none |
| Cancel button (expanded state) | **testid needed**: `sensitive-action-block-comment-cancel-button` — `BlockWithCommentControl.jsx:103` | none — not asserted by this case's steps, but the sibling to the Submit button worth naming while in there (implementer's call whether in-scope; this case's OWN executed path doesn't click Cancel, so per the testid-scope rule, only add it if a case actually exercises it — otherwise leave to a future case) |
| Submit button (expanded state) | **testid needed**: `sensitive-action-block-comment-submit-button` — `BlockWithCommentControl.jsx:110` (same visible text as the collapsed trigger — testid is the only reliable disambiguator) | none |
| Bucket file-listing (non-execution proof) | `ArtifactAPI.list_bucket_files(bucket_name)` | none |

## Network Behavior
Resume action `onHitlResume({action: 'block_with_comment', value: comment, ...})`
— actual frame shape not captured live (see ELITEA-2211's note).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None beyond the shared precondition constraint (see ELITEA-2211).

## Automation Hints
- Same markers as the rest of the cluster.
- Do NOT add the Cancel-button testid unless this test (or a sibling in the
  same PR) actually clicks Cancel — per `.agents/role-overrides.md` §
  Every role locator policy, "touches" = the test's executed code path,
  not "plausible future use."

---

# REWORK — 2026-08-27 (live re-analysis, analyst slot)

**Status after this pass: `extend-existing`** — this case's spec is already merged
(`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionBlockWithComment::test_block_with_comment_records_reason_and_blocks_action`,
on `automation/base`). The gap is a corrected + reordered assertion set plus two new
assertions, not a new spec. Sanctioned-RED on the OPEN defects **#1834** and **#1835**
(`.agents/testing.md` § Merge gate — sanctioned-RED, closed-set variant + analysis-time
entry): every corrected assertion states the CORRECT behaviour and flips green unchanged
when the product is fixed.

## Why this pass happened

Three defects were handed over from the ELITEA-2213 delivery (#416 / PR #1840):

1. **The case's PRIMARY OBSERVABLE has never been evaluated.** In the merged test, the
   backend ground-truth read sits BEHIND `chat.wait_for_message_content_stable(...)`:

   ```python
   chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=CHAT_RESPONSE_TIMEOUT)
   remaining_files = artifact_api.list_bucket_files(bucket_name)
   assert artifact_seeded_file in remaining_files          # ← never reached
   ```

   That wait raises `TimeoutError` at 60 s because the resume drops the turn, so the
   assertion after it never runs. The spec was merged, reviewed and gated in that state.
   Byte-identical to the ELITEA-2213 bug fixed one case earlier.
2. Whether Block-with-Comment shares #1834/#1835's shape was **assumed, never verified**.
3. Whether the case text carries the bogus tool-chip-absence assumption (#1839) was open.

The original 2026-08-03 pass never reached a live card at all ("precondition unreachable
locally") — it was source-read. This is the first live execution of ELITEA-2214.

## What was executed live

Three runs against `http://localhost:5173` (EliteaUI on `automation/testids`), 2026-08-27,
driven through the suite's own `ChatPage` page object with **Socket.IO frame capture armed
before navigation** (`page.on("websocket")` — passive observation, the same class of
evidence the merged support-assistant specs and `PipelineDetailPage.capture_websocket_frames()`
already use). Precondition set through the **same** REST guardrails write the
`sensitive_delete_file_toolkit` fixture uses (§ Fidelity Declaration below).

| | Run 1 — Block with Comment | Run 2 — Block with Comment | Run 3 — **matched control, plain Block** |
|---|---|---|---|
| Conversation | 9691 (fresh) | 9696 (fresh) | 9695 (fresh) |
| Toolkit / bucket | artifact toolkit 3438 → `autotest-2214-live-794458` | same | same |
| Seeded file | `autotest-hitl-2214-794458.txt` | same (survived run 1) | same |
| Observation window after resolve | 118 s + control message + page reload | 58 s | 58 s |

`sensitive_tools` captured as `{}`, restored to `{}` and **verified by readback** at the
end (`#1838` discipline). Nothing was mocked, injected or intercepted.

Three further attempts (conversations 9692/9693/9694) died upstream in setup — the card
never appeared within 45 s. That is the known TRIGGER flake
(`.agents/testing.md` § Unconfirmed): guardrails readback confirmed the flag was set and
the toolkits badge confirmed the attach, so the LLM simply did not call the tool.
Re-run, never classified as a signature.

## Q1 — does Block with Comment show the same shape as #1834 / #1835?

**Yes — identical, and a matched control run proves it is not path-specific. Commented on
#1834 and #1835; no third bug filed.**

### Timeline after Submit (sampled continuously)

| | Run 1 (9691) | Run 2 (9696) | Control, plain Block (9695) |
|---|---|---|---|
| `sensitive-action-panel` at +0.1 s | **0** — closes correctly | **0** | **0** |
| card back at | **+4.4 s → 1** | **+6.9 s → 1** | **+6.9 s → 1** |
| panel through end of window | 1, continuously (118 s) | 1, continuously (58 s) | 1, continuously (58 s) |
| assistant answer body | **never non-empty** — stayed at the `"Thought for 3 secs"` header, 118 s | same, 58 s | same, 58 s |
| `chat-answer-tool-chip` | 1 before AND after, throughout | 1 | 1 |
| seeded file in bucket | **present at every sample** | present at every sample | present at every sample |
| console errors / `pageerror` | **0** | 0 | 0 |
| failed HTTP requests / 4xx / 5xx | **0** | 0 | 0 |
| after page reload | panel **0**, tool chip **0**, message persisted as `"Thought for 3 secs"` with no body | — | — |

### Control — the conversation is left poisoned (run 1)

After the blocked turn, an unrelated message
(`"Reply with exactly the word CONTROL and nothing else."`) was **not answered** — the
sensitive-action card was still up 25 s later, exactly as ELITEA-2213 recorded for plain
Block. The decision is never committed as a tool outcome.

### The turn is NOT silent — it is REJECTED (new, and it names the root cause)

ELITEA-2211/2212/2213 all concluded "no error frame; the turn dies silently". That was an
**instrumentation gap**: HTTP was clean, but nobody read the Socket.IO frames. There is an
error on **every** resume, in **every** run, within ~50 ms of the click.

Initial `chat_predict` (works — the card appears) **carries `llm_settings`**:

```
42["chat_predict",{"user_input":"…","llm_settings":{"model_name":"eu.anthropic.claude-sonnet-4-5-20250929-v1:0","model_project_id":1},"project_id":399,…}]
```

`chat_continue_predict` (the HITL resume) **has no `llm_settings` key at all**:

```
42["chat_continue_predict",{"project_id":399,"conversation_uuid":"…","message_id":"…",
  "thread_id":"…","mcp_tokens":{},"ignored_mcp_servers":[],"user_declined_mcp_servers":[],
  "user_input":"block_with_comment","token_limit_continuation":false,"hitl_resume":true,
  "hitl_decisions":[{"interrupt_id":"hitl_6c75262f37604deebc521e4ed80bd5f5","tool_call_id":"",
                     "action":"block_with_comment",
                     "value":"This action is too risky and could delete important data"}]}]
```

and the backend replies with three frames, every time:

```
42["socket_validation_error",{"event":"chat_predict","content":"llm_settings with model_name is required","type":"error",…}]
42["socket_validation_error",{"event":"chat_predict","content":"llm_settings with model_name is required","type":"error",…}]
42["socket_validation_error",{"event":"chat_predict","content":"Continue execution failed: llm_settings with model_name is required","type":"error",…}]
```

The **matched control** (plain Block, conv 9695) produced the byte-identical rejection with
`"user_input":"reject"` / `"action":"reject"` / `"value":""`. So Authorize, Block and Block
with Comment all fail the same way — one root cause, already tracked as #1834. The frontend
swallows `socket_validation_error` entirely: no console error, no toast, no message-state
change, and the `beforeunload` guard stays armed as if a generation were in flight. That is
why it *looks* silent from the UI.

Two payload details recorded for whoever fixes it: the resume takes the **parallel** branch
of `onHitlResume` (`ChatBox.jsx` ~1806/1859) and sends `hitl_decisions[]` rather than the
singular `hitl_action`/`hitl_value`, even for a single non-parallel interrupt; and
`tool_call_id` is the **empty string** in every observed decision.

**Comments posted (no third issue filed):**
- #1834 — https://github.com/EliteaAI/elitea-testing-public/issues/1834#issuecomment-5433322965
- #1835 — https://github.com/EliteaAI/elitea-testing-public/issues/1835#issuecomment-5433325316

## Q2 — is the typed reason RECORDED anywhere observable? (the case's own headline)

**Half of it is, and the AFS must say which half.** The case title says "Records the
Reason"; its Pass/Fail criteria fail the case if "comment not recorded". Three places were
checked:

| Where | Observed |
|---|---|
| **Outbound resume frame** — `hitl_decisions[0].value` on `chat_continue_predict` | **YES, verbatim, 2/2 runs.** The frontend transmits the exact typed string. |
| **Persisted conversation** — `GET /chat/conversations/9691` after the run | **NO.** The full JSON contains no occurrence of the comment text, no `block_with_comment`, no `denial_reason`. Only the user's original message and an assistant group with an empty body. |
| **UI / assistant reply** | **NO.** The card closes, the reappeared card renders collapsed (the typed reason is not even recoverable from the UI), and no reply ever arrives. |

⇒ The **client-side** half of "records the reason" is real, observable and green, and is
asserted below (row G). The **server-side** half — the reason reaching the SDK's
`denial_reason`, being persisted, or surfacing in the response — **cannot be observed at
all today, because the resume that would carry it is rejected**. That is not a gap in the
test; it is `blocked-on-#1834`, and it is recorded in § Blocked Steps rather than being
quietly dropped from the assertion set.

The old AFS's Expected Results line — *"sends it as `denial_reason`"* — was a source-read
claim (`BlockWithCommentControl.jsx` docstring), never an observation. It is unverifiable
end to end today.

## Q3 — does ELITEA-2214's case text carry the #1839 tool-chip assumption?

**No — and the merged test correctly has no chip assertion at all. Nothing to correct here;
this section exists so nobody later "improves" the spec by adding one.**

ELITEA-2214's step 4 reads only *"Verify toolkit tool does NOT execute → No execution"* —
unlike ELITEA-2213's step 5, it never mentions chips. So the drift filed as clarification
**#1839** does not touch this case's text, and no new clarification is owed.

The underlying fact still holds and was re-confirmed here 3/3 runs: `chat-answer-tool-chip`
is a tool-CALL-ATTEMPT chip (`ActionView.jsx:407`, rendered from the call intent with no
execution predicate) — count **1 while the card is still pending**, **1 after the decision**,
and 0 only after a page reload. Any future `to_have_count(0)` on it asserts a state the
product never enters. **Non-execution is proven on the backend listing (rows F + K), never
on a chip.** No chip assertion is added to this spec: the testid is already referenced
positively on ELITEA-2212's and ELITEA-2213's executed paths (canon ruling #277 shape (b) is
satisfied there, module docstring), so adding a redundant one here would buy nothing.

## Q4 — the primary observable is correct but unreachable (confirmed)

- **Correct:** yes — the seeded file was present at every sample, in all three runs.
- **Reachable:** **no**, exactly as reported. It sits after
  `wait_for_message_content_stable(...)`, which raises at 60 s because the answer body
  never becomes non-empty.
- **Fix:** read the bucket **immediately after the card closes** (row F), and add a
  **second, later** read after the response window (row K) so "did not execute" is
  time-bounded rather than instantaneous.

**Honesty caveat that must survive into the test docstring** (same as ELITEA-2213's):
*file still present* is **not** proof that Block-with-Comment worked. A rejected resume
leaves byte-identical evidence. It is the case's own observable and must be asserted, but
the assertions that actually distinguish "blocked" from "rejected" are rows H and I — and
both are red today.

## Corrected assertion set — exact shapes, in EVALUATION ORDER

Setup is unchanged: `_reach_sensitive_action_card(page, conversation_id, artifact_toolkit, artifact_seeded_file)`.
The websocket collector must be armed **before** `_reach_sensitive_action_card` navigates —
`page.on("websocket")` only fires for sockets opened after the listener is attached.

| # | Order | Step | Assertion | Kind | Verified |
|---|---|---|---|---|---|
| A | 1 | Three action buttons visible on this case's own card | `expect(authorize/block/block_with_comment).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)` | **hard** | GREEN — 3/3 runs |
| C | 2 | Click the collapsed "Block with Comment" trigger; the inline comment control appears IN PLACE | `chat.sensitive_action_block_with_comment_button.first.click()` then `expect(chat.sensitive_action_block_comment_input).to_be_visible(...)` and `expect(chat.sensitive_action_block_comment_submit_button).to_be_visible(...)` | **hard** | GREEN — 2/2 runs |
| D | 3 | Type the comment; the textarea holds it verbatim | `press_sequentially(BLOCK_COMMENT, delay=20)` then `expect(chat.sensitive_action_block_comment_input).to_have_value(BLOCK_COMMENT)` | **hard** | GREEN — exact match, 2/2 runs |
| E | 4 | Click Submit; the card closes | `chat.sensitive_action_block_comment_submit_button.first.click()` then `expect(chat.sensitive_action_panel).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)` | **hard** | GREEN — count 0 at +0.1 s, 2/2 runs |
| F | 5 | **PRIMARY OBSERVABLE, moved to here** — the tool did not execute | `assert artifact_seeded_file in artifact_api.list_bucket_files(bucket_name)` | **hard** | GREEN — 2/2 runs |
| G | 6 | **The typed reason IS transmitted on the resume** (the case's "records the reason", client-side half) | from the captured sent frames, take the `chat_continue_predict` frame(s) after the Submit mark; assert exactly one carries the comment — reading it from **either** payload shape: `frame.get("hitl_value")` **or** `d["value"] for d in frame.get("hitl_decisions", [])` where `d["action"] == "block_with_comment"` — and that the value `== BLOCK_COMMENT` | **hard** | GREEN — verbatim, 2/2 runs |
| I | 7 | The LLM response acknowledges the block | wrap `chat.wait_for_message_content_stable(...)` in `try/except TimeoutError` → on timeout append to `soft_failures`; **only if** text arrived, run the loose checks (`last_text.strip()` non-empty; `not any(p in lowered for p in _SUCCESS_CLAIM_PHRASES)`) + `# Known defect: #1834` | **soft** (`soft_failures`, drained by `pytest.fail` from a `finally`) | **RED** — no response in 118 s / 58 s, 2/2 runs |
| H | 8 | **The resume is not rejected by the backend** | over the frames captured since the Submit mark, assert none has `event == "socket_validation_error"`; on failure report the frames' `content` verbatim + `# Known defect: #1834`. **Match on the event name, never on the message text** — any validation error on a resume is wrong, and the wording is not ours to depend on | **soft** (`soft_failures`) | **RED** — 3 error frames within ~50 ms, 2/2 runs **and** 1/1 control |
| J | 9 | The resolved card stays gone | `expect.soft(chat.sensitive_action_panel, "Known defect #1835: …").to_have_count(0, timeout=PANEL_STAYS_GONE_TIMEOUT)` + `# Known defect: #1835` | **soft** (`expect.soft`) | **RED** — reappears at +4.4 s / +6.9 s and persists, 2/2 runs |
| K | 10 | Late-execution guard — the file is *still* present after the response window | `assert artifact_seeded_file in artifact_api.list_bucket_files(bucket_name)` (second read, after I) | **hard** | GREEN — present through 118 s / 58 s |
| L | 11 | Side channel — no console/JS errors across the flow | `assert not console_issues and not page_errors` via `utils.console_errors.collect_console_errors(page)` + a `pageerror` listener (this spec does not use them today; ELITEA-2211/2212/2213 do) | **hard** | GREEN — 0 errors, 3/3 runs |

### Why H and J are evaluated AFTER I (declared, deliberate)

Both are **absence** assertions over a window, and an absence evaluated too early asserts
nothing. J is the same race ELITEA-2213 declared: `to_have_count(0)` is satisfied the
instant the count is already 0, so at ~1 s after the click it would run inside the 4-7 s
pre-reappearance window and pass silently, dropping #1835 from the closed set. H has the
mirror-image property — the error frames arrive ~50 ms after the click, so H would in fact
fire correctly early, but placing it after the 60 s response window makes it strictly
safer (a *late* rejection would also be caught) at zero cost. Evaluated after I, both are
settled states.

G is deliberately NOT deferred: it is the case's own headline observable and the one row
that distinguishes this case from ELITEA-2213, so it is hard-asserted early, before any
later red can abort the run.

### Structural requirements for the implementer

- **A `ChatPage` websocket-frame collector.** `ChatPage` has none today; the proven shape
  is `PipelineDetailPage.capture_websocket_frames()` (`pages/pipeline_detail_page.py:8650`),
  a `@contextmanager` yielding a growing list of parsed `42["event", {...}]` frames tagged
  with `event` and `_direction`, built for exactly this purpose (ELITEA-2015 HITL resume
  diagnosis). Lift that pattern into `ChatPage` (or a shared home) rather than re-deriving
  it; slice the window with `before = len(frames)` around the Submit click, as its own
  docstring instructs. **This is passive observation, not a substitution** — no
  `route`/`fulfill`, nothing intercepted, delayed, rewritten or fabricated
  (`.agents/testing.md` § Fidelity policy; the merged support-assistant specs declare the
  same and are the in-repo precedent).
- `soft_failures: list[str]` + a `try/finally` that drains it with `pytest.fail`, exactly
  as `TestSensitiveActionAuthorize` and `TestSensitiveActionBlock` already do — so a hard
  failure later can never discard the #1834 evidence, and every member of the closed set
  is reported on every run.
- `@pytest.mark.flaky(reruns=0)` on this test (it does **not** carry it today), matching
  the two sibling sanctioned-RED specs: `pytest.ini`'s global `--reruns=2` can never
  rescue an expected failure — it can only triple a ~2-minute run and add retry noise.
- Every step wrapped in `with allure.step("Step N — …"):`.
- The module docstring's SANCTIONED-RED block must be extended to name
  `TestSensitiveActionBlockWithComment` as a **third** expected-FAILED spec, with its own
  closed enumerable set (**#1834** twice — no response + resume rejected, both 2/2;
  **#1835** — card reappears, 2/2) and the expected signature: a `BaseExceptionGroup` with
  exactly **2** sub-exceptions (the `expect.soft` for #1835, and the single `pytest.fail`
  drain carrying BOTH #1834 rows). The docstring's existing sentence *"the turn dies
  silently, no error"* is now **stale for all three specs** and must be corrected: the turn
  is rejected with `socket_validation_error`, which the UI swallows.
- Keep the declared **transit** substitution wording; do not extend it.

**Resolved/added during ELITEA-2214 implementation (2026-08-27, implementer slot):**
the frame collector has a non-obvious failure mode this AFS did not name, and it
costs a FALSE RED on hard row G if missed. Playwright's **sync** API dispatches
page events (`websocket` / `framesent` / `framereceived`) only while the calling
thread is inside a Playwright call. A `time.sleep`-based poll waiting for the
resume frame therefore **starves the dispatcher**: measured here, the frame list
stayed frozen at 18 entries for a full 15 s poll, and the `chat_continue_predict`
frame plus its three `socket_validation_error` replies materialised *instantly*
the moment any Playwright call was made — so the spec reported "the decision
never left the browser" while the browser had in fact sent it, 2 runs running.
The poll step must be a Playwright call (`page.wait_for_timeout(...)`, declared
as an improvisation since the project otherwise forbids it — it pumps the driver,
it does not stand in for a condition wait). This is also why the in-repo
precedent's usage example puts `page.wait_for_timeout(5000)` after its HITL
click. Row H needs no such poll: row I's 60 s response wait pumps the driver
continuously, so every frame is dispatched by the time H reads them.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| The guardrails sensitivity precondition — `artifact`/`delete_file` marked sensitive via `PUT {api}/admin/plugin_config_values/administration/guardrails` instead of the Admin UI | **transit** | The Admin UI is a separate deployed application `localhost:5173` does not serve (no `/admin` route in `EliteaUI/src/routes.js`, issue #1140). Every observable this case asserts — the card, the buttons, the inline comment control, the typed value, the card closing, the resume frame, the error frames, the file listing, the response, the console — is produced end to end by the real LLM → real tool call → real backend interrupt → real WebSocket frames. Nothing is mocked, injected or intercepted. |
| *(none — for completeness)* `page.on("websocket")` frame capture | **not a substitution** | Passive observation, the same class of evidence as reading a response body (`.agents/testing.md` § Fidelity policy). No `route`/`fulfill`, nothing intercepted, delayed, rewritten or fabricated. In-repo precedent: `pages/support_assistant_page.py:1100` and `PipelineDetailPage.capture_websocket_frames()`. |

**No terminal substitution is specified anywhere in this AFS.**

## Coverage Map (rewritten to reflect reality)

**Axis 1 — the case's own elements:**

| Case element | Expected result | Covered by (rework row) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click 'Block with Comment' | Modal/text input appears for blocking reason | **C** | this case's own test body | **asserted** — GREEN. *CLARIFICATION (not a defect): it is an INLINE expansion on the same card, not an MUI `Dialog` — there is no `[role="dialog"]`. Live-confirmed; the observable ("an input appears") is unaffected. Also observed: the collapsed trigger is REPLACED, so `sensitive-action-block-with-comment-button` count goes 1 → 0 while expanded.* |
| 2 Type comment | Comment entered | **D** | `to_have_value(BLOCK_COMMENT)` | **asserted** — GREEN, exact match |
| 3 Click Submit/Confirm | Modal closes; card updates; action blocked | **E** (+ **J** for "stays" updated) | this case's own test body | **asserted** — GREEN for the close; "card updates" is red via J (it comes back) |
| 4 Verify toolkit tool does NOT execute | No execution | **F** (moved before the response wait) + **K** (late-execution guard) | backend `list_bucket_files` × 2 | **asserted** — GREEN. *Previously UNREACHABLE: it sat behind a wait that times out.* |
| 5 Verify LLM response acknowledges the block | LLM responds about the block | **I** | soft-routed via `soft_failures` → `pytest.fail` | **blocked-on-#1834** — the product emits **no response at all**; asserted as the correct behaviour, sanctioned-RED |
| Pass/Fail criterion: *"comment not recorded" ⇒ Fail* / title "Records the Reason" | reason recorded | **G** (client-side half) | assertion on the resume frame's decision value | **PARTIAL — asserted for the transmitted half (GREEN); the persisted/consumed half is `blocked-on-#1834`, see § Blocked Steps.** Never silently dropped. |

**Axis 2 — analyst additions beyond the case:**

- **G — the resume frame carries the typed reason.** *Added: without it this spec is
  ELITEA-2213 plus three UI steps, and the case's own headline ("Records the Reason") is
  untested. It is the only place in the whole system where the reason is currently
  observable.*
- **H — no `socket_validation_error` on the resume.** *Added: it converts the #1834 signal
  from an absence ("no response arrived after 60 s", weak and slow to diagnose) into a
  positive, precise statement of what the backend actually did. It is the assertion that
  would have prevented three consecutive passes concluding "the turn dies silently".*
- **J — the resolved card stays gone.** *Added: without it the #1835-shaped reappearance
  (~4-7 s here, with all three buttons live) is invisible to this case, even though it lets
  a user re-decide — including **Authorize** — an action they already blocked with a written
  justification. Both sibling specs already carry the mirror of this assertion.*
- **K — the second, later file-presence read.** *Added: F alone proves only that the delete
  had not happened at that instant. Since the turn is rejected rather than completing, a
  late execution is exactly the failure this case would otherwise miss.*
- **L — the console/JS side channel.** *Added: this spec does not collect console errors
  today. All three runs were clean, which is itself the finding that makes "the UI swallows
  the rejection" a verified statement rather than an impression.*

## Concrete Handles (verified live this pass, 2026-08-27)

PROVENANCE verified after `cd ../EliteaUI && git fetch origin`, two-stage grep per
`.agents/workflow.md` § Closure record (`git grep -- "$t" origin/<ref> -- src/ | grep -qiE '(data-testid|testid[[:space:]]*[:=])'`):

| Element | Locator | PROVENANCE | Observed this pass |
|---|---|---|---|
| Sensitive-action card | `LocatorDescriptor(testid="sensitive-action-panel")` | **on-main ✓** (also on `automation/testids`) | 1 pending → **0 at +0.1 s** → **1 again at +4.4 s / +6.9 s**, persists until reload |
| Authorize button | `LocatorDescriptor(testid="sensitive-action-authorize-button")` | **on-main ✓** | visible on the original AND the reappeared card |
| Block button | `LocatorDescriptor(testid="sensitive-action-block-button")` | **on-main ✓** | visible on both |
| Block-with-Comment collapsed trigger | `LocatorDescriptor(testid="sensitive-action-block-with-comment-button")` | **on-main ✓** | count 1 → **0 while expanded** → 1 again on the reappeared card |
| Comment textarea | `LocatorDescriptor(testid="sensitive-action-block-comment-input")` | **on-main ✓** | count 0 → 1 on trigger click; `press_sequentially` + `input_value()` matched the 56-char comment exactly |
| Submit button (expanded) | `LocatorDescriptor(testid="sensitive-action-block-comment-submit-button")` | **on-main ✓** | count 0 → 1 on trigger click; click closes the card at +0.1 s |
| Thought accordion (setup gate) | `LocatorDescriptor(testid="chat-answer-thought-accordion")` | **on-main ✓** | appears before the card; its absence is the trigger flake's Step-2 shape |
| Tool-call chip | `LocatorDescriptor(testid="chat-answer-tool-chip")` | **on-main ✓** | **count 1 before AND after Submit**; 0 after reload. *Not asserted by this spec (Q3).* |
| Model chip | `LocatorDescriptor(testid="chat-answer-model-chip")` | **on-main ✓** | count 1 throughout |
| Non-execution proof | `ArtifactAPI.list_bucket_files(bucket_name)` | n/a (API) | seeded file present at every sample, 118 s / 58 s / 58 s |
| Answer body | `ChatPage.get_last_message_text()` / `wait_for_message_content_stable()` | n/a | **never becomes non-empty**; `get_last_message_text()` returns the 18-char `"Thought for 3 secs"` header, which `wait_for_message_content_stable` correctly treats as a placeholder and therefore raises on |
| Resume + rejection frames | **new** — a `ChatPage` equivalent of `PipelineDetailPage.capture_websocket_frames()` (`pages/pipeline_detail_page.py:8650`) | n/a (Playwright API) | `chat_continue_predict` sent with the comment in `hitl_decisions[0].value`; three `socket_validation_error` frames received ~50 ms later |

**No new testid is needed by this rework** — every UI handle above already exists on
`EliteaAI/EliteaUI` `main`, so nothing here waits on a human cherry-pick.

## Known Defects (this pass)

| ID | State | Symptom on the Block-with-Comment path | Fired |
|---|---|---|---|
| **#1834** | OPEN | The resume is **rejected** — `chat_continue_predict` omits `llm_settings`, the backend answers `socket_validation_error: "llm_settings with model_name is required"` / `"Continue execution failed: …"`, the UI swallows it, and no assistant response ever arrives. The decision is never committed, so the next user message re-triggers the identical card. **Matched control proves plain Block fails identically** — one root cause, not a per-path bug. | **2/2** runs (+ 1/1 control) |
| **#1835** | OPEN | The correctly-closed card re-renders at **+4.4 s / +6.9 s** with all three buttons live, and persists until a page reload — a user can Authorize an action they already blocked with a written justification | **2/2** runs |
| #1839 | OPEN | Clarification (ELITEA-2213 case text only). **Does not touch ELITEA-2214's text** — this case never mentions chips. Cited so the bogus absence assertion is never introduced here. | n/a |
| #1831 | OPEN | `unknown message type parallel_hitl_ready` console **warning** during the flow — a warning, not an error; the error-only collector must not be widened to swallow it | all runs |
| #636 | OPEN | Bucket deletion returned 404 in cleanup (known unreliable bucket deletion) | 1 leftover, see § Environment |

No third issue is filed: every symptom is the Block-with-Comment manifestation of the same
dropped/rejected-resume root cause already tracked by #1834 / #1835. Both were commented
with this pass's evidence (links in Q1).

## Blocked Steps

**One half of one case element is blocked, and it is the case's headline.**

- **"Block with Comment **records** the reason" — the server-side half is unobservable.**
  The reason is transmitted verbatim on the resume frame (asserted, row G), but the resume
  is rejected before anything consumes it: the comment does not reach the conversation
  (`GET /chat/conversations/<id>` contains no occurrence of it, no `block_with_comment`, no
  `denial_reason`), does not surface in any reply (there is none), and is not recoverable
  from the UI (the reappeared card renders collapsed). The old AFS's claim that it is sent
  as `denial_reason` was a source-read of a docstring, never an observation.
  **What would unblock it:** #1834. Once the resume is accepted, re-analyse to add the
  server-side assertion (the reason surfacing in the assistant's reply and/or the persisted
  conversation). Until then this is `blocked-on-#1834`, declared here rather than dropped.

Everything else runs end to end.

## Environment / hygiene

- **`#1838` discipline honoured on both ends.** `sensitive_tools` read as `{}` **before**
  any write, and restored to `{}` with a **verified readback** after the last run
  (`RESTORED sensitive_tools (readback): {}` / `FINAL sensitive_tools: {}`).
- Conversations 9691-9696 and artifact toolkit 3438 deleted.
- **Leftover:** bucket `autotest-2214-live-794458` (1 file) could not be deleted — the
  delete returned 404. Already-known unreliable bucket deletion (`#636`), same leftover
  class ELITEA-2213's pass recorded; not a new finding.
- **Trigger flake, 3 occurrences this session** (conversations 9692/9693/9694): the card
  never appeared within 45 s at setup, with the guardrails flag provably set and the
  toolkits badge provably true. Consistent with `.agents/testing.md` § Unconfirmed —
  re-run, never a signature. 3-in-6 is a noticeably higher rate than the 1-in-4 / 1-in-6
  previously recorded; worth watching, and worth the bounded trigger-retry that ledger
  entry already names as the durable fix if it keeps costing gate time.
