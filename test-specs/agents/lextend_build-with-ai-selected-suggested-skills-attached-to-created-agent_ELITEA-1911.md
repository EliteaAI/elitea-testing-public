# Test Case: Build with AI — selected suggested Skills are attached to the created agent

## Metadata
- **TMS ID**: ELITEA-1911
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Status**: `extend-existing`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS (ELITEA-1907/1909/1915): `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.

## Extension target

- **Covering spec (existing, merged)**: `automation/tests/ui/agents/test_agent_build_with_ai.py:428-608`, class `TestAgentBuildWithAISelectedResourcesAttached`, method `test_selected_suggested_resources_attached_and_non_selected_absent` (`automation/tests/ui/agents/test_agent_build_with_ai.py:440`).
- **Covering AFS**: `test-specs/agents/l2_build-with-ai-selected-suggested-resources-attached-to-created-agent_ELITEA-1909.md`.

## Behavioural overlap (why this is `extend-existing`, not fresh)

ELITEA-1909's implemented test already proves the entire flow shape ELITEA-1911
also exercises: generate a draft → observe a "Suggested {Category}:" section
populated with unchecked cards → select one item and deliberately leave a
sibling item unchecked → click "Create Agent" → the created agent auto-
navigates to its detail page → the selected item is present in the
corresponding attached-resource section → the deliberately-unselected sibling
item is absent. ELITEA-1909's test asserts this shape concretely for
**Toolkit** and **nested Agent** resource types (case ELITEA-1909's own
stated scope, confirmed by its docstring: `"only explicitly selected
suggested resources (Toolkit, nested Agent) are attached... a non-selected
suggested resource is absent"`). It never exercises a **Skill**-type
suggested resource: `TestAgentBuildWithAISuggestedResources` (ELITEA-1907's
covering test in the same file) explicitly mocks
`suggested_skills: []` in its draft payload (line 157 of
`test_agent_build_with_ai.py`), and `TestAgentBuildWithAISelectedResourcesAttached`
(ELITEA-1909's covering test) never selects, asserts-attached, or
asserts-absent any Skill-type item — its fixtures (`github_toolkit`,
`github_relevant_agents`) are Toolkit/Agent-only. ELITEA-1911's subject
(select a suggested Skill, verify it lands in the Agent's **SKILLS** section
— a visibly different accordion/testid, `agent-skills-section`, from the
Toolkit/Agent flow's **Tools** accordion, `agent-toolkits-section`) is
therefore a genuine, previously-unexercised gap, not a duplicate. The overlap
is large enough (same generate→select→approve→verify shape, same page
object, same "Suggested {X}:" pattern already generic over `entity_type`)
that a full fresh `.spec.ts`-equivalent test class would re-derive
everything ELITEA-1909 already proved about the shell — hence `extend-existing`
rather than `ready-for-automation`.

## Preconditions
- User is logged in to Elitea with sufficient permission to open "Build with AI" (`${TEST_USER}` rendered `generate-agent-open-button` live in this run — same permission finding as ELITEA-1907/1909/1915).
- A project is selected/accessible (`Private`, id `399` in this run).
- **Precondition gap investigated and resolved (mirrors ELITEA-1909's finding for Toolkits/Agents) — Skill suggestion:** the case's own preconditions never state how to make an existing Skill suggestible (step 1's prerequisite: "at least two skill cards"). Investigation confirmed: the suggestion engine (`generate_application_draft` response's `suggested_skills` array) draws candidates from the **project's own configured Skills**, filtered by semantic relevance to the submitted prompt — same mechanism ELITEA-1909 documented for Toolkits/Agents. This project (`399`) had 15 pre-existing Skills at exploration time, none semantically relevant to a controllable, distinctive prompt. This run created two dedicated fixture Skills (`elitea-1911-changelog-writer` id `650`, `elitea-1911-issue-labeler` id `651`) via the Skills UI form before invoking "Build with AI", which produced a non-empty `suggested_skills` array live (two cards) — see Test Steps step 1. **Disposition: CLARIFICATION** — the case's stated precondition ("at least two skill cards") is directionally correct but omits the mechanism (relevant pre-existing Skills must be in project inventory); not filed as a separate ticket since ELITEA-1909's AFS already filed the identical clarification for the Toolkit/Agent case (`.agents/profile.md` § Bug filing — avoiding a duplicate ticket for the same recurring case-authoring gap across the "Build with AI" family). The AFS proceeds as `extend-existing` using the now-verified precondition.
- Skill name field is constrained to lowercase letters, digits, and hyphens, max 32 characters (live-confirmed via form validation message: `"Name must be lowercase letters, digits and hyphens only (no spaces), and cannot start or end with a hyphen"`) — the implementer's fixture-Skill names must respect this (both `elitea-1911-changelog-writer` at 29 chars and `elitea-1911-issue-labeler` at 26 chars fit).

## Test Data

### created-with-cleanup (created via UI in this run; both deleted at run end — see Cleanup)
- **Skill A — selected** (`elitea-1911-changelog-writer`, id created live = `650` in this run): description `"Skill that writes GitHub repository changelog entries from merged pull requests."`, instructions `"You are a skill that reads merged GitHub pull requests and writes concise changelog entries summarizing the changes."` — GitHub-relevant, becomes a `suggested_skills` candidate.
- **Skill B — NOT selected** (`elitea-1911-issue-labeler`, id created live = `651` in this run): description `"Skill that reads GitHub issues and applies priority/severity labels automatically."`, instructions `"You are a skill that reads incoming GitHub issues and applies priority and severity labels based on their content."` — also GitHub-relevant (deliberately, so it too surfaces as a suggestion candidate), used as the case's step-6 "non-selected resource must be absent" fixture.
- Both created via the Skills UI form (`/skills/create`) — no `SkillAPI.create_skill()` convenience method exists yet in `automation/api/client.py` (`SkillAPI` currently only offers `list_skills()`/`delete_skill()` — see Automation Hints for the implementer-facing gap this leaves).

### reuse-existing
- Natural-language prompt used (not verbatim from the case, which gives no exact wording — see Coverage Map): `"An agent that manages a GitHub repository by delegating changelog writing to the elitea-1911-changelog-writer skill or issue labeling to the elitea-1911-issue-labeler skill."` — deliberately names both fixture skills by their exact slug names so the generation model's relevance-matching has an unambiguous signal (confirmed live: both skills were suggested).
- `${TEST_USER}` — already has sufficient permission (see Preconditions).

No data is left behind — both fixture Skills and the created Agent are deleted in Cleanup, verified live.

## Test Steps

1. Create the two Skill fixtures (Test Data) via `/skills/create`, then navigate to `${BASE_URL}/agents/create?viewMode=owner`. Click **"Build with AI"** (`data-testid="generate-agent-open-button"`) to open `GenerateAgentModal`. Fill the prompt textarea (`data-testid="generate-agent-prompt-input"`) with the Test Data prompt above, click **"Generate"** (`data-testid="generate-agent-submit-button"`).
   - **Verify**: `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/399` resolves `200` (confirmed live). Review form renders with populated Name (`"GitHub Repository Manager"`), Description, Instructions, Welcome Message, 4 conversation starters. A **"Suggested Skills:"** section (`data-testid="generate-agent-resource-section-skill"`) renders with **two** cards, both unchecked initially: `"elitea-1911-changelog-writer"` / `"Skill that writes GitHub repository changelog entries from merged pull requests."` and `"elitea-1911-issue-labeler"` / `"Skill that reads GitHub issues and applies priority/severity labels automatically."` — both name AND description shown (skill-type cards use `item.description`, per `SuggestionItem.jsx`'s per-entity-type contract already documented by ELITEA-1907/1909 for other entity types — not re-derived here, confirmed to hold identically for `entityType: "skill"`). A **"Suggested MCP:"** section also rendered (`"Remote Github"`, unrelated to this case, left unselected throughout). Screenshot: `test-results/screenshots/ELITEA-1911-step3-suggested-skills-before-select.png`.

2. Select the suggested Skill **"elitea-1911-changelog-writer"** by clicking its checkbox (`data-testid="generate-agent-resource-checkbox-skill-{skill_id}"`, live-observed as `generate-agent-resource-checkbox-skill-650` this run). **Deliberately leave "elitea-1911-issue-labeler" unchecked** — this is the case's step-6 negative fixture.
   - **Verify**: post-click accessibility snapshot shows `checkbox [checked]` (confirmed programmatically: `input.checked === true`) for the changelog-writer card, and `input.checked === false` for the issue-labeler card. Screenshot: `test-results/screenshots/ELITEA-1911-step4-selected-skill.png`.

3. Click **"Create Agent"** (`data-testid="generate-agent-approve-button"`).
   - **Verify**: the following network calls fire, in this order, all resolving with a success status:
     1. `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201` — creates the base agent (id `5054` this run).
     2. `GET /api/v2/elitea_core/skill/prompt_lib/399/650` → `200` — `fetchSkillDetails` for the selected skill, reading its `version_details.id` (needed as `skill_version_id` for the relation PATCH — `GenerateAgentModal.jsx`'s `associateSkills`, source-read).
     3. `PATCH /api/v2/elitea_core/skill/prompt_lib/399/650` → `201` — attaches the selected Skill; body `{"has_relation": true, "entity_version_id": <agent_version_id>, "skill_version_id": <skill_version_id>, "entity_type": "agent"}` (`skillsApi.js` `updateSkillRelation` mutation, source-read — see Concrete Handles/Network Behavior for the full contract, which is a **distinct endpoint and payload shape** from both the Toolkit `PATCH .../tool/...` and the Agent `PATCH .../application_relation/...` calls ELITEA-1909 already documented).
     4. **No `GET`/`PATCH .../skill/.../651` call fires** for the deliberately-unselected `elitea-1911-issue-labeler` — confirmed by filtering the full network log for `skill/prompt_lib` and finding exactly the one GET+PATCH pair above, referencing only id `650`.
   - The UI auto-navigates to the created agent's detail page (`/agents/all/{id}?destTab=configuration&...`) once creation completes — confirmed live: `/agents/all/5054?destTab=configuration&name=GitHub%20Repository%20Manager&viewMode=owner`.

4. Agent detail page is displayed (auto-navigated from step 3 — the case's own step 4 "Open the created Agent" is satisfied by this navigation, same pattern ELITEA-1909 already documented for the Toolkit/Agent flow).
   - **Verify**: page heading reads `"GitHub Repository Manager"`; URL contains `/agents/all/5054`.

5. Verify the selected Skill is present in the **SKILLS** section (case says "SKILLS section" — live-confirmed this is a *distinct* accordion from the Toolkit/Agent flow's "Tools" accordion, unlike the case's own step 7/8 wording for ELITEA-1909 which turned out to share one accordion — no reverse-masking needed here, the case's wording is accurate).
   - **Verify**: the accordion titled "Skills" (`data-testid="agent-skills-section"`) renders, showing a `"1/5 skills added."` counter (`data-testid="agent-skills-counter"`) and exactly one card whose visible text is `"elitea-1911-changelog-writer"` with secondary text `"base"` (the attached Skill's version name — same `isAgentOrPipeline`-adjacent secondary-line convention ELITEA-1909 documented for nested-Agent cards in the Tools accordion, but this is the Skills accordion's own `skill-card-{id}` component, not `ToolCard.jsx`/`agent-toolkit-card`). Screenshot: `test-results/screenshots/ELITEA-1911-step5-6-skills-section-verified.png`.

6. Verify the non-selected suggested Skill is absent from the SKILLS section.
   - **Verify**: the Skills accordion's counter reads `"1/5 skills added."` (not `2/5`), and no `skill-card-651` (or any card containing `"elitea-1911-issue-labeler"`) is rendered. Confirmed via both the accordion contents (single card, id `650` only) and the network log (no `skill/prompt_lib/399/651` call at all — see step 3.4). Same screenshot as step 5.

## Expected Results
Matches the case's stated Pass criteria in full: the review form surfaces a "Suggested Skills:" section (step 1, once the precondition gap is satisfied — see Preconditions); selecting one Skill and clicking Create Agent attaches exactly that Skill to the created agent's SKILLS section (steps 3, 5); a second, deliberately-unselected suggested Skill is confirmed absent from the SKILLS section, its id never referenced by any association call (step 6). All 6 case steps executed live, no blockers, no product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: admin/editor role | Build with AI accessible | step 1 | `generate-agent-open-button` rendered and clickable for `${TEST_USER}` | asserted |
| Precondition: draft includes "SUGGESTED SKILLS" section with ≥2 skill cards — case never says how this is populated | achievable, but case never says how | Preconditions § "Precondition gap investigated" + step 1 | live: `suggested_skills` populated only after two relevant fixture Skills created; empty otherwise (mirrors ELITEA-1909's Toolkit/Agent inventory-gating finding) | **clarification (not separately filed — see Preconditions; ELITEA-1909's AFS already filed the identical recurring gap for this case family)** |
| 1 Generate an agent draft with a Suggested Skills section visible | review form + "SUGGESTED SKILLS" section with skill cards | step 1 | `generate-agent-resource-section-skill` populated with both fixture skills | asserted |
| 2 Select one or more suggested Skills by clicking their cards | selected Skill card(s) highlighted/selected | step 2 | checkbox `[checked]` post-click for `elitea-1911-changelog-writer`, live snapshot + programmatic `input.checked` check | asserted |
| 3 Click "Approve"/"Create Agent" | agent creation initiated | step 3 | `POST .../applications/...` → 201, followed by `GET`+`PATCH .../skill/.../650` → 200/201, UI auto-navigates | asserted |
| 4 Open the created Agent | Agent detail page displayed | step 4 | URL + heading confirm `/agents/all/5054`, "GitHub Repository Manager" | asserted (auto-navigation satisfies this — same pattern as ELITEA-1909) |
| 5 Verify selected Skills appear in the SKILLS section | selected Skill present in SKILLS section | step 5 | `agent-skills-section` contains a card for `elitea-1911-changelog-writer`, counter reads `1/5` | asserted |
| 6 Verify non-selected suggested Skills are absent from the SKILLS section | non-selected Skill absent | step 6 | no card for `elitea-1911-issue-labeler`; no `skill/prompt_lib/.../651` network call ever fired | asserted |

### Axis 2 — Analyst additions

- step 3 documents the exact Skill-attachment network contract (`GET` skill details → `PATCH .../skill/prompt_lib/{project}/{skillId}` with `skill_version_id`) — *added: this is a genuinely distinct endpoint/payload shape from both the Toolkit (`PATCH .../tool/...`) and Agent (`PATCH .../application_relation/...`) association calls ELITEA-1909 already documented; without this, an implementer extending ELITEA-1909's `click_approve_and_wait_for_creation()` helper would likely wait on the wrong response pattern (it currently expects exactly a toolkit-PATCH + an application_relation-PATCH, per `automation/pages/generate_agent_modal_page.py:199-218`) and either time out or silently not await the skill relation call.*
- step 5 documents that the SKILLS section is a **separate accordion** (`agent-skills-section`) from the Tools/Toolkits accordion ELITEA-1909 already documented (`agent-toolkits-section`) — *added: unlike ELITEA-1909's own case, where the case text said "TOOLKITS section" for both Toolkit and nested-Agent verification and the live UI turned out to share one accordion (a case-text/product mismatch ELITEA-1909's AFS flagged as reverse-masking), ELITEA-1911's case text says "SKILLS section" and the live UI genuinely has a dedicated Skills accordion — no mismatch here, but an implementer who assumed all "Build with AI" attached-resource assertions funnel through `AgentDetailPage.is_toolkit_attached()` (ELITEA-1909's reused helper) would get a false negative, since Skills render via a distinct `skill-card-{id}` component/testid, not `agent-toolkit-card`.*
- Preconditions documents the Skill name field's format constraint (lowercase/digits/hyphens, ≤32 chars) discovered while creating the fixture Skills — *added: not mentioned anywhere in the case or in ELITEA-1909/1907's AFS's (which fixture Toolkits/Agents, not Skills), and directly affects how an implementer names any Skill fixture for this or future Skill-suggestion cases.*
- step 6 documents the counter-based absence check (`"1/5 skills added."`, not `"2/5"`) as a second, independent signal alongside the missing-card check — *added: mirrors ELITEA-1909's own step-9 pattern of pairing a locator-based absence check with a network-log cross-check, applied here to the Skills accordion's own counter affordance instead.*

## Cleanup
1. Created "GitHub Repository Manager" agent (id `5054`, the case's own step-3/4 output) — deleted via the UI's "Delete agent" menu action (Agent Actions kebab → Delete agent → typed confirmation), confirmed via redirect away from the agent's detail page and a subsequent full-page text search finding no `elitea-1911` references.
2. Fixture Skill `elitea-1911-changelog-writer` (id `650`) — deleted via the UI's "Delete skill" menu action, confirmed via redirect to `/skills/all`.
3. Fixture Skill `elitea-1911-issue-labeler` (id `651`) — deleted via the same flow.
4. No product state left behind. Project `399` ("Private") inventory is back to its pre-run baseline (Skill count back to pre-run 15; Agent count back to pre-run baseline).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `page.get_by_test_id("generate-agent-open-button")` | on-main ✓ (confirmed via `git grep` against `origin/main`, fetched fresh this run) | n/a — already present |
| Prompt textarea | `page.get_by_test_id("generate-agent-prompt-input")` | on-main ✓ | n/a — already present |
| Generate button | `page.get_by_test_id("generate-agent-submit-button")` | on-main ✓ | n/a — already present |
| "Suggested Skills:" section | `page.get_by_test_id("generate-agent-resource-section-skill")` — same generic `generate-agent-resource-section-{entity_type}` template ELITEA-1907/1909 already documented, confirmed live for `entity_type="skill"` | on-main ✓ (landed via ELITEA-1907's `add-data-testid` pass; generic over entity type, not skill-specific) | n/a — already present |
| Suggested-skill checkbox | `page.get_by_test_id(f"generate-agent-resource-checkbox-skill-{skill_id}")` — e.g. `generate-agent-resource-checkbox-skill-650` | on-main ✓ (same generic template) | n/a — already present |
| Suggested-skill name/description | `page.get_by_test_id(f"generate-agent-resource-name-skill-{skill_id}")` / `generate-agent-resource-description-skill-{skill_id}` | on-main ✓ (same generic template) | n/a — already present |
| "Create Agent" approve button | `page.get_by_test_id("generate-agent-approve-button")` | on-main ✓ | n/a — already present |
| Created-agent SKILLS accordion | `page.get_by_test_id("agent-skills-section")` — pre-existing, ELITEA-1735's testid-only rework; already used by `AgentDetailPage.skills_section`/`ensure_skills_section_visible()` | on-main ✓ | n/a — already present |
| SKILLS accordion counter | `page.get_by_test_id("agent-skills-counter")` — pre-existing, already used by `AgentDetailPage.get_skills_counter_text()` | on-main ✓ | n/a — already present |
| Attached-skill card | `page.get_by_test_id(f"skill-card-{skill_id}")` (`SKILL_CARD_SELECTOR` template already on `AgentDetailPage`) — or the prefix-match `SKILL_CARD_ANY_SELECTOR` (`[data-testid^="skill-card-"]`) filtered by name text, per the class's existing dual-selector pattern | on-main ✓ | n/a — already present |
| Skill create form: Name/Description fields, Instructions editor, Save button | `skill-name-input-field`, `skill-description-input-field`, `skill-instructions-editor-content`, `skill-save-button` (all confirmed live this run, pre-existing from prior Skill-management AFS's, e.g. ELITEA-1737/1739) | on-main ✓ | n/a — already present |

**Summary for the implementer:** no new `add-data-testid` work is needed — every element steps 1–6 touch already carries a testid confirmed on `origin/main` (verified via a fresh `git fetch origin` in `../EliteaUI` this run), inherited either from the generic `generate-agent-resource-*-{entity_type}-{id}` template (ELITEA-1907's pass, already generic over `entity_type` and therefore requires zero new UI work for `"skill"`) or from ELITEA-1735's pre-existing Skills-section testid set. The one piece of net-new work is **test-infrastructure**, not UI testids: `automation/api/client.py`'s `SkillAPI` currently has no `create_skill()` method (only `list_skills()`/`delete_skill()`) — the implementer extending ELITEA-1909's test class will need either a new `SkillAPI.create_skill()` convenience method (mirroring `AgentAPI.create_agent_full()`'s pattern) or a UI-driven fixture helper (this exploration created fixtures via the live Skill-creation form, see Test Data) to avoid hand-rolling skill creation inside the test itself.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/399` — generates the draft; response includes `suggested_skills: [{...both fixture skills...}]` when relevant fixtures exist in inventory (empty array otherwise — mirrors ELITEA-1909's `suggested_toolkits`/`suggested_agents` finding, and ELITEA-1907's mocked-test payload, which deliberately leaves `suggested_skills: []` untouched — confirming this exact category was never previously exercised end-to-end).
- `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201` — creates the base agent (unchanged from ELITEA-1909; `version_details.tools` is `[]`, resources are not attached in this call).
- `GET /api/v2/elitea_core/skill/prompt_lib/399/{skill_id}` → `200` — `fetchSkillDetails`, reads the selected skill's `version_details.id` (the `skill_version_id` the relation PATCH needs). Fires once per selected Skill, before its relation PATCH.
- `PATCH /api/v2/elitea_core/skill/prompt_lib/399/{skill_id}` → `201` — attaches a selected Skill. Body: `{"has_relation": true, "entity_version_id": <agent_version_id>, "skill_version_id": <skill_version_id>, "entity_type": "agent"}` (source: `skillsApi.js`'s `updateSkillRelation` mutation — `entity_type` defaults to `"agent"` via `SKILL_ENTITY_TYPE_AGENT`). Response: `{"has_relation": true, ...}` (not independently re-verified field-by-field beyond confirming `201` and the counter incrementing live).
- One `GET`+`PATCH .../skill/...` pair fires **per selected Skill only** — `associateSkills` (`GenerateAgentModal.jsx`) runs `Promise.allSettled` over just the selected set, same `has_relation`-toggle pattern ELITEA-1909 already documented for Toolkits/Agents/MCPs/Pipelines via their respective association calls. **Zero** calls fire for the deliberately-unselected Skill — confirmed live (no `skill/prompt_lib/.../651` request in the network log at all).

## Known Defects Found During Exploration

**No functional product defect found.** One clarification (already covered by ELITEA-1909's filed clarification, not re-filed — see Preconditions) and one test-infrastructure gap:

1. **[Clarification — already filed via ELITEA-1909, not re-filed]** Case ELITEA-1911's stated preconditions never establish how to make an existing Skill suggestible (step 1's prerequisite: "at least two skill cards"), identical in shape to ELITEA-1909's already-filed clarification for the Toolkit/Agent case. Not filed as a second ticket to avoid duplicating the same recurring case-authoring gap already tracked once for this "Build with AI" case family — see the linked ELITEA-1909 issue for the resolution.
2. **[Not a defect — test-infrastructure gap, not filed]** `automation/api/client.py`'s `SkillAPI` has no `create_skill()` method (only `list_skills()`/`delete_skill()`), unlike `AgentAPI`/`ToolkitAPI`/`CredentialAPI` which all have `create_*` convenience methods. This exploration created its fixture Skills via the live UI form instead. Flagged in Automation Hints for whoever implements this extension — not a product defect, purely a gap in the test framework's existing API-client surface.

## Blocked Steps
None. All 6 case steps executed live, end to end, including the step 1 Skill-suggestion path the case's own preconditions don't fully establish (resolved via the two fixture-Skill precondition documented above).

## Gap assertions (what the implementer appends to ELITEA-1909's covering test/class)

ELITEA-1909's covering test class (`TestAgentBuildWithAISelectedResourcesAttached`) already proves the shell (generate → observe suggestions → select one, leave a sibling unchecked → approve → auto-navigate → verify attached → verify absent) for Toolkit + nested Agent. The implementer should add a **sibling test method in the same class** (or a small new method reusing the class's existing fixtures/page-object wiring) that asserts specifically:

1. **Given** a draft generated with two relevant Skill fixtures in project inventory, **the "Suggested Skills:" section renders both as unchecked cards** with name + description (`generate-agent-resource-section-skill` populated with 2 items) — not currently asserted anywhere (ELITEA-1907's covering test asserts the *absence* of this section when `suggested_skills: []`, the inverse case).
2. **When** one Skill checkbox is selected and "Create Agent" is clicked, **the network sequence includes a `GET` + `PATCH .../skill/prompt_lib/{project}/{skillId}` pair** (not a `tool`/`application_relation` PATCH) — extending `click_approve_and_wait_for_creation()` (or a new sibling method) to additionally wait on this response pair when a Skill was selected, since the existing method (`automation/pages/generate_agent_modal_page.py:184-218`) currently only expects the toolkit-PATCH + application_relation-PATCH pair and does not know about the Skill relation call shape.
3. **Then** the created agent's **`agent-skills-section`** accordion (not `agent-toolkits-section`) contains a `skill-card-{id}` for the selected Skill, and the counter reads `"1/5 skills added."` — a new assertion path, since `AgentDetailPage.is_toolkit_attached()` (ELITEA-1909's reused helper) does not look inside the Skills accordion at all; the implementer should reuse `AgentDetailPage`'s existing `SKILL_CARD_SELECTOR`/`SKILL_CARD_ANY_SELECTOR` constants and `get_skills_counter_text()` method (both already present, pre-dating this case, from ELITEA-1735's Skills-management work) rather than adding new locators.
4. **And** the deliberately-unselected sibling Skill has **no** `skill-card-{id}` in the Skills accordion and **no** `skill/prompt_lib/.../{its_id}` network call at all — same dual locator+network-log absence-verification discipline ELITEA-1909 already established for its own step 9.

No new page-object locators are needed (see Concrete Handles) — only new page-object *methods* (a Skill-aware wait helper for step 2 above) and a new/extended test method.
