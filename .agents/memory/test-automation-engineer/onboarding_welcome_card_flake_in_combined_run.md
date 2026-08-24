---
name: Onboarding welcome-card precondition flakes in a combined onboarding run
description: ELITEA-2232's fresh-user Welcome precondition missed once in a 4-spec invocation; not reproducible, 4 clean runs after.
type: project
aliases: [onboarding-welcome-card, mock_fresh_user_state, ELITEA-2232 flake, onboarding gate flake]
tags: [area/onboarding, type/flake]
created: 2026-08-24
updated: 2026-08-24
---

## Symptom

`tests/ui/onboarding/test_onboarding_provisioning.py::TestOnboardingProvisioning::
test_get_started_starts_provisioning_poll_and_shows_tips_with_progress_footer`
(ELITEA-2232) failed its own **precondition** step:

```
expect(onboarding_page.welcome_card).to_be_visible(timeout=10000)
AssertionError: Locator expected to be visible / Actual value: None
  - waiting for get_by_test_id("onboarding-welcome-card")
```

i.e. `mock_fresh_user_state()` was installed, `/onboarding` was reached, but the
Welcome card never rendered — the app had presumably already moved past the
first-login state.

## When

Observed exactly ONCE, on the batch-onboarding-w2 hardening gate (2026-08-24),
when the four new onboarding specs ran in ONE pytest invocation with the
provisioning spec LAST (tips_card → tips_fullscreen → jump_in → provisioning).

## Not reproducible

- standalone: PASS (29.7s)
- same 4-spec command, same order: PASS ×3 (53.0s / 53.0s / 51.2s)
- whole `tests/ui/onboarding/` dir (5 specs, alphabetical — provisioning 2nd): PASS

So it is **not** deterministic order-dependence. Plausible mechanism worth
checking if it recurs: the earlier specs leave `sessionStorage.onboarding_state`
or `localStorage["interactive-tour:first-elitea:pending"]` behind, or the
fresh-user route mock lost the race with the first `authorDetails` call from
`ProtectedRoutes.jsx`. The spec's own comment already flags that the mock must be
installed before the first `goto()`.

## What to do next time

Re-run once. If it reproduces, look at storage carry-over between contexts before
suspecting the mock. Record further occurrences here.

Related: [[onboarding_provisioning_state_entry]] · [[onboarding_tour_state_without_mocks]]
