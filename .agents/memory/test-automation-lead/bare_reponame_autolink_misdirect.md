---
name: Bare reponame#N autolinks to the wrong repo
description: GitHub's autolinker doesn't recognize "EliteaUI#526" as a cross-repo reference — it silently re-parses the trailing #N against the CURRENT repo, producing a wrong link; only the full "EliteaAI/EliteaUI#526" form is safe
type: feedback
---

## What happened

Control-audited issue #67 (ELITEA-1889, PR #558) — a delivery I did not write.
Its closure record's promotability table and summary line used bare
`EliteaUI#526` / `#540` / `#567` (repo name, no owner prefix) for cross-repo
references to EliteaAI/EliteaUI PRs. Fetched the actual rendered HTML
(`gh api -H "Accept: application/vnd.github.html+json"
repos/.../issues/67/comments`) to check clickability, expecting either a
correct cross-repo link or plain unlinked text. Found worse: in the
free-text summary paragraph, GitHub's autolinker split `EliteaUI#540` and
linked only the bare `#540` portion — to **elitea-testing-public's own**
PR #540 (`test(ELITEA-1872): Edit agent instructions and verify
persistence`), a completely unrelated PR. In table cells the same string
rendered as inert plain text (no link at all) — less actively wrong, but
still non-compliant with the canon's "clickable cross-repo link"
requirement.

## Why it matters

`.agents/workflow.md` § Closure record already warns about this by name:
*"Bare `#<M>` links to THIS repo's #M (wrong)... write
`EliteaAI/EliteaUI#<M>` as PLAIN TEXT."* This audit is the first time I've
seen it actually manifest as a wrong clickable link rather than just sit as
a theoretical warning — worth escalating from "eyeball whether links look
right" to a fast mechanical check.

## Rule going forward

- **When writing a closure record**: always use the full
  `EliteaAI/EliteaUI#<M>` form for every cross-repo reference, in prose AND
  inside table cells — never the bare `EliteaUI#<M>` short form, even
  though it reads fine to a human.
- **When auditing a closure record (item 4)**: grep the raw markdown for
  `EliteaUI#` NOT preceded by `EliteaAI/` — any hit is a violation. Don't
  stop there if a hit exists in free prose (not a table cell) — pull the
  rendered `body_html` via `gh api -H "Accept: application/vnd.github.html+json"`
  and check whether the autolinker attached an `<a href>` to the trailing
  `#N` pointing at the WRONG (current) repo. A same-repo mislink to an
  unrelated PR/issue is a stronger, more concrete finding than "not
  clickable" — cite the wrong target's actual title as evidence.
