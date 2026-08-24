# ELITEA-2241: Onboarding — "Jump in now!" closes onboarding and shows the default project page

**TMS ID:** ELITEA-2241
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2235 and ELITEA-2236 (separate AFS each).
**Surface digest:** `test-specs/onboarding/_surface.md`
**Filed from this case:** #1753 (MINOR — console error), #1754 (CLARIFICATION — case text vs first-visit prompt)

---

## Summary

From the onboarding tips screen, clicking **"Jump in now!"** in the "Your Elitea workspace is
ready!" banner navigates to `/chat` and unmounts the entire onboarding surface. The full sidebar
is present on the destination page — but the product also opens an **interactive-tour first-visit
prompt** whose backdrop blocks interaction until it is dismissed; the sidebar becomes *functional*
after Skip.

---

## Preconditions

Identical to ELITEA-2235 (same screen, same entry path — read that AFS's § Entry path):
authenticated user **with** a personal project, navigate to `/onboarding`, tips card + banner
render. No substitution, no seeding.

**Cleanup:** none required. The test leaves the browser on `/agents` (or `/chat`) and writes only
product-owned storage keys; contexts are per-test.

---

## Live behaviour the case text does not mention (read before implementing)

`Onboarding.jsx handlePersonalProjectReady()` calls `markTourPending(FIRST_ELITEA_TOUR_ID)`, which
writes `localStorage["interactive-tour:first-elitea:pending"] = "true"`. On the next page,
`useProposePendingTour` consumes that key and proposes the tour, so landing on `/chat` **always**
opens the first-visit prompt: *"New here? Take a short interactive tour… **Skip** / **Start!**"*
(`src/[fsd]/features/interactive-tours/ui/FirstVisitPrompt.jsx`). It fires regardless of the
`prompt-seen` flag, because the pending key is set fresh on every `/onboarding` visit — observed
4/4 runs, so it is deterministic, not flaky.

The prompt is a modal (`role="dialog" aria-modal="true"`, `Unstable_TrapFocus`, inside
`InteractiveTourBackdrop`) and its backdrop **intercepts pointer events**. Verified live:

```
locator resolved to <li data-testid="sidebar-menu-item-agents" …>
  - element is visible, enabled and stable
  - <div class="MuiBox-root css-1u2wpa0">…</div> intercepts pointer events
```

So after "Jump in now!" the sidebar is **displayed** but **not clickable** until the prompt is
dismissed. This is correct product behaviour for a modal — the *case text* is what under-specifies
it, so it is filed as a **clarification (#1754)**, not a defect, and this spec asserts the live
contract per the reverse-masking guard. No case step is dropped: step 7's "displayed" is asserted
immediately after landing, and "functional" is asserted after Skip.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Log in first time; onboarding card displayed | Card rendered | `navigate("/onboarding")` → `onboarding-tour-container` | `expect(tour_container).to_be_visible()` | **ready** — same boundary as ELITEA-2235 § Entry path |
| 2 | Locate the "Your Elitea workspace is ready!" banner at the bottom of the page | Banner title visible with exact text | `onboarding-workspace-ready-title` | `expect(ready_title).to_have_text("Your Elitea workspace is ready!")` | **ready** |
| 3 | "Jump in now!" button is visible and styled with a teal/green colour | Button visible, enabled, correct label and fill | `onboarding-workspace-ready-jump-in-button` | `to_be_visible()` + `to_be_enabled()` + `to_have_text("Jump in now!")` + `expect(btn).to_have_css("background-color", "rgb(106, 232, 250)")` | **ready** — colour measured live; see § Risks 1 (theme dependence) |
| 4 | Click the "Jump in now!" button | Control responds | click | action | **ready** |
| 5 | Onboarding card is dismissed / closed | Onboarding surface unmounted | `onboarding-page-container`, `onboarding-tour-container`, `onboarding-workspace-ready-jump-in-button` | `expect(...).to_have_count(0)` on each | **ready** |
| 6 | User is navigated to the default project page (e.g. Chats page) | URL is `/chat`, chat page rendered | `page.wait_for_url("**/chat")` + a chat-page anchor testid | `expect(page).to_have_url(re "/chat$")` | **ready** — `handleJumpIn` navigates to `RouteDefinitions.Chat` (`routes.js`) |
| 7 | Full sidebar navigation is displayed **and functional** | Sidebar visible with its menu items; a menu item navigates | `sidebar-toggle`, `sidebar-menu-item-chat`, `sidebar-menu-item-agents`; then dismiss the prompt and click `sidebar-menu-item-agents` | *displayed*: `to_be_visible()` on the three · *functional*: `expect(page).to_have_url(re "/agents")` after Skip + click | **ready** — decomposed into displayed / dismiss / functional, per #1754. **2 testids needed** for the prompt (below). |
| 8 | Onboarding card is no longer shown on the screen | Still absent after the sidebar interaction | `onboarding-tour-container`, `onboarding-page-container` | `to_have_count(0)` re-asserted at the end | **ready** — deliberate re-assert: proves the onboarding surface does not come back on the next client-side navigation |
| Final | Onboarding card no longer shown | as step 8 | same | same | **ready** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| Interactive-tour first-visit prompt is **shown** on landing | It is part of the live contract of this exact transition (deterministic 4/4) and is the reason step 7 is decomposed; asserting it turns an undocumented surprise into a checked invariant — and its disappearance would be a real product change worth a red | `expect(first_visit_prompt).to_be_visible()` |
| Prompt is **gone** after clicking Skip | Proves the dismissal actually happened before the "functional" assertion, instead of relying on a click that may have hit the backdrop | `expect(first_visit_prompt).to_have_count(0)` |
| Sidebar is present already **before** the prompt is dismissed | Separates "displayed" from "clickable" — the exact distinction #1754 is about; keeps the case's own step 7 wording honestly covered | `to_be_visible()` before Skip |
| Console errors, **excluding the known `MUI: The modal content node does not accept focus.` message** (#1753) | Side-channel check without a hidden green: the excluded message is a filed, open, product-side a11y defect that fires on this exact path; every other console error still fails the test | `assert [e for e in console_errors if "does not accept focus" not in e] == []` with `# Known defect: #1753` |

---

## Testids to add (`add-data-testid` on `EliteaAI/EliteaUI`, branch `automation/testids`)

Both attribute-only additions in
`src/[fsd]/features/interactive-tours/ui/FirstVisitPrompt.jsx`:

| # | testid | Element |
|---|---|---|
| 1 | `interactive-tour-first-visit-prompt` | The `TourCard` root (`role="dialog" aria-modal="true"`) — presence + absence assertions |
| 2 | `interactive-tour-first-visit-skip-button` | The `BaseBtn` labelled **Skip** — clicked on the executed path |

The **Start!** button is deliberately NOT requested: this test never clicks it, and testids go
only on elements tests actually touch (`.agents/testing.md` § Locator policy, ruling #511).

**Do not reuse `interactive-tour-complete-title` / `interactive-tour-complete-icon`.** They are
present inside this prompt only because the shared `TourCardHeader` hardcodes them; they name the
*tour-complete* card and leak into the first-visit prompt. Using them here would bind the spec to
a mis-scoped testid (see findings — reported to the lead as a shared-component testid-naming
issue; pre-existing, not this case's to fix).

---

## Handles Reference

Provenance verified 2026-08-24 after `cd ../EliteaUI && git fetch origin`.

| Element | testid | Provenance |
|---|---|---|
| Onboarding page container (absence) | `onboarding-page-container` | on-`automation/testids` only (awaiting human promotion to main) |
| Tips-card wrapper (absence) | `onboarding-tour-container` | on-`automation/testids` only |
| Workspace-ready banner title | `onboarding-workspace-ready-title` | on-`automation/testids` only |
| "Jump in now!" button | `onboarding-workspace-ready-jump-in-button` | on-`automation/testids` only |
| Sidebar toggle | `sidebar-toggle` | **on-main ✓** (`SidebarBody.jsx`) |
| Project selector trigger | `project-selector-trigger` | **on-main ✓** (`SidebarProjectSelect.jsx`) |
| Sidebar menu items | `sidebar-menu-item-chat`, `sidebar-menu-item-agents` | on-`automation/testids` only — **dynamic**: `testId={\`sidebar-menu-item-${i.value}\`}` (`src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx:272`). Use the class-constant template pattern (`SIDEBAR_MENU_ITEM = '[data-testid="sidebar-menu-item-{}"]'`), never an inline f-string `get_by_test_id`. |
| First-visit prompt card | `interactive-tour-first-visit-prompt` | **needs-adding** |
| First-visit prompt Skip button | `interactive-tour-first-visit-skip-button` | **needs-adding** |

Full sidebar inventory observed live on `/chat` (for whoever needs more): `sidebar-toggle`,
`sidebar-create-button`, `sidebar-menu-item-{chat,agents,pipelines,skills,toolkits,mcps,credentials,applications,artifacts}`,
`sidebar-settings-button`, `sidebar-agent-hub-button`, `sidebar-support-assistant-button`,
`sidebar-collapse-toggle-button`.

---

## Suggested test shape

- File: `automation/tests/ui/onboarding/test_onboarding_jump_in.py` (separate from the tips-card
  spec — this one leaves the onboarding surface and asserts a different screen).
- Markers: shipped as **`p2`** (`pytest.ini`: `p2` = medium priority, matching the case's own
  `priority: medium`), `onboarding`, `regression`, `ui`, `new`.
- One `allure.step` per case step; the Skip dismissal lives inside step 7's block with a comment
  citing #1754.
- Docstring must name the known-defect console filter and link #1753.

---

## Risks / gotchas for the implementer

0. **SHIPPED (implementer, 2026-08-24):** the colour assertion was kept as specified —
   `to_have_css("background-color", "rgb(106, 232, 250)")`, one assertion, with a comment
   naming the default (dark) theme so a failure reads "the theme changed". It passed live on
   the first run. The § Risks 1 fallback was NOT needed.

1. **The colour assertion is theme-dependent.** `rgb(106, 232, 250)` was measured on the default
   (dark) theme via computed `background-color` on `MuiButton-eliteaPrimary`. If the suite ever
   runs a light theme this is the wrong constant — keep it as ONE assertion with a comment naming
   the theme, so a failure reads as "theme changed", not "button broke". If the reviewer judges
   the constant too brittle, the fallback that still covers the case's intent is
   `to_have_class`-free: assert visible + enabled + label and record the colour as evidence-only —
   flag it rather than silently dropping step 3.
2. **Do NOT assert `sessionStorage.onboarding_state` cleanup**, tempting as it is
   (`handleJumpIn` removes the key). It requires `page.evaluate`, which trips the reviewer's
   provenance grep, and the observable is already fully covered by the UI unmount assertions.
3. **Click Skip, not the backdrop.** Escape also skips (`FirstVisitPrompt handleKeyDown`), but the
   backdrop swallows stray clicks — target the Skip testid.
4. The prompt appears **after** the client-side navigation completes; wait on the prompt locator
   (auto-retrying `expect`), never a sleep.
5. `sidebar-menu-item-*` is a dynamic testid — class-level template constant, per
   `.agents/testing.md` § Locator policy.

---

## Evidence

- Live run 2026-08-24: click "Jump in now!" → URL `http://localhost:5173/chat`;
  `onboarding-page-container`, `onboarding-tour-container`, `onboarding-tour-tip-content`,
  `onboarding-workspace-ready-*` all absent; `sidebar-toggle` and `project-selector-trigger`
  visible; `sessionStorage.onboarding_state` = null.
- Prompt probe: modal text "New here? Take a short interactive tour to learn how this section
  works and discover its key features. Skip Start!"; `elementFromPoint` over
  `sidebar-menu-item-agents` returns the backdrop `div`, and a real Playwright click reports
  `intercepts pointer events` (quoted above).
- Console: `MUI: The modal content node does not accept focus.` on 4/4 runs of this path; a direct
  hard navigation to `/chat` (no prompt) produced 0 console errors — control run.

---

## Known defects

| ID | Severity | What | Effect on this spec |
|---|---|---|---|
| **#1753** | MINOR | Interactive-tour first-visit prompt logs `MUI: The modal content node does not accept focus.` every time it opens (deterministic) | Console assertion filters this one message with `# Known defect: #1753`; everything else still fails the test. Not masking — the defect is filed, open and linked. |
| **#1754** | CLARIFICATION (case text) | Case step 7 says the sidebar is "displayed and functional" right after Jump in now!, but the modal prompt blocks it until dismissed | Step 7 is decomposed into displayed → Skip → functional. No step dropped, no weakened assertion. |
