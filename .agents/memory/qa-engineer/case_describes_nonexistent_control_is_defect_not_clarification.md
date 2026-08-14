---
name: A case describing a whole control that doesn't exist on this surface is defect-found, not a reverse-masking clarification
description: When a TMS case's central control (not a minor wording detail) is entirely absent from the surface, and 6/7 of its steps depend on it, classify defect-found + file a bug — don't stretch the reverse-masking guard (which is for the product correctly diverging on a DETAIL) to cover "the feature doesn't exist here at all."
type: feedback
---

## The case (ELITEA-2071, pipelines-remaining-w5)

Case: "Pipeline — Fullscreen Chat Mode" — a fullscreen/expand button in the
chat panel header that hides the left config panel, works during execution,
and restores split view on exit.

Live reality (`probe-pipeline`, id 6934, confirmed via Playwright MCP +
source read): **no such control exists anywhere on the Pipeline surface.**
The only header icon is a *collapse* toggle that does the opposite (shrinks
the chat, doesn't touch the left panel). Source read confirmed why: every
other chat-hosting surface (Agent `Applications/ConfigurationTab.jsx`, Skill
`SkillTestPanel.jsx`, Toolkit-Index `IndexChat.jsx`) wires a real
`FullScreenToggle` component via `useState`; the Pipeline
`ConfigurationTab.jsx:205` only has a **hardcoded dead literal**
`isFullScreenChat: false`, and `ChatPanel.jsx` never imports the toggle
component at all. Looks like a genuine half-finished feature-parity gap.

## The classification call

Two candidate framings, and why the first is wrong:

1. **Reverse-masking guard** (`.agents/testing.md` § reverse-masking) says:
   when the live product *correctly diverges* from stale case text, classify
   `ready-for-automation` and assert the live contract, filing a
   CLARIFICATION rather than a bug. This guard is scoped to **detail-level**
   divergence (case says ≥44px, product is 40px by design; case says "Save
   button visible", product correctly removed Save). It presumes there IS a
   real, live, testable behavior to assert — just not the one the case's
   words literally predicted.
2. **Here there is no live behavior to assert at all** for steps 2–7 — the
   control the case's every remaining step depends on simply isn't there.
   Reframing the AFS around the *actual* control (chat-panel collapse) would
   not be "asserting the live contract of the same observable" — it's
   silently substituting a DIFFERENT feature (opposite direction, doesn't
   touch the left panel) under the original case's name. That's editorializing,
   not reverse-masking.

Correct call: **`defect-found`**, file the bug
(`elitea-testing-public#1363`), Coverage Map step 1 `already-covered` (proven
elsewhere), steps 2–7 `blocked`/`known defect`. `.agents/testing.md` § Merge
gate's own text distinguishes this from the Sanctioned-RED "isolated known
defect, one tail assertion" shape (e.g. ELITEA-1965's search-clear defect,
which blocked only its own step 6 while 5/6 steps passed clean) — `defect-found`
is for when the defect "blocks further exploration," which a whole-case's
central control being absent clearly does (6 of 7 steps depend on it).

## Takeaway for the next case that "looks like the product is just different"

Ask: is this divergence at the **detail** level (same feature, different
number/wording/removed-as-designed element) or at the **existence** level
(the control/flow described isn't there in any form)? Detail → reverse-masking
clarification + `ready-for-automation`. Existence → `defect-found` (or
`un-automatable` if there's genuinely no way to even file it as a gap, which
is rare) — don't force a fresh feature into the old case's clothing.
