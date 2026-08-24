# ELITEA-2237: Onboarding — slides can be navigated forward using the Next arrow

**TMS ID:** ELITEA-2237
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2238 and ELITEA-2239 (separate AFS each — see § Why not a family AFS).
**Surface digest:** `test-specs/onboarding/_surface.md`

---

## Summary

The onboarding tips card (`OnboardingTour` → `TourContent`) carries a right-arrow (Next)
`IconButton` beside the `{currentStep} / 48` counter. Each click advances `currentStep` by one and
re-renders the slide's image, tip title, description and Quick Action from
`onboardingTips[currentStep - 1]`. This case walks the first two forward steps: 1 → 2 → 3.

Slide state is component-local `useState` in `OnboardingTour`; a fresh browser context always
starts at `1 / 48`. There is no persistence, no reset, and no test data anywhere in this surface.

---

## Preconditions

Identical entry path to ELITEA-2235/2236 (read `_surface.md` § The three states of `/onboarding`):
an authenticated user **with** a personal project navigating directly to `/onboarding` lands in the
**tour + workspace-ready** state, tips card at `1 / 48`.

- No route mock. **Must NOT call `OnboardingPage.mock_fresh_user_state()`** — with
  `personal_project_id` forced to null the page stays in the provisioning state.
- Navigate to `/onboarding` **directly**; root `/` lands the standard test user on `/chat`.
- No seeding, no cleanup, no shared state → parallel-safe, read-only.

**Fidelity: ZERO substitution.** Every asserted value (counter text, tip copy, image src) is
produced by the product from a plain authenticated navigation plus real clicks.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Log in for the first time; onboarding card is at slide 1/48 | Authenticated, on the expected landing page | `navigate("/onboarding")` → `onboarding-tour-container`, `onboarding-tour-page-indicator` | `expect(tour_container).to_be_visible()` + `expect(page_indicator).to_have_text("1 / 48")` | **asserted** — the case's "first login" wording is the ROUTE into this screen; the screen itself is what is verified (same boundary as ELITEA-2235 § Entry path; the first-login gate is ELITEA-2231/2232's subject) |
| 2 | Right arrow (>) / Next button is active and clickable | Control is enabled | `onboarding-tour-next-button` | `expect(next_button).to_be_visible()` + `to_be_enabled()` | **asserted** — **testid needed** (see § Testids to add) |
| 3 | Click the right arrow (>) | Control responds; next state shown | click on `onboarding-tour-next-button` | action | **asserted** (action; its effect is steps 4-6) |
| 4 | Slide counter advances to "2 / 48" | Counter reads `2 / 48` | `onboarding-tour-page-indicator` | `expect(page_indicator).to_have_text("2 / 48")` | **asserted** — live-confirmed |
| 5 | Slide content updates to "Tip 2: Navigate the Sidebar" | Tip 2 title shown | `onboarding-tour-tip-content` | `expect(tip_content).to_contain_text("Tip 2: Navigate the Sidebar")` | **asserted** — live-confirmed |
| 6 | Description for slide 2 is displayed correctly | Tip 2's body copy | `onboarding-tour-tip-content` (same node) | `expect(tip_content).to_contain_text(<Tip 2 description verbatim>)` + `to_contain_text(<Tip 2 Quick Action verbatim>)` | **asserted** — decomposition, not a dropped step: `TourContent.jsx` renders the whole tip as ONE `<Markdown>` inside `onboarding-tour-tip-content`, so title/description/quick-action carry no testids of their own (see § Handles note 1) |
| 7 | Click the right arrow (>) again | Control responds | click on `onboarding-tour-next-button` | action | **asserted** |
| 8 | Counter advances to "3 / 48" and new tip content is shown | `3 / 48` + Tip 3 copy | `onboarding-tour-page-indicator`, `onboarding-tour-tip-content` | `to_have_text("3 / 48")` + `to_contain_text("Tip 3: Switch Between Projects")` | **asserted** — live-confirmed |
| Final | Counter at "3 / 48", new tip content shown | as step 8 | same | same | **asserted** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| The slide **image** changes with the slide (`src` differs between slide 1, 2 and 3) | The counter and the text could both advance while the illustration stays stuck — a real regression class this case's own steps cannot see. Live values: `welcome-interface.png` → `sidebar-navigation.png` → `project-selector.png` | `expect(tip_image).to_have_attribute("src", re.compile("sidebar-navigation"))` at slide 2, `…project-selector…` at slide 3 |
| The **previous** arrow becomes ENABLED once the user leaves slide 1 | Independent proof that `currentStep` really moved off the first slide (`TourContent.jsx: disabled={currentStep === 1}`) — a counter label alone could be right while the position is wrong | `expect(prev_button).to_be_disabled()` at slide 1, `to_be_enabled()` at slide 2 |
| No error-level console messages across the navigation flow | Side-channel check; verified clean live (0 errors over the whole 1→48 walk). `/onboarding` needs **no** console filter — the `#1753` MUI focus error requires the first-visit prompt, which only appears after "Jump in now!" navigates away | `assert not console_errors` |

