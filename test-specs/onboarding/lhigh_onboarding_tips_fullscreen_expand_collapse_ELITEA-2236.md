# ELITEA-2236: Onboarding — tips card expands to fullscreen and collapses with the X button

**TMS ID:** ELITEA-2236
**Priority:** high
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in one live session with ELITEA-2235 and ELITEA-2241 (separate AFS each).
**Surface digest:** `test-specs/onboarding/_surface.md`

---

## Summary

The onboarding tips card carries an expand (fullscreen) icon in its top-right corner. Clicking it
opens a **fullscreen MUI Dialog** titled "Onboarding tips" that re-renders the same slide (image,
tip text, counter, nav buttons) at full size, with an **X** button top-right. Clicking X unmounts
the dialog and returns the user to the embedded card, at the same slide.

---

## Preconditions

Identical to ELITEA-2235 (same screen, same entry path — read that AFS's § Entry path):
authenticated user **with** a personal project, navigate to `/onboarding`, tips card renders.
No substitution, no seeding, no cleanup.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Log in first time; onboarding card visible | Card rendered | `navigate("/onboarding")` → `onboarding-tour-container` | `expect(tour_container).to_be_visible()` | **ready** — same boundary as ELITEA-2235 § Entry path |
| 2 | Locate the expand/fullscreen icon in the top-right corner of the card | Icon present and visible | `onboarding-tour-fullscreen-button` | `expect(fullscreen_button).to_be_visible()` | **ready** — **testid needed** (see § Testids to add) |
| 3 | Click the expand icon | Control responds | click on `onboarding-tour-fullscreen-button` | action | **ready** |
| 4 | Card expands to a fullscreen / enlarged modal state | Fullscreen dialog shown | `onboarding-tour-fullscreen-dialog` + its box size vs viewport | `expect(dialog).to_be_visible()` **and** dialog `bounding_box()` width/height == `page.viewport_size` (±2 px) | **ready** — **testid needed**. The box comparison is what makes "fullscreen" an assertion rather than a word; MUI's `paperFullScreen` class is NOT an allowed handle here. |
| 5 | Modal title "Onboarding tips" in the top-left of the enlarged view | Title text | `onboarding-tour-fullscreen-title` | `expect(dialog_title).to_have_text("Onboarding tips")` | **ready** — **testid needed** |
| 6 | Slide content, image, title, description and page counter all still visible in the enlarged state | All four visible **inside the dialog** | dialog-scoped: `onboarding-tour-tip-image`, `onboarding-tour-tip-content`, `onboarding-tour-page-indicator` | `expect(...).to_be_visible()` on each scoped locator + `to_have_text("1 / 48")` on the scoped counter + `to_contain_text("Tip 1: Welcome to ELITEA")` on the scoped tip | **ready** — **image testid needed**; the other two exist but **MUST be dialog-scoped** (see § Handles note 1 — duplicate-testid trap) |
| 7 | X (close/collapse) button displayed top-right of the enlarged modal | Button visible | `onboarding-tour-fullscreen-close-button` | `expect(close_button).to_be_visible()` | **ready** — **testid needed** |
| 8 | Click the X button | Control responds | click on `onboarding-tour-fullscreen-close-button` | action | **ready** |
| 9 | Modal collapses and returns to the embedded card view on the main page | Dialog gone, embedded card visible | `onboarding-tour-fullscreen-dialog` count 0; `onboarding-tour-container` visible | `expect(dialog).to_have_count(0)` + `expect(tour_container).to_be_visible()` | **ready** — verified: MUI Dialog unmounts (no `keepMounted`) |
| Final | Modal collapsed, embedded card view restored | as step 9 | same | same | **ready** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| While the dialog is open, `onboarding-tour-tip-content` resolves to exactly **2** nodes (embedded + dialog) | Encodes the live DOM contract this spec depends on; if a future refactor unmounts the embedded copy the scoped locators still pass but the count assertion tells the next reader why the scoping exists | `expect(tip_content_any).to_have_count(2)` while open |
| After collapse, `onboarding-tour-tip-content` resolves to exactly **1** node | Proves the dialog really unmounted rather than merely hiding — a hidden-but-mounted dialog would break every later unscoped locator | `expect(tip_content_any).to_have_count(1)` |
| Slide position survives the expand/collapse round trip (`1 / 48` before, in dialog, and after) | `currentStep` is shared state lifted in `OnboardingTour`; a regression that remounts `TourContent` would silently reset the user's slide | `to_have_text("1 / 48")` at all three points |
| No error-level console messages across the expand/collapse cycle | Side-channel check; verified clean live over two open/close cycles | `assert not console_errors` — see § Known defects for the one message that must NOT be confused with this flow |

---

## Testids to add (`add-data-testid` on `EliteaAI/EliteaUI`, branch `automation/testids`)

All five are **attribute-only additions** — no new DOM nodes, no new hooks, no replaced MUI
components (zero-functional-impact check passes by construction).

| # | testid | Element | File / line anchor |
|---|---|---|---|
| 1 | `onboarding-tour-fullscreen-button` | The `IconButton` with `aria-label="View tour in full screen"` (top-right of the card) | `src/[fsd]/features/onboarding/ui/OnboardingTour.jsx`, the `IconButton` above `styles.tourFullScreenButton` |
| 2 | `onboarding-tour-fullscreen-dialog` | The `<Dialog fullScreen open={isTourFullScreen}>` root | same file |
| 3 | `onboarding-tour-fullscreen-title` | The `<Typography variant="headingMedium">Onboarding tips</Typography>` in `styles.tourDialogHeader` | same file |
| 4 | `onboarding-tour-fullscreen-close-button` | The `IconButton` with `aria-label="Close full screen tour"` in the dialog header | same file |
| 5 | `onboarding-tour-tip-image` | The `<Box component="img" src={onboardingTips[currentStep-1].image} alt="Elitea">` | `src/[fsd]/features/onboarding/ui/TourContent.jsx` |

Naming follows `{section}-{element}-{type}`; verified unique — none of the five exists on
`origin/main` or `origin/automation/testids` as of 2026-08-24 (fetched, two-stage grep).

**About #5:** `TourContent` is rendered twice while the dialog is open, so this testid (like
`onboarding-tour-tip-content`, `-page-indicator`, `-prev-button`) legitimately matches two nodes
in that state. This is **not** the PR #581 state-switched-testid anti-pattern (one element whose
testid VALUE flips) and not the #277 conditional-pair shape — it is one component mounted twice.
Disambiguation is by scoping, below.

