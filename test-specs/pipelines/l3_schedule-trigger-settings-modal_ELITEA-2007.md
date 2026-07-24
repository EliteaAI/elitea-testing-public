# Test Case: Entry Point Node — Schedule Trigger Settings Modal

## Metadata
- **TMS ID**: ELITEA-2007
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths, no explicit login step
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

**Browser-lane note:** lane 0 (shared Playwright MCP browser) was occupied by a
parallel analyst this batch (`Error: Browser is already in use for
.../mcp-chrome-70a4838`). This session used an ISOLATED `browser-verify` (CDP)
Chrome instance on its own `--remote-debugging-port=9299` +
`--user-data-dir=/tmp/chrome-cdp-elitea2007` — no shared-browser contamination.

**Family note — this case is the Schedule-modal-internals deep dive, deliberately
shallow in the sibling case.** `test-specs/pipelines/l3_entry-point-node-trigger-types_ELITEA-2005.md`
(same batch, same feature) already covers all 3 trigger types end-to-end but its
OWN Schedule step (7–8) is intentionally shallow (open → default weekly-Saturday
cron → Apply → persisted) — its AFS explicitly defers "the deep modal-internals
verification" for Schedule to a sibling case, mirroring how it already treats
Webhook (deep-dived by `l3_webhook-trigger-settings-modal_ELITEA-2006.md`). This
case is that sibling for Schedule: Default/Advanced mode toggle, the "Every"
period dropdown's cascading fields (day/hour/minute pickers), and the dynamic
summary text — none of which ELITEA-2005 exercises. **Testid naming is aligned
to both siblings' already-specced conventions** (`pipeline-trigger-select`,
`pipeline-schedule-modal`, `pipeline-schedule-apply-button`) so one
`add-data-testid` pass across all three cases stays conflict-free — see Concrete
Handles. **`pipeline-trigger-select` and `pipeline-trigger-webhook-edit-button`
are ALREADY LANDED on `automation/testids`** (confirmed via a fresh `git diff
origin/main origin/automation/testids` this session — the ELITEA-2006
implementer's in-flight PR added them mid-session, observed live via Vite HMR
console messages during this exploration). This case's own implementer should
**reuse** `pipeline-trigger-select`, not re-add it.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with an entry point node, no HITL/Printer/interrupts.
  Confirmed live (same finding as ELITEA-2005/2006): a brand-new pipeline starts
  with ONLY an `End` node; adding any node (LLM used here) makes it the entry
  point automatically, no separate "make entrypoint" step.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A throwaway pipeline — reuse the existing `pipeline_with_llm_id` fixture
  (`automation/fixtures/data_fixtures.py:160`, via
  `PipelineAPI.create_pipeline_with_llm_node`) which already produces the
  precondition state (`entry_point: LLM 1`, one LLM node, connected to `END`).
  This session instead created and manually deleted its own pipeline via the UI
  (`QA-ELITEA-2007-ScheduleTrigger`, id `5693`, project `Private`/`399`) since
  analysts don't have automation-fixture authority — see Cleanup.

### case-literal values (used in Test Steps 5/9)
| Field | Value |
|-------|-------|
| Hour | 09 |
| Minute | 30 |
| Every (period) | day |
| **Live summary text** (see Known Findings — CLARIFICATION filed) | `At 09:30` — **not** `At 09:30, every day` as the case's Test Data table states |

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` ("Private" project).

## Test Steps

1. Create a pipeline with a single entry point node (LLM), no HITL/Printer/interrupts.
   - **Verify**: pipeline created, one real node + `END`, new node auto-entrypoint
     (same precondition mechanics as ELITEA-2005/2006 — not re-verified in depth
     here, see those AFSs for the full node-count assertion).
2. Click the entry-point node's Trigger select (`pipeline-trigger-select`, default
   "Chat Message") and select "Schedule".
   - **Verify**: "Schedule settings" modal (`role="dialog"`) opens, defaulting to
     **Default** mode selected, summary heading `At 00:00, only on Saturday`,
     `Every [week] on [SAT] at [00]:[00]` dropdowns, a helper caption
     "minute - hour - day (month) - month - day (week)" with an adjacent
     info-tooltip icon linking to `https://crontab.guru/#*_*_*_*`, and
     Cancel/Apply buttons. **All 6 case-listed elements confirmed present** —
     screenshot `/tmp/2007-08-schedule-modal.png`.
