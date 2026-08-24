# ELITEA-2238: Onboarding — left arrow is inactive on slide 1 and right arrow is inactive on slide 48

**TMS ID:** ELITEA-2238
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2237 and ELITEA-2239 (separate AFS each — see ELITEA-2237 AFS § Why not a family AFS).
**Surface digest:** `test-specs/onboarding/_surface.md`

---

## Summary

Both tips-card navigation arrows are boundary-disabled by `TourContent.jsx`:
`disabled={currentStep === 1}` on Previous and `disabled={currentStep === onboardingTips.length}`
on Next. This case verifies both ends of the 48-slide range — that the control is *visually*
inactive **and** that clicking it does not move the slide.

Live-confirmed 2026-08-24: exactly **47** Next clicks take the card from `1 / 48` to `48 / 48`.

---

## Preconditions

Same entry path and fidelity as ELITEA-2237 (read that AFS § Preconditions): authenticated user
**with** a personal project, direct navigation to `/onboarding`, no route mock, no seeding,
no cleanup. **ZERO substitution.**

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Log in for the first time; onboarding card is at slide 1/48 | Authenticated, on the expected landing page | `navigate("/onboarding")` → `onboarding-tour-container`, `onboarding-tour-page-indicator` | `expect(tour_container).to_be_visible()` + `to_have_text("1 / 48")` | **asserted** — same entry-path boundary as ELITEA-2237 row 1 |
| 2 | Left arrow (<) is visually inactive (disabled / greyed out) on slide 1/48 | Control disabled and greyed | `onboarding-tour-prev-button` | `expect(prev_button).to_be_disabled()` **and** a computed-colour check: `color == rgb(104, 108, 118)` (the theme's `text.disabled`), asserted as *different from* the enabled Next arrow's colour in the same DOM state | **asserted** — "visually inactive" is asserted as BOTH the `disabled` property and the greyed colour; live values captured below |
| 3 | Click the left arrow (<); no navigation occurs (stays on 1/48) | Counter unchanged | `onboarding-tour-prev-button` clicked with `force=True`; `onboarding-tour-page-indicator` | `prev_button.click(force=True)` then `expect(page_indicator).to_have_text("1 / 48")` | **asserted** — `force=True` is required: the disabled button has `pointer-events: none`, so a normal Playwright click would fail actionability. Forcing dispatches a real mouse click at the control's position, which is exactly what a user does; the product's own handler ignores it. Not a substitution — the observable (counter unchanged) is produced by the product |
| 4 | Click the right arrow (>) repeatedly until slide 48/48 is reached | Reaches the last slide | `onboarding-tour-next-button` clicked in a bounded loop | loop of 47 real `next_button.click()` calls, each followed by an auto-waiting counter assertion for the expected step | **asserted** — 47 confirmed live. The loop is bounded by a constant (48), not by `while not disabled` — an off-by-one product regression must FAIL, not silently adapt |
| 5 | Slide counter shows "48 / 48" | Counter text | `onboarding-tour-page-indicator` | `expect(page_indicator).to_have_text("48 / 48")` | **asserted** — live-confirmed |
| 6 | Slide content shows "Tip 48: View Message Execution Details" | Tip 48 title | `onboarding-tour-tip-content` | `expect(tip_content).to_contain_text("Tip 48: View Message Execution Details")` | **asserted** — live-confirmed |
| 7 | Right arrow (>) is visually inactive (disabled / greyed out) on slide 48/48 | Control disabled and greyed | `onboarding-tour-next-button` | `expect(next_button).to_be_disabled()` + the same computed-colour check as row 2 | **asserted** — **testid needed**, added for ELITEA-2237 (see § Testids) |
| 8 | Click the right arrow (>); no navigation occurs (stays on 48/48) | Counter unchanged | `onboarding-tour-next-button` clicked with `force=True` | `next_button.click(force=True)` then `expect(page_indicator).to_have_text("48 / 48")` | **asserted** — same force-click rationale as row 3 |
| Final | Stays on slide 48/48 after clicking the right arrow | as step 8 | same | same | **asserted** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| The **opposite** arrow is ENABLED at each boundary (Next enabled at slide 1; Previous enabled at slide 48) | Without this, `to_be_disabled()` on one arrow would still pass if the product disabled *both* arrows — a real regression the case's own steps cannot distinguish from correct behaviour | `expect(next_button).to_be_enabled()` at slide 1; `expect(prev_button).to_be_enabled()` at slide 48 |
| The 47-click walk lands on exactly `48 / 48`, and the loop asserts the counter after **every** click | Turns "click repeatedly until 48" into a per-step contract: an off-by-one, a skipped slide, or a wrap-around fails at the click that caused it rather than at the end | `expect(page_indicator).to_have_text(f"{step} / 48")` inside the loop |
| Slide 48's **image** src is `message-details` | Same reason as ELITEA-2237's image check — the counter and text can advance while the illustration lags | `expect(tip_image).to_have_attribute("src", re.compile("message-details"))` |
| No error-level console messages across the full 1 → 48 walk | Side-channel; verified clean live over the entire walk (0 errors). No filter needed on `/onboarding` | `assert not console_errors` |

---

## Concrete Handles Reference

| Element | Handle (testid-only) | Provenance |
|---|---|---|
| Tips card wrapper | `onboarding-tour-container` | on `automation/testids` only |
| Slide counter | `onboarding-tour-page-indicator` | on `automation/testids` only |
| Tip markdown node | `onboarding-tour-tip-content` | on `automation/testids` only |
| Slide illustration | `onboarding-tour-tip-image` | on `automation/testids` only (EliteaAI/EliteaUI@3ba7967d) |
| Previous arrow | `onboarding-tour-prev-button` | on `automation/testids` only |
| Next arrow | `onboarding-tour-next-button` | EliteaAI/EliteaUI@f647488d, `automation/testids` only |

**Live-captured disabled-state values (2026-08-24):**

| State | `disabled` | computed `color` | computed `pointer-events` |
|---|---|---|---|
| Previous @ slide 1 | `true` | `rgb(104, 108, 118)` | `none` |
| Next @ slide 48 | `true` | `rgb(104, 108, 118)` | `none` |
| Next @ slide 1 (enabled control, contrast baseline) | `false` | *(theme `text.secondary` — read live, asserted only as "different from disabled")* | `auto` |

The greyed-out colour comes from `TourContent.jsx` `styles.navButton['&:disabled'].color =
'text.disabled'`. Asserting the *exact* hex would bind the test to the dark-theme palette; the
shipped assertion pairs `to_be_disabled()` with "disabled colour differs from the sibling enabled
arrow's colour", which survives a theme change while still proving the control is greyed.

---

## Testids to add

None new for this case. `onboarding-tour-next-button` was added while analysing ELITEA-2237
(EliteaAI/EliteaUI@f647488d, `automation/testids` only — **not yet on `main`**).

---

## Risks

1. **The 47-click walk is the slowest part of this spec** (~3-5 s of real clicks). It is deliberate:
   the case says "repeatedly until slide 48/48", and reaching the boundary any other way (injecting
   `currentStep`) would be a terminal substitution of the very state under test.
2. Tip 48's title is product copy (`onboardingTips.constants.js`); an edit fails row 6 legitimately.
3. `pointer-events: none` on the disabled controls makes `force=True` mandatory for rows 3 and 8 —
   a plain `.click()` times out on actionability and would look like a product failure.

---

## Test Steps (implementation order)

1. Navigate to `/onboarding`; card visible; counter `1 / 48`.
2. Prev arrow disabled + greyed; Next arrow enabled (Axis 2).
3. Force-click Prev; counter still `1 / 48`.
4. Click Next 47 times, asserting the counter after each click.
5. Counter `48 / 48`.
6. Tip content contains `Tip 48: View Message Execution Details`; image src is `message-details`.
7. Next arrow disabled + greyed; Prev arrow enabled (Axis 2).
8. Force-click Next; counter still `48 / 48`.
9. Axis 2 — no console errors.
