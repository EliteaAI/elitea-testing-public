# Test Case: `~` mention in Agent instructions lists only currently attached Skills

## Metadata
- **TMS ID**: ELITEA-1791
- **Linked Story**: none
- **Priority**: l3 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end, fully passes. No
  defect found. **Case-text drift clarification**: the case's steps describe
  navigating to "the Agent instructions field," which reads generically; the live
  product has exactly one such field per Agent — the **Instructions** accordion
  section on the Agent detail/edit page (`data-testid="agent-instructions-input"`),
  distinct from the embedded-chat message input, which has its own, separately
  implemented `~`-mention flow (`AgentDetailPage.send_chat_message_with_mention` /
  `ChatPage.send_message_with_skill_mention`, already covered by
  `test_skill_agent_interaction.py` / `test_skill_conversation_interaction.py` —
  **not** this case's target and not re-asserted here). This case is the first
  coverage of the **Instructions-field** mention scoping specifically.

## Rework — testid-only pass (issue #33, 2026-07-15)

PR #49 (merged to `automation/base` as `af4dde0`) implemented this case's
Instructions-field mention flow correctly in behavior, but shipped 3 raw
non-testid handles in `automation/pages/agent_detail_page.py`, violating the
project's testid-only locator policy (`.agents/role-overrides.md` +
`.agents/testing.md` § Locator policy — no fallback ladder, `data-testid` is
the only rung). Reopened for rework per the operator's directive on issue
#33 and `.agents/retrospectives/2026-07-14-framework-alignment-audit.md`.

**Root cause of the drift:** at analysis time (this AFS's original Concrete
Handles table, rows for "`~`-mention suggestion panel container" and
"`~`-mention candidate row") the analyst correctly observed that the panel
had no `data-testid`/`role="menuitem"` on its rows and documented the
`get_by_text('Mention skill')` + ancestor-xpath / `get_by_text(skillName)`
workaround as the best handle available **at that time**. What the analysis
missed: the exact same panel component (`MentionSkillList.jsx`) is **already
consumed by the embedded-chat mention flow**
(`AgentDetailPage.send_chat_message_with_mention`, same file), which already
carries `data-testid="skill-mention-list"` on the container and a dynamic
`data-testid="skill-mention-item-{skill-name}"` per row — added under
ELITEA-1735's testid-only rework. Since the Instructions-field mention panel
and the embedded-chat mention panel render the **identical shared
component**, the existing testids apply to the Instructions-field surface
for free — no new testid was ever needed. This is a case of "second entry
point into an already-testid'd component," not a genuine testid gap.

### Rework verification (live localhost:5173, playwright-testing MCP)

Read the current `agent_detail_page.py` (methods
`_instructions_mention_container` lines 1251–1260, `get_instructions_mention_item`
lines 1289–1304, `select_skill_from_instructions_mention` lines 1306–1322) and
`tests/ui/skills/test_agent_instructions_tilde_mention.py`. Confirmed via
`git grep` against `EliteaUI` (after `git fetch origin`) that
`data-testid="skill-mention-list"` (container, `MentionSkillList.jsx:56`) and
the dynamic `testId={`skill-mention-item-${item.name}`}` (row,
`MentionSkillList.jsx:81`) exist on `origin/automation/testids` (the live
dev-server integration branch — confirmed present and already reachable by
`automation_base`'s existing `skill_mention_list` `LocatorDescriptor` and
`SKILL_MENTION_ITEM_SELECTOR` template, both already declared class-level in
`agent_detail_page.py` lines 68 and 108 and already exercised by
`send_chat_message_with_mention`) but **absent from `origin/main`** — they
ship in still-open draft PR **#540**
(`testids/ELITEA-1735-skills-testids` → `main`, `EliteaAI/EliteaUI`), not yet
merged. `InstructionsInput.jsx` (the Instructions-field mention consumer)
also exists on `origin/main`, confirming this file isn't itself new/unmerged
— only the testids on the shared `MentionSkillList.jsx`/`MentionToolItem.jsx`
pair are pending in #540.

