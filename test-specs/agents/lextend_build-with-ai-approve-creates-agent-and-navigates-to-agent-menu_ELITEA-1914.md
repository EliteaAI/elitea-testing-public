# Test Case: Build with AI — Approve creates the agent and navigates to Agent menu

## Metadata
- **TMS ID**: ELITEA-1914
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Status**: `extend-existing`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project "UI Testing" / `${ELITEA_PROJECT_ID}`=400)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS (ELITEA-1903/1905/1906/1907/1909/1911/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.

## Extension target

- **Covering spec (existing, merged onto this batch's trunk — `tests/batch-1298-agents-build-with-ai`, confirmed via `git log`, class-and-method line numbers below)**: `automation/tests/ui/agents/test_agent_build_with_ai.py:497-679`, class `TestAgentBuildWithAISelectedResourcesAttached`, method `test_selected_suggested_resources_attached_and_non_selected_absent` (`automation/tests/ui/agents/test_agent_build_with_ai.py:510`).
- **Covering AFS**: `test-specs/agents/l2_build-with-ai-selected-suggested-resources-attached-to-created-agent_ELITEA-1909.md`.

## Behavioural overlap (why this is `extend-existing`, not fresh) — and the genuine gap

ELITEA-1909's implemented test (Step 5, `automation/tests/ui/agents/test_agent_build_with_ai.py:609-635`) already proves the **core shape** ELITEA-1914 asks for: clicking "Create Agent" fires `POST .../applications/prompt_lib/{project}` → `201`, and the UI auto-navigates to the created agent's detail page (`page.wait_for_url(f"**/agents/all/{created_agent_id}**")`, then `AgentDetailPage` assertions at lines 640-645). That is ELITEA-1914's case steps 2-4 verbatim (Approve → create succeeds → navigated to Agent detail/menu). Live re-verification this run (see Test Steps) confirmed the exact same contract, live, with a *plain* draft (no suggested resources): `POST /api/v2/elitea_core/applications/prompt_lib/400` → `201`, immediate auto-navigation to `/agents/all/{id}?destTab=configuration&name=...&viewMode=owner`.

Two things keep this from being a straight `already-covered` and instead make it `extend-existing`:

1. **The only test that currently exercises Approve→create→navigate is gated behind toolkit/agent selection AND the `github_toolkit`/`github_relevant_agents` fixtures, which `pytest.skip()` when `GIT_HUB_TOKEN`/`JIRA_*` test data is unset** (`.agents/profile.md` § Roles & sample users). A case specifically about "does Approve create the agent and navigate" deserves ungated coverage that runs in every environment, not only where GitHub test data happens to be configured. Live-confirmed this run (see Test Steps) that a **plain** draft — no suggested resources at all — never fires the toolkit-PATCH/application_relation-PATCH calls `click_approve_and_wait_for_creation()` waits on; that helper would hang indefinitely on a plain-approve draft (source-read confirmed, `automation/pages/generate_agent_modal_page.py:262-296`, all three `expect_response` waits are entered as one `with` block). A new, lightweight wait helper (or reusing just the base-create wait) is needed — see Gap assertions #1.
2. **Case step 5 — "Navigate to the Agents list and verify the new Agent appears there" — is not asserted anywhere in the suite.** Neither ELITEA-1909 nor ELITEA-1911's tests navigate back to the Agents list after creation; both stop at the detail-page assertion. Live-confirmed this run: navigating to `/agents/all` after creation shows the new agent's name via `AgentsListPage.agent_exists_in_list()` (`automation/pages/agents_list_page.py:263-279`, already exists, unused by any Build-with-AI test to date).

The overlap (create→navigate-to-detail) is large enough, and the existing page-object/test-class machinery (mocked-draft pattern, `AgentDetailPage`, `AgentsListPage`) reusable enough, that a full fresh `.spec.ts`-equivalent test class would re-derive everything ELITEA-1909 already proved about the create+navigate shell — hence `extend-existing` (a new sibling test method in the same class/file, same shape ELITEA-1911 used to extend ELITEA-1909 for the Skill resource type) rather than `ready-for-automation`.

## Preconditions
- User is logged in to Elitea with sufficient permission to open "Build with AI" (`${TEST_USER}` rendered `generate-agent-open-button` live in this run — same permission finding as every prior case in this family).
- A project is selected/accessible ("UI Testing", id `400` in this run).
- No suggested-resource fixtures needed — unlike ELITEA-1909/1911, this case's Preconditions are satisfied by a plain, generic prompt with no toolkit/agent/skill relevance signal. Live-confirmed: the prompt used below produced zero "Suggested {Category}:" sections (no `generate-agent-resource-section-*` testid rendered at all), so no fixture creation or GitHub/Jira test data is required — the flow is inherently ungated.

## Test Data

### reuse-existing
- Natural-language prompt (not verbatim from the case, which gives no exact wording — same gap the whole family's AFS's have already flagged and clarified once, not re-filed): `"Create a simple agent that summarizes long text documents into concise bullet-point summaries."` — deliberately generic/non-resource-implying so no "Suggested {Category}:" section renders (live-confirmed).
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is left behind — the created Agent is deleted in Cleanup, verified live.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create`. Click **"Build with AI"** (`data-testid="generate-agent-open-button"`) to open `GenerateAgentModal`. Fill the prompt textarea (`data-testid="generate-agent-prompt-input"`) with the Test Data prompt above, click **"Generate"** (`data-testid="generate-agent-submit-button"`).
   - **Verify**: `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/400` resolves `200` (confirmed live). Review form renders with populated Name (`"Bullet Summary Agent"`), Description, Instructions, Welcome Message, 4 conversation starters — **no** "Suggested {Category}:" section renders at all (confirmed live: zero `generate-agent-resource-section-*` elements), matching the case's step-1 "review form reflects the finalized agent configuration" with nothing left to select/deselect.

2. Click **"Create Agent"** (`data-testid="generate-agent-approve-button"`).
   - **Verify**: `POST /api/v2/elitea_core/applications/prompt_lib/400` resolves `201` (confirmed live, created agent id `156` this run). **No** `PATCH .../tool/prompt_lib/...`, `PATCH .../application_relation/prompt_lib/...`, or `GET`/`PATCH .../skill/prompt_lib/...` call fires — confirmed via the full network log filtered to `elitea_core`, the only two `elitea_core` POSTs in the whole flow are `generate_application_draft` and `applications` — this is the concrete evidence that `click_approve_and_wait_for_creation()` (ELITEA-1909's helper) cannot be reused as-is for this scenario; see Gap assertions #1.
   - The UI auto-navigates to the created agent's detail page immediately on the `201` response — confirmed live: `/agents/all/156?destTab=configuration&name=Bullet%20Summary%20Agent&viewMode=owner`.

3. Agent is created in the current project without errors (auto-navigated from step 2, satisfying the case's own step 3).
   - **Verify**: the subsequent `GET /api/v2/elitea_core/application/prompt_lib/400/156` resolves `200` (confirmed live) — the created agent is genuinely persisted and fetchable, not just a client-side optimistic-navigation artifact.

4. Verify the user is navigated to the created Agent (Agent menu/details).
   - **Verify**: page title reads `"Agent: Bullet Summary Agent - UI Testing"`; URL contains `/agents/all/156`; the review form's fields carried over verbatim into the detail form (Name field = `"Bullet Summary Agent"`, Description/Instructions/Welcome Message match the generated draft); "Skills" accordion counter reads `"0/5 skills added."` (confirms no resources were attached, as expected for a plain draft — the negative control that distinguishes this test from ELITEA-1909/1911's positive-attachment assertions).

5. Navigate to the Agents list (`${BASE_URL}/agents/all`) and verify the new Agent appears there.
   - **Verify**: `AgentsListPage.agent_exists_in_list("Bullet Summary Agent")` returns `True` — confirmed live via `browser_wait_for(text="Bullet Summary Agent")` on `/agents/all` after navigation. This is the one case step (step 5) genuinely unexercised by any existing merged test in this file — see Gap assertions #2.

## Expected Results
Matches the case's stated Pass criteria in full: clicking Approve/Create Agent on a finalized draft (no resources selected) creates the agent (`201`, no errors), the UI navigates to the created agent's detail/menu page with the draft's content carried over, and the new agent is visible in the Agents list. All 5 case steps executed live, no blockers. One incidental defect found and filed during exploration (see Known Defects Found) — unrelated to the case's own scripted flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: admin/editor role | Build with AI accessible | step 1 | `generate-agent-open-button` rendered and clickable for `${TEST_USER}` | asserted |
| Precondition: agent draft generated, review form displayed | review form with finalized configuration | step 1 | `POST generate_application_draft` → 200, review form fields populated, zero suggested-resource sections (plain prompt) | asserted |
| 1 Generate draft, optionally edit fields, select desired resources | review form reflects finalized config | step 1 | draft fields populated; no resources to select for this plain-prompt scenario (deliberate — negative control vs ELITEA-1909/1911) | asserted |
| 2 Click "Approve"/"Create Agent" | agent creation request submitted | step 2 | `approve_button.click()` → `POST .../applications/...` fires | asserted |
| 3 Verify the agent is created in the current project | agent created successfully, no errors | step 2-3 | `POST` → 201; follow-up `GET application/.../156` → 200 confirms persistence | asserted |
| 4 Verify the user is navigated to the created Agent | redirected to Agent detail/menu page | step 4 | URL contains `/agents/all/156`, page title + Name field match the created agent | asserted |
| 5 Navigate to Agents list, verify new Agent appears there | agent visible in Agents list | step 5 | `AgentsListPage.agent_exists_in_list("Bullet Summary Agent")` → True, live-confirmed | asserted (genuinely new — no existing test exercises this) |

### Axis 2 — Analyst additions

- step 2 documents that a plain (no-resource) draft fires **only** the base-create POST, not the toolkit/agent/skill association calls — *added: this is the concrete evidence an implementer needs to know NOT to reuse `click_approve_and_wait_for_creation()` (which enters all three `expect_response` waits in one `with` block and would hang on a plain-approve draft) or `click_approve_and_wait_for_skill_creation()` as-is; a new, narrower wait helper (or bare `expect_response` on just the create POST) is required — see Gap assertions #1.*
- step 4 documents the "Skills 0/5" negative-control assertion — *added: distinguishes this test's plain-draft scenario from ELITEA-1909/1911's positive-attachment scenarios and gives the implementer a concrete signal that nothing was accidentally attached.*
- step 5 is entirely new coverage — *added: neither ELITEA-1909 nor ELITEA-1911's covering tests navigate back to the Agents list post-creation; `AgentsListPage.agent_exists_in_list()` already exists (pre-dating this case) but had never been called from any Build-with-AI test.*
- **Known Defects Found #1** (bare-URL deep-link resolving to a different agent) — *added: discovered incidentally via my own exploration shortcut (a hard-navigation used to double-check the created agent's persisted state), not part of the case's scripted steps; documented and filed per the profile.md bug-filing policy so it doesn't slip through untracked, but explicitly NOT part of this case's Pass/Fail criteria — the case's own in-app navigation flow (step 4/5) is unaffected and passes cleanly.*

## Cleanup
1. Created "Bullet Summary Agent" agent (id `156`, this run's step 2 output) — deleted via the UI's "Delete agent" menu action, confirmed via redirect away from the agent's detail page. (Implementer: reuse the `agent_api.delete_agent(created_agent_id)` `finally`-block pattern ELITEA-1909/1911 already use, `automation/tests/ui/agents/test_agent_build_with_ai.py:672-678`.)
2. No product state left behind. Project `400` ("UI Testing") agent inventory is back to its pre-run baseline.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `page.get_by_test_id("generate-agent-open-button")` | on-main ✓ (pre-existing, reused by every prior case in this family) | n/a — already present |
| Prompt textarea | `page.get_by_test_id("generate-agent-prompt-input")` | on-main ✓ | n/a — already present |
| Generate button | `page.get_by_test_id("generate-agent-submit-button")` | on-main ✓ | n/a — already present |
| "Create Agent" approve button | `page.get_by_test_id("generate-agent-approve-button")` | on-main ✓ | n/a — already present |
| Created-agent Skills accordion counter | `page.get_by_test_id("agent-skills-counter")` — pre-existing, already used by `AgentDetailPage.get_skills_counter_text()` | on-main ✓ | n/a — already present |
| Agents-list card name (existence check) | `AgentsListPage.agent_exists_in_list(name)` — internally `page.locator(f'text="{name}"')`, a pre-existing raw-text helper (tech debt, `automation/pages/agents_list_page.py:263-279`, predates the testid-only policy) | on-main ✓ (page-object method; not a new locator this case introduces) | n/a — reuse existing method, do not add a new raw locator alongside it |

**Summary for the implementer:** no new `add-data-testid` work is needed — every element steps 1-5 touch already carries a testid confirmed on `origin/main` (verified via a fresh `git fetch origin` in `../EliteaUI` this run: `generate-agent-open-button`, `generate-agent-prompt-input`, `generate-agent-submit-button`, `generate-agent-approve-button`, `agent-skills-counter` all present). The one piece of net-new work is a **page-object method**, not a testid: a lightweight wait helper on `GenerateAgentModalPage` for the plain-approve (no-resource) case — see Gap assertions #1. `AgentsListPage.agent_exists_in_list()` already exists and needs no changes, only a new call site.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/400` → `200` — generates the draft; response has empty/absent `suggested_*` arrays for this plain, non-resource-implying prompt (confirmed live — no `generate-agent-resource-section-*` rendered).
- `POST /api/v2/elitea_core/applications/prompt_lib/400` → `201` — creates the base agent (id `156` this run). **This is the only `elitea_core` write the plain-approve flow fires** — no toolkit/agent/skill relation PATCH/GET calls, confirmed by filtering the full network log to `elitea_core` between the approve click and the detail-page landing.
- `GET /api/v2/elitea_core/application/prompt_lib/400/156` → `200` — fires automatically once the detail page mounts, confirms the created agent is genuinely persisted (not just an optimistic client-side navigation).

## Known Defects Found During Exploration

**No functional defect in ELITEA-1914's own scripted flow.** One incidental defect found via my own exploration shortcut (not part of the case's steps), filed:

1. **[BUG, filed as elitea-testing-public#1316]** A bare hard-navigation to `/agents/all/{id}` with no `?viewMode=owner` query param and no React Router `location.state` (e.g. a fresh page load / typed URL, as opposed to the app's own in-app SPA navigation) can silently render a **completely different, unrelated agent's data** instead of the intended one, when the numeric id happens to collide between the private (`application`) and public (`public_application`) id spaces. Root-cause confirmed via source read: `EliteaUI/src/hooks/useViewMode.js`'s fallback (`projectId == PUBLIC_PROJECT_ID ? ViewMode.Public : ViewMode.Owner`) can resolve to `Public` on a hard reload before the real project is restored, routing `useApplicationInitialValues.jsx` to `usePublicApplicationDetailsQuery` (`GET /public_application/prompt_lib/{id}`, project-unscoped) instead of the project-scoped `application` endpoint. Live-reproduced this run: agent id `156` ("Bullet Summary Agent", just created, project 400) rendered as agent "StoryChecker" (a completely unrelated, pre-existing agent) when re-visited via a bare `/agents/all/156` hard navigation. This is a **sibling** of the already-documented `public_application` vs `application` viewMode-default pattern (`.agents/role-overrides.md` § "4xx/5xx from the UI" cites the identical class of bug for Pipelines) and of tracker issue #638 (Artifacts: bare-URL bucket navigation lands on the wrong bucket) — different object/surface, same symptom family, cross-linked both ways, not filed as a duplicate. **Not part of ELITEA-1914's own Pass/Fail criteria** — the case's own step-4/5 navigation is always via the app's in-app flow (Approve's auto-navigation, and the Agents-list link), which always carries the correct `viewMode`/state and is unaffected.

## Blocked Steps
None. All 5 case steps executed live, end to end.

## Gap assertions (what the implementer appends to the covering test class)

`TestAgentBuildWithAISelectedResourcesAttached` (ELITEA-1909/1911's covering class, `automation/tests/ui/agents/test_agent_build_with_ai.py:497`) already proves the create+auto-navigate shell for a draft with selected resources. The implementer should add a **new sibling test method in the same class** (same shape ELITEA-1911 already used to extend ELITEA-1909 for the Skill resource type) — e.g. `test_approve_with_no_resources_creates_agent_and_appears_in_list` — that asserts specifically:

1. **A new, narrower wait helper is needed on `GenerateAgentModalPage`** (e.g. `click_approve_and_wait_for_agent_created()`) that waits ONLY on the base `POST .../applications/prompt_lib/{project}` response, not the toolkit/agent-relation pair `click_approve_and_wait_for_creation()` (`automation/pages/generate_agent_modal_page.py:262-296`) waits on — that existing helper's `with` block enters all three `expect_response` context managers together and will hang/timeout on a plain-approve draft that never fires the association calls. Reuse `FIELD_POPULATION_DRAFT_PAYLOAD`-style mocking (or a live generate call, per this AFS's Test Steps) with empty `suggested_*` arrays to guarantee no association calls are expected.
2. **Given** a draft generated from a plain, non-resource-implying prompt, **no "Suggested {Category}:" section renders at all** (`modal.is_resource_section_visible(entity_type)` returns `False` for every `entity_type`) — not currently asserted anywhere as a *combined* absence across all categories in one scenario (ELITEA-1907 asserts per-category absence only for the empty `skill` category within an otherwise-populated draft).
3. **When** "Create Agent" is clicked, **the created agent auto-navigates to its detail page** (`page.wait_for_url(f"**/agents/all/{created_agent_id}**")`, same pattern ELITEA-1909/1911 already use) and **the Skills counter reads `"0/5 skills added."`** — a negative-control assertion not currently made by any test in this file (ELITEA-1909/1911 only assert the positive/negative *presence* of specific attached items, never that the counter is genuinely zero for a no-resource draft).
4. **Then** navigating to `AgentsListPage` (`${BASE_URL}/agents/all`) and calling `agent_exists_in_list(created_agent_name)` returns `True` — the case's own step 5, genuinely new coverage; no existing Build-with-AI test in this file navigates back to the Agents list after creation.

No new page-object locators are needed (see Concrete Handles) — only one new page-object *method* (the plain-approve wait helper, #1 above) and a new test method reusing the class's existing `agent_api`/cleanup fixture pattern.
