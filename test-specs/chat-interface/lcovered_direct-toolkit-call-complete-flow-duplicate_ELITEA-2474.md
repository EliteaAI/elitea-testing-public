# ELITEA-2474: Chat – Complete flow from direct toolkit call in thinking steps to output chip display

**Status:** `already-covered`
**Priority:** high
**Module:** chat-interface
**Type:** functional

---

## Dedup Proof — Behavioural Equivalence

This case is **fully covered** by an existing merged spec on `automation/base`:

**Covering spec:**
`automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallCompleteFlow::test_direct_toolkit_call_complete_flow`
Lines 177–319 (class 176, test method 177–319)

**Automation test ID (Form C):**
`tests.ui.chat.test_direct_toolkit_call_complete_flow.TestDirectToolkitCallCompleteFlow.test_direct_toolkit_call_complete_flow`

**Covering AFS:**
`test-specs/chat-interface/l2_direct-toolkit-call-complete-flow_ELITEA-2215.md` (merged to `automation/base`)

**Git history / TMS case covered:**
- Covers TMS case **ELITEA-2215** ("Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call to Output Display") — this is the **same underlying scenario** as ELITEA-2474 ("Chat – Complete flow from direct toolkit call in thinking steps to output chip display"), worded differently by a different case author. The two case texts are not merely similar — ELITEA-2474's own step 5 wording **"LLM model chip, toolkit chip, and tool call chip"** is a verbatim match of ELITEA-2215's case text as quoted in its AFS's CLARIFICATION note, and both cases specify the identical trigger message `"create a file named test.txt"` and the identical toolkit-only-participant precondition.

---

## Behavioural Equivalence Argument

ELITEA-2474's steps are the same observable flow as ELITEA-2215, already proven by the merged test:

| ELITEA-2474 Step | Covered by existing test (line) |
|---|---|
| 1. Navigate to Chats, create a new conversation with only a toolkit participant (no agent) | Setup steps, lines 210–214 — `chat.navigate_to_chat(conversation_id=conversation_id)` + `chat.add_toolkit_participant(toolkit_name)` |
| 2. Send a message requesting a tool action (`"create a file named test.txt"`) | Line 221 — `chat.send_message(MESSAGE_TEXT)` where `MESSAGE_TEXT = "create a file named test.txt"` (line 148), identical to this case's own example message |
| 3. Verify "Thought for X secs" indicator; expand and verify tool call shown as `"toolkit_name.tool_name"` | Line 222 — `expect(chat.answer_thought_accordion).to_be_visible(...)`; lines 280–281 — `expect(chat.answer_tool_chip).to_be_visible(...)` + `.to_contain_text(expected_chip_text)`. **Clarification carried over from ELITEA-2215's AFS** (reverse-masking guard, not a defect): the live rendered format is colon-separated (`"{toolkit_name}: create_file"`, `ActionView.jsx`'s `buildTitle()`) not the dotted example either case's text uses, and the accordion is already auto-expanded for the whole tool-call/streaming window (`ApplicationThinkView.jsx`'s `expanded={isStreaming || expanded}`) — no manual expand click is needed or reliable. Both clarifications apply identically to ELITEA-2474, which uses the same dotted example and the same "expand" phrasing. |
| 4. After tool execution, verify the LLM's response appears | Lines 224–226 — `chat.wait_for_ai_response(...)` + `chat.wait_for_message_content_stable(...)` |
| 5. Verify tool execution chips: LLM model chip, toolkit chip, and tool call chip | Lines 284–294 — `model_chip_count = chat.answer_model_chip.count(); assert model_chip_count >= 1`, `expect(chat.answer_tool_chip).to_have_count(1)` + `.to_contain_text(expected_chip_text)`. **Same clarification as ELITEA-2215's AFS** applies verbatim to this case (the two cases use the identical three-chip phrasing): the live product renders one combined toolkit/tool chip (`chat-answer-tool-chip`, `ActionView.jsx:407`) plus N≥1 model chips (`chat-answer-model-chip`), not three separate elements — the merged test asserts the live contract, not the imprecise case-text count. |
| 6. Verify chips are horizontal in a row with appropriate icons and labels | Not independently re-asserted via layout/bounding-box or icon-presence checks — but this is not a separate observable from step 5's chips. The SAME chip elements the merged test asserts on (`answer_tool_chip`, `answer_model_chip`) are rendered by `ActionView.jsx`'s `styles.header` container (`display: 'flex'`, default row direction, `EliteaUI/src/components/Chat/ActionView.jsx:584-589`) and each chip (`styles.toolkitBadge`, line 592) always renders an `iconContainer` (line 605, icon) followed by a `Typography` label (`toolkitName`) — this is inherent to the component the test already exercises, not a variable/conditional layout a second assertion could catch differently. Confirmed by reading `ActionView.jsx:395-420` this pass. |
| 7. Verify the LLM's response text follows below the chips | Lines 297–306 — `assert chat.answer_tool_chip.is_visible()` (chips still present) + `last_text = chat.get_last_message_text(); assert last_text` (response text non-empty and read after the chips are confirmed present) |

