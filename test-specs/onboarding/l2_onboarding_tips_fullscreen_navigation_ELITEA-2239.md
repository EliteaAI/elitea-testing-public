# ELITEA-2239: Onboarding — slides can be navigated forward and backward from the enlarged/fullscreen state

**TMS ID:** ELITEA-2239
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2237 and ELITEA-2238 (separate AFS each — see ELITEA-2237 AFS § Why not a family AFS).
**Surface digest:** `test-specs/onboarding/_surface.md`

---

## Summary

The tips card's expand icon opens a fullscreen MUI Dialog that re-renders the **same**
`TourContent` — image, tip text, counter and both nav arrows — at full size. `currentStep` is
lifted into `OnboardingTour` and shared by both copies, so navigating inside the dialog moves the
embedded card too. This case walks forward twice (1 → 2 → 3) and back once (3 → 2) **from inside
the dialog**.

**Related but distinct:** ELITEA-2236 covers opening/closing the dialog; this case covers
*navigating* while it is open. ELITEA-2236 is merged on `automation/base` and asserts nothing about
in-dialog navigation, so this is a fresh spec, not an `extend-existing`.

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
| 2 | Click the expand icon to open the enlarged fullscreen view | Dialog opens | `onboarding-tour-fullscreen-button` → `onboarding-tour-fullscreen-dialog` | `open_tour_fullscreen()` then `expect(fullscreen_dialog).to_be_visible()` | **asserted** — the dialog's *geometry* (is it really fullscreen) is ELITEA-2236's subject and is not re-asserted here |
| 3 | Slide counter shows "1 / 48" in the enlarged state | Dialog-scoped counter | `[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="onboarding-tour-page-indicator"]` | `expect(dialog_page_indicator()).to_have_text("1 / 48")` | **asserted** — **must be dialog-scoped** (see § Handles note 1) |
| 4 | Click the right arrow (>) in the enlarged view | Control responds | dialog-scoped `onboarding-tour-next-button` | `dialog_next_button().click()` | **asserted** — **must be dialog-scoped**: the testid resolves to 2 nodes while the dialog is open |
| 5 | Counter advances to "2 / 48" and slide content updates | `2 / 48` + Tip 2 | dialog-scoped indicator + tip content | `to_have_text("2 / 48")` + `to_contain_text("Tip 2: Navigate the Sidebar")` on the dialog-scoped nodes | **asserted** — live-confirmed |
| 6 | Click the right arrow (>) again to advance to slide 3/48 | `3 / 48` | dialog-scoped next + indicator | click, then `to_have_text("3 / 48")` + `to_contain_text("Tip 3: Switch Between Projects")` | **asserted** — live-confirmed |
| 7 | Click the left arrow (<) in the enlarged view | Control responds | dialog-scoped `onboarding-tour-prev-button` | `dialog_prev_button().click()` | **asserted** |
| 8 | Counter returns to "2 / 48" and the previous slide content is shown | `2 / 48` + Tip 2 again | dialog-scoped indicator, tip content, image | `to_have_text("2 / 48")` + `to_contain_text("Tip 2: Navigate the Sidebar")` + image src `sidebar-navigation` | **asserted** — live-confirmed; the image re-check is what proves the *content* went back, not just the label |
| 9 | Navigation is consistent with the same behavior as in the collapsed card view | Same slide state in both views | the EMBEDDED (unscoped-but-first) `onboarding-tour-page-indicator` inside `onboarding-tour-container` | after each in-dialog navigation, `expect(embedded_page_indicator).to_have_text(<same value>)`; and after closing the dialog, the embedded card is still at `2 / 48` with Tip 2 | **asserted** — this is the *testable* reading of a step whose case text is a prose judgement. `currentStep` is shared state lifted into `OnboardingTour`, so "consistent" means both copies report the same slide, live-confirmed (`["2 / 48", "2 / 48"]`) — and it survives collapsing the dialog. See § Case-text note |
| Final | Navigation consistent with the collapsed card view | as step 9 | same | same | **asserted** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| While the dialog is open, `onboarding-tour-prev-button` and `onboarding-tour-next-button` each resolve to exactly **2** nodes | Encodes the live DOM contract every dialog-scoped locator in this spec depends on. If a future refactor unmounts the embedded copy, the scoped locators keep passing and this count assertion is what tells the next reader why the scoping exists (same pattern ELITEA-2236 established for the tip node) | `expect(prev_button).to_have_count(2)` + `expect(next_button).to_have_count(2)` while open |
| Dialog-scoped **Previous** arrow is DISABLED at `1 / 48` and ENABLED at `2 / 48` | The boundary rule (`disabled={currentStep === 1}`) must hold for the dialog's copy too, not only the embedded card's — ELITEA-2238 only proves it for the embedded card | `expect(dialog_prev_button()).to_be_disabled()` at step 3, `to_be_enabled()` at step 5 |
| After collapsing the dialog, the embedded card is at `2 / 48` with Tip 2 | Proves the in-dialog navigation *persisted* into the collapsed view rather than being dialog-local — the strongest available form of step 9 | `to_have_text("2 / 48")` + `to_contain_text("Tip 2: …")` on the embedded nodes after `close_tour_fullscreen()` |
| No error-level console messages across the whole flow | Side-channel; verified clean live. No filter needed on `/onboarding` | `assert not console_errors` |

