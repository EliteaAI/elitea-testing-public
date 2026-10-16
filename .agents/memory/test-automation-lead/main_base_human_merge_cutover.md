---
name: Base is main, humans merge (cut-over 2026-10-16)
description: Since 2026-10-16 every batch lands as ONE PR into main that a human squash-merges — the lead gates and hands off, never `gh pr merge`; back-write, ledger sync and the merge record wait for the human merge
type: project
---

## What changed

Operator ruling 2026-10-16: the factory works against **`main`**, not
`automation/factory`. Agents **open PRs into `main`; a human merges them.**
`automation/factory` and `automation/base` are frozen history — never branch from,
PR into or sync them. Any memory, skill example or daily log that says "merge into
`automation/factory`/`automation/base`" or "you merge (squash) autonomously" predates
this and is superseded.

## Your first moves now

- Cut the batch trunk from a freshly fetched `origin/main`; no session-start sync.
- **One ticket = one batch = one session = ONE PR.** Batches: `base: "main"`,
  `prUnit: "trunk"`. Units branch from and merge back into `tests/batch-<slug>`; after
  the 3× gate on the trunk you open ONE PR trunk → `main` covering every case
  (`.agents/role-overrides.md` § Orchestrator slot). A batch of one = one case branch
  → `main`. Never split a ticket into per-case PRs; dependent cases belong in the
  same batch. A case needing ANOTHER batch's open PR → park `Blocked`,
  `Waiting on #<PR>`; never stack.
- Terminal state = batch PR **ready** (not draft), every unit reviewer-APPROVED, your
  3× gate green on the trunk, hand-off record on every card, cards `Ready`, issues
  OPEN. PR body: one row per case, `Refs #<card>` for each (a closing keyword would
  close the cards at merge and skip the post-merge work), "Squash and merge".
- **Never** `gh pr merge` into `main`, `git push origin main`, rebase or force-push.
- After the human squash-merges (postmerge loop / your next session): TMS back-write
  for every case in the batch (`automation_pr` = the batch PR merged into `main`), `index.json`, `scan` + `sync-ledger`
  on `origin/main` landed via one `chore/ledger-sync-<date>` PR, a merge record on
  every card. Cards stay `Ready`; `Done` is human-only.
- `main` moved under an open PR and touches its files / PR conflicts → merge
  `origin/main` into the PR branch, re-gate, post the fresh result.

**Why:** an agent-merged base meant nobody but the factory saw a change before it
landed; a human merge is the acceptance step, and the lead's gate is its evidence.

**How to apply:** treat the steps above as canon over any older note; the
authoritative text is `.agents/workflow.md` (§ Branching, § After a human merges,
§ Closure record) and `.agents/role-overrides.md` § Orchestrator slot.