**Scope discipline applied:** no new testid is being requested. The fix is
to point the 2 rework'd methods at the **already-declared** `skill_mention_list`
LocatorDescriptor and `SKILL_MENTION_ITEM_SELECTOR` template — the same
fields `send_chat_message_with_mention` already uses — not to add anything
new to `MentionSkillList.jsx`/`MentionToolItem.jsx` or touch any neighboring
element.

### Handles needing rework (implementer scope)

| # | Current (raw, non-testid) | File:line (current) | Rework to |
|---|---|---|---|
| 1 | `self.page.get_by_text("Mention skill", exact=True)` then `.locator("xpath=ancestor::div[2]")` | `agent_detail_page.py:1258-1260` (`_instructions_mention_container`) | `self.skill_mention_list` (existing `LocatorDescriptor(testid="skill-mention-list")`, class field at line 108) — method can likely be deleted entirely once callers reference `self.skill_mention_list` directly (mirrors `send_chat_message_with_mention`'s direct use, no intermediate container-lookup method) |
| 2 | `container.get_by_text(skill_name, exact=True)` | `agent_detail_page.py:1304` (`get_instructions_mention_item`) | `self.skill_mention_list.locator(self.SKILL_MENTION_ITEM_SELECTOR.format(skill_name))` — identical pattern already used at `agent_detail_page.py:1412-1414` inside `send_chat_message_with_mention` |

Note on the dispatch prompt's 3rd bullet ("around line 1412 —
`self.skill_mention_list.locator(...)` for the mention candidate row"): that
line range is `send_chat_message_with_mention`'s **existing, already-correct**
testid-based row lookup (the embedded-chat surface, out of this case's
scope) — not a 3rd raw handle. The 2 rows above are the actual full set of
raw handles in the Instructions-field flow; there is no 3rd one. Likely a
stale line reference in the dispatch (the file has moved since PR #49
merged), as the dispatch itself anticipated ("check current line numbers").

`select_skill_from_instructions_mention` (lines 1306–1322) needs no direct
edit — it only calls `get_instructions_mention_item()`, so fixing #2 above
fixes it transitively. `type_tilde_in_instructions` (lines 1262–1287) needs
no direct edit either beyond its `return self._instructions_mention_container(...)`
call, which either keeps working (if the container helper is kept, now
backed by the testid) or is replaced with `return self.skill_mention_list` if
the helper method is removed — implementer's call, per existing project
precedent (ELITEA-1789/#31, ELITEA-1740/#30 reworks) of inlining once a
single-field testid replaces a multi-line workaround.

### Downstream verify

The regression test (`test_agent_instructions_tilde_mention.py`) calls only
`type_tilde_in_instructions()`, `get_instructions_mention_item()`, and
`select_skill_from_instructions_mention()` — all 3 stay behavior-identical
after the rework (same return types, same call signatures), so the existing
test file needs no changes, only a fresh green run once the page-object
methods are reworked.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills and Agents sections are available in the project.
- At least 3 distinct Skills exist in the project — **only 1 pre-existed**
  (`automated-test-explainer`, id 15); 2 more were created fresh in this run (see
  Test Data) to reach 3 total.
- An Agent exists with only 2 of the 3 Skills attached.

## Test Data

### reuse-existing
- Pre-existing Skill `automated-test-explainer` (id 15) — used as "Skill A"
  (attached to the test agent); not modified, not deleted.

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill B: `elitea-1791-skill-b` (id 233) — kebab-case name (client-side Skill-name
  validation is lowercase-letters/digits/hyphens-only, same constraint already
  documented for ELITEA-1735/1737/1739/1789/1790 —
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`).
  Description: `"Test skill B for ELITEA-1791 tilde-mention verification."`
  Instructions: `"You are test skill B created for ELITEA-1791 verification."`
  (content not asserted — only that a skill with a saved `base` version exists to
  attach). Attached to the Agent.
- Skill C: `elitea-1791-skill-c` (id 234) — same shape, description
  `"Test skill C for ELITEA-1791 tilde-mention verification."`, instructions
  `"You are test skill C created for ELITEA-1791 verification."`. **NOT** attached
  to the Agent — this is the negative-control skill; the whole case hinges on it
  never appearing in the mention list.
- Agent: `elitea-1791-tilde-mention-agent` (id 4668); description
  `"Agent for ELITEA-1791 tilde-mention-lists-only-attached-skills verification."`;
  Skills A (`automated-test-explainer`) and B (`elitea-1791-skill-b`) attached
  (2/5); Skill C left unattached.

The case's literal test-data example ("Skill A"/"Skill B"/"Skill C" placeholders)
is generic prose, not literal names to type — same reverse-masking pattern
already confirmed for ELITEA-1735/1737/1739/1789/1790. No
`generate-shared-with-cleanup` fixture applies — fresh-state flow, all created
entities torn down within the run; the pre-existing 4th (well, in this case, 1st)
skill was reused read-only.

## Test Steps
1. Confirm/create 3 distinct Skills in the project, with 2 attached to a target
   Agent and 1 left unattached.
   - Created Skill B (`elitea-1791-skill-b`, id 233) and Skill C
     (`elitea-1791-skill-c`, id 234) via `${BASE_URL}/skills/create`, filling Name
     (`skill-name-input`), Description (`skill-description-input`), Instructions
     (`skill-instructions-editor-content`, a CodeMirror editor — use
     `press_sequentially`/`type(slowly=true)`, not `fill`), then Save
     (`skill-save-button`).
   - **Verify**: each save triggers the "There are unsaved changes. Are you sure
     you want to leave?" nav-blocker dialog — confirmed via
     `alert-dialog-confirm-button`. URL settles on `/skills/all/{id}` each time
     (233, 234). Combined with the pre-existing `automated-test-explainer` (id
     15), 3 distinct skills now exist.
   - Created Agent `elitea-1791-tilde-mention-agent` via `${BASE_URL}/agents/create`
     (`agent-name-input`, `agent-description-input`, `agent-save-button`) — no
     nav-blocker dialog for the agent-create form (consistent with prior findings).
     Navigated directly to `/agents/all/4668?...`.
   - On the agent detail page, the **Skills** accordion is expanded by default,
     shows "0/5 skills added." with an add-skill button (icon-only, no
     `data-testid`, accessible name **"Skill"** exact — matches the handle already
     documented for ELITEA-1735/1789/1790). Clicked it, opened the "Search
     skills..." popper listing `Create new` + all 3 skills as `role="menuitem"`
     items, and attached `automated-test-explainer` (Skill A) then
     `elitea-1791-skill-b` (Skill B) one at a time. Counter went "0/5" → "1/5" →
     "2/5 skills added."; each attach auto-saves immediately (`PATCH
     /api/v2/elitea_core/skill/prompt_lib/399/{skill-id}` → `201 Created`; the
     page-level `Save`/`Save As Version` button stays disabled throughout —
     matches the documented auto-save pattern). `elitea-1791-skill-c` was left
     unattached.
2. Navigate to the Agent's **Instructions** field (case step: "Navigate to the
   Agent instructions field").
   - **Verify — case-text drift, resolved.** The live Agent detail page has one
     field matching this description: the **Instructions** accordion's textarea,
     `data-testid="agent-instructions-input"`, accessible name "Guidelines for the
     AI agent". Clicked it directly (`browser_click` on the testid) — it became
     the focused/active element (confirmed via snapshot: `textbox [active]`).
3. Type `~` in the instructions field (case step 3).
   - **Verify**: A suggestion panel appears immediately below the textarea,
     headed by literal text **"Mention skill"**
     (`page.get_by_text("Mention skill", exact=True)` — same header text already
     used by the existing embedded-chat mention flow in
     `AgentDetailPage.send_chat_message_with_mention`/
     `ChatPage.send_message_with_skill_mention`, confirming this is the same
     underlying mention-list component reused across both surfaces). No fixed
     wait/network call is involved — the list renders instantly from data the page
     already holds from its earlier `GET
     /api/v2/elitea_core/application_skills/prompt_lib/399/4668` fetch (confirmed:
     no new network request fired between typing `~` and the panel appearing —
     see Network Behavior below); wait on the "Mention skill" text becoming
     visible, not a timeout.
4. Inspect the list of suggestions shown (case step 4).
   - **Verify — exactly matches case expectation.** The panel lists **exactly 2**
     items, both `[cursor=pointer]` rows with name + description text:
     `automated-test-explainer` (Skill A) and `elitea-1791-skill-b` (Skill B).
     `elitea-1791-skill-c` (Skill C, the unattached skill) does **not** appear
     anywhere in the panel. Confirmed via full accessibility snapshot (not just a
     visual screenshot) — the DOM genuinely contains only 2 mention-candidate
     rows, not a 3rd hidden/filtered one. Screenshot:
     `test-results/screenshots/ELITEA-1791-step-3-mention-dropdown.png`. Zero
     console errors/warnings at this point (`browser_console_messages`: 0
     errors, 0 warnings; only informational React-DevTools/version-banner logs).
5. Select "Skill A" (`automated-test-explainer`) from the suggestions (case step
   5).
   - **Verify**: clicking the `automated-test-explainer` mention row inserts
     `~automated-test-explainer` as literal plain text into the textarea
     (confirmed via snapshot: `textbox "Guidelines for the AI agent" [active]:
     ~automated-test-explainer`) — matches the case's expected "`~Skill A` (or the
     appropriate reference syntax) is inserted." The mention panel closes after
     selection.
6. Select-all + delete the inserted text, then type `~` again (case step 6: "Type
   `~` again after removing Skill A reference").
   - **Verify**: the "Mention skill" panel reappears, again listing **exactly**
     the same 2 attached skills (`automated-test-explainer`,
     `elitea-1791-skill-b`) — Skill C still absent. Confirms the scoping is
     re-evaluated live on every `~` trigger, not cached/stale from the first
     invocation. Zero console errors/warnings after this second trigger either.

## Expected Results
- 3 distinct Skills exist in the project (1 pre-existing + 2 created); 2 are
  attached to the test Agent, 1 is not.
- Typing `~` in the Agent's Instructions field opens a "Mention skill" suggestion
  panel scoped to **only** the Agent's currently attached Skills — confirmed
  exactly 2 items shown, matching the 2 attached skills; the unattached 3rd skill
  never appears.
- Selecting a suggestion inserts `~<skill-name>` as plain text into the
  Instructions field.
- Re-triggering `~` after clearing produces the same correctly-scoped list again.
- No console errors or unexpected failed network requests occur during the flow
  (the one expected 404 seen was a stale skill-detail refetch immediately after
  that skill's own deletion during cleanup — documented artifact, not a defect,
  same pattern as ELITEA-1735/1737/1789/1790).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: 3 Skills exist, 2 attached to an Agent | Fixture state exists | Test Step 1 | 3 skills confirmed via UI creation + attach popper listing all 3 during exploration; 2 attached via the Agent detail-page Skills accordion, counter "0/5"→"2/5" | asserted |
| Step 1: Open the Agent in edit mode with 2 Skills attached | Agent edit form open, 2 Skills attached | Test Step 1 | Agent detail page navigated to directly after create; Skills accordion shows "2/5 skills added." with 2 named cards | asserted |
| Step 2: Navigate to the Agent instructions field | Instructions text area focused and editable | Test Step 2 | `agent-instructions-input` testid clicked, confirmed `[active]` in snapshot | asserted — **implementer amendment**: case text says "Agent instructions field" generically; live product's Instructions accordion field (not the embedded-chat input, which is a separate, already-covered mention surface) is the correct target — see Metadata clarification |
| Step 3: Type `~` in the instructions field | Suggestion/autocomplete dropdown appears | Test Step 3 | "Mention skill" panel becomes visible immediately, no network round-trip | asserted |
| Step 4: Inspect the list of suggestions shown | Only "Skill A" and "Skill B" listed; "Skill C" NOT shown | Test Step 4 | Full accessibility snapshot shows exactly 2 mention rows (`automated-test-explainer`, `elitea-1791-skill-b`); `elitea-1791-skill-c` absent from the DOM entirely, not merely hidden | asserted — matches case exactly, no drift |
| Step 5: Select "Skill A" from the suggestions | `~Skill A` (or appropriate reference syntax) inserted | Test Step 5 | Textarea content becomes `~automated-test-explainer` (plain text) after clicking the mention row | asserted |
| Step 6: Type `~` again after removing Skill A reference | Suggestion list appears again with only the attached Skills | Test Step 6 | Select-all+Delete clears the field; retyping `~` reproduces the same 2-item "Mention skill" panel (Skill C still absent) | asserted |
| Test Data: Skill names "Skill A"/"Skill B"/"Skill C" (literal placeholders) | literal names as written | N/A — case-text drift, not a defect | Live Skill `Name *` field is kebab-case-only client-side-validated; used `elitea-1791-skill-b`/`elitea-1791-skill-c` instead, reused `automated-test-explainer` as Skill A | clarification (reverse-masking, same pattern as ELITEA-1735/1737/1739/1789/1790) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| No new network request fires between typing `~` and the mention panel appearing | Confirms the scoping is a **client-side filter** over data the page already holds from its `GET application_skills/prompt_lib/{project}/{agent-id}` fetch (made when the Skills accordion loaded attached-skill cards) — not a fresh per-keystroke server query. Material automation hint: wait on the "Mention skill" text/DOM, not on a network response. |
| The "Mention skill" panel is the **same component** used by the embedded-chat `~`-mention flow (`AgentDetailPage.send_chat_message_with_mention`) | Confirms this case is testing a second entry point into an already-partially-covered mention subsystem, not an unrelated feature — useful context for the implementer deciding whether to extend an existing page-object method or add a new one (recommendation: add a new one, since the target field/testid differs — see Automation Hints) |
| Full accessibility-snapshot check (not just a screenshot) that the unattached Skill C is absent from the DOM, not merely visually hidden | A CSS-only hide could pass a screenshot-based check while still leaking the unattached skill's name/description into the accessibility tree or DOM (a real, if minor, information-scoping concern) — the snapshot confirms a genuine absence, which is the stronger and correct assertion |
| Console messages checked after both the first `~` trigger (step 3/4) and the second (step 6) | Zero errors/warnings both times; only informational React-DevTools/version-banner logs present throughout |
| Re-trigger correctness (step 6) re-evaluates the scoping fresh, not from a stale first-render cache | Confirms the mention list isn't a one-shot computation that could go stale if skills are attached/detached mid-session — directly matches the case's own step 6 intent, called out explicitly here as a distinct observable worth a hard assertion, not just "list appears again" |
| Cleanup verification: the 2 created skills and the Agent are actually gone after teardown | Confirms no orphaned test data leaks past this run — post-cleanup skills-list snapshot shows only `automated-test-explainer` remains |

## Cleanup
Three entities existed transiently in this run: 2 freshly-created Skills (`elitea-1791-skill-b` id 233, `elitea-1791-skill-c` id 234) and 1 Agent (`elitea-1791-tilde-mention-agent` id 4668). The pre-existing skill (`automated-test-explainer`, id 15) was **not** deleted (read-only reuse). All created entities were deleted live in this run; final skills-list screenshot/snapshot confirms only `automated-test-explainer` remains.

1. **Delete the Agent first, then the 2 Skills** — teardown-hygiene order (delete
   the thing with attached-state dependencies first), consistent with
   ELITEA-1735/1789/1790.
2. **Agent deletion**: UI overflow menu (`agent-actions-menu-button`) → "AGENT"
   group → "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` → inner `#name` field, typed
   `elitea-1791-tilde-mention-agent`) → click "Delete". Verified: page redirected
   away from the agent detail URL after confirm.
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`AgentAPI.delete_agent(agent_id)` in `automation/api/client.py`), same as
   ELITEA-1735/1789/1790.
3. **Skill deletion** (×2, ids 233, 234): UI overflow menu
   (`skill-controls-menu-button`) → "SKILL" group → "Delete skill"
   (`skill-delete-menu-item`) → same type-to-confirm dialog (typing each skill's
   own name) → click "Delete". Verified via UI redirect back to `/skills/all`
   after each; the well-known immediate follow-up `GET
   .../skill/prompt_lib/399/{id}` → `404` (stale refetch artifact of the
   redirect) appeared once for the last-deleted skill, as expected — not a
   defect (same as ELITEA-1737/1735/1789/1790).
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py`), once per
   created skill id.
4. **Recommended teardown fixture shape**: function-scoped fixture creating 2
   skills + 1 agent via the `skill_api`/`agent_api` clients directly (UI only
   needed for the mention-flow interaction itself, not for setup — the case's own
   assertions only require the skills/agent to *exist* and be *attached/not
   attached* correctly), attaching 2 of the 2 skills to the agent (plus reusing
   whatever skill(s) pre-exist as needed to reach 3 total distinct skills — look
   up the pre-existing skill via the skills-list API rather than assuming
   `automated-test-explainer` by name, since that name is this-environment-specific
   test data, not a guaranteed fixture), yielding all ids, and in its
   `finally`/post-yield block calling `agent_api.delete_agent(agent_id)` then
   `skill_api.delete_skill(skill_id)` for each of the 2 created skill ids, each in
   its own `try/except` (mirrors the pattern used in
   ELITEA-1735/1737/1738/1739/1789/1790).

## Concrete Handles (discovered during exploration; PROVENANCE added in the
2026-07-15 testid-only rework pass — see § Rework above)

| Element | Recommended Locator | Fallback | PROVENANCE |
|---|---|---|---|
| Skill Name field | `getByTestId('skill-name-input')` | — (testid is the only reliable handle; kebab-case validation applies) | on `main` |
| Skill Description field | `getByTestId('skill-description-input')` | — | on `main` |
| Skill Instructions editor | `getByTestId('skill-instructions-editor-content')` | CodeMirror inner content — use `press_sequentially`, never `fill` | on `main` |
| Skill Save button | `getByTestId('skill-save-button')` | — | on `main` |
| Nav-blocker confirm (fires on Skill-create Save) | `getByTestId('alert-dialog-confirm-button')` | — | on `main` |
| Agent Name field | `getByTestId('agent-name-input')` | — | on `main` |
| Agent Description field | `getByTestId('agent-description-input')` | — | on `main` |
| Agent Save button (create form) | `getByTestId('agent-save-button')` | — | on `main` |
| Agent detail-page Skills add-skill button (<5 attached) | `getByRole('button', { name: 'Skill', exact: true })` | no `data-testid` — matches ELITEA-1735/1789/1790's implementer-amended handle | not testid'd — role/name handle remains the team-accepted exception here (see ELITEA-1735/1789/1790 precedent), unchanged by this rework |
| Skill-attach popper item | `role="menuitem"`, accessible name = skill name (search box placeholder `"Search skills..."`) | use `exact: true` on the name match to avoid ambiguous substring matches between `elitea-1791-skill-b`/`-c` | not testid'd — same team-accepted exception, unchanged by this rework |
| Skills-added counter text | `getByText(/\d\/5 skills added\./)` | — | not testid'd — unchanged by this rework |
| **Agent Instructions field (this case's actual target)** | `getByTestId('agent-instructions-input')` — accessible name "Guidelines for the AI agent" | — no fallback needed, stable testid confirmed live | on `main` |
| **`~`-mention suggestion panel container — REWORKED** | `getByTestId('skill-mention-list')` — same `LocatorDescriptor` (`skill_mention_list`, `agent_detail_page.py:108`) already used by `send_chat_message_with_mention`; **superseded** `getByText('Mention skill', exact: true)` + `xpath=ancestor::div[2]` (raw handle, PR #49) | none — testid-only, no fallback permitted | **on `automation/testids`** (`MentionSkillList.jsx:56`, confirmed via `git grep` after `git fetch origin`), **not yet on `main`** — ships in open draft PR **#540** (`testids/ELITEA-1735-skills-testids` → `main`, `EliteaAI/EliteaUI`). `testid needed: NO` — testid already exists, reuse only |
| **`~`-mention candidate row — REWORKED** | `self.skill_mention_list.locator(self.SKILL_MENTION_ITEM_SELECTOR.format(skill_name))` — dynamic testid `skill-mention-item-{skill_name}`, same template constant (`agent_detail_page.py:68`) and pattern already used by `send_chat_message_with_mention` (`agent_detail_page.py:1412-1414`); **superseded** `page.get_by_text(skillName, exact=True)` scoped under the panel container (raw handle, PR #49) | none — testid-only, no fallback permitted | **on `automation/testids`** (`MentionSkillList.jsx:81`, `testId={`skill-mention-item-${item.name}`}` on `MentionToolItem`), **not yet on `main`** — same draft PR **#540**. `testid needed: NO` — testid already exists, reuse only |
| Agent actions (overflow) menu | `getByTestId('agent-actions-menu-button')` | — | on `main` |
| Delete-agent menu item | `getByTestId('delete-agent-menuitem')` | — | on `main` |
| Skill controls (overflow) menu | `getByTestId('skill-controls-menu-button')` | — | on `main` |
| Delete-skill menu item | `getByTestId('skill-delete-menu-item')` | — | on `main` |
| Delete-confirmation name field | `getByTestId('delete-confirm-name-input')` scoped to inner `#name` field | shared component, both agent and skill delete flows | on `main` |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | enabled only once typed name matches | not testid'd — unchanged by this rework |

## Network Behavior
- `GET /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}` —
  fetched once when the Agent detail page's Skills accordion loads (and again
  after each attach); this is the data source the `~`-mention panel filters
  client-side. **No additional network call fires when typing `~` or when
  re-triggering it** — confirmed via `browser_network_requests` diffed
  before/after the trigger.
