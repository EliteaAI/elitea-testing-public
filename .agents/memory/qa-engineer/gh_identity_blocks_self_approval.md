---
name: gh identity blocks self-approval on formal PR reviews
description: gh pr review --approve fails when the local gh auth matches the PR author; use gh pr comment as the fallback
type: reference
---

In this environment the local `gh` CLI is authenticated as the same GitHub
account (`bermudas` / Alexander Bychinskiy) that authors the test-automation
pipeline's PRs (implementer commits, orchestrator dispatch, etc.). When the
reviewer slot tries a formal review:

```
gh pr review <N> --approve --body "..."
```

GitHub's GraphQL API rejects it:

```
failed to create review: GraphQL: Can not approve your own pull request (addPullRequestReview)
```

This is an account-identity limit on GitHub's side (self-review is disallowed
regardless of session/role framing) — not something `--repo` flags, `-u
GITHUB_TOKEN` prefixing, or a different review `--body` will route around.

**Fallback that works:** post the same verdict + evidence as a plain PR
comment instead of a formal review object:

```bash
env -u GITHUB_TOKEN gh pr comment <N> --body "$(cat <<'EOF'
## Reviewer verdict: APPROVED
...full findings + evidence...
EOF
)"
```

This still lands on the PR, is still visible to humans/audits, and still
carries the pasted command+output evidence the reviewer slot is required to
post. It just isn't a GitHub "Review" object (no green/red review badge) —
note that explicitly in the comment so a human skimming the PR knows why
there's no formal review state, and say so in the final report back to
whoever dispatched the review.

First confirmed on PR #561 (ELITEA-1897) during a fresh-session qa-engineer
reviewer pass. Expect this to recur on every future review in this repo
until the `gh` auth identity changes — check this note before assuming
`--approve` will work, and go straight to the comment fallback if the PR
author is also `bermudas`.
