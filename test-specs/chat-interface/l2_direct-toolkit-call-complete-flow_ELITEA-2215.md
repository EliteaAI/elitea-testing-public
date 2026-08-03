# Test Case: Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call to Output Display

## Metadata
- **TMS ID**: ELITEA-2215
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`) — **fully executed
  live**, no environment gaps for this case (unlike ELITEA-2211..2214, this
  case needs NO Guardrails/HITL configuration — a plain toolkit call).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
- An Artifact-type toolkit (`ToolkitAPI.create_artifact_toolkit`, includes
  `create_file` in its default `selected_tools`) is added as the ONLY
  participant in a fresh conversation, via "+ > Toolkits" (no agent).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Artifact bucket + toolkit — same fixture shape as ELITEA-2211's, reused
  as-is (`artifact_toolkit` fixture already exists, `create_file` is already
  in its hardcoded `selected_tools` list — no fixture change needed).
- Message: `"create a file named test.txt"` (case's literal text) —
  **live-confirmed this pass** (using the equivalent `delete_file` variant of
  this exact flow — see § Concrete Handles for the confirmed DOM this
  produced) that an unambiguous, single-target message reaches a real tool
  call without any clarifying-question detour, unlike ELITEA-2211's message
  wording (see that AFS's Test Data note). The case's `create_file` message
  is already unambiguous (one file name, no "the bucket" reference) — no
  substitution needed here, reuse verbatim.

## Test Steps
1. Send `"create a file named test.txt"` with the toolkit as the sole
   participant.
   - **Verify**: `[data-testid="chat-answer-thought-accordion"]` appears
     showing "Thought for X secs" (confirmed live, e.g. "Thought for 14
     secs" on the analogous `delete_file` message).
2. Expand the thinking-steps accordion.
   - **CONFIRMED LIVE during implementation (CLARIFICATION 3, added fix
     round 1, 2026-08-03):** this step's own "expand the accordion" action
     does not apply as written — 5 timed polls against the real backend
     (0.5s apart) confirm the accordion is ALREADY auto-expanded for the
     whole tool-call/streaming window (`ApplicationThinkView.jsx`'s
     `expanded={isStreaming || expanded}`, the same auto-expand behavior
     ELITEA-2181's streaming-response test already asserts without ever
     clicking). A manual click is not only unnecessary, it is actively
     unreliable — the accordion's rendered height changes as it streams, so
     a fixed click point can land on a different part of a growing element
     between the actionability check and the dispatched event. The
     implementation asserts presence/text directly instead of clicking.
   - **Verify**: tool call shown — **CONFIRMED LIVE, case-text drift found
     (CLARIFICATION, not a defect):** the case describes this as
     `"toolkit_name.tool_name"` (dot-separated), but the LIVE rendered chip
     text is `"{toolkit_name}: create_file"` (**colon-separated**, e.g.
     `"autotest-hitl-tk-749815: delete_file"` confirmed for the
     structurally-identical `delete_file` case — `ActionView.jsx`'s
     `buildTitle()` uses `": "` as its badge separator, `ActionView.jsx:249`).
     Assert the colon-separated live format, not the case's dotted example.
3. Wait for execution; verify the response appears.
   - **Verify**: assistant's markdown response renders below the accordion
     (confirmed live).
4. Verify the three horizontally-arranged chips.
   - **Verify — CONFIRMED LIVE, second case-text drift (CLARIFICATION):**
     the case describes THREE distinct chips ("LLM model chip, toolkit chip,
     tool call chip") as if toolkit-identity and tool-call were separate
     elements. Live DOM (captured via `#panel-content`'s full `outerHTML`
     after expanding the accordion) shows exactly:
     - 2× `[data-testid="chat-answer-model-chip"]` (one per distinct model
       invoked in this turn's reasoning chain — e.g. "Anthropic Claude 4.5
       Sonnet" + "Anthropic Claude Haiku 4.5"; COUNT is data-dependent, not
       fixed at 1)
     - 1× toolkit/tool combined chip, NO testid today (`ActionView.jsx:360`,
       `data-testid={toolkitType === 'model' ? '...' : undefined}` — else
       branch unnamed), text `"{toolkit_name}: create_file"`.
     There is no SEPARATE "toolkit chip" distinct from the "tool call
     chip" — the case's 3-chip description maps to this project's
     2-elements-in-practice-but-variable-count-of-model-chips reality.
     Assert: at least one model chip present, AND exactly one toolkit/tool
     chip present with the expected `"{toolkit_name}: create_file"` text.
5. Verify the LLM response text follows below the chips.
   - **Verify**: response markdown renders after the chip row in DOM order
     (confirmed live via the accordion's `outerHTML` structure —
     `MuiAccordionDetails-root` contains the chip row THEN the response
     text container in sequence).

## Expected Results
- Full flow completes: thinking accordion → chips → response, all without
  an agent intermediary.
