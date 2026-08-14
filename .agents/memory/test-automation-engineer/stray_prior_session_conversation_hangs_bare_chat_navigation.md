---
name: A stray conversation left over from an EARLIER, unrelated session can hang bare /chat navigation for every later test
description: chat.navigate_to_chat() (bare /chat, no conversation id) got stuck on an infinite loading spinner, deterministically (2/2), before the test under construction had done anything itself. Root cause was a pre-existing "HI Chat" conversation + "echo" agent left over from an EARLIER (analyst) session in the same shared local dev backend — not caused by the new test's own code. Deleting the stray conversation+agent via the API fixed it immediately (2/2 clean afterward).
type: feedback
---

## What happened (ELITEA-2166 implementation)

A brand-new test (`test_create_agent_via_chat_canvas.py`) failed
deterministically, 2/2, at its very FIRST interactive step — clicking
`plus-menu-button` a second time (to close the menu) timed out with a MUI
"subtree intercepts pointer events" error. The failure screenshot showed
the entire main chat panel stuck on an infinite `CircularProgress` spinner,
with a "HI Chat" conversation visible in the sidebar's Today group.

The test's own `Setup` step only calls `chat.navigate_to_chat()` +
`chat.wait_for_page_load()` + `chat.switch_project(...)` before this —
nothing in the test itself should have been able to cause a stuck spinner.

## Root cause

`ConversationAPI.list_conversations()` showed exactly ONE conversation in
the Private project: id 5617, name "HI Chat", `created_at` from **hours
before this session even started**. `AgentAPI.get_agent()` on its
attached agent participant (id 5476) showed name="echo",
description="test agent" — i.e. this was the **analyst's own leftover
exploration artifact** from producing the AFS (the AFS's own § Known
Defects describes creating an agent named "echo" and sending "hi" to
reproduce issue #708), never cleaned up after that session ended.

`ChatPage.navigate_to_chat()`'s own docstring already documents that the
SPA "may redirect to the last-viewed conversation stored in the browser
session" — that stale "last-viewed" pointer, combined with something about
this specific leftover conversation/agent pair being unable to render
cleanly (possibly connected to the SAME #708 investigation that produced
it), stuck the whole page in a loading state for every subsequent test
that touched bare `/chat` in this project — not just this one.

## The fix

```python
from api import ConversationAPI, AgentAPI
capi = ConversationAPI(browser_cookies=[])
capi.delete_conversation(5617)
capi.close()
aapi = AgentAPI(browser_cookies=[])
aapi.delete_agent(5476)
aapi.close()
```

Confirmed via `capi.list_conversations()` returning 0 rows afterward, and
2/2 clean green pytest runs immediately following the cleanup (previously
2/2 identical failures).

## When this applies / diagnostic shortcut

If a UI test that starts with a bare `chat.navigate_to_chat()` (no
conversation id) hangs on an infinite spinner **before your own test logic
has done anything meaningful**, and the failure is deterministic (not a
one-off flake): **before debugging your own selectors/waits**, check for
stray debris via the API:

```python
from api import ConversationAPI
api = ConversationAPI(browser_cookies=[])
data = api.list_conversations()
print(data.get('rows', data))
```

A near-empty project with ONE orphaned conversation (often named after
whatever the LAST message sent was — e.g. "HI Chat" from a `send_message
("hi")` flow) is the signature. Cross-check its participants for an
orphaned agent from the same abandoned session and delete both. This is
environmental debris from a DIFFERENT prior session's incomplete cleanup —
not a defect in the current test's own code — but it silently breaks
every later test that touches the same project's bare `/chat` route until
cleared. Distinct from (but easy to confuse with) the already-documented
`chat_created_conversation_stuck_active_after_navigate_away.md` defect
(#692) — that one is a SAME-SESSION sidebar-click no-op after navigating
away; this one is a cross-session, page-load-time hang from someone else's
leftover data.

## Broader lesson for cleanup discipline

Every implementer session (this one included, until this incident) tends
to assume its own `try/finally` cleanup is sufficient. It is — for THIS
session's own data. But manual Phase-2 `playwright-cli`/`browser-verify`
exploration that creates real server-side entities (agents, conversations)
needs the SAME cleanup discipline as the automated test itself, and a
crashed/aborted exploration session (or one where the agent simply forgot)
leaves debris that can silently break a LATER, unrelated session's tests.
When you hit an inexplicable stuck-load failure at the very start of a
fresh test, checking for stray prior-session debris via the API is now a
cheap first move, not a last resort.
