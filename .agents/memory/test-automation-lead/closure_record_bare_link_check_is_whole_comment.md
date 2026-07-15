---
name: Closure record bare-link check is whole-comment, not table-only
description: the cross-repo bare-#N-link rule and internal-consistency checks apply to every line of a closure record, not just the artifact table — audit the whole posted comment text, not just the table cells
type: feedback
---

Origin: control-audit of issue #31 (ELITEA-1789 rework, PR #278), 2026-07-15.

The delivery got every substantive fact right — locator policy, testid
delivery, promotability (independently re-verified with a fresh fetch and
matched line-by-line), merge gate, reviewer gate, TMS back-write. The audit
still had to FAIL it, because the closure record's "**Unblocks when:**" prose
line (below the table) wrote bare `#526, #540, and #545` instead of the
mandated `EliteaAI/EliteaUI#N` plain-text form. Confirmed via
`gh api repos/<this-repo>/issues/526` → 404 that these aren't just
wrong-repo links, they're dead links (this repo's issue numbers don't reach
that high). The same line also said "blocked on ALL FOUR of ... (three
separate draft PRs ...)" — three named PRs, "ALL FOUR" in the lead-in, "three"
in the very next parenthetical. Both errors sat in prose, not in the table
where `.agents/workflow.md` § Closure record's worked example lives.

**Lesson for writing closure records (implementer/lead) and for auditing them
(control mode):** the `owner/repo#N` full-form rule and any accuracy claims
apply to the ENTIRE posted comment, not just the artifact table. When
drafting: after finishing the table, re-scan every other sentence for a bare
`#N` referencing a cross-repo PR/issue, and re-count any prose that
enumerates "how many things this is blocked on" against what's actually
listed. When auditing: don't stop at grep-checking the table rows — pull the
full comment body and grep it for `[^/]#[0-9]+` (bare, not preceded by
`owner/repo`) to catch stray bare links in prose lines, and sanity-check any
"N things" language against the actual enumerated list.
