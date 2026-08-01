# Test Case: Agent "Save As Version" preserves all attached Skills

## Metadata
- **TMS ID**: ELITEA-1889
- **Linked Story**: none
- **Priority**: l1 (critical, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), default project
  model: Anthropic Claude 4.5 Sonnet (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`,
  `supports_reasoning: true`)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — **resume pass**, superseding the
  prior `defect-found` AFS at this same path
- **Status**: `ready-for-automation` — the blocking defect
  ([EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524))
  that previously stopped this case at its own Step 1 is **confirmed fixed on the
  DEV backend** in this run. The full case (create Agent, attach Skill, Save As
  Version, open the new version, verify the Skill is still listed) was executed
  end-to-end live, no synthetic input, with a full cleanup. One caveat carries
  forward for the implementer — see "Known Defects" below: the **API-level**
  `AgentAPI.create_agent()` helper (a different, test-code-only path) is still
  broken and must not be used as-is for this test's fixture data.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- An existing Skill named "VersionedSkill" is available in the project — **case-text
  drift, not a literal value**: the live Skill `Name *` field is kebab-case-only
  client-side-validated (same pattern already documented for ELITEA-1789/1737/1735/1739
  — see `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`). Used
  `elitea-1889-versioned-skill` instead when creating the skill in this run.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `elitea-1889-versioned-skill` (see case-text drift note
  above — the case's literal `"VersionedSkill"` is not typeable).
- Skill description / instructions: any non-empty strings under limits (content not
  asserted by this case). Instructions used this run: "You are a test skill created
  for ELITEA-1889 save-as-version preservation verification. Respond with VERSIONED."
- Agent name: e.g. `elitea-1889-versioning-agent` (used this run); description a
  short generic string (agent instructions content is not asserted by this case).
- Version name: `v1` (per case Test Data) — confirmed live the "Create version"
  dialog's Name field accepts an arbitrary string and the Save button stays
  disabled until it is non-empty (no auto-generation).

**Agent creation path — IMPORTANT for the implementer.** Use the live **UI**
create flow (`AgentsListPage.navigate_to_create()` → `AgentFormPage.fill_form()`
→ `save_and_wait_for_navigation()`), exactly as `test_skill_agent_version_selector.py`
(ELITEA-1789) already does — this is now confirmed to work end-to-end (see
Test Steps below, `201 Created`). **Do NOT** use the raw `AgentAPI.create_agent()`
helper (`automation/api/client.py:366`) for this test's fixture data: it still
hard-codes `"temperature": 0.6, "reasoning_effort": "medium"` and still 400s
against the project's reasoning-capable default model — confirmed broken again in
this run (see Known Defects). If API-side agent provisioning is preferred over a
full UI create (e.g. for speed), use `AgentAPI.create_agent_full()` with the
`reasoning_effort: "none"` / no-`temperature` workaround payload, exactly as
`test_agent_save_as_version.py::_build_dedicated_agent_payload()` (ELITEA-1888)
already does — that pattern is proven working in the existing suite.

No `reuse-existing` fixture applies — this is a fresh-state flow (1 skill + 1 agent
created and torn down within the run).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input`), Description
   (`skill-description-input`), and Instructions (`skill-instructions-editor-content`,
   a CodeMirror editor — used `type(slowly=true)`, not `fill`) with the Skill test data
   above. Click Save (`skill-save-button`).
   - **Verify — PASSES.** URL settled on `/skills/all/{id}` (Skill ID `591`, base
     Version ID `611` in this run — IDs are per-run, not stable). No nav-blocker
     dialog fired this run (unlike some prior ELITEA-178x runs — not asserted
     either way by this case). No console errors.
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`) and
   Description (`agent-description-input`) only — no other field touched (default
   model/LLM settings left as-is). Click Save (`agent-save-button`).
   - **Verify — PASSES** (previously the blocking defect; **now confirmed fixed**).
     `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201 Created`. Page
     navigated to `/agents/all/{agent_id}` (agent id `4895` in this run, base
     version id `4914`). No console errors, no validation toast.
3. In the Agent detail page's Skills section (`agent-skills-section`,
   `0/5 skills added.` initially), click the add-skill button
   (`agent-add-skill-button`), select the Skill created in Step 1 from the search
   dropdown (menu item by accessible name = the skill's kebab-case name).
   - **Verify — PASSES.** Counter updated to `1/5 skills added.`; a skill card
     appeared showing the skill's name and its version (`base`). No console errors.
     Attach is auto-saved via API — the agent-level `Save` button stayed disabled
     throughout (same behavior documented for ELITEA-1789), but `Save As Version`
     was enabled once the skill was attached.
4. Click "Save As Version" (`agent-save-as-version-button`). In the "Create version"
   dialog that appears, enter the version name (`agent-version-dialog-name-input`)
   and click the dialog's Save (`agent-version-dialog-save-button`).
   - **Verify — PASSES.** Dialog's Save button was disabled while the Name field was
     empty, enabled once "v1" was typed (confirms case's Test Data note about the
     dialog requiring a non-empty name). On confirm: `POST
     /api/v2/elitea_core/versions/prompt_lib/399/4895` → `201 Created`; URL updated
     to `/agents/all/4895/4915` (new version id `4915`); VERSION selector
     (`agent-version-selector-trigger`) now reads "v1"; agent-level `Save`/`Discard`
     returned to disabled (persisted, not a local edit).
5. With the new version "v1" now open (this is the state the app lands in
   immediately after Step 4 — no separate navigation was needed to "open" it),
   verify the SKILLS section still lists the attached Skill.
   - **Verify — PASSES.** Skills section shows `1/5 skills added.` with the same
     skill card (`elitea-1889-versioned-skill`, version `base`) present under the
     new agent version "v1" (version id `4915`). Confirmed via a fresh `GET
     /api/v2/elitea_core/application_skills/prompt_lib/399/4915` → `200 OK` — the
     skill association is server-persisted against the *new* version id, not just
     a stale UI render carried over from the prior version's state.

## Expected Results

- Agent is created successfully via the plain UI create form (no LLM-settings
  defect blocking Save).
- The attached Skill ("VersionedSkill" per case text; `elitea-1889-versioned-skill`
  live) is visible in the agent's Skills section before and after "Save As Version".
- "Save As Version" creates a new named version ("v1") whose Skills section still
  lists the attached Skill — the case's core assertion. Confirmed both in the UI
  (skill card rendered under version "v1") and at the API layer
  (`GET .../application_skills/prompt_lib/399/{new_version_id}` returns the skill).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Skill "VersionedSkill" available | A Skill exists to attach | step 1 | Skill created live (`elitea-1889-versioned-skill`, id 591); case-text drift on the literal name (kebab-case-only field) — clarification, same pattern as ELITEA-1789/1735/1737/1739 | asserted *(with clarification)* |
| Step 1: Create an Agent with attached Skill "VersionedSkill" | Agent created, "VersionedSkill" listed in SKILLS section | steps 2–3 | step 2: `201 Created` on agent create; step 3: skill card + `1/5 skills added.` counter | asserted *(decomposed: agent-create and skill-attach split into two AFS steps)* |
| Step 2: Click "Save As Version" → enter "v1" → confirm | Version "v1" created | step 4 | `agent-version-selector-trigger` reads "v1"; `POST .../versions/...` → 201; new version id in URL | asserted |
| Step 3: Open version "v1" in the Agent editor | "v1" loaded in editor | step 4 (no separate navigation needed — landed on "v1" immediately after confirm) | URL `/agents/all/4895/4915`, VERSION selector shows "v1" | asserted *(decomposed — the app auto-opens the new version; no distinct "open" action exists to exercise separately)* |
| Step 4: Verify "VersionedSkill" listed in SKILLS section of "v1" | Skill present in the new version | step 5 | skill card in Skills section under v1; `GET application_skills/.../4915` → 200 with the skill present | asserted |
| Test Data: Skill name "VersionedSkill" | literal value | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1889-versioned-skill` instead | clarification (reverse-masking, same pattern as ELITEA-1735/1737/1739/1789) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| `POST /api/v2/elitea_core/applications/prompt_lib/399` returns `201` (not just UI navigation) | Direct evidence the previously-blocking #524 defect is fixed at the API-validation layer, not just superficially in the UI — grounds the fixed-status confirmation posted back to #524 |
| `GET /api/v2/elitea_core/application_skills/prompt_lib/399/{new_version_id}` returns the skill | The case's core assertion ("skill still listed after Save As Version") is confirmed server-side, not just as a possibly-stale client-side render — this is the load-bearing assertion an automated test must wait on/check, not just the UI card |
| No console errors across all 5 steps | Silent errors are the worst bugs (`test-case-analysis` discipline) — explicitly checked after every interaction, not just relying on visible UI success |
| "Create version" dialog Save button disabled while Name empty, enabled once non-empty | Confirms the case's own Test Data note about entering a version name is a real, enforced precondition of the dialog, not decorative — useful assertion for the automated test to include |