3. Open the "Every" period dropdown (`select-period`, ant-design Select) and
   click "day".
   - **Verify**: the "on" (day-of-week, `custom-select-week-days`) field
     disappears entirely from the layout (not just visually hidden — confirmed
     via a subsequent full-dialog testid enumeration finding zero
     `custom-select-week-days` node); summary updates to `At 00:00` — screenshot
     `/tmp/2007-18-day-set.png`.
4. Open the hour select (`custom-select-hours`) and set it to `09`.
   - **Verify**: summary updates to `At 09:00`. **Automation-critical gotcha
     found live**: this select is a MULTI-select (ant-design), and its default
     value `00` is NOT auto-replaced — clicking `09` ADDS it, producing `00,09`
     and summary `At 00:00 and 09:00` (screenshot `/tmp/2007-12-hour09.png`).
     Getting a single `09` requires an explicit second click on `00` to
     deselect it (screenshot `/tmp/2007-13-hour09only.png`) — see Known
     Findings and Automation Hints for the full mechanism + a scoping gotcha
     this discovery surfaced.
5. Open the minute select (`custom-select-minutes`) and set it to `30` (same
   deselect-the-default discipline as step 4).
   - **Verify**: summary updates to exactly `At 09:30` — screenshot
     `/tmp/2007-21-minute30-only.png`. **A validation message
     "Frequency cannot be less than every hour" appears (in red, replacing the
     summary) if the minute select is left with >1 value while hour also has a
     single/narrow value** (confirmed live at the intermediate `00,30` minute
     state, screenshot `/tmp/2007-20-minute30-added.png`) — this is CORRECT
     product behavior (a 2-value minute selection under a 1-value hour would
     fire twice within the same hour, i.e. more often than hourly), not a
     defect; it resolves the instant the minute selection is narrowed back to
     one value.
6. Click the "Advanced" radio.
   - **Verify**: a raw cron-expression text input appears, pre-populated from
     the Default-mode state (`30 9 * * *` — confirmed exactly matches
     Every=day/09:30), placeholder `* * * * *`; summary heading remains live,
     still reading `At 09:30` — screenshot `/tmp/2007-23-advanced.png`.
7. Click the "Default" radio (without editing the Advanced cron text).
   - **Verify**: the Default-mode dropdowns return, showing the exact same
     values as before switching (`day` / `09` / `30`), summary unchanged
     (`At 09:30`) — screenshot `/tmp/2007-24-back-to-default.png`. Values are
     **not** lost or reset by the round-trip through Advanced mode.
8. Click "Apply".
   - **Verify**: modal closes; the Trigger select eventually reads "Schedule" —
     **confirmed to lag by a few seconds in this session** (still read "Chat
     Message" ~1s after the click, resolved to "Schedule" after waiting;
     screenshots `/tmp/2007-26-applied.png` vs. the later poll) — same
     toast-vs-display-update lag ELITEA-2005's AFS already documented for this
     exact mechanism (RTK-query cache-invalidation + refetch round-trip).
     Automation must poll/wait for this text, never assert on the same tick as
     the Apply click.
9. Click the pipeline's "Save" button, then reload the page at its canonical URL.
   - **Verify**: after reload, the Trigger select shows "Schedule"
     (screenshot `/tmp/2007-29-reloaded2.png`); re-opening the schedule config
     via the new "Edit schedule" icon button (`aria-label="Edit schedule"`,
     appears next to the Trigger select whenever it reads "Schedule") shows the
     exact persisted state: Default mode, `Every [day] at [09]:[30]`, summary
     `At 09:30` — screenshot `/tmp/2007-30-edit-schedule.png`. Full round-trip
     persistence confirmed.

