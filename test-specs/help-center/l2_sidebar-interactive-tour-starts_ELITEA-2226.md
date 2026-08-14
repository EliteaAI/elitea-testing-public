# Test Case: Help Center — Sidebar Interactive Tour starts when clicking the link

## Metadata
- **TMS ID**: ELITEA-2226
- **Linked Story**: none found — no `[Automate][ELITEA-<id>]` tracker card exists for this case ID (verified via real-time gh issue list, limit 1000, at implementation time); the sibling case ELITEA-2227 has one (#734, CLOSED, case-specific — not a shared story for this cluster)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (localhost bypasses
  Keycloak, authenticates via `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: extend-existing

## Extension target
- **Covering spec**: `automation/tests/ui/help_center/test_help_center_sidebar_tour.py`
  (`TestHelpCenterSidebarTour`), merged to `origin/automation/base`
  (commit `37dbd948`).
- **Covering spec's own AFS**:
  `test-specs/help-center/l2_sidebar-interactive-tour-completes_ELITEA-2227.md`.
- **Why extend, not fresh**: the covering spec already opens the tour from the
  Help Center link and reaches step 1/17 with Back disabled (its Step 2/3), but
  it does not assert the exact step-1 description text nor that all three
  footer buttons (Skip / Back / Next) are visible together at step 1 — it only
  checks the Skip/Back/Next trio explicitly at step 17/17 (its Step 9). This
  case's Pass criterion ("verify three navigation buttons are visible: skip,
  back(inactive), next") is a distinct, closable observable the covering spec
  does not fully assert at the initial state.
- **Insertion point**: a new `test_sidebar_interactive_tour_starts_on_link_click`
  method, in the same file, in a new sibling class `TestHelpCenterSidebarTourExtras`
  (additive — `TestHelpCenterSidebarTour.test_sidebar_interactive_tour_completes_via_next`
  is untouched). Amended post-implementation (fix round 1): the original plan was
  to append this method directly into `TestHelpCenterSidebarTour`; the shipped
  diff instead groups all four ELITEA-2226/2228/2229/2230 extension methods
  together under one new class in the same module, to keep the covering test's
  class scoped to its own AFS (ELITEA-2227) while still being 100%-additive at
  the file level. The additive-only contract (no existing test body touched) is
  unaffected by this organizational choice.

## Preconditions
- User is authenticated (`auth_state` fixture).
- No prior tour-completion state needs seeding — confirmed live (again) that
  the tour always mounts fresh at step 1 when the link is clicked, regardless
  of prior runs in the same session.

## Test Data
### reuse-existing
- (none required)

## Test Steps

1. Navigate to `${BASE_URL}/help-center` (`HelpCenterPage.navigate()`).
   - **Verify**: page header visible (`help-center-page-header`, text "Help
     Center").
2. Locate the "INTERACTIVE TOURS" card and verify the "Sidebar Interactive
   Tour" and "Chat Interactive Tour" links are both displayed.
   - **Verify**: both links present via `HelpCenterPage.resource_link(slug)`
     for `sidebar-interactive-tour` and `chat-interactive-tour`.
3. Click "Sidebar Interactive Tour" (`HelpCenterPage.open_resource_link_in_new_tab`).
   - **Verify**: a new page/tab opens (the tour overlay launches immediately —
     confirmed live, dialog present on first snapshot after the click, no
     intermediate loading state observed).
4. On the new page, verify the tour dialog's first step is anchored to the
   ELITEA Logo (title `"ELITEA Logo"`) and its description reads exactly:
   *"The ELITEA Logo in the sidebar shows the server status. Green mark points
   that server is working. Red mark points that server is updating."*
   (confirmed live verbatim — see § Automation Hints for the exact DOM
   textContent shape, which concatenates two paragraphs with no space).
5. Verify the step counter reads `"1 / 17"`.
6. Verify all three footer buttons are visible: "Skip" (enabled), "Back"
   (`disabled` attribute present), "Next" (enabled).

## Expected Results
- Clicking "Sidebar Interactive Tour" opens the tour overlay on a new page
  immediately, anchored to the ELITEA Logo, with the exact step-1 description
  text, counter `1 / 17`, and Skip/Back(disabled)/Next all visible together.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | Page loads | AFS step 1 | step 1: `help-center-page-header` visible | asserted |
| 2 Locate INTERACTIVE TOURS card | Action completes | AFS step 2 | step 2: card located via both link testids | asserted |
| 3 Verify Sidebar/Chat Interactive Tour links displayed | Condition holds | AFS step 2 | step 2: both links visible | asserted |
| 4 Click "Sidebar Interactive Tour" link | Control responds | AFS step 3 | step 3: click + new page opens | asserted |
| 5 Verify tour overlay launches immediately | Condition holds | AFS step 3 | step 3: dialog present on first snapshot, no wait needed beyond the click itself | asserted |
| 6 Verify first step anchored to ELITEA Logo | Condition holds | AFS step 4 | step 4: title text `"ELITEA Logo"` | asserted |
| 7 Verify first step description exact text | Condition holds | AFS step 4 | step 4: description exact-text match (confirmed live) | asserted |
| 8 Verify step counter shows "1 / 17" | Condition holds | AFS step 5 | step 5: counter text | asserted |
| 9 Verify three nav buttons visible (Skip, Back inactive, Next) | Condition holds | AFS step 6 | step 6: all three buttons visible + Back `disabled` attribute | asserted |

**Axis 2 — Analyst additions:** none beyond the case — this case is
intentionally scoped to the initial-state snapshot only (no "Next" click, that
belongs to ELITEA-2227's covering flow).

## Cleanup
- None required — no test data created, no persisted state to reset.

## Concrete Handles (discovered during exploration)
All handles reused from the covering spec's page object / component — no new
testids needed:
- `HelpCenterPage.page_header` (`help-center-page-header`)
- `HelpCenterPage.resource_link("sidebar-interactive-tour")` /
  `resource_link("chat-interactive-tour")` (`help-center-tour-link-{slug}`)
- `HelpCenterPage.open_resource_link_in_new_tab("sidebar-interactive-tour")`
- `InteractiveTourCard.title` / `.description` / `.step_counter` /
  `.skip_button` / `.back_button` / `.next_button` / `.is_back_disabled()`
  (all in `automation/components/interactive_tour.py`)

Confirmed live description `textContent` (no space between the two
paragraphs, matches the pattern already used by
`test_sidebar_interactive_tour_completes_via_next`'s
`get_description_text()` helper — assert via `.to_contain_text()` on stable
substrings rather than a single fragile full-string equality, since the DOM
concatenates `<p>` boundaries with no separator):
```
The ELITEA Logo in the sidebar shows the server status.Green mark points that server is working.
Red mark points that server is updating.
```

## Network Behavior
- None — same as the covering spec (pure client-side tour state).

## Known Defects Found During Exploration
None.

## Blocked Steps
None — all steps executed and confirmed live.

## Automation Hints
- Framework: Playwright + pytest.
- Reuses `HelpCenterPage` and `InteractiveTourCard` verbatim — no page-object
  changes needed.
- Marker set matches the covering spec:
  `@pytest.mark.ui @pytest.mark.help_center @pytest.mark.p2 @pytest.mark.regression`.
- New-tab handling identical to the covering spec's Step 1
  (`open_resource_link_in_new_tab`).
- Assert the description via a substring match rather than a brittle full
  string equal, to tolerate incidental whitespace/markdown-render changes
  while still proving the correct step-1 content is shown (distinct from the
  covering spec, which only checks description non-empty at each step —
  this case is specifically about verifying the FIRST step's exact content
  per case step 7's literal text).
