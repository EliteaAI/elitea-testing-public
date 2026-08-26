---
name: A repaired test can go inert instead of wrong — check the old assertion can still FAIL
description: When product drift changes HOW a state is expressed, the old assertion may still pass everywhere; repairing only the red step ships a green test that verifies nothing.
type: feedback
aliases: [inert assertion, repair drift review, disabled in place, hidden to greyed out, discriminating assertion]
tags: [area/review, type/triangulation-trap]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

A merged test goes red after a product change. The obvious repair is "fix the step
that failed". That is not sufficient when the change moved a state from
*presence* to *attribute*.

Worked case: ELITEA-2008 (PR #1809). EliteaAI/EliteaUI@cb70a64e (EL-6128) changed the
pipeline trigger restriction from **hiding** Schedule/Webhook to **greying them out
in place** (`TRIGGER_OPTIONS.filter(...)` → `{...opt, disabled: true}`). Only ONE step
(the post-Save "only Chat Message" check) went red. But the *other* checkpoints —
`assert options == ["Chat Message","Schedule","Webhook"]` at baseline, pre-Save and
post-cleanup — became **inert**: post-EL-6128 that list is identical whether the
pipeline is restricted or not, so those assertions can no longer fail in either
direction. Relaxing only the red step would have shipped a green suite proving nothing.

## The reviewer's question

For every assertion in a repair diff, ask **"what change in the product would make
this line fail now?"** If the answer is "none" or "only a change the other steps
already catch", it is decoration, not coverage. Applies especially to:

- presence/absence assertions after a hide → disable (or disable → hide) change
- name/label list assertions after an ordering or rendering change
- any step whose expectation is now identical in both branches of the behaviour

## Also worth knowing

MUI emits option state as `aria-disabled="true"`; an **enabled** MenuItem carries
**no** `aria-disabled` attribute at all (absent, never `"false"`), so the enabled
filter must be `:not([aria-disabled="true"])` —
`to_have_attribute("aria-disabled", "false")` never matches.

Related: [[../test-automation-engineer/aria_disabled_is_absent_not_false_when_enabled]]