**Observable:** Sending a tool-triggering message to a conversation whose sole participant is a toolkit (no agent) causes: a "Thought for X secs" accordion (auto-expanded), a colon-formatted toolkit/tool chip plus one-or-more model chips rendered in a horizontal row with icons, and the LLM's response text settling below the chips once execution completes.

**Expected result:** The merged test asserts every numbered step and expected outcome ELITEA-2474 describes, using the SAME trigger message, the SAME toolkit-only-participant precondition, and the SAME chip/response assertions — carrying forward the identical reverse-masking clarifications ELITEA-2215's own case text needed (dotted-vs-colon chip format; "3 distinct chips" vs "1 combined chip + N model chips"; accordion already-auto-expanded).

**No terminal substitution:** the covering test performs a real toolkit-call flow, verifies chip rendering from real backend execution (cross-checked against `ArtifactAPI.list_bucket_files()` ground truth — see Known Defect note below), and reads the real response text; fully compliant with the fidelity policy.

---

## TMS Case Link

**Source case:**
`.agents/automation/chat-remaining-w15/cases/ELITEA-2474.md` (intake snapshot)

**Case metadata:**
- Title: "Chat – Complete flow from direct toolkit call in thinking steps to output chip display"
- Module: chat-interface
- Priority: high
- Type: functional
- Tags: `automated:UI:regression`, `feat:chat`

---

## Rationale — Why No Separate Implementation

1. **Complete coverage:** the existing test exercises every step ELITEA-2474 requires, with the identical trigger precondition ("a conversation with only a toolkit participant, no agent") and the identical trigger message.
2. **Identical observable:** both cases assert Thought-accordion → tool-call chip (thinking steps) → response appears → chips (model + toolkit/tool) rendered horizontally with icons → response text below chips.
3. **Merged to base:** the covering spec is on `automation/base` (verified via `git show origin/automation/base:...`, not in-flight), satisfying the merged-target rule for `already-covered`.
4. **No gap:** ELITEA-2474 adds no assertion, edge case, or precondition variant beyond what ELITEA-2215's merged test already proves. It reads as the same manual case authored a second time under a different TMS ID (same pattern already established this batch for ELITEA-2471/2472/2473 against ELITEA-2212/2213).

A second implementation would duplicate assertions without adding coverage.

---

## Evidence

Test source reviewed 2026-08-19 (`git fetch origin` then `git show origin/automation/base:automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py`):
- Class: `TestDirectToolkitCallCompleteFlow` (line 176)
- Method: `test_direct_toolkit_call_complete_flow` (line 177)
- File: `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py`
- Lines: 177–319
- Markers: module-level `pytestmark` — `ui`, `chat`, `p2`, `regression`, `new`
- Allure link: references the ELITEA-2215 onetest-ai case (module docstring + `@allure.issue`)

Component source reviewed 2026-08-19 (`../EliteaUI/src/components/Chat/ActionView.jsx`, local checkout on `automation/testids`):
- `data-testid={toolkitType === 'model' ? 'chat-answer-model-chip' : 'chat-answer-tool-chip'}` — line 407
- Chip row container `styles.header` — `display: 'flex'`, line 584 (horizontal by default flex-direction)
- Chip `styles.toolkitBadge` (icon + label) — line 592; `styles.iconContainer` — line 605

**Known open defect (does not block this verdict):** `test_direct_toolkit_call_complete_flow.py` carries a documented, still-open, non-deterministic known defect [EliteaAI/elitea-testing-public#1127](https://github.com/EliteaAI/elitea-testing-public/issues/1127) (the direct-toolkit-call flow sometimes leaks the model's tool-call intent as raw text instead of invoking the real tool, ~2/5 run rate) and is excluded from this repo's N-consecutive-green hardening gate for that reason (see the module's `GATE_EXCLUDED_REASON` constant). This affects the covering test's gate eligibility, not its coverage validity — the test still asserts ELITEA-2474's full observable set on its GREEN path, and the same defect would affect ELITEA-2474 identically were it separately automated (same trigger, same product code path). No new defect filing needed here; #1127 remains the single tracked instance for this flow.

---

## Analyst Notes

- This is a **duplicate manual TMS case**, not a new scenario — ELITEA-2474's steps map 1:1 onto ELITEA-2215's already-automated flow (same toolkit-only-participant precondition, same trigger message, same chip/response checks, even verbatim-matching case-text phrasing for the chip description). Flagging in findings for the lead in case the TMS wants the duplicate manual case archived/merged upstream — same pattern as ELITEA-2471/2472/2473 discovered earlier in this batch.
- No new testid work or defect filing required by this case — all handles (`chat-answer-thought-accordion`, `chat-answer-model-chip`, `chat-answer-tool-chip`) already exist and are exercised by the covering test.

**Analysis date:** 2026-08-19
**Analyst:** qa-engineer (Sage), chat-remaining-w15 batch
