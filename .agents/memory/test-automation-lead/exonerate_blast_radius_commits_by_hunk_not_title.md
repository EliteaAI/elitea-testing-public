---
name: Exonerate a blast-radius commit by reading its hunks, never by its title
description: A commit whose title names your broken feature can be entirely unrelated to it — read the diff; and post the exoneration so nobody re-chases it
type: feedback
aliases: [blast radius, culprit commit, suspect commit, commit title is not evidence, regression bisect by inspection]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Triaging a regression, you list commits touching the feature's files since it
last worked and get a shortlist. Those titles are written to describe the
author's *intent for their own ticket*, not the surface area they touched.

Worked case 2026-09-09 (ELITEA-1899 / #2055, agent header icon stops updating
in place):

| Commit | Title | Reality |
|---|---|---|
| EliteaAI/EliteaUI@94a61b81 | "Lazy-load optional data … Defer API requests for Toolkits, MCPs, Agents, Pipelines, **Icons**, and Tags" | touched `SelectIconDialog.jsx`, `ApplicationEditForm.jsx`, `CreateAgentForm.jsx` — and every hunk in the two form files is **Tags-only** (`useTagListQuery` deferral + a wrapping `<Box onFocus>`). The dialog hunk only adds `\|\| !open` skip conditions to icon-LIST queries, which demonstrably still populate. |
| EliteaAI/EliteaUI@cf648e9a | "Enhancement of version select" — touched the very file holding the broken optimistic patch | **+21/-0**, purely additive: a *new* `updateQueryData` patch for a different flow. Does not modify the icon patch or its cache key. |

The first looked damning (its title literally lists "Icons") and was innocent.
Four commands settled both.

## The move

```bash
git show <sha> --stat                 # which files, how big
git show <sha> -- <file> | grep -nE '^[-+]' | grep -viE '^\+\+\+|^---'
```

Read the actual `+`/`-` lines against **the specific mechanism** you believe is
broken. `+21/-0` on the right file is an *addition*, not a modification —
it cannot break an existing path unless it shares a cache key or a name.

## The half people skip

**Post the exoneration** on the defect issue, with the evidence. A shortlist of
"suspects" left in a bug report gets re-chased by the next person — and by the
product team, who will spend their time re-reading commits you already cleared.
Naming what is ruled OUT is as valuable as naming a cause, especially when you
end with **no** identified culprit: that itself is a finding, and it redirects
the search (backend response shape? a latent defect that never worked?) instead
of leaving a false trail.

Related: [[an_empty_string_on_both_sides_of_an_assert_means_absence]] · [[ci_red_check_base_for_an_existing_fix_first]]