## Expected Results
- The Schedule settings modal shows all case-listed elements (summary line, mode
  radio, Default-mode fields, helper text, Cancel/Apply).
- Changing "Every" to "day" hides the day-of-week field.
- The summary line updates dynamically and correctly reflects every intermediate
  configuration change, including through the multi-select hour/minute quirk.
- Advanced mode shows a cron-expression text input pre-populated from the
  Default-mode state; switching back to Default restores the same dropdown
  values with no data loss.
- Clicking Apply closes the modal and (after a short display-update lag) updates
  the Trigger select to "Schedule".
- The configured schedule (day/09:30) persists exactly across Save + full page
  reload, verifiable both via the Trigger select's text and via re-opening the
  Schedule settings modal through the new "Edit schedule" icon.
- No console errors attributable to app code (two third-party `react-js-cron`
  console warnings observed — not app defects, see Known Findings).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with entry point node, no HITL/Printer/interrupts | setup exists | step 1 | step 1 | asserted |
| 1 Create pipeline with entry point node | Pipeline ready, single entry point | step 1 | step 1 | asserted |
| 2 Select "Schedule" from Trigger dropdown | Trigger updates to "Schedule" | step 2 | step 2 (modal open is the observable proxy) + step 8 (select text itself) | asserted *(decomposed)* |
| 3 Verify Schedule settings modal contents (summary, mode radio, Default fields, helper text, Cancel/Apply) | All listed elements present | step 2 | step 2 | asserted |
| 4 Change "Every" to "day" — verify "on" field hides | "on" field hidden | step 3 | step 3 | asserted |
| 5 Change hour=09, minute=30 — verify summary updates | Summary reads (per case) "At 09:30, every day" | steps 4–5 | steps 4–5 | asserted *(with a CLARIFICATION filed on the exact expected string — see Known Findings; live text is `At 09:30`)* |
| 6 Switch to Advanced — verify cron input appears | Cron input shown | step 6 | step 6 | asserted |
| 7 Switch back to Default — verify dropdowns return | Default dropdowns restored | step 7 | step 7 | asserted |
| 8 Click Apply — verify modal closes, Trigger shows "Schedule" | Modal closes, Trigger = Schedule | step 8 | step 8 | asserted |
| 9 Save — reload — verify Schedule trigger persists | Trigger = Schedule after reload | step 9 | step 9 | asserted |
| Expected Final State: Default/Advanced work, summary updates dynamically, trigger persists | — | all steps | all steps | asserted |
| Pass/Fail: all steps complete without errors; modal elements present, summary updates, trigger persists | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 4/5 additionally document the **hour/minute multi-select deselect
  discipline** — *added: the case's own text ("change hour to 09") reads like a
  simple field replacement, but the live control is a multi-select that ADDS
  the clicked value; an implementer following the case text literally would
  produce `00,09` (or leave the validation error active) instead of the
  intended single `09`. This is exactly the kind of behavior only live
  execution reveals — a copy-paste AFS from the case text would ship a broken
  or flaky test.*
- Step 5 additionally documents the **"Frequency cannot be less than every
  hour" validation message** — *added: neither in the case text nor implied by
  it; without documenting this, an implementer hitting the same intermediate
  state during exploration could misclassify it as a defect. It is correct
  guard-rail behavior, not a bug.*
- Step 6/7 additionally assert **value round-trip fidelity through the
  Default↔Advanced toggle** (the exact `30 9 * * *` cron string appears in
  Advanced, and the Default dropdowns show the exact same day/09/30 after
  switching back) — *added: the case only asks that "the input appears" /
  "dropdowns return," not that the underlying values are preserved verbatim.
  This is the more meaningful assertion (a naive implementation could silently
  reset to a default cron on mode switch) and costs nothing extra to check.*
