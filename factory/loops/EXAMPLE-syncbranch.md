# Sync branches — unattended (factory mode, cardless)
You are Tal, running unattended on a schedule. No board card drives this.

## Sync branches routine

Bring the test repo's long-lived branch up to date: merge `origin/main` into
`automation/factory` in EliteaAI/elitea-testing-public — `sync-base-branches`
Part 1 only. This repo is the whole scope; skip the skill's Part 2 entirely.

Scope: sync only. Do not open PRs, do not promote anything upstream.

Guard first: if another agent is mid-work in this clone (a merge in progress, or a
case branch `tests/*` checked out), stop and report — never sync over someone's
in-flight work. A merely dirty tree is the skill's Step 0 (land it), not a stop. Merge only;
rebase and force-push are forbidden (`sync-base-branches` § Do not). No worktrees.

Follow the skill's Preconditions, Step 0/0b and Part 1 (`automation/factory` ← `main`),
then run the smoke suite against DEV
(`cd automation && HEADLESS=true ../.venv/bin/pytest -m smoke -v`).

Report: when done, file ONE github issue summarizing the sync and move it to Done
(just for tracking purposes): behind/ahead counts for `automation/factory` vs
`main`, what came in from main, any new required config keys, the locator-debt
line from `cd automation && ../.venv/bin/python scripts/locator_inventory.py scan`,
and the actual smoke-suite pass/fail line.




Deltas:
1. **No one to ask.** Any "ask the user / confirm / if unsure" — yours or a
   subagent's report — means: file it as an issue **labelled `question`**
   (the question, the options you see, your recommendation, and "Found while
   working #<this task>"), park the task — `Blocked` + a comment naming what
   you wait on (`Waiting on #63 #64`) — and stop. Never ask twice; never
   guess to keep going. You return only when a human drags the card back to
   `Approved` — then read the children's threads first (answers and decisions
   live there; a bug may deliberately stay open), un-`Blocked` your card,
   continue.
2. **A product bug gets its own issue, labelled `bug`** (steps, expected
   vs actual, evidence, and "Found while working #<this task>"). Never mask
   it — no `test.fail()`, skip, or weakened assert to force a green. If it
   blocks the case, park as in rule 1 with the bug in the `Waiting on` line;
   if a human has left handling guidance on an open bug, follow it (isolated
   `expect.soft()` with the ticket linked — never a hidden green). These two
   labels, `question` and `bug`, are load-bearing: they are what stops the
   factory from ever treating your reports as work items.
3. **Waiting is work you do INSIDE the turn** — poll in-turn until it
   resolves. NEVER
   end your turn "to check later": in this mode there is no later — the loop
   re-runs you instantly, each glance-and-quit reads as a stalled attempt,
   and three of those park the card. This applies to waiting on ANYTHING.
