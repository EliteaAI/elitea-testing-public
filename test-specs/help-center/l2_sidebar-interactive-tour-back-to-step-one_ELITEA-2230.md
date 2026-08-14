# Test Case: Help Center — Back button navigates to previous step during Interactive Tour

## Metadata
- **TMS ID**: ELITEA-2230
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
- **Why extend, not fresh**: the covering spec already exercises Back once
  (its Step 7, at step 3→2, mid-sequence) but that assertion never returns all
  the way to step 1, so it never re-proves that the "Back disabled on step 1"
  state (asserted once, initially, in its Step 3) also holds true AFTER
  navigating back to step 1 via Back — i.e. it never confirms Back correctly
  re-disables itself on arrival, only that it starts disabled. This case is
  specifically that missing "Back to the very first step" observable,
  confirmed live to behave correctly but not yet asserted by any merged test.
- **Insertion point**: a new `test_sidebar_interactive_tour_back_returns_to_step_one`
  method appended to `TestHelpCenterSidebarTour` in the same file (additive).

## Preconditions
- User is authenticated (`auth_state` fixture).
- No special setup.

## Test Data
### reuse-existing
- (none required)

## Test Steps

1. Navigate to `${BASE_URL}/help-center` and click "Sidebar Interactive Tour".
   - **Verify**: new tab opens, tour dialog shows step `1 / 17`, title
     "ELITEA Logo".
2. Click "Next" to advance to step 2/17.
   - **Verify**: step counter reads `"2 / 17"`, title "Notifications", Back
     enabled (`disabled` attribute absent — confirmed live).
3. Click the "Back" button.
4. Verify the tour returns to step 1/17: counter reads `"1 / 17"`.
5. Verify the tooltip content matches step 1's content: title "ELITEA Logo",
   description matching the exact step-1 text (confirmed live identical to
   the initial launch — same DOM textContent as ELITEA-2226's step-1 check).
6. Verify the step counter updates to "1 / 17" (same assertion as step 4,
   restated per the case's own step numbering — kept as a single assertion,
   not duplicated).
7. Verify the "Back" button is disabled/inactive again on step 1/17
   (confirmed live: `disabled` attribute present, identical to the very
   first launch — Back correctly re-disables itself on returning to step 1,
   it does not get "stuck enabled" from having been used once).

## Expected Results
- Clicking "Back" from step 2/17 returns the tour to step 1/17 with the exact
  same title, description, and counter as the original first-step state, and
  "Back" becomes disabled again — proving the disabled state is driven by the
  CURRENT step index, not a one-time initial flag.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center and click "Sidebar Interactive Tour" | Page loads | AFS step 1 | step 1: link click, dialog at 1/17 | asserted |
| 2 Click "Next" to advance to step 2/17 | Control responds | AFS step 2 | step 2: click + counter `2/17` | asserted |
| 3 Verify tour is on step 2/17 and counter shows "2 / 17" | Condition holds | AFS step 2 | step 2: counter text + title + Back enabled | asserted |
| 4 Click "Back" | Control responds | AFS step 3 | step 3: `click_back()` | asserted |
| 5 Verify tour returns to step 1/17 | Condition holds | AFS step 4 | step 4: counter `1/17` | asserted |
| 6 Verify tooltip content matches step 1 | Condition holds | AFS step 5 | step 5: title + description match original step 1 | asserted |
| 7 Verify step counter updates to "1 / 17" | Condition holds | AFS step 6 | step 6: same counter check (case restates it as its own numbered step) | asserted |
| 8 Verify "Back" button disabled/inactive on step 1/17 | Condition holds | AFS step 7 | step 7: `disabled` attribute present | asserted |

**Axis 2 — Analyst additions:** none beyond the case — deliberately scoped to
a single Next→Back round trip (step 1→2→1) rather than a deeper multi-step
detour, since the deeper mid-sequence Back-and-resume case (step 3→2, then
forward again) is already the covering spec's own Step 7 and would duplicate
that assertion without adding information; this case's unique value is
specifically the return-to-the-boundary (step 1) behavior.

## Cleanup
- None required — no persisted state.

## Concrete Handles (discovered during exploration)
All reused verbatim from the covering spec's infrastructure — no new
testids:
- `HelpCenterPage.open_resource_link_in_new_tab("sidebar-interactive-tour")`
- `InteractiveTourCard.step_counter`, `.title`, `.description`,
  `.click_next()`, `.click_back()`, `.is_back_disabled()`,
  `.get_description_text()`

## Network Behavior
- None — same as covering spec.

## Known Defects Found During Exploration
None — confirmed live exactly as expected (Back correctly re-disables on
returning to step 1; title/description/counter all match the original
step-1 state).

## Blocked Steps
None — full flow executed and confirmed live.

## Automation Hints
- Framework: Playwright + pytest.
- Marker set matches the covering spec's file-level `pytestmark`
  (`ui`, `help_center`, `p2`, `regression`) — this case's own priority (l2 /
  medium) matches the file's `p2` cleanly, no mismatch to declare (unlike
  ELITEA-2229's l1/p2 tension).
- No sleep needed — all assertions are Playwright web-first `expect()` waits
  on the same testids the covering spec already uses.
