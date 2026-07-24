# Test Case: Agent — Advanced Settings: Step limit accepts value, clamps to 0–999, blocks non-numeric input, and persists

## Metadata
- **TMS ID**: GAP-003 (coverage-gap campaign `cov60` card, not an onetest case —
  source: `.agents/automation-board/batches/cov60/cases/GAP-003/source.md`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case metadata — pytest.ini's `p2` marker is the
  direct match: p0=critical/p1=high/p2=medium/p3=low)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  on `automation/testids`)
- **User set**: none — localhost `auth_state` bypass (`VITE_DEV_TOKEN`), no
  login required
- **Analyst**: qa-engineer (Sage), 2026-07-23
- **Status**: ready-for-automation (re-confirmed on redispatch 2026-07-24 —
  see § Redispatch confirmations below; one PROVENANCE correction made,
  classification unchanged)

## Preconditions
- User is on `${BASE_URL}` (localhost auth bypass — no explicit login step).
- A dedicated, disposable agent exists in owner/edit mode
  (`/agents/all/{id}?viewMode=owner`) with `version_details.meta.step_limit`
  explicitly `null` — **not merely omitted**. Confirmed live: `POST
  .../applications/prompt_lib/{project}` with `meta: {}` (key omitted
  entirely) makes the **backend** default `step_limit` to `25`; only
  `meta: {"step_limit": null}` in the create payload produces the empty-field
  starting state the case's Step 1 requires. Use
  `AgentAPI.create_agent_full()` with that explicit payload — do NOT reuse
  the shared `agent_id` fixture or `AgentAPI.create_agent()` (both default
  `meta.step_limit` to `25`).
- The Advanced accordion (`agent-canvas-section-advanced`) is expanded by
  **default** — `BasicAccordion` renders with `defaultExpanded={true}` and no
  `expanded`/`onChange` override is passed from `ApplicationConfigurationForm.jsx`
  — confirmed live (`aria-expanded="true"` on load, Step limit input visible
  with zero clicks). No "expand the accordion" interaction is needed; assert
  the expanded state instead of clicking to open it.
