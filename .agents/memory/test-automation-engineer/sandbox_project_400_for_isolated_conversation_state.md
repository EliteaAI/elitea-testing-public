---
name: Sandbox project 400 for isolated conversation state
description: Project 400 ("UI Testing") is a genuinely empty sandbox — use it for any case needing a clean conversation/folder count precondition
type: reference
---

Project **400 ("UI Testing")** is confirmed live (2026-08-15, ELITEA-2115/
2116/2117) to be a genuinely empty sandbox — `ConversationAPI(browser_cookies=[],
project_id="400").list_conversations()` returns `total: 0`, both before and
after a session, once temp data is cleaned up. Use it (via
`ConversationAPI(browser_cookies=_browser_cookies, project_id="400")` +
`chat.switch_project("400")`) for ANY case whose precondition needs an exact
conversation/folder COUNT — "exactly one conversation", "no folders", "empty
project" — instead of trying to temporarily clear a shared project.

**Do NOT use for this** — both already carry pre-existing data other analyses
reuse or that has unconfirmed origin:
- Project 471 ("Elitea Testing Team") — "Review attached documents" (id 420)
  is repeatedly reused/restored by many chat analyses (see `_surface.md`).
- Project 399 (Private, `settings.elitea_project_id` default) — carries 4
  non-`autotest_`-named conversations ("GitHub docs lookup", "Docs lookup",
  "Tell about Elitea" x2) of unconfirmed origin — NOT safe to assume
  disposable.

**Isolation discipline**: any test using project 400 must assert it starts
empty (`get_conversation_link_count() == 0` before seeding) and clean up
everything it creates — a future test polluting it silently breaks every
other test relying on "project 400 = empty".

`findNextConversation()` (`useDeleteConversation.js`) is scope-aware for
ungrouped conversations (searches only OTHER ungrouped conversations, not
folder-nested ones) — the true empty/welcome-state ("last conversation
deleted") branch triggers whenever zero OTHER ungrouped conversations exist,
even with folders still present. Full mechanism + a confirmed isolated
defect from deleting the true last conversation (URL doesn't clear —
elitea-testing-public#1523) are in `test-specs/chat-interface/_surface.md`
§ "Conversation deletion — folder-preserved, last-conversation empty state,
modal styling/dismissal, and a project-400 sandbox discovery".
