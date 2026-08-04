# Test Case: Help Center — Sidebar Interactive Tour completes successfully by clicking Next through all steps

## Metadata
- **TMS ID**: ELITEA-2227
- **Linked Story**: EliteaAI/elitea-testing-public#734
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (on localhost this bypasses
  Keycloak entirely and authenticates through `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: qa-engineer (Sage)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (use the framework's `auth_state` fixture — localhost skips
  login via `VITE_DEV_TOKEN`, see `.agents/testing.md` § Hooks).
- No prior tour-completion localStorage/DB state needs seeding — the tour always
  replays from step 1 when launched via `?tour=sidebar` regardless of whether it
  was seen before (confirmed: `useTourFromUrl` starts the tour unconditionally on
  that query param; the first-visit "prompt" phase is a *different*, unprompted
  entry path this case does not exercise).

## Test Data
### reuse-existing
- (none required — case has no data inputs)

## Test Steps

1. Navigate to `${BASE_URL}/help-center` (via `navigate("/help-center")` — respects
   `APP_PREFIX`).
   - **Verify**: Help Center page header is visible (`help-center-page-header`
     testid, text "Help Center").
2. Click the "Sidebar Interactive Tour" link (`help-center-tour-link-sidebar-interactive-tour`
   testid). **This link has `target="_blank"`** — it opens in a NEW browser tab/page.
   Playwright: use `page.expect_popup()` (or the framework's equivalent) around the
   click, then continue on the popup page.
   - **Verify**: a new page/tab opens; the tour dialog is present and shows step
     `1 / 17` with title "ELITEA Logo" (`interactive-tour-step-counter`,
     `interactive-tour-title` testids, scoped to the new page).
   - **⚠ Known localhost-only quirk** (not a product defect — see § Automation
     Hints): the new tab's URL is `/app/chat?tour=sidebar` (backend-served CMS
     content hardcodes the `/app` prefix, correct for deployed envs, wrong for
     localhost where `APP_PREFIX=""`). The main content area therefore renders
     "Page not found" for the rest of this test — **this does not affect any of
     the tour assertions below**, which target the tour dialog/overlay only
     (mounted independently of route). Do not assert on main-content identity
     after step 2.
3. On the new page, verify the tour dialog step counter reads `1 / 17` and the
   "Back" button is disabled.
4. Click "Next" (`interactive-tour-next-button` testid).
   - **Verify**: step counter advances to `2 / 17`, title changes to
     "Notifications", "Back" button becomes enabled
     (`interactive-tour-back-button` testid, `disabled` attribute false), and the
     spotlight highlight (`interactive-tour-spotlight` testid) is present with a
     bounding box that differs from step 1's (proves "the highlighted sidebar
     element changes accordingly" — see § Automation Hints for why this, not a
     per-nav-item testid, is the chosen verification).
5. Continue clicking "Next" through all remaining steps (steps 3–17 per the
   reference table in § Automation Hints), asserting per step: counter
   increments, title matches the reference table, spotlight bounding box changes
   from the previous step.
6. At each step, verify the dialog shows a title (`interactive-tour-title`), a
   description body with markdown content (`interactive-tour-description`), and
   the step counter (`interactive-tour-step-counter`).
7. At step 3 (or any intermediate step), click "Back" (`interactive-tour-back-button`)
   and verify the counter decrements (e.g. `3/17` → `2/17`) and the title reverts
   to the previous step's title (confirmed live: "Project Switcher" → "Notifications").
   Then continue forward again with "Next" to resume the sequence.
8. Verify the final step reads `17 / 17` with title "Support Assistant" and the
   matching description text (confirmed live, see reference table).
9. On step `17/17`, verify the footer buttons are "Skip", "Back", "Finish" — the
   primary button (`interactive-tour-next-button` testid — **same stable testid**
   as "Next"; only its label changes to "Finish" on the last step, per the
   testid-is-stable-identity rule) reads "Finish". Click it.
   - **Verify**: the running tour dialog closes and the "Tour Complete!" modal
     appears.
10. Verify the "Tour Complete!" modal shows: a checkmark/success icon
    (`interactive-tour-complete-icon`), title "Tour Complete!"
    (`interactive-tour-complete-title`).
11. Verify the modal shows "Keep exploring:" (`interactive-tour-complete-keep-exploring-label`)
    with a "Chat Interactive Tour" option
    (`interactive-tour-complete-keep-exploring-chat` — dynamic testid keyed by
    `tourId`, see § Concrete Handles).
12. Verify a "Done!" button is displayed (`interactive-tour-complete-done-button`).
13. Click "Done!" and verify the "Tour Complete!" modal closes (removed from DOM —
    no `[role="dialog"]` present) and the full-screen tour backdrop/blocker is
    also removed, i.e. the underlying page becomes interactive again (sidebar
    buttons clickable, no overlay intercepting pointer events). This is the
    environment-agnostic form of "returns to the current project default page
    view" — see § Automation Hints for why the literal page-identity check is
    not used here.

## Expected Results
- The tour runs all 17 steps in order via "Next", each with a title + markdown
  description + step counter + a changing spotlight highlight.
- "Back" is disabled only on step 1; enabled and functional (decrements + title
  reverts) on every other step.
- Step 17/17 is "Support Assistant"; its primary button reads "Finish".
- Clicking "Finish" replaces the running-tour dialog with the "Tour Complete!"
  modal (checkmark icon, title, "Keep exploring: Chat Interactive Tour", "Done!").
- Clicking "Done!" removes the modal and the tour backdrop entirely; no console
  errors at any point (confirmed: 0 console errors across the full run).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center and click "Sidebar Interactive Tour" | Target page/section loads | AFS steps 1–2 | step 1: `help-center-page-header` visible; step 2: new tab opens, tour dialog shows `1/17` | asserted |
| 2 Verify tour starts at step 1/17 | Condition holds | AFS step 3 | step 3: counter `1/17`, Back disabled | asserted |
| 3 Click "Next" | Control responds | AFS step 4 | step 4: click + counter change | asserted |
| 4 Verify tour advances to 2/17, highlighted element changes, Back becomes active/coloured | Condition holds | AFS step 4 | step 4: counter `2/17`, title change, spotlight bbox diff, Back `disabled=false` | asserted *(colour nuance scoped to enabled/disabled state — see Axis 2 note)* |
| 5 Continue clicking Next through all remaining steps | Completes without error | AFS step 5 | step 5: loop steps 3–17 against reference table | asserted |
| 6 Verify each step shows title, description, step counter | Condition holds | AFS step 6 | step 6: 3 testids checked per step | asserted |
| 7 Verify Back returns to previous step, counter decrements | Condition holds | AFS step 7 | step 7: Back click, counter + title revert (confirmed live: `3/17`→`2/17`, "Project Switcher"→"Notifications") | asserted |
| 8 Verify final step (17/17) describes "Support Assistant" | Condition holds | AFS step 8 | step 8: counter `17/17`, title "Support Assistant", description text | asserted |
| 9 On 17/17 buttons are Skip/Back/Finish; click "Finish" | Action completes | AFS step 9 | step 9: button labels + click | asserted |
| 10 Verify "Tour Complete!" modal with checkmark icon | Condition holds | AFS step 10 | step 10: icon + title testids | asserted |
| 11 Verify "Keep exploring:" with "Chat Interactive Tour" option | Condition holds | AFS step 11 | step 11: label + dynamic button testid | asserted |
| 12 Verify "Done!" button displayed | Condition holds | AFS step 12 | step 12: button testid | asserted |
| 13 Click "Done!", verify modal closes and user returns to project default page view | Control responds | AFS step 13 | step 13: dialog removed + backdrop removed (environment-agnostic form; literal page-identity check blocked by a localhost-only link-prefix quirk, not a product defect — see Automation Hints) | asserted *(scoped — see note)* |

**Axis 2 — Analyst additions:**
- Console-error check across the whole 17-step run + modal close — *added:
  silent JS errors during a long-lived overlay component are exactly the kind of
  bug that wouldn't surface any other way; confirmed 0 errors live.*
- Spotlight bounding-box diff between consecutive steps — *added as the concrete,
  testable form of "highlighted sidebar element changes accordingly" (case step
  4), scoped to avoid adding testids to all 17 sidebar nav targets — see
  Automation Hints for the reasoning.*
- (nothing else added beyond the case)

## Cleanup
- None required — the tour is stateless UI (no persisted "tour seen" flag was
  observed to change function across runs; re-launching via `?tour=sidebar`
  always restarts at step 1). No test data created.

## Concrete Handles (discovered during exploration)

**All new testids below were confirmed absent** (`grep -rln "data-testid"` across
`src/[fsd]/features/interactive-tours/` returned zero files, and the Help Center
resources page + sidebar nav items carry testids only on 3 unrelated elements:
`project-selector-trigger`, `sidebar-toggle`, `sidebar-create-button`). Every
testid in this table is `testid needed` — none of them fall back to role/text.

| Element | Testid needed | Component to edit | Notes |
|---|---|---|---|
| Help Center page header ("Help Center" title) | `help-center-page-header` | `src/[fsd]/pages/resources/ui/ResourceVersionInfo.jsx` | confirms page loaded (case step 1) |
| "Sidebar Interactive Tour" resource link | `help-center-tour-link-{slug}` (dynamic — see below) | `src/[fsd]/pages/resources/index.jsx` (the `links.map(...)` loop) | `target="_blank"`; slug = kebab-case of `link.title` (backend-config data, no stable id field exists) |
| Tour dialog title (running phase) | `interactive-tour-title` | `src/[fsd]/features/interactive-tours/ui/InteractiveTourCard.jsx` (the `Typography variant="headingMedium"` for `currentStep.title`) | generic — shared by all 17 tour configs (chat/agent/pipeline/…), not sidebar-specific |
| Tour dialog description | `interactive-tour-description` | same file — the `Box` wrapping `<MuiMarkdown>` | generic |
| Tour dialog step counter | `interactive-tour-step-counter` | same file — the `Typography variant="labelSmall"` (`{stepIndex+1} / {totalSteps}`) | generic |
| Tour dialog "Skip" button | `interactive-tour-skip-button` | same file | generic |
| Tour dialog "Back" button | `interactive-tour-back-button` | same file | generic; assert `disabled` attr, not colour, for enabled/disabled state (PR #581-style — state via attribute, not a separate testid) |
| Tour dialog "Next"/"Finish" button | `interactive-tour-next-button` | same file | **one stable testid** — label flips Next→Finish on the last step; do NOT create two testids for this (testid = stable identity ruling) |
| Spotlight highlight box | `interactive-tour-spotlight` | `src/[fsd]/features/interactive-tours/ui/InteractiveTourSpotlight.jsx` (the `hasTarget && <Box sx={spotlightSx(...)}>`) | only rendered when a target is resolved; generic |
| Tour Complete icon | `interactive-tour-complete-icon` | `src/[fsd]/features/interactive-tours/ui/TourCardHeader.jsx` (the icon `Box`) | `TourCardHeader` is currently consumed only by `TourCompleteCard`, but keep the testid generic (`interactive-tour-complete-*`, not `sidebar-tour-complete-*`) since it will back every tour's completion screen |
| Tour Complete title ("Tour Complete!") | `interactive-tour-complete-title` | same file — the `Typography` wrapping `{children}` | generic |
| "Keep exploring:" label | `interactive-tour-complete-keep-exploring-label` | `src/[fsd]/features/interactive-tours/ui/TourCompleteCard.jsx` | generic |
| "Chat Interactive Tour" keep-exploring button | `interactive-tour-complete-keep-exploring-{tourId}` (dynamic — see below) | same file — the `BaseBtn` inside `keepExploring.map(...)` | template on `item.tourId` (already available as `data-tour-id={item.tourId}`, a clean stable key — unlike the resource-link slug, no CMS-text derivation needed); for this case the rendered instance is `interactive-tour-complete-keep-exploring-chat` |
| "Done!" button | `interactive-tour-complete-done-button` | same file — the final `BaseBtn` | generic |

**Dynamic testid template constants** (per `.agents/testing.md` § Locator policy):
```python
# help_center_page.py
TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'
# usage: self.page.locator(self.TOUR_LINK.format("sidebar-interactive-tour"))

# interactive_tour_page.py (or wherever the tour page object lives)
COMPLETE_KEEP_EXPLORING_OPTION = '[data-testid="interactive-tour-complete-keep-exploring-{}"]'
# usage: self.page.locator(self.COMPLETE_KEEP_EXPLORING_OPTION.format("chat"))
```

**Sidebar tour step reference (source of truth:
`EliteaUI/src/[fsd]/features/interactive-tours/lib/constants/sidebarTour.constants.js`,
17 entries; titles below CONFIRMED live against steps 1, 2, 3(→2 via Back), 5,
6, 10, 15, 17):**

| # | step id | title |
|---|---|---|
| 1 | sidebar-logo | ELITEA Logo |
| 2 | notifications | Notifications |
| 3 | project-switcher | Project Switcher |
| 4 | create-button | + Create Button |
| 5 | chat | Chats |
| 6 | agents | Agents |
| 7 | pipelines | Pipelines |
| 8 | skills | Skills |
| 9 | toolkits | Toolkits |
| 10 | mcps | MCPs |
| 11 | credentials | Credentials |
| 12 | applications | Applications |
| 13 | artifacts | Artifacts |
| 14 | settings | Settings |
| 15 | elitea-catalog | ELITEA Catalog |
| 16 | resources | Help Center |
| 17 | support-assistant | Support Assistant |

(Full markdown description text per step is in the source constants file above —
the implementer may assert full text or just a stable substring per step;
exact strings were not transcribed here to avoid drift if the copy changes —
title + counter + spotlight-diff is the load-bearing assertion set per step,
full-text description checks are optional enrichment.)

## Network Behavior
- No XHR/fetch traffic observed as part of tour navigation itself (tour state is
  pure client-side React state via `InteractiveTourProvider` + `useTourFromUrl`).
- The Help Center page itself fires `useGetResourcesConfigQuery` /
  `useGetSystemInfoQuery` on load (pre-existing, unrelated to the tour) — no
  action needed, not in scope for this case.

## Known Defects Found During Exploration
None found. One environment-specific (not product) quirk is documented above and
in § Automation Hints — it does not block automation and was not filed as a
defect (see reasoning there).

## Blocked Steps
None — case executed end-to-end, all 17 steps + Back + Finish + Tour Complete +
Done confirmed live, 0 console errors.

## Automation Hints

- Framework: Playwright + pytest (per `.agents/testing.md`).
- **New page object needed**: `automation/pages/help_center_page.py` (Help Center
  page + resource links) and either a second page object or a component helper
  for the tour dialog itself, e.g. `automation/pages/interactive_tour_page.py` /
  `automation/components/interactive_tour.py` — the tour overlay is shared UI
  (not scoped to Help Center), so putting it in `components/` (per
  `.agents/testing.md` § Structure: `automation/components/` = "reusable UI
  component helpers") is the better fit; either is acceptable, follow whichever
  convention `page-object-generator` produces.
- **New pytest marker needed**: `help_center` — register in `automation/pytest.ini`
  alongside the existing per-feature markers (same pattern as `support_assistant`).
  Mark the test `@pytest.mark.help_center @pytest.mark.p2 @pytest.mark.regression`.
- **New-tab handling**: the "Sidebar Interactive Tour" link opens
  `target="_blank"`. Use Playwright's `expect_popup()` (sync API:
  `with page.context.expect_page() as new_page_info: <click>` /
  `with page.expect_popup() as popup_info:`) to capture the new `Page` object,
  then drive all subsequent tour steps on that page — not the original Help
  Center tab.
- **Why direct-URL navigation was NOT used for step 1, and what the localhost
  quirk actually means (declared reasoning, `.agents/role-overrides.md` §
  Declared-improvisation protocol — no canon precedent for a backend-CMS-served
  link hardcoding `/app` on an env where `APP_PREFIX=""`):** confirmed live that
  navigating directly to `${BASE_URL}/chat?tour=sidebar` (respecting
  `APP_PREFIX` via `navigate()`) starts the *identical* tour (same
  `useTourFromUrl` hook, same `?tour=` param) on a page that resolves correctly
  locally — this would make step 13's "returns to project default page view"
  fully assertable by page identity. I chose to keep the REAL CLICK
  (`help-center-tour-link-*` → new tab → `/app/chat?tour=sidebar`, which 404s to
  "Page not found" locally only) as the primary flow because it is what case
  step 1 literally specifies and it is fully sufficient to verify every other
  case assertion (the tour dialog/overlay mounts independently of the route, as
  confirmed live through all 17 steps + Finish + Tour Complete + Done). Only the
  literal "which page are we on" sub-check of step 13 is affected, so I scoped
  that assertion to the environment-agnostic "modal + backdrop removed" form
  instead. This is a localhost-only artifact (the same backend-CMS link works
  correctly on any deployed env, where `APP_PREFIX=/app` matches the href) — not
  a product defect, so nothing was filed. If the implementer prefers full
  page-identity coverage for step 13, the direct-URL variant is a valid
  alternative entry point for a *second*, narrower test — not a replacement for
  this one.
- Wait strategy: no network requests to wait on; use element-visibility /
  `expect(...).to_have_text(...)` waits on the tour dialog testids, never a
  `sleep()`.
- Spotlight bbox diff: read `getBoundingClientRect()`-equivalent via
  `locator.bounding_box()` on `interactive-tour-spotlight` before/after each
  "Next" click and assert the tuple changed — this is the testable proxy for
  "highlighted sidebar element changes accordingly" (see Coverage Map Axis 2).
