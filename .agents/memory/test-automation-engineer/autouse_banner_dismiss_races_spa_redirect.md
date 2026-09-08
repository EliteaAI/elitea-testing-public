---
name: Autouse banner-dismiss races the SPA redirect on deployed envs
description: An unguarded page.evaluate right after a domcontentloaded goto dies on deployed envs and is invisible on localhost
type: feedback
aliases: [execution context was destroyed, banner dismiss race, dismiss_banner_if_present, navigation race, goto domcontentloaded evaluate]
tags: [area/framework, type/flake]
created: 2026-09-07
updated: 2026-09-07
---

## The failure shape

`conftest.py`'s autouse `dismiss_banner_after_navigation` monkey-patches `page.goto`/
`page.reload` to run `BasePage.dismiss_banner_if_present()` **immediately** after every
navigation. `BasePage.navigate()` returns at `wait_until="domcontentloaded"`, so the SPA is
still routing. On deployed envs the app then does a client-side redirect (app-prefix / auth),
which destroys the JS execution context mid-`page.evaluate` →
`playwright._impl._errors.Error: Page.evaluate: Execution context was destroyed, most likely
because of a navigation`, raised out of `page.goto()` and killing the test.

**It killed 10/10 GHA jobs across unrelated feature areas** (run 34092431538, issue #2023) —
49-59 occurrences per job — because *every* page object navigates.

## Why local runs never see it

`auth_state` bypasses login on localhost, so **no redirect fires**. Green locally, red on
every deployed env. Any framework code that runs right after a `domcontentloaded` goto has
this asymmetry — do not conclude "works locally" means "works".

## The pattern that fixes it

Best-effort transit machinery (banner/popup dismissal, cosmetic cleanup) must be
**race-tolerant at its single source**, never patched at call sites. `pages/base_page.py`:
`is_navigation_race_error()` + a bounded `wait_for_load_state("domcontentloaded")` settle +
**one** retry, then give up quietly. Never `except Exception`.

## Verify the tolerated messages against the INSTALLED driver

Do not copy an error-string list from folklore. Grep the shipped bundle:
`.venv/lib/python3.13/site-packages/playwright/driver/package/lib/coreBundle.js`.
In **1.61.0** only two fragments exist for this race — `execution context was destroyed`
and `frame was detached`. The commonly-cited `Cannot find context with specified id` and
`Execution context is not available` have **0 hits** and would be dead tolerance widening
the catch for nothing.

## Gate a race with a unit test, not a UI run

A timing-dependent failure cannot be a merge gate. Stub the page (`evaluate` scripted to
raise) and pin the contract: each tolerated variant swallowed, a *different* Playwright
error propagates, retry budget exactly one, happy path unchanged.
**Red-green properly:** reverting the whole file gives an `ImportError` collection error,
which proves nothing. Strip *only* the try/except and keep the helpers — then the reds are
behavioural (10 failed / 12 passed here).

Related: [[never_assume_a_transition_settled]] · [[verify_your_own_delivery_before_handoff]]
