---
name: Support Assistant widget survives SPA navigation (app-shell mount)
description: Widget is mounted outside the routed subtree — in-app nav never closes it; assert the strong form, never a conditional reopen
type: reference
aliases: [support assistant navigation, widget persistence, ELITEA-2422, app-shell mount]
tags: [area/support-assistant, type/product-behaviour]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

`EliteaUI/src/[fsd]/widgets/support-assistant/ui/SupportAssistant.jsx:33-44` renders
`<EliteaAssistant>` as a **sibling** of `children({ onToggleAssistant })` — i.e. at
app-shell level, outside the routed subtree. React-Router navigation therefore never
unmounts or closes the widget, and never re-fetches the conversation.

Verified live 2026-08-22 (`/chat` → `/agents/all` → `/chat`, widget left open): message
items, `data-role`s, texts and copy-button counts were byte-identical before and after,
and a follow-up message appended to the **same** thread.

## Why it matters for a test

A TMS case that hedges *"widget is still open **or can be reopened via the launcher**"*
is weaker than the live contract. Assert the strong form — still visible, **no reopen
click**. A conditional reopen is a branch that never executes: untested code that would
silently mask a regression to a routed mount.

Same-session proof needs the **text**, not just counts: assert the pre-navigation user
message is still rendered after the follow-up reply.

Related: [[false_bug_1581_support_assistant_send_button]]
