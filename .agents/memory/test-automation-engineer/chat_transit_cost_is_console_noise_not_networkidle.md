---
name: /chat as a transit page — the real cost is ELITEA-2234 console noise, not networkidle
description: networkidle DOES resolve on /chat locally (measured 4.7s); avoid /chat as transit for its restore-path 4xx console noise instead.
type: reference
aliases: [chat transit page, transit target choice, networkidle on chat, sidebar control transit, lightest read-only page]
tags: [area/waits, area/flakiness]
created: 2026-09-30
updated: 2026-09-30
---

## Measured, and it corrects a comment in our own code

`base_page.py`'s `navigate()` comment says *"Pages with persistent WebSocket
connections (e.g. Skills, Chat) never reach networkidle."* On **localhost that is
not true for /chat** — measured 2026-09-30 against `localhost:5173`:

| Path | requests | networkidle |
|---|---|---|
| `/chat` | 2521 | resolves, 4.69s |
| `/agents/all` | 2153 | resolves, 3.29s |
| `/pipelines/all` | — | resolves, 3.16s |
| `/skills/all` | — | resolves, 3.32s |

So the 30s `try/except` ceiling is not what /chat costs you. (Consistent with
`.agents/testing.md` ELITEA-2354/#2166: socket.io's localhost topology is
cross-origin to `dev.elitea.ai`, so it does not hold the page's network idle.)

## The real reason to avoid /chat as transit

It **restores the shared test user's most recent conversation**, and that restore
path is the documented origin of unrelated background 4xx console errors
(`.agents/testing.md` ELITEA-2234). Any spec with a console-error axis is opting
into a known, non-reproducing flake class for no coverage benefit.

Do NOT justify avoiding it with `#1082` — that is about *mutating* shared
conversations, which a read-only `navigate()` never does. (Reviewer correction,
ELITEA-2219.)

## Picking a transit target for an app-shell control

Sidebar controls are **route-independent**: `SidebarBody` mounts them inside the
app-shell `Drawer`, gated only on `!sideBarCollapsed` (expanded is the default
and does not persist). So any authenticated route serves — pick the lightest
read-only one and verify live rather than assuming.

`/skills/all` is excluded by the WebSocket criterion per that same `base_page.py`
comment; `/agents/all` and `/pipelines/all` measured equivalent.

Measured effect on ELITEA-2219 (matched control, same machine, minutes apart):
`/chat` 15.44s / 16.00s → `/agents/all` 11.62s / 11.59s.
