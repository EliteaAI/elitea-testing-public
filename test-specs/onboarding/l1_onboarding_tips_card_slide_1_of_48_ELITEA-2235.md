# ELITEA-2235: Onboarding — onboarding tips card is displayed, starting at slide 1 / 48

**TMS ID:** ELITEA-2235
**Priority:** high
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2236 and ELITEA-2241 (separate AFS each — they differ in STEPS, not data).
**Surface digest:** `test-specs/onboarding/_surface.md`

---

## Summary

On the onboarding page the product renders the **onboarding tips card** (`OnboardingTour`)
positioned at slide **1 / 48**, showing Tip 1 ("Welcome to ELITEA") with its description and
Quick Action, the ELITEA wordmark above the card, and — once the personal project is ready —
the **"Your Elitea workspace is ready!"** banner with the **"Jump in now!"** button below it.

---

## Preconditions

- Authenticated user (localhost: `auth_state` fast-path via `VITE_DEV_TOKEN`, no Keycloak login).
- The user **has** a personal project (`user.personal_project_id` is non-null) — the standard
  `${TEST_USER}` state. This is what makes the case's own final state (step 8, the
  workspace-ready banner) reachable; see § Entry path below.
- No test data, no seeding, no cleanup. The flow is read-only apart from
  `localStorage["interactive-tour:first-elitea:pending"]`, which the product itself writes
  and the next page consumes.

---

## Entry path — why `/onboarding` as an existing user is the HONEST route (read before implementing)

`Onboarding.jsx` gates its three states purely on Redux `user.personal_project_id` and local state:

| State | Gate (Onboarding.jsx) | What renders |
|---|---|---|
| Welcome | `!showTour && !user.personal_project_id && user.id` | `Welcome` card — **ELITEA-2231's subject** |
| Tour + provisioning | `showTour && !thePrivateProjectIsReady` | `OnboardingTour` **+ `onboarding-progress-footer`** ("Configuring Personal project…") |
| Tour + ready | `showTour && thePrivateProjectIsReady` | `OnboardingTour` **+ `WorkspaceIsReady`** ("Jump in now!") |

`showTour` is initialised `hasClickedGetStarted || !!user.personal_project_id`, and the
`useEffect` at `Onboarding.jsx:130-134` calls `handlePersonalProjectReady()` whenever
`user.personal_project_id` is truthy — which sets `thePrivateProjectIsReady = true`.
So **an existing authenticated user navigating to `/onboarding` lands directly in the third
state**, which is exactly the state this case describes (tips card at 1/48 **and** the
workspace-ready banner in step 8).

The literal "first login" path (`personal_project_id: null`, ELITEA-2231's route, established
there by an author-details route mock) **cannot** produce step 8's banner: with
`personal_project_id` null the page stays in the provisioning state and shows the progress
footer instead. Reaching the banner that way would require the backend to actually provision a
project mid-test.

