# Test Case: Skill creation from chat with missing information triggers Ask User clarification

## Metadata
- **TMS ID**: ELITEA-3367 (story `EliteaAI/elitea_issues#6239`), priority l1 (critical)
- **Environment**: DEV (`https://dev.elitea.ai/app`), user `${TEST_USER}`, project Private
- **Analyst**: qa-engineer, re-executed live 2026-10-20 (supersedes the 2026-10-19 env-blocked pass: DEV chat answers again)
- **Status**: **blocked** (non-deterministic trigger). The whole flow was executed live and every step passes WHEN the card appears, but with the case's exact message the model asks via Ask User in only ~3 of ~17 fresh-conversation attempts (~18%); otherwise it guesses and creates the skill directly. A 3x gate cannot be green on that rate.
- Case snapshot `.agents/automation/skills-builder-chat/cases/ELITEA-3367.md` missing; read from the TMS repo file.

## Live execution (2026-10-20, scripted headless, conversation created BEFORE enabling toggles)
Preconditions: new conversation; Modules (hover `internal-tools-menuitem`) -> `ChatPage.ensure_module_toggle_checked("skill_builder")` and `("ask_user")`; `close_modules_panel`. Send `Create a skill for onboarding` (Enter).
1. (when asked) AI shows tool chip `Ask User: ask_user` and a card: heading text, small caps category label (e.g. `ONBOARDING FOCUS`), `1. <question>`, counter `1/2`, 3-4 radio rows (title + description), free-text `Your option`, `Skip` button, `Previous question`/`Next question` buttons. Observed 2 questions in 3/3 asked runs (1..4 OK).
2. Controls: single-select radio rows (`role=radio`, hidden `input[type=radio]`, readonly) + free text. No checkbox seen. Radio inputs are covered by an overlay div: Playwright needs the row label click, not the raw input (a plain `.click()` on the input timed out "intercepts pointer events"; `force=True` worked).
3. Picking an option auto-advances to Q2; after the last pick the `Skip` button flips to `Continue`; clicking it submits. Card disappears (0 `Your option` inputs). An answer summary renders in the message: `1. <question>` / `<chosen option>` / `2. ...`.
4. No second card appeared after submit (card count 0 for the remainder of the run).
5. AI continues: tools `Ask User: ask_user`, `post_elitea_core_generate_skill_draft`, `post_elitea_core_skills`; text "Created the employee-onboarding-checklist skill as a draft..."; exactly one `generated-entity-chip` labelled `employee-onboarding-checklist` (slugified name).
6. Chip -> `ChatPage.open_generated_entity_chip()` opens the Skill canvas: name `employee-onboarding-checklist`, description "Acts as a friendly, interactive employee onboarding checklist assistant..." - reflects answers (Employee onboarding + Interactive checklist), AI-rephrased.
Evidence: /tmp/3367-a.png (card), /tmp/3367-d.png (canvas); uploaded names `ELITEA-3367-step-1-card.png` if needed.

## Blocking issue - non-deterministic Ask User trigger
- Same exact message, fresh conversation each time, both toggles on: card in ~3/17 attempts; otherwise the model skips Ask User and creates a skill (e.g. `onboarding`, 18s). That is the case's own Fail criterion ("assistant guesses missing fields without asking"), but it is LLM variance, not deterministic (so the sanctioned-RED exception, which requires identical 3/3 failures, does not apply).
- Options for the lead: (a) accept blocked until product/prompt makes Ask User reliable; (b) approve a retry-until-card loop (fresh conversation per attempt, >=10 attempts, FAIL not skip when never asked) - expected pass ~85% at 10 attempts, ~7 min worst case, will not gate 3/3 reliably; (c) amend the case text/test data with a prompt that forces clarification (needs author sign-off). No product defect ticket filed (nondeterminism, no stable repro).
- Do NOT use the 3366-style "tool chip text" wait alone: wait on the card input `Your option` OR the `generated-entity-chip`, whichever comes first, to detect the no-ask branch quickly.

## Concrete Handles (verified live on DEV 2026-10-20 unless noted)
| Element | Handle | Rung / provenance | suggested_testid |
|---|---|---|---|
| Ask User toggle | `testid="modules-toggle-ask_user"` | rung 1, DEV ok | - |
| Skills Builder toggle | `testid="modules-toggle-skill_builder"` | rung 1, DEV ok | - |
| Ask User tool chip | `testid="chat-answer-tool-chip"` text `Ask User: ask_user` | rung 1, DEV ok | - |
| Card free-text field | `placeholder="Your option"` (unique while a card is open) | rung 3/4; ladder - no testid on DEV | `chat-clarifying-question-custom-input` |
| Option rows | role `radio` (hidden input; click the visible row/label by option text) | rung 2; no testid | `chat-clarifying-question-option-{}` |
| Skip / Continue | role button `Skip` (unanswered) -> `Continue` (answered) | rung 2; label flips | `chat-clarifying-question-continue-button` |
| Prev/Next | role button `Previous question` / `Next question` (aria-label) | rung 2 | - |
| Counter | text `1/2` inside card | text only; do not assert exact N | - |
| Answer summary | text `1. <question>` + chosen option after submit; no testid | ladder - text | `chat-ask-user-answer-summary` |
| Skill chip | `testid="generated-entity-chip"`; `ChatPage.get_generated_entity_chip_labels()` / `open_generated_entity_chip()` (on trunk) | rung 1 | - |
| Canvas fields | `skill-name-input-field`, `skill-description-input-field`, `skill-tags-input-field` (`SkillFormPage`) | rung 1 | - |

Waits: card appears after ~5-20s ("Thought for less than a second" accordion). Model/question text/option labels vary per run - never assert specific text; assert card count>0, 1<=questions<=4, radio/checkbox or text control present, card gone after submit, summary contains the clicked option text, chip label contains a topical keyword from the chosen option (e.g. `onboarding`). Dismiss `platform-banner-center` first and retry once (racy); create conversation BEFORE enabling toggles.

## Coverage Map
| Case element | Disposition |
|---|---|
| Step 1 card with 1-4 questions | executed live (3 asked runs); nondeterministic trigger -> blocked for automation |
| Step 2 input controls | executed: radio rows + free text |
| Step 3 submit closes card | executed: auto-advance, Skip->Continue, card closes, summary shown |
| Step 4 not re-shown | executed: 0 cards after submit |
| Step 5 skill chip | executed: one chip, slug of generated name |
| Step 6 fields reflect answers | executed: topical (employee / checklist); AI-rephrased |
| Axis 2 extra: answer summary renders | grounded: observed live |

## Known Defects / Clarifications
- The case does not say which Modules toggles must be on or that they are OFF by default; the live product needs explicit enabling.
- The model chooses the questions, so asserting specific question text would be flaky; assert count in 1..4, a control present, and card gone after submit.
- Case omits that both toggles default OFF; and that Ask User is model-discretionary (see Blocking issue).
