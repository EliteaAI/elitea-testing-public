# Test Case: Entry Point Node — Schedule Trigger Settings Modal

## Metadata
- **TMS ID**: ELITEA-2007
- **Priority**: l3 (medium — see ELITEA-2005 AFS Metadata for the medium→p2 convention citation)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2005/2006/2008)
- **Status**: ready-for-automation
- **surface_key**: `pipeline-entry-point-trigger`

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with an entry point node and no HITL/Printer/interrupts — satisfied by
  `pipeline_with_llm_id` (same as ELITEA-2005/2006).

## Test Data
| Field | Value |
|-------|-------|
| Hour | 09 |
| Minute | 30 |
| Expected summary (daily) | `At 09:30` — **NOT** the case's own literal "At 09:30, every day"; see CLARIFICATION below |

**CLARIFICATION on Test Data (case-text drift, not a defect) — already filed as
[EliteaAI/elitea-testing-public#1013](https://github.com/EliteaAI/elitea-testing-public/issues/1013)
(found by a prior analysis pass on this exact case; cross-checked and confirmed consistent with
this session's own live observation of the summary re-deriving dynamically, though this session
did not itself pin the exact final string before moving on to the multi-select interaction
finding — see § Test Steps step 5). Two points, both from #1013, both incorporated directly into
this AFS's own assertions (not re-argued here):**
1. **The summary's exact live string for Every=day, 09:30 is `At 09:30` — no `, every day` suffix.**
   The qualifier clause only appears when it disambiguates a non-daily period (e.g. the modal's
   own default, Every=week/SAT, reads "At 00:00, only on Saturday"); for the daily period there is
   nothing left to disambiguate, so the formatter correctly omits it. This AFS's own step 5
   asserts the CORRECT live string, not the case's stale one, per the reverse-masking guard.
2. The default cron on a freshly-created pipeline is `0 0 * * 6` (`PipelineScheduleModal.jsx`'s
   hardcoded `PipelineCronDefault`) — "Every **week** on **SAT** at 00:00", **not** "Every day".
   The case's step 4 ("Change 'Every' to 'day'") is phrased as if starting from a daily default,
   but is actually the FIRST switch into "day" from the real "week" default — doesn't block or
   alter any step, just means the "before" state in a screenshot/assertion is "week"/"SAT".

## Test Steps

1. Use `pipeline_with_llm_id` (single LLM-node pipeline). Navigate to detail page, wait for
   canvas, click the "LLM 1" node.
   - **Verify**: pipeline ready with single entry point node.
2. Select "Schedule" from the Trigger dropdown.
   - **Verify (network)**: `PUT .../pipeline_trigger/.../trigger` fires with `type: "schedule"`
     — confirmed live this does NOT require the same URL/secret two-wave settle as Webhook (no
     secret/URL generation involved for Schedule), so the modal opens with ALL its fields present
     immediately — no analogous timing gap to ELITEA-2006's.
3. Verify the "Schedule settings" modal (`role="dialog"`) opens with: Summary line, Mode radio
   (Default/Advanced), Default mode fields (Every dropdown, on dropdown, at hour:minute), Helper
   text, Cancel/Apply buttons.
   - **Verify (all present immediately, confirmed live)**: Summary line reads "At 00:00, only on
     Saturday" (the default cron's rendering). Mode radio shows "Default"/"Advanced" (radio group
     — **CLARIFICATION**: the modal source passes a `label="Schedule Type"` prop to
     `Checkbox.RadioButtonGroup`, but that component does NOT render/consume a `label` prop at all
     (confirmed via source read — `RadioButtonGroup.jsx` destructures `value, defaultValue,
     onChange, items, wrapRow, columnGap, disabled, testId` only) — so the radio group renders
     with NO visible group heading, just the bare "Default"/"Advanced" options; this is a silent
     prop-drop, not something the case's own Pass/Fail criteria requires, so not filed as a
     defect against this case, but worth noting since automation should locate the radio group by
     its two option labels, not by any "Schedule Type" text). Default-mode fields: "Every"
     dropdown (ant-design `react-js-cron-select`, showing "week"), "on" dropdown (showing "SAT",
     visible only while Every="week"), "at" hour:minute pickers (showing "00"/"00"). Helper text:
     "minute - hour - day (month) - month - day (week)". Cancel/Apply buttons present.
