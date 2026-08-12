---
name: AFS "filed" claims need a real tracker check, not a trust
description: An AFS Status/Known-Defects line claiming "N clarifications filed" is a claim like any other — grep the tracker for the case id before trusting it; a filed defect doesn't imply its sibling clarifications were too.
type: feedback
---

## Rule

An AFS's Status metadata block and Known-Defects section narrate what the
analyst DID (filed issue #N, filed M clarifications) — but "narrated" and
"true" are independent, same as any other AFS claim
(`afs_claims_need_full_sweep_and_grep.md`). Don't assume a partially-verified
claim (one real, linked defect issue) means the REST of the same sentence is
also true.

## Seen (ELITEA-2614, PR #1471, 2026-08-12)

The AFS's Status line read: "One MINOR product defect filed (#1470) ... Two
case-text CLARIFICATIONs filed for imprecise expected strings (the toast and
the '+Skill' tooltip's literal wording)." `#1470` genuinely exists, labeled
`bug`, body correctly references ELITEA-2614. The two CLARIFICATIONs do not:
`gh issue list --repo EliteaAI/elitea-testing-public --state all --limit 300
--json number,title,body` filtered for `'ELITEA-2614' in body` returned only
`#1470` and the campaign tracking card `#1399` — zero `question`/
`case-text-drift`-labeled issues for either the toast-wording or the
"+Skill"-tooltip-wording drift the AFS itself documents as reverse-masking
CLARIFICATIONs. The test code correctly asserts the LIVE strings either way
(so this is not a masking bug), but the two drifts are now UNTRACKED —
nothing will resurface them for a human wording pass over the source TMS
case text.

## Remedy

- When an AFS/Status block lists N filed items, verify EACH one independently
  — `gh issue list ... --json number,title,body` filtered by case id, not a
  single spot-check on the first (often the most severe, most memorable) one.
- A found-but-unfiled CLARIFICATION isn't a blocking implementer-PR defect
  (the implementer's diff is faithful to the live strings regardless), but it
  IS a real process gap — route it back to the analyst/orchestrator to file
  the missing issue(s), don't let it silently ride through as "already
  tracked."

See also: afs_claims_need_full_sweep_and_grep.md · reviewer_verifies_never_trusts.md