- No console/JS errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Send message, toolkit as only participant | "Thought for X secs" appears | step 1 | step 1 | asserted |
| 2 Expand thinking steps; tool call shown as toolkit_name.tool_name | tool call in thinking steps | step 2 | step 2 | asserted *(clarification: live format is colon-separated `"name: tool"`, not dotted — see step 2 note)* |
| 3 Wait for execution; response appears | response visible | step 3 | step 3 | asserted |
| 4 Chips: model, toolkit, tool-call (3 chips) | three chips displayed horizontally | step 4 | step 4 | asserted *(clarification: live product renders 1 combined toolkit/tool chip + N≥1 model chips, not a fixed "3 distinct chips" — see step 4 note)* |
| 5 Response text follows below chips | text below chips | step 5 | step 5 | asserted |

**Axis 2 — Analyst additions:**
- Assert no console/JS errors — *added: standard side-channel check.*
- Assert the toolkit/tool chip's exact text format (`"{name}: {tool}"`) —
  *added: this is the one new testid's whole reason for existing; asserting
  presence alone without the text would under-specify the observable.*

## Cleanup
1. Delete the toolkit.
2. Delete the bucket (**flaky, see ELITEA-2211's Automation Hints note** —
   both delete paths 404'd live this pass; not blocking since this case
   doesn't assert bucket contents, but flag if teardown logs a failure).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Thought accordion | `[data-testid="chat-answer-thought-accordion"]` (exists, confirmed live) | none |
| Accordion expand toggle | `chat-answer-thought-accordion button` (the `AccordionSummary` button inside — same element, confirmed live via `aria-expanded` toggling `false`→`true`) | none — scoped to the existing testid parent, compliant |
| Model chip(s) | `[data-testid="chat-answer-model-chip"]` (exists, confirmed live — 2 instances observed for a 2-model reasoning chain) | none |
| Toolkit/tool chip | **testid needed**: e.g. `chat-answer-tool-chip` — add via `add-data-testid` to `ActionView.jsx:360`, naming the else-branch (shared new-testid ask with ELITEA-2212/2213, same element) | none — do not assert by chip text/position alone |
| Response text container | scoped inside the accordion's `MuiAccordionDetails-root`, DOM-order-after the chip row (confirmed live) — **no dedicated testid observed**; if the implementer needs a stable handle beyond DOM order, flag for `add-data-testid` rather than using a raw CSS class (`css-*` classes are Emotion-generated, unstable across builds) | none |

## Network Behavior
- Standard `chat_predict` websocket envelope (`start_task` → `agent_start` →
  intermediate frames → final response), confirmed live via captured frames
  this pass — no HITL pause frames in this flow (no sensitivity configured).

## Known Defects Found During Exploration
**Updated fix round 1 (2026-08-03) — was stale at "None found."** One
product defect WAS found during implementation, filed as
[EliteaAI/elitea-testing-public#1127](https://github.com/EliteaAI/elitea-testing-public/issues/1127):
across 3 separate live local runs, the direct-toolkit-call flow (no agent)
sometimes leaks the model's tool-call intent as raw visible text instead of
invoking the real backend tool — confirmed non-deterministic (2/5 runs
executed correctly). Per `.agents/testing.md`'s 2026-07-18 closed-set
variant (ELITEA-1892/#615 precedent), the implementation handles this via a
`soft_failures`/`pytest.fail()` aggregation gated behind an independent
`ArtifactAPI` ground-truth tie-breaker (same backend check ELITEA-2212/2213
use) — never a weakened assertion of the correct contract. See the test's
module docstring "Fix round 1" note for the full classification logic.

Both case-text/live-product divergences below (dotted vs colon-separated
chip format; 3-chips-as-described vs 1-combined-chip+N-model-chips-in-
practice; and CLARIFICATION 3 above, the accordion auto-expand) are
classified as **CLARIFICATION** per the reverse-masking guard — the live
product's behavior is correct and internally consistent; the case text is
the stale/imprecise element. Recommend filing a lightweight case-text
clarification note against ELITEA-2215 in the TMS per
`.agents/role-overrides.md`'s interaction-discovery-ladder precedent (not a
`bug`-labelled tracker issue — this repo's bug-filing is for THIS repo's
product-defect findings, not TMS case-text wording).

## Blocked Steps
None — this case was fully executed live end-to-end.

## Automation Hints
- Framework: Playwright + pytest.
- Markers: `pytest.mark.p2`, `pytest.mark.chat`, `pytest.mark.regression`
  (no `guardrails` marker needed — this case runs fine on localhost).
- Reuse `ChatPage.add_toolkit_participant()` (existing, confirmed live) for
  step 1's setup; `chat.wait_for_ai_response()` /
  `wait_for_message_content_stable()` (existing `ChatPage` methods per
  `.agents/testing.md` § Hooks) for the response-settle wait, never a
  `page.wait_for_timeout()` sleep.
- This case's toolkit/tool-chip testid ask is the SAME one ELITEA-2212/2213
  need — implement once, reuse across all affected specs in this batch's PR.