- Step 9 additionally re-opens the persisted config via the **"Edit schedule"**
  icon button (not explicitly named in the case) to verify the full
  Default-mode field state survived reload, not just the Trigger select's
  label text — *added: the case's step 9 expected result only names "Schedule
  trigger is present after page reload," which the Trigger select text alone
  already satisfies; re-opening the modal is a stronger, free verification that
  the underlying day/hour/minute values (not just the trigger TYPE) persisted.*
- No console-error assertion was in the original case text; added throughout as
  a side-channel check per this project's standard practice. Two react-js-cron
  library warnings were observed (see Known Findings) — not app defects, no
  new assertion needed beyond noting them.
- No explicit wait-strategy note was in the case text; added as an Automation
  Hint after observing the same toast-vs-display-update lag on Apply that
  ELITEA-2005's AFS already documented for this shared mechanism.

## Cleanup

1. This session created and then fully deleted its own throwaway pipeline
   (`QA-ELITEA-2007-ScheduleTrigger`, id `5693`, project `Private`/`399`) via
   the UI's own three-dot "Delete pipeline" action (typed-name confirmation
   dialog) — confirmed gone from the pipelines list afterward. Analyst has no
   automation-fixture authority per `.agents/workflow.md`.
   **Tooling gotcha hit during cleanup**: the delete-confirmation dialog's
   "type the name" input shares the literal DOM `id="name"` with the page's
   OWN pipeline-name field (both are on-screen simultaneously, dialog portals
   to `document.body`) — a bare `#name` selector resolves to the WRONG (page)
   field. Scope with `div[role="dialog"] input#name` to hit the dialog's own
   field. Harmless here (typed the same string into both), but worth a
   `browser-verify` tooling note.
2. Implementer: use the existing `pipeline_with_llm_id` fixture
   (`automation/fixtures/data_fixtures.py:160`) — function-scoped, auto-creates
   via `PipelineAPI.create_pipeline_with_llm_node`, auto-deletes on teardown.
   No new fixture is needed for this case.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** (`.agents/testing.md` §
Locator policy, `.agents/role-overrides.md`). Provenance verified via a fresh
`git fetch origin` this session (`EliteaUI`), checked against both
`origin/main` and `origin/automation/testids`.

