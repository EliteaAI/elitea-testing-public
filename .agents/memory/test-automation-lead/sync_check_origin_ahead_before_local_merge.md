---
name: Check origin/automation/factory ahead before the mandatory local sync merge
description: Another concurrent session (e.g. factory-ops) can already have merged main into automation/factory on origin before you fetch — a blind local `merge origin/main` then produces a redundant divergent merge commit instead of a fast-forward.
type: feedback
---

## The trap

The per-session mandatory sync (`.agents/role-overrides.md` § Orchestrator: "Sync
`automation/factory` with `main` before dispatching the first case") is written as a
single linear recipe — `git fetch && checkout automation/factory && merge
origin/main` — that assumes your local clone's `automation/factory` is the freshest
copy of that branch. In a shared-tree, multi-session factory it often isn't: another
actor (notably the `factory-ops` agent, whose whole job is exactly this sync) can have
already run the same merge and pushed it, between your last fetch and now.

If you merge blindly anyway, you get a **second, independent merge commit for the
same `main` content** — same merge-base, divergent tip from `origin/automation/factory`.
It isn't wrong per se, but it's redundant history, and pushing it either races the other
actor's push or forces a confusing extra merge-of-merges later.

## The check (cheap, do it right after `git fetch origin`)

```bash
git log --oneline origin/automation/factory -3
git log --oneline automation/factory -3   # or HEAD if already checked out
```

If `origin/automation/factory`'s tip is already a sync-shaped commit (message like
"sync main into automation/factory", or its tree is way bigger than your pending
`main` diff would justify) and your local tip is behind it — **don't merge locally.**
Just catch up:

```bash
git status --porcelain   # MUST be clean — verify before any reset
git reset --hard origin/automation/factory
```

`reset --hard` is normally banned in this shared tree
(`shared_tree_git_discipline.md`) because it can destroy another actor's uncommitted
work. It is safe **only** in this exact shape: `git status --porcelain` is empty (no
working-tree changes to lose) and the commit being discarded is your own, just-made,
not-yet-pushed, content-redundant merge — never use it to jump branches when there is
any uncommitted diff, yours or anyone else's.

## If you already made the redundant merge

Same remedy: confirm clean status, confirm the discarded commit is yours alone and
unpushed, `reset --hard` to origin's tip, move on. Don't try to rebase or cherry-pick
your merge away — it carries no unique content worth preserving.

## Seen 1×

- #2408/ELITEA-2059 (2026-10-07) — `factory-ops` had already pushed
  `06cb7f00 chore: sync main into automation/factory` before this session's fetch;
  caught by noticing the merge's file list (`.agents/team-comms.md` + 4 new
  `factory-ops` agent files) was far too small to be a real `main`→`factory` sync, and
  confirming via `git log` that HEAD and `origin/automation/factory` shared a merge-base
  but had independent merge commits for it.
