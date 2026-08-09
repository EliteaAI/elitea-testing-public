# Test Case: Pipeline — Unsaved Changes and Discard

## Metadata
- **TMS ID**: ELITEA-2048
- **Linked Story**: none
- **Priority**: l2 (medium — case declares "high" but the flow is a small,
  already-proven-adjacent UI check; keeping the repo's `l2` convention for
  this class of case, same as the sibling `l2_pipeline-*` AFS files this
  session references)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, pipelines-remaining wave-04
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/pipelines/test_pipeline_advanced.py`
  (`TestDiscardChanges::test_discard_reverts_name_change`, PIPE-022 — merged
  to `origin/automation/base` since the initial commit). No AFS exists for
  the covering test (it predates the AFS convention); the "Why extend-
  existing" section below covers what it does and doesn't already prove.

## Why extend-existing, not a fresh spec

The covering test `test_discard_reverts_name_change` already exercises 3 of
ELITEA-2048's 8 steps: navigate to an existing pipeline (step 1), modify the
name (step 3, without asserting the button state change of step 4/5), click
Discard (step 6), and verify the name reverts (step 7). **Confirmed live,
2026-08-09** (ran `test_discard_reverts_name_change` against localhost —
passed clean) — the flow itself is sound and unchanged.

What it does **not** assert at all — the actual core of ELITEA-2048's
objective — is any Save/Discard **button state**: it never checks the
buttons are disabled before the edit, enabled after the edit, or disabled
again after discard. That is a real, complete gap (case steps 2, 4, 5, 8),
and the page object already has everything needed to close it —
`is_save_enabled()` and `is_discard_enabled()` (`PipelineFormPage`) are
pre-existing, already used by `test_pipeline_create_version.py` and
`test_pipeline_yaml_flow_sync.py` for an identical "disabled on a clean
pipeline" baseline check. Zero new page-object work, zero new testids.

Because the button-state checkpoints are *interleaved* with the same
name-change/discard/revert actions the covering test already performs, the
gap can't be split out as an independent assertion tacked onto an unrelated
setup — verifying "Save is enabled" requires actually being in the dirty
state the existing test's own step 3 produces. The correct shape (Rule 7,
same reasoning as the ELITEA-2057/ELITEA-2019 sibling AFS in this feature)
is therefore ONE new, self-contained `test()` appended to
`TestDiscardChanges`, sharing the exact same fixture/navigation/action
methods as the existing test, with the 4 missing button-state assertions
added at their natural points in the sequence. The existing test's body is
left byte-identical (additive-only contract).

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- An existing pipeline is open — reuses the SAME `pipeline_id` fixture
  (data_fixtures.py: `PipelineAPI.create_pipeline()`, zero-node) the covering
  test already uses. **Seeding gotcha (confirmed in `_surface.md`):** this is
  the fixture that loads with Save/Discard correctly **disabled** at
  baseline — `pipeline_with_two_llm_nodes_id`-style multi-node seeding must
  NOT be substituted here, it loads with Save/Discard already enabled on
  first render (auto-layout counts as an unsaved change), which would make
  case step 2's disabled-baseline assertion fail for the wrong reason.

## Test Data
### reuse-existing
- none required beyond the seeded pipeline above; the modified name is a
  disposable literal (`f"{original_name} modified"`), not a fixture.

## Test Steps (gap only — steps 1/3/6/7 already exist as actions in the covering test; this AFS adds the button-state checkpoints and reuses the same actions to reach them)

1. Open an existing pipeline (via `pipeline_id` fixture + `_navigate_to_detail`).
   - **Verify**: page loaded — *already proven by the covering test's own
     step 2 (equivalent navigation); reused here as the entry action, not a
     new assertion.*
2. Verify Save and Discard are initially disabled.
   - **Verify** (NEW): `is_save_enabled() is False` and
     `is_discard_enabled() is False` immediately after navigation — same
     live-confirmed pattern `test_pipeline_create_version.py` step 1 already
     uses on the identical `pipeline_id` fixture.
3. Modify the pipeline name (append " modified").
   - **Verify**: `get_name()` reflects the new value — *same action/
     assertion shape as the covering test's step 3, reused here because the
     button-state checks in steps 4/5 need this dirty state to exist.*
4. Verify Save button becomes enabled.
   - **Verify** (NEW): `is_save_enabled() is True` after the name edit —
     confirmed live this session (2026-08-09): flips true immediately
     following `update_name()` (which already waits for MUI validation
     debounce internally — no extra sleep needed).
5. Verify Discard button becomes enabled.
   - **Verify** (NEW): `is_discard_enabled() is True` after the name edit —
     confirmed live alongside step 4, same timing.
6. Click "Discard" button.
   - **Verify**: `click_discard()` completes (dismisses confirmation dialog
     if one appears, waits for network) — *same action as the covering
     test's step 4, reused here.*
7. Verify pipeline name reverts to original value.
   - **Verify**: `get_name() == original_name` — *same assertion shape as
     the covering test's step 5, re-asserted here as the sequence anchor
     confirming discard actually fired before checking step 8's button
     states (a stale-DOM read would show the OLD dirty-state buttons
     alongside the reverted name, which is exactly the failure step 8
     exists to catch).*
8. Verify Save and Discard return to the disabled state.
   - **Verify** (NEW): `is_save_enabled() is False` and
     `is_discard_enabled() is False` after discard completes — confirmed
     live this session: both flip back to disabled once
     `wait_for_detail_page_load()` settles post-discard.

## Expected Results
- Save and Discard are both disabled on a freshly loaded, unedited pipeline.
- Modifying the name enables both Save and Discard.
- Discard reverts the name to its last-saved value AND disables both
  buttons again — the full round trip, not just the name revert in
  isolation.
- No console errors, no network requests beyond the click-discard settle
  (confirmed live: no `prompt_lib` POST/PUT fires — Discard is a pure
  client-side state revert, it never calls the save endpoint).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing pipeline | Pipeline is loaded in the editor | this AFS step 1 (reuses covering-test action) | new test, step 1: navigation via `_navigate_to_detail` | asserted |
| 2 Verify Save/Discard initially disabled | Both buttons disabled/inactive | this AFS step 2 | new test, step 2: `is_save_enabled() is False`, `is_discard_enabled() is False` | asserted |
| 3 Modify the pipeline name | Name field shows the modified value | this AFS step 3 (reuses covering-test action) | new test, step 3: `get_name()` equals modified value | asserted |
| 4 Verify Save button becomes enabled | Save button is active/enabled | this AFS step 4 | new test, step 4: `is_save_enabled() is True` | asserted |
| 5 Verify Discard button becomes enabled | Discard button is active/enabled | this AFS step 5 | new test, step 5: `is_discard_enabled() is True` | asserted |
| 6 Click "Discard" button | Discard action is triggered | this AFS step 6 (reuses covering-test action) | new test, step 6: `click_discard()` | asserted |
| 7 Verify pipeline name reverts to original value | Name field shows the original pipeline name | this AFS step 7 (reuses covering-test assertion) | new test, step 7: `get_name() == original_name` | asserted |
| 8 Verify Save/Discard return to disabled state | Both buttons disabled again | this AFS step 8 | new test, step 8: `is_save_enabled() is False`, `is_discard_enabled() is False` | asserted |

### Axis 2 — Analyst additions

- None beyond the case's own text — every step maps 1:1 to a case row; no
  additional observable was added. The only "addition" is technique-level:
  reusing the exact same action methods (`update_name`, `click_discard`,
  `get_name`) the pre-existing covering test already exercises, rather than
  re-deriving the flow, per Rule 7.

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` — handled by the `pipeline_id`
   fixture's own teardown (same as the covering test — no new cleanup
   needed).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Save button | `PipelineFormPage.save_button` (existing `LocatorDescriptor`, testid `agent-save-button`, confirmed on `main`) | — |
