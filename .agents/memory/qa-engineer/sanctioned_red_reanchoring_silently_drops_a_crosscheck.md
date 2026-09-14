---
name: Sanctioned-RED re-anchoring silently drops a cross-check
description: When a defect makes a reference value unreadable, re-pointing downstream asserts at a substitute anchor loses the original link — permanently, not just during the defect window
type: feedback
---

## The trap

A sanctioned-RED repair has a recognisable shape: the observable a defect broke is
demoted to a soft assert, and a **transit** step (reload / re-fetch) produces a
substitute reference value so the later hard assertions can still run. The later
assertions are then **re-anchored** onto that substitute.

The demotion is the loudly-declared part, and every gate looks at it. The
**re-anchoring is the silent part**, and it is where coverage leaks: any chain that
ran *through* the broken value stops being verified — and it stays unverified after
the product is fixed, because the transit step usually survives the fix.

## Worked instance — ELITEA-1899 / #2055 (2026-09-09)

`#2055`: the agent header `<img>` is absent from the DOM until a reload, so
`get_header_icon_src()` returns `""` right after an icon selection.

- Pre-repair, hard: `card_src == new_src`, where `new_src` was the **immediately
  rendered header** src. That single line proved *the icon the header shows at once
  is the icon that ends up on the dashboard card.*
- Post-repair: Step 4's immediate read became a soft `non-empty and != previous`,
  a transit `page.reload()` produced `persisted_src`, and Step 7 became
  `card_src == persisted_src`.
- Every individual assertion still looked strong, exact-equality included. But once
  `#2055` is fixed, a header that renders the **wrong** icon immediately while the
  right one persists passes every assertion in the file. The pre-repair spec caught
  exactly that.

The AFS and the module docstring both stated "nothing is deleted, weakened, or made
conditional." Both were sincere and both were wrong — because nobody had listed the
pre-repair hard assertions and ticked them off one by one.

## The review move

On any sanctioned-RED / adjust-automated-test diff, **enumerate the pre-repair hard
assertions from `git show <base>:<path>` and tick each against the new file.** Score
each as `kept` / `sanctioned-demotion` / `re-anchored`. Then, for every `re-anchored`
one, ask the only question that matters:

> what did the OLD anchor prove that the NEW anchor does not — after the defect is fixed?

If the answer is non-empty, that is a blocker with a cheap fix: restore the dropped
link as an assertion **guarded on the broken value being readable**
(`if immediate_src: assert immediate_src == persisted_src`). Guarded that way it
never fires during the defect window — so it cannot pollute the single-cause
signature the merge gate needs — and it comes back automatically on the fix.

Do not accept "Expected-result changes: None" from an AFS or a docstring as evidence.
It is a claim about a diff, and claims about diffs are checked against the diff.
