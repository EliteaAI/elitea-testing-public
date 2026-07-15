# Test Case: Agent "Save As Version" preserves all attached Skills

## Metadata
- **TMS ID**: ELITEA-1889
- **Linked Story**: none
- **Priority**: critical (per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), default project
  model: Anthropic Claude 4.5 Sonnet (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`,
  `supports_reasoning: true`)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `defect-found` — **case cannot be executed past its own Step 1.** A
  critical, deterministically-reproducible product defect
  ([EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524))
  blocks Agent creation for **any** new agent in this project via the default UI
  create flow, while the project's default model is a reasoning-capable one. No
  agent exists in the project to substitute (`/agents/all` list is empty — verified
  live), so there is no way to reach Steps 2–4 (Save As Version / open version /
  verify Skills section) at all right now.

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
  asserted by this case).
- Agent name: e.g. `elitea-1889-versioning-agent`; description a short generic string
  (agent instructions content is not asserted by this case).
- Version name: `v1` (per case Test Data — this run never reached the point where a
  version name is entered; unconfirmed live whether the "Save As Version" dialog
  accepts arbitrary version names or auto-generates them — see Blocked Steps).

No `reuse-existing` fixture applies — this is a fresh-state flow (1 skill + 1 agent
created and torn down within the run) and, per this run's discovery, **no existing
agent exists in the project to fall back on** (`/agents/all` verified empty live).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input`), Description
   (`skill-description-input`), and Instructions (`skill-instructions-editor-content`,
   a CodeMirror editor — used `type(slowly=true)`, not `fill`) with the Skill test data
   above. Click Save (`skill-save-button`).
   - **Verify — PASSES.** A "There are unsaved changes. Are you sure you want to
     leave?" nav-blocker dialog appeared — confirmed via `alert-dialog-confirm-button`.
     URL settled on `/skills/all/{id}`; Skill ID `573` in this run, base Version ID
     `593`. Same behavior already documented for ELITEA-1789/1737/1735.
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`) and
   Description (`agent-description-input`) only — no other field touched (default
   model/LLM settings left as-is, matching the case's intent of a plain agent create).
   Click Save (`agent-save-button`).
   - **Verify — FAILS. Blocking defect, reproduced 2/2 in independent fresh page
     loads** (separate `browser_navigate` to `/agents/create` each time, same
     Name/Description test data, no shared state carried over, no synthetic input —
     all real `click()`/`pressSequentially()`). The page never navigates away from
     `/agents/create`; `POST /api/v2/elitea_core/applications/prompt_lib/399` returns
     `400 Bad Request`:
     ```json
     [{"type": "value_error", "loc": ["versions", 0, "llm_settings"], "msg": "Value error, temperature is not allowed together with a reasoning_effort (other than 'none') — reasoning models reject a custom temperature"}]
     ```
     A visible alert/toast surfaces the same message to the user; a console warning
     fires at `useCreateApplication.jsx:92` with the identical `value_error`. Filed as
     [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
     (see Known Defects).
   - **Root-cause hint** (not confirmed, for RCA): `GET
     /api/v2/configurations/models/399?include_shared=true` shows the project's
     default model is `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` ("Anthropic
     Claude 4.5 Sonnet") with `"supports_reasoning": true`. The create form's default
     `llm_settings` payload apparently still sends a non-null `temperature` alongside
     a non-`'none'` `reasoning_effort` for this model — the backend's validator now
     rejects that combination. Every one of the 11 models returned by that endpoint
     has `supports_reasoning: true` except `gpt-5-mini`, so this is not a one-model
     edge case — it looks like a systemic regression in default-LLM-settings
     construction (or in what counts as "reasoning-capable" now) affecting the whole
     Agent-create surface.
   - **No workaround found via the UI.** The plain create form (General / Instructions
     / Welcome message / Chat starters / Advanced-Step-limit sections) exposes no
     visible control to change temperature/reasoning_effort defaults before Save.
     Whether an LLM-model-settings panel exists elsewhere (e.g. reachable only after
     the agent exists, or via a "model settings menu" control seen on the Skill
     detail page's embedded-chat panel, not the Agent create form) that could avoid
     this default is an **open question**, not a confirmed workaround — flagged for
     whoever picks up #524, not investigated further here since it is out of this
     case's scope (the case doesn't ask to customize LLM settings).
3. **Not reached.** Confirmed live that `/agents/all` (list view) is currently
   **empty** for this project — there is no existing agent in the project to
   substitute for a freshly-created one, so there is no path to Steps 2–4 of the
   case (attach Skill / Save As Version / open version / verify Skills section)
   right now, by any route.
4. **Not reached** — depends on Step 2/3.

## Handles Reference

Partially populated — only what was actually exercised or confirmed present in the
codebase this run. Everything below Test Step 2 is **unconfirmed live** (the flow
never reached these elements) and is carried over from the existing page-object
inventory for the implementer's reference once #524 is fixed.

| Element | testid | Confirmed live this run? | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` | yes | kebab-case validation, same as prior AFS |
| Skill Description field | `skill-description-input` | yes | |
| Skill Instructions editor | `skill-instructions-editor-content` | yes | CodeMirror; `press_sequentially` |
| Skill Save button | `skill-save-button` | yes | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | yes | fires on Skill-create Save |
| Agent Name field | `agent-name-input` | yes | |
| Agent Description field | `agent-description-input` | yes | |
| Agent Save button | `agent-save-button` | yes (click succeeds; the resulting POST 400s) | `AgentFormPage.save_button` in `automation/pages/agent_form_page.py:145` |
| Skill controls (overflow) menu | `skill-controls-menu-button` | yes | used for skill cleanup this run |
| Delete-skill menu item | `skill-delete-menu-item` | yes | |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name`) | yes | |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | yes | not testid'd — pre-existing residual gap, out of this case's scope |
| **Agent Save As Version button** | `agent-save-as-version-button` | **NOT exercised — no agent could be created to test it on.** Referenced in `automation/pages/agent_form_page.py:163-167`, currently carrying a `fallback=lambda page: page.get_by_role("button", name="Save As Version")` | **Pre-existing policy violation, NOT introduced by this AFS**: `fallback=` is forbidden by `.agents/testing.md` § Locator policy / `.claude/rules/page-objects.md`. Flagged for the implementer/lead to strip when this case is picked back up — not fixed here per the dispatch note ("that's a pre-existing issue in the page object, not something to fix yourself") |
| Skill-detail-page "Save As Version" button (a **different**, already-functioning control, confirmed live on the Skill detail page, not the Agent detail page) | none captured — out of scope; only glimpsed while cleaning up the test skill | **confirmed present and enabled** on `/skills/all/{id}` (`button "Save As Version"`, next to disabled Save/Discard) | Evidence only that the "Save As Version" UI *pattern* exists elsewhere in the product and is not itself broken — does not stand in for the Agent-side control, which lives on a different page/component and was never reached |
| Agent Skills section / attach-skill flow | `agent-add-skill-button`, `skill-card-{skill_id}`, `agent-skills-section`, `agent-skills-counter` (all in `automation/pages/agent_detail_page.py`, documented fully in `test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md`) | **not exercised this run** | Carried over unchanged from the ELITEA-1789/1735 rework — these testids exist and were previously confirmed live on `automation/testids`; nothing in this run contradicts that, but this run did not re-confirm them since no agent existed to attach a skill to |
| Version selector / open-a-specific-version control (Agent side) | **none known** | **not found — never reached.** No agent version-switcher UI element was ever observed by this analyst pass; the codebase has no existing method/locator for "open agent version {name}" on `AgentDetailPage` (only the Skill-side `SKILL_VERSION_*` selectors documented for ELITEA-1789 exist, and those are for the Skill's own version, not for switching between an *Agent's* saved versions) | **testid gap, not yet scoped** — once #524 unblocks Step 2, the implementer will need to explore what UI actually appears after "Save As Version" is clicked (a version dropdown near the Agent's Information section, an overflow-menu "Versions" list, a URL-param switch, or something else) before any handle can be captured here. This AFS cannot specify it without fabricating a locator sight-unseen (anti-pattern per `test-case-analysis` § Anti-patterns) |

## Expected Results

Not observed — case blocked at Step 2. Per the case's own Pass/Fail Criteria, the
expected end-state is: a saved version "v1" whose Skills section still lists
"VersionedSkill" (i.e. the analogous kebab-case skill created for this run). None of
that could be produced or falsified in this environment as it currently stands.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Skill "VersionedSkill" available | A Skill exists to attach | Test Step 1 | Skill created live (`elitea-1889-versioned-skill`, id 573); case-text drift on the name — clarification, not a defect (kebab-case-only field), same pattern as ELITEA-1789/1735/1737/1739 | covered — with clarification |
| Step 1: Create an Agent with attached Skill "VersionedSkill" | Agent created, "VersionedSkill" listed in SKILLS section | Test Step 2 (agent-create half only) | Agent creation itself fails — `400` on `POST .../applications/prompt_lib/399`, default `llm_settings` payload conflict; skill-attach half of this step was never reached because there is no agent to attach to | **blocked — real product defect** (#524), not case-text drift: the case asks for a plain agent create with an attached skill, and the plain create path itself is broken independent of any skill-attach logic |
| Step 2: Click "Save As Version" → enter "v1" → confirm | Version "v1" created | not reached | N/A | blocked (depends on Step 1) |
| Step 3: Open version "v1" in the Agent editor | "v1" loaded in editor | not reached | N/A | blocked (depends on Step 1–2) |
| Step 4: Verify "VersionedSkill" listed in SKILLS section of "v1" | Skill present in the new version | not reached | N/A | blocked (depends on Step 1–3) |
| Test Data: Skill name "VersionedSkill" | literal value | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1889-versioned-skill` instead | clarification (reverse-masking, same pattern as ELITEA-1735/1737/1739/1789) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| `POST /api/v2/elitea_core/applications/prompt_lib/399` response body (`400`, pydantic `value_error`) | The concrete evidence that Agent creation is broken at the API-validation layer, not a UI-only glitch — grounds the defect filing and gives RCA an exact `loc`/`msg` to start from |
| `GET /api/v2/configurations/models/399?include_shared=true` response | Establishes the project's default model (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`) has `supports_reasoning: true`, and that 10/11 configured models share that flag — supports the root-cause hint that this is a systemic default-settings regression, not a one-model fluke |
| `/agents/all` list state (confirmed empty) | Rules out "use an existing agent instead" as a workaround for reaching Steps 2–4 in this environment right now — the blocker is total, not just "can't create a fresh one" |
| Reproduction across two independent, fresh `/agents/create` page loads | Confirms the failure is deterministic (2/2) and not a one-off flake, per the pristine-repro discipline (`reproducing-issues` skill / `test-case-analysis` § Absolute boundaries) — no synthetic input was used anywhere in this run, only real `click()`/`type(slowly=true)` |
| Skill-detail-page "Save As Version" button, confirmed present/enabled | Establishes the "Save As Version" UI *pattern* is not universally broken in the product — narrows the defect specifically to the Agent-create → Agent-versioning path, information useful to whoever triages #524's scope |

