# Test Case: Help Center — completed Sidebar Interactive Tour can be restarted from Help Center

## Metadata
- **TMS ID**: ELITEA-2228
- **Linked Story**: none found — no `[Automate][ELITEA-<id>]` tracker card exists for this case ID (verified via real-time gh issue list, limit 1000, at implementation time); the sibling case ELITEA-2227 has one (#734, CLOSED, case-specific — not a shared story for this cluster)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: extend-existing

## Extension target
- **Covering spec**: `automation/tests/ui/help_center/test_help_center_sidebar_tour.py`
  (`TestHelpCenterSidebarTour`), merged to `origin/automation/base`
  (commit `37dbd948`).
- **Covering spec's own AFS**:
  `test-specs/help-center/l2_sidebar-interactive-tour-completes_ELITEA-2227.md`.
- **Why extend, not fresh**: the covering spec's own AFS preconditions section
  already documents the underlying mechanism this case tests ("the tour always
  replays from step 1 when launched via `?tour=sidebar` regardless of whether
  it was seen before") — but the covering spec itself never exercises a
  SECOND launch after a completed run; it opens the tour once, finishes it,
  and ends the test. This case is the missing "launch again after Done!"
  observable and reuses 100% of the existing page object / component
  infrastructure.
- **Insertion point**: a new `test_sidebar_interactive_tour_restarts_after_completion`
  method appended to `TestHelpCenterSidebarTour` in the same file (additive).

## Preconditions
- User is authenticated (`auth_state` fixture).
- No special setup — a fresh completed run is produced within the test itself
  (steps 1–2 below), no persisted "tour seen" state exists to interfere
  (confirmed live, same as ELITEA-2227's precondition note).

## Test Data
### reuse-existing
- (none required)

## Test Steps

1. Navigate to `${BASE_URL}/help-center`, click "Sidebar Interactive Tour",
   and complete the tour fully: click "Next" 16 times (steps 1→17), then click
   the primary button (labelled "Finish" on step 17) to open the "Tour
   Complete!" modal, then click "Done!".
   - **Verify**: "Tour Complete!" modal appears (`interactive-tour-complete-title`)
     before Done is clicked; after Done, the modal is removed from the DOM.
2. Navigate back to the original Help Center tab (still open — the tour ran in
   a separate `target="_blank"` tab).
   - **Verify**: the "Sidebar Interactive Tour" link is still visible and
     clickable (confirmed live: the Help Center tab is untouched by the
     tour's completion in the other tab — same page, same link).
3. Click "Sidebar Interactive Tour" again (a second `open_resource_link_in_new_tab`
   call — opens a THIRD tab).
   - **Verify**: the tour restarts at step counter `"1 / 17"`, title "ELITEA
     Logo", and "Back" disabled again (confirmed live — identical initial
     state to a first-time launch; no "already seen" branch exists).

## Expected Results
- After fully completing the tour once (Finish → Done), the "Sidebar
  Interactive Tour" link on Help Center remains clickable and, when clicked
  again, opens a fresh tour instance starting at step 1/17 with Back disabled
  — i.e. every step is accessible again from the beginning.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Complete the Sidebar Interactive Tour fully via all steps + "Done!" | Action completes without error | AFS step 1 | step 1: 16× Next, Finish, Tour Complete modal, Done | asserted |
| 2 Navigate back to Help Center | Page loads | AFS step 2 | step 2: original tab still has the page loaded | asserted |
| 3 Locate INTERACTIVE TOURS card | Action completes | AFS step 2 | step 2: link located via existing testid | asserted |
| 4 Verify "Sidebar Interactive Tour" link still visible/clickable | Condition holds | AFS step 2 | step 2: link visibility check before re-click | asserted |
| 5 Click "Sidebar Interactive Tour" again | Control responds | AFS step 3 | step 3: second `open_resource_link_in_new_tab` call | asserted |
| 6 Verify tour restarts from step 1/17 | Condition holds | AFS step 3 | step 3: counter `"1 / 17"`, title "ELITEA Logo" | asserted |
| 7 Verify all steps accessible again from the beginning | Condition holds | AFS step 3 | step 3: Back disabled (proves genuine fresh-start state, not a resumed/disabled UI) | asserted *(scoped to the initial-state proof — re-walking all 17 steps a second time is the covering spec's job, not this case's; see Axis 2 note)* |

**Axis 2 — Analyst additions:** none added beyond scoping note above — "all
steps are accessible again" is verified via the fresh step-1 state (counter +
title + Back-disabled), not by re-running the full 17-step walk a second time,
since that exact walk is already proven once by the covering spec and
repeating it here would duplicate assertions without adding new information.

## Cleanup
- None required — no persisted state; each tour launch is a fresh client-side
  mount.

## Concrete Handles (discovered during exploration)
All reused verbatim from the covering spec's infrastructure — no new testids:
- `HelpCenterPage.open_resource_link_in_new_tab("sidebar-interactive-tour")`
  (called twice in this test — once to complete, once to verify restart)
- `InteractiveTourCard` (`.next_button`/`.click_next()`, `.click_finish()`,
  `.step_counter`, `.title`, `.is_back_disabled()`)
- `TourCompleteCard` (`.wait_for()`, `.click_done()`)

## Network Behavior
- None — same as covering spec (pure client-side tour state, no persistence
  layer involved in the restart).

## Known Defects Found During Exploration
None — confirmed live exactly as expected (tour has no "seen" memory; always
restarts fresh).

## Blocked Steps
None — full flow executed and confirmed live (completed tour once, verified
link still present, clicked again, confirmed fresh restart at 1/17 with Back
disabled).

## Automation Hints
- Framework: Playwright + pytest.
- Marker set matches the covering spec:
  `@pytest.mark.ui @pytest.mark.help_center @pytest.mark.p2 @pytest.mark.regression`.
- To keep the test fast, drive the first (throwaway) completion loop the same
  way the covering spec asserts it — `click_next()` in a loop — but this new
  test does not need to re-assert every intermediate step's title/description
  (that is the covering spec's job); only the counter reaching `17 / 17`
  before Finish, and the fresh `1 / 17` state after re-launching, are
  load-bearing here.
- The original Help Center tab and the two tour tabs (first completed run,
  second restarted run) are three separate `Page` objects — track them
  explicitly rather than relying on "the current page" implicitly, to avoid
  cross-tab locator confusion.
