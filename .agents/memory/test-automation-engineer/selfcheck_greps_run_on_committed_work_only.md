---
name: The mandatory self-check greps see COMMITTED work only — commit before you grep
description: git diff <base>...HEAD -- automation/ excludes the working tree, so running the locator/provenance self-checks before committing prints a false "0 hits" on a diff that genuinely has hits.
type: feedback
aliases: [self-check grep, mechanical grep, 0 hits, locator grep, provenance grep, empty diff]
tags: [area/handoff, type/trap]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

The handoff owes two mechanical greps, both in the three-dot form:

```bash
git diff automation/base...HEAD -- automation/ | grep -nE '^[+].*(get_by_role|...|\.locator\()'
git diff automation/base...HEAD -- automation/ | grep -nE '^[+].*(\.mock_|page\.route\(|...)'
```

`<base>...HEAD` compares two **commits**. Uncommitted edits are invisible to it.
So running the greps while your work is still in the working tree prints
`0 hits` — and `0 hits` is exactly the evidence the Run Report is supposed to
paste. The check silently degrades into a no-op that *looks* like a pass.

Hit live on ELITEA-2367 / card #2079 (2026-09-09): both greps printed nothing.
The real diff, once committed, had **2** locator hits (both compliant one-hop
`[data-testid=` class constants — but that is a judgement the reviewer is
entitled to see me make, not one to skip by accident).

## The fix

**Commit first, grep second.** Order the handoff: run green → commit on the case
branch → run both greps against `<base>...HEAD` → paste command + output.

Sanity guard that costs nothing: print `git diff <base>...HEAD --stat` in the
same call. If the stat block does not list the files you just edited, the greps
below it are meaningless.

## Why the empty result is so convincing

Every incentive points the wrong way: an empty result is the *desired* outcome,
it arrives instantly, and there is no error. Nothing distinguishes "clean diff"
from "no diff". The `--stat` line is the only cheap discriminator.

Related: [[additive_only_grep_scope_your_own_unmerged_commits]] — the complement.
That entry says scope the additive-only check to the trunk (`...HEAD`) rather
than the working tree; this one says the same scoping makes the check blind
until you commit.
