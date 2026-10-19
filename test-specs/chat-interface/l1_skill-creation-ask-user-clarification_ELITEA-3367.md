# Test Case: Skill creation from chat with missing information triggers Ask User clarification

## Metadata
- **TMS ID**: ELITEA-3367 (story `EliteaAI/elitea_issues#6239`), priority l1 (critical)
- **Environment**: DEV (`https://dev.elitea.ai/app`), user `${TEST_USER}`
- **Analyst**: qa-engineer, 2026-10-19
- **Status**: **blocked** (environment: DEV chat returns no AI reply in this sandbox; the Ask User card was never observed live)
- Case snapshot `.agents/automation/skills-builder-chat/cases/ELITEA-3367.md` was missing; read the case straight from the TMS repo file.

## Blocked Steps
Steps 1-6 all depend on a model reply. Live probe, 2026-10-19 (scripted, headless, storage state):
- Modules panel: `modules-toggle-skill_builder` and `modules-toggle-ask_user` both exist (11 toggles total, DOM order: image_generation, web_search, data_analysis, internal_mcp, skill_builder, project_context_builder, ask_user, planner, pyodide, swarm, lazy_tools_mode). Both toggled on via `ChatPage.ensure_module_toggle_checked()` without trouble.
- Sent `Create a skill for onboarding` (x2): one run showed an "Unknown error" AI bubble, the other stayed empty after ~85s. A control message `Say hello` with no modules got no reply either. Same env fault as ELITEA-3366 (see memory `dev_chat_ai_no_reply_and_center_banner`).
- Unblock: DEV chat must answer. Then execute steps 1-6 live and verify the handles below.

## Test Steps (from case; not executed live)
1. Enable Skills Builder + Ask User toggles (case precondition; both default OFF per new conversation as in ELITEA-3366). Send `Create a skill for onboarding`. Expect a clarifying-question card with 1-4 questions.
2. Card shows input controls: radio rows (single-select) or checkbox rows (multi-select), plus a free-text field.
3. Answer all, submit on the last step. Card closes; an answer summary renders.
4. Same card not shown again.
5. A `generated-entity-chip` appears (see ELITEA-3366 AFS for chip/canvas handles).
6. Open the chip; Name/Description/Instructions reflect the answers (assert topically, descriptions are AI-rephrased per 3366).

## Concrete Handles (SOURCE-DERIVED from EliteaUI `main` `chat-hitl-actions/ClarifyingQuestionControl.jsx`; NOT verified on DEV, verify before use)
| Element | Handle | Rung / provenance |
|---|---|---|
| Ask User toggle | `testid="modules-toggle-ask_user"` | rung 1, DEV ✓ (live) |
| Skills Builder toggle | `testid="modules-toggle-skill_builder"` | rung 1, DEV ✓ (live) |
| Clarifying card container | none | `suggested_testid="chat-clarifying-question-card"`; anchor on the free-text field's placeholder |
| Free-text answer field | `placeholder="Your option"` | rung 3/4, source only; `suggested_testid="chat-clarifying-question-custom-input"` |
| Continue / Skip button | role button, name `Continue` (when answered) or `Skip` | rung 2, source only; label flips by answered state; `suggested_testid="chat-clarifying-question-continue-button"` |
| Prev / Next question | `aria-label="Previous question"` / `"Next question"` | rung 2, source only |
| Option rows | `BaseCheckbox` mode radio (single) / checkbox (multi), label = option text | no testid; role radio/checkbox + name; verify |
| Answer summary after submit | `AskUserAnswerSummary`: text `"{n}. {question}"` + answer; no testid | `suggested_testid="chat-ask-user-answer-summary"` |
| Skill chip | `testid="generated-entity-chip"` | reuse `ChatPage.generated_entity_chip` / `open_generated_entity_chip()` (3366 branch) |

Behavioural notes from source: single-select option click auto-advances to the next question; the last question's Continue submits all answers as an object keyed by question id; the composer is NOT locked while a clarifying question is pending (typing a reply also answers it).

## Coverage Map (planned, unverified)
| Case element | Disposition |
|---|---|
| Step 1 card appears, 1-4 questions | blocked (env) |
| Step 2 input controls | blocked (env) |
| Step 3 submit closes card | blocked (env) |
| Step 4 card not re-shown | blocked (env) |
| Step 5 skill chip | blocked (env) |
| Step 6 fields reflect answers | blocked (env) |

## Known Defects / Clarifications
- The case does not say which Modules toggles must be on or that they are OFF by default; the live product needs explicit enabling.
- The model chooses the questions, so asserting specific question text would be flaky; assert count in 1..4, a control present, and card gone after submit.