---

## Concrete Handles Reference

| Element | Handle (testid-only) | Provenance |
|---|---|---|
| Tips card wrapper | `onboarding-tour-container` | on `automation/testids` only (EliteaAI/EliteaUI@3ba7967d family) |
| Slide counter | `onboarding-tour-page-indicator` | on `automation/testids` only |
| Tip markdown node | `onboarding-tour-tip-content` | on `automation/testids` only |
| Slide illustration | `onboarding-tour-tip-image` | on `automation/testids` only (EliteaAI/EliteaUI@3ba7967d) |
| Previous arrow | `onboarding-tour-prev-button` | on `automation/testids` only |
| **Next arrow** | `onboarding-tour-next-button` | **added for this case** — EliteaAI/EliteaUI@f647488d, `automation/testids` only |

**Note 1 — one markdown node per tip.** `TourContent.jsx` renders the tip as a single
`<Markdown>` child of `onboarding-tour-tip-content`; the heading / paragraph / Quick-Action
elements inside are produced by the markdown renderer, not by app JSX, so **no per-part testid can
be placed** on them. Title, description and Quick Action are therefore asserted as `to_contain_text`
checks on that one node. The rendered text drops the markdown `**` around "Quick Action:".

**Note 2 — no dialog on this path.** This case stays in the embedded card, so every testid above
resolves to exactly ONE node. (The duplicate-testid trap applies only while the fullscreen dialog is
open — ELITEA-2239.)

---

## Expected copy (source of truth: `onboardingTips.constants.js`)

- Slide 2 title: `Tip 2: Navigate the Sidebar`
- Slide 2 description: `Your main navigation lives in the left sidebar: Chat for conversations, Agents for AI assistants, Pipelines for workflows, Collections for organization, and more. Each menu gives you quick access to create and manage your AI resources.`
- Slide 2 Quick Action: `Quick Action: Hover over each sidebar icon to see what it does.`
- Slide 3 title: `Tip 3: Switch Between Projects`

---

## Testids to add (`add-data-testid` on `EliteaAI/EliteaUI`, branch `automation/testids`)

| # | testid | Element | File |
|---|---|---|---|
| 1 | `onboarding-tour-next-button` | The forward `IconButton` (`onClick={onNext}`, `disabled={currentStep === onboardingTips.length}`) beside the page indicator | `src/[fsd]/features/onboarding/ui/TourContent.jsx` |

Attribute-only addition on the existing element — no new DOM node, no hook, no render-prop change
(zero-functional-impact check passes by construction). Naming follows `{section}-{element}-{type}`;
verified unique before adding.

**Shipped:** EliteaAI/EliteaUI@f647488d, pushed to `automation/testids`; **not yet on `main`** —
human cherry-pick pending, same as every other `onboarding-*` testid.

---

## Why not a family AFS

ELITEA-2237 / 2238 / 2239 share a surface and one live session, but they are not flow-variants of
one parameterisable flow: 2237 asserts *slide content* after forward steps, 2238 asserts *boundary
disabled state* at both ends of a 48-slide walk, 2239 asserts *dialog-scoped bidirectional*
navigation. A parameter table would have to carry three different assertion shapes, so each case
gets its own AFS and its own test.

---

## Risks

1. **Do not navigate to `/`** — root redirects to `/onboarding` only for a user *without* a personal
   project; the standard test user lands on `/chat`.
2. **Tip copy is product data.** If the UI team edits `onboardingTips.constants.js`, the Tip 2/3
   text assertions fail legitimately — that is a case-text/product-copy sync question, not a flake.
   The counter and image assertions are copy-independent.
3. The `/ 48` denominator is `onboardingTips.length`. A 49th tip changes every counter string in
   this AFS family (and is exactly the kind of drift these assertions should catch loudly).

---

## Test Steps (implementation order)

1. Navigate to `/onboarding`; card visible; counter `1 / 48`; prev disabled.
2. Next arrow visible + enabled.
3. Click next.
4. Counter `2 / 48`.
5. Tip content contains `Tip 2: Navigate the Sidebar`.
6. Tip content contains the Tip 2 description and Quick Action; image src is `sidebar-navigation`; prev now enabled.
7. Click next again.
8. Counter `3 / 48`; tip content contains `Tip 3: Switch Between Projects`; image src is `project-selector`.
9. Axis 2 — no console errors.