4. Change "Every" to "day" — verify "on" field hides.
   - **Verify**: confirmed live — the `.react-js-cron-select` count inside the modal drops from 4
     (week/SAT/hour/minute) to 3 (day/hour/minute) the instant "day" is selected; the "on" (day-of-
     week) selector is entirely removed from the DOM, not merely hidden (confirmed via a
     before/after `.react-js-cron-select` locator count). Summary line updates to "At 00:00" (the
     "only on Saturday" clause drops along with the "on" field).
5. Change hour to "09", minute to "30" — verify summary updates.
   - **IMPORTANT INTERACTION-MODEL FINDING, confirmed live (decisive — read the third-party
     `react-js-cron` library's rendered markup, not assumed from the case text)**: the hour and
     minute "at HH:MM" pickers are **MULTI-SELECT checkbox grids** (a popover grid of 00–23 for
     hour, 00–59 for minute — confirmed via screenshot), **NOT single-value dropdowns**. Clicking
     a new value does not REPLACE the current selection — it ADDS to it (checkbox-toggle
     semantics). Naively clicking "09" without first deselecting "00" (the still-checked default)
     produces a MULTI-hour cron (`at 00,09 : 00`), and the modal surfaces an inline validation
     message ("Frequency cannot be less than every hour") once both hour AND minute end up
     multi-valued — confirmed live, reproduced this exact sequence. **The case's step wording
     ("Change hour to 09, minute to 30") implies a simple replace; the correct live interaction is:
     open the hour popover, click the currently-checked "00" cell to UNCHECK it, then click "09" to
     check it (repeat the same pattern for minute: uncheck "00", check "30")** — this produces the
     clean single-value result the case's Test Data table expects. This interaction-model detail
     is essential for the implementer and is captured as an Automation Hint, not filed as a defect
     (the widget's multi-select capability is an intentional third-party library feature —
     react-js-cron supports comma-separated cron fields by design — the case simply doesn't
     anticipate it).
   - **Verify (once hour/minute correctly single-valued)**: summary line updates dynamically to
     **`At 09:30`** (the CORRECT live string per #1013 — NOT the case's own "At 09:30, every day",
     see § Test Data CLARIFICATION) — confirmed the summary DOES re-derive live off every
     hour/minute change (observed intermediate states "At 00:00 and 09:00" → "At 00:00,09:00 :
     00,30" → clean "09:30" form once both fields are correctly single-valued), satisfying the
     case's core
     assertion that the summary updates dynamically.
6. Switch to "Advanced" mode — verify cron expression input appears.
   - **Verify**: confirmed live — switching to Advanced hides the Default-mode dropdowns/Every-
     field UI entirely and reveals a single text `<input>` pre-filled with the equivalent 5-field
     cron expression (e.g. minute-field `"0,30"`, hour-field `"0,9"` when carried over from a
     dirty multi-valued Default-mode state — confirming the two modes share the SAME underlying
     `cronExpression` string state, they're just two different editors for it). The Summary line
     re-renders based on the raw cron string's validity (an invalid/ambiguous cron shows an error
     message where the summary normally sits — confirmed live: "Frequency cannot be less than
     every hour" rendered in the summary's position when the underlying cron was still the
     dirty 00,09/00,30 combination from step 5's demonstration of the multi-select pitfall).
7. Switch back to "Default" — verify dropdowns return.
   - **Verify**: confirmed live — switching back to Default re-renders the Every/on/hour/minute
     dropdown UI, re-parsed from the SAME `cronExpression` string (no data loss switching modes
     either direction — confirmed both directions this session).
8. Click "Apply" — verify modal closes, Trigger shows "Schedule".
   - **Verify**: modal closes (`role="dialog"` count → 0). Trigger combobox reads "Schedule" —
     **NOTE the same immediate-read staleness risk documented in the ELITEA-2005/2006 AFS's
     shared § Quirks applies here too** (confirmed live this session: an immediate post-Apply read
     showed the STALE pre-change value once, in one of the two runs performed — prefer asserting
     via the icon-button presence, `role="dialog"` closure, or a reload, over a bare immediate
     `inner_text()` read, for maximum reliability).
9. Save pipeline — reload — verify Schedule trigger persists.
   - **CLARIFICATION (same reverse-masking note as ELITEA-2005/2006)**: no meaningful pipeline
     "Save" action exists for trigger state; reload directly.
   - **Verify**: after reload, Trigger combobox reads "Schedule" — confirmed live,
     `TRIGGER_AFTER_RELOAD == "Schedule"`. Additionally confirmed: clicking the small clock icon
     that renders next to the Trigger combobox (visible only while `currentTriggerType ===
     "schedule"`) reopens the Schedule modal showing "Schedule settings" with the saved cron —
     round-tripping the actual cron value, not just the trigger-type string.

## Expected Results
- The Schedule settings modal opens with all fields present immediately (no timing gap, unlike
  the Webhook modal).
- Default mode's Every/on/hour/minute controls are all live third-party-library
  (`react-js-cron`) widgets — the day-of-week "on" selector conditionally hides for `day`/`hour`/
  `minute` frequencies; hour/minute are MULTI-SELECT checkbox grids, not single-value dropdowns.
- The Summary line re-derives dynamically from the underlying cron string on every field change,
  in both Default and Advanced mode.
- Advanced mode exposes the raw cron string via a single text input; switching modes preserves
  the underlying value both directions.
- Apply persists the schedule; it survives a full page reload, and the saved cron round-trips
  correctly back into the modal on reopen.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with entry point, no HITL/Printer/interrupts | setup exists | step 1 | step 1 | asserted |
| 1 Create pipeline with entry point node | Pipeline ready | step 1 | step 1 | asserted — via fixture |
| 2 Select "Schedule" from Trigger dropdown | Dropdown updates to Schedule | step 2 | step 2 | asserted |
| 3 Verify Schedule settings modal opens with all listed elements | All elements present | step 3 | step 3: full field inventory, present immediately | asserted — **CLARIFICATION: the "Mode radio" has no visible "Schedule Type" group heading due to a silently-dropped `label` prop — not required by the case's own criteria, noted for awareness, not filed** |
| 4 Change "Every" to "day" — "on" field hides | "on" hidden for daily | step 4 | step 4: `.react-js-cron-select` count | asserted |
| 5 Change hour/minute — summary updates | Summary reflects new schedule | step 5 | step 5: summary text after correct single-value interaction | asserted — **CLARIFICATION: hour/minute widgets are multi-select checkboxes, not simple dropdowns — the case's "change hour to 09" wording implies a replace; correct live interaction requires deselecting the prior value first. Documented as an Automation Hint, not a defect (intentional third-party widget capability).** |
| 6 Switch to "Advanced" — cron input appears | Cron text input shown | step 6 | step 6: input presence + value | asserted |
| 7 Switch back to "Default" — dropdowns return | Default dropdowns restored | step 7 | step 7: dropdown presence | asserted |
| 8 Click "Apply" — modal closes, Trigger shows "Schedule" | Modal closes, Schedule shown | step 8 | step 8 | asserted — noted immediate-read staleness risk |
| 9 Save — reload — Schedule trigger persists | Trigger persists | step 9 | step 9: post-reload combobox + modal reopen | asserted — same "Save" clarification as ELITEA-2005/2006 |
| Expected Final State: Default/Advanced modes work, summary updates dynamically, persists after reload | — | steps 3–9 | steps 3–9 | asserted |
| Pass/Fail: all steps complete without errors; modal elements present, summary updates, persists | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 5 documents the multi-select checkbox mechanics of the hour/minute pickers in detail,
  including the exact validation-message trigger condition (`"Frequency cannot be less than
  every hour"`) — *added because this is THE single highest-risk step in the whole case for a
  flaky/wrong automated implementation: a naive "click 09, click 30" sequence silently produces a
  multi-valued cron and an inline error, not the clean single-value result the case's Test Data
  table expects, and nothing about the case text signals this. Confirmed via decisive source-level
  investigation (screenshot showing the checkbox grid) after two failed naive attempts this
  session — recording it here saves the implementer from repeating that exact debugging loop.*
- Step 3's radio-group `label` prop drop is recorded as a CLARIFICATION directly in the Coverage
  Map rather than filed as a ticket — *the case's own Pass/Fail criteria doesn't require a visible
  group heading (it says "Mode radio (Default/Advanced)", which the live product satisfies via
  the two option labels alone), so this doesn't block or alter the case; recorded for awareness
  per the reverse-masking guard, since it IS a genuine (if very minor) prop-plumbing bug in the
  source (`label="Schedule Type"` passed but never consumed).*

## Cleanup

1. All pipelines created via `pipeline_with_llm_id` (function-scoped, auto-deletes in teardown).
   No manual cleanup needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Trigger combobox | see ELITEA-2005 § Concrete Handles (shared) | same |
| Modal root | `[role="dialog"]` | `Modal.BaseModal` already accepts a top-level `data-testid` prop (confirmed via source read, same as the Webhook modal) — recommend `pipeline-schedule-settings-modal`. |
| Mode radio group (Default/Advanced) | `dialog.get_by_text("Default", exact=True)` / `dialog.get_by_text("Advanced", exact=True)` — confirmed reliable by visible text (no group heading exists to scope by, see § Known Defects) | **NO `data-testid`.** `Checkbox.RadioButtonGroup` already accepts `testId` (same plumbing as the Webhook modal's type radios) — recommend `testId="pipeline-schedule-mode-radio"` at the call site, auto-deriving `pipeline-schedule-mode-radio-default`/`-advanced`. |
| Summary line | `dialog.locator("h6, [class*=headingSmall]").first` (the `Typography variant="headingSmall"` rendering `cronState.message`) — confirmed present as the first text block in the modal content | **NO `data-testid`.** Recommended: `pipeline-schedule-summary-text`. |
| "Every" / "on" ant-design selects | `dialog.locator(".react-js-cron-select")` — 4 elements when "on" is visible (week/on/hour/minute), 3 when hidden (day-or-finer/hour/minute); DOM order confirmed stable | **Third-party widget (`react-js-cron`, ant-design internals) — sanctioned #579 raw-handle exception.** No app testid possible on the library's internal `.ant-select`/`.react-js-cron-select` nodes; the `.react-js-cron-select` CSS class IS the stable scoped handle, chained off the modal's own root (which itself should get a `data-testid` per above) — this satisfies the #579 discipline (parent has a real testid once added, raw handle scoped to it). |
| "at" hour/minute multi-select popovers | Opened via clicking the currently-shown hour/minute text (e.g. `page.get_by_text("00", exact=True).first`); grid cells are plain text nodes ("00".."23" for hour, "00".."59" for minute) inside the opened popover, NOT `.ant-select-item-option` (that class is for the Every/on ant-selects only — confirmed live these are a DIFFERENT sub-widget within `react-js-cron`) | Same #579 third-party exception as above — no app testid possible; scope interactions to the open popover container (`page.locator('[role="presentation"]').last` immediately after the click that opens it, to avoid cross-matching stray "00"/"09" text elsewhere on the page). |
| Advanced-mode cron text input | `dialog.locator("input")` — the sole non-radio input when in Advanced mode | **NO `data-testid`.** `FormInput` used here too — same `inputProps={{'data-testid': ...}}` fix as the Webhook modal's URL/Secret fields. Recommended: `pipeline-schedule-cron-input`. |
| Cancel / Apply buttons | `dialog.get_by_role("button", name="Cancel"/"Apply")` | **CORRECTED 2026-08-04 (post implementation):** same as the Webhook modal — `PipelineScheduleModal.jsx` passes a custom `actions={<Box>...</Box>}` block to `Modal.BaseModal`, bypassing `cancelButtonTestId`/`confirmButtonTestId` entirely. `data-testid="pipeline-schedule-modal-cancel-button"`/`"pipeline-schedule-modal-apply-button"` are wired directly onto the two custom `Button` elements inside that `actions` block instead. |
| Schedule-edit clock icon (post-Apply, next to Trigger combobox) | `node.locator("button").last` scoped to the entry point node — present only while `currentTriggerType === "schedule"` (confirmed via source read of `TriggerTypeSelector.jsx`'s conditional render) | **NO `data-testid`.** Recommended: `pipeline-entry-point-trigger-schedule-edit-button`. |

## Network Behavior

- `PUT .../pipeline_trigger/.../trigger` (body `type: "schedule"`) — fires on initial Schedule
  selection; unlike Webhook, no secret/URL generation is involved, so the modal's own fields don't
  depend on a follow-up GET to populate (confirmed live: no analogous timing gap).
- Changing Every/on/hour/minute/cron-text produces NO network traffic — confirmed live, purely
  client-side `cronExpression` state managed by the `react-js-cron` library + the modal's local
  `cronType` state.
- Apply fires a SECOND `PUT .../trigger` with `type: "schedule"`, `cron: {finalCronExpression}`,
  `timezone: {browser Intl timezone}` (confirmed via the `handleScheduleSubmit` source read).

## Known Defects Found During Exploration

**None filed as `bug`.** All 9 case steps produced the expected observable end-to-end (once the
multi-select hour/minute interaction is driven correctly — see § Coverage Map row 5). Zero console
errors observed. Zero failed (≥400) network requests observed.

**Two CLARIFICATIONs worth filing** (light, non-blocking — per `.agents/profile.md` § Bug filing
routing):
1. The Mode radio group's `label="Schedule Type"` prop is silently dropped by
   `Checkbox.RadioButtonGroup` (component doesn't consume a `label` prop) — the group renders with
   no visible heading. One-line fix candidate for the dev team (either wire the prop through or
   remove the dead prop pass), does not affect any case's Pass/Fail criteria.
2. The hour/minute "at HH:MM" pickers' multi-select checkbox semantics are not signposted in any
   way (no helper text, no visual affordance distinguishing them from a simple dropdown) and
   silently produce an inline error ("Frequency cannot be less than every hour") if a user clicks
   a new value without first deselecting the old one — a plausible real-user confusion point, not
   just an automation-authoring trap. Worth a UX note to the team; does not fail this case since
   the correct (uncheck-then-check) interaction does produce the expected result.
Both filed as issues — see reference once created by the orchestrator per the seeded bug-filing
policy (this analyst session did not file directly — see notes for routing, same as ELITEA-2006).

## ⚠️ Prior Work Discovered Mid-Session — orchestrator attention needed

**A complete, working, previously-reviewed automation implementation for this exact cluster
already exists in this repo's git history, but is NOT reachable from the current tip of
`origin/automation/base`.** Discovered while dedup-checking before filing a defect (found
issues #1006/#1009/#1013/#1021 already filed against this exact surface by a prior pass) —
followed the trail into `gh pr list --search trigger` and confirmed via `git merge-base
--is-ancestor`:

| Case | PR | State | Base (per GitHub) | Merge commit | Reachable from current `origin/automation/base`? |
|---|---|---|---|---|---|
| ELITEA-2006 | [#1015](https://github.com/EliteaAI/elitea-testing-public/pull/1015) | MERGED (2026-07-24) | `automation/base` | `32fb6fe4` | **NO** |
| ELITEA-2005 | [#1022](https://github.com/EliteaAI/elitea-testing-public/pull/1022) | MERGED (2026-07-24) | `tests/ELITEA-2006-webhook-trigger-settings-modal` (stacked) | `29333bd8` | **NO** |
| ELITEA-2007 | [#1038](https://github.com/EliteaAI/elitea-testing-public/pull/1038) | **CLOSED, not merged** (2026-07-29) | `tests/ELITEA-2005-entry-point-trigger-types` (stacked) | — | N/A — never merged |
| ELITEA-2008 | none found | — | — | — | no prior PR located |

PR #1015's own GitHub metadata says its base was `automation/base`, yet its merge commit is
**not** an ancestor of the CURRENT `origin/automation/base` tip (`68e8f6f4`, 2026-08-03) — it
IS reachable from `origin/automation/base-merged` (a separate, older, diverged branch,
`a895133d`, 2026-07-24) and two unrelated feature branches. This strongly suggests
`automation/base`'s history was rewritten/reset at some point after 2026-07-24, orphaning at
least these two merged PRs (and possibly others merged in the same window) — a serious finding
given `.agents/workflow.md` documents `automation/base` as long-lived and never force-pushed.
**This analyst session did not attempt any git-history recovery or investigation beyond
confirming the above — that is squarely an orchestrator/lead-level decision, not an analyst
one.**

**Why this AFS still classifies `ready-for-automation` rather than `already-covered`**: per this
session's own contract, `already-covered`/`extend-existing` may target ONLY a spec/test merged
to the CURRENT `origin/automation/base` (or, for `extend-existing`, this batch's own trunk) — the
orphaned PRs satisfy neither, so the strict rule is followed and this case proceeds as fresh
`ready-for-automation` work. **But dispatching an implementer to redo this from scratch, without
first checking whether PRs #1015/#1022's actual code can simply be recovered and re-merged
(`git cherry-pick 32fb6fe4`/`29333bd8` onto a fresh `automation/base`-rooted branch, or a direct
branch-history investigation), risks pure duplicated effort for ELITEA-2005/2006** — both PRs'
own descriptions indicate essentially complete, testid'd, reviewed implementations covering the
same case observables this AFS documents. ELITEA-2007's closed PR #1038 also contains a
substantially complete implementation (same multi-select-checkbox finding this AFS independently
rediscovered live) that was abandoned only because its branch stack rested on the now-orphaned
ELITEA-2005 branch — recovering it may be far cheaper than a fresh implementation. ELITEA-2008
appears to have no prior implementation attempt.

**Recommendation for the orchestrator**: before dispatching implementers for this cluster,
have someone (lead or a dedicated git-recovery task) investigate why `automation/base` lost
these commits and whether `32fb6fe4` (ELITEA-2006), `29333bd8` (ELITEA-2005), and PR #1038's
branch tip (ELITEA-2007, closed but not deleted — check `tests/ELITEA-2007-schedule-trigger-settings-modal`
or similar for the actual head ref) can be cherry-picked/rebased onto current `automation/base`
directly, which would likely be far cheaper than fresh implementation for 3 of the 4 cases in
this cluster.

## Blocked Steps

None. All 9 case steps were executed to completion against the live local environment.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. **Requires `add-data-testid`
  work** — see § Concrete Handles (Mode radio via existing `testId` prop plumbing on
  `Checkbox.RadioButtonGroup`; Summary/cron-input via a bare/`inputProps` `data-testid`; modal
  root via `Modal.BaseModal`'s existing `data-testid` prop). **Correction (2026-08-04, post
  implementation):** Cancel/Apply do NOT go through `Modal.BaseModal`'s testid props — see §
  Concrete Handles — they're wired directly on the custom `actions` block's `Button` elements.
  The `.react-js-cron-select` / hour-minute-popover elements are the #579 sanctioned third-party
  exception — no testid work needed or possible there, scope raw handles to the (testid'd) modal
  root.
- **The single most important automation-authoring detail in this case**: to set hour/minute to a
  SPECIFIC single value, first click the currently-checked cell to UNCHECK it, THEN click the
  target cell to check it — for both hour and minute independently. Recommend a page-object
  method `set_schedule_hour_minute(page, dialog, hour: str, minute: str)` that encapsulates this
  uncheck-then-check sequence, rather than leaving every call site to rediscover it.
- Use `pipeline_with_llm_id` (existing fixture). No new fixture needed.
- Suggested pytest markers: `@pytest.mark.p2`, `@pytest.mark.pipelines`, `@pytest.mark.regression`.
- Shares Trigger-combobox mechanics with ELITEA-2005/2006 — see ELITEA-2006's Automation Hints
  for the shared-helper suggestion (applies here too, minus the Webhook-specific settle-wait,
  which this modal doesn't need).
