---
name: Run Details State Before/After — implementation notes (ELITEA-2452)
description: RunStateDialog.jsx/PipelineStateViewModal.jsx testid additions, the fstring-chained-LLM node dict shape that works live, and confirmation of #1271's routing workaround.
type: feedback
---

## Testids added (EliteaAI/EliteaUI@2b40e5a6, automation/testids)

- `ProcessStepIcon`'s outer `Box` (timeline stepper dot) — dynamic,
  `pipeline-run-details-timeline-step-{index}` (keyed by list index, not
  node id).
- `BasicAccordion`'s `items[].testId` — already wired to
  `StyledAccordionSummary`'s `data-testid` (no shared-component change
  needed); `RunStateDialog.jsx` just passes
  `testId: `pipeline-run-details-state-row-${variable}`` in its `items` array.
- `StateItemView`'s two value boxes — new `data-testid` directly on each
  `Box`: `pipeline-run-details-state-value-before-{variable}` /
  `-after-{variable}`.
- `StateItemViewHeader` gained a `testId` prop (threaded from
  `StateItemView`'s two call sites), landing on the fullscreen `IconButton`:
  `pipeline-run-details-state-expand-before-{variable}` / `-after-{variable}`.
- `PipelineStateViewModal.jsx` (zero testids before this case): root testid
  goes directly on `<Dialog data-testid={testId}>` — confirmed working live
  (same MUI-forwards-to-root-wrapper mechanism as
  `basemodal_data_testid_lands_on_wrapper...md`). Header on `DialogTitle`
  (`-header`), close `IconButton` (`-close-button`), `DialogContent`
  (`-content`).
  **CORRECTED in fix round 1 (EliteaUI@0f55411b):** the FIRST-round
  implementation hardcoded these 4 as literal strings directly in
  `PipelineStateViewModal.jsx` (`src/components/`), on the AFS's own
  "single consumer, so it's fine" reasoning. Reviewer flagged it — there is
  **no single-consumer carve-out** in the PR #581 shared-component ruling
  (`.agents/testing.md` § Locator policy / `.agents/role-overrides.md`
  § Reviewer slot). Fixed by adding 4 props (`testId`, `headerTestId`,
  `closeButtonTestId`, `contentTestId`, all `undefined` by default) and
  threading the literal values from `RunStateDialog.jsx`'s call site —
  mirroring the `StateItemViewHeader`/`BasicAccordion` pattern already used
  in the SAME original commit, which is the tell: don't trust "this one's
  different" reasoning inside an AFS when the same diff already shows the
  compliant shape elsewhere. Apply the caller-prop pattern to EVERY
  `src/components/`/`src/[fsd]/shared/` testid up front — never reach for
  "only one consumer today" as a reason to hardcode.

## `create_pipeline_with_nodes` — fstring task + chained LLM->LLM confirmed live

A 2-node `LLM 1 -> LLM 2 -> END` pipeline with `type: fstring` task mappings
(`"User asked: {input}"`, `"Ack: {messages}"`) executes correctly via
`PipelineAPI.create_pipeline_with_nodes()` — no prior fixture in this repo
used `fstring` (all existing node-dict helpers in `data_fixtures.py` use
`fixed`). Node shape: `input_mapping.task = {"type": "fstring", "value":
"...{state_var}..."}`. New fixture: `pipeline_with_two_llm_nodes_id` +
`build_two_llm_nodes()` in `fixtures/data_fixtures.py`.

## #1271 workaround confirmed in a real test run

Asserting "unmodified variable => Before=After" at the pipeline's SECOND
timeline step (not the first) reliably avoids known defect #1271 (Before at
step 0 is hardcoded `''`). Test green on first run with this approach —
`input` @ `LLM2`: Before=After=the chat message text, both non-empty.