## Known Defects

### [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524) — [CRITICAL] Agent create fails 400: default LLM settings send temperature with reasoning_effort on a reasoning-capable model

- **Repro rate**: 100% (2/2), both in fresh, independent `/agents/create` page loads
  (separate `browser_navigate`, no shared session state), using only real
  `click()`/`pressSequentially()` — no synthetic event dispatch anywhere in this
  session.
- **Trigger**: Plain `/agents/create` form, Name + Description filled, no other field
  touched, Save clicked. No custom model/LLM settings were ever opened or changed by
  this analyst pass.
- **Evidence**: `POST /api/v2/elitea_core/applications/prompt_lib/399` → `400`,
  body `[{"type": "value_error", "loc": ["versions", 0, "llm_settings"], "msg":
  "Value error, temperature is not allowed together with a reasoning_effort (other
  than 'none') — reasoning models reject a custom temperature"}]`. Console warning at
  `useCreateApplication.jsx:92` carries the same message. User-visible alert shown,
  Save button re-enables, page never navigates away from `/agents/create`.
- **Root-cause hint**: project's default model (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`)
  has `supports_reasoning: true` (confirmed via `GET
  /api/v2/configurations/models/399?include_shared=true`); the create form's default
  `llm_settings` payload appears to still populate a non-null `temperature` together
  with a non-`'none'` `reasoning_effort` for such models, which the backend's pydantic
  validator now rejects.
