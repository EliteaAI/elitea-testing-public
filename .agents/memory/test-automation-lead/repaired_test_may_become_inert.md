---
name: A drifted test's reported red is rarely its only broken assertion
description: When a product change makes a UI signal non-discriminating, sibling assertions go inert silently — repair the axis, not the red line
type: feedback
aliases: [inert assertion, test drift repair, adjust-automated-test scope, repaired test verifies nothing]
tags: [area/test-repair, type/gate]
created: 2026-08-26
updated: 2026-08-26
---

## The failure mode

A `[Investigate]` card hands you ONE red assertion. The temptation is to repair that
line and gate. But a product change that alters *what a signal means* usually
invalidates every assertion reading that signal — and the others fail **silently**,
by becoming unable to fail at all.

Worked case (ELITEA-2008, issue #1802, 2026-08-26). EL-6128 changed a pipeline's
restricted trigger options from **hidden** to **greyed out in place**:

```diff
-  if (hasInteractiveElements) return TRIGGER_OPTIONS.filter(o => o.value === chat_message);
-  return TRIGGER_OPTIONS;
+  if (!restrictedToChatMessage) return TRIGGER_OPTIONS;
+  return TRIGGER_OPTIONS.map(o => o.value === chat_message ? o : {...o, disabled: true});
```

Only the *restricted* step went red (`== ["Chat Message"]` got all 3 names). But the
option NAME list is now identical in both states — so the three steps asserting
`== ["Chat Message","Schedule","Webhook"]` for the **unrestricted** side had become
assertions that *cannot fail*. Repairing just the red one would have merged a green
test that verified nothing, and no gate would have objected: green ×3, reviewer
triangulation passes, TMS back-write claims coverage.

## The rule

When triaging a drifted test, ask: **did the product change make the asserted signal
non-discriminating?** If yes, the repair scope is the whole axis:

1. Find every assertion reading that signal — including the ones that still PASS.
2. For each, ask "under the new behaviour, what input makes this fail?" No answer ⇒
   it is inert ⇒ it is in scope.
3. Move the assertion to the discriminator the product now uses (here: the
   enabled/disabled split), on **both** sides of the contract.

Put this in the analyst dispatch explicitly — the analyst is the one re-executing
live and is best placed to spot it, but only if asked. Name the suspect steps.

## Cheap guards that paid off here

- Name forbidden handles **in the implementer dispatch**, not at review: two testids
  existed only on `automation/testids`, and using either would have gone green
  locally and red on DEV — the exact failure being repaired.
- Ask the implementer for a **pristine-base control run** before accepting any
  "pre-existing failure" claim about a sibling spec.

Related: [[../qa-engineer/repaired_test_may_become_inert_not_wrong]]
