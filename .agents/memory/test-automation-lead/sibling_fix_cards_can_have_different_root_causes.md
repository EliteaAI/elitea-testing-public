---
name: Sibling fix cards can have different root causes
description: A [Fix] card asserting "same issue as #N" is a hypothesis; the sibling's own closure record is often the disproof
type: feedback
aliases: [same issue as, sibling failure, shared root cause, batch of red tests, fix card triage]
tags: [area/triage, type/lesson]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`[Fix]` cards are generated from a CI run, and the generator groups by surface —
so several cards land saying *"same X issue as #N"*. That line is an **untested
hypothesis written by a log parser**, not a finding. Acting on it means
inheriting a diagnosis nobody checked against this failure.

Worked case, 2026-08-28: #1891 (ELITEA-2037) said *"Same MCP popper issue as
#1890."* Same file, same button, same `assert 0 > 0`, same GHA run. It was a
different bug — and **#1890's own closure record contained the disproof**: that
repair had established `toolkit-search-input` renders from the popper's first
frame, *which is why that assertion never flaked*. So a load race could not
explain a search-input failure. Ten minutes of reading beat a wrong dispatch.

## The move

1. **Read the sibling's closure record before dispatching**, specifically for
   what it *ruled out* — a good repair states why the assertions that stayed
   green stayed green, and that is exactly what discriminates the siblings.
2. **Compare which assertion failed, not which file.** One line apart is one
   bug apart. #1890 failed on `toolkit-menu-item`; #1891 on `toolkit-search-input`,
   one assertion earlier.
3. **Harvest the allure artifacts first** (§ related entry) — a screenshot
   settles it before any subagent burns context.
4. When the shared cause IS real, expect the shared fix to repair other cards'
   specs. That is fine; say so on those cards rather than staying quiet — but
   never let it silently substitute for their own gates.

## The inverse also bit

The same session found the reverse: #1892 had **both** bugs. Fixing one left it
red, which reads as "the fix failed" unless you predicted it. Say in the PR and
on the sibling card which half you fixed and which half remains.

Related: [[a_product_change_is_not_a_product_bug]] · [[harvest_gha_allure_artifacts_before_dispatching]]
