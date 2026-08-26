# Test Case: Chat – Tool Action Rendering – Verify Tool Call Displays in Thinking Steps When Toolkit Called Directly

## Metadata
- **TMS ID**: ELITEA-2209
- **Linked Story**: none
- **Priority**: lextend (case frontmatter says `priority: high`, which maps to `l1` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `chat-remaining-w15`
- **Status**: **extend-existing** — case executed live end-to-end (participants-panel portion; the
  message→thinking-steps→chip portion re-executed by observation of the covering spec's already-live-
  confirmed mechanism, per Overlap check below), zero NEW product defects found by this case's own
  delta. Target: `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallCompleteFlow::test_direct_toolkit_call_complete_flow` (merged to `origin/automation/base`, commit `76666eeae2df4c5697620e840e9f3f2dedb0b1c1`).

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py` (ELITEA-2215,
"Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call to Output Display"). Its AFS
is `test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md`.

ELITEA-2209 and ELITEA-2215 are the **same live flow** — a toolkit added as the sole chat participant
(no agent), sending a message that triggers a real tool call, and verifying the "Thought for X secs"
accordion + the tool-call chip in the thinking steps. Side-by-side against ELITEA-2209's own steps:

| ELITEA-2209 step | Expected | Covered by ELITEA-2215's merged test? |
|---|---|---|
| 1. Add toolkit via + > Toolkits (no agent) | Toolkit in PARTICIPANTS; **no AGENTS section** | **Setup step only adds the toolkit — does NOT assert the participants panel state.** GAP. |
| 2. Send message that triggers a tool call | "Thought for X secs" indicator appears | Step 1 (`chat.answer_thought_accordion` visible) — covered |
| 3. Expand "Thought for X secs" section | Thinking steps show the tool call | Covered, with a live-confirmed CLARIFICATION: the accordion is already auto-expanded for the whole streaming window (`ApplicationThinkView.jsx`'s `expanded={isStreaming || expanded}`) — no manual expand action is needed or correct. Same clarification applies verbatim to this case's step 3. |
| 4. Tool call shown as chip `"toolkit_name.tool_name"` (e.g. `"aaa: create_file"`) | Chip visible with icon | Covered, with a live-confirmed CLARIFICATION: the case's OWN example (`"aaa: create_file"`) is already colon-separated, contradicting its own "dotted" format description — the live rendered format IS `"{toolkit_name}: create_file"` (`chat.answer_tool_chip`, `ActionView.jsx`'s `buildTitle()`). Same clarification, same assertion, same handle. |

**Only ELITEA-2209's step 1 is unproven by the merged spec** — the covering test's Setup step calls
`chat.add_toolkit_participant(toolkit_name)` and moves straight to sending the message; it never reads
the participants panel to confirm the toolkit landed in the right section or that no AGENTS section
appeared. This is a genuinely small, isolable gap — not a near-rewrite — so `extend-existing` (not
`ready-for-automation`) is the correct call.

**Live-confirmed this pass** (project 399 "Private", fresh blank conversation, `AutoTest Confluence
Toolkit 1787` added via + > Toolkits > search > select): once a toolkit is added as sole participant, a
**collapsed participants badge for the `toolkits` section appears** in the composer's top-right control
row (screenshot: `.playwright-mcp/page-2026-08-19T12-53-41-658Z.png`) — confirming
`CollapsedPerticapantsList.jsx`'s per-`ENTITY_SECTIONS`-section badge (`chat-participants-badge-{section}`,
`section: "toolkits"`) renders for a toolkit-only conversation, and **no `agents` badge renders**
(no agent was added). This is the exact mechanism `is_participants_badge_visible()` already asserts in
three OTHER merged specs (`test_slash_mention_toolkit_tool_selection.py`,
`test_slash_mention_toolkit_and_mcp_participants.py`, `test_slash_mention_empty_state.py`) for the
identical `section="toolkits"` / `section="agents"` pair — so the handle is proven, not newly invented.

**Caution, not a defect (test-data note, not case-blocking):** the specific toolkit used for this live
probe (`AutoTest Confluence Toolkit 1787`, seeded test data) is itself misconfigured — selecting it
fired a `400 Bad Request` on `GET .../toolkit_validator/prompt_lib/399/2945` and the badge rendered in
its **error/attention variant** (`AttentionIcon`, "Misconfiguration error in toolkits", visible in the
cited screenshot) rather than the plain variant. This is unrelated to ELITEA-2209/2215's own subject
(stale/broken credentials on ONE seeded toolkit, not a product defect in the participants-panel
mechanism) and does not affect the classification — the badge existing (even in error styling) is
itself the proof that the toolkit registered as a participant and rendered under the `toolkits` section,
not the `agents` one. **Recommend the implementer reuse ELITEA-2215's own `artifact_toolkit` fixture**
(already used by the covering test, confirmed properly configured) for this extension's assertion,
not the Confluence toolkit used for this scouting probe.

## Preconditions
- Same as the covering spec: an Artifact-type toolkit (`artifact_toolkit` fixture, `ToolkitAPI.create_artifact_toolkit`) is added as the ONLY participant in a fresh conversation, via "+ > Toolkits" (no agent).

## Test Data
- No new test data. Reuses the covering spec's existing `artifact_toolkit` fixture and `MESSAGE_TEXT`/`TOOL_NAME`/`EXPECTED_FILE_KEY` constants verbatim (`automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py:146-148`).

## Test Steps
1. (Existing, unchanged) Setup — add the artifact toolkit as the only participant
   (`test_direct_toolkit_call_complete_flow.py:213`).
   - **NEW Verify (this case's step 1, the gap):** `chat.is_participants_badge_visible(section="toolkits")`
     is `True` (toolkit registered as a participant, collapsed badge visible) AND
     `chat.is_participants_badge_visible(section="agents")` is `False` (no agent was added — the
     no-AGENTS-section requirement the case text states explicitly).
2.–5. (Existing, unchanged) — send message, thinking-steps chip, response — exactly as implemented in
   the covering spec's Steps 1–3, already proven per the Overlap check table above.

## Expected Results
- Same as the covering spec, PLUS: immediately after adding the toolkit as sole participant, the
  participants panel shows it under the TOOLKITS section (collapsed badge present) and shows NO
  AGENTS section (badge absent) — confirming ELITEA-2209's own case-text precondition, which the
  covering test's Setup step performs but never asserts.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Add toolkit via + > Toolkits (no agent) | Toolkit in PARTICIPANTS; no AGENTS section | step 1 (NEW gap assertion) | new assertion in covering spec's Setup step | **gap — to be added** |
| 2 Send message triggering tool call | "Thought for X secs" appears | covering spec Step 1 | `test_direct_toolkit_call_complete_flow.py:217-224` | asserted (reused, already merged) |
| 3 Expand "Thought for X secs" section | Thinking steps show the tool call | covering spec Step 2/2b/3 | `test_direct_toolkit_call_complete_flow.py:226-260ish` | asserted (reused) *(clarification: accordion is already auto-expanded, no click needed — same live mechanism ELITEA-2181 uses)* |
| 4 Tool call shown as chip `toolkit_name.tool_name` (e.g. `aaa: create_file`) | Chip visible with icon | covering spec Step 3 (chip assertion) | same file | asserted (reused) *(clarification: live format is colon-separated `"{name}: {tool}"`, matching the case's OWN example despite its "dotted" description — no new drift, same drift ELITEA-2215 already documented)* |
| Expected Final State: tool call visible in thinking steps | — | covering spec, all steps | — | asserted (reused, composite) |

**Axis 2 — Analyst additions**
- None beyond the case's own step 1 gap — this extension adds no observable beyond what ELITEA-2209's
  own case text already requires.

## Cleanup
Same as the covering spec (delete toolkit, delete bucket) — no new cleanup needed for the added
assertion (it reads state already present after Setup, no new writes).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Toolkits collapsed participants badge | `[data-testid="chat-participants-badge-toolkits"]` | on-`automation/testids` (ELITEA-1793 rework; used by 3 other merged specs — confirmed live this pass) | `ChatPage.is_participants_badge_visible(section="toolkits")` (pre-existing method, `chat_page.py:6860`) |
| Agents collapsed participants badge (for the negative/absence check) | `[data-testid="chat-participants-badge-agents"]` | same rework | `ChatPage.is_participants_badge_visible(section="agents")` — same method, `section="agents"`. Per the method's own docstring, this container is **absent from the DOM entirely** when the agents count is 0 (not rendered showing "0") — assert via this method's boolean return, never a text-content check. |

No new testid needed — both handles are pre-existing and already exercised by other merged specs on
their own executed paths.

## Network Behavior
No new network behavior beyond the covering spec's — adding a toolkit participant is already covered
by `chat.add_toolkit_participant()`'s existing `wait_for_network()` call.

## Known Defects Found During Exploration
None NEW. The misconfigured-toolkit `400` noted in the Overlap check above is a stale-test-data
observation (unrelated seeded Confluence toolkit credentials), not a defect in scope for this case —
flagging so the implementer doesn't reuse that specific toolkit for the new assertion.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is an ADDED assertion inside the EXISTING covering
  test method** (`test_direct_toolkit_call_complete_flow`, same class/file), not a new test method —
  the gap is a single Setup-time check on state the existing test already reaches, and duplicating the
  whole `artifact_toolkit`/bucket fixture setup for one assertion would be wasteful.
- **Place the new assertion INSIDE the existing `allure.step("Setup — add the artifact toolkit as the
  only participant")` block, immediately after `chat.add_toolkit_participant(toolkit_name)`** — i.e.
  BEFORE the message is sent and BEFORE the covering test's known-defect (`#1127`) classification logic
  (Step 2b) runs. This keeps the new assertion a **plain, unconditional `assert`** (or a fresh
  `allure.step`), NOT routed through the existing `soft_failures` aggregation — participants-panel
  rendering is unrelated to #1127's mechanism (tool-call-intent leaking as text), so it should be a
  hard, independent check, not coupled to that known defect's classification.
- Add: `assert chat.is_participants_badge_visible(section="toolkits"), "expected a toolkits participants badge after adding the toolkit"` and `assert not chat.is_participants_badge_visible(section="agents"), "no agent was added — the agents badge must be absent"`.
- No new `@pytest.mark` needed — priority/feature markers unchanged from the covering test (`p2`, `chat`, `regression`).
- Reference ELITEA-2209's own TMS case in a second `@allure.issue(...)` decorator alongside the
  existing ELITEA-2215 one, same pattern as any multi-case-covering spec in this suite.
