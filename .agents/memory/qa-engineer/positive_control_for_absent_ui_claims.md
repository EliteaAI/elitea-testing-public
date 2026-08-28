---
name: Positive control for absent-UI claims
description: When a case claims a panel that isn't there, run the same probe where it DOES live — turns a negative into disproof
type: feedback
aliases: [positive control, panel not found, absent observable, disproof, case-text drift proof]
tags: [area/analysis, type/technique]
created: 2026-08-28
updated: 2026-08-28
---

## The problem

Reporting "0 matches for every label the case names" is a *negative observation*. A human reading it
cannot distinguish "the panel isn't there" from "your probe was broken / you looked in the wrong
place / you used the wrong bucket". ELITEA-1865 was returned `blocked` on exactly that evidence in
2026-08-23, and the human bounced it back five days later with "Panel is expected to be in place.
Double check UI." — one full re-analysis cycle spent because the first negative wasn't falsifiable.

## The technique

Run the **identical probe** on the surface where the thing genuinely does live, in the same browser
session, and report both results side by side.

ELITEA-1865, 2026-08-28:

- Artifacts file preview → `Context Management 0 · Max Tokens 0 · Summarization 0 · …`
- `/settings/memory`, same probe, same session → `Context Management 3 · Max Context Tokens 1 ·
  Preserve Recent Messages 1 · Summarization 2 · Target Summary Tokens 1`

Same method, one finds it, one doesn't. That is positive disproof, and it cost one extra navigation.

## The full disproof kit for "this UI element doesn't exist"

1. **Positive control** (above) — proves the probe works.
2. **Closed affordance list from source** — enumerate what the component renders
   (`PreviewHeader.jsx` renders exactly 7 things) rather than saying "I didn't see it".
3. **No-mount-path grep** — `grep -rln "<Widget>" src/ | grep -i "<the feature>"` returning nothing,
   plus a check that **no feature flag** in that feature dir could gate it.
4. **Exhaust the affordances by opening them**, not by looking: every 3-dot menu (page-level AND
   row/bucket-level), plus a wide viewport (1920×1200) for a right-hand drawer.
5. **Use the object the case names**, or prove it doesn't exist — the first pass used a fixture
   bucket and that gap alone justified the human's bounce.

Related: [[artifacts_bucket_menu_is_hover_gated]]
