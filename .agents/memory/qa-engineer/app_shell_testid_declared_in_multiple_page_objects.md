---
name: App-shell testid declared in multiple page objects
description: sidebar-toggle now sits in 3 page objects vs conventions' one-file rule — review trap, fix is BasePage
type: feedback
aliases: [sidebar-toggle duplication, one testid one file, app-shell chrome locator]
tags: [area/page-objects, type/review-trap]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`.agents/conventions.md` says *"one `data-testid` appears in exactly one file"*. App-shell
chrome breaks it quietly: `sidebar-toggle` is declared as a `LocatorDescriptor` in
`automation/pages/chat_page.py`, `onboarding_page.py` and (since ELITEA-2233/2234, PR #1766)
`sidebar_header_page.py`. Each addition looks locally correct — the new page object genuinely
needs the header anchor — so nobody blocks it, and the count keeps growing.

## What to do at review

Precedent is not authority: the two prior declarations do NOT license a third. But the
compliant fix is **not** local — it is to promote the testid to `BasePage` (which already owns
`sidebar-collapse-toggle-button` exactly this way) and let the three page objects inherit it.
That is a subtractive change to shared-caller files, which Hard Rule 3 (additive-only) makes
unsafe mid-batch.

So: report it as a finding + route a `question` card proposing the canon shape for app-shell
chrome locators; do not solo-block a green, honest case on it. Block only once the canon card
exists and is ignored (declared-improvisation protocol limit 3).

Related: [[project_briefing]]
