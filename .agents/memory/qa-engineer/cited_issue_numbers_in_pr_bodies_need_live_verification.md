---
name: Cited issue numbers in PR bodies/comments need live verification
description: "#636" in test_artifacts_create_bucket_upload_file.py's delete_bucket comment does not resolve to any issue/PR in elitea-testing-public (or elitea_issues/onetest-ai-tm-Elitea) — a stale/wrong citation, inherited and repeated across PRs
type: project
---

Found reviewing PR #2420 (ELITEA-2493 fix). The PR body/Run Report cites a
"known, already-filed, pre-existing defect #636" for `ArtifactAPI.delete_bucket()`
404ing on DEV, pointing at the identical `try/except + logger.warning` comment in
`automation/tests/ui/artifacts/test_artifacts_create_bucket_upload_file.py:338-349`.

Checked live: `gh issue view 636` / `gh pr view 636` against
`EliteaAI/elitea-testing-public` both return "Could not resolve" — #636 does not
exist in this repo as either an issue or a PR. It's not in `elitea_issues` or
`onetest-ai-tm-Elitea` either (elitea_issues#636 is an unrelated closed VS Code
tooltip issue). `git log -S"#636"` traces the citation back to commit `e286172f`
(PR #643, ELITEA-1808) — it has been silently copy-pasted into every subsequent
PR/comment that touches `delete_bucket()` cleanup since, including this one,
without anyone re-checking it resolves.

**Lesson: when a PR/Run Report leans on "already tracked as #N" to justify NOT
re-filing or NOT fixing something, verify #N actually resolves — in THIS repo
first, then the other two (`elitea_issues`, `onetest-ai-tm-Elitea`) — before
accepting the claim.** A citation that looks load-bearing (reused verbatim
across multiple files/PRs) is exactly the kind nobody re-checks. Did not block
PR #2420 on this (the underlying delete_bucket 404 is out-of-scope for that fix
either way, and #2420 only repeats a pre-existing citation, doesn't introduce
it) — flagged as a non-blocking finding recommending someone file the real
ticket. `gh issue view <n>` / `gh pr view <n>` is a one-call check, cheap enough
to always do before trusting a cited number.
