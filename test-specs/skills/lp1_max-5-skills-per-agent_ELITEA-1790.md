# Test Case: Maximum 5 Skills can be attached to one Agent

## Metadata
- **TMS ID**: ELITEA-1790
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — **REWORK pass (locator-compliance only,
  no re-execution)**. This case was previously automated and merged (PR #48);
  behavior is already proven and is NOT being re-verified here. A
  framework-alignment audit (2026-07-15) found 3 raw non-testid handles in the
  merged implementation, all traceable to the two Concrete-Handles rows below
  that were written as "no `data-testid`" at analysis time — under
  `.agents/role-overrides.md` § Analyst slot, a missing testid is a work item,
  never an accepted permanent handle. Fresh-fetch re-verification (this pass)
  found one of the two is **not actually a fresh testid-needed item**: the
  button's testid (`agent-add-skill-button`) already exists on
  `automation/testids` (draft EliteaUI#540) — it just needs to be *used*,
  not added. The wrapper-span raw handle is replaced by a scoped read off
  that same testid (no new testid). See **Handles Reference — Rework**
  below for the full corrected work order. Original functional finding (no
  defect; limit enforcement is stronger than the case text implies) stands
  unchanged.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills and Agents sections are available in the project.
- At least 6 distinct Skills exist in the project — **only 1 pre-existed**
  (`automated-test-explainer`); 5 more were created fresh in this run (see Test
  Data) to reach 6 total.

## Test Data

### reuse-existing
- Pre-existing Skill `automated-test-explainer` (used as one of the 6 available
  skills; not attached to the test agent in this run — 5 freshly-created skills
  were attached instead, keeping the reused skill's own state/history untouched).

### generate-per-test (in test setup, cleaned up in its own teardown)
- 5 Skills, kebab-case names (client-side Skill-name validation is
  lowercase-letters/digits/hyphens-only — see
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`):
  `elitea-1790-skill-2` (id 182), `elitea-1790-skill-3` (id 183),
  `elitea-1790-skill-4` (id 184), `elitea-1790-skill-5` (id 185),
  `elitea-1790-skill-6` (id 186). Each: description
  `"Test skill N for ELITEA-1790 max-5-skills-per-agent verification."`,
  instructions `"You are test skill N created for ELITEA-1790 verification.
  Respond with SKILLN."` (content not asserted — only that a skill with a saved
  `base` version exists to attach). The case's literal test-data example
  ("Skill 1" .. "Skill 6") is generic prose, not literal names to type — same
  reverse-masking pattern already confirmed for ELITEA-1735/1737/1739/1789.
- Agent name: `elitea-1790-max5skills-agent` (id 4658); description
  `"Agent for ELITEA-1790 max-5-skills-per-agent verification."`; instructions
  left blank (not asserted by this case).

No `generate-shared-with-cleanup` fixture applies — this is a fresh-state flow
(5 skills + 1 agent, all created and torn down within the run; the 6th
pre-existing skill was reused read-only).

## Test Steps
1. Confirm/create 6 distinct Skills in the project.
   - Navigated to `${BASE_URL}/skills/create` 5 times, filling Name
     (`skill-name-input`), Description (`skill-description-input`), and
     Instructions (`skill-instructions-editor-content`, a CodeMirror editor —
     use `press_sequentially`/`type(slowly=true)`, not `fill`) with each skill's
     test data, then clicking Save (`skill-save-button`).
   - **Verify**: each save triggers a "There are unsaved changes. Are you sure
     you want to leave?" nav-blocker dialog — confirm via
     `alert-dialog-confirm-button`. URL settles on `/skills/all/{id}` each time
     (ids 182–186). Combined with the pre-existing `automated-test-explainer`,
     6 skills now exist in the project.
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`) and
   Description (`agent-description-input`) with the Agent test data. Click Save
   (`agent-save-button`).
   - **Verify**: navigates directly to
     `/agents/all/{agent-id}?destTab=configuration&name={name}&viewMode=owner`
     (agent id 4658 in this run) — no nav-blocker dialog for the agent create
     form (consistent with ELITEA-1789's prior finding).
3. On the agent detail page, the **Skills** accordion section is expanded by
   default and shows "0/5 skills added." with an add-skill button (icon-only,
   no `data-testid`; accessible name **"Skill"**, exact — matches the amended
   handle already documented for ELITEA-1735/1789).
4. Attach Skill 1 (`elitea-1790-skill-2`): click the add-skill button → a
   "Search skills..." popper opens listing `Create new` + all 6 skills as
   `role="menuitem"` items → click the skill's menuitem.
   - **Verify**: counter updates "0/5 skills added." → "1/5 skills added.";
     a card renders showing the skill's name + `base` version label. Attachment
     is immediate/auto-saved: `PATCH
     /api/v2/elitea_core/skill/prompt_lib/399/182` → `201 Created` fires; the
     page-level `Save`/`Save As Version` button stays disabled throughout
     (same auto-save behavior documented for ELITEA-1735/1789).
5. Attach Skill 2 (`elitea-1790-skill-3`) the same way.
   - **Verify**: "1/5" → "2/5 skills added."; `PATCH .../skill/prompt_lib/399/183`
     → `201`.
6. Attach Skill 3 (`elitea-1790-skill-4`) the same way.
   - **Verify**: "2/5" → "3/5 skills added."; `PATCH .../skill/prompt_lib/399/184`
     → `201`.
7. Attach Skill 4 (`elitea-1790-skill-5`) the same way.
   - **Verify**: "3/5" → "4/5 skills added."; `PATCH .../skill/prompt_lib/399/185`
     → `201`. Reopening the add-skill popper at this point still lists both
     remaining unattached skills (`elitea-1790-skill-6` and
     `automated-test-explainer`) as selectable menuitems — the limit has not
     yet engaged (4 < 5).
8. Attach Skill 5 (`elitea-1790-skill-6`) the same way — the 5th and last
   allowed attachment.
   - **Verify**: "4/5" → "5/5 skills added."; `PATCH .../skill/prompt_lib/399/186`
     → `201`. **Immediately upon reaching 5/5**, the add-skill button itself
     becomes wrapped in `<span aria-label="Maximum number of skills reached">`
     and the inner `<button>` gets the `disabled` attribute (confirmed via
     `browser_evaluate`: `{ariaLabel: "Maximum number of skills reached",
     buttonDisabled: true}`) — this happens automatically, without any 6th
     attach attempt yet being made.
9. Attempt to attach Skill 6 (case step 8: `automated-test-explainer`, the only
   remaining unattached skill).
   - **Verify — blocked, exceeds the case's own expectation.** A real
     Playwright `click()` targeting the add-skill button (scoped by its
     `aria-label` wrapper) **timed out after 5s** with
     `element is not enabled` — i.e. the control is genuinely disabled at the
     actionability level, not merely showing an error after a successful
     click. No popper opened, no 6th `PATCH` fired (network trace confirms the
     request log stops at id `186`'s `PATCH .../201` — no further skill-attach
     call after it), and "5/5 skills added." plus all 5 attached-skill cards
     remain unchanged. Zero console errors/warnings throughout. This satisfies
     — and exceeds — the case's Pass bar for step 8 ("action is blocked; an
     error message **or disabled state** indicates the limit").
10. Save the Agent with 5 Skills attached (case step 9).
    - **Verify — no explicit Save action needed/available**, same pattern as
      ELITEA-1735/1789: because each attach is auto-saved immediately (step 4
      above), the agent-level `Save` button stays disabled throughout. To
      confirm persistence in lieu of a literal Save click, the agent detail
      page was fully reloaded (`browser_navigate` to the same URL). **Verify**:
      after reload, "5/5 skills added." and all 5 skill cards
      (`elitea-1790-skill-2` through `-skill-6`, each `base` version) persisted
      server-side; the add-skill button is still disabled with the same
      tooltip; zero console errors on reload.

## Expected Results
- 6 distinct Skills exist in the project (1 pre-existing + 5 created).
- Skills 1 through 5 attach to the Agent successfully; the counter increments
  "0/5" → "5/5" and a card renders for each with name + `base` version.
- Once 5/5 is reached, the add-skill control becomes **disabled** (not just
  rejecting on click) with an accessible tooltip explaining why — a 6th skill
  cannot be attached through the UI.
- The Agent persists with exactly 5 Skills attached (auto-saved per-attach,
  confirmed via full page reload — no explicit Save click needed/available).
- No console errors or unexpected failed network requests occur during the
  flow (the one expected 404 seen was a stale skill-detail refetch immediately
  after that skill's own deletion during cleanup — documented artifact, not a
  defect, same as ELITEA-1737/1735/1789).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create/confirm 6 distinct Skills | 6 Skills available to attach | Test Step 1 | 5 skills created via UI + 1 pre-existing = 6 total, confirmed via `skill_api.list_skills()` (id/name-excluding this run's own 5) — **implementer amendment**: the analyst confirmed this via the attach popper listing all 6 during exploration; the implementer used the equivalent `skill_api` list check instead (cheaper, avoids an extra popper-open/close cycle before the flow under test even starts, and is an equally valid confirmation that 6 distinct skills exist) | asserted |
| Step 2: Navigate to Agents, create new Agent | Agent creation form open | Test Step 2 | Agent create form fields fillable, Save navigates to detail page | asserted |
| Steps 3–7: Attach Skills 1–5 one at a time | Each Skill listed as attached; 5/5 after Skill 5 | Test Steps 4–8 | Counter increments 0/5→5/5 exactly once per attach; card + captured `PATCH .../201` per skill (real network-request log via `BasePage.capture_requests_matching()`, matching `request`→`response` events by URL — asserted count == attach index AND status == 201 after each attach); zero console errors asserted after each attach | asserted |
| Step 8: Attempt to attach Skill 6 | Action blocked; error/disabled-state indicates limit reached | Test Step 9 | Add-skill button `disabled=true` + `aria-label="Maximum number of skills reached"`; real Playwright click times out (`element is not enabled`) — asserted via `toBeDisabled()`-equivalent, not a literal click attempt; captured network-request log shows exactly 5 skill-attach PATCH calls total (no 6th, for any skill id) after reaching 5/5; "5/5" unchanged; zero console errors asserted after the blocked attempt | asserted — **exceeds case expectation** (proactive disable, not just click-rejection). **Implementer amendment (post-review, R1)**: the "no popper opens" sub-claim is dropped from this row — the add-skill button is the popper's *only* trigger, so once it is asserted disabled, "does the popper open" is untestable by construction (attempting to open it means clicking the same disabled control, which is exactly the click the AFS says not to attempt). The "no 6th PATCH fires" sub-claim IS now asserted for real, via a captured `page.on("request")`/`page.on("response")` network log (`BasePage.capture_requests_matching()`), not just inferred from UI state. **Implementer amendment (post-review, R2)**: console-error checking (Axis 2) is now genuinely wired in via a `page.on("console", ...)` listener (previously claimed in Axis 2 but not implemented). |
| Step 9: Save the Agent with 5 Skills attached | Agent saves successfully with exactly 5 Skills | Test Step 10 | Agent-level Save button stays disabled (attach already auto-saved); persistence confirmed via full page reload showing "5/5 skills added." + all 5 cards; zero console errors asserted after the reload | asserted — **case-text drift** (reverse-masking): "Save the Agent" describes a generic save gesture the live product doesn't require for this action; asserted via persistence-after-reload instead of a literal Save click, same pattern as ELITEA-1735/1789 |
| Test Data: Skill names "Skill 1".."Skill 6" (literal placeholders) | literal names as written | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1790-skill-N` instead | clarification (reverse-masking, same pattern as ELITEA-1735/1737/1739/1789) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Add-skill button's DOM `disabled` attribute + `aria-label` wrapper text (not just visual/UI appearance) | Confirms the block is a real actionability-level disable, not a CSS-only visual cue that a forced/JS click could bypass — material for a hard (not soft) automation assertion |
| A genuine Playwright `click()` attempt against the disabled control, expecting/observing a timeout | Load-bearing automation gotcha: proves to the implementer that `expect(button).toBeDisabled()` is the correct assertion, and that attempting an actual click as the "attempt to attach Skill 6" step will legitimately time out — the implementer must not treat that timeout as a test failure but as the expected proof of blocking |
| Skill-attach network calls (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) for all 5 attachments, and their absence for the blocked 6th | Confirms attachment is immediate API-level auto-save (don't wait on/assert `agent-save-button` state after attaching) and that the block is enforced client-side before any 6th request is even attempted. **Implementer amendment (post-review, R2)**: response status IS captured and asserted (`201` per attach), not just method+URL — `BasePage.capture_requests_matching()` matches `response` events to `request` events by URL and fills in `status` live. |
| Popper contents at 4/5 (both remaining skills still listed/selectable) vs. at 5/5 (button disabled, popper cannot even open) | Documents the exact transition point — the limit engages strictly at 5, not before. **Implementer note**: this is an analyst-exploration record (manual observation), not separately re-asserted in automation — the automated test asserts the functionally-equivalent and stronger claim (`is_add_skill_button_disabled()` at 5/5, not disabled at 0/5) rather than additionally opening the popper at 4/5, which would add an extra interaction cycle without covering a distinct failure mode. |
| Console messages checked after every attach + after the blocked attempt + after reload | Zero errors throughout the functional flow; the single 404 seen was during cleanup (post-delete stale refetch), not during the case's own steps. **Implementer amendment (post-review, R2)**: genuinely wired in via a `page.on("console", ...)` listener (matching the established `test_skill_tag_filter.py`/`test_skill_export_import.py` pattern — no shared helper exists yet for it, so the inline pattern is reused rather than a new abstraction invented for a single caller), asserted `not console_messages` at all three checkpoints — this row was previously claimed but not implemented, caught at review. |
| Cleanup verification: the 5 created skills and the Agent are actually gone after teardown (not merely that the delete calls didn't raise) | Confirms no orphaned test data leaks past this run. **Implementer amendment (post-review, R2)**: the literal "returns to its exact pre-test state (only `automated-test-explainer` remains)" phrasing was environment-specific and unautomatable in general (the exact pre-existing 6th skill's name/count varies by environment — already generalized in the Step-1 row above); what's actually asserted is the equivalent, environment-independent claim — none of the 5 created skill ids remain in `skill_api.list_skills()`, and the agent id is absent from `agent_api.list_agents()` — checked in a post-`try/finally` step that only runs on the success path (so it can't mask a real failure inside the flow above). Previously claimed but not implemented (no post-cleanup assertion existed at all), caught during this round's full self-audit. |

## Cleanup
Six entities existed transiently in this run: 5 freshly-created Skills and 1
Agent. The 6th skill (`automated-test-explainer`) pre-existed and was **not**
deleted (read-only reuse). All created entities were deleted live in this run;
final skills-list screenshot confirms only `automated-test-explainer` remains.

1. **Delete the Agent first, then the 5 Skills** — teardown-hygiene order
   (delete the thing with attached-state dependencies first), consistent with
   ELITEA-1735/1789.
2. **Agent deletion**: UI overflow menu (`agent-actions-menu-button`) → "AGENT"
   group → "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` → inner `#name` field, type
   `elitea-1790-max5skills-agent`) → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/application/prompt_lib/399/4658` → `204 No Content`.
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`, `AgentAPI.delete_agent(agent_id)` in
   `automation/api/client.py:452`), same as ELITEA-1735/1789.
3. **Skill deletion** (×5, ids 182–186): UI overflow menu
   (`skill-controls-menu-button`) → "SKILL" group → "Delete skill"
   (`skill-delete-menu-item`) → same type-to-confirm dialog (typing each
   skill's own name) → click "Delete". Verified via UI redirect back to
   `/skills/all` after each; the well-known immediate follow-up
   `GET .../skill/prompt_lib/399/{id}` → `404` (stale refetch artifact of the
   redirect) appeared once, as expected, and is not a defect (same as
   ELITEA-1737/1735/1789).
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1227`), once
   per created skill id.
4. **Recommended teardown fixture shape**: function-scoped fixture creating 5
   skills + 1 agent via UI (or the skill/agent API clients directly, to save
   setup time — the case's own assertions only require the skills/agent to
   *exist*, not that they be created via UI), attaching skills 1–5 to the
   agent, yielding all 6 ids, and in its `finally`/post-yield block calling
   `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_id)`
   for each of the 5 created skill ids, each in its own `try/except` (mirrors
   the pattern used in ELITEA-1735/1737/1738/1739/1789). The pre-existing 6th
   skill (whatever it is in a given environment) should be looked up via the
   skills-list API/UI rather than assumed to be `automated-test-explainer` by
   name — that name is this-environment-specific test data, not a guaranteed
   fixture.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill Name field | `getByTestId('skill-name-input')` | — (testid is the only reliable handle; kebab-case validation applies) |
| Skill Description field | `getByTestId('skill-description-input')` | — |
| Skill Instructions editor | `getByTestId('skill-instructions-editor-content')` | CodeMirror inner content — use `press_sequentially`, never `fill` |
| Skill Save button | `getByTestId('skill-save-button')` | — |
| Nav-blocker confirm (fires on Skill-create Save) | `getByTestId('alert-dialog-confirm-button')` | — |
| Agent Name field | `getByTestId('agent-name-input')` | — |
| Agent Description field | `getByTestId('agent-description-input')` | — |
| Agent Save button (create form) | `getByTestId('agent-save-button')` | — |
| Agent detail-page Skills add-skill button (normal AND disabled state — SAME DOM button) | `getByTestId('agent-add-skill-button')` — **`on-automation/testids only (draft EliteaUI#540)`**, not yet on `origin/main` (see Handles Reference — Rework below) | superseded raw handle (pre-rework): `getByRole('button', { name: 'Skill', exact: true })` |
| **Agent detail-page Skills add-skill button (at 5/5, disabled — this case's core assertion)** | Same testid as above, `getByTestId('agent-add-skill-button')` covers both enabled and disabled state; assert `toBeDisabled()` on it | superseded raw handle (pre-rework): `page.locator('[aria-label="Maximum number of skills reached"] button')` / `page.locator('[aria-label="Maximum number of skills reached"]')` for the wrapper — no new testid needed for the wrapper span; see reasoning below |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name (search box placeholder `"Search skills..."`, `getByRole('menuitem', { name: skillName, exact: true })` — **use `exact: true`**, a substring match on `elitea-1790-skill-` will ambiguously match multiple menuitems) | — |
| Skills-added counter text | `getByText(/\d\/5 skills added\./)` | — |
| Attached-skill card name + version | card shows skill name as plain text + `.version-text` span for the version label (see ELITEA-1789 for version-selector interaction specifics, not exercised by this case) | — |
| Agent actions (overflow) menu | `getByTestId('agent-actions-menu-button')` | — |
| Delete-agent menu item | `getByTestId('delete-agent-menuitem')` | — |
| Skill controls (overflow) menu | `getByTestId('skill-controls-menu-button')` | — |
| Delete-skill menu item | `getByTestId('skill-delete-menu-item')` | — |
| Delete-confirmation name field | `getByTestId('delete-confirm-name-input')` scoped to inner `#name` field | shared component, both agent and skill delete flows |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | enabled only once typed name matches |

## Handles Reference — Rework (2026-07-15, locator-compliance pass)

Per `.agents/role-overrides.md` § Analyst slot: this project has NO locator
ladder, only `data-testid`; every handle row below carries a PROVENANCE
column verified with a **fresh fetch** (`cd ../EliteaUI && git fetch origin`
run immediately before the greps, in the same command block).

### Raw handles found in the merged implementation (PR #48) — testid work items

**Correction during this rework pass:** my first grep pass wrongly concluded
`agent-add-skill-button` was `needs-adding` — that grep matched an unrelated
line ("Maximum number of skills reached") at the same line number on both
refs and I stopped there without diffing the rest of the file. A full
repo-wide `git grep` (below) shows the testid **already exists** on
`automation/testids` — added by draft PR **EliteaUI#540** ("test: [EL-1735]
add data-testid hooks for agent-skills attach/mention flow",
`testids/ELITEA-1735-skills-testids`, still `DRAFT` as of 2026-07-15) — and
is genuinely **absent from `origin/main`**. This also matches this agent's
own prior memory note (ELITEA-1789 rework session, same day): "`agent-add-skill-button`
now has a real testid (same draft #540)". Corrected table:

| # | Raw handle (superseded) | Where used | Testid to use | Provenance (verified 2026-07-15, fresh fetch) |
|---|---|---|---|---|
| 1 | `page.get_by_role("button", name="Skill", exact=True)` | Skills-section "+ Skill" add button, enabled state | **`agent-add-skill-button`** | `on-automation/testids only (draft EliteaUI#540)` — NOT a new-testid work item; no `add-data-testid` run needed, just switch the locator to the testid that already exists on the dev server. Blocked from promoting to `main` until #540 merges. |
| 2 | `page.locator('[aria-label="Maximum number of skills reached"] button')` | Same button, disabled state (SAME DOM node as #1 — only the `disabled` prop toggles) | **`agent-add-skill-button`** (same testid — one node, one handle, regardless of disabled state) | same as #1 — same node, same provenance |
| 3 | `page.locator('[aria-label="Maximum number of skills reached"]')` | Wrapper `<span>` used to read the tooltip/aria-label text | *(none proposed — see reasoning below)* | n/a — no testid needed on the wrapper; reasoning below |

**Why one testid covers both button states (#1 and #2).** Source
(`../EliteaUI/src/[fsd]/features/skill/ui/SkillMenu.jsx`) shows a single
`<BaseBtn>` whose only state change between "normal" and "at-limit" is the
`disabled` prop (`disabled={isButtonDisabled}`, where `isButtonDisabled =
disabled || isEntityUnsaved`) — not two components, not a swapped node. On
`automation/testids` (post-#540) the testid sits directly on that `<BaseBtn>`:
`data-testid="agent-add-skill-button"` at line 180, alongside the existing
`disabled={isButtonDisabled}` at line 176 — same node, same testid, both
states. The implementer asserts `toBeDisabled()`/`not toBeDisabled()` on the
*same* located element rather than needing two testids.

**Why the wrapper span (#3) does not need its own testid.** The `aria-label`
lives on MUI's `<Box component="span">` Tooltip wrapper (`SkillMenu.jsx:153,
158`) because MUI wraps disabled buttons in an aria-labelled span — disabled
elements don't fire hover/focus, so the tooltip mechanism moves the
accessible description to the ancestor. Once the button itself carries
`agent-add-skill-button`, the implementer does not need a second testid to
read that text: `page.get_by_test_id("agent-add-skill-button").locator("xpath=..")`
(one hop to the immediate parent `<span>`) yields the wrapper without ever
locating it independently — the testid-located button is still the anchor,
per `.agents/testing.md` § Locator policy's "scoped sub-selector off an
existing field" allowance (`.claude/rules/page-objects.md`). Adding a
second, unused-for-navigation testid purely to assert one attribute would be
exactly the "testid on an element no test uses for locating" pattern the
team's scope rule (role-overrides.md § Every role — locator policy) doesn't
require — the button's testid is the load-bearing handle; the aria-label
text is read off it, not located via a rung of its own. **Documented as a
judgment call, not a hard rule**: if the implementer finds the one-hop
parent traversal awkward in practice (e.g. MUI DOM structure changes), a
second testid on the wrapper span (`agent-skill-limit-tooltip`) is an
acceptable escalation — not required by this AFS.

### Provenance verification — fresh-fetch command output (verbatim)

```
$ cd ../EliteaUI && git fetch origin
   (ran clean; no output — nothing new beyond what was already local)

$ git rev-parse origin/main automation/testids
1707d98c7932173d271815216318f1fe1d9d2b1c
96b4dae933cb899d1bcd05916c4f2fc2d03eb7e1

$ git grep -n "agent-add-skill-button" origin/main
(no output — exit 1, not found on main)

$ git grep -n "agent-add-skill-button" automation/testids
automation/testids:src/[fsd]/features/skill/ui/SkillMenu.jsx:180:              data-testid="agent-add-skill-button"

$ git log automation/testids --oneline -- 'src/[fsd]/features/skill/ui/SkillMenu.jsx' | head -3
916fcc3 test: [EL-1735] add data-testid hooks for agent-skills attach/mention flow
e44a6f9 feat: [EL-5699] custom icon upload for skills (#493)
a1eaf9c feat: [EL-5206] Skills library UI (#350)

$ env -u GITHUB_TOKEN gh pr list --repo EliteaAI/EliteaUI --search "agent-add-skill-button" --state all
540	test: [EL-1735] add data-testid hooks for agent-skills attach/mention flow	testids/ELITEA-1735-skills-testids	DRAFT	2026-07-14T19:16:32Z
```

**Verdict: `on-automation/testids only (draft EliteaUI#540)`.** The testid
already exists on the dev-server-serving integration branch (commit
`916fcc3`, "test: [EL-1735] add data-testid hooks for agent-skills
attach/mention flow") and is exposed by draft PR #540 to `main`
(`testids/ELITEA-1735-skills-testids`, still `DRAFT`). It is genuinely absent
from `origin/main` today. **This means no fresh `add-data-testid` run is
needed for this handle** — the implementer switches the two raw-handle call
sites to `LocatorDescriptor(testid="agent-add-skill-button")` and the value
is already live at `localhost:5173` (which serves ALL of
`automation/testids`, merged or draft, per this project's dual-target
convention). Promoting this case's own test to `main` remains blocked until
PR #540 merges — track that dependency in the closure record, don't
re-derive it.

**Wrapper span (#3) — confirmed no additional testid on either ref**, same
grep pattern applied to the `aria-label` string itself:

```
$ git grep -n "Maximum number of skills reached" origin/main -- src
origin/main:src/[fsd]/features/skill/ui/SkillMenu.jsx:162:      ? 'Maximum number of skills reached'

$ git grep -n "Maximum number of skills reached" automation/testids -- src
automation/testids:src/[fsd]/features/skill/ui/SkillMenu.jsx:162:      ? 'Maximum number of skills reached'
```

Both resolve to the same source line (the `tooltipTitle` ternary) — the
wrapper `<Box component="span">` itself carries no `data-testid` on either
ref, and none is being requested (see reasoning above: read via a one-hop
parent traversal off the button's testid instead).

### `skill-instructions-editor-content` provenance (dependency of `_create_skill` helper)

| Check | Command | Result |
|---|---|---|
| On `origin/main`? | `git grep -n "skill-instructions-editor-content" origin/main -- src` | **No match** (exit 1) — absent from main |
| On `automation/testids`? | `git grep -n "skill-instructions-editor-content" automation/testids -- src` | **Match**: `automation/testids:src/[fsd]/features/skill/ui/skill-details/form/CreateSkillForm.jsx:303: contentTestId="skill-instructions-editor-content"` |

**Verdict: `on-automation/testids only (draft #526)`** — confirmed via fresh
fetch, not assumed. The testid exists today only on the integration branch;
`_create_skill`'s dependency on it remains blocked from promoting to `main`
until EliteaUI PR #526 merges. This is a pre-existing condition (not
introduced by this rework) but is re-confirmed here per the fresh-ground-truth
rule rather than carried forward from a stale prior claim.

## Network Behavior
- `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `201
  Created` — fires once per successful attach, immediately on menuitem click
  (auto-save; no page-level Save needed). Exactly 5 of these fire in this case;
  a 6th attempt produces **zero** additional calls because the control is
  disabled before any request could be issued.
- `GET /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}`
  — refetches the agent's attached-skills list after each attach (drives the
  counter + card re-render); wait for this (or the counter text) rather than a
  fixed timeout.
- `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{agent-id}` →
  `204 No Content` on agent delete.
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `204 No
  Content` on skill delete, followed by one expected stale
  `GET .../skill/prompt_lib/{project}/{skill-id}` → `404` artifact (not a
  defect).

## Known Defects Found During Exploration
None found. The limit-enforcement behavior is correct and, if anything,
better than the case text implies (proactive disable + accessible tooltip,
not merely an on-click rejection).

## Blocked Steps
None — case executed end-to-end, all 9 case steps completed and verified
successfully.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md` — no non-obvious
  framework call needed.
- Page objects: extend `automation/pages/agent_detail_page.py` /
  `automation/pages/agent_form_page.py` for the agent-side interactions and
  `automation/pages/skill_form_page.py` for skill creation — do not duplicate
  existing `fill_form`/`click_save`/locator patterns already present there
  (see `.claude/rules/page-objects.md`).
- Wait strategy: wait on the counter text (`"N/5 skills added."`) after each
  attach, not a fixed timeout or the agent-level Save button state (which
  never becomes enabled in this flow).
- **The "attempt to attach Skill 6" assertion should be `expect(addSkillButton
  ).toBeDisabled()` plus an `aria-label`/tooltip-text check — not a literal
  click-and-expect-error.** A real `.click()` against a genuinely disabled
  Playwright locator will hang/timeout by design; assert the disabled state
  directly instead of attempting the interaction.
- Prefer creating the 5 skills via the existing `skill_api` fixture
  (`SkillAPI` in `automation/api/client.py`) rather than the UI, to keep this
  test's own setup fast and focused on the Agent-Skills-limit behavior itself
  — only the Agent-side attach flow needs to go through the UI/`agent_detail_page`.
- **Rework work order (blocking, this pass)**: `agent-add-skill-button`
  already exists on `automation/testids` (draft EliteaUI#540 — no
  `add-data-testid` run needed for this handle). Replace both raw-handle
  call sites (`get_by_role("button", name="Skill", exact=True)` and
  `[aria-label="Maximum number of skills reached"] button`) with a single
  class-level `LocatorDescriptor(testid="agent-add-skill-button")` field on
  `agent_detail_page.py`, assert `toBeDisabled()`/not on that one field for
  both states. The wrapper-span raw handle
  (`[aria-label="Maximum number of skills reached"]`, used only to read the
  tooltip text) does not get its own testid per the reasoning in Handles
  Reference — Rework above — read the `aria-label` off the testid-located
  button's parent instead. Because `agent-add-skill-button` lives only on
  `automation/testids` today, this test can run and pass locally
  immediately, but **promoting it to `main`-targeted CI is blocked until
  EliteaUI#540 merges** — track that as a promotability dependency, same
  as the pre-existing `skill-instructions-editor-content` dependency below.
  This AFS also depends on `skill-instructions-editor-content` for
  `_create_skill`, which is `on-automation/testids only (draft #526)` — not
  yet promotable to `main` until #526 merges (see provenance table above).
