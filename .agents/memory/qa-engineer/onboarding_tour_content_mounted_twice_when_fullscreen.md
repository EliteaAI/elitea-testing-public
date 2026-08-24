---
name: Onboarding TourContent is mounted twice while the fullscreen dialog is open
description: Shared tips-card testids resolve to 2 visible nodes with the dialog open; dialog-scoped UPPER_CASE constants are the compliant fix, not a raw-handle exception
type: reference
aliases: [onboarding fullscreen dialog duplicate testid, tour tip content strict mode, onboarding-tour-tip-content two nodes]
tags: [area/onboarding, type/locator]
created: 2026-08-24
updated: 2026-08-24
---

## What

`OnboardingTour.jsx` keeps the **embedded** `TourContent` mounted while the fullscreen
`Dialog` renders a **second** copy. With the dialog open,
`onboarding-tour-tip-content`, `onboarding-tour-tip-image`, `onboarding-tour-page-indicator`
and `onboarding-tour-prev-button` each resolve to **two visible nodes** — an unscoped
`expect(...)` is a Playwright strict-mode violation.

## Why it is NOT a policy exception

This is one component mounted twice, so it is neither the PR #581 state-switched-testid
anti-pattern (one element whose testid VALUE flips) nor the #277 same-element conditional
pair. The compliant disambiguation is a **class-level UPPER_CASE constant chaining two
`[data-testid="…"]` selectors**:

```python
DIALOG_TIP_CONTENT = ('[data-testid="onboarding-tour-fullscreen-dialog"] '
                      '[data-testid="onboarding-tour-tip-content"]')
```

Reviewers: `self.page.locator(self.DIALOG_TIP_CONTENT)` in a method body PASSES the
mechanical locator grep (one-hop check — the constant is a `[data-testid=` string).
No #579 raw-handle waiver is needed or allowed here.

## Related

Same shape as [[artifacts_tree_testid_is_bucket_relative_page_wide_locators_collide]].
Companion fact: the fullscreen dialog testid must sit on `slotProps.paper`, not the
`<Dialog>` root — the Modal root is `position:fixed; inset:0` for EVERY dialog, so a
bounding-box "is it fullscreen" assertion against it is a tautology.
Seen reviewing ELITEA-2235/2236/2241 (PR #1755).
