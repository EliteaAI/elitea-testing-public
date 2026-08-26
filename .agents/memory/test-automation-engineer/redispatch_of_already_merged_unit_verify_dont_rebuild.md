---
name: Re-dispatch of an already-merged unit — verify, don't rebuild
description: An empty `git log <trunk>..<branch>` means merged-not-missing as often as never-started; check the trunk's merge commits BEFORE assuming a killed attempt.
type: feedback
aliases: [already merged unit, re-dispatch, empty branch diff, merged not missing, rebuild guard]
tags: [area/pipeline, type/process]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

The combined-slot dispatch says "check whether your feature branch already
exists with commits from a killed attempt (`git log <trunk>..<branch>`)". That
command returns **empty** in two opposite situations:

1. **Never started** — the branch has no work. Build it.
2. **Already merged** — the branch is an *ancestor* of the trunk, so there is
   nothing in `trunk..branch` by definition. Do **not** build it.

Reading (2) as (1) means rebuilding a unit that already shipped: duplicate
specs, a second PR, and a re-run of analysis whose AFS is already committed.

## The check that disambiguates (do this FIRST, before writing anything)

```bash
git --no-pager log --oneline -12                 # look for "merge <CASE-IDs> into <trunk>"
ls test-specs/<feature>/ | grep <CASE-ID>        # AFS already present => analysis half done
env -u GITHUB_TOKEN gh pr list --repo <repo> --state all --limit 8 \
  --json number,state,headRefName,baseRefName,title
```

A trunk merge commit naming your case ids + an AFS on disk + a `MERGED` PR into
the trunk = the unit is complete. `git log <trunk>..<branch>` returning 0 then
**confirms** it merged, it does not contradict it.

## What to do instead

Verify inheritance, then **re-run the merged spec(s) once on the current trunk
head** — that is the only thing a re-dispatch can usefully add, because units
merged *after* yours could have regressed it. Report the verification, the
existing PR number, and `reruns: 0`. Don't cut a new branch, don't re-analyse,
don't open a second PR.

## Confirmed twice, same batch (artifacts-w02, 2026-08-21)

- **ELITEA-1825** — re-dispatched after PR #1627 merged; re-ran 1/1 PASS 69.76s.
- **ELITEA-1830 + ELITEA-1833** — re-dispatched after PR #1628 merged
  (trunk commit `0bf73950b`); re-ran 2/2 PASS 89.64s, no regression from the
  ELITEA-1834 unit merged after it.

Both times the branch existed, both times `trunk..branch` was empty, and both
times the correct answer was "already done", not "killed attempt".

Related: [[resume_dispatch_trust_disk_not_prior_session_notes]] · [[dispatch_tree_starts_on_trunk_cut_your_own_branch_first]]
