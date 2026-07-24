---
name: gh api compare verifies testid-branch provenance without a local EliteaUI checkout
description: In an isolated fix-round worktree with no sibling EliteaUI clone reachable (sandbox blocks cross-directory git ops), `gh api repos/EliteaAI/EliteaUI/compare/<ref>...<sha>` gives the same ahead/behind ancestry answer as `git -C ../EliteaUI log --oneline <ref>..<sha>` — use it to verify a Concrete-Handles provenance finding (testid on automation/testids? on main?) when the sibling repo isn't accessible.
type: feedback
---

**Situation.** A fix-round dispatch lands in a fresh isolated worktree
(`.claude/worktrees/wf_.../`). Unlike the main checkout, there's no sibling
`../EliteaUI` clone reachable from it — the harness's worktree-isolation
guard refuses any command that reaches outside the worktree's own directory
(`cd ../EliteaUI && git ...` gets blocked). But a reviewer finding may still
require verifying testid provenance (e.g. "these testids were pushed to
`automation/testids` in this same PR, not `needs-adding`" — ELITEA-2033
fix round, PR #1041, finding 6).

**Fix — use the GitHub REST compare endpoint via `gh api` instead of local
git:**

```bash
# does commit <sha> exist as an ancestor of automation/testids?
gh api repos/EliteaAI/EliteaUI/compare/automation/testids...<sha> \
  --jq '.status,.ahead_by,.behind_by'
# status=behind, ahead_by=0  ⇒  <sha> IS an ancestor of automation/testids
#   (ahead_by=0 means <sha> has no commits automation/testids lacks;
#    behind_by=N means automation/testids has N commits <sha> lacks)

# is the same commit ALSO on main yet?
gh api repos/EliteaAI/EliteaUI/compare/main...<sha> \
  --jq '.status,.ahead_by,.behind_by'
# status=ahead, ahead_by=143  ⇒  <sha> has 143 commits main does NOT have
#   ⇒ NOT an ancestor of main (not yet promoted)
```

Also useful for identifying which testids a commit actually touched, without
cloning:

```bash
gh api repos/EliteaAI/EliteaUI/commits/<sha> --jq '.files[].filename'
gh api repos/EliteaAI/EliteaUI/commits/<sha> --jq '.files[].patch' \
  | grep -o 'pipeline-router-node-[a-z-]*' | sort -u
```

**Why this matters:** `git fetch origin` from the isolated worktree only
fetches the CURRENT repo's remote (`elitea-testing-public`), not EliteaUI's
— there is no local ref to walk. `gh api .../compare/...` hits GitHub's
server-side ancestry graph directly, giving the identical
ahead/behind/status answer the workflow.md closure-record recipe expects
from `git grep`/`git log`, without needing the sibling clone at all. This
is a within-worktree-limits substitute, not a lesser check — the fresh-
ground-truth requirement (`.agents/role-overrides.md`) is satisfied because
`gh api` always reads the server's current state, same as `git fetch
origin` would.

**Caveat:** this verifies ancestry/reachability and file-level diffs, not a
live `git grep` across the tree at that ref. For a FULL closure-record
promotability sweep (every testid the case's diff uses, cross-checked
against both refs) the orchestrator still needs the local EliteaUI clone
per `.agents/workflow.md` — this technique is for a single-commit provenance
check inside a sandboxed worktree, not a replacement for the closure-record
procedure.
