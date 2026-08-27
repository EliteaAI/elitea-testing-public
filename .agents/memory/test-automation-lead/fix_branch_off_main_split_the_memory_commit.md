---
name: A [Fix] branch cut from main truncates .agents/memory — split the commit, don't patch it
description: Repair cards mandate branch-from-main, but memory files live fuller on automation/base; keep the PR spec-only and land memory directly on automation/base
type: technique
aliases: [fix branch main memory collision, add/add memory conflict, spec-only PR, memory commit branch point, repair branch base]
tags: [area/git, area/test-repair, type/technique]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`[Fix][ELITEA-xxxx]` cards for already-promoted tests mandate **branch from `main`,
PR to `main`** (precedent PR #1848/#1811, and #1851/#1812). But `.agents/memory/**`
is **tracked** in this repo and diverges hard between the branches — `automation/base`
is hundreds of commits ahead, so:

- `chat_send_button_force_click_race.md`: **58 lines on `automation/base`**
  (frontmatter + Recurrences 1-2), **absent on `main`**
- `MEMORY.md`: **55 lines on `main`** vs **147 on `automation/base`**

An IC who commits memory on a main-cut branch therefore writes a *frontmatter-less
fragment* as a "new file", and edits the truncated index. On the eventual
`main → automation/base` merge that is an **add/add conflict on the very note that
documents the bug being fixed** — resolved carelessly it deletes the prior recurrences
and ~92 lines of index. (The ELITEA-1790 merge already hit this: its commit message
reads *"ledger/memory conflicts resolved keeping both sides"*.)

## The fix — split, don't patch

The reviewer offered "restore the full content onto the branch" as a minimum. **Better:
remove memory from the fix branch entirely.**

1. Fix branch carries **one file** — the spec. Verify: `git diff origin/main...<branch> --stat`
   must show exactly 1, and `git log --name-only origin/main..<branch> | grep '^\.agents/'`
   must be empty (branch *history*, not just the diff).
2. Memory lands **directly on `automation/base`**, appended to the real files. Direct
   `docs(memory):` commits there are established practice — no PR.
3. Prove it additive: `git show <sha> --numstat` — **every row's second column must be `0`**.

Result: the later merge is clean (verified — `99cb44ae8` merged only the spec), and no
conflict resolution can lose anything. The reviewer agreed this beats both options he
had offered and recorded it as first-recommended.

## The same trap bites when RESTORING a stashed working copy

Landing another role's uncommitted memory, I nearly clobbered it: their working copy of
`daily/2026-08-27.md` was **20 lines** (main-based) against `automation/base`'s **51**.
`cp` would have deleted 33 lines of that day's earlier entries.

Append only what is genuinely new:

```bash
git checkout -- "$D"                       # restore the FULL branch version first
grep -vxF -f "$D" /tmp/their-copy.md | grep -v '^[[:space:]]*$' >> "$D"
git diff --cached --numstat                # must read N<TAB>0
```

**Never `cp` a working copy over a tracked file whose branch version you have not
diffed.** Same class as the closure-record false-negative rule: a wholesale overwrite
that *looks* like a restore is a silent deletion.

Related: [[pr_fixes_keyword_auto_closes_issue]]
