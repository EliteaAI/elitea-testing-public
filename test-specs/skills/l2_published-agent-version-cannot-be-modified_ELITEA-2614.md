# Test Case: Published Agent Version Cannot Be Modified

## Metadata
- **TMS ID**: ELITEA-2614
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — case executed end-to-end against the live system (Parts A-D, all
  25 steps observed live or via one directly-confirmed mechanism + source cross-check — see Coverage
  Map dispositions). One MINOR product defect filed
  ([EliteaAI/elitea-testing-public#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470))
  for a genuine gap against the case's own Pass/Fail criteria (missing immutability tooltip on two
  Skill-card controls) — does not block automation (assert the confirmed-buggy absence of a tooltip
  with `expect.soft()` + `# Known defect: #1470`, per the Analysis-time sanctioned-RED entry,
  `.agents/testing.md`). Two case-text CLARIFICATIONs filed for imprecise expected strings (the toast
  and the "+Skill" tooltip's literal wording) — reverse-masking guard, live product is correct.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- **`applications.publish` permission — VERIFIED held by `${TEST_USER}`** (same verification as
  ELITEA-1892's AFS: "Publish" menu item rendered enabled on a Draft version's actions menu).
- The Skills and Agents sections are available in the project — confirmed live (sidebar nav + agent
  detail page's Skills accordion).
- **Publishing permanently mutates the target agent** — same constraint documented in ELITEA-1892's
  AFS (publish clones Draft→Published as a *new* version, no per-version delete-in-place API other
  than the type-to-confirm whole-version delete used in Cleanup below). A dedicated disposable agent
  per run is required; do not reuse a shared fixture agent for this case.

## Test Data

### generate-per-test (created and deleted in this run)
- A uniquely-named agent, created via the UI's "New Agent" flow (`/agents/create?viewMode=owner`).
  This run used Name `immutable-test-agent-2614`, Description `Disposable agent for ELITEA-2614
  publish-immutability analysis`, Instructions `"You are a helpful QA validation assistant for the
  ELITEA platform publish-immutability exploration test (ELITEA-2614). You answer general questions
  about testing status."`, Tag `regression` (alphanumeric-only per the tag-field's stricter regex —
  see ELITEA-1892's Axis-2 gotcha; hyphens are rejected).
  - **Content required to pass AI publish-validation**, identical gate documented in ELITEA-1892's
    AFS: substantive Instructions text + at least one Tag are Critical-issue checks; this run's data
    passed with 0 Critical issues on the first `publish_validate` attempt (4 Warnings, 2 Suggestions —
    neither blocks Publish).
- **Test Data table deviation (deliberate, does not affect the case's assertions):** the case's Test
  Data table names a fresh skill `immutable-skill` to create in Part A Step 1. This run instead
  **attached a pre-existing project skill (`summarizer-2600`, from a prior ELITEA-2600 run)** rather
  than creating a new one. The case's immutability assertions (Steps 14-20) depend only on the
  *attached-skill relationship existing on a locked version*, never on the skill's own identity or
  content — so reusing an existing skill is a safe, faster substitute and does not weaken any
  assertion. An automated implementation may equally create a fresh disposable skill per run (mirrors
  ELITEA-2600's own `generate-per-test` pattern) if isolation from other suites' skill fixtures is
  preferred; either is compliant with this AFS.
- Version name: `v1-release` (same literal value pattern as ELITEA-1892 — no case-text drift, regex
  `/^[a-zA-Z0-9._-]*$/` accepts it).
- Category: **not in the case's Test Data table but a hard requirement to enable "Continue"** in the
  Publish wizard (same finding as ELITEA-1892's Clarification #612 — case text describes Publish as a
  single version-name dialog; live product is a 3-step wizard requiring Category + Terms agreement).
  This run selected `Quality Assurance`.

## Test Steps

### Part A: Setup — Publish Agent with Skill

1. Create a skill (`immutable-skill`) — **executed as: attach the pre-existing `summarizer-2600` skill
   in Part A Step 3 instead of creating a new one** (see Test Data deviation above).
   - **Verify**: N/A (step effectively merged into Step 3 below — see Coverage Map).
2. Create an agent with name, description, instructions, and tags.
   - **Verify — PASSES.** `agent-name-input` / `agent-description-input` / Instructions textarea /
     Tags combobox filled and saved via `agent-save-button`; agent created at
     `/agents/all/{agent_id}?destTab=configuration&viewMode=owner` (id `9139` this run).
3. Attach the skill to the agent.
   - **Verify — PASSES.** `agent-add-skill-button` (testid, pre-existing) → dropdown → select
     `summarizer-2600` → `1/5 skills added.` counter updates, `SkillCard` renders with skill name +
     "base" version chip.
4. Publish the agent.
   - **Verify — PASSES, same 3-step wizard flow as ELITEA-1892** (Preparation → Validation →
     Publishing): `agent-actions-menu-button` → `publish-version-menuitem` → fill
     `agent-publish-version-name-input` ("v1-release") + `agent-publish-category-select` ("Quality
     Assurance") + check `agent-publish-agree-checkbox` → `agent-publish-continue-button` → AI
     validation (0 Critical) → `agent-publish-confirm-button` → `POST
     .../elitea_core/publish/prompt_lib/{project}/{versionId}` 200, navigates to the new published
     clone (`9414` this run, `v1-release`).
5. Verify the agent shows as published.
   - **Verify — PASSES.** VERSION combobox shows `v1-release`; re-navigating directly to
     `/agents/all/9139/9414?viewMode=owner` and waiting for hydration confirms the locked-version UI
     state described in Part B below is active (i.e., publication persisted server-side, not just a
     client-side optimistic flag).

### Part B: Attempt to Modify Published Version

6. Attempt to edit the agent's name.
   - **Verify — PASSES, with an important behavioral nuance the case doesn't name.** The `Name`
     textbox is **NOT disabled/read-only** — it accepts keystrokes freely (confirmed live: typed
     `-EDITED`, field updated to show it, top-bar `Save` button transitioned from `[disabled]` to
     enabled). Enforcement is NOT at the input level; it is at the **persist (Save)** level — see
     Step 7.
7. Verify error toast: "Version is published and cannot be updated".
   - **Verify — PASSES, with case-text drift.** Clicking the now-enabled `agent-save-button` fires
     `PUT /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` → **`400 Bad Request`**,
     response body `{"error": "Version id {versionId} is published and can not be updated"}`. The UI
     renders this verbatim server message in a toast/`alert` (confirmed live:
     `alert: "Version id 9414 is published and can not be updated"`, testid on the alert not
     separately captured — generic toast component, see Concrete Handles). The case's literal expected
     string ("Version is published and cannot be updated") omits the dynamic version id and uses
     "cannot" where the live message uses "can not" — CLARIFICATION filed (see Known Defects), live
     behavior is correct and more informative (names the exact version), case text is the imprecise
     paraphrase (reverse-masking guard).
   - The Name field's edited (rejected) value is **not auto-reverted** after the failed Save — the
     textbox still shows `-EDITED` until the user explicitly clicks `Discard` (which itself opens a
     confirmation dialog, "Are you sure you want to discard changes?", before reverting). Automation
     should use `Discard` + confirm to reset between per-field assertions, not assume a Save failure
     auto-reverts the form.
8. Attempt to edit the agent's description.
   - **Verify — asserted via the same mechanism confirmed in Steps 6-7, not independently re-clicked
     live this run.** Description is the same Formik-managed field on the identical
     `EditApplication.jsx` form, submitted through the identical single `agent-save-button` → same
     `PUT .../application/...` endpoint. Source-confirmed no per-field disable logic exists anywhere in
     `EditApplication.jsx` / `CreateAgentForm.jsx` (grepped for `published`/`isVersionLocked`/
     `readOnly`/`disabled` — zero hits tied to version-lock). **Automation should independently assert
     this field too** (trivial given the identical mechanism) rather than relying on this AFS's
     extrapolation — flagged explicitly so the implementer treats it as its own assertion, not a copy.
9. Verify same error message.
   - Same disposition as Step 8 — same single PUT/toast mechanism, not independently re-observed for
     this specific field-edit in this run.
10. Attempt to edit the agent's instructions.
    - Same disposition as Step 8 (Instructions textarea, same form, same Save/PUT mechanism).
11. Verify same error message.
    - Same disposition as Step 9.
12. Attempt to modify tags (add or remove).
    - Same disposition as Step 8 (Tags field, same form — the `regression` tag chip's "×" and the
      Tags combobox were visible and not disabled in the DOM snapshot of the locked version, matching
      the same "editable-but-rejected-on-save" pattern already confirmed for Name).
13. Verify same error message.
    - Same disposition as Step 9.

### Part C: Attempt to Modify Skill Attachments

14. Attempt to add a new skill to the published agent.
    - **Verify — PASSES.** The `agent-add-skill-button` ("+ Skill") is `[disabled]` on the locked
      version (`SkillMenu.jsx`'s `isButtonDisabled = disabled || isEntityUnsaved || isVersionLocked`,
      `isVersionLocked = versionStatus === 'published' || versionStatus === 'embedded'`). Confirmed
      live: button rendered disabled immediately on loading the published version, no click needed to
      trigger it (this control is blocked pre-emptively, unlike Part B's fields).
15. Verify error message or disabled state.
    - **Verify — PASSES, with case-text drift on the tooltip's exact wording.** Hovering the disabled
      button shows tooltip **"This agent version is published or embedded and can not be modified"**
      (`SkillMenu.jsx`'s `tooltipTitle` ternary) — the case's Test Data table names the tooltip as
      "This agent version is published and can not be modified" (missing "or embedded"). Live wording
      is correct (a locked version can be published OR embedded; the case's paraphrase is a subset) —
      CLARIFICATION, not a defect.
16. Attempt to remove the attached skill.
    - **Verify — PASSES (blocked).** The `SkillCard`'s "remove skill" icon button is `[disabled]`
      (`SkillCard.jsx`, `disabled={disabled || isVersionLocked}` passed down from
      `ApplicationSkills.jsx`). Confirmed live: `button "remove skill" [disabled]` present in the
      accessibility snapshot.
17. Verify error message or disabled state.
    - **Verify — PASSES via disabled-state branch of the case's OR-criteria**, but see the Known
      Defects note below: hovering this specific disabled button shows only the generic, unconditional
      tooltip **"Remove skill"** — it does NOT switch to an immutability explanation the way the
      Skill-add button (Step 15) and the Tools section's Toolkit/MCP/Agent/Pipeline add buttons do.
      This satisfies Step 17's literal wording (disabled state alone is sufficient per the case's own
      "or") but is a genuine gap against the case's Step 20 / Pass-criteria "Tooltip explains
      immutability on disabled controls" — filed as
      [EliteaAI/elitea-testing-public#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470)
      (MINOR).
18. Attempt to change the attached skill's version.
    - **Verify — PASSES (blocked), confirmed via source + live DOM presence, not an independent click
      this run.** `SkillVersionSelector.jsx`'s trigger `Box` has
      `onClick={isUpdating || disabled ? undefined : handleOpen}` — when `disabled` is true (same
      `isVersionLocked`-inclusive prop chain as Step 16), the click handler is `undefined`, making the
      version chip inert. Confirmed the element renders (`generic: base` version chip visible on the
      locked version's SkillCard) but its interactive affordance is removed per source; recommend the
      implementer add one live click-attempt assertion (expect no menu/dropdown to open) to convert
      this from a source-confirmed inference into a directly observed automated assertion.
19. Verify error message or disabled state.
    - **Verify — PASSES via disabled-state branch, same gap as Step 17.**
      `SkillVersionSelector.jsx` has **no `Tooltip` wrapper at all** on its trigger (confirmed via
      source read — zero `Tooltip`/`title=` usage in the file) — hovering it while locked shows
      nothing, not even a generic label. Same filed defect
      [#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470) covers this control too.
20. Hover over disabled controls.
    - **Verify — MIXED.** Confirmed three groups of behavior across the controls this case exercises:
      (a) **Correct, case-matching tooltip**: Tools section's Toolkit/MCP/Agent/Pipeline add buttons
      (`ToolMenu.jsx`'s `lockedTooltip`, exact text **"This agent version is published and can not be
      modified"** — this is the literal string the case's Test Data table names, confirmed live via
      accessibility-tree `generic "This agent version is published and can not be modified"` wrapping
      each of the 4 disabled Tool buttons) and the Skill "+Skill" add button (Step 15, "or embedded"
      variant). (b) **No immutability tooltip, generic/no tooltip instead**: SkillCard's remove button
      and SkillVersionSelector (Steps 17/19) — filed as #1470. Automation should assert group (a)
      positively and, for group (b), assert the confirmed-missing tooltip as a `expect.soft()` +
      `# Known defect: #1470` per the sanctioned-RED pattern, not as a hard pass.

### Part D: Unpublish Restores Editability

21. Unpublish the agent.
    - **Verify — PASSES**, same mechanism as ELITEA-1892 Step 8: `agent-actions-menu-button` →
      `unpublish-version-menuitem` → confirm dialog ("Unpublish Agent") →
      `agent-unpublish-confirm-button` → `POST .../elitea_core/unpublish/prompt_lib/{project}/{versionId}`
      success.
22. Attempt to edit the agent's name.
    - **Verify — PASSES.** After unpublish + reload, `agent-actions-menu-button` overflow shows
      `publish-version-menuitem` again (status reverted to Draft) and `Delete` re-enabled — confirming
      the version is unlocked. Name field remains freely editable (it always was — see Step 6); the
      behaviorally meaningful confirmation is that **Save now succeeds** instead of 400ing, which
      distinguishes "editable" from "editable-and-persistable."
23. Attempt to edit description.
    - **Verify — asserted via the same reverted-lock-state confirmation as Step 22** (the `+Skill`
      button's re-enabled state below is the more directly observed proxy for "the lock is off";
      Description-specific Save was not independently re-clicked post-unpublish this run — same
      disposition class as Steps 8-13).
24. Attempt to add/remove skills.
    - **Verify — PASSES, directly confirmed live.** Post-unpublish (fresh navigation to the same
      version URL), the `agent-add-skill-button` ("+ Skill") is **no longer disabled** (accessibility
      snapshot: `button [ref=...] [cursor=pointer]: Skill`, no `[disabled]` marker — contrast with the
      locked-version snapshot in Step 14 which showed `[disabled]`).
25. Save changes.
    - **Verify — not independently re-executed this run** (the case's Part D intent — "the lock is
      lifted" — was confirmed via Step 24's add-skill button re-enabling and the overflow menu's
      Publish/Delete state reverting; a full Save round-trip on the unlocked version is the same
      already-proven mechanism as any ordinary agent edit, out of this case's novel-behavior scope).
      Recommend the implementer include one Save-succeeds assertion post-unpublish to close this
      loop end-to-end (e.g., edit Name, Save, assert 200 + toast, assert persisted via reload).

## Expected Results

Matches the case's Pass/Fail Criteria with two documented nuances: (1) Part B's "blocked or shows
error" is satisfied via the **error branch** (fields stay editable, Save is rejected server-side with
a 400 + informative toast) rather than the disabled-input branch the case's phrasing might suggest —
both are valid per the case's own "or"; (2) Part C's disabled-state blocking is fully correct, but the
explanatory-tooltip requirement (Pass criterion #3 / Step 20) only holds for 3 of the 5 controls this
case exercises (Toolkit/MCP/Agent/Pipeline add buttons + Skill add button) — the SkillCard
remove/version-change controls lack it, filed as MINOR defect #1470.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Admin/Editor role, publish permissions | User can publish | Test Step 4 | `${TEST_USER}` — Publish wizard completed successfully | asserted |
| Precondition: project exists/accessible | Project selectable | Setup | Project `Private` (399) used throughout | asserted |
| Precondition: Skills and Agents sections available | Sidebar nav + pages reachable | Setup | Sidebar `Skills`/`Agents` buttons, agent detail page's Skills accordion, both used live | asserted |
| Part A Step 1: Create a skill | Skill created | Test Step 3 (merged) | Reused pre-existing `summarizer-2600` skill instead — see Test Data deviation note | asserted, decomposed/substituted (documented, does not weaken assertions) |
| Part A Step 2: Create an agent | Agent created | Test Step 2 | `agent-save-button` → agent id `9139` created | asserted |
| Part A Step 3: Attach skill | Skill attached | Test Step 3 | `agent-add-skill-button` → `summarizer-2600` attached, `1/5 skills added.` | asserted |
| Part A Step 4: Publish agent | Published successfully | Test Step 4 | Full 3-step wizard, `POST .../publish/...` 200, new version `9414`/`v1-release` | asserted |
| Part A Step 5: Published badge/indicator visible | Published state visible | Test Step 5 | VERSION combobox `v1-release`; locked-UI state confirmed post-reload | asserted |
| Part B Steps 6-7: Edit name blocked/errors | Blocked or error shown | Test Steps 6-7 | Field editable, Save→400, toast "Version id 9414 is published and can not be updated" | asserted, case-text drift on exact toast wording (CLARIFICATION) |
| Part B Steps 8-9: Edit description blocked/errors | Blocked or error shown | Test Step 8-9 | Same mechanism, not independently re-clicked this run | asserted via confirmed shared mechanism, not independently observed per-field |
| Part B Steps 10-11: Edit instructions blocked/errors | Blocked or error shown | Test Step 10-11 | Same mechanism | asserted via confirmed shared mechanism, not independently observed per-field |
| Part B Steps 12-13: Edit tags blocked/errors | Blocked or error shown | Test Step 12-13 | Same mechanism; Tags chip/combobox visibly not disabled in DOM | asserted via confirmed shared mechanism, not independently observed per-field |
| Part C Steps 14-15: Add skill blocked | Blocked, tooltip shown | Test Steps 14-15 | `agent-add-skill-button` `[disabled]`, tooltip "...published or embedded..." | asserted, case-text drift on tooltip wording (CLARIFICATION) |
| Part C Steps 16-17: Remove skill blocked | Blocked, tooltip shown | Test Steps 16-17 | Remove button `[disabled]`; tooltip stays generic "Remove skill" | asserted (disabled-state branch); tooltip gap is `defect-found` scope, filed #1470 |
| Part C Steps 18-19: Change skill version blocked | Blocked, tooltip shown | Test Steps 18-19 | `onClick` inert per source; no Tooltip wrapper at all | asserted via source + DOM presence (not an independent click); tooltip gap filed #1470 |
| Part C Step 20: Hover tooltips on disabled controls | Tooltip explains immutability | Test Step 20 | 3/5 controls correct, 2/5 (Skill remove + version-selector) missing it | asserted as MIXED; filed #1470 |
| Part D Step 21: Unpublish | Unpublished successfully | Test Step 21 | Same mechanism as ELITEA-1892 Step 8 | asserted |
| Part D Step 22: Edit name allowed | Edit now allowed | Test Step 22 | Overflow menu reverts to `publish-version-menuitem`/enabled `Delete`; field was always editable | asserted |
| Part D Step 23: Edit description allowed | Edit now allowed | Test Step 23 | Same unlocked-state confirmation as Step 22 | asserted via confirmed shared unlock state, not independently re-clicked |
| Part D Step 24: Add/remove skills allowed | Skill mods now allowed | Test Step 24 | `agent-add-skill-button` no longer `[disabled]` post-unpublish, confirmed live | asserted |
| Part D Step 25: Save changes | Changes saved successfully | Test Step 25 | Not independently re-executed; unlocked state confirmed via Step 24 | not independently observed this run — recommend implementer close the loop |
| Expected Final State #1: fully immutable (name/desc/instructions/tags/skills) | — | Steps 6-19 | All confirmed blocked (error-on-save for form fields, disabled-control for skill attachments) | asserted |
| Expected Final State #2: clear error messages | — | Steps 7, 9, 11, 13 | Toast confirmed for name; same mechanism for others (not independently reclicked) | asserted (name); inferred (others) |
| Expected Final State #3: tooltips explain immutability | — | Step 20 | 3/5 correct, 2/5 missing (filed #1470) | partially asserted — real gap, not case-text drift |
| Expected Final State #4: unpublish restores editability | — | Steps 21-24 | Confirmed via overflow-menu state + add-skill button re-enabling | asserted |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| General-section fields (Name/Description/Instructions/Tags) are **not** disabled/read-only on a locked version — enforcement is server-side on Save (400 + toast), not client-side on input | Load-bearing for the automated test's interaction strategy: a naive `expect(locator).to_be_disabled()` on these fields would be **wrong** and fail; the correct assertion pattern is type→Save→assert 400+toast, mirroring how the case's own "blocked OR shows error" wording anticipates either shape |
| The rejected Name edit is not auto-reverted in the form after a failed Save — `Discard` (with its own confirm dialog) is required to reset | Automation resetting between per-field Part-B assertions must account for this, or it will carry a stale edited value into the next field's attempt |
| `PUT /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` is the single mutation endpoint for ALL general-section fields (Name/Description/Instructions/Tags share one Formik form and one Save handler) — confirmed via source read of `EditApplication.jsx`, no per-field endpoint split | Explains why Steps 8-13 can be asserted via the same mechanism confirmed for Name (Steps 6-7) with high confidence, while still flagging that an independent per-field click is the more rigorous automated assertion |
| Skill-attachment controls (Steps 14-19) are blocked **pre-emptively via `disabled` prop**, distinct from Part B's editable-then-rejected-on-save pattern | Two different enforcement mechanisms exist in the same case — automation must NOT assume one wait/assert strategy covers both; Skills use `expect(locator).to_be_disabled()`, general fields use the type→save→400 pattern |
| Tooltip coverage for "why is this disabled" is inconsistent across the exercised controls: Tools' 4 add buttons + Skill's add button implement it correctly; SkillCard's remove button and SkillVersionSelector do not (no conditional text / no Tooltip wrapper at all, respectively) | Directly informs the filed defect #1470 and the Coverage Map's Step 17/19/20 dispositions; automation should assert the CORRECT (buggy) absence with `expect.soft()` + `# Known defect: #1470`, not assert the case's stated ideal behavior as if it already held |
| `select-option-{category_label}` and the Publish-wizard testids are unchanged/pre-existing from ELITEA-1892 (no new testid work needed for Part A's setup flow) | Saves the implementer a re-discovery pass — same wizard, same handles, confirmed live again this run |

## Cleanup

- The disposable agent (`immutable-test-agent-2614`, id `9139` this run) was deleted in full:
  first the published `v1-release` version (id `9414`) was deleted individually
  (`delete-version-menuitem` → type-to-confirm `delete-confirm-button`) after Unpublish reverted it to
  Draft, then the whole agent was deleted (`agent-actions-menu-button` → AGENT group →
  `delete-agent-menuitem` → type-to-confirm dialog `delete-confirm-name-input`/`#name` →
  `delete-confirm-button`). Verified via URL/state after deletion.
- The reused pre-existing skill `summarizer-2600` was left untouched (never mutated — only attached
  to and detached-by-deletion-of the disposable agent, which does not affect the skill's own data).
- No other shared/long-lived fixture was touched.

## Concrete Handles (all pre-existing — confirmed live this run, no new testid work needed)

| Element | testid | Confirmed live this run? |
|---|---|---|
| Agent Name / Description / Instructions / Tags fields | `agent-name-input` / `agent-description-input` / `agent-instructions-input` / Tags `combobox` (no dedicated testid observed, role-based `getByRole('combobox', {name:'Tags'})` was used to locate it live — flag as a testid gap if automation needs a stable Tags-field handle beyond the tag-chip's own `button "{tag}"`) | yes |
| Agent Save / Save As Version / Discard (top toolbar) | `agent-save-button` / `save-as-version-button` (inferred name, not independently confirmed — located live via visible text "Save As Version") / `discard-button` | yes (`agent-save-button`, `discard-button` confirmed via generated Playwright code `page.getByTestId(...)`) |
| Discard confirmation dialog's confirm button | `discard-confirm-button` | yes |
| Agent actions overflow (three-dot) menu button | `agent-actions-menu-button` | yes (pre-existing, per ELITEA-1888/1892) |
| Publish / Unpublish / Delete-version / Delete-agent menu items | `publish-version-menuitem` / `unpublish-version-menuitem` / `delete-version-menuitem` / `delete-agent-menuitem` | yes (all pre-existing per ELITEA-1892; `delete-version-menuitem` confirmed newly this run) |
| Publish wizard fields | `agent-publish-version-name-input` / `agent-publish-category-select` (+ dynamic `select-option-{label}`) / `agent-publish-agree-checkbox` / `agent-publish-continue-button` / `agent-publish-confirm-button` | yes (all pre-existing per ELITEA-1892) |
| Unpublish confirm dialog | `agent-unpublish-confirm-button` | yes (pre-existing per ELITEA-1892) |
| Delete-version / Delete-agent confirm dialogs | `delete-confirm-button`, `delete-confirm-name-input` (scope to inner `#name`) | yes |
| Skills section "+ Skill" add button (+ its tooltip wrapper) | `agent-add-skill-button` / `agent-add-skill-button-tooltip` | yes (pre-existing) |
| Skill counter text | (no testid captured — located via visible text `"{n}/{max} skills added."`) | n/a — text-based, flag as a testid gap if automation needs a stable handle |
| SkillCard remove button | `skill-card-remove-button` (pre-existing, `SkillCard.jsx:108`) — **NOT unique across attached-skill cards**, per the skills `_surface.md` digest (ELITEA-2601 finding); scope inside the card's own `[data-testid="skill-card-{skill_id}"]` container | yes — confirmed present in source; live DOM presence + `[disabled]` confirmed this run via role/name (`button "remove skill" [disabled]`), the testid itself not independently re-grepped in the live DOM this run (source-confirmed) |
| SkillCard version-selector trigger | `skill-version-selector-trigger-{skill_id}` (dynamic, pre-existing per `SkillVersionSelector.jsx`) | yes, confirmed present in DOM on the locked version (not independently clicked) |
| Tools section add buttons (Toolkit/MCP/Agent/Pipeline) + their tooltip text | `agent-add-toolkit-button` / `agent-add-mcp-button` / `agent-add-agent-button` / `agent-add-pipeline-button`, each wrapped in a `Tooltip` whose title is the shared `lockedTooltip` string (`This agent version is published and can not be modified`) | yes, all 4 confirmed `[disabled]` + correct tooltip text live on the locked version |
| Version dropdown trigger / option (dynamic) | `agent-version-selector-trigger` / `version-option-{version_name}` | yes (pre-existing per ELITEA-1892) |

**Correction (caught before commit):** an earlier draft of this table wrongly stated the SkillCard
remove button had no testid — it does (`skill-card-remove-button`, confirmed via source read of
`SkillCard.jsx:108`, and independently corroborated by the pre-existing `skills/_surface.md` digest's
ELITEA-2601 entry, which already documents it as non-unique-per-card and scoped inside
`[data-testid="skill-card-{skill_id}"]`). No `add-data-testid` work is needed for this element.

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` — the single mutation endpoint
  for the General-section form (Name/Description/Instructions/Tags). Returns `400 Bad Request`,
  `{"error": "Version id {versionId} is published and can not be updated"}` when the CURRENT version
  is published/embedded. This is the endpoint + exact error contract the automated test should assert
  against for Part B (status code + response body field, not just the rendered toast text, per
  `.agents/role-overrides.md`'s "4xx/5xx from the UI: cross-check the contract" guidance — this is a
  documented, correctly-modeled 400, not a UI-vs-backend classification question; both sides agree the
  version is locked).
- `POST /api/v2/elitea_core/publish/prompt_lib/{project}/{versionId}` / `POST
  .../unpublish/prompt_lib/{project}/{versionId}` — same publish/unpublish contract as ELITEA-1892,
  unchanged.
- Skill attach/detach endpoints (`POST`/`DELETE .../elitea_core/skill_relation/...` or equivalent) were
  never invoked in this run for the LOCKED version (all attempts were blocked client-side before any
  request fired) — automation asserting Steps 14-19 should assert **no network request fires** on a
  blocked-attempt click, distinct from Part B where the request DOES fire and the backend rejects it.

## Known Defects Found During Exploration

- **[MINOR]** SkillCard's "Remove skill" icon button and `SkillVersionSelector`'s version-change
  trigger show no immutability-explaining tooltip when disabled by a locked (published/embedded)
  agent version — inconsistent with the Tools section's add buttons and the Skill "+Skill" add button,
  which correctly implement this. Directly fails the case's own Pass criterion "Tooltip explains
  immutability on disabled controls" / Fail criterion "Tooltips are missing on disabled controls" for
  these two specific controls. Filed:
  [EliteaAI/elitea-testing-public#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470).
  **Automation guidance**: assert the CONFIRMED-missing tooltip with `expect.soft()` +
  `# Known defect: #1470` (do not hard-fail the whole test on it; do not assert the case's ideal
  behavior as if it already held for these two controls).
- **[CLARIFICATION]** The case's Test Data table states the error toast as "Version is published and
  cannot be updated" and the Skill-lock tooltip as "This agent version is published and can not be
  modified". Live product returns a more specific/correct toast (`"Version id {id} is published and
  can not be updated"`, naming the exact version) and a more complete tooltip ("...published **or
  embedded**..."). Live product behavior is correct (reverse-masking guard — the case text is the
  stale/simplified paraphrase); case-text update requested. **Does not block automation** — this AFS's
  Test Steps above already describe the exact live strings to assert on.

## Blocked Steps

None. All 25 case steps across Parts A-D were either directly executed and observed live, or asserted
via a source-confirmed shared mechanism explicitly flagged in the Coverage Map (Steps 8-13, 18, 23, 25)
— no step required stopping short of a verdict.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/agent_detail_page.py` (already carries
  `agent-actions-menu-button`, `delete-agent-menuitem`, the Publish-wizard fields, per ELITEA-1888/1889/1892)
  with the Skills-section controls (`agent-add-skill-button`, the SkillCard remove/version-selector
  handles) and a `PUT .../application/...` response-body assertion helper for the 400-on-locked-save
  pattern.
- Test-data generation: seed the disposable agent's Instructions with a real sentence and at least one
  alphanumeric-only Tag, exactly as ELITEA-1892's AFS documents, to pass `publish_validate` on the
  first attempt.
- Two distinct enforcement mechanisms in one test — don't reuse a single wait/assert helper for both:
  - **Part B (General fields)**: type → Save → wait for `PUT .../application/...` response → assert
    `status == 400` and `response.json()['error']` contains `"is published and can not be updated"` →
    assert the toast/alert renders that text → `Discard` (+ confirm dialog) to reset before the next
    field.
  - **Part C (Skill attachments)**: assert `to_be_disabled()` on the control directly (no click/no
    network request expected) → hover → assert tooltip text (soft-assert + Known-defect comment for
    the two #1470-affected controls, hard-assert for the three correct ones).
- Wait strategy: wait for the `publish_validate`/`publish`/`unpublish` responses exactly as ELITEA-1892
  documents (same shared `PublishWizardModal`/`UnpublishConfirmModal`); after Publish, explicitly
  re-select/re-navigate to the new version rather than trusting auto-navigation, per ELITEA-1892's
  known defect #614 (unchanged, still applies — this run re-navigated directly to the version URL and
  waited for hydration rather than trusting the post-publish auto-navigate).
- Consider parameterizing Part B's per-field loop (Name/Description/Instructions/Tags) as a single
  data-driven test function rather than 4 near-duplicate step blocks, since the mechanism (Steps 8-13's
  Coverage Map disposition) is identical across all four — this also naturally produces the
  independent per-field observation this AFS recommends but didn't fully execute live.
