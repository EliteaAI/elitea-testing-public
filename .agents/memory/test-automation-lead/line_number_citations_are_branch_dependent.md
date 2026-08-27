---
name: Line-number citations are branch-dependent — cite the symbol
description: A reviewer and an implementer can both be right about a file:line and disagree, because they read different refs; symbol-based citations are correct on every ref
type: feedback
aliases: [file:line citation, line number drift, cite the symbol, reviewer line number wrong]
tags: [area/review, type/convention]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

On PR #1878 I passed a reviewer nit down as a literal instruction: *"the citation says
`convertChatConversationMessages.js:25`, the declaration is at line 26 — fix it."*

The implementer verified before complying and found:

```
origin/main               -> convertTime declared at line 26
origin/automation/testids -> line 25
```

The branches differ by an unrelated import above it. The reviewer read `main`; the
implementer had read `automation/testids` — **the branch the dev server actually serves**.
Making the "fix" would have made the doc wrong on the branch under test.

Resolution: cite the **symbol** (`convertChatConversationMessages.js`'s `convertTime()`),
which is correct on both refs and survives future edits above it.

## The rules

- **Line numbers are only meaningful with a ref.** `file:line` in a durable artifact — a
  docstring, an AFS, a surface doc — is a citation with a hidden, unstated dependency.
  In a *review comment* it is fine (both parties are looking at one diff); in a **committed
  artifact** prefer `file`'s `symbol()`.
- **This repo has at least three live refs of the UI** (`main`, `automation/testids`, and
  whatever a case branch carries), so the hazard is structural here, not hypothetical.
- **An IC that refuses an instruction with evidence is doing the job.** I passed a nit
  down as settled; the implementer checked the premise and it was false. Prefer handing an
  IC the *requirement* over the *patch* — the reviewer's suggested code for the same PR
  (`created_at.rstrip("Z")`) would also have reintroduced the very bug they were blocking on.

Related: [[a_product_change_is_not_a_product_bug]]
