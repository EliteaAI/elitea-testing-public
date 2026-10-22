# Test Case: Agent and Pipeline Builder work correctly when Skills Builder and Project Context Builder are enabled

## Metadata
- **TMS ID**: ELITEA-3372 (story `EliteaAI/elitea_issues#6239`), priority l1 (critical), regression
- **Environment**: DEV (`https://dev.elitea.ai/app`), user `${TEST_USER}`, Private project (575)
- **Analyst**: qa-engineer, live 2026-10-22 (scripted headless; Playwright MCP chrome is not installed here)
- **Status**: **blocked** (non-deterministic Ask User trigger on steps 3-4; steps 1-2, 5-12 execute and are deterministic)
- Snapshot read: `.agents/automation/agent-pipeline-builder-skills-2502/cases/ELITEA-3372.md`

## Live execution
Preconditions: new conversation FIRST, then Modules (`open_internal_tools_menu`) -> `ensure_module_toggle_checked` for `internal_mcp` ("Agent & Pipeline Builder"), `skill_builder`, `project_context_builder`, `ask_user`; all 4 read back checked; `close_modules_panel`. (Existing ChatPage helpers work unchanged; the 4 toggles coexist.)

| Step | Observed |
|---|---|
| 1-2 | Menu opens; all four toggles checked (`is_module_toggle_checked`). |
| 3 "Create an agent for customer support" | **Ask User NOT triggered in 5/5 fresh conversations.** Model calls `Elitea Applications: post_elitea_core_applications` directly (~12-20s) and creates "Customer Support Agent" (draft, GPT-4o). Case's expected clarifying card never appears. |
| 4-5 | N/a when no card; chip `generated-entity-chip` label `Customer Support Agent` (exactly 1) appears. |
| 6 "Create a pipeline for data processing" (fresh conversation) | Ask User card in **4/5** runs (~9s). 2 questions in the run that was answered (Q1 type of processing -> ETL, Q2 number of stages -> Simple). Not triggered when it follows the agent request in the same conversation (0 cards). |
| 7-8 | After picking an option per question and clicking `Continue`, `post_elitea_core_applications` runs, chip `ETL Data Pipeline` appears; answer summary `1. q / answer` in message. |
| 9-10 HITL approve | Needs a sensitive tool: Admin Guardrails (`GuardrailsAdminPage.add_sensitive_tool("jira","list_projects")`+`save_configuration`) + Jira toolkit (`jira` creds in .env.test) added via `ChatPage.add_toolkit_participant` AFTER modules were set. Message "Use the <toolkit> toolkit list_projects tool now and show me the project keys." -> `sensitive-action-panel` appears; `sensitive-action-authorize-button` -> panel hides, tool chip `<toolkit>: list_projects`, response lists 6 projects. With all 4 modules on. |
| 11-12 HITL reject | Same message again -> panel shown again; `sensitive-action-block-button` -> panel hides, LLM replies gracefully (references earlier results, no error). |
Side effects cleaned: 5 agents + 2 pipelines created by probes deleted via API; probe toolkit/credential deleted; sensitive-tool flag removed.

## Blocking issue
Ask User is model-discretionary (same class as ELITEA-3367): agent request never asked (0/5), pipeline request asked 4/5 and only in a fresh conversation. A 3x gate on the case's literal steps 3-4 cannot be deterministic, and steps 6-8 depend on conversation order. Case's Fail criterion ("Ask User does not trigger") is thus exactly the LLM variance, no stable product repro, no defect filed.
Options for lead: (a) keep blocked; (b) author-sign-off amended test data (prompt that forces clarification, e.g. explicitly "ask me clarifying questions first"); (c) implement steps 1-2, 5, 8, 9-12 deterministically plus a retry-until-card branch for 3-4/6-7 (fresh conversation per attempt, accept either branch only if card path is observed, otherwise FAIL not skip) - will not gate 3/3 reliably for the agent half.

## Concrete Handles (verified live on DEV)
| Element | Handle | Rung | suggested_testid |
|---|---|---|---|
| Module toggles | `modules-toggle-internal_mcp` / `-skill_builder` / `-project_context_builder` / `-ask_user` (ChatPage.ensure_module_toggle_checked) | 1 | - |
| Ask User card input | `input[placeholder="Your option"]` | 4 | `chat-clarifying-question-custom-input` |
| Option rows | role `radio` (click with force / row label) | 2 | `chat-clarifying-question-option-{}` |
| Submit | button `Skip` -> `Continue` once answered (last question needs explicit click) | 2 | `chat-clarifying-question-submit-button` |
| Entity chip | `generated-entity-chip` (`get_generated_entity_chip_labels()`); label = entity name | 1 | - |
| Tool chip | `chat-answer-tool-chip` text `Elitea Applications: post_elitea_core_applications` | 1 | - |
| HITL | `sensitive-action-panel`, `-authorize-button`, `-block-button` (ChatPage fields exist) | 1 | - |
Waits: card/chip within 9-20s; HITL panel < 90s. Never assert model-chosen names/questions beyond topical keywords (Agent label contained "Customer Support"; pipeline "Data Processing"/"ETL").

## Coverage Map
| Case element | Disposition |
|---|---|
| 1-2 Enable four modules | executed; deterministic |
| 3-4 Agent + Ask User + resume | executed; Ask User not triggered 0/5 -> blocked (nondeterministic) |
| 5 Agent chip | executed; deterministic |
| 6-7 Pipeline + Ask User + resume | executed; card 4/5 -> nondeterministic |
| 8 Pipeline chip | executed; deterministic |
| 9-10 HITL approve | executed; tool runs, conversation continues |
| 11-12 HITL reject | executed; panel re-shown, graceful reply |
Axis 2: assert modules checked (grounded: precondition silently lost otherwise); backend cleanup of created entities.

## Known Defects / Clarifications
- Case text implies the incomplete prompt reliably triggers Ask User; live it does not (clarification, not defect).
- Modules default OFF per conversation and toggles must be set after creating the conversation. Sensitive-tool precondition requires admin Guardrails config (project-wide, type-scoped; clean up).
- Created agents/pipelines must be deleted by name via AgentAPI/PipelineAPI (probe leftovers accumulate, 5 duplicates "Customer Support Agent").
- Sibling: ELITEA-3367 (same Ask User nondeterminism); HITL parts overlap `test_guardrails_live_reload.py::TestSensitiveToolLiveReload` (agent-embedded chat, authorize only) - not coverage for main-chat reject.
