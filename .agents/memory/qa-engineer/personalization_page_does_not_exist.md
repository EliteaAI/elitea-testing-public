---
name: There is no Personalization settings page in Elitea
description: A whole TMS case family targets /settings/personalization, which 404s — its sections live on preferences/memory/profile/ai-personality
type: project
aliases: [personalization 404, settings personalization, long-term memory coming soon, default personality QA]
tags: [area/settings, type/case-text-drift]
created: 2026-08-28
updated: 2026-08-28
---

## Fact

`GET /settings/personalization` renders the app's global "Page not found" view. The
Settings drawer PERSONAL group is: Profile, Preferences, AI Personality, Memory, Personal
Tokens, Notifications. Verified live 2026-08-28.

| Case's "Personalization" element | Real route |
|---|---|
| profile area (avatar/name/email) | `/settings/profile` |
| GENERAL, VOICE PERSONALIZATION, SOUND NOTIFICATIONS | `/settings/preferences` |
| DEFAULT CONTEXT MANAGEMENT (+ DEFAULT SUMMARIZATION) | `/settings/memory` (`CONTEXT MANAGEMENT` / `Automatic Summarization`) |
| "Default Personality" | `/settings/ai-personality` (`Default persona` select) |
| LONG-TERM MEMORY | **nowhere** — `MemoryLongTermMemory.jsx` is dead code, its only import is commented out at `MemoryContextManagement.jsx:13` |

Clarifications: #1238 (ELITEA-2374), #1772 (drawer inventory), **#1960** (this family —
ELITEA-2371/2372/2373/2380/2387).

## How I dispositioned it (reusable rule of thumb)

- The case's **subject exists under a different name/route** ⇒ `ready-for-automation`,
  assert the live contract (2372, 2373, 2387).
- The case's **subject does not exist at all** ⇒ `blocked`, route to a human. Rewriting it
  into a different case would change *what* is verified, which is above the
  declared-improvisation ceiling (2371: the consolidated page; 2380: the dead section).

Related: [[mui_accordion_collapse_hides_not_unmounts]]
