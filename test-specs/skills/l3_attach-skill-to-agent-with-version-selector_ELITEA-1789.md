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
- **Status**: `ready-for-automation` — **REWORK pass, 2026-07-15** (framework-alignment
  audit; supersedes the version of this AFS behind merged PR #47). The full functional
  flow (attach skill, version selector present + functional, default version shown,
  persistence after "save") completes and passes — re-verified live in this rework,
  unchanged from the original run. **What changed in this rework**: PR #47 shipped 11
  raw-handle occurrences (`get_by_text(skill_name, exact=True)` + `xpath=ancestor::div[3]`
  to scope the attached-skill card, `.version-text` CSS class for the version-selector
  trigger, raw `get_by_text("Versions", exact=True)` for the menu header,
  `xpath=ancestor::div[2]` again, `get_by_role("menuitem")` for menu items) — none of
  it testid-based, in violation of the project's testid-only locator policy
  (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). This rework
  replaces every one of those with a testid: the attached-skill card scope is already
  solved (`skill-card-${skill.skill_id}`, added by the ELITEA-1735 rework, draft
  EliteaUI#540); the version-selector trigger, the "Versions" menu container, and the
  per-version menu items are **`testid needed`** rows this AFS now specifies (see
  Handles Reference) — implementer adds them via `add-data-testid`. Closing the
  testid gap **also closes the testid portion of**
  github.com/EliteaAI/elitea-testing-public/issues/46. Issue #46's **other** finding —
  the trigger's `tabIndex=-1` / no ARIA role / no accessible name (real
  keyboard-accessibility defect, re-verified live in this rework, still present) — is
  a **separate, narrower a11y concern** that stays open; a `data-testid` does not by
  itself make an element keyboard-operable. See Known Defects.

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
   default and shows "0/5 skills added." with an add-skill button.
   - **Verify**: Skills attachment area is visible (case step 2). Confirmed live.
   - **Rework note**: this button now carries `data-testid="agent-add-skill-button"`
     — added since the original AFS (found in `SkillMenu.jsx` on
     `automation/testids`, part of the same ELITEA-1735 rework/draft EliteaUI#540
     that added the skill-card testid; not yet on `main`). Superseded handle: use
     `agent-add-skill-button`, not the old accessible-name locator.
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
   - **Verify — PASSES.** Re-confirmed live in this rework (fresh skill id `483`
     attached to fresh agent id `4756`). The card shows a `span.version-text`
     containing `"base"` plus a sibling `KeyboardArrowDownIcon` chevron styled as a
     dropdown affordance, inside a `Box` wrapper (`SkillVersionSelector.jsx:70-73`,
     `EliteaUI/src/[fsd]/features/skill/ui/`). **A real mouse click directly on
     `.version-text`** (Playwright `page.locator('.version-text').click()`, a
     genuine CDP-level click — not a snapshot-`ref`-resolved click) **opens the
     "Versions" menu** — reconfirmed live (`menu` role in the a11y tree, header
     text `"Versions"`, `menuitem "base"`). DOM inspection (`browser_evaluate`)
     also reconfirmed: the "Versions" `<Menu>` React-portals to `document.body` —
     it is **not** a DOM descendant of the skill's card (`isMenuInsideCard: false`,
     `bodyChildMenuExists: true`) — so any testid scoping strategy for the menu
     and its items must carry the skill/version identity itself (dynamic testid),
     not rely on DOM ancestry under the card.
   - **Rework — the raw-handle version of this step is gone.** PR #47's
     `.get_by_text(skill_name, exact=True)` + `xpath=ancestor::div[3]` card-scope,
     `.version-text` CSS trigger, raw `get_by_text("Versions")` header, and
     `xpath=ancestor::div[2]` menu-scope are all replaced by testids specified in
     Handles Reference: `skill-card-${skill.skill_id}` (already added, not yet on
     `main`), and three **new `testid needed` rows** — the trigger, the menu
     container, and the per-version menu item — for the implementer to add via
     `add-data-testid`.
   - **Accessibility-ref click still silently fails** — reconfirmed live this
     rework: an ARIA-tree/`ref=`-resolved click on the same visible "base" text
     lands on a non-interactive ancestor and does nothing (same defect as
     originally filed). DOM attributes of the trigger, reconfirmed via
     `browser_evaluate` this run: `{tabIndex: -1, role: null, ariaLabel: null,
     dataTestid: null}`. This is issue #46's **surviving** (a11y) finding — see
     Known Defects. Once the implementer adds the specified testid, automation
     targets the testid directly (no CSS-class/ancestor-walk needed), but the
     control **still won't be keyboard-operable** until the a11y half of #46 is
     separately fixed.
