---
name: Support Assistant launcher click quirk
description: A MUI tooltip wrapper intercepts clicks on the launcher — click the WRAPPER, not the button; JS-evaluate is no longer needed
type: reference
aliases: [support assistant launcher, elitea-assistant-button, sidebar-support-assistant]
tags: [area/support-assistant, type/quirk]
created: 2026-07-10
updated: 2026-08-22
---

## The quirk

A native Playwright click on the launcher (`button.elitea-assistant-button`,
`aria-label="Support Assistant"`) times out: a MUI tooltip clone
(`div[data-tour="sidebar-support-assistant"][data-mui-internal-clone-element="true"]`)
intercepts pointer events on the button.

## The fix — click the wrapper, NOT the button (verified 2026-08-22)

**Correction to the pre-2026-08-22 version of this note, which said a JS-evaluate click was
mandatory.** It is not. A genuine Playwright pointer click on the *intercepting wrapper*
works first try:

```python
page.locator('[data-tour="sidebar-support-assistant"]').click()   # opens the widget
```

Verified live on `http://localhost:5173/chat` (2026-08-22 triage): the native click on the
button timed out with the interception log, then the wrapper click opened the widget
("ELITEA Support") immediately. Prefer this — it is a real user-equivalent gesture, so it
carries no fidelity-declaration burden, unlike `page.evaluate`'s synthetic `btn.click()`
still used by `SupportAssistantPage.open_widget()`.

The **Close (X)** button (`button[aria-label="Close chat"]`) never had this problem.

## Testids ARE addable here — the "third-party" framing is SUPERSEDED

The pre-2026-07-23 version of this note called the widget third-party and concluded
`add-data-testid` "cannot remediate any Support Assistant selector". **That is wrong and is
superseded by canon ruling #705** (`.agents/testing.md` § Locator policy, connected-first-party
-repo bullet): the widget is `@eliteaai/elitea-assistant` — **our** repo, cloned as the sibling
`../elitea_assistant`, with its own `automation/testids` integration branch, aliased live into
the dev server by `VITE_ASSISTANT_LOCAL=1` (`EliteaUI/vite.config.js`). Missing testids there
are *work to do in that repo*, not a #579 scope exception.

**Update 2026-08-27 (ELITEA-1802 re-analysis).** The "zero `data-testid` attributes" state above
is over. Waves ELITEA-2418/2419/2420/2421/2423 added **17** `support-assistant-*` testids on
`EliteaAI/elitea_assistant` `origin/automation/testids`; all 17 confirmed rendering in the live
DOM through the alias on 2026-08-27, and **none is on that repo's `origin/main`** (awaiting human
promotion, then an EliteaUI `@eliteaai/elitea-assistant` dep bump — the connected repo's extra
promotion hop). The launcher itself now has `sidebar-support-assistant-button` in **EliteaUI**
(`SidebarBody.jsx`), and clicking that testid natively opens the widget first try — so
`open_widget_via_sidebar()` is preferred over the legacy JS-evaluate `open_widget()`.
The remaining `fallback=` fields in `support_assistant_page.py` are grandfathered tech debt to
migrate, not precedent.

Related: [[support_assistant_response_latency_and_no_streaming]]
