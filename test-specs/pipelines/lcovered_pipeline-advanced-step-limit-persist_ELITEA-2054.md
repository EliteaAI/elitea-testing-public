# Test Case: Pipeline — Advanced Settings (Step Limit)

## Metadata
- **TMS ID**: ELITEA-2054
- **Linked Story**: none
- **Priority**: l2 (per source case's `medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-09
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline is open for editing.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/pipelines/test_pipeline_create_full_details_persist.py`
(TMS ELITEA-2021, AFS
`test-specs/pipelines/l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`),
merged to `origin/automation/base` at commit `2ff0fc96`
("test: (ELITEA-2021) pipeline create full-details persist-after-reload").

**Re-confirmed live this session** (2026-08-09, same repo state, localhost:5173):

```
cd automation && HEADLESS=true ../.venv/bin/pytest tests/ui/pipelines/test_pipeline_create_full_details_persist.py -v -p no:cacheprovider
...
tests/ui/pipelines/test_pipeline_create_full_details_persist.py::test_create_pipeline_full_details_persist_after_reload PASSED [100%]
============================== 1 passed in 41.94s ==============================
```

**Behavioural-equivalence argument.** ELITEA-2054 asks for exactly one observable:
the ADVANCED section's Step limit field accepts a non-default value, the value shows
in the field, Save succeeds without error, and the value survives a full page reload.
`test_pipeline_create_full_details_persist.py` exercises this identical mechanism —
same field (`pipeline-step-limit-input` / `PipelineDetailPage.step_limit_input`, same
`fill_step_limit()`/`get_step_limit()` methods ELITEA-2054's implementer would have
had to write from scratch), same screen (`ApplicationAdvanceSettings.jsx` via
`PipelineConfigurationForm.jsx`), same Save→reload→re-read round trip — differing only
in the literal chosen value (`"50"` there vs. the case text's `"10"` here), which is
not a distinguishing observable: the field is a generic numeric input
(`min=0 max=999`), and nothing about the mechanism depends on which non-default digit
string is typed.

| ELITEA-2054 step | Covered by (`test_pipeline_create_full_details_persist.py`) |
|---|---|
| 1. Open a pipeline → loaded in the editor | Steps 1–2, `:70-77` — navigates to the create form, then Step 9 (`:104-113`) Saves to obtain a real pipeline id and lands on the detail page |
| 2. Expand "Advanced" section → visible | Not clicked in either spec — confirmed live + in `test-specs/pipelines/_surface.md` § "Quirks observed live" that ADVANCED renders `aria-expanded="true"` by default, so no expand action is a step either case needs |
| 3. Locate "Step limit" field → visible | `pipeline_page.step_limit_input` (`LocatorDescriptor(testid="pipeline-step-limit-input")`, `automation/pages/pipeline_detail_page.py:1388-1391`) — resolved and interacted with at `:101` |
| 4. Change value from default ("25") to "10" → field shows "10" | `:100-102` — `fill_step_limit(_STEP_LIMIT)` then `assert pipeline_page.get_step_limit() == _STEP_LIMIT` (covering spec's `_STEP_LIMIT = "50"`; same field, same change-from-default mechanism, different literal digit string) |
| 5. Save pipeline → saves without errors | `:104-113` — `save_and_wait_for_creation()` asserts a 2xx create response and `assert not console_errors` |
| 6. Reload page → page reloads | `:130-134` — `page.goto(canonical_url)` + `wait_for_detail_page_load()` |
| 7. Verify Step limit shows "10" → persisted | `:150` — `assert pipeline_page.get_step_limit() == _STEP_LIMIT, "Step limit should persist after reload"` |

**Scope note (no gap, so no `extend-existing`).** The covering spec's Save→reload
happens after a SECOND save (Step 12, toolkit attach + editor notes), one save-cycle
further than ELITEA-2054's own single-save flow — but Step limit is asserted
unchanged across BOTH saves (`:102` immediately after typing, `:150` after the second
save + reload), so the covering spec's evidence is strictly stronger, not narrower,
than what ELITEA-2054 asks for. No missing assertion.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open a pipeline — Pipeline is loaded in the editor
2. Expand "Advanced" section in left panel — Advanced section is visible
3. Locate "Step limit" field (textbox with info tooltip icon) — Step limit field is visible
4. Change value from default (e.g., "25") to "10" — Step limit field shows "10"
5. Save pipeline — Pipeline saves without errors
6. Reload page — Page reloads
7. Verify Step limit field shows "10" — Step limit is persisted as "10" after reload

## Expected Results
- Changing the Step limit field to a non-default value, saving, and reloading
  correctly persists the new value — proven live by
  `test_pipeline_create_full_details_persist.py` (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open pipeline | loaded in editor | `test_pipeline_create_full_details_persist.py` Steps 1–2, 9 | `:70-77`, `:104-113` | already-covered |
| Step 2 — expand Advanced section | section visible | expanded by default, no click needed (confirmed in `_surface.md`) | n/a | already-covered |
| Step 3 — locate Step limit field | field visible | `step_limit_input` `LocatorDescriptor` | `pipeline_detail_page.py:1388-1391` | already-covered |
| Step 4 — change value to "10" | field shows "10" | same, Step 8 | `:100-102` | already-covered |
| Step 5 — save, no errors | saves without errors | same, Step 9 | `:104-113` | already-covered |
| Step 6 — reload page | page reloads | same, Step 13 | `:130-134` | already-covered |
| Step 7 — verify "10" persisted | value persisted | same, Step 13 | `:150` | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`'s Coverage
  Map) — none needed here.

## Cleanup
N/A — no new test written; nothing new to clean up. Covering spec's own `finally`
block deletes its pipeline via `pipeline_api.delete_pipeline(pipeline_id)`
(`:154-159`).

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `step_limit_input`
(`testid="pipeline-step-limit-input"`, `automation/pages/pipeline_detail_page.py:1388-1391`,
present on `automation/testids`, **not yet on `main`** — confirmed via fresh
`git fetch origin` + `git grep` this session, added by ELITEA-2021's
`add-data-testid` work) + `fill_step_limit()`/`get_step_limit()`
(`pipeline_detail_page.py:5588-5609`). No new handles needed for this
traceability pass.

## TMS linkage
Link ELITEA-2054 to ELITEA-2021 in the TMS (both ways) so the audit trail resolves:
ELITEA-2054's `already-covered` disposition points at ELITEA-2021's automated test;
ELITEA-2021's case gains a "also satisfies ELITEA-2054" back-reference.
