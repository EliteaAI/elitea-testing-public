# Test Case: Remove attached Skill from Agent

## Metadata
- **TMS ID**: ELITEA-1792
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end, all 6 steps pass, no
  defects. One live discovery not mentioned in the case text: removal is gated by a
  "Remove skill?" confirmation dialog (Cancel/Remove) rather than an instant
  removal — this is additive detail, not case-text drift (the case's own
  pass/fail criteria are unaffected either way), so it is not filed as a
  clarification, just documented here for the implementer.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.
- An Agent exists with at least 2 Skills attached — created fresh in this run (see
  Test Data). No pre-existing Agent in the project had exactly this shape, so
  seed-and-cleanup was used rather than reusing existing data (this case's
  observable — removing one of two attachments while confirming the other
  persists and the removed Skill survives standalone — inherently requires a
  disposable Agent+2-Skills fixture; Hard Rule 10 read-only-by-default doesn't
  apply to a mutating case like this one).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill A name: kebab-case, e.g. `elitea-1792-skill-a` — **must be lowercase
  letters/digits/hyphens only** (client-side Skill-name validation documented in
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md` and
  confirmed again live in this run).
- Skill A description: any non-empty string, e.g. `"Test skill A for ELITEA-1792
  remove-attached-skill verification."`
- Skill A instructions: any non-empty string under the 2500-char limit, e.g. `"You
  are Skill A, created for ELITEA-1792 verification. Respond with SKILLA."`
  (content not asserted by this case — only that a skill with a saved `base`
  version exists to attach).
- Skill B name/description/instructions: same shape, `elitea-1792-skill-b` /
  `"Test skill B for ELITEA-1792 remove-attached-skill verification."` /
  `"You are Skill B, created for ELITEA-1792 verification. Respond with SKILLB."`
- Agent name: e.g. `elitea-1792-remove-skill-agent`; description and a short
  generic instructions string (agent instructions content is not asserted by
  this case).
- The case's Test Data table ("Skill A" / "Skill B" as literal names) is
  descriptive shorthand, not literal values to type — same reverse-masking
  pattern already confirmed for ELITEA-1789/1739/1737/1735 (kebab-case-only
  validation on the Name field).

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (2
skills + 1 agent, all created and torn down within the run).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create` twice to create Skill A (fields:
   `skill-name-input`/`skill-description-input` resolve to MUI `FormControl`
   wrapper divs — target the descendant `input`/`textarea`, e.g. via
   `getByRole('textbox', { name: 'Name *' })`/`getByRole('textbox', { name:
   'Description *' })` or the page object's `_fill_text_input` helper; do NOT
   `.fill()` the testid div directly, it throws "Element is not an <input>...")
   and `skill-instructions-editor-content` (CodeMirror — use
   `press_sequentially`/`type(slowly=true)`, not `fill`). Click Save
   (`skill-save-button`); confirm the "There are unsaved changes..." nav-blocker
   dialog via `alert-dialog-confirm-button`. Repeat for Skill B.
   - **Verify**: both skills save successfully; URLs settle on `/skills/all/{id}`
     (Skill A id `253`, Skill B id `254` in this run).
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input` — same
   wrapper-div caveat as above), Description (`agent-description-input`), and
   Instructions (`agent-instructions-input`) with the Agent test data. Click Save
   (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`
     (no nav-blocker dialog for the agent create form — consistent with
     ELITEA-1789). Agent ID `4678` in this run.
3. On the agent detail page, the Skills accordion section is expanded by default,
   shows "0/5 skills added." with an add-skill button (`getByRole('button', {
   name: 'Skill', exact: true })`, no testid — matches the ELITEA-1735/1789
   handle). Click it twice, once per skill, selecting each from the "Search
   skills..." popper's menuitem list to attach both Skill A and Skill B.
   - **Verify** (case Precondition — "Agent exists with at least 2 Skills
     attached"): counter updates "0/5" → "1/5" → "2/5"; two skill cards render,
     `elitea-1792-skill-a` and `elitea-1792-skill-b`, each showing `base` as the
     version. Attachment is auto-saved via `PATCH
     /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `201 Created`
     per skill (same auto-save behavior documented for ELITEA-1735/1789); the
     agent-level `Save` button stays disabled throughout.
4. (Case step 1/2) Confirm both Skills are listed as attached, and locate the
   remove control for Skill B. Each attached-skill card's "open in new tab" /
   "remove skill" icon buttons are **hover-revealed** — not present in the
   accessibility tree until the specific card is hovered (confirmed live: a
   snapshot of an un-hovered card shows only the name+version `generic` nodes;
   hovering that exact card reveals `button "open in new tab"` and `button
   "remove skill"` as siblings). Hover Skill B's card, then locate `button
   "remove skill"` scoped to that card.
   - **Verify** (case step 2): remove control is visible for Skill B once its
     card is hovered. Confirmed live via before/after accessibility snapshot of
     the Skills region.
5. (Case step 3) Click the "remove skill" button on Skill B's card.
   - **Verify — with an additive discovery not in the case text.** Clicking
     "remove skill" does **not** remove the skill instantly; it opens a
     **"Remove skill?" confirmation dialog** — heading "Remove skill?", body
     "Are you sure to remove the elitea-1792-skill-b skill from agent?", buttons
     "Cancel" / "Remove" (same confirmation-dialog pattern as `remove_toolkit()`
     in `automation/pages/agent_detail_page.py:465`, "Remove toolkit?"). Clicking
     "Remove" confirms the removal: the Skills counter updates "2/5 skills
     added." → "1/5 skills added.", Skill B's card disappears, Skill A's card
     remains. Confirmed via network trace: `PATCH
     /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-b-id}` → `200 OK`
     (note: `200`, not `201` — attach uses `201 Created`, detach uses `200 OK`),
     followed by a `GET .../application_skills/prompt_lib/{project}/{agent-id}`
     refetch that resolves the updated (1-skill) list. No console errors during
     this step.
6. (Case step 4) Save the Agent. **No explicit action needed/available** — same
   auto-save pattern as attach (ELITEA-1789): the agent-level `Save` button
   stays **disabled** after the removal (confirmed live: `Save` remains
   `[disabled]` in the post-removal snapshot). To confirm persistence in lieu of
   a literal Save click, the agent detail page was fully reloaded
   (`browser_navigate` to the same URL).
   - **Verify**: after reload, the Skills section shows "1/5 skills added." with
     only Skill A's card (`elitea-1792-skill-a` / `base`) — removal persisted
     server-side. No console errors, no failed network requests on reload. This
     is case-text drift (reverse-masking), not a defect — same pattern already
     documented for ELITEA-1789's Save-button behavior on attach; assert
     persistence-after-reload rather than a literal Save-button click.
7. (Case step 5) Reopen the Agent in edit/view mode (same reload as step 6 above
   satisfies this — case steps 4 and 5 collapse into a single reload+assert in
   the live flow, since there's no separate "close and reopen" gesture needed).
   - **Verify** (case step 5): Agent shows only Skill A attached; Skill B is no
     longer listed. Confirmed via the same post-reload snapshot as step 6.
8. (Case step 6) Navigate to `${BASE_URL}/skills/all/{skill-b-id}` directly, and
   also to `${BASE_URL}/skills/all` (the Skills list).
   - **Verify** (case step 6): Skill B (`elitea-1792-skill-b`, id `254`) still
     resolves — its detail page loads with Name, Description, and Instructions
     intact (i.e. it was NOT deleted, only detached from the agent), and it
     appears in the project's Skills list. Confirmed live via both direct
     detail-page navigation and the Skills list page.

## Handles Reference

| Element | testid / locator | Provenance | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` (wrapper) → target descendant `input` or use `getByRole('textbox', { name: 'Name *' })` | pre-dates provenance column | kebab-case validation; `.fill()` on the testid div itself throws |
| Skill Description field | `skill-description-input` (wrapper) → descendant `textarea` or `getByRole('textbox', { name: 'Description *' })` | pre-dates provenance column | same wrapper-div caveat |
| Skill Instructions editor | `skill-instructions-editor-content` | pre-dates provenance column | CodeMirror; use `press_sequentially`/`type(slowly=true)` |
| Skill Save button | `skill-save-button` | pre-dates provenance column | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | pre-dates provenance column | fires on Skill-create Save; did **not** fire on Agent-create Save |
| Agent Name field | `agent-name-input` | pre-dates provenance column | same wrapper-div fill caveat as Skill Name |
| Agent Description field | `agent-description-input` | pre-dates provenance column | |
| Agent Instructions field | `agent-instructions-input` | pre-dates provenance column | this run used `.fill()` via testid successfully on the Agent Instructions field (single-line MUI `Textarea`, not a wrapper div) — contrast with Skill Name/Description above |
| Agent Save button | `agent-save-button` (create form) | pre-dates provenance column | stays **disabled** on the detail page once a skill is attached/removed — both operations auto-save, nothing to click |
| Agent add-skill button | no testid; `getByRole('button', { name: 'Skill', exact: true })` | pre-dates provenance column | matches ELITEA-1735/1789's amended handle |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name (search box placeholder `"Search skills..."`) | pre-dates provenance column | |
| **Attached-skill card "remove skill" button (this case's core element)** | `skill-card-remove-button`, scoped to the specific skill's card via `SKILL_CARD_REMOVE_BUTTON_SELECTOR` | on-`automation/testids` (commit `fc0c02f`) via draft PR EliteaUI#547, not yet on `main` | **REWORK (2026-07-15):** replaced the prior `getByRole('button', { name: 'remove skill' })` raw handle — testid-only policy violation (team ruling PR #23) — with a `data-testid` added via `add-data-testid`. **Hover-revealed** — not present in the accessibility tree for an un-hovered card; hover the card first (or use a `force` click). Sibling button `"open in new tab"` shares the same reveal-on-hover behavior but is out of scope (no testid added — this test never touches it). |
| **"Remove skill?" confirmation dialog (new discovery, not in case text)** | dialog heading `"Remove skill?"`; buttons `getByRole('button', { name: 'Cancel' })` / `getByRole('button', { name: 'Remove' })` scoped to the dialog | no testid on `DeleteEntityModal.jsx` action buttons (framework-scale change, out of scope for this rework) | Same shape as the existing `remove_toolkit()` "Remove toolkit?" dialog (`automation/pages/agent_detail_page.py:504`, `Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")`) — a `remove_skill()` page-object method should follow the identical click-then-confirm pattern |
| Skill card version selector | `.version-text` CSS class, scoped to the skill's card (see ELITEA-1789 for the accessibility-tree click gotcha, issue #46) | pre-dates provenance column | not this case's target but visible on both cards during exploration |
| Agent actions (overflow) menu | `agent-actions-menu-button` | pre-dates provenance column | opens VERSION/AGENT grouped menu |
| Delete-agent menu item | `delete-agent-menuitem` | pre-dates provenance column | in the AGENT group |
| Skill controls (overflow) menu | `skill-controls-menu-button` | opens VERSION/SKILL grouped menu |
| Delete-skill menu item | `skill-delete-menu-item` | in the SKILL group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | shared component, both agent and skill delete flows |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | enabled only once typed name matches |

## Expected Results
- An Agent with 2 attached Skills (A and B) is created successfully.
- The remove control ("remove skill" icon button) is discoverable for Skill B
  once its card is hovered.
- Clicking it opens a "Remove skill?" confirmation dialog; confirming removes
  Skill B from the agent's attached-Skills list in the UI, while Skill A remains.
- The Agent "saves" (auto-saved via API, no explicit Save-button click required)
  without errors — confirmed via full page reload showing only Skill A attached.
- Skill B continues to exist as a standalone Skill in the project — its detail
  page and the Skills list both still resolve it after removal from the agent.
- No console errors or failed network requests occur during the functional flow
  (the one 404 seen during Skill-B's own final teardown-delete is an expected
  stale-refetch artifact, not a defect — same pattern as ELITEA-1737/1735/1789).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Agent exists with ≥2 Skills attached | Agent edit form open, both Skills listed | Test Steps 1–3 | Skill A + Skill B created; both attached to fresh Agent; counter "2/5 skills added.", both cards render | asserted |
| Step 1: Open Agent in edit mode with Skill A + Skill B attached | Agent edit form open; both Skills listed | Test Step 3 | Both skill cards visible with names + `base` version | asserted |
| Step 2: Locate remove control for Skill B | Remove button/icon visible for Skill B | Test Step 4 | Hover-revealed `button "remove skill"` confirmed present on Skill B's card via before/after snapshot | asserted |
| Step 3: Click remove control for Skill B | Skill B removed from UI list; Skill A remains | Test Step 5 | Counter "2/5"→"1/5"; Skill B card disappears; Skill A card remains; confirmed via `PATCH .../skill-b-id → 200` + `application_skills` refetch | asserted — **with an additive discovery**: a "Remove skill?" confirm dialog gates the removal (not mentioned in case text, but doesn't change the pass/fail outcome — see Metadata) |
| Step 4: Save the Agent | Agent saves without errors | Test Step 6 | Save button stays disabled (removal already auto-saved); persistence confirmed via full page reload | asserted — **case-text drift** (reverse-masking): "Save the Agent" describes a generic save gesture the live product doesn't require here; asserted via persistence-after-reload instead of a literal Save click, same pattern as ELITEA-1789 |
| Step 5: Reopen Agent in edit/view mode | Only Skill A attached; Skill B no longer listed | Test Step 7 (same reload as Step 6) | Post-reload snapshot: "1/5 skills added.", only Skill A's card present | asserted |
| Step 6: Navigate to Skills section, verify Skill B still exists | Skill B present in Skills list, not deleted | Test Step 8 | Direct navigation to `/skills/all/254` resolves full skill detail (name/description/instructions intact); Skill B also visible in `/skills/all` list | asserted |
| Test Data: "Skill A" / "Skill B" as literal names | literal names as written | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1792-skill-a`/`-b` instead | clarification (reverse-masking, same pattern as ELITEA-1789/1739/1737/1735) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-detach network call (`PATCH .../skill/prompt_lib/{project}/{skill-id}` → `200 OK`, contrast with attach's `201 Created`) | Confirms detach is a distinct auto-save operation from attach at the API level; material for correct wait strategy after clicking Remove |
| Existence of the "Remove skill?" confirmation dialog | Load-bearing automation gotcha discovered live: a naive `remove_skill()` implementation that clicks the icon button and immediately asserts the counter would fail, since a confirmation click is required first. Documented so the implementer builds the two-click flow (icon → dialog Remove) from the start, mirroring the existing `remove_toolkit()` pattern. |
| Hover-reveal behavior of the "open in new tab"/"remove skill" icon buttons | These buttons are absent from the accessibility tree for an unhovered card — an implementer relying on a bare `get_by_role` without first hovering (or without Playwright's auto-hover-on-click behavior) could get a "not found" flake depending on framework/click-implementation details. Documented explicitly so the `remove_skill()` page-object method hovers the card before locating the button. |
| Console messages checked after every step | Zero errors during the functional flow; the one 404 seen was during Skill B's own final teardown-delete (post-delete stale refetch), not during the case's own steps |
| Skill B's full detail (name/description/instructions) re-verified intact post-removal, not just its existence | Confirms detachment from the agent has zero side effect on the Skill entity itself — stronger evidence than "the list contains the name" alone |

## Known Defects
None. No product defects found. The confirmation-dialog discovery (§ Test Step 5)
is documented as an additive finding, not a defect — it doesn't violate any of
the case's own pass/fail criteria.

## Cleanup

Three entities created per run: two Skills and the Agent that attaches them. All
three were deleted live in this run.

1. **Delete the Agent first, then the Skills** — recommended teardown order
   (delete the thing with attached-state dependencies first), consistent with
   ELITEA-1735/1789's prior finding that the API doesn't strictly enforce this
   ordering.
2. **Agent deletion**: UI overflow menu (`agent-actions-menu-button`) → "AGENT"
   group → "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` → inner `#name` field) → click "Delete". Verified:
   `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` →
   `204 No Content`.
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`, `AgentAPI.delete_agent(agent_id)` in
   `automation/api/client.py:452`), same as ELITEA-1735/1789.
3. **Skill deletion (both A and B)**: UI overflow menu
   (`skill-controls-menu-button`) → "SKILL" group → "Delete skill"
   (`skill-delete-menu-item`) → same type-to-confirm dialog → click "Delete".
   Verified for both: `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}`
   → `204 No Content`. The immediate follow-up `GET .../skill/prompt_lib/{project}/{skill_id}`
   → `404` seen in the console afterward is an expected stale-refetch artifact of
   the redirect, not a defect (same as ELITEA-1737/1735/1789).
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1227`).
4. **Recommended teardown fixture shape**: function-scoped fixture creating two
   skills + one agent via UI in the test body (attaching both skills to the
   agent), yielding all three IDs, and in its `finally`/post-yield block calling
   `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_a_id)`
   and `skill_api.delete_skill(skill_b_id)`, each in its own `try/except`
   (mirrors the pattern used in ELITEA-1735/1737/1738/1739/1789).

## Blocked Steps
None — case executed end-to-end, all 6 case steps confirmed live, no blockers.
