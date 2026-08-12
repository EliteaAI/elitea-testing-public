# Test Case: Build with AI — suggested resources require explicit selection before creation

## Metadata
- **TMS ID**: ELITEA-1908
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Status**: `extend-existing`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project "UI Testing" / `${ELITEA_PROJECT_ID}`=400)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS (ELITEA-1903/1905/1906/1907/1909/1911/1914/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout (now recurring 8×).

## Extension target

- **Covering spec (existing, merged onto this batch's trunk — `tests/batch-1298-agents-build-with-ai`, confirmed via `git log`/file read, class-and-method line numbers below)**: `automation/tests/ui/agents/test_agent_build_with_ai.py`, class `TestAgentBuildWithAISelectedResourcesAttached` (line 515):
  - `test_selected_suggested_resources_attached_and_non_selected_absent` (ELITEA-1909, line 528)
  - `test_selected_suggested_skill_attached_and_non_selected_absent` (ELITEA-1911, line 705)
  - `test_approve_with_no_resources_creates_agent_and_appears_in_list` (ELITEA-1914, line 892)
- **Covering AFS**: `test-specs/agents/l2_build-with-ai-selected-suggested-resources-attached-to-created-agent_ELITEA-1909.md`, `test-specs/agents/lextend_build-with-ai-selected-suggested-skills-attached-to-created-agent_ELITEA-1911.md`, `test-specs/agents/lextend_build-with-ai-approve-creates-agent-and-navigates-to-agent-menu_ELITEA-1914.md`.

## Behavioural overlap (why this is `extend-existing`, not fresh) — and the genuine gap

I triangulated this case against all three existing tests in the class before executing anything live, per the dispatch's instruction — then confirmed the gap live.

**What ELITEA-1909/1911 already prove:** clicking "Create Agent" after selecting **some** suggested resources (one Toolkit + one Agent in 1909; one Skill in 1911) attaches exactly the selected items, and a **sibling, deliberately-unselected** item of the *same category* is absent (`test_agent_build_with_ai.py:686-689`, `:866-876`). This proves selection *discriminates* between two items on offer — but in both tests **at least one relation call always fires** (the toolkit-PATCH and agent-relation-PATCH in 1909; the skill GET+PATCH in 1911). Neither test ever exercises the "zero selections at all" path.

**What ELITEA-1914 already proves:** approving a **plain draft with no suggested resources rendered at all** (`suggested_toolkits`/`suggested_mcp`/`suggested_pipelines`/`suggested_agents`/`suggested_skills` all `[]`) creates the agent via the base-create POST only, with the Skills counter reading `"0/N skills added."` (`test_agent_build_with_ai.py:892-989`). This is the negative control for "nothing was ever offered" — but it is a **structurally different code path** from ELITEA-1908: `ResourceSuggestions.jsx`'s `if (!items?.length) return null` means no section, no card, no checkbox ever renders, so there is nothing for the case's own step 2 ("do NOT select any suggested resource" — implying resources exist and are visibly skippable) to actually exercise.

**The genuine gap ELITEA-1908 asks for, confirmed by re-reading every merged test in the file (Coverage Map below) plus the class docstring (`test_agent_build_with_ai.py:515-519`, "non-selected suggested resources are absent" — always phrased per-sibling-item, never per-full-zero-selection):** no test in this file generates a draft where suggested resources ARE rendered across **multiple categories simultaneously** (cards visible, checkboxes present and clickable) and then approves with **literally zero** boxes checked, verifying that (a) **no** toolkit/agent/pipeline/mcp/skill relation call fires at all — not even for one item — and (b) the created agent's Tools/Skills sections are empty across **every** category, not just the one sibling item 1909/1911 leave unchecked. This is the case's actual Pass criterion ("The created agent has no Toolkits, Agents, Pipelines, or MCPs attached, confirming that skipping selection results in no auto-attached resources") and it has never been asserted as a *combined, all-category* zero.

The overlap is large (same modal, same mock-payload technique ELITEA-1907 already established for multi-category suggestions, same class, same `agent_api` cleanup fixture, same `click_approve_and_wait_for_agent_created()` helper ELITEA-1914 already added) — a fresh `.spec.ts`-equivalent test class would re-derive all of that. Hence `extend-existing`: a new sibling test method in the same class (the exact shape ELITEA-1911 and ELITEA-1914 already used to extend this same class), per the Gap assertions below.

## Preconditions
- User is logged in to Elitea with sufficient permission to open "Build with AI" (`${TEST_USER}` rendered `generate-agent-open-button` live in this run — same permission finding as every prior case in this family).
- A project is selected/accessible ("UI Testing", id `400` in this run).
- **Live-data-availability limitation, live-reproduced this run (matches the open bug `EliteaAI/elitea-testing-public#1081` flagged for ELITEA-1909's "Suggested Agents" section):** the live-verified prompt from ELITEA-1907's AFS (`"An agent that queries GitHub and runs Jira updates"`, previously observed in project 399 to reliably suggest one MCP, `Remote Github`/id 3) produced **zero** suggestions of any category in THIS project (400, "UI Testing") — confirmed via the network response body (`suggested_toolkits: [], suggested_mcp: [], suggested_pipelines: [], suggested_agents: [], suggested_skills: []`, see Test Steps step 1 and Known Defects/Gaps). This is a test-data/environment gap, not a functional defect (root-caused identically to ELITEA-1907's finding: the suggestion engine draws from project-configured resources filtered by relevance, and project 400 currently has none relevant to this prompt). **Per this run's dispatch instructions, not re-filed** — noted here and resolved the same way ELITEA-1906/1907/1915 already resolve it: mocking `generate_application_draft`'s response.

## Test Data

### mocked (sidesteps the live-data-availability gap — same technique as ELITEA-1907/1906/1915)
- Reuse `SUGGESTED_RESOURCES_DRAFT_PAYLOAD` (already defined in `test_agent_build_with_ai.py:155-197` for ELITEA-1907) verbatim, or an equivalent payload with the same shape: `suggested_toolkits`, `suggested_mcp`, `suggested_pipelines`, `suggested_agents` all non-empty (one item each), `suggested_skills` empty (Skill's zero-selection path is out of this case's scope — ELITEA-1911 already covers Skill selection/non-selection specifically; this case's four named categories per the case's own Pass criteria are Toolkits/Agents/Pipelines/MCPs, not Skills).
- Prompt text: reuse `SUGGESTED_RESOURCES_PROMPT_TEXT` (`"An agent that queries GitHub and runs Jira updates"`, `test_agent_build_with_ai.py:112`) — the mock intercepts the response regardless of live suggestion availability, so the exact prompt wording only needs to enable the Generate button (any non-empty text does).
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is left behind — the created Agent (base-create POST is the only network write this scenario fires — see Network Behavior) is deleted in Cleanup via the existing `agent_api.delete_agent()` `finally`-block pattern.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`. Click **"Build with AI"** (`data-testid="generate-agent-open-button"`) to open `GenerateAgentModal`. Fill the prompt textarea (`data-testid="generate-agent-prompt-input"`) with a resource-implying prompt, click **"Generate"** (`data-testid="generate-agent-submit-button"`).
   - **Verify (live-reproduced this run, confirms the mocking rationale above)**: with the live-verified prompt `"An agent that queries GitHub and runs Jira updates"` in project 400, `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/400` resolved `200` with **all five `suggested_*` arrays empty** — no "Suggested {Category}:" section rendered at all (confirmed via accessibility snapshot: the review form shows only Name/Description/Instructions/Welcome Message/Chat starters, no `generate-agent-resource-section-*` element). This live run is a Preconditions/environment finding, not this case's own scripted assertion — the implementer mocks the response instead (Test Data above) so the case's own steps 2-5 can actually exercise multi-category suggestion cards.
   - **Verify (implementer, via the mock)**: the review form renders **"Suggested Toolkits:"**, **"Suggested MCP:"**, **"Suggested Pipelines:"**, and **"Suggested Agents:"** sections (`modal.is_resource_section_visible(entity_type)` → `True` for `"toolkit"`, `"mcp"`, `"pipeline"`, `"agent"`), each with one unchecked card — this is ELITEA-1907's already-merged step 3/5 assertions, re-run here as this test's own precondition-confirmation before the case's real point (steps 2-5) begins.

2. In the review form, do **NOT** select any suggested resource.
   - **Verify**: `modal.is_resource_checked(entity_type, item_id)` returns `False` for every rendered card across all four categories (toolkit id 101, mcp id 3, pipeline id 202, agent id 303, per the mock payload) — reusing ELITEA-1907's step-5 assertion pattern, but as this case's own explicit "did not touch any checkbox" confirmation immediately before approving (not merely the generation-time default state 1907 checked).

3. Click **"Approve"/"Create Agent"** (`data-testid="generate-agent-approve-button"`).
   - **Verify — the case's core assertion, source-confirmed (see Automation Hints for the exact grep)**: `GenerateAgentModal.jsx`'s `associateToolkits`/`associateApplications`/`associateSkills` each guard on `if (!versionId || !items.length) return;` (lines 121/140/179) — with every selection `Set` empty, **all three association callbacks return immediately without calling `associateToolkit`/`updateApplicationRelation`/`updateSkillRelation`**, regardless of how many resources were suggested/rendered. This means only `POST /api/v2/elitea_core/applications/prompt_lib/{project}` fires — use `modal.click_approve_and_wait_for_agent_created()` (already added for ELITEA-1914, `generate_agent_modal_page.py:357-374`; waits ONLY on the base-create POST — `click_approve_and_wait_for_creation()` would hang, since it `expect_response`s the toolkit-PATCH and agent-relation-PATCH that this scenario never fires).
   - **Verify (network-level negative assertion)**: capture requests matching `/elitea_core/tool/prompt_lib/`, `/elitea_core/application_relation/prompt_lib/`, and `/elitea_core/skill/prompt_lib/` from just before the approve click (same `capture_requests_matching()` helper ELITEA-1911 already uses, `base_page.py:239`) — assert the captured list is empty after creation. This is the strongest possible proof of "no auto-attachment": not just "the specific sibling item is absent" (1909/1911's per-item check) but "the relation endpoint was never called for **any** suggested item, across **every** category."

4. Open the created Agent (auto-navigation on the `201` response, same as every other test in this class).
   - **Verify**: `page.wait_for_url(f"**/agents/all/{created_agent_id}**")`; `AgentDetailPage.wait_for_page_load()`; URL contains `/agents/all/{created_agent_id}`.

5. Verify no Toolkits, Agents, Pipelines, or MCPs were automatically attached.
   - **Verify (Toolkit, MCP, Agent — source-confirmed shared component)**: `detail_page.is_toolkit_attached(name)` returns `False` for the mock payload's toolkit name (`"GitHub Toolkit"`), MCP name (`"Remote Github"`), and agent name (`"Jira Triage Agent"`). Source-confirmed this run (`generate_agent_modal_page.py:300-306`'s docstring on `add_mcp()`): *"MCP and Toolkit cards share the same `ToolCard.jsx` component and `agent-toolkit-card` / `agent-toolkit-delete-button` testids, so no MCP-specific card/removal methods are needed"* — and ELITEA-1909's own merged test already uses `is_toolkit_attached()` successfully for a nested **Agent** (`test_agent_build_with_ai.py:679`), confirming the same generic Tools-section-card check covers Toolkit/MCP/Agent uniformly.
   - **Verify (Pipeline — source-inferred, flagged as NOT independently live-verified)**: `detail_page.is_toolkit_attached("Jira Update Pipeline")` returns `False`. Source-confirmed (`EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/GenerateAgentModal.jsx:256-262`): `selectedPipelines` is concatenated with `selectedAgents` into one array and passed to the SAME `associateApplications()` call that handles nested Agents (`await associateApplications(versionId, entityId, [...selectedAgents, ...selectedPipelines])`) — i.e. Pipelines attach via the identical `application_relation` PATCH and (by inference from the shared association mechanism) the identical `ToolCard.jsx` rendering as Agents. **This inference was never live-observed with an actual Pipeline attachment in this project** (no live Pipeline suggestion was ever available to check against) — flagged for the implementer to visually confirm against the mocked Pipeline card during implementation (a quick `page.pause()`/screenshot check), not to block automation on.
   - **Verify (Skills counter, negative control, same pattern as ELITEA-1914)**: `detail_page.get_skills_counter_text()` starts with `"0/"` — confirms no Skill-type resource was attached either (this case's mock payload's `suggested_skills` is empty, so this doubles as a sanity check that the mock matches Test Data).

## Expected Results
Matches the case's stated Pass criteria in full: with suggested resources rendered across all four named categories (Toolkits, Agents, Pipelines, MCPs) and none explicitly selected, clicking "Approve"/"Create Agent" creates the agent via the base-create call alone — no toolkit/agent-relation/pipeline-relation/mcp-relation call ever fires (source-confirmed, not merely DOM-observed) — and the created agent's Tools section and Skills counter both confirm zero attachments across every category.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: admin/editor role | Build with AI accessible | step 1 | `generate-agent-open-button` rendered and clickable for `${TEST_USER}` | asserted |
| Precondition: draft with Suggested Resources produced | review form + Suggested Resources section shown | step 1 | live run showed the environment can't reliably produce multi-category suggestions (Preconditions); resolved via the ELITEA-1907-precedent mock | asserted *(via mock — see Preconditions)* |
| 1 Generate draft with suggested Toolkits/Agents | Suggested Resources section displayed | step 1 | `is_resource_section_visible()` True for all 4 categories (mocked payload) | asserted |
| 2 Do NOT select any suggested resource | all cards remain unselected | step 2 | `is_resource_checked()` False for every rendered item, explicit re-check immediately before approve | asserted *(new: 1907 only checks this at generation time, not immediately pre-approve)* |
| 3 Click "Approve"/"Create Agent" | agent creation initiated | step 3 | `approve_button.click()` via `click_approve_and_wait_for_agent_created()` → base-create POST fires | asserted |
| 4 Open the created Agent | Agent detail page displayed | step 4 | `page.wait_for_url()`, `wait_for_page_load()`, URL assertion | asserted |
| 5 Verify no Toolkits/Agents/Pipelines/MCPs attached | none appear in the created agent | step 5 | `is_toolkit_attached()` False ×4 (toolkit/mcp/agent source-confirmed shared component; pipeline source-inferred, flagged) + Skills counter "0/" | asserted *(pipeline sub-case flagged — see step 5 note)* |

### Axis 2 — Analyst additions

- step 3 documents the exact source guard (`GenerateAgentModal.jsx:121/140/179`, `if (!items.length) return;`) that GUARANTEES zero relation calls for a full-zero selection, regardless of how many resources were suggested — *added: this is the mechanism proof an implementer needs so the assertion isn't merely "I didn't see a card appear" but "the code path that would fire the call was never entered," matching this project's reverse-masking-guard style of citing source, not just DOM observation.*
- step 3's network-capture negative assertion (`capture_requests_matching` on all three relation-endpoint substrings) — *added: neither 1909 nor 1911 assert a **combined, all-endpoint** absence; each only checks that ONE specific sibling item's relation call didn't fire, while a DIFFERENT item's relation call for the SAME category legitimately did. This case is the first to assert zero relation traffic of any kind.*
- step 5's Pipeline sub-case flag — *added: this is the one part of the case's literal Pass criteria ("Toolkits, Agents, Pipelines, or MCPs") that could not be either live-verified (no live Pipeline suggestion ever available in this project across this whole case family) or confirmed via an existing merged test (no test in this file has ever exercised a Pipeline-type suggestion, selected or not). The source-level inference (shared `associateApplications`/`application_relation` mechanism with Agents) is sound but explicitly flagged as unverified-by-observation, per this project's declared-improvisation discipline.*

## Cleanup
1. Created agent (id from `create_response.json()["id"]`) — deleted via `agent_api.delete_agent(created_agent_id)` in a `finally` block, the same pattern ELITEA-1909/1911/1914 already use (`test_agent_build_with_ai.py:690-696`, `:877-883`, `:983-989`).
2. No temporary fixtures created (mock payload is inline, not a DB fixture) — nothing else to tear down.
3. No product state left behind beyond the created-then-deleted agent.

## Concrete Handles (discovered during exploration — all already present, confirmed live/via file read this run)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `page.get_by_test_id("generate-agent-open-button")` | on-main ✓ (confirmed live this run) | n/a — already present |
| Prompt textarea | `page.get_by_test_id("generate-agent-prompt-input")` | on-main ✓ (confirmed live) | n/a — already present |
| Generate button | `page.get_by_test_id("generate-agent-submit-button")` | on-main ✓ (confirmed live) | n/a — already present |
| Suggested-resource section title (per category) | `GenerateAgentModalPage.RESOURCE_SECTION` template (`generate_agent_modal_page.py:150`) via `is_resource_section_visible()` | on-main ✓ (landed for ELITEA-1907, per that AFS's Implementer Amendment) | n/a — already present |
| Suggested-resource checkbox (per category+id) | `GenerateAgentModalPage.RESOURCE_CHECKBOX` template (`:152`) via `is_resource_checked()`/`select_resource()` | on-main ✓ | n/a — already present |
| "Create Agent" approve button | `page.get_by_test_id("generate-agent-approve-button")` | on-main ✓ (confirmed live) | n/a — already present |
| Attached-Tools card (Toolkit/MCP/Agent/[Pipeline, inferred]) | `AgentDetailPage.toolkit_card` (`data-testid="agent-toolkit-card"`) via `is_toolkit_attached(name)` | on-main ✓ (confirmed live, reused by ELITEA-1909's Agent check) | n/a — already present |
| Skills counter | `page.get_by_test_id("agent-skills-counter")` via `get_skills_counter_text()` | on-main ✓ (reused from ELITEA-1911/1914) | n/a — already present |

**Summary for the implementer:** no new `add-data-testid` work is needed — every element this case's steps touch already carries a testid landed by ELITEA-1907's (`resource-section`/`resource-checkbox`/…) or ELITEA-1914's (`approve-button` wait helper) prior implementation work. The one net-new artifact is the **test method itself** — no new page-object locators, one possible new page-object *method* only if `capture_requests_matching()`'s existing multi-substring support (verify signature — `base_page.py:239` takes a single `url_substring`, so three separate capture calls, one per endpoint, may be needed rather than one combined call) needs a small wrapper.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/{project_id}` → `200` (mocked per Test Data) — the only draft-generation call.
- `POST /api/v2/elitea_core/applications/prompt_lib/{project_id}` → `201` — creates the base agent. **This is the ONLY `elitea_core` write this scenario fires** — source-confirmed (see Test Steps step 3): the three association callbacks (`associateToolkits`/`associateApplications`/`associateSkills`) all early-return on an empty selected-items array, so `PATCH .../tool/prompt_lib/...`, `PATCH .../application_relation/prompt_lib/...`, and `GET`/`PATCH .../skill/prompt_lib/...` never fire — not even once, for any of the four rendered-but-unselected categories.
- `GET /api/v2/elitea_core/application/prompt_lib/{project_id}/{created_agent_id}` → `200` — fires automatically once the detail page mounts (same pattern as every other test in this class).

## Known Defects Found During Exploration

**No functional product defect found.** One environment/test-data gap, live-reproduced and already known:

1. **[Non-blocking, already-tracked as `EliteaAI/elitea-testing-public#1081`] Live suggestion generation in project 400 ("UI Testing") produced zero suggestions across all five categories for the live-verified GitHub/Jira prompt**, where the *same* prompt in project 399 (ELITEA-1907's exploration) reliably produced one MCP suggestion. This is the identical data-availability class of gap flagged for ELITEA-1909's "Suggested Agents" section (per this run's dispatch instructions). **Not re-filed** — resolved via mocking (Test Data), the same technique ELITEA-1906/1907/1915 already use for this exact family of tests.

## Blocked Steps
None. All 5 case steps have a defined, source-grounded automation path (mocked generation + source-confirmed association-guard behavior + existing page-object methods). The one caveat (Pipeline attachment-check not independently live-observed) is documented as a flagged inference in step 5 and Axis 2, not a blocker — the implementer verifies it once, during implementation, against the mocked card.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home: `automation/tests/ui/agents/test_agent_build_with_ai.py`, new sibling method in `TestAgentBuildWithAISelectedResourcesAttached` (same class ELITEA-1911/1914 already extended).
- Page objects: `GenerateAgentModalPage` (`automation/pages/generate_agent_modal_page.py`) and `AgentDetailPage` (`automation/pages/agent_detail_page.py`) — no changes needed, reuse existing methods per Concrete Handles.
- Mock technique: reuse `modal.mock_generate_success(SUGGESTED_RESOURCES_DRAFT_PAYLOAD)` — the exact same helper and payload constant ELITEA-1907's test already defines at `test_agent_build_with_ai.py:155-197` (no new payload constant needed unless the implementer prefers a case-specific one for clarity).
- Approve wait: `modal.click_approve_and_wait_for_agent_created()` (`generate_agent_modal_page.py:357-374`) — NOT `click_approve_and_wait_for_creation()`, which would hang waiting on relation-PATCH calls that never fire in this scenario (documented in ELITEA-1914's AFS Gap assertions #1, same rationale applies here).
- Network negative-assertion: `self.capture_requests_matching(url_substring)` (`base_page.py:239`) — start capture before the approve click (mirrors ELITEA-1911's `skill_requests = modal.capture_requests_matching(...)` pattern, `test_agent_build_with_ai.py:785`), one call per endpoint substring (`/elitea_core/tool/prompt_lib/`, `/elitea_core/application_relation/prompt_lib/`, `/elitea_core/skill/prompt_lib/`), assert each captured list is empty after creation.
- Source citations to verify once more at implementation time (grep, don't just trust this AFS): `grep -n "if (!versionId || !.*\.length) return" "../EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/GenerateAgentModal.jsx"` should show all three guards (lines ~121/140/179 this run); re-verify against `origin/main`/`automation/testids` at implementation time since this is a moving file.
