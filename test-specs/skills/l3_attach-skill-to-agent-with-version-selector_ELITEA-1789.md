# Test Case: Attach a Skill to an Agent and verify it appears with version selector

## Metadata
- **TMS ID**: ELITEA-1789
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: defect-found — isolated, non-blocking. The full functional flow (attach
  skill, version selector present + functional, default version shown, persistence
  after "save") completes and passes. One accessibility/testability gap was found on
  the version-selector control itself: no `data-testid`, no ARIA role/accessible name,
  and `tabIndex=-1` (not keyboard-reachable) — filed as
  github.com/EliteaAI/elitea-testing-public/issues/46 (MINOR). Recommend automating
  the functional flow as a hard assertion (it's 100% reliable) and separately tracking
  the a11y/testid gap; no `expect.soft()` needed since nothing in this case's own
  pass/fail criteria is flaky — the gap is a *handle-quality* issue for automation
  and an accessibility issue for the product, not an intermittent functional failure.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills and Agents sections are available in the project.
- At least one Skill with at least one saved version exists (created fresh in this
  run — see Test Data).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill name: kebab-case, e.g. `elitea-1789-versel-skill` — **must be lowercase
  letters/digits/hyphens only** (same client-side Skill-name validation documented
  for ELITEA-1737/1735 — see
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`). The case's
  literal test-data example (`"Formatter"`) is case-text drift, not a literal value
  to type — same reverse-masking pattern already confirmed for ELITEA-1739/1735.
- Skill description: any non-empty string, e.g. `"Test skill for ELITEA-1789 version
  selector verification."`
- Skill instructions: any non-empty string under the 2500-char limit, e.g. `"You are
  a test skill created for ELITEA-1789 version selector verification. Respond with
  VERSEL."` (content not asserted by this case — only that a skill with a saved
  `base` version exists to attach).
- Agent name: e.g. `elitea-1789-versel-agent`; description and a short generic
  instructions string (agent instructions content is not asserted by this case).

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (1 skill +
1 agent, both created and torn down within the run).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input`),
   Description (`skill-description-input`), and Instructions
   (`skill-instructions-editor-content`, a CodeMirror editor — use
   `press_sequentially`/`type(slowly=true)`, not `fill`) with the Skill test data
   above. Click Save (`skill-save-button`).
   - **Verify**: a "There are unsaved changes. Are you sure you want to leave?"
     nav-blocker dialog appears — confirm via `alert-dialog-confirm-button`. URL
     settles on `/skills/all/{id}`; note the Skill ID (`173` in this run).
2. Navigate to `${BASE_URL}/agents/create`. Fill Name (`agent-name-input`),
   Description (`agent-description-input`), and Instructions
   (`agent-instructions-input`) with the Agent test data. Click Save
   (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`
     (no nav-blocker dialog for the agent create form in this run — only the Skill
     create form triggered one). Note the Agent ID (`4649` in this run).
3. On the agent detail page, the **Skills** accordion section is expanded by
   default and shows "0/5 skills added." with an add-skill button (icon-only, no
   `data-testid`; accessible name **"Skill"**, exact — confirmed live via
   `getByRole('button', { name: 'Skill', exact: true })`, matching the amended
   handle already documented for ELITEA-1735).
   - **Verify**: Skills attachment area is visible (case step 2). Confirmed live.
4. Click the add-skill button. A "Search skills..." popper opens listing
   `Create new`, the newly-created skill, and any other existing skills in the
   project as menuitems.
   - **Verify** (case step 3, partial): popper lists the skill by name.
5. Click the skill's menuitem to attach it.
   - **Verify** (case step 3): the Skills section counter updates immediately
     ("0/5 skills added." → "1/5 skills added.") and a card renders showing the
     skill's name and its version label. **Attachment is immediate/auto-saved via
     API** — confirmed via network trace: `PATCH
     /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `201 Created`
     fires on attach; the page-level `Save`/`Save As Version` button stays disabled
     throughout (same auto-save behavior already documented for ELITEA-1735).
6. Verify the attached Skill card displays a version selector next to the skill
   name (case step 4).
   - **Verify — PASSES, with a handle-quality caveat.** The card shows a
     `span.version-text` containing `"base"` plus a sibling `KeyboardArrowDownIcon`
     (chevron) styled as a dropdown affordance. **A real mouse click directly on
     `.version-text` (or its immediate `.MuiBox-root` wrapper) opens a "Versions"
     popper menu** (header `"Versions"`, menuitem `"base"`) — confirmed live twice.
     **However**, a click resolved via the Playwright accessibility snapshot's ref
     for the "base" text node (i.e. `getByRole`/ARIA-tree-derived locators, which
     is how `browser_click` resolves a `ref=` target) lands on a *different,
     non-interactive ancestor* `<div>` one level up and **silently does nothing** —
     confirmed twice, reproducibly. DOM inspection of the actual clickable wrapper:
     `tabIndex: -1`, `role: null`, `aria-label: null`, `data-testid: null` — plain,
     non-semantic markup with no keyboard path and no ARIA identity. Filed as
     github.com/EliteaAI/elitea-testing-public/issues/46 (see Known Defects).
     **Automation must target `.version-text` by CSS class scoped under the
     specific skill's card** (e.g. ancestor-scoped by the skill's name text), not
     by accessibility role/name — the control has none.
7. Confirm the default selected version in the version selector (case step 5).
   - **Verify**: the `"base"` text is shown pre-selected on the card before any
     interaction, and the opened "Versions" menu's single menuitem (`"base"`) has
     no distinguishing "selected" visual marker beyond being the only entry (only
     one version exists in this run) — consistent with `base` being the
     agent-attachment default. Confirmed live.
8. "Save the Agent" (case step 6) — **no explicit action needed/available.**
   Because attach is auto-saved immediately (step 5 above), the agent-level `Save`
   button remains disabled after attaching the skill and after opening/closing the
   version menu — there is nothing to click. To confirm persistence in lieu of a
   literal Save click, the agent detail page was fully reloaded
   (`browser_navigate` to the same URL).
   - **Verify**: after reload, the Skills section still shows "1/5 skills added."
     and the same card (`elitea-1789-versel-skill` / `base`) — attachment and
     version selection persisted server-side. No console errors, no failed network
     requests on reload. This is case-text drift (reverse-masking), not a defect —
     same pattern already documented for ELITEA-1735's Skills-attachment save
     behavior; assert persistence-after-reload rather than a literal Save-button
     click.

## Handles Reference

| Element | testid / locator | Notes |
|---|---|---|
| Skill Name field | `skill-name-input` | kebab-case validation |
| Skill Description field | `skill-description-input` | |
| Skill Instructions editor | `skill-instructions-editor-content` | CodeMirror; use `press_sequentially` |
| Skill Save button | `skill-save-button` | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | fires on Skill-create Save; did **not** fire on Agent-create Save in this run |
| Agent Name field | `agent-name-input` | |
| Agent Description field | `agent-description-input` | |
| Agent Instructions field | `agent-instructions-input` | |
| Agent Save button | `agent-save-button` (create form) | stays **disabled** on the detail page once a skill is attached — attach is auto-saved, nothing to click |
| Agent add-skill button | no testid; accessible name `getByRole('button', { name: 'Skill', exact: true })` | matches ELITEA-1735's implementer-amended handle |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name (search box placeholder `"Search skills..."`) | |
| **Attached-skill card version selector (this case's core element)** | **no testid, no ARIA role, `tabIndex=-1`** — only reliable handle is CSS class `.version-text` (the `<span>` showing the version name), scoped to the specific skill's card via an ancestor selector on the skill name text | **Do not use an accessibility-tree/role-based locator** — confirmed it silently clicks the wrong ancestor and opens nothing. See Known Defects (issue #46). Recommend filing an `add-data-testid` request, e.g. `agent-skill-version-selector-button`, before automating this interaction cleanly. |
| Versions popper (opened by the version selector) | header text `"Versions"`, menuitem `role="menuitem"` with accessible name = version name (e.g. `"base"`) | the popper itself IS a proper ARIA menu once opened — only the *trigger* lacks semantics |
| Skill card "open in new tab" / "remove skill" buttons | accessible names `"open in new tab"` / `"remove skill"` | icon-only buttons, no testid, but do carry accessible names |
| Agent actions (overflow) menu | `agent-actions-menu-button` | opens VERSION/AGENT grouped menu |
| Delete-agent menu item | `delete-agent-menuitem` | in the AGENT group |
| Skill controls (overflow) menu | `skill-controls-menu-button` | opens VERSION/SKILL grouped menu |
| Delete-skill menu item | `skill-delete-menu-item` | in the SKILL group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | shared component, both agent and skill delete flows |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | enabled only once typed name matches |

## Expected Results
- A Skill with a saved `base` version and an Agent are both created successfully.
- Attaching the skill to the agent shows a card with the skill's name and a version
  label (`base`) plus a dropdown-styled control.
- That control **is** a real, functional version selector — clicking it (via a
  correctly-scoped locator) opens a "Versions" menu showing the current version.
- The default version (`base`) is shown pre-selected.
- Attachment + version selection persist without an explicit agent-level Save
  action (auto-saved via API), confirmed via full page reload.
- No console errors or failed network requests occur during the flow (the one
  console error seen — a `404` on a stale skill-detail refetch immediately after
  the skill's own deletion during cleanup — is an expected artifact of the
  redirect-after-delete pattern, not a defect; documented in prior AFS/memory).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Navigate to Agents, create new Agent | Agent creation form is open | Test Step 2 | Agent create form fields fillable, Save enables once required fields non-empty | covered |
| Step 2: Locate Skills attachment section | Skills attachment area visible | Test Step 3 | Skills accordion expanded by default, shows "0/5 skills added." + add-skill button | covered |
| Step 3: Click to add a Skill, select existing Skill | Selected Skill appears in attached list | Test Steps 4–5 | Popper lists skill by name; card renders with skill name after click; counter updates "0/5"→"1/5" | covered |
| Step 4: Verify attached Skill entry displays version selector | Version selector (dropdown or similar) shown next to Skill name | Test Step 6 | Chevron-icon + "base" text control confirmed clickable (correctly-scoped locator) and opens a real "Versions" menu | covered — **with a handle-quality/accessibility caveat**, see Known Defects |
| Step 5: Confirm default selected version | Default version pre-selected (e.g. `base`) | Test Step 7 | "base" shown on card pre-interaction; sole entry in opened Versions menu | covered |
| Step 6: Save the Agent | Agent saves without errors; Skill remains attached with selected version | Test Step 8 | Agent-level Save button stays disabled (attach already auto-saved); persistence confirmed via full page reload showing "1/5 skills added." + same card | covered — **case-text drift** (reverse-masking): "Save the Agent" describes a generic save gesture the live product doesn't require for this action; asserted via persistence-after-reload instead of a literal Save click |
| Test Data: Skill name example `"Formatter"` | literal skill name as written | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1789-versel-skill` instead | clarification (reverse-masking, same pattern as ELITEA-1735/1739/1737) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is immediate API-level auto-save; material for correct wait strategy (don't wait on/assert `agent-save-button` state after attaching) — consistent with ELITEA-1735 |
| Accessibility-ref click vs. CSS-class click on the version-selector trigger | Load-bearing automation gotcha discovered live: an ARIA-tree/role-based locator resolves to the wrong DOM ancestor and silently no-ops; only a CSS-class-scoped or coordinate click reaches the actual clickable element. Any implementer using `getByRole`/snapshot refs alone will write a test that "passes" without ever actually opening the version menu. |
| DOM attribute inspection of the version-selector wrapper (`tabIndex`, `role`, `aria-label`, `data-testid`) | Confirms the accessibility/testid gap is real and not a one-off snapshot artifact — grounds for filing issue #46 |
| Full page reload to confirm persistence | Since the agent-level Save button is disabled throughout, reload is the only way to independently verify the attach + version selection survived past the immediate in-session state |
| Console messages checked after every step | Zero errors during the functional flow; the single 404 seen was during cleanup (post-delete stale refetch), not during the case's own steps |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/46 — [MINOR] Agent Skills card version-selector control is not keyboard-accessible and has no data-testid
- **Repro rate**: 100% (confirmed twice in this run — both a scripted JS click via
  `browser_evaluate` and a real Playwright click via a correctly-scoped CSS locator
  (`.version-text`) opened the menu; both attempts to click via the accessibility
  snapshot's `ref=` for the same visible text silently failed to open anything).
- **Root-cause hint**: the wrapping element (`div.MuiBox-root` containing
  `span.version-text` + the `KeyboardArrowDownIcon` svg) has `cursor: pointer` in
  its computed style (so it visually invites a click) but carries no `role`, no
  `aria-label`, `tabIndex="-1"`, and no `data-testid`. Its own parent `MuiBox-root`
  (one level further out) has `cursor: default` and is a dead click target — this
  is almost certainly why the accessibility-snapshot's ref-to-locator resolution
  (which walks up to the nearest "meaningfully-boxed" ancestor when a leaf has no
  semantic role) lands on the wrong element.
- **Evidence**: `test-results/screenshots/ELITEA-1789-step4-version-selector-menu.png`
  (Versions menu open, functional-click confirmation); DOM attributes captured via
  `browser_evaluate`: `{tabIndex: -1, role: null, ariaLabel: null, testid: null}`.
- **Impact**: keyboard-only and screen-reader users cannot operate this control at
  all (severity: accessibility, WCAG 2.1.1 keyboard-operability class of issue).
  For automation, any implementation using `getByRole`/accessibility-tree-derived
  locators will silently fail to interact with the real control — must use a
  CSS-class-scoped locator instead (see Handles Reference).
- **Automation guidance**: this does **not** block automating the case — the
  underlying functional behavior (version selector present, functional via mouse,
  shows correct default) is 100% reliable and should be **hard-asserted**. Use
  `.version-text` (scoped to the specific attached skill's card, e.g. via an
  ancestor `has_text` filter on the skill's name) as the click target, not a role
  or testid locator (none exist yet). Track issue #46 for an eventual
  `add-data-testid` + accessibility pass on this specific control.

## Cleanup

Two entities created per run: the Skill and the Agent that attaches it. Both were
deleted live in this run.

1. **Delete the Agent first, then the Skill** — recommended order for teardown
   hygiene (delete the thing with attached-state dependencies first), though per
   ELITEA-1735's prior finding the API doesn't strictly enforce this ordering.
2. **Agent deletion**: UI overflow menu (`agent-actions-menu-button`) → "AGENT"
   group → "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` → inner `#name` field) → click "Delete". Verified:
   `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` →
   `204 No Content`. Redirected to `/skills/all/{last-viewed-skill-id}` in this run
   (not a fixed target — don't assert a specific post-delete URL).
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`, `AgentAPI.delete_agent(agent_id)` in
   `automation/api/client.py:452`), same as ELITEA-1735.
3. **Skill deletion**: UI overflow menu (`skill-controls-menu-button`) → "SKILL"
   group → "Delete skill" (`skill-delete-menu-item`) → same type-to-confirm dialog
   → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}` → `204 No Content`.
   The immediate follow-up `GET .../skill/prompt_lib/{project}/{skill_id}` → `404`
   seen in the network/console log afterward is an expected stale-refetch artifact
   of the redirect, not a defect (same as ELITEA-1737/1735).
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1227`).
4. **Recommended teardown fixture shape**: function-scoped fixture creating the
   skill + agent via UI in the test body, yielding both IDs, and in its
   `finally`/post-yield block calling `agent_api.delete_agent(agent_id)` then
   `skill_api.delete_skill(skill_id)`, each in its own `try/except` (mirrors the
   `clean_skill` pattern used in ELITEA-1735/1737/1738/1739).

## Blocked Steps
None — case executed end-to-end. The version-selector accessibility/testid gap
(issue #46) is a non-blocking, isolated finding; it does not prevent completion of
any case step and does not require `expect.soft()` treatment since the case's own
pass/fail criteria (a version selector is shown, default version is correct, agent
saves/persists with the skill attached) are all satisfied reliably via the correct
(CSS-class-scoped) handle.
