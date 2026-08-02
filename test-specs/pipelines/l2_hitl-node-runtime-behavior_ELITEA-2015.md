# Test Case: Pipeline HITL Node — Runtime Behavior

## Metadata
- **TMS ID**: ELITEA-2015
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-02 (cluster dispatch with ELITEA-2014)
- **Status**: ready-for-automation

**Classification-note (declared improvisation, `.agents/testing.md` § Merge gate
"Analysis-time entry" bullet, 2026-07-23/#557/ELITEA-1965):** this case's core
runtime-resume behavior (steps 4 and 6) is broken by a deterministic, single-cause,
now-filed-and-OPEN defect (`EliteaAI/elitea-testing-public#1103`). Per that bullet,
because the defect was fully explored (not merely encountered and stopped on — both
the Approve and Reject branches were run to completion and their actual results
captured), this classifies as `ready-for-automation` rather than `defect-found`: the
implementer should write steps 4–6's assertions as the CORRECT expected behavior
(per the case text) using `expect.soft()` + `# Known defect: #1103`, so the test
documents the intended contract, fails deterministically today (sanctioned RED per
the Merge gate), and flips green automatically the moment the backend fix ships.
Steps 1–3 (pause + message + button-presence) are unaffected and assert normally.

**Implementer correction (2026-08-02, automation pass, fresh live websocket capture,
2/2 repro attempts each — independent of the analyst's session above):** step 4
(Approve) does **not** reproduce the defect described above. Approve correctly sends
`chat_continue_predict {hitl_resume:true, hitl_action:"approve"}` and the backend
routes to the configured APPROVE target — Printer 1's formatted output
("Final: pipeline approved") reaches the chat's `agent_response` frame. The
"static hint, no Printer execution" symptom in `#1103`'s title/body applies to
**Reject only**: Reject re-emits a fresh `start_task`/`agent_start` sequence and
restarts the whole pipeline from the entry point instead of ending at END —
confirmed 2/2. Per the reverse-masking guard (live product is ground truth over a
filed defect's text), the shipped test asserts Approve as a normal HARD assertion
and reserves `expect.soft()` / `# Known defect: #1103` for Reject only. A comment
was added to `#1103` documenting this split so the ticket isn't chased for a
non-repro Approve half.

**Second implementer correction:** step 3's "Approve/Edit/Reject buttons appear"
does not hold with this case's own precondition (APPROVE + REJECT routes only, no
EDIT). Live-confirmed via the `agent_hitl_interrupt` payload's `available_actions`
field: it is exactly `["approve", "reject"]` — no `edit` — because the live product
only offers the Edit action when the HITL node has an `edit` route configured (same
class of route-gating as ELITEA-2014's EDIT-STATE-KEY-gates-EDIT-route finding, not
a defect). The shipped test asserts the Edit button's ABSENCE, matching the
precondition as literally specified rather than adding an edit route the case never
asked for.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with configuration: `LLM 1 → HITL 1 → Printer 1 → END`, with HITL
  routes `APPROVE → Printer 1`, `REJECT → END` (case's stated precondition, matched
  exactly — this session used pipeline id `6757`, `autotest_hitl_2014_2015`, seeded
  via `PipelineAPI.create_pipeline_with_nodes`).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline with the exact topology above. `LLM 1`'s `task` should be a fixed
  non-empty value (this session's exploration pipeline had an EMPTY fixed `task`,
  which is why the Reject-path evidence shows the LLM answering "It looks like your
  last message was empty..." — that empty-task detail is incidental to the
  precondition, not required by the case; the implementer's fixture should give
  `LLM 1` a real task so the Reject-defect's actual-vs-expected text stays legible
  without relying on this incidental artifact).
- `HITL 1`'s `user_message` set to a fixed, recognizable string (e.g. `"Please
  review this response"`) so step 3's chat-content assertion has a known target.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`).

## Test Steps

1. Create pipeline `LLM 1 → HITL 1 → Printer 1 → END` with HITL routes configured
   (`APPROVE → Printer 1`, `REJECT → END`).
   - **Verify**: pipeline saves with the described topology (via
     `PipelineAPI.create_pipeline_with_nodes` + a read-back `get_pipeline()`, or via
     the UI per ELITEA-2014's flow).
2. Execute the pipeline by sending a message in the embedded chat
   (`send_message_in_embedded_chat`, existing `PipelineDetailPage` method).
   - **Verify**: pipeline starts execution — a "Run N details" indicator appears on
     the canvas.
3. Wait for the pipeline to pause at the HITL node.
   - **Verify**: (a) an `agent_hitl_interrupt` websocket event with the configured
     `user_message` content arrives; (b) the chat renders a card showing that exact
     message text; (c) exactly one each of Approve / Edit / Reject buttons are
     visible and enabled in that card. Confirmed live via screenshot + button-count
     probe (`1` Approve, `1` Reject, `1`+ Edit-related elements — the "Edit" text
     also appears once the inline edit form label expands, see Concrete Handles).
4. Click "Approve".
   - **Expected (case)**: flow proceeds to the configured APPROVE route (`Printer
     1`) and its formatted output appears in the chat.
   - **Actual (live, confirmed via websocket capture)**: the client correctly sends
     `chat_continue_predict {hitl_resume: true, hitl_action: "approve", user_input:
     "approve"}`, but the backend's `agent_response` is a static hint —
     `"\n\n-----\n*How to proceed? To resume the pipeline - type anything...*"` —
     with `finish_reason: "stop"` (i.e. this is the final response, not an
     intermediate one). No `Printer 1` execution is observed. **This is
     `EliteaAI/elitea-testing-public#1103`** — assert the CORRECT expected behavior
     (chat's final message contains the Printer's formatted output, e.g. `"Final:"`)
     via `expect.soft()` + `# Known defect: #1103`.
5. Verify the final response appears in chat.
   - Covered by step 4's soft-assertion (same defect; the "final response" IS the
     Printer output that step 4 expects and doesn't get).
6. Execute the pipeline again (fresh conversation), this time click "Reject" instead
   of "Approve".
   - **Expected (case)**: flow goes to `END`; no further processing, no Printer
     output.
   - **Actual (live, confirmed via websocket capture)**: the client correctly sends
     `chat_continue_predict {hitl_resume: true, hitl_action: "reject", user_input:
     "reject"}`, but the backend re-emits `start_task` → `agent_start` →
     `pipeline_finish` — i.e. it **restarts the whole pipeline from the entry point**
     (`LLM 1` is re-invoked) instead of terminating at END. This is genuine "further
     processing," directly contradicting the case's "no further processing"
     contract. Same root cause as step 4 — **`EliteaAI/elitea-testing-public#1103`**.
     Assert the CORRECT expected behavior (no new `agent_start`/`start_task` event
     fires after the Reject click, and no Printer output appears) via
     `expect.soft()` + `# Known defect: #1103`.

## Expected Results
- HITL node pauses execution and renders the configured user message with Approve /
  Reject buttons — no Edit button with this precondition's routes (confirmed
  working; see implementer correction above re: Edit gating).
- Approve routes execution to the configured APPROVE target and its output reaches
  the chat (**implementer correction: confirmed WORKING** — see note above; the
  analyst's original "confirmed BROKEN — #1103" applies to Reject only).
- Reject routes execution to END with no further node execution (confirmed BROKEN —
  `#1103`; the backend restarts the pipeline from its entry point instead).
- No console errors at any step (confirmed — none observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline `LLM → HITL → Printer → END` with `APPROVE→Printer`, `REJECT→END` | setup exists | step 1 | step 1: read-back topology | asserted |
| 1 Create pipeline with described topology | pipeline saved | step 1 | step 1 | asserted |
| 2 Execute pipeline with a message | execution starts | step 2 | step 2: Run indicator | asserted |
| 3 Verify pipeline pauses at HITL — message + Approve/Edit/Reject shown | pause + message + buttons | step 3 | step 3: websocket `agent_hitl_interrupt` + button-count probe | asserted — **implementer correction: Edit button asserted ABSENT** (route-gated on a configured `edit` route, which this precondition doesn't have; not a defect) |
| 4 Click Approve — verify flow continues to APPROVE route | flow proceeds to Printer | step 4 | step 4: HARD assertion (`agent_response` contains Printer 1's output) | **implementer correction: asserted normally** — live-confirmed WORKING (2/2), contradicting the analyst's original "confirmed BROKEN" note; `#1103` scoped to Reject only, see implementer comment on the ticket |
| 5 Verify final response appears in chat | Printer response shown | step 5 (folded into step 4) | step 4's hard assertion | **implementer correction** — same as above |
| 6 Execute again, click Reject — verify flow goes to END | pipeline ends, no Printer output | step 6 | step 6: `expect.soft()` + `# Known defect: #1103` | **clarification-via-defect** — live product restarts the pipeline instead of ending; same disposition |
| Expected Final State: HITL pauses, shows buttons, routes correctly per action | — | steps 3–6 | steps 3–6 | partially asserted — pause/buttons pass; routing is the defect above |
| Pass/Fail: HITL pauses correctly; routing matches configuration | — | all steps | all steps | steps 1–3 asserted; steps 4–6 soft-assert the correct behavior against `#1103` |

### Axis 2 — Analyst additions

- Step 3 additionally asserts the exact `agent_hitl_interrupt` websocket payload
  (not just the rendered DOM) — *added: the DOM-only assertion could pass even if
  the wrong message text were shown due to a stale-render bug; asserting the
  websocket payload's `content` field pins the source of truth.*
- Steps 4 and 6 additionally capture and assert on the specific websocket event
  sequence (`agent_response`/`finish_reason` for Approve; `start_task`/`agent_start`
  for Reject) rather than only the rendered chat text — *added: this is what made
  the defect diagnosable as "wrong routing" vs "slow/streaming response" in the
  first place, and pins the regression signature precisely enough that a partial
  fix (e.g. Approve fixed but Reject still restarting) is still caught.*
- No console-error assertion was in the original case text; added it throughout —
  zero console errors were observed in this session (the defect is a
  backend-response-content issue, not a client-side exception).

## Cleanup

1. This session reused the same exploration pipeline as ELITEA-2014
   (`autotest_hitl_2014_2015`, id `6757`) for execution. Deleted at the end of this
   session via `PipelineAPI.delete_pipeline(6757)` — see ELITEA-2014's AFS Cleanup
   section (same pipeline, deleted once, shared by both cases' analysis).
2. Each execution run also created a conversation record (visible as "Run N
   details" on the canvas / `Run History` tab) — these are scoped to the pipeline
   and were removed along with it.
3. Implementer teardown: use the `pipeline_id` fixture pattern, seeding via
   `PipelineAPI.create_pipeline_with_nodes` as this session did, rather than reusing
   pipeline `6757` directly.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Embedded chat send input/button | existing `PipelineDetailPage.send_message_in_embedded_chat()` | **on-main ✓** — existing method, confirmed working this session | none needed |
| HITL pause detection | `page.wait_for_selector('button:has-text("Approve")')` used during exploration ONLY — **not compliant for shipped test code** (text-based, no testid) | **needs-adding**: `testid needed: chat-hitl-actions-panel` on the non-sensitive-tool branch's container `Box` in `ChatHitlActions.jsx` (currently has no testid at all — only the unrelated `sensitive_tool` guardrail branch has `sensitive-action-panel`) | none — flag to `add-data-testid`, do not ship the text-based selector |
| Approve button (chat HITL card) | scoped inside the HITL actions container, currently only distinguishable by visible text `"Approve"` | **needs-adding**: `testid needed: chat-hitl-approve-button` on the `BaseBtn` in `ChatHitlActions.jsx`'s non-sensitive-tool branch | none — flag to `add-data-testid` |
| Reject button (chat HITL card) | same container, visible text `"Reject"` | **needs-adding**: `testid needed: chat-hitl-reject-button` | none — flag to `add-data-testid` |
| Edit button/control (chat HITL card) | `EditControl.jsx`, visible text `"Edit"`, expands an inline textarea + submit/cancel on click | **needs-adding**: `testid needed: chat-hitl-edit-button` (the toggle button) — this case doesn't exercise the Edit action itself (not in the case's steps), so the inline form's own fields are out of scope here; note only, not a blocker | none — flag to `add-data-testid` |
| Chat message list (for reading the pause message + final response) | `ul.MuiList-root > li.MuiListItem-root` (existing project convention, `.claude/rules/mui-patterns.md`) | **on-main ✓** — existing convention; NOTE the existing `PipelineDetailPage.get_embedded_chat_last_message()` method threw a Playwright strict-mode violation this session (`div.css-xn5i2e` resolved to 2 elements inside the last `<li>`) — pre-existing page-object bug, not introduced here, flagged for the implementer/lead rather than fixed by this analysis (analyst has no code-authoring authority). | read chat content via websocket capture (`page.on("websocket", ...)` filtering `chat_predict`/`chat_continue_predict` frames) instead of the broken DOM method, until it's fixed |
| WebSocket resume payload | `chat_continue_predict` frame with `hitl_resume: true, hitl_action: "approve"\|"reject"` | **on-main ✓** — this is the actual product wire contract, confirmed via live capture; not a UI locator but the authoritative signal for asserting resume behavior | DOM-only assertion (chat text) as a secondary check |

## Network Behavior
- `chat_predict` (WS) — sent on message send (step 2); server responds with a stream
  of `agent_llm_chunk` → `agent_llm_end` → `agent_on_transitional_edge` →
  `agent_hitl_interrupt` (the pause signal, step 3) frames.
- `chat_continue_predict` (WS) — sent on Approve/Edit/Reject click, carrying
  `hitl_resume: true` and `hitl_action`. **This is the frame to assert on for steps
  4/6** — wait for the follow-up `agent_response` (Approve) or
  `start_task`/`pipeline_finish` (Reject) frame rather than a fixed timeout.
- No REST calls are involved in the resume flow itself — it is entirely
  WebSocket-driven, unlike the HITL node's static configuration (ELITEA-2014), which
  goes through the pipeline's `PUT`/`GET` REST endpoints.

## Known Defects Found During Exploration

- **[MAJOR] HITL node Reject resume does not end the pipeline — it restarts from
  the entry point** — filed as `EliteaAI/elitea-testing-public#1103` (originally
  filed against both Approve and Reject; **narrowed by the implementer's
  automation pass, 2026-08-02**, see below). Reject sends the correct
  `chat_continue_predict {hitl_resume:true, hitl_action:"reject"}` frame, but the
  backend re-emits a fresh `start_task`/`agent_start` sequence and re-invokes the
  entry-point node instead of ending at the REJECT route (`END`) — confirmed 2/2
  fresh-conversation attempts (this session's original run + the implementer's
  independent re-verification). Automation expects `expect.soft()`-equivalent
  (`soft_failures` list + `pytest.fail()`, the Python shape for plain-value
  comparisons) with `# Known defect: #1103` on the Reject assertions (step 6)
  per the sanctioned-RED merge-gate exception (`.agents/testing.md` § Merge
  gate).
- **Implementer correction (2026-08-02):** Approve does **not** reproduce this
  defect — confirmed 2/2 fresh-conversation attempts, independent of this
  session's original observation. Approve correctly routes to the configured
  APPROVE target; Printer 1's formatted output reaches the chat's
  `agent_response` frame. A comment was added to `#1103` narrowing it to
  Reject-only so the ticket isn't chased for a non-repro Approve half. Steps
  1–5 (pause, message, button-presence, Approve) are unaffected and assert
  normally (hard assert, no known-defect marker).
- **Implementer correction (2026-08-02), Edit button:** case step 3 describes
  Approve/Edit/Reject as always present, but with THIS precondition's routes
  (APPROVE + REJECT only, no EDIT), the live product's `agent_hitl_interrupt`
  payload reports `available_actions: ["approve", "reject"]` — no `edit`. The
  Edit action is gated on a configured `edit` route (same class as ELITEA-2014's
  EDIT-STATE-KEY-gates-EDIT-route finding), not a defect. Automation asserts the
  Edit button's absence rather than inventing an edit route the case never
  specified.

No other defects found — the pause/message behavior (case steps 1–3, adjusted
for the Edit-button correction above) works exactly as specified.

## Blocked Steps

None. All 6 case steps were executed to completion against the live local
environment (two full pipeline executions: one ending on Approve, one on Reject),
including live websocket capture of the resume payloads and responses.

## Automation Hints

- Framework: Playwright + pytest. Steps 1–3 need only the `add-data-testid` work
  listed in Concrete Handles (chat HITL buttons currently have zero testids); steps
  4–6 need no new locators beyond those same buttons — the assertions are on
  chat/websocket content, not on new UI elements.
- **Websocket assertion pattern**: this project's existing tests read chat content
  via the DOM (`get_embedded_chat_last_message()` etc.); this case's defect was only
  diagnosable by also capturing raw websocket frames (`page.on("websocket", ...)`).
  Recommend adding a small helper (e.g. `capture_chat_ws_frames(page)` context
  manager) to `PipelineDetailPage` or a shared chat-testing util, since any future
  HITL/streaming case will likely need the same technique — this is new
  infrastructure, not present in the codebase today.
- Test isolation: use a fresh pipeline/conversation per Approve/Reject variant (this
  session did, specifically to rule out session-state pollution as an explanation
  for the defect) — do not reuse one conversation for both branches.
- Wait strategy: wait for the specific follow-up websocket frame type
  (`agent_response` for Approve, `start_task` for Reject) after sending the resume
  action, not a fixed timeout — the existing `wait_for_embedded_chat_response()`
  page-object method works for the Approve case (it waits on chat-message-count
  change) but should be double-checked against the Reject case's different event
  sequence.
- `PipelineAPI.create_pipeline_with_nodes(name, description, entry_point, nodes)` is
  the right helper for seeding this case's precondition topology — confirmed working
  this session (same helper used for ELITEA-2014's precondition pipeline, id
  `6757`).