---

## Concrete Handles Reference

| Element | Handle (testid-only) | Provenance |
|---|---|---|
| Tips card wrapper | `onboarding-tour-container` | on `automation/testids` only |
| Expand icon | `onboarding-tour-fullscreen-button` | EliteaAI/EliteaUI@3ba7967d, `automation/testids` only |
| Fullscreen dialog (paper) | `onboarding-tour-fullscreen-dialog` | EliteaAI/EliteaUI@3ba7967d, `automation/testids` only |
| Dialog close (X) | `onboarding-tour-fullscreen-close-button` | EliteaAI/EliteaUI@3ba7967d, `automation/testids` only |
| Slide counter (both copies) | `onboarding-tour-page-indicator` | on `automation/testids` only |
| Tip markdown node (both copies) | `onboarding-tour-tip-content` | on `automation/testids` only |
| Slide illustration (both copies) | `onboarding-tour-tip-image` | EliteaAI/EliteaUI@3ba7967d, `automation/testids` only |
| Previous arrow (both copies) | `onboarding-tour-prev-button` | on `automation/testids` only |
| Next arrow (both copies) | `onboarding-tour-next-button` | EliteaAI/EliteaUI@f647488d, `automation/testids` only |

**Note 1 — the duplicate-testid trap (digest quirk 1).** `OnboardingTour` keeps the embedded
`TourContent` mounted and renders a SECOND copy inside the Dialog, so
`onboarding-tour-page-indicator` / `-tip-content` / `-tip-image` / `-prev-button` / `-next-button`
each resolve to **2 visible nodes** while the dialog is open. Every in-dialog locator must be
scoped through a class constant
(`'[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="…"]'`); an unscoped `expect()`
is a strict-mode violation. The page object already ships `DIALOG_TIP_CONTENT`,
`DIALOG_TIP_IMAGE` and `DIALOG_PAGE_INDICATOR` (ELITEA-2236) — this case adds
`DIALOG_PREV_BUTTON` and `DIALOG_NEXT_BUTTON` in the same shape.

**Note 2 — reading the EMBEDDED copy while the dialog is open (step 9).** The embedded card's
nodes must be reached by scoping *into* `onboarding-tour-container`, not by index: the page object
adds `CARD_PAGE_INDICATOR` / `CARD_TIP_CONTENT` class constants
(`'[data-testid="onboarding-tour-container"] [data-testid="…"]'`) — the dialog's paper is NOT a
descendant of the card wrapper, so this cleanly selects the embedded copy alone. Same class-constant
mechanism, no raw handles.

---

## Case-text note (step 9)

Step 9's expected result — *"navigation is consistent with the same behavior as in the collapsed
card view"* — is a prose judgement, not an observable. It is implemented as the two concrete
invariants the product actually guarantees: (a) both copies report the same slide at every point,
and (b) the slide reached inside the dialog is still current after the dialog is collapsed. This is
a decomposition of the step, not a weakening: no other reading of "consistent" is machine-checkable
without re-running ELITEA-2237's whole collapsed-card walk inside this spec, which would duplicate
that case rather than verify this one. **No clarification ticket filed** — the step is
under-specified, not wrong, and the product behaviour matches its evident intent.

---

## Risks

1. Every in-dialog locator MUST be dialog-scoped (note 1) — an unscoped one fails with a
   strict-mode violation that reads like a product bug.
2. Tip 2/3 copy is product data (`onboardingTips.constants.js`); an edit fails rows 5/6/8
   legitimately.
3. MUI's dialog open/close transition is covered by `expect()` auto-retry — never a sleep.

---

## Test Steps (implementation order)

1. Navigate to `/onboarding`; card visible; counter `1 / 48`.
2. Click the expand icon; dialog visible.
3. Dialog-scoped counter `1 / 48`; dialog prev disabled; prev/next each count 2 (Axis 2).
4. Click the dialog's next arrow.
5. Dialog counter `2 / 48`, Tip 2 copy; dialog prev now enabled; embedded counter also `2 / 48`.
6. Click the dialog's next arrow again; dialog counter `3 / 48`, Tip 3 copy; embedded counter `3 / 48`.
7. Click the dialog's prev arrow.
8. Dialog counter `2 / 48`, Tip 2 copy, image `sidebar-navigation`; embedded counter `2 / 48`.
9. Collapse the dialog; embedded card still at `2 / 48` with Tip 2 (step 9's persistence half).
10. Axis 2 — no console errors.