- `add-data-testid` has been applied to the Step limit input
  (`agent-step-limit-input`) and pushed to `automation/testids` — see
  Automation Notes.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated agent via `AgentAPI.create_agent_full()`:
  ```python
  {
      "name": f"gap003-step-limit-{uuid4().hex[:8]}",
      "description": "...",
      "type": "interface",
      "versions": [{
          "name": "base", "tags": [], "instructions": "", "variables": [],
          "tools": [],
          "llm_settings": {
              "max_tokens": -1, "reasoning_effort": "none",
              "model_name": settings.default_model_name,
              "model_project_id": settings.default_model_project_id,
          },
          "conversation_starters": [], "agent_type": "openai",
          "welcome_message": "",
          "meta": {"step_limit": None},   # <-- the load-bearing part
      }],
  }
  ```
  (Mirrors the `reasoning_effort: "none"` / omit-`temperature` pattern already
  used by `test_agent_add_variables_persist_after_reload.py` to avoid the
  known-bad `agent_id` fixture payload, issue #563.)
- `MAX_STEP_LIMIT = 999`, `MIN_STEP_LIMIT = 0` (from `@/common/constants`,
  confirmed via `ApplicationAdvanceSettings.jsx` imports)
- Valid value: `"25"`
- Over-max value (paste-only, see Quirk below): `"1500"` → expected clamp `"999"`
- Below-min value (paste-only): `"-5"` → expected clamp `"0"`
- Rejected typed characters: `"a"`, `"b"`, `"-"` (one at a time)

## Test Steps
1. Navigate to the dedicated agent's detail page in owner/edit mode.
   - **Verify**: `agent-canvas-section-advanced` header has `aria-expanded="true"`
     (already expanded, no click needed); `agent-step-limit-input` is visible
     with value `""`.
2. Type `"25"` into `agent-step-limit-input` (real keystrokes, one at a time).
   - **Verify**: field shows `"25"`.
3. Click Save (`agent-save-button`); wait for the `PUT
   .../application/prompt_lib/{project}/{id}` response; reload the page
   (full navigation) and re-expand is not needed (still `defaultExpanded`).
   - **Verify**: Save response status `201`; response body
     `version_details.meta.step_limit == 25`; after reload,
     `agent-step-limit-input` still reads `"25"`.
4. Clear the field (`Ctrl/Cmd+A` then `Delete`), then **paste** `"1500"` (see
   Quirk — typing cannot reach this branch).
   - **Verify**: field shows `"999"`, not `"1500"`.
5. Clear the field, then **paste** `"-5"`.
   - **Verify**: field shows `"0"`, not `"-5"`.
6. Clear the field, then type `"a"`, `"b"`, `"-"` one at a time (real
   keystrokes).
   - **Verify**: field remains `""` after each keystroke (no character is
     ever inserted); typing a valid digit immediately afterward still works
     (field is not "stuck") — confirmed live by typing `"7"`/`"42"` right
     after the rejected sequence.
7. Select-all + Delete so the field is empty.
   - **Verify**: field is `""`; `aria-invalid="false"` on the input (no
     validation error surfaced).
8. (Cleanup) Delete the dedicated agent via `AgentDetailPage.delete_agent_via_menu()`
   or `AgentAPI.delete_agent()` in a `finally` block.
   - **Verify**: agent removed; no residual test data.

## Expected Results
- A valid Step limit (`"25"`) is accepted, the Save PUT returns `201` with
  `version_details.meta.step_limit == 25` in the body, and the value survives
  a full-navigation reload.
- A pasted `"1500"` clamps to `"999"`; a pasted `"-5"` clamps to `"0"`.
- Typed `"a"`/`"b"`/`"-"` are each rejected at keydown — the field never
  changes — and the field remains fully functional for digit entry
  immediately afterward.
- Clearing the field leaves it `""` with no validation error
  (`aria-invalid="false"`).
- No console errors are attributable to any Step-limit interaction (an
  unrelated, pre-existing `403` burst on `/api/v2/secrets/secrets/default/{id}`
  and `/api/v2/elitea_core/upload_icon/prompt_lib/{id}` fires on every agent
  detail page load in this project regardless of feature — see Automation
  Hints; exclude it explicitly from any "no new console errors" assertion).

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: Step limit accepts value, clamps 0–999, blocks non-numeric, persists | all 5 sub-behaviors true | steps 2–7 | steps 2,3,4,5,6,7 | asserted |
| 1 Open agent in edit mode, expand Advanced | accordion open, input visible+empty | AFS step 1 | step 1 | asserted *(clarified: already expanded by default — see Precondition note; "expand" reduces to an assertion, not a click)* |
| 2 Type `25` | field shows `25` | AFS step 2 | step 2 | asserted |
| 3 Save, reload, re-expand | field still `25` | AFS step 3 | step 3 | asserted *(decomposed: Save-response-body assertion added alongside the DOM assertion — see Axis 2)* |
| 4 Clear, paste `1500` | clamps to `999` | AFS step 4 | step 4 | asserted |
| 5 Clear, paste `-5` | clamps to `0` | AFS step 5 | step 5 | asserted |
| 6 Clear, type `a`,`b`,`-` one at a time | each keystroke blocked, field unchanged; navigation keys still work | AFS step 6 | step 6 | asserted *(decomposed: navigation-key-still-works and "field still accepts digits afterward" folded into the same step as a follow-up check — see Axis 2)* |
| 7 Select-all+Delete | field empty, no validation error | AFS step 7 | step 7 | asserted |
| 8 Delete throwaway agent | agent removed | AFS step 8 (Cleanup) | step 8 | asserted |
| Test Data: MAX_STEP_LIMIT=999, MIN_STEP_LIMIT=0 | clamp boundaries | steps 4–5 | steps 4,5 | asserted |
| Precondition: `add-data-testid` applied to Step limit input | testid present | (satisfied by this analyst pass — see Automation Notes) | n/a | asserted — testid added, committed + pushed to `automation/testids` this run (commit `74df748f`) |

**Axis 2 — Analyst additions.**

- `step 1` asserts `aria-expanded="true"` on the Advanced header rather than
  performing a click-to-expand — *added: live exploration showed
  `BasicAccordion`'s `defaultExpanded={true}` already renders it open; a
  blind click per the case's literal wording would have TOGGLED it CLOSED,
  which is the opposite of the case's intent. Documented as a reverse-masking-
  adjacent clarification, not a defect (the case text under-specifies "expand"
  when the true precondition is "assert already-open").*
- `step 3` asserts the Save PUT response body's
  `version_details.meta.step_limit == 25` (network-level ground truth) in
  addition to the DOM read — *added: mirrors the sibling ELITEA-1883/1884
  pattern (assert both the API response and the post-reload DOM value) so a
  DOM-only false-positive (e.g. stale client cache) can't hide a real
  persistence regression.*
- `step 4`/`step 5` use a **synthesized native-value-setter + `input`-event
  dispatch** to simulate paste, not Playwright's `fill()` or a raw keystroke
  sequence — *added: required because `isValidKeyInput`'s keydown gate blocks
  any single keystroke that would push the value over `MAX_STEP_LIMIT`, so
  the case's own "(pasted)" annotation is load-bearing, not decorative; see
  Automation Hints for the exact mechanism and its Synthetic-Input-Hygiene
  justification.*
- `step 6` additionally types a valid digit (`"7"`, then `"42"` after a fresh
  clear) immediately after the rejected sequence — *added: confirms the
  keydown gate's `preventDefault` calls don't leave the input in a "stuck"
  state; a real user recovering from a mistyped character needs this to keep
  working.*
- Non-console-error assertion excludes the pre-existing `403` burst on
  `/api/v2/secrets/secrets/default/{id}` and
  `/api/v2/elitea_core/upload_icon/prompt_lib/{id}` — *added: this exact
  noise is already documented as "not a defect" in two sibling AFS files
  (`l2_llm-selector-change-model-verify-settings-dialog-save-persist_ELITEA-1880.md`,
  `l2_fork-agent-version-to-different-project_ELITEA-1893.md`); confirmed
  again live this run, tied to project id `471`, unrelated to Step limit.*

## Cleanup
1. Delete the dedicated agent via `AgentDetailPage.delete_agent_via_menu()`
   (preferred — exercises the real UI delete flow) or
   `AgentAPI.delete_agent(agent_id)` as a `finally`-block fallback if the test
   fails before reaching a UI-deletable state.

## Concrete Handles (discovered during exploration)

All handles below are `data-testid`-based per `.agents/testing.md` § Locator
policy (testid-only, no fallback ladder). PROVENANCE verified fresh this run
(`cd ../EliteaUI && git fetch origin` immediately before checking).

| Element | testid | PROVENANCE | Notes |
|---|---|---|---|
| Advanced accordion header | `agent-canvas-section-advanced` | **CORRECTED 2026-07-24** (redispatch re-verification) — on `automation/testids` **only** (`EliteaAI/EliteaUI@353be956`, added by ELITEA-2166's in-chat-canvas work, a different case touching this shared component), **NOT yet on `main`**. Originally misclassified `on-main ✓ (pre-existing)` in the first analysis pass — the testid renders live on localhost regardless of which branch added it (dev server serves `automation/testids`), which is what made it read as "pre-existing" without checking which branch actually carries it. Re-verified fresh: `cd ../EliteaUI && git fetch origin && git show origin/main:"src/[fsd]/features/agent/ui/agent-details/configurations/ApplicationAdvanceSettings.jsx" \| grep testId` → 0 hits; `git grep -n agent-canvas-section-advanced origin/automation/testids` → 1 hit (line 88). Same testid renders identically on the create form, edit form, AND the in-chat create-agent canvas panel. | `aria-expanded` reflects open/closed state; `defaultExpanded={true}` so already `"true"` on load |
| Step limit input | `agent-step-limit-input` | **needs-adding → added this run** — on `automation/testids` only (EliteaAI/EliteaUI@74df748f), **NOT yet on `main`** (awaiting human cherry-pick) | Added via `add-data-testid` to `ApplicationAdvanceSettings.jsx`'s `Input.StyledInputEnhancer`, `inputProps={{ ..., 'data-testid': 'agent-step-limit-input' }}` — confirmed forwarded onto the real `<input>` via `StyledInputEnhancer` → `Input.InputBase` → MUI `TextField`'s `slotProps.htmlInput` |
| Save button | `agent-save-button` | on-main ✓ (pre-existing, already used by every other agent-form test) | inherited from `AgentFormPage` |

**Page object:** all three locators + 4 new methods
(`get_step_limit()`, `is_advanced_section_expanded()`, `type_step_limit()`,
`clear_step_limit()`, `paste_step_limit()`) were added to
`automation/pages/agent_form_page.py` (shared ancestor of `AgentDetailPage`,
since `ApplicationAdvanceSettings` is common to both the create and edit
routes) **this run**, and verified end-to-end against the live app via a
standalone script (headless Chromium, fresh browser context, real
`AgentDetailPage` calls) — every branch below passed:

```
[PASS] Advanced section expanded by default
[PASS] Step limit empty on fresh agent
[PASS] Type '25' -> field shows '25'
[PASS] Clear -> field empty
[PASS] Paste 1500 -> clamps to 999
[PASS] Paste -5 -> clamps to 0
[PASS] Typing 'ab-' rejected -> field stays empty
[PASS] Field still functional after rejection -> '42'
[PASS] Final clear -> empty, no crash
```

Plus a separate persistence check (Save → reload):
```
save status: 201
meta in response: {'step_limit': 25}
value after reload: 25
```

The implementer can lift these methods directly — they are not scaffolding,
they were exercised.

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/{project_id}` — setup
  (create dedicated agent). `201 Created`. Confirmed: `meta: {}` (key
  omitted) makes the backend DEFAULT `step_limit` to `25`; only
  `meta: {"step_limit": null}` produces the empty starting field the case
  needs — **this is load-bearing test-data detail, not a formatting choice.**
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  fires on Save. `201 Created` (not `200` — confirmed, matches the sibling
  ELITEA-1883/1884 pattern). Response body's
  `version_details.meta.step_limit` reflects the saved value.
- `DELETE /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  cleanup. `204 No Content`.
- No dedicated request fires for the clamp/reject/clear interactions — they
  are entirely client-side (formik `setFieldValue` only), confirmed by
  network-tab inspection during steps 2, 4, 5, 6, 7 (zero new requests
  besides the page's ambient/unrelated `403`s below).

## Known Defects Found During Exploration
None. All branches — accept, clamp-over-max, clamp-under-min, reject
non-numeric, clear-to-empty, persist-after-reload — behaved exactly per the
`ApplicationAdvanceSettings.jsx` source read (`isValidStepLimit` /
`isValidKeyInput`). Zero console errors attributable to any Step-limit
interaction (see the pre-existing, unrelated `403` note below).

**Note, not a defect:** a `403 Forbidden` burst on
`/api/v2/secrets/secrets/default/471` and
`/api/v2/elitea_core/upload_icon/prompt_lib/471?limit=20&skip=0` fires on
every agent-detail-page load in this local environment, regardless of
feature. This exact pattern (same project id `471`) is already documented as
"not a defect" in `l2_llm-selector-change-model-verify-settings-dialog-save-persist_ELITEA-1880.md`
and `l2_fork-agent-version-to-different-project_ELITEA-1893.md` — a
permission-scoping quirk of project `471`, unrelated to whatever feature is
under test. Confirmed again this run: it fires identically before, during,
and after every Step-limit interaction, never triggered BY one.

## Blocked Steps
None. All 8 case steps executed to completion with no blockers.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Extend
  `AgentFormPage` (`automation/pages/agent_form_page.py`) — new locators
  (`advanced_section_header`, `step_limit_input`) and methods
  (`get_step_limit()`, `is_advanced_section_expanded()`, `type_step_limit()`,
  `clear_step_limit()`, `paste_step_limit()`) already added and verified
  this run; `AgentDetailPage` inherits them, no duplication needed.
- **Paste simulation is the load-bearing mechanic for steps 4–5.**
  `isValidKeyInput`'s keydown gate (`ApplicationAdvanceSettings.jsx:28-52`)
  blocks any single keystroke that would push the value over
  `MAX_STEP_LIMIT` — so typing `"1500"` character-by-character can NEVER
  reach the `>MAX` clamp branch; the field would just stop accepting digits
  once it hit `"999"` and refuse the extra characters at the keydown layer,
  never invoking the `>MAX` arm of `isValidStepLimit` at all. `paste_step_limit()`
  reproduces a real browser paste's actual DOM path — set the input's value
  via the native `HTMLInputElement` prototype's value setter (bypassing
  React's controlled-value interception), then dispatch a real `input` event.
  This IS the same event sequence a genuine OS-level clipboard paste produces
  (paste → browser inserts the full text → single `input` event → React
  `onChange` fires) — a single correct, complete gesture, not a poisoned
  synthetic sequence (`playwright-testing` skill § Synthetic Input Hygiene).
  Do NOT reach for `locator.fill()` for this — `fill()` also bypasses
  `onKeyDown`, but per `.claude/rules/mui-patterns.md` React's
  controlled-component `onChange` may not fire reliably via `fill()`; the
  native-setter + dispatched-`input`-event approach is more explicit and was
  the one actually verified live.
- Use `agent_api.create_agent_full()` with the exact payload in § Test Data —
  reusing the shared `agent_id` fixture or `AgentAPI.create_agent()`'s
  convenience method defaults `meta.step_limit` to `25`, which fails Step 1's
  "field is empty" precondition.
- Marker: `@pytest.mark.p2` (medium priority — pytest.ini names it "Priority 2
  (medium) tests", the direct match for this case's `priority: medium`
  metadata) + `@pytest.mark.agents` + `@pytest.mark.regression`.
- Testid `agent-step-limit-input` is on `automation/testids` only as of this
  run (`EliteaAI/EliteaUI@74df748f`) — **not yet on `main`**. The test will
  run green on localhost (dev server serves `automation/testids`) but will
  fail on any deployed env until a human cherry-picks it — standard for this
  project's dual-target testid flow, not a blocker for merging the test to
  `automation/base`.

## Cleanup
See § Cleanup above (single entry, duplicated per spec-format for tooling
that scans for the heading either place).

## Redispatch confirmations

**Pass 2 (2026-07-24, ~00:05–00:15Z)** — analyst slot redispatched with no
review/PR/branch yet in existence for this case. Per the "no newer verdict,
complete prior AFS" playbook: read the AFS + `_surface.md` end-to-end
(self-consistent), `git status --short` confirmed no stray page-object diff
survived from Pass 1's self-verification, fresh `git fetch origin` +
`git grep` in `../EliteaUI` reconfirmed `agent-step-limit-input`
present-on-`automation/testids`/absent-on-`main` exactly as documented, and a
bounded live spot-check (against a real pre-existing agent, `manual_test_agent`
id 5189) reconfirmed: Advanced accordion expanded by default with zero
clicks, the keydown gate still rejects `"a"` while `"42"` immediately after
still succeeds (field not stuck), and this agent's own Step limit read `"25"`
on load (independent corroboration of the `meta:{}`-omitted → backend-defaults
quirk). Did not redo the paste-simulation clamp math or the create/delete
cleanup cycle — already proven with a passing transcript in Pass 1, zero new
signal from a third run. Experimental edit (`"42"` typed into the shared
agent) discarded cleanly — never saved, `beforeunload` accepted, re-loaded
fresh, confirmed `"25"` still reads back. Returned **ready-for-automation**,
AFS unchanged.

**Pass 3 (2026-07-24, this dispatch)** — redispatched again; still zero
PR/branch/review for GAP-003 (`env -u GITHUB_TOKEN gh pr list --search
"GAP-003" --state all` → `[]`; `git branch -a` / `git worktree list` → no
`GAP-003` worktree or branch exists). `git status --short` on the shared tree
remains clean of any stray `automation/pages`/`automation/tests` diff. Given
Pass 2 already spot-checked the live interaction claims (accordion
default-expanded, keydown-gate-not-stuck, testid-resolves-live) within the
same short window and nothing external could have changed them (no
implementer/UI-team action landed against this specific flow in the
interim), did **not** repeat that same live UI spot-check a third time —
would add zero signal per the Pass-2 finding itself. Instead spent the
re-verification budget on the highest-remaining-uncertainty item: a full
PROVENANCE re-derivation for **every** handle in the Concrete Handles table,
not just the previously-checked `agent-step-limit-input` row. This caught a
real inaccuracy neither Pass 1 nor Pass 2 had surfaced:

```
$ cd ../EliteaUI && git fetch origin
$ git show origin/main:"src/[fsd]/features/agent/ui/agent-details/configurations/ApplicationAdvanceSettings.jsx" | grep -n testId
(no output — zero hits)
$ git grep -n "agent-canvas-section-advanced" origin/automation/testids
origin/automation/testids:src/[fsd]/features/agent/ui/agent-details/configurations/ApplicationAdvanceSettings.jsx:88:        testId: 'agent-canvas-section-advanced',
$ git log origin/main..origin/automation/testids --oneline -- "src/[fsd]/features/agent/ui/agent-details/configurations/ApplicationAdvanceSettings.jsx"
74df748f test: [EL-0000] add data-testid for agent Step limit input (GAP-003)
353be956 test: [EL-0000] add data-testids for in-chat Create New Agent canvas (ELITEA-2166)
$ git grep -n "agent-save-button" origin/main | head -2
origin/main:src/pages/Applications/Components/Applications/SaveApplicationButton.jsx:62:      data-testid="agent-save-button"
origin/main:src/pages/Applications/Components/Applications/CreateApplicationTabBar.jsx:70:          data-testid="agent-save-button"
```

`agent-canvas-section-advanced` was classified `on-main ✓ (pre-existing)` in
Pass 1 — **wrong**. It is on `automation/testids` only, added by a *different*
case's commit (`353be956`, ELITEA-2166's in-chat canvas work touching this
same shared `ApplicationAdvanceSettings.jsx` component) — not yet cherry-picked
to `main`. The testid genuinely renders live on localhost regardless (dev
server serves `automation/testids`), which is exactly what made it read as
"pre-existing" without checking which branch actually carries it. Corrected
the Concrete Handles table row in place (see above) with the git evidence.
`agent-save-button` re-verified and confirmed genuinely `on-main ✓` (2 hits,
unrelated to this case's own testid work). Classification unaffected — still
**ready-for-automation**; the correction only changes what the eventual
closure record's promotability row must say (2 pending cherry-picks, not 1)
and is exactly the kind of drift the "fresh ground truth" discipline exists
to catch on a redispatch, not just re-answer the same questions already
answered. AFS otherwise unchanged.
