---
name: A blocked case's AFS still lands on base
description: Analysis-only output is docs — merge it, so a re-attempt inherits it instead of rediscovering it on an orphan branch
type: feedback
aliases: [defect-found AFS, blocked case deliverable, docs-only PR, analysis lands, orphan branch]
tags: [area/orchestration, type/decision]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

A case that ends `blocked` / `defect-found` still produced a **deliverable**: the AFS, the updated
`_surface.md` exploration digest, and role-memory findings. Land them on the base branch as a
docs-only PR.

The batch workflow's `next:` line says "nothing reaches base until it is green" — that guard is about
**specs**. When the branch carries no executable code, the N×-green merge gate is inapplicable: there
is nothing to run. Say so in the PR body rather than inventing a gate.

## Why it matters

The alternative is what actually happened to ELITEA-2094: the July analysis sat on an unmerged branch
for five weeks, went 813 commits stale, and the re-attempt had to re-execute the case from scratch.
Landed analysis is inherited; orphaned analysis is repeated.

## Checklist when landing one

- Secret-scan it — `scripts/scan-secrets.py` needs the files **staged**; run it against a temp index
  (`GIT_INDEX_FILE`) or it reports "clean" on an empty set. Beware crude ad-hoc scanners: matching
  every `.env.test` value flags benign words (`BITBUCKET_REPOSITORY=automation` hits any doc saying
  "automation").
- PR body carries the *why-not-automated*: the defect ref, the live re-confirmation counts, and which
  of the case's steps are unsatisfiable out of how many.
- **Do not close the case as `already-covered` against a sibling that is itself blocked** —
  `already-covered` needs a spec **merged to base**. Closing against a blocked sibling drops the case
  from the remainder invisibly. Record the sequencing (implement the superset first, re-classify
  after) in the AFS instead.
- Close the superseded PR **deliberately, with reasoning**, naming what was salvaged and what the
  branch preserves.

Related: [[stale_parked_card_reanalyse_dont_rebase]]