**Consequence (fidelity):** this AFS specifies **zero substitution** — no `page.route`, no
injected state, no wrong-interface precondition. Every asserted value is produced by the product
from a plain authenticated navigation. The trade is a documented **coverage boundary**: the test
verifies the tips-card contract in the tour+ready state, *not* the first-login gate that reaches
it (that gate is ELITEA-2231's / ELITEA-2232's subject). Do not "improve" this by mocking
`/social/author/` — that would swap an honest observable for a fabricated precondition and would
break step 8 anyway.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | User is logged in | Authenticated session | `auth_state` fixture (localhost dev token) | fixture | **ready** |
| 1 | Log in for the first time; land on the expected landing page | Onboarding page is shown | `navigate("/onboarding")` → page container visible | `expect(page).to_have_url(re "/onboarding")` + `expect(page_container).to_be_visible()` | **ready** — see § Entry path (boundary: tour+ready state, not the first-login gate) |
| 2 | Onboarding tips card automatically displayed in main content area | Card visible without any user action | `onboarding-tour-container` | `expect(tour_container).to_be_visible()` | **ready** — testid exists |
| 3 | ELITEA logo shown at the top centre of the card | Wordmark visible above the card | `onboarding-page-logo` | `expect(page_logo).to_be_visible()` | **ready** — minor case-text drift: the wordmark is rendered by `Onboarding.jsx` **above** the card (`styles.logo`), not inside it. Same element the user sees; no defect, no ticket (cosmetic wording). |
| 4 | First slide title "Tip 1: Welcome to ELITEA" | Title text present | `onboarding-tour-tip-content` (single markdown block) | `expect(tip_content).to_contain_text("Tip 1: Welcome to ELITEA")` | **ready** — decomposed: steps 4-6 all live in ONE testid'd node (see § Handles note 1) |
| 5 | Description "ELITEA is your AI-powered workspace … left sidebar for easy access." | Exact description text present | `onboarding-tour-tip-content` | `expect(tip_content).to_contain_text(_EXPECTED_TIP1_DESCRIPTION)` | **ready** — verified verbatim live |
| 6 | Quick Action "Click the ELITEA logo (top-left) to explore all available menus." | Quick-action text present | `onboarding-tour-tip-content` | `expect(tip_content).to_contain_text("Quick Action: Click the ELITEA logo (top-left) to explore all available menus.")` | **ready** — note the rendered text drops the markdown `**` around `Quick Action:` |
| 7 | Slide counter shows "1 / 48" | Counter text is exactly `1 / 48` | `onboarding-tour-page-indicator` | `expect(page_indicator).to_have_text("1 / 48")` | **ready** — 48 verified against source (`onboardingTips` has 48 entries) and live |
| 8 | "Your Elitea workspace is ready!" banner with "Jump in now!" button visible below the card | Banner title + button visible | `onboarding-workspace-ready-title`, `onboarding-workspace-ready-jump-in-button` | `to_have_text("Your Elitea workspace is ready!")` + `to_be_visible()` / `to_have_text("Jump in now!")` | **ready** — testids exist |
| Final | Banner with "Jump in now!" visible below the card | as step 8 | same as step 8 | same | **ready** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| Previous-slide button is **disabled** at slide 1 | Independent proof that the card really is at the FIRST slide — the case only checks the counter *text*, which a rendering bug could get right while the position is wrong (`TourContent.jsx`: `disabled={currentStep === 1}`) | `expect(prev_button).to_be_disabled()` |
| `onboarding-progress-footer` is **absent** | Distinguishes the tour+ready state from the tour+provisioning state; if the footer were present, step 8's banner could not be (they are mutually exclusive in `Onboarding.jsx`) | `expect(progress_footer).to_have_count(0)` |
| `onboarding-welcome-card` is **absent** | Confirms this is the tour state, not ELITEA-2231's Welcome state — keeps the two onboarding specs from silently asserting each other's screen | `expect(welcome_card).to_have_count(0)` |
| No error-level console messages on `/onboarding` | Standard side-channel check; verified clean 3× live on this page | `assert not console_errors` |

---

## Handles Reference

Provenance verified 2026-08-24 after `cd ../EliteaUI && git fetch origin`, two-stage grep per
`.agents/workflow.md` § Closure record.

| Element | testid | Provenance | Source |
|---|---|---|---|
| Onboarding page container | `onboarding-page-container` | on-`automation/testids` only (awaiting human promotion to main) | `src/pages/Onboarding/Onboarding.jsx` |
| ELITEA wordmark above the card | `onboarding-page-logo` | on-`automation/testids` only | `src/pages/Onboarding/Onboarding.jsx` |
| Tips-card wrapper | `onboarding-tour-container` | on-`automation/testids` only | `src/[fsd]/features/onboarding/ui/OnboardingTour.jsx` |
| Slide tip markdown block (title + description + quick action) | `onboarding-tour-tip-content` | on-`automation/testids` only | `src/[fsd]/features/onboarding/ui/TourContent.jsx` |
| Slide counter | `onboarding-tour-page-indicator` | on-`automation/testids` only | `TourContent.jsx` |
| Previous-slide button | `onboarding-tour-prev-button` | on-`automation/testids` only | `TourContent.jsx` |
| Workspace-ready banner title | `onboarding-workspace-ready-title` | on-`automation/testids` only | `src/[fsd]/features/onboarding/ui/WorkspaceIsReady.jsx` |
| "Jump in now!" button | `onboarding-workspace-ready-jump-in-button` | on-`automation/testids` only | `WorkspaceIsReady.jsx` |
| Progress footer (absence) | `onboarding-progress-footer` | on-`automation/testids` only | `Onboarding.jsx` |
| Welcome card (absence) | `onboarding-welcome-card` | on-`automation/testids` only | `src/[fsd]/features/onboarding/ui/Welcome.jsx` |

**No new testids are needed for this case.** (ELITEA-2236 requests five; see its AFS.)

**Note 1 — steps 4/5/6 share one node.** `TourContent.jsx` renders the whole tip as a single
`<Markdown>` inside `onboarding-tour-tip-content`; the `### Tip 1: …` heading, the description
paragraph and the `**Quick Action:**` paragraph are children of that node with **no testids of
their own**. Splitting them would mean raw handles (`h3`, `p:nth-child`), which this project
forbids, and adding three testids inside a markdown renderer is not possible (the DOM is produced
by the markdown component, not by app JSX). Assert the three strings with `to_contain_text` on the
one node — this is a decomposition, not a dropped step.