## Cleanup

- Agent `elitea-1889-versioning-agent` (id `4895`) deleted live via the agent
  overflow menu → "AGENT" group → "Delete agent" (`delete-agent-menuitem`) →
  type-to-confirm dialog → Delete. Deleting the agent removes all its versions
  (base + v1) in one action — no separate per-version cleanup needed.
- Skill `elitea-1889-versioned-skill` (id `591`) deleted live via the skill
  overflow menu (`skill-controls-menu-button`) → "SKILL" group →
  `skill-delete-menu-item` → type-to-confirm dialog → Delete.
- Verified: returned to `/skills/all` list; no orphaned skill or agent remains.

## Concrete Handles (discovered during exploration)

| Element | testid | Confirmed live this run? | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` | yes | kebab-case validation |
| Skill Description field | `skill-description-input` | yes | |
| Skill Instructions editor | `skill-instructions-editor-content` | yes | CodeMirror; use `press_sequentially`/`type(slowly=true)`, not `fill` |
| Skill Save button | `skill-save-button` | yes | |
| Agent Name field | `agent-name-input` | yes | |
| Agent Description field | `agent-description-input` | yes | |
| Agent Save button | `agent-save-button` | yes | `AgentFormPage.save_button`, `automation/pages/agent_form_page.py:145`; POST now returns 201 (previously 400 — #524, now fixed) |
| Agent Skills section | `agent-skills-section` | yes | `AgentDetailPage.skills_section` |
| Add-skill button | `agent-add-skill-button` | yes | `AgentDetailPage.agent_add_skill_button`; opens a search-and-select dropdown; select by `getByRole('menuitem', { name: <skill_name> })` |
| Skills counter | (read via `AgentDetailPage.get_skills_counter_text()` / `wait_for_skills_counter()`) | yes | reads "N/5 skills added." text |
| Skill card (per-skill, dynamic) | `AgentDetailPage.SKILL_CARD_SELECTOR = '[data-testid="skill-card-{}"]'` (by skill_id) or `SKILL_CARD_ANY_SELECTOR` prefix-match by rendered name | yes | already exists in `agent_detail_page.py`; use `is_skill_attached(skill_name)` helper |
| **Save As Version button** | `agent-save-as-version-button` | yes | `AgentFormPage.save_as_version_button` (`automation/pages/agent_form_page.py:163-167`) — **confirmed in this run to carry ONLY `testid` + `description`, no `fallback=` lambda.** The forbidden-fallback flag raised in the prior AFS pass no longer applies to the code as it stands now; re-verify at implementation time in case it regresses, but do not carry that finding forward as still-open. |
| Create-version dialog Name field | `agent-version-dialog-name-input` | yes | `AgentDetailPage.create_version_name_input` |
| Create-version dialog Save button | `agent-version-dialog-save-button` | yes | `AgentDetailPage.create_version_save_button`; disabled while Name is empty |
| VERSION selector trigger | `agent-version-selector-trigger` | yes | `AgentDetailPage.version_selector_trigger`; reads current version name |
| Delete-agent menu item | `delete-agent-menuitem` | yes | under the overflow menu's "AGENT" group, distinct from the "VERSION" group's `Delete` (which only deletes the currently-open version and was disabled on the base/only version in this run) |
| Delete-confirmation name field | scope `delete-confirm-name-input` to inner `#name` | yes | shared pattern across Agent/Skill delete dialogs |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | yes | not testid'd — pre-existing residual gap, out of this case's scope |
| Agent-side "Skills" attach/version infra (`attach_skill`, `is_skill_attached`, `_skill_card`, skill-version-selector testids) | see `automation/pages/agent_detail_page.py:160-230` and `:1200-1600` | pre-existing, reused unchanged | Fully built out already from ELITEA-1789/1792/1793 work — nothing new needed for this case beyond calling the existing methods |
| Agent version create/confirm infra (`open_save_as_version_dialog`, `confirm_new_version`, `get_version_id`) | `automation/pages/agent_detail_page.py:288-360` | pre-existing, reused unchanged | Built out from ELITEA-1888 work — directly reusable for this case |