| Element | Testid (recommended name where missing) | Provenance |
|---|---|---|
| Entry-point Trigger select | `pipeline-trigger-select` — `TriggerTypeSelector.jsx:296` | **on-`automation/testids` ✓ (landed mid-session by the ELITEA-2006 implementer's in-flight PR — confirmed via `git diff origin/main origin/automation/testids`)**, needs-adding on `main` (human cherry-pick pending). **Reuse, do not re-add.** |
| Trigger option "Schedule" | `select-option-schedule` (shared `SELECT_OPTION` family) | on-main ✓ |
| "Edit schedule" icon button (reopens the modal once Trigger=Schedule) | **NO `data-testid` today.** `TriggerTypeSelector.jsx:312-320` (`<IconButton onClick={handleScheduleIconClick} ...><ClockIcon .../></IconButton>`, conditionally mounted `currentTriggerType === TRIGGER_TYPES.schedule`) — its Webhook sibling (`handleWebhookIconClick`, lines 329-338, conditionally mounted on `=== TRIGGER_TYPES.webhook`) already has `data-testid="pipeline-trigger-webhook-edit-button"` (same in-flight PR). **Flag to `add-data-testid`**: add `data-testid="pipeline-trigger-schedule-edit-button"` on the Schedule button — same naming pattern as its already-landed sibling, no shared-component dependency (plain same-file `IconButton`). Note: this is two DISTINCT, mutually-exclusive JSX elements (not one node with a state-conditional testid ternary), so this is a normal single-element gap, not a #277-style conditional-pair case. | needs-adding |
| Schedule settings modal (root) | **NO `data-testid` today.** `PipelineScheduleModal.jsx:46` (`<Modal.BaseModal ...>`) is missing the `dataTestId` prop `BaseModal.jsx:32,124` already supports. **Flag to `add-data-testid`**: add `dataTestId="pipeline-schedule-modal"` (name matches ELITEA-2005's AFS's already-recommended name for this exact element). | needs-adding (mechanism on-main ✓, confirmed via `git show origin/main:.../BaseModal.jsx` — `data-testid={dataTestId}` at line 124) |
| Schedule settings modal — Close (X) button | **NO `data-testid` today.** `BaseModal.jsx` already supports `closeButtonTestId` (line 146). **Flag to `add-data-testid`**: add `closeButtonTestId="pipeline-schedule-modal-close-button"` at the `PipelineScheduleModal.jsx` call site. | needs-adding (mechanism on-main ✓) |
| Schedule settings modal — dynamic summary text (e.g. "At 09:30", "At 00:00, only on Saturday") | **NO `data-testid` today.** `PipelineScheduleModal.jsx:54-59` (`<Typography variant="headingSmall" ...>{cronState.message}</Typography>`). **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-modal-summary-text"` directly (plain Typography, no shared-component dependency; name matches ELITEA-2005's AFS's recommendation). | needs-adding |
| Mode radio group (Default/Advanced) | **NO `data-testid` today.** `PipelineScheduleModal.jsx:62-70` uses `Checkbox.RadioButtonGroup` (the SAME shared component already used for the Webhook Type radio, `RadioButtonGroup.jsx:36-38`), but the call site passes no `testId` prop. **Flag to `add-data-testid`**: add `testId="pipeline-schedule-mode-radio"` → yields `pipeline-schedule-mode-radio-default` / `pipeline-schedule-mode-radio-advanced` (per-item testid derived as `${testId}-${value.toLowerCase()}`, confirmed mechanism). **PROVENANCE CAVEAT (re-confirmed fresh this session, same as ELITEA-2005/2006's identical caveat for the Webhook radio)**: the `testId` prop mechanism itself is on `automation/testids` ONLY (`git diff origin/main origin/automation/testids -- RadioButtonGroup.jsx` shows the prop was added there, absent from `main`) — not a blocker (dev server runs `automation/testids`), but the closure record should note this shared dependency's own promotion status. | needs-adding — **the `testId` prop mechanism it depends on is on `automation/testids` only, not yet on `main`** |
| "Every" period select (Default mode) | `select-period` — **third-party library** (`react-js-cron` ^5.2.0, `<Cron>` component rendered directly by `PipelineScheduleModal.jsx:74-79`), NOT app JSX. The testid is baked into the npm package itself. | **on-main ✓ (third-party npm dependency, stable unless the package version changes — not app code, no `add-data-testid` work needed)** |
| "on" day-of-week select (Default mode, `week` period only) | `custom-select-week-days` — same third-party library | on-main ✓ (same caveat as above) |
| Hour select (Default mode) | `custom-select-hours` — same third-party library. **MULTI-select** — see Test Steps 4 and Automation Hints for the deselect-the-default discipline this requires. | on-main ✓ (same caveat) |
| Minute select (Default mode) | `custom-select-minutes` — same third-party library. **MULTI-select**, same discipline as hours. | on-main ✓ (same caveat) |
| Cron expression text input (Advanced mode) | **NO `data-testid` today.** `PipelineScheduleModal.jsx:81-87` (`<FormInput value={cronExpression} onChange={...} placeholder="* * * * *" .../>`, a thin MUI `TextField` wrapper). **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-modal-cron-input"` as a plain prop — lands on the `MuiFormControl-root` wrapper (standard MUI unrecognized-prop forwarding), same accepted pattern ELITEA-2005/2006's AFS already used for the Webhook modal's URL/Secret `FormInput` fields (scope a nested `input` locator off it). | needs-adding |
| Helper caption text ("minute - hour - day (month) - month - day (week)") | No testid needed for this case — static text, not asserted by any step; if a future case needs it, `PipelineScheduleModal.jsx:90-96` is a plain `Typography`, same wiring shape as the summary text above. | not applicable to this case |
| Info-tooltip icon (links to crontab.guru) | `data-info-tooltip="true"` attribute already present (`InfoTooltip` component) — sufficient if a future case needs to assert its `href`; not exercised by this case's steps. | on-main ✓ (existing attribute, not a `data-testid` but stable and not needed here) |
| Cancel button | **NO `data-testid` today.** `PipelineScheduleModal.jsx:108-115` builds its own `<Button>` (custom `actions` prop, not `BaseModal`'s built-in `onConfirm`/`cancelButtonTestId` path). **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-cancel-button"`. Not clicked by this case's steps (case never exercises Cancel) — specced for completeness/future use. | needs-adding |
| Apply button | **NO `data-testid` today.** `PipelineScheduleModal.jsx:116-124`, same custom-`actions` shape. **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-apply-button"` (name matches ELITEA-2005's AFS's already-recommended name for this exact element). | needs-adding |
| Pipeline's own entry-point node id / Save button | `get_entrypoint_node_id()` / `save_and_wait_for_update()` — existing `PipelineDetailPage` methods, reused as-is | on-main ✓ (existing helpers) |

## Network Behavior

Same underlying mechanism ELITEA-2005's AFS already confirmed and documented in
full (endpoint, version-scoping, refetch behavior) — not re-derived here to
avoid duplicate exploration:

- `PUT .../elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger`
  fires on this modal's Apply click.
- `GET` on the same path refetches after the PUT (RTK-query cache invalidation)
  — this is what the Trigger select's displayed text is waiting on, producing
  the observed few-second display lag after Apply (step 8).
- `PUT .../elitea_core/application/prompt_lib/{project_id}/{pipeline_id}` fires
  on the pipeline's own "Save" click, `201` on success — separate from the
  trigger-config mutation above.

## Known Findings During Exploration

**No product defect found in the Schedule modal's core functionality.** Default
mode, Advanced mode, the mode toggle round-trip, dynamic summary updates, and
full Save+reload persistence all work correctly across every configuration this
case exercises.

Two items filed / re-confirmed, plus two non-actionable observations:

- **CLARIFICATION filed**: [EliteaAI/elitea-testing-public#1013](https://github.com/EliteaAI/elitea-testing-public/issues/1013)
  — the case's Test Data table names the expected summary as `At 09:30, every
  day`; the live product correctly renders `At 09:30` (no day-qualifier suffix
  for the `day` period — the qualifier clause only appears for periods that
  need disambiguation, e.g. `week`'s `At 00:00, only on Saturday`). Classified
  per the reverse-masking guard: case text is stale, product is correct. This
  AFS's Coverage Map asserts the LIVE string.
- **Already-filed bug re-confirmed, not re-filed**: `#694` (`BaseModal`
  `aria-labelledby="alert-dialog-title"` pointing at a non-existent id — the
  real `<h2>` carries the stale `id="variables-dialog-title"`) reproduces in
  THIS modal too (confirmed via DOM dump: `<h2 ... id="variables-dialog-title">`
  under `aria-describedby="alert-dialog-description" aria-labelledby=
  "alert-dialog-title"`). This is a `BaseModal`-wide defect, not specific to
  the Schedule modal — no new issue filed, `#694` already covers it.
- **Not a defect (validation guard)**: the "Frequency cannot be less than every
  hour" message (Test Step 5) — correct behavior preventing a sub-hourly
  schedule from being silently accepted, not a bug.
- **Third-party library console noise, not an app defect**: two console
  `error`-level warnings observed, both traced via their stack trace to
  `node_modules/.vite/deps/react-js-cron.js` internals — `[antd: Select]
  popupClassName is deprecated` and a React "does not recognize the
  `dropdownAlign` prop" warning from `react-js-cron`'s own `SelectInput`/
  `SelectTrigger` components. Neither originates from `PipelineScheduleModal.jsx`
  or any other app-owned file — out of scope to fix in this codebase (upstream
  library issue), not filed.

## Blocked Steps

None. All 9 case steps were executed to completion against the live local
environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). **This case requires `add-data-testid` work** — 6 new
  testids across 2 files (`TriggerTypeSelector.jsx` ×1 — the Schedule edit
  icon, since its Trigger-select sibling already landed;
  `PipelineScheduleModal.jsx` ×5 — modal root, close button, summary text, mode
  radio `testId` prop, cron input, apply/cancel buttons) — see Concrete Handles
  for exact wiring points and line numbers. The Default-mode period/day/hour/
  minute selects need ZERO new work — they already carry stable, semantic
  testids from the `react-js-cron` npm package itself.
- Reuse, don't rebuild: `PipelineDetailPage.add_node()`, `.get_entrypoint_node_id()`,
  `.save_and_wait_for_update()` all already exist. **`pipeline-trigger-select`
  is already landed on `automation/testids`** (confirmed live this session,
  added by ELITEA-2006's implementer) — this case's implementer opens the
  Trigger select and clicks `select-option-schedule` exactly as ELITEA-2005's
  AFS already specs, no new work for that part.
- **MULTI-select discipline (critical, confirmed live) — the hour and minute
  Default-mode selects (`custom-select-hours`, `custom-select-minutes`) are
  ant-design multi-selects, not single-value dropdowns.** Their default value
  (`00` for both) is NOT replaced by clicking a new option — it is ADDED.
  To reach a single target value (e.g. `09` for hour), click the target value
  THEN click the previously-selected value again to deselect it. Leaving
  multiple values selected on EITHER field while the other field is narrow
  triggers the "Frequency cannot be less than every hour" validation message
  (correct behavior, not a bug — see Known Findings).
- **Scoping gotcha this discovery surfaced**: ant-design (`antd`) `Select`
  dropdown option-lists, once opened, stay mounted in the DOM (with a
  `-hidden` class) after closing rather than unmounting — a blind
  `document.querySelectorAll('.ant-select-item-option')` (or an unscoped
  Playwright locator) across MULTIPLE such selects on the same page can match
  a STALE, no-longer-visible list from a previously-opened dropdown instead of
  the currently-open one. Scope every interaction to the one dropdown that is
  actually open (e.g. Playwright: assert the specific `custom-select-hours`/
  `custom-select-minutes` combobox is `aria-expanded="true"` before acting, or
  chain off the freshly-clicked trigger's own popper reference — never a
  page-wide `get_by_text()` across all option lists at once).
- **Escape key closes the WHOLE modal, not a nested dropdown** — confirmed live
  (pressing Escape while a period/hour/minute dropdown was open closed the
  entire Schedule settings modal and reverted the Trigger select to "Chat
  Message," since Apply had not yet been clicked). Never use Escape as a
  "close this dropdown" action inside this modal; click elsewhere in the modal
  body instead, or simply let the next click transfer focus.
- Wait strategy: **never assert the Trigger select's displayed text on the
  same tick as the Apply click** — poll (Playwright auto-retrying
  `expect(locator).to_have_text("Schedule")`) per the toast-vs-display-update
  lag ELITEA-2005's AFS already documented for this exact shared mechanism.
  For the post-reload persistence check, wait for the entry-point select's
  `GET .../pipeline_trigger/.../trigger` response (or general network-idle)
  before reading its text.
- New page-object surface: this case shares `PipelineDetailPage` with
  ELITEA-2005/2006 — a small set of methods to open/read/select the Trigger
  select (if not already added by whichever of the three cases implements
  first) plus Schedule-modal-specific helpers: wait-for-visible via
  `pipeline-schedule-modal`, read the summary text, toggle Default/Advanced,
  interact with the period/hour/minute selects (respecting the multi-select
  discipline above), read/set the Advanced cron text, click Apply/Cancel.
  **Sequence implementer dispatches** so whichever of ELITEA-2005/2006/2007
  lands first does the shared `pipeline-trigger-select` + page-object
  scaffolding work and the others reuse it.
