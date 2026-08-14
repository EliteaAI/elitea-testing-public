---
name: Agent Instructions field tilde-mention quirks
description: agent-instructions-input testid + the two distinct `~`-mention surfaces (Instructions field vs embedded chat) share one "Mention skill" panel component but are separate call sites
type: reference
---

## Two distinct `~`-mention entry points — don't conflate them

Elitea has (at least) two separate places where typing `~` opens a
"Mention skill" suggestion panel scoped to the current Agent's **attached**
Skills only:

1. **Agent detail page → Instructions field** (`ELITEA-1791`'s target).
   Stable testid: `getByTestId('agent-instructions-input')` — accessible
   name "Guidelines for the AI agent". Previously undocumented; confirmed
   live 2026-07-14.
2. **Embedded chat message input** (agent detail page's own chat, or a
   conversation with the agent as participant) — already covered by
   `AgentDetailPage.send_chat_message_with_mention` /
   `ChatPage.send_message_with_skill_mention` (`automation/pages/
   agent_detail_page.py:1146`, `automation/pages/chat_page.py:2113`),
   pre-dating ELITEA-1791.

Both surfaces render the **same** "Mention skill" panel component
(`page.get_by_text("Mention skill", exact=True)` header, then plain
`[cursor=pointer]` rows with skill name + description text, no
`data-testid`/`role="menuitem"` on the rows themselves — unlike the
Skills-attach popper, which DOES use `role="menuitem"`). Don't reuse
`send_chat_message_with_mention` for the Instructions-field flow — it
targets a different input entirely, even though the panel looks/behaves
identically. Give the Instructions-field flow its own page-object method.

## Client-side filter, no network round-trip

Typing `~` in either surface does **not** fire a new network request — the
mention list is a client-side filter over data already fetched via
`GET .../application_skills/prompt_lib/{project}/{agent-id}` (loaded when
the Skills accordion first renders, and re-fetched after every attach/
detach). Confirmed via `browser_network_requests` diffed immediately
before/after typing `~`: zero new requests. **Automation should wait on
the "Mention skill" text becoming visible, never a network-idle wait.**

## Negative-assertion discipline

The whole point of this scoping feature is that an *unattached* skill must
NEVER appear. Assert the negative explicitly — the unattached skill's
name/description text is genuinely absent from the DOM (confirmed via full
accessibility snapshot, not just a screenshot), not merely visually hidden.
A count-only assertion ("exactly 2 rows shown") wouldn't catch a case where
the unattached skill leaks in under an unexpected label.
