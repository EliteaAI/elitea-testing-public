# Test Case: Test panel uses the currently selected Skill version's instructions

## Metadata
- **TMS ID**: ELITEA-2440
- **Linked Story**: none
- **Priority**: l3 (case frontmatter/body: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value, not an exclusion. Proceeded
  to full execution.
- **Dedup / reuse check**: grepped `test-specs/skills/` and
  `automation/tests/ui/skills/*.py` for `send_test_message` + `switch_version`
  used together — no existing merged spec combines version-switching with a
  test-panel prompt run/response assertion. Closest neighbours are
  `l3_skill-version-dropdown-set-default_ELITEA-2437.md` (per-version
  *default* pin control, no test panel involved) and
  `l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md` (a
  different, agent-attach version selector component). Not a duplicate —
  proceeded as new coverage.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills section is accessible (`/skills/all` and `/skills/create`).

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- Skill: created via the UI create-skill form (`SkillsListPage.navigate_to_create()`
  → `SkillFormPage.fill_form(name, instructions="Always say BASE",
  description)` → `save_and_wait_for_navigation()`), not via `SkillAPI` —
  see the Coverage Map note on step 1 for why the case's own "Create a
  Skill" step is executed through the real UI form here rather than seeded
  via API, unlike the sibling ELITEA-2437 spec.
- Skill name used this run: `autotest-2440-version-test` (must satisfy the
  Name field's `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, ≤32-char constraint
  documented in `test-specs/skills/_surface.md`).
- Second version `v1`: created live via editing the instructions editor to
  `"Always say V1"` then `SkillDetailPage.save_as_version("v1")`
  (`automation/pages/skill_detail_page.py:483`) — confirmed this call
  captures the *current* (edited) instructions-editor content as the new
  version's instructions, leaving `base`'s stored instructions
  (`"Always say BASE"`) untouched.
- `SkillDetailPage.delete_skill_via_menu(skill_name)` (or
  `SkillAPI.delete_skill(skill_id)`) reused for teardown.

## Test Steps

1. Create a Skill with "base" instructions: `"Always say BASE"`, via the UI
   create-skill form (`/skills/create`).
   - **Verify**: form Save succeeds and the app navigates to the new
     skill's detail page — confirmed live: `POST
     /api/v2/elitea_core/skills/prompt_lib/399` → `201 Created`, URL becomes
     `/skills/all/{skillId}` (e.g. `/skills/all/1336`), Information panel
     shows `Skill ID: 1336` / `Version ID: 1377`. No separate "created"
     toast is shown for initial skill creation (confirmed live, matches the
     already-merged `test_skill_management.py::TestCreateSkill` behaviour) —
     the navigation to the detail page **is** the confirmation signal.

2. Save As Version `"v1"` with instructions `"Always say V1"`.
   - Edit the instructions editor's content to `"Always say V1"` (Ctrl+A +
     type, replacing `"Always say BASE"`), then click "Save As Version" and
     name it `v1` in the "Create version" dialog.
   - **Verify**: `POST /api/v2/elitea_core/skill/prompt_lib/399/1336` →
     `201 Created`; toast text is exactly `Version "v1" created`
     (confirmed live, matches `save_as_version()`'s existing assertion);
     URL gains the new version's id segment
     (`/skills/all/1336/1378` in this run); the instructions editor on this
     new version shows `"Always say V1"`.

3. Switch to `"v1"` in the version selector.
   - **Verify**: confirmed live — after step 2 the app is *already* on the
     newly-created `v1` version (`save_as_version()` auto-navigates there),
     so this step is a no-op state-check at automation time unless the
     implementer inserts an intermediate switch back to `base` first. See
     Coverage Map note — recommend calling `switch_version("v1")` explicitly
     anyway for step-fidelity with the case text (idempotent; confirmed live
     it does not error when the target version is already selected).

4. Run test prompt: `"What should you say?"` (via
   `SkillDetailPage.send_test_message()` + `wait_for_test_response()`).
   - **Verify**: message sends without error; AI response streams and
     stabilizes.

5. Verify the response contains `"V1"` (not `"BASE"`).
   - **Verify — confirmed live**: response text is exactly `"V1"`
     (`get_last_test_response()` reads `"V1"` verbatim, no other content).

6. Switch to `"base"` (via the VERSION dropdown — `version-option-base`)
   and run the same prompt again; verify the response contains `"BASE"`.
   - **Verify — confirmed live**: switching re-fetches
     `GET /api/v2/elitea_core/skill/prompt_lib/399/1336/1377` → `200 OK`;
     the instructions editor shows `"Always say BASE"` again; sending
     `"What should you say?"` a second time yields a response text of
     exactly `"BASE"` (`get_last_test_response()` reads `"BASE"` verbatim).

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end: the
SkillTestPanel's AI response reflects the **currently selected version's**
instructions, not a stale/cached version's — switching from `v1` (instructs
"Always say V1") to `base` (instructs "Always say BASE") and re-running the
identical prompt changes the response from `"V1"` to `"BASE"`. No functional
product defect found; no testid gaps found — every element this case
touches already carries a testid (see Concrete Handles), so this case ships
testid-only with zero new `add-data-testid` work.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| 1 Create a Skill with "base" instructions | operation completes; confirmation shown | step 1 | step 1: `201 Created`, navigation to detail page, Skill/Version ID panel | asserted |
| 2 Save As Version "v1" with instructions | operation completes; confirmation shown | step 2 | step 2: `201 Created`, `Version "v1" created` toast, URL version-segment change | asserted |
| 3 Switch to "v1" in the version selector | action completes; expected UI state | step 3 | step 3: already-on-`v1` state confirmed live (see note below) | asserted *(decomposed — see note)* |
| 4 Run test prompt "What should you say?" | action completes; expected UI state | step 4 | step 4: message sent, response streams | asserted |
| 5 Verify response contains "V1" (not "BASE") | condition holds | step 5 | step 5: `get_last_test_response()` == `"V1"` | asserted |
| 6 Switch to "base" and run same prompt; verify response contains "BASE" | action completes; condition holds | step 6 | step 6: version switch `200 OK`, `get_last_test_response()` == `"BASE"` | asserted |
| Expected Final State: response contains "BASE" after switching to base | — | step 6 | step 6, same assertion | asserted |

**Note on step 3 (decomposition):** the case text implies a discrete
"switch to v1" action distinct from step 2's version-creation. Live
execution showed `save_as_version()` auto-navigates to the newly-created
version, so by the time step 3 would run, the app is already on `v1` —
there is no observable state transition to assert *if* the implementer's
test flows straight from step 2 into step 3. This is not a case-text defect
(the underlying intent — "the test panel must be driven from the `v1`
version" — is satisfied either way) but the implementer should decide
between (a) calling `switch_version("v1")` anyway, purely for 1:1 step
fidelity with the TMS case (confirmed live this is a safe no-op when
already selected), or (b) documenting in the test's own docstring that
step 3 is satisfied as a side effect of step 2. Recommendation: (a), it's
one extra call and keeps the step count 1:1 with the TMS case for
traceability.

### Axis 2 — Analyst additions

- Step 1 executes the skill creation through the **real UI form**
  (`/skills/create`) rather than the `SkillAPI.create_skill()` shortcut the
  sibling ELITEA-2437 spec uses for its setup — *why: unlike ELITEA-2437,
  this case's own TMS text numbers "Create a Skill" as step 1 with its own
  explicit expected result ("confirmation is shown"), so it is case-owned
  behaviour here, not incidental setup. The behaviour itself (UI-driven
  skill creation with detail-page-navigation confirmation) is already
  independently proven by the merged `test_skill_management.py::
  TestCreateSkill::test_create_skill_and_verify_execution` — this AFS
  reuses that same flow rather than inventing a second one, and the
  implementer may lift the create+fill+save sequence directly from that
  test's Steps 1–3 rather than re-deriving it.*
- Step 2 documents the exact instructions-editor-mutation mechanics
  (Ctrl+A + type before clicking "Save As Version") — *added: without this,
  an implementer might call `save_as_version("v1")` right after skill
  creation without first changing the instructions, which would create a
  `v1` version whose instructions are identical to `base`'s and silently
  defeat the case's whole point (the test only proves anything if `v1` and
  `base` have genuinely different instructions).*
- Step 1/2/6 document the underlying `POST`/`GET` network calls and status
  codes — *added: gives the implementer wait-on-response hooks instead of
  fixed sleeps, consistent with `save_as_version()`'s existing pattern.*
- "zero console errors across the case's own 6 steps" — *added: side-channel
  check per this skill's standard discipline; not itself a case requirement.
  (A single 404 console error was observed, but only AFTER the case's 6
  steps completed, during this run's own cleanup/delete — see Known
  Defects/Observations. It is out of the case's own scope.)*
- Response-text exactness (`"V1"` / `"BASE"` verbatim, not merely
  "contains") — *added: the case's Pass text says "contains", but live
  observation shows the model (with these terse "Always say X"
  instructions) returns the bare word with no other content, so an exact
  match is the stronger and still-accurate assertion. The implementer
  should use a `"V1" in response` / `"BASE" in response` containment check
  if they want to match the case text literally and be robust to minor
  model wording variance across runs — either is defensible; containment
  is slightly safer against model non-determinism.*

## Cleanup
1. Delete the skill created in Test Data via
   `SkillDetailPage.delete_skill_via_menu(skill_name)` (or
   `SkillAPI.delete_skill(skill_id)`) in test teardown (`try`/`finally`),
   regardless of pass/fail — this removes both versions (`base` + `v1`) in
   one call, no separate per-version cleanup needed.
2. This run's own skill (`autotest-2440-version-test`, id `1336`) was fully
   deleted via the UI's "Delete skill" flow (type-to-confirm dialog) before
   this run ended — confirmed by the post-delete `GET
   .../skill/prompt_lib/399/1336/1377` returning `404 Not Found` and the
   skills list no longer showing it.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill create form — Name field | `page.get_by_test_id("skill-name-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.name_input` | n/a — testid already present |
| Skill create form — Description field | `page.get_by_test_id("skill-description-input-field")` — **confirmed live, existing testid**, already `SkillFormPage.description_input` | n/a — testid already present |
| Skill create form — Instructions CodeMirror editor content | `page.get_by_test_id("skill-instructions-editor-content")` — **confirmed live, existing testid**, already `SkillFormPage.instructions_editor_content` / `fill_instructions()` | n/a — testid already present |
| Skill create form — Save button | `page.get_by_test_id("skill-save-button")` — **confirmed live, existing testid** | n/a — testid already present |
| Detail page — "Save As Version" button | `page.get_by_test_id("skill-save-as-version-button")` — **confirmed live, existing testid**, already `SkillDetailPage.save_as_version_button` | n/a — testid already present |
| "Create version" dialog — Name field | `page.get_by_test_id("skill-create-version-name-input-field")` — **confirmed live, existing testid** | n/a — testid already present |
| "Create version" dialog — Save button | `page.get_by_test_id("skill-create-version-save-button")` — **confirmed live, existing testid** | n/a — testid already present |
| "Create version" confirmation toast | `page.get_by_test_id("toast-message")` — **confirmed live, existing testid**, already `SkillDetailPage.version_toast_message` | n/a — testid already present |
| VERSION dropdown trigger | `page.get_by_test_id("skill-version-select-combobox")` — **confirmed live, existing testid**, already `SkillDetailPage.version_selector` | n/a — testid already present |
| Version option row, keyed by name | `page.locator('[data-testid="version-option-{}"]'.format(name))` — **confirmed live, existing dynamic testid**, already `SkillDetailPage.VERSION_OPTION`; confirmed both `version-option-base` and `version-option-v1` resolve correctly | n/a — testid already present |
| Test panel chat input | `page.get_by_test_id("chat-message-input")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel send button | `page.get_by_test_id("chat-send-button")` — **confirmed live, existing testid**, already used inline in `SkillDetailPage.send_test_message()` | n/a — testid already present |
| Test panel last AI response text | `page.get_by_test_id("skill-test-last-response")` — **confirmed live, existing testid**, already `SkillDetailPage.get_last_test_response()` | n/a — testid already present |
| Overflow menu → "Delete skill" (cleanup) | `page.get_by_test_id("skill-controls-menu-button")` then `page.get_by_test_id("skill-delete-menu-item")` — **confirmed live, existing testids**, already `SkillDetailPage.delete_skill_via_menu()` | n/a — testid already present |
| Delete-confirmation dialog — Name field / Delete button | `page.get_by_test_id("delete-confirm-name-input")` / `page.get_by_test_id("delete-confirm-button")` — **confirmed live, existing testids**, already used inline in `SkillDetailPage.delete_skill_via_menu()` | n/a — testid already present |

**Summary for the implementer / `add-data-testid`:** zero testid gaps found
this run — every element the case touches already carries a testid, all
already wired into `SkillFormPage` / `SkillDetailPage` page-object methods.
No `add-data-testid` round-trip is needed for this case.

## Network Behavior
- `POST /api/v2/elitea_core/skills/prompt_lib/399` → `201 Created` (step 1,
  skill creation).
- `POST /api/v2/elitea_core/skill/prompt_lib/399/1336` → `201 Created`
  (step 2, "Save As Version").
- `GET /api/v2/elitea_core/skill/prompt_lib/399/1336/1378` → `200 OK`
  (loading the newly-created `v1` version, step 2/3).
- `GET /api/v2/elitea_core/skill/prompt_lib/399/1336/1377` → `200 OK`
  (switching back to `base`, step 6).
- `DELETE /api/v2/elitea_core/skill/prompt_lib/399/1336` → `204 No Content`
  (cleanup).
- AI test-panel responses arrive over WebSocket (per `.agents/testing.md`),
  not a plain REST call — `wait_for_test_response()`'s content-stabilization
  polling is the correct wait strategy, not a network-response wait.

## Known Defects / Observations Found During Exploration

No functional product defect was found. The test panel correctly reflects
whichever version is currently selected — confirmed by getting a
version-specific response (`"V1"` vs `"BASE"`) after each switch, with the
version's own instructions-editor content also confirmed to match
(`"Always say V1"` / `"Always say BASE"`) at the moment of each run. Zero
console errors occurred during the case's own 6 steps.

One console error was observed, but strictly **after** the case's 6 steps
completed, during this run's own cleanup (`DELETE .../skill/.../1336` then
a stale in-flight `GET .../skill/.../1336/1377` resolving as `404 Not
Found` post-delete) — a benign artifact of deleting a skill whose detail
page was still mid-refetch, not a defect in the feature under test. Not
filed; noted here for completeness only, per this skill's side-channel
discipline.

## Blocked Steps
None. All 6 case steps were executed end-to-end live against the real DEV
backend on localhost: creating the skill, editing instructions and saving
a second version, confirming the version switch, running the test prompt
on each version, and observing both version-specific responses — followed
by full cleanup.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_test_panel_version_instructions.py`
  (new file — grep of `automation/tests/ui/skills/` found no existing test
  combining version-switching with a test-panel prompt/response assertion).
- `SkillFormPage.fill_form()` / `save_and_wait_for_navigation()` for step 1
  (mirrors `test_skill_management.py::TestCreateSkill`'s Steps 1–3 almost
  verbatim — reuse that sequence).
- `SkillDetailPage.fill_instructions("Always say V1")` +
  `SkillDetailPage.save_as_version("v1")` for step 2 (edit-then-save-as
  order matters — see Axis 2 note).
- `SkillDetailPage.switch_version("v1")` for step 3 (recommended even
  though a live no-op right after step 2 — see the step 3 Coverage Map
  note).
- `SkillDetailPage.get_test_message_count()` →
  `SkillDetailPage.send_test_message("What should you say?")` →
  `SkillDetailPage.wait_for_test_response(initial_count=..., timeout=
  AI_RESPONSE_TIMEOUT)` → `SkillDetailPage.get_last_test_response()` for
  steps 4–5, repeated for step 6 after `switch_version("base")`.
- Cleanup: `SkillDetailPage.delete_skill_via_menu(skill_name)` in a
  `try`/`finally`, mirroring `test_skill_management.py`'s Step 6/7 pattern.
- No testid work required — see Concrete Handles summary.