| Discard button | `PipelineFormPage.discard_button` (existing `LocatorDescriptor`, testid `discard-button`, confirmed on `main` and live-wired on the pipeline detail page per `_surface.md`) | — |
| Save enabled/disabled check | `PipelineFormPage.is_save_enabled()` (existing, no changes) | — |
| Discard enabled/disabled check | `PipelineFormPage.is_discard_enabled()` (existing, no changes) | — |
| Name field | `PipelineFormPage.name_input` / `update_name()` / `get_name()` (existing, no changes) | — |

No new page-object work, no new `add-data-testid` work — every element and
method this case needs already exists and is already exercised by sibling
merged tests.

## Network Behavior
- **None beyond Discard's own settle** — confirmed live via console/network
  capture across the full sequence: the name edit itself fires no network
  request (client-side form state only), and `click_discard()` fires no
  `prompt_lib` POST/PUT — Discard is a pure client-side revert of the
  in-memory form state, not a server round-trip.

## Known Defects Found During Exploration
- None. The case's described behavior (disabled → enabled → discard →
  disabled) matches live product behavior exactly, confirmed both via the
  pre-existing merged test (name-revert half) and this session's live
  button-state checks (2026-08-09, pipeline created via the `pipeline_id`
  fixture pattern, same technique used interactively for verification before
  writing the automated assertions).

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Fixture: `pipeline_id` (existing, `automation/fixtures/data_fixtures.py`)
  — reused unmodified, same as the covering test.
- Page object: `automation/pages/pipeline_form_page.py` /
  `pipeline_detail_page.py`. Zero new methods, zero new testids — every
  method (`is_save_enabled`, `is_discard_enabled`, `update_name`, `get_name`,
  `click_discard`) already exists and is already exercised by sibling tests
  (`test_pipeline_create_version.py`, `test_pipeline_yaml_flow_sync.py`,
  `test_pipeline_advanced.py` itself).
- **Extend, don't duplicate**: the new test is APPENDED to
  `TestDiscardChanges` in `test_pipeline_advanced.py` as a second `test()`
  method, tagged with `@allure.issue(...)` pointing at ELITEA-2048 — the
  existing `test_discard_reverts_name_change` body stays byte-identical
  (additive-only contract, `.agents/testing.md` / skill Hard Rule 3).
- `tests.ui.pipelines.helpers._navigate_to_detail(page, pipeline_id)` is the
  existing shared navigation helper — reuse it, don't re-navigate manually.
