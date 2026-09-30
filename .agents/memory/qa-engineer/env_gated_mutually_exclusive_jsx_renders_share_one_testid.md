---
name: Env-gated mutually exclusive JSX renders share one testid
description: When one logical control renders through two exclusive JSX branches chosen by a BUILD-time flag, canon #277's shapes do not apply — same testid value on every branch is the spirit-compliant answer.
type: feedback
aliases: [ResourcesButton two returns, VITE_ELITEA_ASSISTANT, build-time branch testid, mutually exclusive renders]
tags: [area/testids, type/canon-gap]
created: 2026-09-30
updated: 2026-09-30
---

## The shape

ELITEA-2219 (2026-09-30). `ResourcesButton.jsx` (the sidebar Help Center control) has
**two `return` statements**. `SidebarBody.jsx` picks between them with a ternary on
`onToggleAssistant`, which is `undefined` unless the **build-time** env var
`VITE_ELITEA_ASSISTANT` is truthy:

- assistant **ON** → icon-only control, rendered next to `sidebar-support-assistant-button`
- assistant **OFF** → `fullWidth` control with a visible "Help Center" label, no Support Bot

Both click through to `/help-center`. Which one exists is a property of the **build**, so
it can differ between localhost and CI-on-DEV.

## Why the existing canon does not decide it

Canon ruling #277 covers `data-testid={cond ? A : B}` on a **single JSX node** with a
**per-mount data prop**, allowing (a) only the used branch named, or (b) both named and
both referenced, the untested one via an absence assertion. Neither maps:

- Two separate JSX nodes in two separate `return`s — not a ternary on one node.
- Shape (a) needs "which branch is used" to be knowable when writing the testid. It is
  not: pick one and the spec passes in one deployment config and fails in the other, for
  a reason unrelated to the behaviour under test.
- Shape (b)'s absence assertion is **structurally vacuous** — the branches can never
  coexist, so `to_have_count(0)` on the unrendered one is trivially satisfied every run.

## The answer used, and the argument

**Same testid value on every branch.**

- Collision-impossible by construction, not convention: one component, exclusive `return`
  paths on the same prop. Live-verified count == 1 in both configurations.
- #511 holds — in whatever environment runs, the element bearing the testid is the one the
  test clicks, so the value is referenced on the executed path.
- The presence-based coverage metric counts the *value*, and exactly one element ever
  bears it. Both nodes are the same logical control, so no untested UI lights up.
- **Not** the PR #581 anti-pattern: that is a testid whose value *flips on the same live
  element* as state changes. Here the value is constant; only which node mounts varies,
  and it varies per build, not per interaction.

Declared in the AFS per § declared-improvisation protocol and raised to the lead as a
proposed canon addition — a declaration makes a deviation visible, not permitted, so it
owed a `question` card before batch close.

## Generalise

Before reaching for #277, ask **what selects the branch**: a per-mount data prop (→ #277
applies) or a build/deployment flag (→ this entry). Also check whether the "untested"
branch can ever coexist with the tested one — if not, an absence assertion on it is
vacuous and must not be used to satisfy shape (b).