**Note 2 — page-object placement.** `automation/pages/onboarding_page.py` exists (ELITEA-2231)
and covers the **Welcome** state only, with an explicit scope boundary in its docstring. The tour
state is a different screen: add the tour/banner locators there (extending the docstring's scope
line) or in a sibling page object — implementer's call, but keep the ELITEA-2231 locators and
`mock_fresh_user_state()` untouched; this case must not use that mock.

**RESOLVED at implementation (2026-08-24, implementer):** the locators were added to the
**existing `OnboardingPage`**, not a sibling. A sibling would have had to re-declare
`onboarding-page-container` / `-page-logo` / `-progress-footer` / `onboarding-welcome-card`
(all needed by this case's presence + absence assertions), breaking the project's
"one testid appears in exactly one file" convention. The module/class docstring scope line was
extended to name both states; every ELITEA-2231 locator, `mock_fresh_user_state()` and
`clear_author_details_mock()` are byte-identical (additive-only diff verified).

---

## Expected values (verified live 2026-08-24)

```python
_EXPECTED_TIP1_TITLE = "Tip 1: Welcome to ELITEA"
_EXPECTED_TIP1_DESCRIPTION = (
    "ELITEA is your AI-powered workspace where you create intelligent agents, "
    "automate workflows with pipelines, and chat with powerful AI models. "
    "Everything you need is organized in the left sidebar for easy access."
)
_EXPECTED_TIP1_QUICK_ACTION = (
    "Quick Action: Click the ELITEA logo (top-left) to explore all available menus."
)
_EXPECTED_SLIDE_COUNTER = "1 / 48"
_EXPECTED_READY_TITLE = "Your Elitea workspace is ready!"
_EXPECTED_JUMP_IN_LABEL = "Jump in now!"
```

Source of truth for the copy: `src/[fsd]/features/onboarding/lib/constants/onboardingTips.constants.js`
(48 entries — `onboardingTips.length` is what feeds the `/ 48` in the counter).

---

## Suggested test shape

**AMENDED at implementation (2026-08-24, implementer):** shipped as
`automation/tests/ui/onboarding/test_onboarding_tips_card.py`, holding ELITEA-2235 **only**.
ELITEA-2236 ships as its own spec file (`test_onboarding_tips_fullscreen.py`) — the batch
dispatch requires one spec per case; they still share the page object, which is where the
"same screen" reuse belongs. Marker shipped as `p1` (`pytest.ini`: `p1` = high priority,
matching the case's own `priority: high`).

- File: `automation/tests/ui/onboarding/test_onboarding_tips_card.py`
- Markers: `p1`, `onboarding`, `regression`, `ui`, `new`.
- One `allure.step` per case step, `"Step N — …"`.
- Console listener attached before navigation (Axis 2).

---

## Risks / gotchas for the implementer

1. **Do not navigate to `/` .** Root redirects to `/onboarding` only for a user *without* a
   personal project; for the standard user it lands on `/chat`. Navigate to `/onboarding`
   directly — the route is public to any authenticated user (`RouteDefinitions.Onboarding`).
2. **Visiting `/onboarding` has a side effect on the NEXT page:** `handlePersonalProjectReady()`
   writes `localStorage["interactive-tour:first-elitea:pending"]=true`, so the first-visit
   interactive-tour prompt will open on whatever page the context visits next. Harmless within
   this test (it never leaves `/onboarding`), but it is why ELITEA-2241 must dismiss that prompt.
3. Slide state is component-local (`useState`), so a fresh context always starts at 1/48 — no
   reset needed, and no cleanup.
4. `48` is data-driven from `onboardingTips.length`. If the product adds a tip, the counter
   assertion is the intended red — update the case, not the assertion, silently.

---

## Evidence

- `test-results/screenshots/ELITEA-2235-step-02-tour-card-slide-1.png` — tips card at 1 / 48 with the workspace-ready banner below.
- Live DOM probe (2026-08-24) returned: tip content = Tip 1 copy verbatim, indicator = `1 / 48`,
  ready title = `Your Elitea workspace is ready!`, jump-in label = `Jump in now!`,
  `onboarding-progress-footer` absent, `onboarding-welcome-card` absent, 0 console errors.

---

## Known defects

None blocking this case. Two issues filed from this cluster, both scoped to ELITEA-2241:
#1753 (MINOR console error from the interactive-tour prompt) and #1754 (case-text clarification).