7. Confirm the default selected version in the version selector (case step 5).
   - **Verify**: the `"base"` text is shown pre-selected on the card before any
     interaction, and the opened "Versions" menu's single menuitem (`"base"`) has
     no distinguishing "selected" visual marker beyond being the only entry (only
     one version exists in this run) — consistent with `base` being the
     agent-attachment default. Confirmed live, reconfirmed this rework.
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

**REWORK — testid-only, per `.agents/testing.md` § Locator policy /
`.agents/role-overrides.md`.** Every row below is a `data-testid` or an explicit
`testid needed:` work order — no role/text/CSS/xpath handle is a primary locator.
PROVENANCE was verified fresh this session:
`cd EliteaUI && git fetch origin` (ran 2026-07-15, see raw output under each
provenance value), then `git grep` against `origin/main` and
`origin/automation/testids`.

```
$ git fetch origin
=== commits in automation/testids not in main === (17 commits, testid-only work; 0 in the other direction)
$ git grep -n "skill-card-\${skill" origin/main -- '*.jsx'
(no output — not on main)
$ git grep -n "skill-card-\${skill" origin/automation/testids -- '*.jsx'
origin/automation/testids:src/[fsd]/features/skill/ui/SkillCard.jsx:45:        data-testid={`skill-card-${skill.skill_id}`}
$ git grep -n "agent-add-skill-button" origin/main -- '*.jsx'
(no output — not on main)
$ git grep -n "agent-add-skill-button" origin/automation/testids -- '*.jsx'
origin/automation/testids:src/[fsd]/features/skill/ui/SkillMenu.jsx:180:              data-testid="agent-add-skill-button"
$ git show origin/main:"src/[fsd]/features/skill/ui/SkillVersionSelector.jsx" | grep -n "data-testid"
(no output)
$ git show origin/automation/testids:"src/[fsd]/features/skill/ui/SkillVersionSelector.jsx" | grep -n "data-testid"
(no output — confirmed: zero testids anywhere in this component, either ref)
$ gh pr view 540 --repo EliteaAI/EliteaUI --json state,isDraft,baseRefName,headRefName
{"baseRefName":"main","headRefName":"testids/ELITEA-1735-skills-testids","isDraft":true,"state":"OPEN"}
$ gh pr diff 540 --repo EliteaAI/EliteaUI | grep -n "agent-add-skill-button\|skill-card-"
68:+        data-testid={`skill-card-${skill.skill_id}`}
81:+              data-testid="agent-add-skill-button"
```

