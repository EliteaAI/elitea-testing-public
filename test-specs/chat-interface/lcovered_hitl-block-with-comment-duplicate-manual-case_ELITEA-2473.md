# ELITEA-2473: Chat – HITL Block with Comment prompts for comment and prevents tool execution

**Status:** `already-covered`
**Priority:** high
**Module:** chat-interface
**Type:** functional

---

## Dedup Proof — Behavioural Equivalence

This case is **fully covered** by an existing merged spec on `automation/base`:

**Covering spec:**
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionBlockWithComment::test_block_with_comment_records_reason_and_blocks_action`
Lines 365–435 (class 365, test method 376–435)

**Automation test ID (Form C):**
`tests.ui.chat.test_hitl_sensitive_action_authorization.TestSensitiveActionBlockWithComment.test_block_with_comment_records_reason_and_blocks_action`

**Git history:**
- Test authored/merged to `automation/base` in commit `ddaf8b31b` — "test: (2211,2212,2213,2214,2215) chat HITL sensitive-action authorization + direct toolkit-call flow"
- Covers TMS case **ELITEA-2214** ("Block with Comment Records the Reason and Blocks the Toolkit Action") — same underlying feature "HITL Block with Comment" as ELITEA-2473, worded differently by a different case author.

---

## Behavioural Equivalence Argument

ELITEA-2473's steps are the same observable flow as ELITEA-2214, already proven by the merged test:

| ELITEA-2473 Step | Covered by existing test (line) |
|---|---|
| 1. Navigate to a conversation with only a HITL toolkit participant, trigger a sensitive action | `_reach_sensitive_action_card()` helper (lines 96–125), invoked at line 388 |
| 2. Verify the "Sensitive Action Authorization Required" card appears | `_reach_sensitive_action_card()` step 3 (lines 121–123) — `chat.wait_for_sensitive_action_panel()` |
| 3. Click the Block with Comment button (gray) | Lines 394–399 — `chat.sensitive_action_block_with_comment_button.click()` |
| 4. Verify a modal or text input appears prompting for a comment | Lines 396–399 — `sensitive_action_block_comment_input` + `sensitive_action_block_comment_submit_button` asserted visible. **Case-text note (matches ELITEA-2214's own already-recorded clarification):** the case calls this a "modal", but it is source-confirmed to be an INLINE expansion on the same card (`BlockWithCommentControl.jsx`, `Collapse`-free conditional render), not an MUI `Dialog`. This is case-text imprecision only — the observable ("an input appears, submitting blocks the action") is unaffected. |
| 5. Type a comment (e.g. "This action is too risky and could delete important data") | Lines 401–405 — `press_sequentially(self.BLOCK_COMMENT, ...)`; `expect(...).to_have_value(self.BLOCK_COMMENT)`. `BLOCK_COMMENT` constant (line 367) is the **identical literal string** ELITEA-2473 uses as its example comment. |
| 6. Click Submit or Confirm | Lines 407–409 — `chat.sensitive_action_block_comment_submit_button.click()` |
| 7. Verify the modal closes and the action was blocked with comment | Line 409 — `expect(chat.sensitive_action_panel).to_have_count(0, ...)` |
| 8. Verify the LLM does NOT execute the sensitive toolkit tool and may reference the provided comment | Lines 411–419 (non-execution, backend-verified file survival) + lines 421–428 (loose "response does not claim success" signal — exact wording, including whether the LLM echoes the comment, is non-deterministic and noted as unverifiable locally in the covering AFS) |

**Observable:** Clicking "Block with Comment" expands an inline comment input on the card; typing and submitting a comment blocks the toolkit tool from executing (file survives, backend-verified), closes the card, and the LLM's follow-up response does not claim success.

**Expected result:** The merged test asserts every numbered step and expected outcome ELITEA-2473 describes — same trigger, same button, same comment-input flow (down to the identical example comment string), same submit behavior, same non-execution proof, same response check.

**No terminal substitution:** the covering test performs real UI interactions (click, type, submit) and verifies real backend file survival — nothing here is fabricated; fully compliant with the fidelity policy.

---

## TMS Case Link

**Source case:**
`.agents/automation/chat-remaining-w15/cases/ELITEA-2473.md` (intake snapshot)

**Case metadata:**
- Title: "Chat – HITL Block with Comment prompts for comment and prevents tool execution"
- Module: chat-interface
- Priority: high
- Type: functional
- Tags: `automated:UI:regression`, `feat:chat`

---

## Rationale — Why No Separate Implementation

1. **Complete coverage:** the existing test exercises every step ELITEA-2473 requires, with the identical trigger precondition and even the identical example comment text.
2. **Identical observable:** both cases assert card display → Block-with-Comment click → comment input appears → comment typed → submit → card closes → tool does NOT execute (backend-verified) → LLM response check.
3. **Merged to base:** the covering spec is on `automation/base` (commit `ddaf8b31b`, not in-flight), satisfying the merged-target rule for `already-covered`.
4. **No gap:** ELITEA-2473 adds no assertion, edge case, or precondition variant beyond what ELITEA-2214's merged test already proves — including the "modal" wording, which the covering AFS/test already flagged and resolved as case-text imprecision, not a defect. It reads as the same manual case authored a second time under a different TMS ID.

A second implementation would duplicate assertions without adding coverage.

---

## Evidence

Test source reviewed 2026-08-19 (`git show origin/automation/base:automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`):
- Class: `TestSensitiveActionBlockWithComment` (line 365)
- Method: `test_block_with_comment_records_reason_and_blocks_action` (line 376)
- File: `automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`
- Lines: 365–435
- Markers: module-level `pytestmark` — `p2`, `regression`, `guardrails`, `chat`, `ui`, `new`
- Allure link: references the ELITEA-2214 onetest-ai case (lines 368–372)

**Note on the `guardrails` marker:** same environment-limitation note as the sibling traceability AFSs (Admin Guardrails route not served on `localhost:5173`) — neither ELITEA-2473 nor its covering test ELITEA-2214 can be re-executed live from this analyst session; the dedup call rests on reading the merged test's source and confirming step-for-step equivalence against the case text, per the skill's Rule-6 dedup bar.

---

## Analyst Notes

- This is a **duplicate manual TMS case**, not a new scenario — ELITEA-2473's steps map 1:1 onto ELITEA-2214's already-automated flow, down to reusing the exact same example comment text ("This action is too risky and could delete important data"). Flagging in findings for the lead in case the TMS wants the duplicate manual case archived/merged upstream.
- No live re-execution was possible or necessary for this dedup call (see Evidence note above); the classification rests on direct comparison of case text against the merged test's assertions.
- Companion cases ELITEA-2471 (→ ELITEA-2212/Authorize) and ELITEA-2472 (→ ELITEA-2213/Block) show the same duplication pattern — all three of ELITEA-2471/2472/2473 are near-verbatim restatements of the ELITEA-2212/2213/2214 cluster analysed and automated 2026-08-03.

**Analysis date:** 2026-08-19
**Analyst:** qa-engineer (Sage), cluster run ELITEA-2471/2472/2473
