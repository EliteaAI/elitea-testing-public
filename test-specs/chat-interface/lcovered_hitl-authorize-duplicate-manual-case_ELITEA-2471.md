# ELITEA-2471: Chat – HITL Authorize button executes toolkit tool directly

**Status:** `already-covered`
**Priority:** high
**Module:** chat-interface
**Type:** functional

---

## Dedup Proof — Behavioural Equivalence

This case is **fully covered** by an existing merged spec on `automation/base`:

**Covering spec:**
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionAuthorize::test_authorize_executes_toolkit_tool_directly`
Lines 206–279 (class 206, test method 215–279)

**Automation test ID (Form C):**
`tests.ui.chat.test_hitl_sensitive_action_authorization.TestSensitiveActionAuthorize.test_authorize_executes_toolkit_tool_directly`

**Git history:**
- Test authored/merged to `automation/base` in commit `ddaf8b31b` — "test: (2211,2212,2213,2214,2215) chat HITL sensitive-action authorization + direct toolkit-call flow"
- Covers TMS case **ELITEA-2212** ("Click Authorize Executes the Toolkit Tool Directly") — same underlying AI-agent feature "HITL Authorize button" as ELITEA-2471, worded differently by a different case author.

---

## Behavioural Equivalence Argument

ELITEA-2471's steps are the same observable flow as ELITEA-2212, already proven by the merged test:

| ELITEA-2471 Step | Covered by existing test (line) |
|---|---|
| 1. Navigate to a conversation with only a HITL toolkit participant, trigger a sensitive action | `_reach_sensitive_action_card()` helper (lines 96–125), invoked at line 226 — adds the artifact toolkit as the sole participant via "+ > Toolkits" (no agent) and sends an unambiguous `delete_file` message |
| 2. Verify the "Sensitive Action Authorization Required" card appears | `_reach_sensitive_action_card()` step 3 (lines 121–123) — `chat.wait_for_sensitive_action_panel()` |
| 3. Click the Authorize button (green with checkmark) | Lines 244–246 — `chat.sensitive_action_authorize_button.first.click()` |
| 4. Verify the authorization card closes / updates to show authorization was granted | Line 246 — `expect(chat.sensitive_action_panel).to_have_count(0, ...)` |
| 5. Verify the LLM proceeds to execute the authorized toolkit tool directly | Lines 248–256 — `expect.poll(_file_deleted, ...)` polls `ArtifactAPI.list_bucket_files()` until the fixture file is genuinely gone — backend-verified real execution, not a UI-only signal |
| 6. Verify tool execution chips appear (LLM model, toolkit, tool call) and the conversation continues normally | Lines 258–271 — model chip + `answer_tool_chip` (containing `"{toolkit_name}: delete_file"`) both asserted visible; composer re-editable and panel stays gone |

**Observable:** Clicking Authorize on the Sensitive Action Authorization card closes the card, causes the toolkit tool to genuinely execute against the backend (verified via `ArtifactAPI`, not just a UI signal), renders both a model chip and a toolkit/tool chip, and leaves the conversation usable.

**Expected result:** The merged test asserts every numbered step and expected outcome ELITEA-2471 describes — same trigger (toolkit-only participant + sensitive action), same button, same card-close behavior, same execution proof, same chip assertions, same "conversation continues normally" check.

**No terminal substitution:** the covering test performs a real Authorize click and verifies real backend file deletion — nothing here is fabricated; fully compliant with the fidelity policy.

---

## TMS Case Link

**Source case:**
`.agents/automation/chat-remaining-w15/cases/ELITEA-2471.md` (intake snapshot)

**Case metadata:**
- Title: "Chat – HITL Authorize button executes toolkit tool directly"
- Module: chat-interface
- Priority: high
- Type: functional
- Tags: `automated:UI:regression`, `feat:chat`

---

## Rationale — Why No Separate Implementation

1. **Complete coverage:** the existing test exercises every step ELITEA-2471 requires, with the identical trigger precondition ("a conversation with only a HITL toolkit participant").
2. **Identical observable:** both cases assert card display → Authorize click → card closes → tool executes (backend-verified) → chips render → conversation continues.
3. **Merged to base:** the covering spec is on `automation/base` (commit `ddaf8b31b`, not in-flight), satisfying the merged-target rule for `already-covered`.
4. **No gap:** ELITEA-2471 adds no assertion, edge case, or precondition variant beyond what ELITEA-2212's merged test already proves. It reads as the same manual case authored a second time under a different TMS ID.

A second implementation would duplicate assertions without adding coverage.

---

## Evidence

Test source reviewed 2026-08-19 (`git show origin/automation/base:automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`):
- Class: `TestSensitiveActionAuthorize` (line 206)
- Method: `test_authorize_executes_toolkit_tool_directly` (line 215)
- File: `automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`
- Lines: 206–279
- Markers: module-level `pytestmark` — `p2`, `regression`, `guardrails`, `chat`, `ui`, `new`
- Allure link: references the ELITEA-2212 onetest-ai case (lines 208–212)

**Note on the `guardrails` marker:** the underlying precondition (marking `delete_file` sensitive via Admin UI Guardrails) is not reachable on `localhost:5173` — the Admin Guardrails route 404s locally, a pre-existing, already-documented environment limitation (see ELITEA-2211's AFS § Preconditions and `test_guardrails_live_reload.py`'s own comment). This means neither ELITEA-2471 nor its covering test ELITEA-2212 can be re-executed live from this analyst session regardless of TMS ID — the dedup call here rests on reading the merged test's source and confirming step-for-step equivalence against the case text, which is sufficient per the skill's Rule-6 dedup bar (merged spec, cited at file:line, same observable/expected result).

---

## Analyst Notes

- This is a **duplicate manual TMS case**, not a new scenario — ELITEA-2471's steps map 1:1 onto ELITEA-2212's already-automated flow (same toolkit-participant precondition, same Authorize button, same execution + chip + continuation checks). Flagging in findings for the lead in case the TMS wants the duplicate manual case archived/merged upstream.
- No live re-execution was possible or necessary for this dedup call (see Evidence note above); the classification rests on direct comparison of case text against the merged test's assertions, which is textbook Rule-6 dedup.

**Analysis date:** 2026-08-19
**Analyst:** qa-engineer (Sage), cluster run ELITEA-2471/2472/2473
