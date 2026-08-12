---
name: Large dependency-set promotability trace technique
description: How to derive and resolve a 30+ testid promotability table efficiently when a test uses several page objects — walk each instance's actual method calls, not the AFS table, then batch-resolve origin commits with git log -S per distinct testid/template
type: feedback
---

## What happened (#257, ELITEA-1866, PR #670)

A 39-step case instantiated 5 page objects (`ToolkitsListPage`,
`ToolkitCreationPage`, `ToolkitDetailPage`, `ToolkitTestSettingsPage`,
`ArtifactsPage`) and ended up with **37 distinct testid dependencies** in
its promotability set — by far the largest traced this cycle. Doing this
by re-reading the AFS table (per `promotability_afs_handles_table_can_both_omit_and_overinclude.md`
and the `sixth variant` recurrence in `promotability_must_cover_every_dependency_not_just_this_prs.md`)
would have been both slow and risky at this scale.

## The technique that scaled

1. **Find every instance the test creates**: `grep -n "^from pages\|Page(page)"`
   on the test file — gives the exact set of page objects in play (5 here).
2. **For each instance variable, enumerate every attribute/method the test
   actually calls**: `grep -oE "${var}\.[a-zA-Z_]+" test_file.py | sort -u`.
   This is the REAL call chain — cheaper and more reliable than reading the
   whole page-object file and guessing which methods matter.
3. **For each called method/field, open the page object and trace it to its
   `LocatorDescriptor(testid=...)` or `UPPER_CASE = '[data-testid="..."]'`
   template** — a method that doesn't touch a locator (e.g. a pure Python
   helper) contributes nothing; skip it.
4. **Batch the fresh `git grep` promotability check** — write all resolved
   testids (using a representative concrete value for templated ones, e.g.
   `toolkit-type-card-artifact` for `toolkit-type-card-{}`) to a single file,
   loop `git grep -q -- "$t" origin/main -- src/` / `origin/automation/testids`
   over it in one shell block. Bare-substring, never the literal-quoted
   `data-testid="..."` form (template literals/prop-drilling false-negative
   on that, per `promotability_grep_false_negative.md` and the 5th
   recurrence in the "must cover every dependency" memory).
5. **For every "no/no" hit, don't conclude "missing"** — re-check with the
   testid's PREFIX stripped of its dynamic segment (e.g. `toolkit-field-`
   instead of `toolkit-field-bucket-input`) to catch the template-literal
   shape. Genuinely new/absent testids are the ones where even the stripped
   prefix search comes up empty on both refs.
6. **Batch-resolve origin commits** — one `git log --oneline origin/main..origin/automation/testids -S"<pattern>" -- src/`
   per distinct testid or template family (not per page object), `tail -3`
   to see the earliest hit. Several unrelated testids often trace to the
   SAME commit (a prior case added many at once) — dedupe before citing so
   the closure record's "Unblocks when" line names N *distinct* commits,
   not 37 rows' worth of repeats.
7. **Verify the citations rendered, don't just trust the markdown** — fetch
   `body_html` (`gh api .../comments/<id> -H "Accept: application/vnd.github.full+json"
   --jq '.body_html'`) and grep for `class="commit-link"` anchor count — a
   plain `EliteaUI@[0-9a-f]{7,}` string grep on body_html gives a FALSE
   negative because GitHub wraps the hash in a `<tt>` tag inside the anchor
   text (`EliteaAI/EliteaUI@<tt>2fa2d8...`), splitting the literal
   substring. Count `class="commit-link"` occurrences instead, or grep for
   `commit/[0-9a-f]{7,}"` (the href form).
   **Also note the default `gh api` response has NO `body_html` field at
   all** — the `Accept: application/vnd.github.full+json` header is
   required, or the jq extraction silently returns null/empty and every
   downstream check reports zero matches even when the record is correct.

## Why this matters

At 5-10 dependencies, reading the AFS table and eyeballing it is fine. At
30+, that same eyeballing either takes too long or silently drops rows
(exactly the "sixth variant" failure this repo's memory already
documents). The call-chain-first, batch-grep, batch-resolve approach scales
linearly with actual effort (one grep per distinct testid/commit, not one
per row) instead of getting slower/riskier as the dependency count grows.