## Network Behavior

- `POST /api/v2/elitea_core/applications/prompt_lib/399` — agent create; `201`
  (previously `400` under #524).
- `GET /api/v2/elitea_core/application_skills/prompt_lib/399/{version_id}` — fires
  both on initial agent-detail load (base version) and again after "Save As
  Version" completes (new version id) — this is the call the automated test should
  wait on / assert against to confirm skill-persistence server-side, not just by
  reading the rendered card.
- `POST /api/v2/elitea_core/versions/prompt_lib/399/{agent_id}` — Save As Version
  confirm; `201`. Response's version id becomes the new URL segment and the value
  `get_version_id()` should read after confirmation.
- `PATCH /api/v2/elitea_core/skill/prompt_lib/399/{skill_id}` — fired once when
  attaching the skill to the agent (part of the attach flow's own bookkeeping, not
  something this case needs to assert on directly).

## Known Defects Found During Exploration

- **[EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
  — status update, not a new defect.** The **UI create-form** path (`/agents/create`
  plain Save) is **confirmed fixed** on DEV as of this run — posted verification
  comment on the issue. However, the **API-level** `AgentAPI.create_agent()` helper
  (`automation/api/client.py:366`, used by the shared `agent_id` pytest fixture at
  `automation/fixtures/data_fixtures.py:76`) is a **separate, still-broken** code
  path: it hard-codes `"temperature": 0.6, "reasoning_effort": "medium"` and still
  reproduces the identical `400` (`value_error: temperature is not allowed together
  with a reasoning_effort ...`). Reconfirmed live this run via
  `pytest tests/ui/agents/test_agent_management.py -k test_edit_agent_name` (a test
  that depends on the `agent_id` fixture) — fails at setup with the same 400. This
  was already known and documented on #524 by two prior comments (ELITEA-1897 and
  ELITEA-1872 passes); **not re-filed**, just reconfirmed still-open and flagged
  here because it directly affects how this case's implementer should provision
  agent fixture data (see Test Data § "Agent creation path" above — use the UI flow
  or `create_agent_full()` with the `reasoning_effort: "none"` workaround, not the
  raw `create_agent()` helper).
- No new defects found in the Save As Version / skill-preservation flow itself —
  the case's own pass/fail criteria are all satisfied.

## Automation Hints

- Framework: pytest + Playwright, project's existing page-object model
  (`automation/pages/`).
- Page objects: `AgentFormPage` (create form), `AgentDetailPage` (extends
  `AgentFormPage`; skills attach + Save As Version infra), `SkillFormPage` /
  `SkillDetailPage` (skill create) — all pre-existing, no new page-object methods
  needed for this case.
- Closest sibling implementations to model this test on:
  - `tests/ui/agents/test_agent_save_as_version.py` (ELITEA-1888) — Save As
    Version → named version → verify in VERSION dropdown, using the
    `reasoning_effort: "none"` dedicated-agent-payload workaround for
    `AgentAPI.create_agent_full()`. This case's test should follow the same
    workaround for its agent fixture, then layer skill-attach + skill-persistence
    assertions on top (which ELITEA-1888's test does not cover).
  - `tests/ui/skills/test_skill_agent_version_selector.py` (ELITEA-1789) — Skill
    creation via UI, Agent creation via UI (`fill_form` + `save_and_wait_for_navigation`),
    skill attach, and version-selector interactions — the closest existing example
    of the full Skill-create → Agent-create (UI) → attach flow this case needs for
    Steps 1–3.
- Wait strategy: after "Save As Version" confirm, wait on the URL's version-id
  segment changing (or the `agent-version-selector-trigger` text updating to the
  new name) before asserting the Skills section — same pattern already used in
  `AgentDetailPage.confirm_new_version()`.
- This case's own setup (fresh skill + fresh agent + attach + version) does not
  overlap enough with ELITEA-1888's edit-instructions setup to justify an
  `extend-existing` classification — the skill-creation and skill-attach
  scaffolding this case needs is absent from that test file entirely. Treated as
  `ready-for-automation` (fresh implementation), reusing existing page-object
  methods rather than a shared test file.
