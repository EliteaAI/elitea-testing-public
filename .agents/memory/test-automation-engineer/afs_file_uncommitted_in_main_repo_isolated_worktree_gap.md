---
name: AFS file left uncommitted in main repo — invisible to isolated implementer worktrees
description: The analyst's AFS markdown named in an implementer dispatch may exist only as an uncommitted working-tree file in the main repo checkout, not in git history at all — isolated worktrees never see it.
type: feedback
---

Dispatched for ELITEA-2082/2083/2080, my prompt named
`test-specs/chat-interface/l2_create-toolkit-from-conversation-canvas_ELITEA-2082-2083-2080.md`
as the AFS to read. It did not exist anywhere in my isolated worktree, and
`git log --all -- <path>` from that worktree found it on NO branch at all.
The file DID exist, but only as an uncommitted file sitting in the main
repo's working tree (`git status --porcelain` there would have shown it as
`??`) — the analyst session had written it to disk but never `git add`/
committed it.

Isolated worktrees only get committed refs checked out — untracked files in
the main checkout are invisible to them (same class of gap as `.venv`/
`.env.test`, which needed special-casing already, per the repo's own commit
history). I had to `Read` the file directly via its absolute path in the
MAIN repo's working tree, then `Write` its content into my own worktree at
the matching path and commit it as part of my branch — otherwise my test's
own docstring reference to the AFS path would have been dangling in my PR.

**Takeaway for next time:** if a named AFS path 404s inside an isolated
implementer worktree, don't assume the case is unautomatable or the
dispatch is wrong — check the MAIN repo's working tree for an uncommitted
copy before escalating. And flag it upstream: AFS files should be
committed by the analyst slot as part of its own deliverable, not left as
loose uncommitted files, or every downstream isolated-worktree implementer
re-hits this same gap.
