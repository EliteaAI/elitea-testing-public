# Test Case: Help Center — clicking Skip during Sidebar Interactive Tour terminates the tour

## Metadata
- **TMS ID**: ELITEA-2229
- **Linked Story**: EliteaAI/elitea-testing-public#734
- **Priority**: l1 (case priority: high)
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
- **Why extend, not fresh**: the covering spec never exercises the "Skip"
  button at all — its full run always finishes via Next→Finish→Done. Skip is
  a completely untested exit path (early termination mid-tour) with different
  application-state consequences (no completion, tour never reaches its final
  step) — this is new, non-overlapping coverage on the same shared
  infrastructure (`HelpCenterPage`, `InteractiveTourCard`).
- **Insertion point**: a new `test_sidebar_interactive_tour_skip_terminates`
  method appended to `TestHelpCenterSidebarTour` in the same file (additive).
  Requires ONE new `InteractiveTourCard.click_skip()` action method (the
  `skip_button` `LocatorDescriptor` already exists — only the click action
  method is missing) — a pure addition alongside `click_next`/`click_back`/
  `click_finish`, no existing method body touched.

## Preconditions
- User is authenticated (`auth_state` fixture).
- No special setup.

## Test Data
### reuse-existing
- (none required)

## Test Steps

1. Navigate to `${BASE_URL}/help-center` and click "Sidebar Interactive Tour".
   - **Verify**: new tab opens, tour dialog shows step `1 / 17`.
2. Verify the tour starts at step 1/17 with Skip, Back, and Next buttons
   visible (Back disabled).
3. Click "Next" to advance to step 2/17, then click "Next" again to advance
   to step 3/17 (confirmed live: the case's literal "advance to step 3/17"
   requires two Next clicks from step 1, not one).
   - **Verify**: step counter reads `"3 / 17"`.
4. Click the "Skip" button (`InteractiveTourCard.click_skip()`).
5. Verify the tour overlay and tooltip close immediately: no `[role="dialog"]`
   element remains in the DOM (same environment-agnostic pattern the covering
   spec uses for its own Done-button close check —
   `Dialog.wait_for_hidden(page)`).
6. Verify no tour overlay or highlighted elements remain on screen: the
   spotlight (`interactive-tour-spotlight`) has zero matching elements.
7. Verify the application is fully functional after skipping: click a real
   sidebar navigation item (e.g. "Chats") and confirm it navigates
   successfully (confirmed live: clicking "Chats" after Skip navigates the
   tab to `/chat` cleanly, proving no overlay intercepts pointer events and
   the underlying app is genuinely interactive — the same actionability-proof
   pattern the covering spec uses for its own "Done!" case, applied here to
   the Skip path).

## Expected Results
- Clicking "Skip" at any point mid-tour (tested at step 3/17) immediately
  removes the tour dialog and spotlight from the DOM — no completion modal
  appears (unlike Finish) — and the underlying application remains fully
  interactive: sidebar navigation works normally afterward.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center and click "Sidebar Interactive Tour" | Page loads | AFS step 1 | step 1: link click, new tab opens at 1/17 | asserted |
| 2 Verify tour starts at 1/17 with Skip/Back/Next visible | Condition holds | AFS step 2 | step 2: counter + 3 buttons visible, Back disabled | asserted |
| 3 Click "Next" to advance to step 3/17 | Control responds | AFS step 3 | step 3: two Next clicks, counter `3/17` | asserted |
| 4 Click "Skip" | Control responds | AFS step 4 | step 4: `click_skip()` | asserted |
| 5 Verify tour overlay and tooltip close immediately | Condition holds | AFS step 5 | step 5: `[role="dialog"]` count 0 | asserted |
| 6 Verify user returned to project's default view (e.g. Chats or last visited) | Condition holds | AFS step 7 (folded into the functional-check) | step 7: successful navigation via a real sidebar click | asserted *(scoped — see Axis 2 note, same reasoning the covering spec already applies to its own "returns to default view" step)* |
| 7 Verify no tour overlay or highlighted elements remain | Condition holds | AFS step 6 | step 6: spotlight locator count 0 | asserted |
| 8 Verify application fully functional after skipping (nav + sidebar accessible) | Condition holds | AFS step 7 | step 7: real click-through navigation to `/chat` succeeds | asserted |