- `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` → `201
  Created` — fires once per successful attach during setup (2 in this run).
- `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{agent-id}` on
  agent delete.
- `DELETE /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` on skill
  delete (×2), followed by one expected stale `GET
  .../skill/prompt_lib/{project}/{skill-id}` → `404` artifact for the
  last-deleted skill (not a defect).

## Known Defects Found During Exploration
None found. The mention-scoping behavior in the Agent Instructions field
correctly matches the case's Pass criteria exactly — no reverse-masking beyond
the already-established test-data-naming drift, no scoping leak, no console
errors, no unexpected network traffic.

## Blocked Steps
None — case executed end-to-end, all 6 case steps completed and verified
successfully.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md` — no non-obvious
  framework call needed.
- Page objects: extend `automation/pages/agent_detail_page.py` with a new method
  for this Instructions-field mention flow (e.g.
  `type_tilde_in_instructions_and_get_suggestions()` /
  `select_skill_from_instructions_mention(skill_name)`) — **do not** reuse
  `send_chat_message_with_mention`, which targets the embedded-chat input, a
  different field entirely, even though both surface the same "Mention skill"
  panel component. Reuse `skill_form_page.py` for skill creation (same as
  ELITEA-1790) and `agent_form_page.py`/`agent_detail_page.py` conventions for
  agent creation/attach — don't duplicate existing `fill_form`/`click_save`
  helpers (see `.claude/rules/page-objects.md`).
- Wait strategy: wait on `getByText('Mention skill', exact=True)` becoming
  visible after typing `~`, not a fixed timeout and not a network-idle wait
  (confirmed no network round-trip is involved).
- Assert the **negative** as strongly as the positive: not just "2 items shown"
  but "Skill C's name does not appear anywhere in the panel" — use
  `expect(mentionPanel.getByText(skillCName, { exact: true })).toHaveCount(0)`
  (or the async/Python equivalent) rather than only counting rows, since a count
  assertion alone wouldn't catch a scenario where the unattached skill appears
  under a different label.
- Prefer creating the 2 skills and the agent via the existing `skill_api`/
  `agent_api` fixtures (`automation/api/client.py`) rather than the UI, to keep
  this test's setup fast and focused on the mention-scoping behavior itself —
  only the Instructions-field `~`-trigger interaction needs to go through the
  UI/`agent_detail_page`.
- **Implementer amendment (PR #49 review):** `SkillAPI` has no `create_skill`
  endpoint (confirmed during implementation — see `agent_instructions_tilde_mention_quirks`
  memory entry), so all 3 skills are created via UI, same as the sibling
  ELITEA-1790 (`test_agent_max_five_skills_limit.py`). Agent creation was
  *also* kept on the UI path — even though `AgentAPI.create_agent()` exists at
  `automation/api/client.py:366` — for consistency with that same sibling test
  and because the test still needs a live `AgentDetailPage` instance
  immediately after creation (to click Instructions, attach 2 skills, and
  drive the `~`-trigger); API-creating the agent would only save one
  `fill_form`/`save_and_wait_for_navigation` round-trip while adding a second,
  divergent agent-setup pattern to this file area. Not a hard rule — a future
  pass could switch this one call to `agent_api.create_agent()` if setup speed
  becomes a real constraint.
