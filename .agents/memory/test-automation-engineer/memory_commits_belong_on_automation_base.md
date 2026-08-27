---
name: Memory commits belong on automation/base, not on a main-cut repair branch
description: a repair branch cut from origin/main sees TRUNCATED memory files — committing memory there creates an add/add conflict that silently deletes history
type: feedback
updated: 2026-08-27
---

## The trap

Most work branches from `automation/base`, so "commit memory by exact path on
the branch you are on" is safe. **A repair branch cut from `origin/main` is the
exception**, and it is not visually obvious.

`.agents/memory/` is far ahead on `automation/base`. Measured 2026-08-27:

| File | on `origin/main` | on `origin/automation/base` |
|---|---|---|
| `chat_send_button_force_click_race.md` | **absent** | 58 lines (2 recurrences) |
| `test-automation-engineer/MEMORY.md` | 55 lines | **147 lines** |

So memory written on a main-cut branch is written against **truncated or
missing** copies. Git then records the note as a *new file* containing only
your fragment — no frontmatter, no prior content. When `main` later merges into
`automation/base` that is an **add/add conflict on the very note you were
extending**; resolved carelessly it deletes the earlier recurrences and
truncates the index by ~92 lines. The ELITEA-1790 merge already hit this class
("ledger/memory conflicts resolved keeping both sides").

## The rule

**Ask which branch your work branch was cut from, before staging memory.**

- Cut from `automation/base` → commit memory with your work, as usual.
- Cut from `origin/main` (a repair/fix branch targeting `main`) → keep the
  branch **code-only**, and land the memory in a *separate* commit made
  directly on `automation/base`. Direct memory commits there are established
  practice in this repo; no PR is needed.

Verify the branch is code-only before handing off:

```bash
git diff origin/main...HEAD --stat     # expect ONLY the code paths
```

## Doing the split after the fact

If memory is already committed on the fix branch, save the content first, then:

```bash
git reset --soft origin/main
git restore --staged .agents/memory/<role>/      # unstage memory only
# recommit code-only, force-push (fine on a short-lived private fix branch —
# the never-force rule covers automation/testids and automation/base, not this)
```

Then restore each memory file **by exact path** (`git checkout -- <path>` for
tracked, `rm` for untracked), switch to `automation/base`, and re-apply the
knowledge to the **full** files there. Never `git checkout -- .` — other roles'
uncommitted notes routinely sit in the same tree.

Related: [[chat_send_button_force_click_race]] — the note this actually happened to.
