---
name: FIX-card refiling loop — the mechanical root cause
description: The intake's dedup lookup is unpaginated and its [FIX] term is tokenized, so old cards are invisible and every CI run refiles
type: project
---

**Why one failing spec produces an unbounded stream of [FIX] cards.** Measured
2026-09-10 on ELITEA-1899 (6 cards in 3 days: #2043 → #2051 → #2081 → #2113 →
#2146 → #2164). The routine is readable in-repo:
`automation/routines/test_failure_intake.yml`.

The dedup **exists and is correct**. `ClassifyTests` extracts `\[ELITEA-(\d+)\]`
from titles and marks a match `already_in_progress`. It never fires because its
input step is blind:

```yaml
- id: SearchExistingIssues
  tool: search_issues
  search_query: "is:issue is:open [FIX]"   # no repo:, no per_page, no pagination
```

Three compounding defects:
1. **`[FIX]` is tokenized** — GitHub search drops the brackets and matches "FIX"
   in bodies too. Measured: `total_count` 342 vs only 70 real `[FIX]`-titled
   open issues. ~80% of the window is wasted.
2. **Unpaginated** — one page. Of the first 100 results only 67 are `[FIX]`-titled.
3. **Consequence:** at the API default `per_page=30`, **0 of 6** ELITEA-1899
   cards were visible; all 6 appear only at `per_page=100`.

So any case whose cards have aged past the first page refiles **every run,
deterministically**.

**Latent inverse bug in the same step** — suppression is gated on:
```python
if 'ready' not in [l.lower() for l in label_names]:
```
That reads a **label** named `ready`. This factory never applies one — `Ready`
is a board **Status** (Projects v2 single-select), and `search_issues` does not
return project fields. Dead code today. ⚠️ "Fixing" it by adding a literal
`ready` label flips it into **over**-suppression: a genuine new regression of a
delivered case would be silently swallowed.

Note `profile.md` § Issue tracker already bans the search index for dedup
("the index lags minutes… #17/#18"); the routine uses it anyway.

Tracked on **#2157** (root cause posted), **#2135** (same step), **#2064**
(no sanctioned-RED awareness — the second, independent cause). A sanctioned-RED
spec stays red by design, so even perfect dedup would still refile once.
