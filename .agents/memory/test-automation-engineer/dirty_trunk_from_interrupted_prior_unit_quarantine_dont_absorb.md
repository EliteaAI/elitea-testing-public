---
name: Dirty trunk from an interrupted prior unit — quarantine onto its own branch, don't absorb or clean
description: If `git status` on arrival shows uncommitted work for a DIFFERENT case than yours, a prior unit's implementer session was interrupted before Phase 6 (commit/branch/PR). Rescue it onto its OWN branch (git checkout -b, add by exact path, commit, push) BEFORE cutting your own branch — never silently include it in your commits, never `git clean`/`stash` it away.
type: feedback
---

## What happened (ELITEA-2605, implementer, 2026-08-12)

Dispatched to implement ELITEA-2605 on batch trunk `tests/batch-skills-remaining-w2`.
`git status` on arrival showed modified `automation/pages/skill_form_page.py`,
modified `test-specs/skills/l2_..._ELITEA-2604.md`, and an untracked full test
file `test_skill_custom_icon_upload_and_validation.py` plus 2 untracked memory
entries — all clearly **ELITEA-2604** work (a different, earlier case in the
same wave), complete-looking (280-line test file with live-observed docstrings,
2 EliteaUI testid-fix commit SHAs cited in the AFS's own "Implementation-time
findings" section), but never committed. A prior implementer session had
evidently done the real work and reached Phase 6 without executing it — no
branch, no commit, no PR — leaving the trunk itself dirty.

## Why this matters

- **Never silently absorb it into your own commit** — it's a different case;
  mixing it into your ELITEA-2605 diff misattributes work, corrupts the
  Coverage Map story, and would ship an unreviewed/unverified test under the
  wrong ticket.
- **Never `git stash`/`git clean`/`git checkout -- .` it away** — that's
  exactly the "never clean the tree wholesale" violation; the work is real
  and undocumented anywhere else, so discarding it destroys it permanently.
- **Don't just leave it dirty and work around it either** — if you cut your
  branch via `git checkout -b <mine>` while it's still uncommitted, the dirty
  files ride along into your branch's working tree (uncommitted state follows
  you across checkouts), and when you later `git checkout <trunk>` to hand the
  tree back, those files vanish from the working directory (git silently
  reverts to the trunk's committed state) — the ONLY way they survive is if
  they got committed somewhere first.

## The fix — quarantine before doing anything else

```bash
# 1. Branch from the current (dirty) trunk state — checkout -b carries the
#    uncommitted changes with it, doesn't touch them.
git checkout -b tests/<other-case-id>-<slug>

# 2. Stage ONLY the other case's exact paths (never -A/.)
git add <path1> <path2> ...

# 3. Commit with a message that says plainly this is a recovery, not your
#    own verified work — name that Phase 4 (Execute) was never run by you.
git commit -m "test(<OTHER-CASE-ID>): <slug> (recovered)

Recovered from uncommitted work found on <trunk> at the start of <YOUR-CASE-ID>'s
dispatch — an interrupted prior implementer session left this uncommitted
instead of on its own branch. Quarantined verbatim to avoid losing it.
NOT verified by this session — Phase 4 (Execute) was never run against this
content by me. Route through a normal implementer dispatch or a fresh
Execute pass before treating it as done."

git push -u origin tests/<other-case-id>-<slug>

# 4. NOW return to the trunk (clean — the commit above absorbed everything)
#    and cut YOUR OWN branch from it.
git checkout <trunk>
git status --short   # should be empty
git checkout -b tests/<your-case-id>-<slug>
```

Flag the recovered branch in your own PR body/findings so the orchestrator
routes it (a normal implementer/reviewer dispatch, or at minimum a fresh
green-run verification) — you rescued the artifact, you did not verify it.

## Distinct from the "I committed on the wrong branch" family

This is NOT the `verify_feature_branch_before_first_commit.md` failure mode
(where YOU forget to cut your own branch before committing YOUR OWN work).
Here the dirty state belongs to someone else's case and was already there
when you arrived — the fix is quarantine-then-proceed, not a branch-name
gate on your own commits. Both lessons matter on the same dispatch: check
`git status` AND `git branch --show-current` on arrival, before touching
anything.
