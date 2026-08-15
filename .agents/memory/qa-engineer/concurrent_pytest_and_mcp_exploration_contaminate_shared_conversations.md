---
name: Concurrent pytest and MCP exploration contaminate shared conversations
description: Running a live pytest re-run while a manual Playwright-MCP session is also open on localhost risks one polluting the other's conversation
type: feedback
---

## What happened (ELITEA-2171/2172 analysis, chat-remaining-w10, 2026-08-15)

While re-confirming the merged `test_team_users_mention_and_remove_participants.py`
(ELITEA-2168) live via `HEADLESS=true pytest` in the background, a separate manual
Playwright-MCP browser session was also open against the SAME `localhost:5173` dev
server, on a different, shared, pre-existing conversation (`/chat/420`, used by
ELITEA-2091's test artifacts). Both pytest attempts failed at their own Setup stage
(once on the already-tracked #1082 stale-conversation flake, once on an "Add users"
search timeout) — and immediately after, `/chat/420`'s badge jumped from 1 to 3,
gaining exactly ELITEA-2168's own SETUP users (Daniyar Chambylov, Ihar Bylitski) as
participants, without my MCP session having added them.

## Root cause (not fully isolated)

pytest's own browser context is separate from the MCP session's — this is NOT a
shared-browser-tab collision. Most likely: server/backend-side "most recently
active conversation" contention — pytest's own `_open_blank_conversation()`
retry-guard (the #1082 mechanism) can land on whatever conversation the backend
considers "most recent" rather than a genuinely fresh one, and my MCP session's
recent navigation to `/chat/420` may have made it that conversation.

## Practical lesson

**Don't run a pytest suite against localhost while a manual MCP exploration
session is also active on the same dev server.** Either serialize them (finish
the MCP exploration, close/pause it, then run pytest — or vice versa), or budget
for extra cleanup on whichever conversation the manual session was using
afterward. If a pytest re-run is genuinely needed to reconfirm a merged test's
current behavior during analysis, prefer doing it BEFORE starting manual MCP
exploration, or on a dedicated, disposable conversation you don't mind pytest
touching.

## What we did instead

Abandoned the flaky pytest re-run path (2 attempts, both failed at Setup, never
reaching the step under test) and did a direct, clean manual repro of the exact
case steps via Playwright MCP instead — cheaper and more conclusive than fighting
test-data contention with an unrelated background process.
