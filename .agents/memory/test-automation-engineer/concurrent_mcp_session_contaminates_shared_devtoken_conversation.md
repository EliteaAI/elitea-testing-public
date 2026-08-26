---
name: Concurrent MCP session contaminates shared dev-token conversation
description: A live MCP/browser-verify session run while a pytest test also drives localhost with the SAME auth_state/VITE_DEV_TOKEN identity can cross-contaminate "current conversation" state between the two sessions — pytest's message-thread assertions can end up reading the MCP session's conversation content.
type: feedback
---

## What happened (ELITEA-2091 implementation, 2026-08-14)

While debugging a drag-and-drop attachment test, I ran a live MCP browser
exploration probe (creating a "+Chat" conversation, attaching files, sending
a message) WHILE re-running the pytest test in the same time window. The
pytest run then failed with an assertion showing the WRONG conversation's
content: `'...probe testelitea_2091_probe_1.txt...'` — literally the message
and filenames from my MCP probe session, not the pytest test's own
conversation.

Re-running the exact same pytest invocation in isolation (no concurrent MCP
session touching localhost) passed clean, no code change needed. This
confirms it was cross-session state bleed, not a product defect or a test
bug.

## Why

`auth_state`/`VITE_DEV_TOKEN` on localhost is a SINGLE shared backend user
identity across every browser session that authenticates against it — MCP
browser sessions, pytest's own browser contexts, and any other tool driving
localhost:5173 all authenticate as the SAME user. Some app/backend state
(e.g. "last active/created conversation") appears to be tracked per-user
rather than strictly per-browser-session/tab, so concurrent activity from
two different tools under the same identity can race and cross-pollute.

## Rule

**Never drive live exploration (MCP/browser-verify) and a pytest run
concurrently against the same dev-token identity.** If a pytest run fails
with content that looks like it belongs to a DIFFERENT conversation/flow
than the one under test, check first whether a concurrent live session was
touching localhost in the same window before concluding it's a product bug
or a genuine test defect — re-run the pytest invocation in isolation to
rule out contamination before spending further debugging time on it.