**Axis 2 — Analyst additions:**
- Case step 6 ("user is returned to the project's default view") is asserted
  via the SAME environment-agnostic reasoning the covering spec's AFS already
  established for its own Step 13 (`.agents` role-overrides declared-
  improvisation precedent carries over unchanged — no new declaration needed,
  this is the identical localhost `/app`-prefix quirk, not a new one): a
  literal page-identity check is blocked by the localhost-only `/app`-prefix
  href quirk (documented in `test-specs/help-center/_surface.md`), so
  "returned to default view" is proven by demonstrating the app is
  interactive and normal in-app navigation succeeds, rather than by asserting
  a specific URL.
- (nothing else added beyond the case)

## Cleanup
- None required — no persisted state; Skip has no side effect beyond closing
  the tour UI (confirmed live).

## Concrete Handles (discovered during exploration)
Reused from the covering spec's infrastructure, plus one new action method:
- `HelpCenterPage.open_resource_link_in_new_tab("sidebar-interactive-tour")`
- `InteractiveTourCard.skip_button` (`interactive-tour-skip-button` — testid
  already exists, added by ELITEA-2227's implementer)
- **New**: `InteractiveTourCard.click_skip()` — `self.skip_button.click()`,
  same pattern as the existing `click_next`/`click_back`/`click_finish`
  action methods (pure addition to `automation/components/interactive_tour.py`,
  no existing method touched).
- `components.mui.Dialog.wait_for_hidden(page)` (already used by the covering
  spec for its own modal-close assertion)
- `InteractiveTourCard.spotlight` (`interactive-tour-spotlight`, already a
  `LocatorDescriptor` field) — assert `.count() == 0` after Skip.
- `ChatPage` sidebar button, or a direct `page.get_by_role("button", name="Chats")`
  click — confirmed live this navigates cleanly to `/chat` after Skip (unlike
  the tour-launch tab's `/app/chat` 404, in-app sidebar navigation uses the
  correct router path, not the CMS-served href).

## Network Behavior
- None — Skip is pure client-side state (confirmed live: no XHR/fetch fired
  by the click).

## Known Defects Found During Exploration
None — confirmed live exactly as expected: Skip closes the overlay
immediately, no completion modal, sidebar fully functional afterward
(verified by successfully clicking "Chats" and landing on `/chat`).

## Blocked Steps
None — full flow executed and confirmed live.

## Automation Hints
- Framework: Playwright + pytest.
- File-level `pytestmark` (`ui`, `help_center`, `p2`, `regression`) applies to
  every test in the module including this one; per pytest's marker-stacking
  rules a method-level `@pytest.mark.p1` decorator on this specific test
  ADDS `p1` alongside the inherited `p2` rather than replacing it (both
  markers end up on the test item) — that is not the desired shape for a
  clean priority signal. Since this case's priority is genuinely `high` (l1)
  while the rest of the file is `p2`, and pytest has no clean per-test marker
  *removal*, prefer keeping this test under the file's `p2` (documented as a
  known minor mismatch in the test's docstring, citing ELITEA-2229's case
  priority) rather than producing a test carrying both `p1` and `p2`
  simultaneously — a case where the AFS's coverage-tagging convention has no
  clean answer for a mixed-priority file; declared per
  `.agents/role-overrides.md` § Declared-improvisation protocol.
- No sleep needed — `Dialog.wait_for_hidden()` and the spotlight
  `.count() == 0` check are both condition-based; the final navigation click
  is itself the interactivity proof (Playwright's actionability engine fails
  the click if anything still intercepts pointer events).
