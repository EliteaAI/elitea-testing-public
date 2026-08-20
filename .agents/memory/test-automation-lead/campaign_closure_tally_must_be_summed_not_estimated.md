---
name: Campaign closure tally must be summed, not estimated
description: When posting a final multi-wave campaign tally, sum the actual per-wave numbers from the campaign doc before posting — don't eyeball it, and correct immediately if an early approximate number was wrong
type: feedback
---

## What happened (2026-08-20, chat-remaining campaign #1393 close, 16/16 waves)

Posted the wave-16/final closure comment with a rough tally ("~119/127
automated, ~4 already-covered, ~4 blocked") eyeballed from memory of how the
campaign felt, without actually summing the campaign doc's own per-wave
table. On a second pass, summed every wave's own landed row precisely:

```
automated = [3,6,9,7,6,7,11,7,4,5,2,8,6,7,4,7]   -> 99
covered   = [0,0,0,1,0,4,0,0,4,2,2,0,0,0,3,2]     -> 18
blocked   = [2,0,0,0,0,0,1,0,0,0,3,3,0,0,1,0]     -> 10
sum = 127  (matches the campaign's own known total exactly)
```

The real numbers (99/18/10) were meaningfully different from the eyeballed
ones — the rough estimate had conflated "automated" with "automated +
already-covered" and undercounted blocked cases by more than half. Posted a
follow-up correction comment with the verified numbers rather than letting
the approximate one stand as the record.

## Rule going forward

**Never post a final/summary tally for a multi-wave campaign from memory or
impression.** Before writing the number: `grep`/read every wave's own
"LANDED" row in the campaign doc, extract its automated/covered/blocked
counts, sum them in a real calculation (a one-line Python `sum()` is
sufficient), and verify the total matches the campaign's known case count.
Only then post it as the official closure record. If an approximate number
was already posted, don't leave it standing — post a correction immediately,
labeled as the corrected/verified number, so the closure record's final
state is accurate rather than whichever comment happened to land last.