- **Impact**: Blocks creation of **any** new Agent via the default UI flow while the
  project's default model remains reasoning-capable — this is not narrowly scoped to
  ELITEA-1889. Filed as CRITICAL because it is a total, deterministic block on a core
  entity-creation path, not an isolated cosmetic/edge-case issue.
- **Bundling**: filed strict-per-bug per `.agents/profile.md` § Bug filing; body names
  the originating task ("Found while working #67") per that policy.

## Cleanup

- The Skill created for this run (`elitea-1889-versioned-skill`, id `573`) was deleted
  live via the UI overflow menu (`skill-controls-menu-button` → "SKILL" group →
  `skill-delete-menu-item` → type-to-confirm dialog → Delete). Verified: returned to
  `/skills/all` list, no orphaned skill remains.
- No Agent was ever successfully created, so there is nothing to clean up on that side.

## Blocked Steps

**Steps 2, 3, and 4 of the case are blocked**, and Step 1 is only half-satisfied (the
Skill precondition is met; the Agent-creation half is not), by
[EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524) —
a critical, deterministically-reproducible defect in the default Agent-create payload
that rejects Save with a `400` for any project whose default model is
reasoning-capable. There is currently no existing agent in the project to work around
this with (`/agents/all` confirmed empty), so **no part of Steps 2–4 can be explored
at all** until #524 is fixed. Once it is, this AFS's Test Steps 2–4 and the
"Version selector / open-a-specific-version control" row in Handles Reference need a
fresh exploration pass — this run intentionally does not fabricate handles for UI it
never saw (per `test-case-analysis` § Anti-patterns).
