---
name: Platform release-notes modal + "New Models" top banner block the plus-menu on first chat load
description: A full-screen "Announcing ELITEA X.Y.Z!" modal (data-testid="platform-banner-center", close button testid="platform-banner-close") and a "New Models are added" top banner (data-testid="platform-banner-top", same close testid) can both render on the very first /chat navigation of a session and intercept the plus-menu click
type: feedback
tags: [area/chat, type/pitfall]
created: 2026-10-19
---

## What happened

Confirmed live 2026-10-19 (ELITEA-3372 implementation): on a fresh browser
context's first `navigate_to_chat()`, a full-screen MUI Dialog
(`data-testid="platform-banner-center"`, e.g. "Announcing ELITEA 2.0.7!") can
render. It is NOT covered by `BasePage.dismiss_banner_if_present()` (which only
matches `button[aria-label="close"]` inside a z-index>1000 overlay) — this
modal's only control is a button labelled "Got it", testid
`platform-banner-close`.

**Sequential reveal, not simultaneous:** dismissing the center modal can reveal
a SECOND banner — a top banner (`data-testid="platform-banner-top"`, e.g. "New
Models are added: Sonnet 5.5, Opus 5.5, and GPT-6.1 Luna") whose close button
IS `button[aria-label="close"]` + `data-testid="platform-banner-close"` — i.e.
this second one IS handled by the existing `dismiss_banner_if_present()`, but
only becomes visible/clickable after the first one is gone.

Left either undismissed, the next click (plus-menu button, or
`close_modules_panel()`'s outside-click target) gets intercepted:
`<div ... data-testid="platform-banner-center/top"> subtree intercepts pointer
events`.

## The fix

Added `BasePage.PLATFORM_RELEASE_BANNER_CLOSE_BUTTON` (testid rung,
`LocatorDescriptor(testid="platform-banner-close")`) +
`dismiss_platform_release_banner_if_present()` — call it, THEN call the
existing `dismiss_banner_if_present()`:

```python
chat.navigate_to_chat(conversation_id=conversation_id)
chat.dismiss_platform_release_banner_if_present()
chat.dismiss_banner_if_present()
```

Both testids were confirmed live; a non-visible/absent banner is a silent
no-op in both methods (best-effort transit machinery, same spirit as the
existing `dismiss_popups()`).

**Likely session-scoped, not permanent**: dismissing the center modal once did
not reproduce on a LATER navigation within the same browser context in this
session's testing — but every fresh browser context (every pytest `page`
fixture instantiation) saw it again, so the dismiss call belongs in the test
flow, not a one-time setup step.

Related: existing `dismiss_popups()` / `dismiss_banner_if_present()` /
`dismiss_nps_survey_if_present()` in `pages/base_page.py`.
