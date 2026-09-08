---
name: An empty string on BOTH sides of a failed assert means absence, not equality
description: assert '' != '' is a missing/invisible element reported as a value comparison — check the page object's except-to-default branch before chasing the values
type: feedback
aliases: [assert '' != '', empty string assertion, both sides empty, get_header_icon_src returned empty, swallow and return default, absence not equality]
tags: [area/triage, type/trap]
created: 2026-09-09
updated: 2026-09-09
---

## The tell

A `[FIX]` card whose failure reads `AssertionError: assert '' != ''` (or
`'' == ''`, or two empty lists) is **not** telling you two values coincided.
It is telling you the reader returned its *default* twice — i.e. the element
was never there, or never visible.

Worked case 2026-09-09, ELITEA-1899 / #2051. The card's own generated summary
called it "a definitive feature regression in icon management" and the
assertion message said *"Selecting a different icon option should change the
header icon src"* — both of which point you at the icon-change logic. The real
statement was: `agent-form-icon-img` was absent from the DOM entirely, before
**and** after the click.

## Why the shape hides

Page objects legitimately swallow-and-default so a probe does not time out:

```python
try:
    self.agent_icon_img.wait_for(state="visible", timeout=timeout)
except Exception:
    return ""            # documented: fresh entity renders an inline SVG, no <img>
```

That is good design — but it converts *absence* into a **value**, and the
assertion downstream then compares two values and reports a value mismatch.
The failure text is honest about what it compared and silent about what it
could not find.

## The move

When both sides of a failed comparison are the reader's default:

1. **Read the reader first**, not the subject. Find the `except → default` /
   `if not found: return ...` branch and note what it swallows.
2. **Re-state the failure as absence** before forming any hypothesis:
   "the element was never visible", not "the value did not change".
3. **Distinguish absent from invisible** — they have different causes and
   different fixes. Dump `outerHTML` of the container rather than trusting a
   locator's visibility state: a `display:none` node and a node that was never
   rendered look identical to `wait_for(state="visible")`. This is exactly
   what refuted my own hover/`display:none` hypothesis on ELITEA-1899 in one
   step (`hasImg: false` ⇒ never rendered ⇒ the upstream value was never set).
4. Only then ask *why* the producer never produced it.

## Generalisation

Any default-returning reader has this property: `""`, `0`, `[]`, `None`,
`False`. A failed assert where **both** operands are the default is an
absence report wearing a comparison's clothes. Treat the symmetry as the
signal.

Related: [[deployed_only_failure_claims_are_hypotheses]] · [[fix_card_body_can_carry_a_policy_violating_instruction]]
