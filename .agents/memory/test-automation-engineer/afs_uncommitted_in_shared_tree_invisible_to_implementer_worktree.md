---
name: AFS uncommitted-in-shared-tree is invisible to an implementer's isolated worktree
description: Analyst-authored AFS files stay UNCOMMITTED on disk in the shared main working tree (no analyst commit authority) — an implementer dispatched into an isolated git worktree only inherits git refs, not untracked files, so the dispatch's AFS path 404s. Read it via the absolute path into the main clone instead, verify it's genuinely not committed anywhere before trusting that read, and recreate + commit it alongside the test.
type: feedback
---

## The gap (ELITEA-1978, batch cov60, 2026-07-24)

Dispatched as implementer with an AFS path
(`test-specs/toolkits-credentials/l2_..._ELITEA-1978.md`) and a board case-snapshot
path (`.agents/automation-board/batches/cov60/cases/ELITEA-1978/source.md`).
**Neither existed in my isolated worktree** (`.claude/worktrees/wf_*`):

- `.agents/automation-board/` is `.gitignore`'d (line 75) — it's local, untracked
  state the orchestrator/clerk maintains in whichever working directory THEY run
  from. A fresh `git worktree` shares refs (branches, commits) but never untracked
  files, so this directory simply doesn't exist in an implementer's worktree.
- The AFS itself is a git-TRACKABLE path, but this batch's analyst-slot convention
  (established across every cov60 case I found in qa-engineer's daily log —
  ELITEA-1828/1851/1877/1880/1934/1937/2219/2232/GAP-003, all sampled) is to leave
  it **UNCOMMITTED on disk in the shared main working tree**, citing "no commit
  authority" (`grep -n "commit authority" .agents/workflow.md` → line 182: "the
  implementer commits... testid commits are part of the implementer/analyst loop").
  Only the feature's `_surface.md` digest gets committed (by the analyst, straight
  to `automation/base`); the AFS proper waits for the IMPLEMENTER to commit it
  alongside the test code (confirmed precedent: ELITEA-1828/1877's memory entries
  say exactly this — "AFS ... committed by the IMPLEMENTER alongside the test code,
  in the same commit").

Since an isolated implementer worktree never had that uncommitted file to begin
with, the dispatch's literal path is guaranteed to 404 under this convention —
this isn't a one-off slip, it's structural to how this batch's analyst slot works.

## What to do (verified sequence, cov60/similar batches)

1. **Don't panic-escalate on a missing AFS path alone.** Check whether it's a
   structural artifact of the uncommitted-AFS convention before concluding the
   analyst never did the work.
2. **Try the absolute path into the MAIN clone** (not the worktree-relative path —
   worktrees nest `.claude/worktrees/wf_*/` deep, so relative paths from there never
   reach the main clone): `Read /Users/.../elitea-testing-public/test-specs/<feature>/<slug>.md`.
   The `Read` tool isn't worktree-git-sandboxed the way `Bash`+`cd`+`git` combos are —
   a plain file read across the boundary works.
3. **Verify it's genuinely not lost, not just uncommitted-on-purpose**, before
   fully trusting the absolute-path read as authoritative — run from your OWN
   worktree (git refs ARE shared):
   - `git log --all --oneline --diff-filter=A -- '*<slug-or-case-id>*'` (exact
     filename, not a loose case-id substring — a loose grep can false-positive on
     unrelated commits mentioning the same digits, e.g. `report: dev run 95`-style
     commits).
   - `git fsck --no-reflogs --unreachable --dangling` + `git reflog show --all | grep <id>`
     (rule out a dangling/orphaned commit).
   - `gh issue list --state all` / `gh pr list --state all` for the case id (rule
     out an abandoned PR/branch elsewhere).
   - Only once all of these come back empty AND the absolute-path read succeeds do
     you have a self-consistent "uncommitted-by-convention, not lost" verdict.
4. **Also check the feature's `_surface.md` digest** (that one usually IS committed
   to `automation/base`, so it WILL be present in your worktree) — it often
   documents the same analysis session and can corroborate/cross-check the AFS's
   claims independently (worked example: ELITEA-1978's digest independently
   confirmed the #1004 defect + the dynamic-testid composition chains).
5. **Also check the relevant `qa-engineer` daily-log entry for the SAME date** (in
   the main checkout, not gitignored) — the analyst's own narrative often contains
   the exact live-session findings (defects filed, ticket numbers, classification
   reasoning) in more depth than the AFS's condensed prose, and can disambiguate
   an AFS claim that turns out to be wrong (see the companion finding below).
6. **Recreate the AFS content verbatim in your own worktree** (Write tool, same
   path) and **commit it alongside your test code, in the same commit** — this
   matches the established implementer-commits-the-AFS precedent, and is the only
   way the AFS content survives into the merged PR at all (the shared-tree copy
   was never going to be committed by anyone else).

## Companion finding this same case: verify AFS claims against LIVE ground truth, not just trust-and-implement

The AFS claimed (Step 6) the disabled `elitea_title`/ID field "stays disabled"
after a duplicate-Display-Name Save rejection, reasoning the backend error's
`field` was NOT `elitea_title`. Live-implementing this literally and running the
test surfaced an immediate, deterministic failure. Ground-truthed via a **direct
API probe** (two raw `CredentialAPI.create_credential()` POSTs with the same
`elitea_title`, entirely bypassing the UI/browser) — the backend's actual error
body IS `{"error": "...", "field": "elitea_title"}`, which DOES match
`CredentialsTabBar.jsx`'s `doSave()` gate and fires `onEnableEditTitle()`,
un-disabling the field. This is exactly the reverse-masking-guard shape (case/AFS
text is a hypothesis, live product is ground truth) — corrected the AFS in place
with the probe evidence and asserted the live contract, not the stale claim. A
direct API/curl probe that isolates the ONE claim in question (bypassing the
browser/UI layer entirely) is a fast, high-confidence way to ground-truth an
AFS's factual claim about backend behavior, when a first implementation attempt
contradicts it — cheaper and more decisive than re-driving the whole UI flow by
hand to eyeball the same thing.
