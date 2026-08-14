# Test Case: Build with AI — Suggested Skills section is shown with up to 5 skills

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the `generate_application_draft` response) for a TMS case whose text never asks for
> simulation. Classification: **TERMINAL** — the 5-card cap is read off a hand-authored 7-item payload; it also produced #1317, which is unresolved.
>
> Its justifications ("the same sanctioned-mocking technique this file already uses",
> "not a good use of fixture-creation effort") are **not valid authorities**: nothing
> sanctions response mocking, and cost is never a reason to substitute. See
> `.agents/testing.md` § Fidelity policy and `.agents/role-overrides.md` § Every role —
> precedent is not authority.
>
> **`extend-existing` must not inherit this design.** Rework is tracked on
> [#1298](https://github.com/EliteaAI/elitea-testing-public/issues/1298); the full chain
> is in `sdlc-skills/bundles/test-automation/incidents/2026-08-14-response-mocking-drift.md`.

## Metadata
- **TMS ID**: ELITEA-1910
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Status**: `extend-existing`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS (ELITEA-1903/1905/1906/1907/1908/1909/1911/1914/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.
- **Batch trunk**: `tests/batch-1298-agents-build-with-ai` — this AFS committed there directly (no per-case branch at analysis time).

## Extension target

- **Covering spec (existing, merged to `automation/base`, present on this batch's trunk)**: `automation/tests/ui/agents/test_agent_build_with_ai.py:364-527`, class `TestAgentBuildWithAISuggestedResources`, method `test_generated_draft_includes_suggested_resources_section` (`automation/tests/ui/agents/test_agent_build_with_ai.py:376`).
- **Covering AFS**: `test-specs/agents/l2_build-with-ai-generated-draft-suggested-resources_ELITEA-1907.md`.

## Behavioural overlap (why this is `extend-existing`, not fresh)

ELITEA-1907's covering test already proves the entire shell this case also
exercises: open "Build with AI" → submit a description → mock the
`generate_application_draft` response (`GenerateEntityModalPageBase.mock_generate_success()`
/ `page.route()`, the same sanctioned-mocking technique this file already uses
for ELITEA-1907 and ELITEA-1915) → wait for the review form → assert each
"Suggested {Category}:" section's presence, per-item name/description
rendering, and unselected-by-default state. Its own mocked payload
(`SUGGESTED_RESOURCES_DRAFT_PAYLOAD`, `test_agent_build_with_ai.py:168-210`)
deliberately leaves `suggested_skills: []` and its Step 3 explicitly asserts
`not modal.is_resource_section_visible("skill")` — the **inverse** of
ELITEA-1910's subject. No existing test in this file (or anywhere in
`test-specs/agents/`) ever mocks or observes a `suggested_skills` array with
more than 2 items (ELITEA-1911's live-fixture run, the only other test to
populate `suggested_skills` at all, used exactly 2). **No cap-of-5 behavior
has ever been exercised, by any merged spec.** The overlap is large enough
(same modal, same page object, same mocking technique, same
`RESOURCE_SECTION`/`RESOURCE_ITEM`/`RESOURCE_NAME`/`RESOURCE_DESCRIPTION`/
`RESOURCE_CHECKBOX` locator templates already generic over `entity_type`)
that a fresh `.spec.ts`-equivalent test class would re-derive everything
ELITEA-1907 already proved about the shell — hence `extend-existing` (a new
sibling test method in the same class, mirroring the pattern ELITEA-1911 used
to add its own sibling method to `TestAgentBuildWithAISelectedResourcesAttached`)
rather than `ready-for-automation`.

## Preconditions
- User is logged in to Elitea with sufficient permission to open "Build with AI" (`${TEST_USER}` renders `generate-agent-open-button` live — same permission finding as every prior case in this family).
- A project is selected/accessible (`Private`, id `399` in this run).
- No live Skill fixtures are needed for this case (unlike ELITEA-1911) — the cap behavior is tested via a **mocked** `generate_application_draft` response, per the reasoning in Known Defects Found below (live-inventory suggestion counts are LLM-relevance-driven and not reliably controllable — this project's real Skills inventory has never surfaced more than 2 relevant suggestions in any prior exploration, and coaxing the live suggestion engine into returning >5 semantically-relevant Skills is neither deterministic nor a good use of fixture-creation effort when the same sanctioned mocking technique ELITEA-1907/1915 already use answers the question conclusively).

## Test Data

### reuse-existing (no fixture creation/teardown needed — mocked response, no live data mutated)
- Prompt text: any non-empty string enables Generate; no specific wording required since the response is mocked (unlike ELITEA-1907/1911, which need the prompt to semantically drive live suggestions). Recommend a fixed constant for readability, e.g. `"An agent that uses several specialized skills to manage repository workflows"`.
- Mocked `generate_application_draft` response payload — **7 `suggested_skills` items** (2 more than the case's stated cap of 5), each with a distinct `id`/`name`/`description`, `suggested_toolkits`/`_mcp`/`_pipelines`/`_agents` all empty (keeps the DOM surface focused on the Skills section this case cares about, same narrowing technique `FIELD_POPULATION_DRAFT_PAYLOAD` already uses in this file for an unrelated case).
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is created or persisted in the product by this AFS's steps (the draft is never approved — "Create Agent" is not clicked, matching ELITEA-1907's own scope).

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`. Click **"Build with AI"** (`data-testid="generate-agent-open-button"`) to open `GenerateAgentModal`. Fill the prompt textarea (`data-testid="generate-agent-prompt-input"`) with any non-empty prompt.
   - **Verify**: prompt textarea contains the entered text; **"Generate"** button (`data-testid="generate-agent-submit-button"`) becomes enabled.

2. Mock the `generate_application_draft` response (`GenerateEntityModalPageBase.mock_generate_success()`) with the 7-item `suggested_skills` payload (Test Data above) **before** clicking Generate, then click **"Generate"**.
   - **Verify**: the modal shows the loading state, then transitions to the review form once the mocked response resolves. Confirmed live (this exploration): `POST .../generate_application_draft/...` resolves `200` with the mocked body; `modal.wait_for_review_form()` completes without error.

3. Observe the review form.
   - **Verify**: a **"SUGGESTED SKILLS"** section (`data-testid="generate-agent-resource-section-skill"`) is present — `modal.is_resource_section_visible("skill")` returns `true`. **Live-confirmed**, same generic `RESOURCE_SECTION` template ELITEA-1907/1909/1911 already established for `entity_type="skill"`.

4. Count the rendered Skill suggestion cards.
   - **Case's stated expectation**: "The section displays between 1 and 5 Skill cards (never more than 5)."
   - **Live-verified actual behavior (via a scratch Playwright probe run against this exact mocking mechanism during this analysis, deleted afterward — not committed)**: with a 7-item mocked payload, **all 7** `[data-testid^="generate-agent-resource-item-skill-"]` cards render — `page.locator('[data-testid^="generate-agent-resource-item-skill-"]').count()` returned `7`, not `5`. **This is a live-verified product defect, filed as `EliteaAI/elitea-testing-public#1317`** (see Known Defects Found below) — `ResourceSuggestions.jsx` (`../EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/ResourceSuggestions.jsx:24`, `items.map(item => ...)`) has no `.slice(0, 5)`/count guard anywhere in the component, `GenerateAgentReviewForm.jsx`, or `GenerateAgentModal.jsx` — confirmed by grepping all three files for `slice|MAX_|limit|cap` (no cap-relevant hits; the only `MAX_*` constants belong to unrelated name/description/welcome-message/conversation-starter fields).
   - **Per this project's analysis-time sanctioned-RED exception** (`.agents/testing.md` § Merge gate, the 2026-07-23/ELITEA-1965 "Analysis-time entry" bullet): this defect is deterministic (reproduced via a controlled mock, not live LLM variance), single-cause (one missing guard in one shared component), and does not block reaching this case's remaining steps (5/6 below still execute and assert meaningfully against the same 7-card render) — so this AFS classifies `extend-existing`/`ready-for-automation`-shaped (not `defect-found`), and the implementer writes this step's count assertion as `expect.soft()` against the case's stated expectation (`count <= 5`) with a `# Known defect: EliteaAI/elitea-testing-public#1317` comment, rather than pausing automation.

5. Verify each rendered Skill card shows its name and description.
   - **Verify**: for a representative sample across the full rendered range (first item `id=1`, middle item `id=4`, last item `id=7` — deliberately spanning both sides of the case's nominal 5-item cap, since the defect means all 7 are live DOM elements to assert against), `modal.get_resource_name_text("skill", item_id)` equals the mocked item's `name`, and `modal.get_resource_description_text("skill", item_id)` equals the mocked item's `description` (skill-type cards render `item.description` per `SuggestionItem.jsx`'s per-entity-type contract, already established by ELITEA-1907/1909/1911 — not re-derived here). **Live-confirmed** via the same scratch probe (all 7 cards carried correct, distinct name/description text matching their payload index).

6. Verify all suggested Skills are unselected by default.
   - **Verify**: for the same representative sample (items `1`, `4`, `7`), `modal.is_resource_checked("skill", item_id)` returns `false`. **Source-confirmed why, beyond the live observation**: `GenerateAgentModal.jsx:50-54` initializes `selectedSkillIds` via `useState(new Set())` (empty), and `handleDraftGenerated` (`GenerateAgentModal.jsx:106-112`, fired on every successful generation) explicitly resets it to a fresh empty `Set()` — already documented by ELITEA-1907/1911's AFS's for this exact invariant, confirmed to hold identically regardless of item count.

## Expected Results
Matches the case's stated Pass criteria for sections 1, 3, 5, 6 (loading→review transition, section presence, name+description per card, none pre-selected — all live-verified). Section 4 (the "never more than 5" cap) does **not** hold against the live-verified current implementation — see step 4 and Known Defects Found; this is filed as `EliteaAI/elitea-testing-public#1317` and the implementer writes that one assertion as a linked, deterministic soft-failure per this project's analysis-time sanctioned-RED exception, preserving full automated coverage of every other Pass-criterion.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: admin/editor role | Build with AI accessible | step 1 | `generate-agent-open-button` rendered and clickable for `${TEST_USER}` | asserted |
| Precondition: ≥1 Skill exists that could be suggested | achievable, case doesn't say how many/relevance | Preconditions | resolved via mocking — no live Skill count/relevance dependency for THIS case (unlike ELITEA-1911, which needed live fixtures because it tests the create→attach flow, not the display cap) | asserted (mocking sidesteps the gap entirely — no clarification needed for this case) |
| 1 Generate an agent draft that would benefit from Skills | loading → review form transition | steps 1–2 | step 2: loading indicator then review form, mocked 200 response | asserted |
| 2 Wait for generation to complete | review/edit form displayed | step 2 | step 2: `wait_for_review_form()` completes | asserted |
| 3 Verify "SUGGESTED SKILLS" section is displayed | section present | step 3 | `generate-agent-resource-section-skill` present | asserted |
| 4 Verify at most 5 Skill cards are shown (never more than 5) | 1–5 cards | step 4 | live-verified: **7 cards render for a 7-item mock — cap does NOT hold** | **defect (filed `EliteaAI/elitea-testing-public#1317`) — implementer asserts via `expect.soft()` per analysis-time sanctioned-RED exception, not blocked** |
| 5 Verify each Skill card shows Skill name and Skill description | name + description shown | step 5 | sampled cards (`id` 1, 4, 7) — name/description text match payload | asserted |
| 6 Verify all suggested Skills are unselected by default | all cards unselected | step 6 | sampled cards (`id` 1, 4, 7) — checkbox unchecked; source-confirmed reset-on-generate | asserted |

### Axis 2 — Analyst additions

- step 2 documents that this case's mocking approach differs from ELITEA-1911's live-fixture approach, and why (cap testing needs a deterministic >5-item payload; live LLM relevance-matching cannot reliably be coaxed past 2 items per this project's own exploration history) — *added: an implementer defaulting to ELITEA-1911's live-fixture pattern would spend significant fixture-creation effort (6+ Skills) for a nondeterministic result, when the mocking technique ELITEA-1907/1915 already sanction in this exact file answers the question in one deterministic assertion.*
- step 4 documents the exact root-cause grep (`slice|MAX_|limit|cap` across all three relevant JSX files) that rules out a cap living anywhere else in the render path — *added: without this, a reviewer might suspect the analyst missed a cap implemented elsewhere (e.g. in `GenerateAgentModal.jsx`'s state layer) rather than confirming its total absence.*
- step 5 samples the first/middle/last of the 7 rendered items rather than asserting all 7 individually — *added: a deliberate economy call, not a coverage gap — the per-item name/description rendering logic is identical for every array index (`SuggestionItem.jsx` has no index-dependent branching), so a 3-point sample spanning both sides of the nominal cap boundary is sufficient to prove the rendering path without redundant per-item assertions.*

## Cleanup
1. No product state is created by any step in this AFS — the draft is never approved ("Create Agent" is not clicked, matching ELITEA-1907's scope). Navigating away from `/agents/create` is sufficient.
2. No fixtures were created (mocked response only — no live Skills, Toolkits, MCPs, Pipelines, or Agents created or mutated).
3. The scratch Playwright probe used to live-verify step 4 (`automation/tests/ui/agents/test_zzz_scratch_cap_probe.py`) was deleted after use — never committed. The implementer's real sibling test method (see Gap assertions) supersedes it with proper page-object usage, allure steps, and the soft-assert/Known-defect pattern.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `page.get_by_test_id("generate-agent-open-button")` | on-main ✓ (confirmed via fresh `git fetch origin` + `git grep` this run) | n/a — already present |
| Prompt textarea | `page.get_by_test_id("generate-agent-prompt-input")` | on-main ✓ | n/a — already present |
| Generate button | `page.get_by_test_id("generate-agent-submit-button")` | on-main ✓ | n/a — already present |
| "Suggested Skills:" section | `page.get_by_test_id("generate-agent-resource-section-skill")` — generic `generate-agent-resource-section-${entityType}` template, source-confirmed on `origin/main` via bare-substring `git grep` (the template interpolation means a literal-string grep for `-skill` alone false-negatives; verified with the `${entityType}` substring per `.agents/workflow.md`'s two-stage closure-record pattern) | on-main ✓ | n/a — already present |
| Suggestion card / name / description / checkbox | `RESOURCE_ITEM`/`RESOURCE_NAME`/`RESOURCE_DESCRIPTION`/`RESOURCE_CHECKBOX` templates already on `GenerateAgentModalPage` (`generate_agent_modal_page.py:150-154`), all generic over `entity_type` | on-main ✓ (same generic template, same fresh-fetch verification) | n/a — already present |

**Summary for the implementer:** no new `add-data-testid` work is needed — every element this case touches already carries a testid confirmed on `origin/main` (fresh `git fetch origin` this run), inherited from the generic `generate-agent-resource-*-{entity_type}-{id}` template ELITEA-1907's `add-data-testid` pass already landed, generic over `entity_type` and therefore zero new UI work for `"skill"` or for testing >5 items (the template has no id-count-dependent behavior).

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/{project_id}` — the sole endpoint; this case mocks it directly via `page.route()` rather than exercising the live LLM (see Preconditions/Test Data for why). Mocked response body: `suggested_skills` = 7 objects, each `{"id": N, "type": "skill", "name": "...", "description": "..."}`; all other `suggested_*` arrays empty.
- No other network calls are specific to this case's flow — surrounding page-load traffic (`applications`, `tags`, `models`, `permissions`, etc.) is unrelated, matching every prior "Build with AI" AFS in this family.

## Known Defects Found During Exploration

**One real, live-verified product defect — filed.**

1. **[CONFIRMED — filed as `EliteaAI/elitea-testing-public#1317`]** `ResourceSuggestions.jsx` (shared by all five "Suggested {Category}:" sections — Toolkits/MCP/Pipelines/Agents/Skills) renders every item in its `items` array unconditionally (`items.map(...)`, `ResourceSuggestions.jsx:24`), with no `.slice(0, 5)` or count guard anywhere in that component, `GenerateAgentReviewForm.jsx`, or `GenerateAgentModal.jsx` (confirmed via source grep — see step 4). Live-reproduced via a scratch Playwright probe (deleted after use, not committed) that mocked the `generate_application_draft` response with 7 `suggested_skills` items: **all 7 cards rendered**, not the case-expected maximum of 5. Root cause is a single missing guard in one shared component — deterministic, single-cause, reproducible on demand via the mock. Per `.agents/testing.md`'s analysis-time sanctioned-RED exception (ELITEA-1965/#557), this AFS classifies `extend-existing` rather than `defect-found` (the defect is isolable to this one step and does not block steps 5/6), directing the implementer to assert step 4's count check via `expect.soft()` + `# Known defect: EliteaAI/elitea-testing-public#1317`.
   - **Backend-contract caveat, explicitly not over-claimed**: the `generate_application_draft` endpoint's OpenAPI entry documents no response schema (spec silent per `/shared/openapi/?all=true`), so whether the *backend* independently caps suggestion counts at 5 is unverifiable from this repo. This defect is filed strictly as a **frontend gap** (no display-side defense exists regardless of what the backend sends) — not a claim about backend behavior. Live-observed real suggestion counts to date (ELITEA-1907/1911) never exceeded 2 per category, so this has not manifested in production observation; the mock makes the latent gap concrete and testable.
2. **[Non-issue — informational]** No live Skill-inventory experiment was attempted to try to coax >5 real suggestions from the LLM-driven suggestion engine (as opposed to ELITEA-1911's 2-fixture approach) — deliberately out of scope per the Preconditions/Test Data reasoning (nondeterministic, expensive, and the mocking technique already answers the question conclusively and repeatably). Flagged only so a future reader doesn't assume this was tried and failed; it was a considered economy decision.

## Blocked Steps
None. All 6 case steps executed against the live application (steps 1–3 via real interaction; steps 4–6 verified against the real rendered DOM of the mocked response, the same "live system, synthetic network boundary" technique already sanctioned and merged for ELITEA-1907/1915 in this exact file).

## Gap assertions (what the implementer appends to ELITEA-1907's covering test class)

`TestAgentBuildWithAISuggestedResources` (ELITEA-1907's covering class) already
proves the shell (generate → mock → review form → per-category section
presence/absence → name/description → unselected-by-default) for a
single-item-per-category payload. The implementer should add a **sibling test
method in the same class** — mirroring the pattern ELITEA-1911 used to add
`test_selected_suggested_skill_attached_and_non_selected_absent` as a sibling
of ELITEA-1909's method in `TestAgentBuildWithAISelectedResourcesAttached` —
that asserts specifically:

1. **Given** a draft mocked with **7** `suggested_skills` items (a fixed
   module-level payload constant, e.g. `SUGGESTED_SKILLS_CAP_PROBE_PAYLOAD`,
   analogous to `SUGGESTED_RESOURCES_DRAFT_PAYLOAD`), **the "Suggested
   Skills:" section renders** (`is_resource_section_visible("skill")`) — hard
   assert, not currently exercised by any merged test with more than 2 items.
2. **When** the review form settles, **the rendered card count is asserted
   via `expect.soft()`** against the case's stated expectation
   (`count <= 5`), with a `# Known defect: EliteaAI/elitea-testing-public#1317`
   comment directly above it — this is the one assertion expected to FAIL
   deterministically (actual: 7) until the product fix ships; per this
   project's analysis-time sanctioned-RED exception this is the *correct*
   expected-behavior assertion, not a weakened one.
3. **Then**, independent of the cap outcome, **sample cards (`id` 1, 4, 7)
   show correct name + description** (`get_resource_name_text`/
   `get_resource_description_text`) — hard asserts, genuinely new coverage
   (no existing test samples a Skill suggestion card past index 1).
4. **And** the same sampled cards are **unchecked by default**
   (`is_resource_checked` → `false`) — hard asserts, extending the existing
   unselected-by-default invariant (already proven for 1–2 items by
   ELITEA-1907/1911) to a larger item count with no special-casing in the
   selection-reset logic.

No new page-object locators or methods are needed (see Concrete Handles) —
only a new mocked-payload constant and a new test method using
`allure.step`-wrapped versions of steps 1–6 above, following this file's
existing `test_generated_draft_includes_suggested_resources_section` as the
template for the mock-based flow (`modal.mock_generate_success(...)` +
`modal.expect_generate_response(...)` + `modal.wait_for_review_form(...)`).
