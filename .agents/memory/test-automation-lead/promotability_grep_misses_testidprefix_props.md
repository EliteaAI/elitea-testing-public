---
name: The closure-record promotability grep misses <part>TestIdPrefix="x" — a false "not on main"
description: Stage-2 filter needs TestId followed by [:=]; an interposed word (Prefix) drops the line and writes a false not-promotable row
type: feedback
aliases: [promotability false negative, chipTestIdPrefix, closure record grep, testid not on main]
tags: [area/branching, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

`.agents/workflow.md` § Closure record's stage-2 filter is
`(data-testid|testid[[:space:]]*[:=])` with `-i`. It handles `buttonTestId="x"`
(needs `-i`) and `testId: 'x'` (needs `[:=]`), both fixed 2026-08-10.

It does **not** handle an interposed word between `TestId` and the `=`:

```
chipTestIdPrefix="catalog-agent-category-filter-chip"     # AgentsTab.jsx:246
```

`TestId` is followed by `Prefix=`, not by `[[:space:]]*[:=]`, so stage 2 drops a
line stage 1 correctly found — and the row reads `main:no testids:no` for a testid
that is on **both** refs.

**Why this one is worse than #1791's false positive:** it writes *"NOT yet on main
→ not promotable"* into a closure record and parks a case that was promotable all
along. That is the #19 false-0-of-12 class, which the mandatory `git fetch` was
added to prevent — the fetch is only half the fix; the filter is the other half.

**The catch that actually worked, and it was not the recipe:** the spec was passing
3/3 against DEV, so a testid it demonstrably uses could not really be absent. When a
row reads `no`/`no` for a testid a *passing* test exercises, stop counting and read
the hits:

```bash
git grep -- "$t" origin/main -- src/ | head
```

Filed as `question` #2208 (sibling of #1791, opposite direction) proposing
`(data-testid|testid[a-z]*[[:space:]]*[:=])` — not applied unilaterally, because a
looser filter recovers more prose/comment false positives, which is what stage 2
exists to reject.
