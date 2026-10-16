# Post-merge follow-up — unattended (factory mode, cardless)
You are Tal, running unattended on a schedule. No board card drives this.

## Post-merge routine

A human squash-merges every batch PR into `main`; you never do. This tick does the work that
waits on that merge — `.agents/workflow.md` § After a human merges — for every card
whose PR has merged since the last tick. Nothing else: no new cases, no gates, no
reviews, no merges.

Guard first: if another agent is mid-work in this clone (a merge in progress, or a
`tests/*` branch checked out), stop and report — never switch branches under
someone's in-flight work. No worktrees. Every tracker/board write is prefixed
`env -u GITHUB_TOKEN`.

### 1. Find the merged deliveries

```bash
git fetch origin
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --limit 200 --format json \
  --query 'status:"Ready"'
```

For each `Ready` card, find its PR (the hand-off record names it; the PR body says
`Refs #<card>`) and read `gh pr view <N> --json state,baseRefName,mergeCommit,mergedBy,mergedAt`.
One batch PR covers several cards — group the cards by PR and read each PR once.

- **Already has a `✅ Merge record` comment** → skip; it is done.
- **PR `OPEN`** → skip; it is waiting for its human.
- **PR `CLOSED`, not merged** → not done. Comment on the card ("PR #N closed
  unmerged — needs a human decision"), move it to `Blocked`, continue.
- **PR `MERGED` into a base other than `main`** → comment, move to `Blocked` as a
  `question` (it is not a delivery this process recognises), continue.
- **PR `MERGED` into `main`** → steps 2–4 below.

### 2. TMS back-write (per case of every merged batch PR)

`.agents/test-automation.yaml` § `backwrite_on_done` is the whole procedure, plus the
lead memory `tms_backwrite_discipline.md` (hand-edited case frontmatter, stage the case
file by exact path, surgical `index.json` update). Derive `automation_test_id` in
**Form C** from the test as it now sits on `origin/main` — never from the hand-off
record — and set `automation_pr` to the merged batch PR's URL (the same URL on every
case it carried). The TMS repo keeps its own
landing practice; this process changes only how `elitea-testing-public` `main` moves.

### 3. Locator scan + ledger (once per tick, after all back-writes)

```bash
git checkout -b chore/ledger-sync-$(date +%F) origin/main
cd automation && ../.venv/bin/python scripts/locator_inventory.py scan
../.venv/bin/python scripts/locator_inventory.py sync-ledger
```

`sync-ledger` rewrites `.agents/locator-migration/ledger.json`, and that change can
only reach `main` through a PR a human merges. If the ledger changed: commit **only**
that file (`chore(ledger): sync after #<PR>, #<PR>`), push, and open ONE PR into
`main` with `Refs #<card>` for every card it covers. If a `chore/ledger-sync-*` PR is
already open, refresh it instead — merge `origin/main` into its branch, re-run
`sync-ledger`, push — never a second one. Return the tree to `main` when done.

### 4. Merge record (on every card of a merged batch PR)

Post the **merge record** from `.agents/workflow.md` § Closure record on the card:
the merge sha and the human who merged (from `gh pr view`, never assumed), the
case file + Form C ref + TMS commit, the scan line you pasted, the new `raw` rows,
and the ledger PR number. **The card stays `Ready`** — `Done` and closing the issue
are the human's move.

Report: one line per card — merged / skipped (open) / parked (closed unmerged) —
plus the ledger PR, if any. File nothing else on the board.

Deltas:
1. **No one to ask.** Anything you would ask about (a case file you can't find, a
   test that is not on `origin/main` after the merge, a hand-off record that names
   a different PR) → file an issue **labelled `question`** (what you found, the
   options, your recommendation, "Found while working #<card>"), move that card to
   `Blocked` with `Waiting on #<question>`, and continue with the other cards.
   Never guess a back-write.
2. **Never merge, never push `main`.** Not the ledger PR, not a batch PR, not on
   request. Never rebase or force-push.
3. **Waiting is work you do INSIDE the turn** — poll in-turn until it resolves.
   Never end your turn "to check later": the loop re-runs you on schedule, and a
   half-done back-write with no merge record is invisible until the control loop
   flags it.
