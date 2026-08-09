# Test Case: Pipeline — Editor Notes

## Metadata
- **TMS ID**: ELITEA-2055
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

**Behavioural-equivalence argument.** ELITEA-2055 asks for exactly one observable:
the EDITOR NOTES textbox accepts free text, shows the entered text, Save succeeds
without error, and the text survives a full page reload. `test_pipeline_create_full_details_persist.py`
exercises this identical mechanism — same field (`pipeline-editor-notes-input` /
`PipelineDetailPage.editor_notes_input`, same `fill_editor_notes()`/`get_editor_notes()`
methods ELITEA-2055's implementer would have had to write from scratch), same
accordion (`ApplicationEditorNotes.jsx` via `PipelineConfigurationForm.jsx`, titled
"EDITOR NOTES"), same Save→reload→re-read round trip — differing only in the literal
chosen text (`"Test pipeline for automation"` there vs. the case text's `"This
pipeline is under development. Do not publish."` here), which is not a
distinguishing observable: the field is a generic free-text textarea with no
content-specific validation, and nothing about the persistence mechanism depends on
which string is typed.

| ELITEA-2055 step | Covered by (`test_pipeline_create_full_details_persist.py`) |
|---|---|
| 1. Open a pipeline → loaded in the editor | Steps 1–2, `:70-77` — navigates to the create form, then Step 9 (`:104-113`) Saves to obtain a real pipeline id and lands on the detail page (the EDITOR NOTES section only renders on the detail page — case-text drift already documented in `_surface.md` § "Two distinct pipeline form surfaces", not a defect) |
| 2. Expand "EDITOR NOTES" section → visible | `editor_notes_section.scroll_into_view_if_needed()` at `:145` scrolls the accordion into view; the accordion is confirmed (source read, `_surface.md` § "Confirmed testid gaps") to render inline/visible on the detail page, no separate expand-click required |
| 3. Locate "Notes" textbox → visible | `pipeline_page.editor_notes_input` (`LocatorDescriptor(testid="pipeline-editor-notes-input")`, `automation/pages/pipeline_detail_page.py:1402-1405`) — resolved and interacted with at `:123` |
| 4. Enter text: "This pipeline is under development. Do not publish." → textbox populated | `:122-124` — `fill_editor_notes(_EDITOR_NOTES)` then `assert pipeline_page.get_editor_notes() == _EDITOR_NOTES` (covering spec's `_EDITOR_NOTES = "Test pipeline for automation"`; same field, same fill-and-read mechanism, different literal text) |
| 5. Save pipeline → saves without errors | `:126-129` — `save_and_wait_for_update()` + `assert not console_errors` |
| 6. Reload page → page reloads | `:130-134` — `page.goto(canonical_url)` + `wait_for_detail_page_load()` |
| 7. Verify notes text persists | `:145-152` — `editor_notes_section.scroll_into_view_if_needed()` then `assert pipeline_page.get_editor_notes() == _EDITOR_NOTES, "Editor notes should persist after reload"` |

**Scope note (no gap, so no `extend-existing`).** The covering spec fills Editor
Notes on the SAME save cycle that also attaches a toolkit (Step 11, both under one
Save at Step 12) rather than notes alone — but the two fields are independent
sibling inputs in the same form; attaching a toolkit alongside has no interaction
with the Notes textarea's own fill/save/reload/persist mechanism (confirmed live:
zero console errors, zero unexpected network across the whole run). No missing
assertion for ELITEA-2055's narrower single-field scope.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open a pipeline — Pipeline is loaded in the editor
2. Expand "EDITOR NOTES" section in left panel — EDITOR NOTES section is visible
3. Locate "Notes" textbox (with info tooltip icon) — Notes textbox is visible
4. Enter text: "This pipeline is under development. Do not publish." — Notes textbox is populated with the entered text
5. Save pipeline — Pipeline saves without errors
6. Reload page — Page reloads
7. Verify notes text persists: "This pipeline is under development. Do not publish." — Notes text is correctly restored after reload

## Expected Results
- Entering text in the EDITOR NOTES textbox, saving, and reloading correctly
  persists the text unchanged — proven live by
  `test_pipeline_create_full_details_persist.py` (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open pipeline | loaded in editor | `test_pipeline_create_full_details_persist.py` Steps 1–2, 9 | `:70-77`, `:104-113` | already-covered |
| Step 2 — expand EDITOR NOTES section | section visible | same, Step 13 | `:145` | already-covered |
| Step 3 — locate Notes textbox | textbox visible | `editor_notes_input` `LocatorDescriptor` | `pipeline_detail_page.py:1402-1405` | already-covered |
| Step 4 — enter notes text | textbox populated | same, Step 11 | `:122-124` | already-covered |
| Step 5 — save, no errors | saves without errors | same, Step 12 | `:126-129` | already-covered |
| Step 6 — reload page | page reloads | same, Step 13 | `:130-134` | already-covered |
| Step 7 — verify text persists | text restored unchanged | same, Step 13 | `:145-152` | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`'s Coverage
  Map) — none needed here.

## Cleanup
N/A — no new test written; nothing new to clean up. Covering spec's own `finally`
block deletes its pipeline via `pipeline_api.delete_pipeline(pipeline_id)`
(`:154-159`).

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `editor_notes_section`
(`testid="pipeline-editor-notes-section"`), `editor_notes_input`
(`testid="pipeline-editor-notes-input"`, `automation/pages/pipeline_detail_page.py:1397-1405`,
present on `automation/testids`, **not yet on `main`** — confirmed via fresh
`git fetch origin` + `git grep` this session, added by ELITEA-2021's
`add-data-testid` work) + `fill_editor_notes()`/`get_editor_notes()`
(`pipeline_detail_page.py:5611-5627`). No new handles needed for this
traceability pass.

## TMS linkage
Link ELITEA-2055 to ELITEA-2021 in the TMS (both ways) so the audit trail resolves:
ELITEA-2055's `already-covered` disposition points at ELITEA-2021's automated test;
ELITEA-2021's case gains a "also satisfies ELITEA-2055" back-reference.
