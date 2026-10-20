---
name: Hardening-gate RED on ELITEA-3370 — "Announcing ELITEA 2.0.7" banner blocks plus-menu-button
description: Hardening gate for batch builder-modules-chat-2459, 2026-10-19 — first n=1 run against DEV went RED deterministically (3/3 identical inside pytest-rerunfailures) at Step 1's open_internal_tools_menu(), not navigate_to_chat(). A release-announcement MuiDialog ("Announcing ELITEA 2.0.7!", data-testid="platform-banner-center") intercepts clicks on plus-menu-button; existing dismiss_banner_if_present()/dismiss_popups() only clicks button[aria-label="close"] inside a high-z-index ancestor, and this dialog's dismiss control is a "Got it" button, not a close icon, so it is never found/clicked.
type: feedback
tags: [area/chat, area/gate, type/environment]
created: 2026-10-19
---

## What happened

Gating ELITEA-3370's spec (`tests/ui/chat/test_builder_modules_disabled.py::TestBuilderModulesDisabledPreventsEntityCreation::test_builder_modules_disabled_prevents_entity_creation`)
for batch `builder-modules-chat-2459`. First `gate-case.mjs --n 1` attempt hit the
**known** `missing_env_test_app_prefix_silently_empty` trap (sandbox had no
`automation/.env.test`, `APP_PREFIX` unset) — fixed by exporting
`APP_PREFIX=/app` in the run command, same workaround the implementer's own
daily log already recorded for this same case.

With `APP_PREFIX` fixed, navigation now succeeds (`navigate_to_chat` passes),
but the test still goes RED **deterministically** — pytest-rerunfailures
burned both reruns, 3/3 identical failures, same screenshot:

```
tests/ui/chat/test_builder_modules_disabled.py:107: in test
    chat.open_internal_tools_menu()
pages/chat_page.py:3808: in open_internal_tools_menu
    self.plus_menu_button.click()
playwright._impl._errors.TimeoutError: Locator.click: Timeout 10000ms exceeded.
  - <div ... class="MuiDialog-container ... css-fh1hs4"> from
    <div role="presentation" data-testid="platform-banner-center"
         class="MuiDialog-root MuiModal-root ...">
    subtree intercepts pointer events
```

Screenshot shows a centered modal: **"Announcing ELITEA 2.0.7!"** release-notes
dialog with a **"Got it"** button — not the top banner strip
`dismiss_banner_if_present()` already handles. `_click_banner_close_button()`
only queries `button[aria-label="close"]` inside a high-z-index ancestor; this
dialog's dismiss control has no such aria-label (it's a labeled "Got it" MUI
button), so the existing dismissal machinery silently finds nothing and the
dialog stays up, eating every click underneath it.

## Why this is NOT this batch's fault (blast-radius ruling)

`chat_page.py`'s only diff in this batch is a pure *addition* —
`GENERATED_ENTITY_CHIP` + `message_has_generated_entity_chip()` — nothing in
the diff touches `plus_menu_button`, `open_internal_tools_menu`,
`dismiss_banner_if_present`, or navigation. `plus_menu_button`'s declaration
predates this batch entirely (last touched in the ELITEA-3370 test commit only
by nothing — grep confirms no modification). This is a **pre-existing
environment-timing gap**: a NEW release-announcement dialog type DEV started
serving (2.0.7) that the dismissal helper's selector doesn't cover, surfaced
now because this is the first gate run to hit a cold chat page after that
dialog started appearing.

## What to do next time this fires

1. Confirm it's the same dialog (`data-testid="platform-banner-center"` +
   "Announcing ELITEA" text + "Got it" button) via the FAIL screenshot before
   assuming it's a flake — it is reproducible 100% from a fresh browser
   context hitting `/chat` for the first time in the session.
2. This is a gate finding, not something the gate agent fixes — report it to
   the lead as a RED with this exact signature; the fix (teach
   `dismiss_popups()`/`_click_banner_close_button()` to also click the "Got
   it" button on `platform-banner-center`, or call it from
   `open_internal_tools_menu()` before the plus-menu click) is implementer/
   lead-routed work, not something to patch mid-gate.
3. Do not burn retries chasing this as a fluke — it was 3/3 identical inside
   one pytest-rerunfailures invocation already; a 2nd/3rd independent gate
   `--n 1` run will almost certainly reproduce identically until the
   dismissal helper is fixed.

Related: [[../qa-engineer/missing_env_test_app_prefix_silently_empty]] (the
APP_PREFIX trap hit first, same session, same case).