| Element | testid | PROVENANCE | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input` | on-main ✓ | kebab-case validation |
| Skill Description field | `skill-description-input` | on-main ✓ | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-main ✓ | CodeMirror; use `press_sequentially` |
| Skill Save button | `skill-save-button` | on-main ✓ | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | on-main ✓ | fires on Skill-create Save; did **not** fire on Agent-create Save in this run |
| Agent Name field | `agent-name-input` | on-main ✓ | |
| Agent Description field | `agent-description-input` | on-main ✓ | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | |
| Agent Save button | `agent-save-button` (create form) | on-main ✓ | stays **disabled** on the detail page once a skill is attached — attach is auto-saved, nothing to click |
| Agent add-skill button | `agent-add-skill-button` | **on-automation/testids only (draft EliteaUI#540)** | **rework-superseded handle** — was accessible-name-only (`getByRole('button', {name:'Skill'})`) in the merged PR #47 version; now a real testid, added by the ELITEA-1735 rework (same PR that added the skill-card testid below), not yet on `main` |
| Attached-skill card (scope for everything inside it) | `skill-card-${skill_id}` | **on-automation/testids only (draft EliteaUI#540)** | **rework-superseded handle** — replaces PR #47's `get_by_text(skill_name, exact=True)` + `xpath=ancestor::div[3]` card-scoping entirely. Dynamic testid, param = the skill's own id (already known to the test from skill creation) |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name | not testid'd on either ref | **out of this rework's scope** — not one of the raw handles PR #47 introduced for the version-selector flow (case step 3, pre-existing from ELITEA-1735); flag as a residual testid gap for a future pass, not blocking this AFS |
| **Version-selector trigger** (`.version-text` span + chevron, wrapped in a `Box`, `SkillVersionSelector.jsx:70-73`) | **`testid needed: skill-version-selector-trigger-{skill_id}`** (dynamic, param = skill_id — the `Box` at line 70 currently carries no testid at all) | **needs-adding** (absent from both refs — confirmed via the `git show \| grep data-testid` above, zero hits) | **Replaces PR #47's `.version-text` CSS-class handle.** Must be scoped by `skill_id` (not by DOM ancestry) because a real click on `.version-text` opens a `<Menu>` that React-portals to `document.body`, outside `skill-card-{id}` — confirmed live via `browser_evaluate`: `isMenuInsideCard: false`. The trigger itself remains `tabIndex=-1`, `role=null`, `aria-label=null` — a testid closes the *automation-handle* gap only; keyboard-accessibility is the surviving half of issue #46 (see Known Defects) |
| **"Versions" menu container/header** (`Box` at `SkillVersionSelector.jsx:98-105`, text `"Versions"`) | **`testid needed: skill-version-selector-menu-{skill_id}`** (dynamic, param = skill_id) | **needs-adding** | Replaces PR #47's raw `get_by_text("Versions", exact=True)` + `xpath=ancestor::div[2]`. Scope by `skill_id` for the same portal-to-body reason as the trigger — only one `SkillVersionSelector`'s menu is ever open at a time, but the testid must still carry identity since the menu isn't a DOM descendant of the card |
| **Version menu item** (per-version `MenuItem`, `SkillVersionSelector.jsx:116-128`, e.g. `"base"`) | **`testid needed: skill-version-option-{version_name}`** (dynamic, param = version name) | **needs-adding** | Replaces PR #47's raw `get_by_role("menuitem")`. Deliberately a **fresh, distinctly-named** key — NOT a reuse of the `version-option-{name}` pattern from the ELITEA-1738 rework (`skill_detail_page.py`, EliteaUI commit `eb5361f`), because that pattern is set by a different component's own `buildVersionOption()` helper (the skill-detail-page's own VERSION combobox), which `SkillVersionSelector.jsx` does not use — it maps its own `versions` array directly. Reusing the other component's exact key would create a false-equivalence between two unrelated selectors |
| Skill card "open in new tab" / "remove skill" buttons | accessible names `"open in new tab"` / `"remove skill"` | not testid'd on either ref | icon-only buttons, no testid — **out of this rework's scope** (not touched by this case's steps; case step 4/5/6 only exercise the version selector, not these buttons) |
| Agent actions (overflow) menu | `agent-actions-menu-button` | on-main ✓ | opens VERSION/AGENT grouped menu |
| Delete-agent menu item | `delete-agent-menuitem` | on-main ✓ | in the AGENT group |
| Skill controls (overflow) menu | `skill-controls-menu-button` | on-main ✓ | opens VERSION/SKILL grouped menu |
| Delete-skill menu item | `skill-delete-menu-item` | on-main ✓ | in the SKILL group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | on-main ✓ | shared component, both agent and skill delete flows |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | not testid'd on either ref | **out of this rework's scope** — pre-existing shared-dialog handle from ELITEA-1735/1737, not part of PR #47's version-selector raw-handle set; flag as residual gap, not blocking |

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
| Step 4: Verify attached Skill entry displays version selector | Version selector (dropdown or similar) shown next to Skill name | Test Step 6 | Chevron-icon + "base" text control confirmed clickable (real CSS-locator click, reconfirmed this rework) and opens a real "Versions" menu | covered — **rework: testid-only handles specified** (`skill-version-selector-trigger-{skill_id}`, `skill-version-selector-menu-{skill_id}`, `skill-version-option-{version_name}`, all `testid needed`), replacing PR #47's 11 raw-handle occurrences. Keyboard-accessibility (issue #46's a11y half) remains open — a testid doesn't grant keyboard operability, see Known Defects |
| Step 5: Confirm default selected version | Default version pre-selected (e.g. `base`) | Test Step 7 | "base" shown on card pre-interaction; sole entry in opened Versions menu | covered |
| Step 6: Save the Agent | Agent saves without errors; Skill remains attached with selected version | Test Step 8 | Agent-level Save button stays disabled (attach already auto-saved); persistence confirmed via full page reload showing "1/5 skills added." + same card | covered — **case-text drift** (reverse-masking): "Save the Agent" describes a generic save gesture the live product doesn't require for this action; asserted via persistence-after-reload instead of a literal Save click |
| Test Data: Skill name example `"Formatter"` | literal skill name as written | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1789-versel-skill` instead | clarification (reverse-masking, same pattern as ELITEA-1735/1739/1737) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is immediate API-level auto-save; material for correct wait strategy (don't wait on/assert `agent-save-button` state after attaching) — consistent with ELITEA-1735 |
| Accessibility-ref click vs. real CSS-locator click on the version-selector trigger | Load-bearing automation gotcha, reconfirmed this rework: an ARIA-tree/`ref=`-resolved locator resolves to the wrong DOM ancestor and silently no-ops; only a real click via a scoped locator (post-rework: the new testid) reaches the actual clickable element. Any implementer using `getByRole`/snapshot refs alone will write a test that "passes" without ever actually opening the version menu — this is why the rework's `testid needed` rows are a hard requirement, not a nice-to-have |
| DOM attribute inspection of the version-selector wrapper (`tabIndex`, `role`, `aria-label`, `data-testid`) | Confirms the accessibility gap is real and not a one-off snapshot artifact; reconfirmed this rework (`data-testid` still `null` on both `main` and `automation/testids` — see the `git show \| grep` output in Handles Reference) — grounds for the surviving (a11y) half of issue #46 |
| `<Menu>` portal-to-`document.body` confirmed via `browser_evaluate` (`isMenuInsideCard: false`) | Rework-specific finding: explains why the new `skill-version-selector-menu-{skill_id}` / `skill-version-option-{version_name}` testids must be dynamically scoped by identity rather than by DOM ancestry under `skill-card-{skill_id}` — a naive "testid inside the card" assumption would be wrong |
| Full page reload to confirm persistence | Since the agent-level Save button is disabled throughout, reload is the only way to independently verify the attach + version selection survived past the immediate in-session state |
| Console messages checked after every step | Zero errors during the functional flow; the single 404 seen was during cleanup (post-delete stale refetch), not during the case's own steps |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/46 — [MINOR] Agent Skills card version-selector control is not keyboard-accessible and has no data-testid

**REWORK STATUS: split.** This issue originally bundled two distinct findings — a
missing-testid finding and a keyboard-accessibility finding. This rework's Handles
Reference now specifies the exact `testid needed:` rows
(`skill-version-selector-trigger-{skill_id}`, `skill-version-selector-menu-{skill_id}`,
`skill-version-option-{version_name}`) that close the **testid** portion once the
implementer adds them via `add-data-testid`. The **keyboard-accessibility** portion
is unrelated to testid presence and was re-verified live in this rework — it is
still present and should stay open as its own, narrower a11y concern. (The
orchestrator/analyst dispatch owns actually updating/closing #46 on the tracker —
this AFS only records what re-verification found.)

- **Repro rate**: 100% (reconfirmed this rework — a real Playwright click via
  `page.locator('.version-text').click()` opened the "Versions" menu cleanly;
  a JS-evaluated click on the same element also opened it; an
  accessibility-snapshot/`ref=`-resolved click on the same visible "base" text
  silently did nothing, same as the original run).
- **Root-cause hint** (unchanged): the wrapping element (`div.MuiBox-root`
  containing `span.version-text` + the `KeyboardArrowDownIcon` svg,
  `SkillVersionSelector.jsx:70-73`) has `cursor: pointer` in its computed style
  but carries no `role`, no `aria-label`, `tabIndex="-1"`, and (still, reconfirmed
  this rework) no `data-testid`. Its own parent `MuiBox-root` (one level further
  out, `contentWrapper` at line 69) has `cursor: default` and is a dead click
  target — this is almost certainly why the accessibility-snapshot's
  ref-to-locator resolution lands on the wrong element.
- **Evidence (this rework)**: `browser_evaluate` DOM-attribute capture on the live
  trigger for skill id `483`/agent id `4756`: `{tabIndex: -1, role: null,
  ariaLabel: null, testid: null, className: "MuiBox-root css-x68gxm"}`; confirmed
  the "Versions" `<Menu>` portals to `document.body` (`isMenuInsideCard: false`,
  `bodyChildMenuExists: true`) — not a DOM descendant of the skill's card, which is
  why the new testids must carry `skill_id`/`version_name` identity rather than
  relying on ancestor scoping.
- **Impact**: keyboard-only and screen-reader users still cannot operate this
  control at all (severity: accessibility, WCAG 2.1.1 keyboard-operability class
  of issue) — **this part of #46 stays open**, independent of the testid fix.
- **Automation guidance (updated)**: once the implementer adds the three
  `testid needed` rows above, automation targets them directly — no CSS-class
  scoping, no ancestor `xpath`, no accessibility-tree/role-based locator. The
  underlying functional behavior (version selector present, functional via a real
  click, shows correct default) remains 100% reliable and should be
  **hard-asserted**. Do not attempt to automate via keyboard interaction (Tab /
  Enter) on this control — it is not currently reachable that way; that gap is
  tracked as the surviving half of #46, not worked around in the test.

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
None — case executed end-to-end, both in the original run and reconfirmed in this
rework (fresh skill id `483` / fresh agent id `4756`, cleaned up at the end of this
session). The version-selector's surviving keyboard-accessibility gap (issue #46,
a11y half only — see Known Defects) is a non-blocking, isolated finding; it does not
prevent completion of any case step and does not require `expect.soft()` treatment
since the case's own pass/fail criteria (a version selector is shown, default
version is correct, agent saves/persists with the skill attached) are all satisfied
reliably via the rework's testid-based handles once the implementer adds them.

## Rework Summary (2026-07-15)
- **Trigger**: framework-alignment audit found PR #47 (merged) shipped 11 raw-handle
  occurrences for this case, violating the project's testid-only locator policy.
- **Functional flow**: unchanged — re-verified live, not re-derived from scratch.
- **Handles Reference**: rewritten testid-only with a PROVENANCE column per row,
  verified via a fresh `git fetch origin` + `git grep` on both `origin/main` and
  `origin/automation/testids` (raw output pasted inline above the table).
- **New `testid needed` rows** (implementer work, via `add-data-testid`):
  - `skill-version-selector-trigger-{skill_id}`
  - `skill-version-selector-menu-{skill_id}`
  - `skill-version-option-{version_name}`
- **Bonus finding**: `agent-add-skill-button` now has a real testid (added since
  the original AFS, same draft EliteaUI#540) — Handles Reference updated to use it.
- **Issue #46**: testid portion closes once the three rows above are implemented;
  keyboard-accessibility portion re-verified live as still present and stays open
  as its own narrower a11y issue (closure/tracker edits are the orchestrator's, not
  this AFS's).
