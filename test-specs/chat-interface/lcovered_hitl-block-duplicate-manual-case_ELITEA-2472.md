# ELITEA-2472: Chat – HITL Block button prevents toolkit tool from executing

**Status:** `already-covered`
**Priority:** high
**Module:** chat-interface
**Type:** functional

---

## Dedup Proof — Behavioural Equivalence

This case is **fully covered** by an existing merged spec on `automation/base`:

**Covering spec:**
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionBlock::test_block_prevents_toolkit_tool_from_executing`
Lines 283–360 (class 283, test method 292–360)

**Automation test ID (Form C):**
`tests.ui.chat.test_hitl_sensitive_action_authorization.TestSensitiveActionBlock.test_block_prevents_toolkit_tool_from_executing`

**Git history:**
- Test authored/merged to `automation/base` in commit `ddaf8b31b` — "test: (2211,2212,2213,2214,2215) chat HITL sensitive-action authorization + direct toolkit-call flow"
- Covers TMS case **ELITEA-2213** ("Click Block Prevents the Toolkit Tool from Executing") — same underlying feature "HITL Block button" as ELITEA-2472, worded differently by a different case author.

---

## Behavioural Equivalence Argument

ELITEA-2472's steps are the same observable flow as ELITEA-2213, already proven by the merged test:

| ELITEA-2472 Step | Covered by existing test (line) |
|---|---|
| 1. Navigate to a conversation with only a HITL toolkit participant, trigger a sensitive action | `_reach_sensitive_action_card()` helper (lines 96–125), invoked at line 303 |
| 2. Verify the "Sensitive Action Authorization Required" card appears | `_reach_sensitive_action_card()` step 3 (lines 121–123) — `chat.wait_for_sensitive_action_panel()` |
| 3. Click the Block button (red with X) | Lines 321–323 — `chat.sensitive_action_block_button.first.click()` |
| 4. Verify the authorization card closes / updates to show the action was blocked | Line 323 — `expect(chat.sensitive_action_panel).to_have_count(0, ...)` |
| 5. Verify the LLM does NOT execute the sensitive toolkit tool | Lines 325–332 — `remaining_files = artifact_api.list_bucket_files(bucket_name)`; asserts the fixture file is **still present** — backend-verified non-execution, not a UI-only signal |
| 6. Verify no tool execution chips appear for the blocked tool | Lines 350–355 — `expect(chat.answer_tool_chip).to_have_count(0)` (absence assertion) |
| 7. Verify the LLM responds indicating the action was blocked or not performed | Lines 334–341 — asserts the last message is non-empty and does not contain any of the `_SUCCESS_CLAIM_PHRASES` (a loose, resilient signal since exact LLM wording is non-deterministic) |

**Observable:** Clicking Block on the Sensitive Action Authorization card closes the card, the toolkit tool does NOT execute (file survives, backend-verified), no tool-execution chip renders, and the LLM's follow-up response does not claim success.

**Expected result:** The merged test asserts every numbered step and expected outcome ELITEA-2472 describes — same trigger (toolkit-only participant + sensitive action), same button, same card-close behavior, same non-execution proof, same chip-absence assertion, same "response indicates blocked" check.

**No terminal substitution:** the covering test performs a real Block click and verifies real backend file survival — nothing here is fabricated; fully compliant with the fidelity policy.

---

## TMS Case Link

**Source case:**
`.agents/automation/chat-remaining-w15/cases/ELITEA-2472.md` (intake snapshot)

**Case metadata:**
- Title: "Chat – HITL Block button prevents toolkit tool from executing"
- Module: chat-interface
- Priority: high
- Type: functional
- Tags: `automated:UI:regression`, `feat:chat`

---

## Rationale — Why No Separate Implementation

1. **Complete coverage:** the existing test exercises every step ELITEA-2472 requires, with the identical trigger precondition ("a conversation with only a HITL toolkit participant").
2. **Identical observable:** both cases assert card display → Block click → card closes → tool does NOT execute (backend-verified) → no chip renders → LLM response acknowledges the block.
3. **Merged to base:** the covering spec is on `automation/base` (commit `ddaf8b31b`, not in-flight), satisfying the merged-target rule for `already-covered`.
4. **No gap:** ELITEA-2472 adds no assertion, edge case, or precondition variant beyond what ELITEA-2213's merged test already proves. It reads as the same manual case authored a second time under a different TMS ID.

A second implementation would duplicate assertions without adding coverage.

---

## Evidence

Test source reviewed 2026-08-19 (`git show origin/automation/base:automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`):
- Class: `TestSensitiveActionBlock` (line 283)
- Method: `test_block_prevents_toolkit_tool_from_executing` (line 292)
- File: `automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`
- Lines: 283–360
- Markers: module-level `pytestmark` — `p2`, `regression`, `guardrails`, `chat`, `ui`, `new`
- Allure link: references the ELITEA-2213 onetest-ai case (lines 285–289)

**Note on the `guardrails` marker:** same environment-limitation note as ELITEA-2471's traceability AFS (Admin Guardrails route not served on `localhost:5173`) — neither ELITEA-2472 nor its covering test ELITEA-2213 can be re-executed live from this analyst session; the dedup call rests on reading the merged test's source and confirming step-for-step equivalence against the case text, per the skill's Rule-6 dedup bar.

---

## Analyst Notes

- This is a **duplicate manual TMS case**, not a new scenario — ELITEA-2472's steps map 1:1 onto ELITEA-2213's already-automated flow (same toolkit-participant precondition, same Block button, same non-execution + chip-absence + response checks). Flagging in findings for the lead in case the TMS wants the duplicate manual case archived/merged upstream.
- No live re-execution was possible or necessary for this dedup call (see Evidence note above); the classification rests on direct comparison of case text against the merged test's assertions.

**Analysis date:** 2026-08-19
**Analyst:** qa-engineer (Sage), cluster run ELITEA-2471/2472/2473