---

## Handles Reference

Provenance verified 2026-08-24 after `cd ../EliteaUI && git fetch origin`.

| Element | testid | Provenance |
|---|---|---|
| Tips-card wrapper | `onboarding-tour-container` | on-`automation/testids` only (awaiting human promotion to main) |
| Tip markdown block | `onboarding-tour-tip-content` | on-`automation/testids` only |
| Slide counter | `onboarding-tour-page-indicator` | on-`automation/testids` only |
| Previous-slide button | `onboarding-tour-prev-button` | on-`automation/testids` only |
| Expand/fullscreen button | `onboarding-tour-fullscreen-button` | **needs-adding** |
| Fullscreen dialog | `onboarding-tour-fullscreen-dialog` | **needs-adding** |
| Dialog title | `onboarding-tour-fullscreen-title` | **needs-adding** |
| Dialog X (close) button | `onboarding-tour-fullscreen-close-button` | **needs-adding** |
| Slide image | `onboarding-tour-tip-image` | **needs-adding** |

**Note 1 — the duplicate-testid trap (the single most important thing in this spec).**
`OnboardingTour.jsx` keeps the **embedded** `TourContent` mounted while the fullscreen `Dialog`
renders a **second** `TourContent`. Verified live: with the dialog open,
`onboarding-tour-tip-content`, `onboarding-tour-page-indicator` and `onboarding-tour-prev-button`
each resolve to **2 elements, both with non-zero client rects** — so an unscoped
`expect(...).to_be_visible()` raises a Playwright **strict-mode violation**, and an unscoped
`to_have_text` is ambiguous. Every step-6 assertion must go through dialog-scoped class constants
(`.claude/rules/page-objects.md` UPPER_CASE `[data-testid="…"]` constants, which is compliant
testid-only locating):

```python
# class level, e.g. in the onboarding tour page object
DIALOG = '[data-testid="onboarding-tour-fullscreen-dialog"]'
DIALOG_TIP_CONTENT = '[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="onboarding-tour-tip-content"]'
DIALOG_TIP_IMAGE = '[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="onboarding-tour-tip-image"]'
DIALOG_PAGE_INDICATOR = '[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="onboarding-tour-page-indicator"]'
```

The dialog title and close button live only inside the dialog, so their plain
`LocatorDescriptor(testid=…)` fields are unambiguous.

---

## Suggested test shape

- File: `automation/tests/ui/onboarding/test_onboarding_tips_card.py` (shared with ELITEA-2235).
- Markers: `p2` *(case priority high — follow the suite's mapping)*, `onboarding`, `regression`, `ui`.
- One `allure.step` per case step.
- No teardown needed — the dialog is closed by step 8, and context state is per-test.

---

## Risks / gotchas for the implementer

1. **Escape also closes the dialog** (`OnboardingTour.jsx` `handleKeyDown`). The case asks for the
   X button — click the button, do not press Escape.
2. Do not assert MUI class names (`MuiDialog-paperFullScreen`) — raw handle, forbidden. Use the
   bounding-box-vs-viewport comparison for step 4.
3. The dialog animates (MUI default transition). Use `expect(...).to_be_visible()` /
   `to_have_count(0)` — Playwright's auto-retry covers the transition; never a sleep.
4. Everything about the entry path (why `/onboarding` as an existing user, why no mock) is in
   ELITEA-2235's AFS § Entry path — read it before writing the fixture.

---

## Evidence

- `test-results/screenshots/ELITEA-2236-step-04-fullscreen-dialog.png` — fullscreen dialog with
  "Onboarding tips" title, slide image, tip text, `1 / 48` counter and the X button.
- Live probe with the dialog open (2026-08-24): `role="dialog"`, classes include
  `MuiDialog-paperFullScreen`; `onboarding-tour-tip-content` × 2 (one `inDialog: true`),
  `onboarding-tour-page-indicator` × 2 (both `1 / 48`), dialog image
  `src=/src/assets/onbording/welcome-interface.png`.
- After clicking X: dialog absent, close button absent, testid counts back to 1, indicator still
  `1 / 48`, embedded card visible. Two open/close cycles, 0 console errors.

---

## Known defects

None in this flow. One console error observed in the same session — `MUI: The modal content node
does not accept focus.` — was traced to the **interactive-tour first-visit prompt on `/chat`**
(ELITEA-2241's path), **not** to this fullscreen dialog: a control run that opened and closed this
dialog twice without leaving `/onboarding` produced 0 console errors. Filed as **#1753** so nobody
re-attributes it to this case.
