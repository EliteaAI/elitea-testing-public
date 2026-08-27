---
name: A repair branch cut from origin/main silently re-creates automation/base files
description: Branching a fix off origin/main (not automation/base) turns every append-style file that exists only on automation/base into an add/add conflict — memory entries lose frontmatter and prior recurrences
type: feedback
---

## The trap

`origin/main` lags `origin/automation/base` by a lot (measured 2026-08-27:
`MEMORY.md` 55 lines on main vs 147 on automation/base). A branch cut from
`origin/main` therefore does not see files that were born on `automation/base`.

When an agent then "appends a recurrence" to such a file, git records it as a
**new file containing only the fragment** — no frontmatter, no prior content.

Worked example — ELITEA-1886/#1812 repair, branch `fix/ELITEA-1886-starter-chip-send`
off `origin/main`:

- `.agents/memory/test-automation-engineer/chat_send_button_force_click_race.md`
  exists on `origin/automation/base` with `name`/`description`/`type` frontmatter
  and Recurrences 1 (ELITEA-2093) and 2. The branch created it fresh with ONLY
  "Recurrence 3" and no frontmatter → add/add conflict at merge, and a careless
  resolution destroys the two earlier recurrences.
- The spec's own code comment cited two sibling specs
  (`test_agent_hub_create_conversation_via_starter.py`,
  `test_chat_agent_starters_add_remove.py`) that exist ONLY on `automation/base` —
  the references dangle for any reader on `main`.

## Reviewer check

When a diff's stated base is `origin/main`, run before anything else:

```bash
git merge-base origin/main <branch>; git rev-parse origin/main origin/automation/base
for f in <every non-automation/ path in the diff>; do
  git cat-file -e origin/automation/base:$f 2>/dev/null && echo "ADD/ADD RISK: $f"
done
```

Any "new file" in the diff that already exists on `automation/base` is a blocker.
`.agents/workflow.md` § Branching says work branches are cut from `automation/base`
and never target `main` — this is one of the concrete costs of deviating.

## How it was actually resolved (2026-08-27, ELITEA-1886/#1812)

Neither of the two options a reviewer naturally offers ("re-target the branch" /
"restore the full file content"). A **third, better** one, and it is the one to
recommend first next time:

> **Split the commit by base.** Keep the fix branch **spec-only** (PR to `main`,
> per the already-promoted-test fix policy), and land the memory **directly on
> `automation/base`** where the full-context files live.

Why it beats re-targeting: the branch strategy for a fix to an already-promoted
test (`branch from main` → `PR to main`) may be fixed by the card and by
precedent, so re-targeting is not always available to the implementer. Removing
the colliding paths from the branch achieves the same protection without
contradicting the strategy — and the memory lands where it can be a *modify*
(`36 0`, `2 0`, `5 0` — zero deletions) instead of an add/add.

Verify a claimed split with `git show <sha> --numstat`: every row must read
`N 0`. A non-zero second column on `MEMORY.md` or an existing entry means prior
content was dropped.

## Reviewer trap this exposed (my own error, cost a near-false-confirm)

Do **not** put `git fetch origin` and a command that reads `origin/<ref>` in the
same parallel tool batch — they race, the read runs against the pre-fetch ref,
and a delta diff comes back **EMPTY**. An empty diff reads as "nothing changed",
which is exactly the false-clean the § fresh-ground-truth rule exists to prevent.
Fetch in its own call, or chain with `&&` in one shell.

Authoritative delta check on a **force-pushed** branch — compare the blobs, never
the branch names:

```bash
diff <(git show <old-sha>:<path>) <(git show <new-sha>:<path>)
git rev-parse <old-sha>:<path> <new-sha>:<path>   # differing blob ids = real change
```
