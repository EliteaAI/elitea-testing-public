---
name: A tracker comment naming AFS file paths may be a promise, not a fact
description: A GitHub issue comment listing "delivered" AFS file paths can predate/outlive the actual commit — verify with git log --all / git fsck before reusing the paths or trusting the priority prefixes in them.
type: feedback
created: 2026-08-26
updated: 2026-08-26
tags: [area/afs, area/tracker]
---

## Rule

Before reusing file paths cited in a tracker (issue/PR) comment as if they are
real, on-disk artifacts — especially paths a PRIOR session claims to have
"delivered" — verify they actually exist somewhere in git history:

```bash
git log --all --oneline -- "<claimed/path>"
git rev-list --all --objects | grep -i "<slug-fragment>"
git fsck --lost-found   # then grep dangling commits' messages if the above is empty
```

An empty result on all three means the comment describes work that was never
committed anywhere reachable — the session that posted it likely crashed or
was cut off between "post the tracker comment" and "commit the files" (the
wrong order — commit-then-report is the contract), or fabricated the comment
outright. Either way, treat the comment as a plan, not a source of truth: do
the analysis yourself, and if the comment also asserted derived facts (e.g. a
priority-digit mapping in the filename prefix), re-derive those independently
too rather than copying them — they can be wrong even when the intent was
honest (see below).

## Seen (ELITEA-2242/2243/2244, batch settings-w01, 2026-08-26)

Clarification issue EliteaAI/elitea-testing-public#1772 had a correction
comment naming three exact AFS paths under `test-specs/settings-navigation/`
as "delivered" with priority prefixes `l1`/`l2`/`l2`. None of the three paths
existed anywhere in `git log --all`, `git rev-list --all --objects`, or
`git fsck --lost-found` dangling commits — genuinely never committed. Also,
the claimed prefixes were wrong: `spec-format.md` maps `1=critical,
2=high, 3=medium, 4=low`; the cases' own TMS frontmatter is `high, medium,
medium`, which maps to `l2, l3, l3` — the stale comment had shifted every
one up by a level. Wrote the real files this run and posted a correcting
comment.

## Remedy

- Don't skip live execution because a tracker comment claims the analysis
  already happened — that comment is exactly the kind of unverified claim
  `afs_filed_issue_claims_need_tracker_verification.md` already warns about,
  just one level up (the artifact's *existence*, not just a sub-claim inside
  an existing artifact).
- When you do end up reusing a prior comment's filenames (as continuity, not
  as fact), re-derive anything numeric or structural in them — priority
  digits, counts, mappings — from the actual case data instead of copying.

See also: afs_filed_issue_claims_need_tracker_verification.md ·
afs_claims_need_full_sweep_and_grep.md
