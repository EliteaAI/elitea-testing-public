---
name: Platform release-notes modal (2.0.7+) blocks plus-menu — shared fix landed
description: BasePage.dismiss_platform_release_banner_if_present() (testid platform-banner-close) now runs from dismiss_popups() AND ChatPage.open_internal_tools_menu(); call it anywhere else that clicks plus_menu_button on a cold /chat load
type: feedback
tags: [area/chat, area/gate, type/environment]
created: 2026-10-19
---

## What this entry replaces

Supersedes the "no fix applied" state recorded in
`gate_elitea_3370_release_banner_intercepts_plus_menu.md` — that entry's
root-cause analysis was correct; this entry records the fix that landed on
top of it (fixer round 1, batch `builder-modules-chat-2459`, 2026-10-19).

## The fix

`BasePage` gained:
- `PLATFORM_RELEASE_BANNER_CLOSE_BUTTON = LocatorDescriptor(testid="platform-banner-close", …)`
- `dismiss_platform_release_banner_if_present(timeout=2000)` — best-effort,
  same shape as `dismiss_banner_if_present()`: waits briefly for the "Got it"
  button, clicks it if present, swallows the timeout quietly if not.

Two call sites, both additive:
1. `BasePage.dismiss_popups()` — calls it FIRST, ahead of
   `dismiss_banner_if_present()` and `dismiss_nps_survey_if_present()`. Order
   matters: the release-notes modal is a full-screen overlay that sits on top
   of (and, once closed, can itself reveal) the banner overlay the second
   helper targets.
2. `ChatPage.open_internal_tools_menu()` — calls it immediately on entry,
   before `plus_menu_button.click()`. This is belt-and-suspenders for callers
   that reach the modules menu WITHOUT going through `BasePage.navigate()`
   first (e.g. already on `/chat`, or a raw `page.goto()`) — those skip
   `navigate()`'s own `dismiss_popups()` call entirely.

Both diffs are additive-only (verified: `git diff -- base_page.py chat_page.py
| grep -E '^-[^-]'` only touches `dismiss_popups()`'s own docstring, not its
body logic or any other method). Locator delta: +1 declared (testid rung),
unmanaged handles unchanged (351).

## If this gate signature recurs on a DIFFERENT call site

If a future gate run shows `plus_menu_button.click()` (or any other
`platform-banner-center`-adjacent click) intercepted by the modal from a
THIRD call site that doesn't go through `navigate()` or
`open_internal_tools_menu()`, add `self.dismiss_platform_release_banner_if_present()`
at that call site too — the helper is cheap (2s timeout, swallows absence)
and idempotent. Don't re-derive a new helper; this one is the shared fix.

## Regression test

`automation/tests/unit/test_platform_release_banner_dismissal.py` pins:
- the helper's own present/absent contract,
- that `open_internal_tools_menu()` dismisses the banner STRICTLY BEFORE the
  plus-menu click (the exact ordering the gate failure needed),
- that a caller reaching the menu via `open_internal_tools_menu()` without a
  shown banner still proceeds normally,
- that `dismiss_popups()` calls the three dismissals in the right order.

Verified these tests actually catch the regression: reverting the fix
(`git stash` on `base_page.py`/`chat_page.py`) turns 4 of 5 new tests red
with exactly the failure shapes you'd expect (`AttributeError` for the
missing method, ordering assertion failures for the missing call site).

## Separate, unrelated finding surfaced while verifying the fix live

Re-running ELITEA-3370's spec against DEV after the fix got PAST the
originally-diagnosed failure (plus-menu now opens cleanly — screenshot
confirms Modules panel's switch list renders) but then hit a DIFFERENT
timeout: `wait_for_ai_response` — "Copy button never appeared" — at Step 3
(the skill-creation message's AI response). This matches the sibling
ELITEA-3372 unit's same-day BLOCKED note on a live DEV predict-pipeline
outage ("every turn stalls after `agent_llm_start`"), not a product/test
defect in this spec. Did not range into fixing it (out of scope for this
fixer dispatch — a different, live-environment cause); reported to the lead
to classify/re-gate once the outage clears.

Related: [[gate_elitea_3370_release_banner_intercepts_plus_menu]]
