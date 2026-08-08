# Test Case: Pipeline — Version Dropdown and Switch

## Metadata
- **TMS ID**: ELITEA-2063
- **Linked Story**: none
- **Priority**: l2 (per source case; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-08
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline with multiple saved versions (including "base") exists.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/pipelines/test_pipeline_create_version.py`
(TMS ELITEA-2002, AFS `test-specs/pipelines/l2_create-pipeline-version_ELITEA-2002.md`),
merged to `origin/automation/base` at commit `ed51edab`
("test: (ELITEA-2002) batch elitea-2002 — Create Pipeline Version (#1308)").

**Re-confirmed live this session** (2026-08-08, same repo state, localhost:5173):

```
cd automation && HEADLESS=true ../.venv/bin/pytest tests/ui/pipelines/test_pipeline_create_version.py -v -p no:cacheprovider
...
tests/ui/pipelines/test_pipeline_create_version.py::test_create_pipeline_version_save_list_switch_preserves_canvas_state PASSED [100%]
============================== 1 passed in 51.69s ==============================
```

**Behavioural-equivalence argument.** ELITEA-2063's seven steps ask for exactly the
observable `test_pipeline_create_version.py` already asserts, step for step, against
the same shared components (`ApplicationVersionSelect.jsx`, `SaveNewVersionButton.jsx`,
`ApplicationInformation.jsx`) on the same pipeline-detail screen:

| ELITEA-2063 step | Covered by (`test_pipeline_create_version.py`) |
|---|---|
| 1. Open a pipeline with multiple versions → selector visible | Step 1, `automation/tests/ui/pipelines/test_pipeline_create_version.py:58-71` — navigates to the fixture pipeline's canvas and asserts the VERSION selector renders |
| 2. VERSION combobox shows "base" | `test_pipeline_create_version.py:62-65` — `assert pipeline_page.get_version_display() == "base"` |
| 3. Click the combobox → dropdown opens listing all versions | `test_pipeline_create_version.py:129-140` (Step 4) — `open_version_selector()` then `is_version_option_visible("base")` and `is_version_option_visible(VERSION_NAME)` both assert True |
| 4. Select a different version → selected name appears in the combobox | `test_pipeline_create_version.py:157-164` (Step 6) — `select_version_by_name(VERSION_NAME)` then `assert pipeline_page.get_version_display() == VERSION_NAME` |
| 5. Canvas updates to the selected version's topology | `test_pipeline_create_version.py:165-168` — `wait_for_node_type_count("llm", 1, ...)` after switching to `v1_test`; and `test_pipeline_create_version.py:150-155` (Step 5) — `wait_for_node_type_count("llm", 0, ...)` after switching to `base` — proves the canvas topology follows the selected version in both directions |
| 6. Information-section Version ID updates | `PipelineDetailPage.get_version_id()` (`automation/pages/pipeline_detail_page.py:1372-…`) is documented "Read the Version ID from the Information section" and is the exact value asserted at `test_pipeline_create_version.py:119-122` (`new_version_id != previous_version_id`), `:150` (`base_version_id == previous_version_id`), and `:165` (`v1_version_id == new_version_id`) |
| 7. Switch back to "base" → original topology restored | `test_pipeline_create_version.py:142-155` (Step 5) — switches to `base`, asserts the selector text, the Information-panel version id (`base_version_id == previous_version_id`, i.e. a true revert not a new version), and `wait_for_node_type_count("llm", 0, ...)` |

The covering spec additionally proves the version-id equality is a real reconciliation
(not a coincidental same-value poll) via `select_version_by_name()`'s belt-and-braces
reload cycle — documented in `test-specs/pipelines/_surface.md` § "Save As Version
(`agent-save-as-version-button` + dialog) works on Pipelines exactly like Agents", which
also records the live-confirmed no-cross-version-leakage behaviour ELITEA-2063's steps
5–7 exercise. Same screen, same page-object methods (`open_version_selector`,
`is_version_option_visible`, `select_version_by_name`, `get_version_display`,
`get_version_id`), same expected results — this is the case's own observable, already
proven, not a similar-looking neighbour.

**Scope note (no gap, so no `extend-existing`).** ELITEA-2002's fixture pipeline only
ever holds two versions ("base" + "v1_test"), while ELITEA-2063's precondition text says
"multiple saved versions" generically — but the assertions exercised (dropdown listing
membership, selector text, canvas topology, Information-panel Version ID, round-trip
revert) are identical regardless of how many versions exist beyond two; a third/fourth
version would exercise the same code path with no new observable. Not treated as a gap.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open a pipeline that has multiple versions — Pipeline is loaded with the version selector visible
2. Locate "VERSION:" label and the version combobox (e.g., showing "base") — Version combobox is visible showing "base"
3. Click the version combobox to open dropdown — Dropdown opens with all available versions listed
4. Select a different version — Selected version name appears in the combobox
5. Verify canvas updates to show the node topology of the selected version — Canvas displays the nodes/edges for the selected version
6. Verify version ID in Information section updates — Information section shows the new version's ID
7. Switch back to "base" — verify original topology is restored — Canvas restores the base version node topology

## Expected Results
- Switching versions via the dropdown correctly updates the canvas to show the
  selected version's topology and the Version ID in the Information section updates
  accordingly — proven live by `test_pipeline_create_version.py` (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open multi-version pipeline, selector visible | selector visible | `test_pipeline_create_version.py` Step 1 | `:58-71` | already-covered |
| Step 2 — combobox shows "base" | shows "base" | same | `:62-65` | already-covered |
| Step 3 — open dropdown, lists all versions | dropdown lists all versions | same, Step 4 | `:129-140` | already-covered |
| Step 4 — select different version, name appears | combobox shows new name | same, Step 6 | `:157-164` | already-covered |
| Step 5 — canvas shows selected version's topology | canvas matches version | same, Steps 5+6 | `:150-155`, `:165-168` | already-covered |
| Step 6 — Information-section Version ID updates | ID updates | same, Steps 3/5/6 | `:119-122`, `:150`, `:165` | already-covered |
| Step 7 — switch back to base, topology restored | base topology restored | same, Step 5 | `:142-155` | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_create-pipeline-version_ELITEA-2002.md`'s Coverage Map) — none needed here.

## Cleanup
N/A — no new test written; nothing new to clean up. (Covering spec's own fixture,
`pipeline_id`, creates and deletes its dedicated pipeline per test.)

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — see `l2_create-pipeline-version_ELITEA-2002.md`
§ Concrete Handles and `test-specs/pipelines/_surface.md`. No new handles were needed for
this traceability pass.

## TMS linkage
Link ELITEA-2063 to ELITEA-2002 in the TMS (both ways) so the audit trail resolves:
ELITEA-2063's `already-covered` disposition points at ELITEA-2002's automated test;
ELITEA-2002's case gains a "also satisfies ELITEA-2063" back-reference.
