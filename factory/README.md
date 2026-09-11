# Factory mode

Run the test-automation team unattended. Same Tal, same skills, same tracking
discipline as your interactive sessions — a loop launches him instead of you.

## How the two modes fit together

**Headed mode does not care about any of this.** Interactive Tal is the
untouched bundle — no board duties, no statuses, no factory awareness. When
you want work queued, you just ask him ("file an issue per un-automated
case") and that's his ordinary issue-tracking skill, on request. The board is
YOUR control panel for the factory, not a discipline imposed on your
sessions.

```
 you (+ headed Tal on request)              the factory (unattended)
 ─────────────────────────────              ────────────────────────
 issues get filed → land in Backlog         works ONLY cards in Approved
        │                                            │
        ▼                                            ▼
 you approve: drag to Approved ──────────▶  run.sh picks the next one
                                            one issue = one conversation
 handle its questions/bugs, then                     │
 drag back to Approved ◀─────────────────   questions/bug park the
                                            card as Blocked and stop
```

**One gesture runs everything: the drag to `Approved`.** It starts new work,
wakes answered work, and retries stuck work. Nothing is ever worked without
it. All board duties live in the factory's loop prompts — the agents follow
them because the dispatch says so, only there.

## Setup (once)

0. If you copied `factory/` here by hand, restore the execute bits first —
   copying can drop them (`zsh: permission denied` on step 6 means this):

   ```bash
   chmod +x factory/*.sh
   ```

1. Create the tracking repo and a Projects v2 board with Status columns:
   `Backlog · Approved · In Progress · Blocked · Done`. In the project's
   settings enable two built-in workflows (UI-only, no API — setup.sh cannot
   check these): **auto-add** for the tracking repo, and **item added →
   Status: Backlog**. From then on every issue filed lands on the board by
   itself — by you or by Tal planning.
2. `gh label create question -R <tracking-repo>` and same for `bug` —
   the child-issue types (conversation places, never worked as tasks).
3. Fill in `factory/config.env` (repo, board number, status names).
4. *(Optional)* Copy `factory/SEED.md` into `.agents/profile.md` § Project
   systems — ONLY if you also want interactive sessions to know the board
   exists (e.g. so headed Tal files straight into it by habit). Skip it and
   headed mode stays completely board-unaware, which is fine. If you do seed:
   the seed and the loop prompts are mirrors — same labels, same parking
   lines, same board duties; change a convention in both or the board goes
   bilingual (`setup.sh` cross-checks the facts, prose is on you).
5. Two keys in `.claude/settings.json` (added to your existing file):

   ```bash
   jq '. + {cleanupPeriodDays: 90, enableAllProjectMcpServers: true}' \
      .claude/settings.json > /tmp/s.json && mv /tmp/s.json .claude/settings.json
   ```

   `cleanupPeriodDays`: each issue owns a long-lived conversation; the 30-day
   default expires them mid-case. `enableAllProjectMcpServers`: the repo's
   `.mcp.json` servers (Playwright, TMS, …) need approval to load, and
   headless sessions have nobody to approve — without this they silently run
   without the project's own tooling.
6. `gh auth refresh -s project` if your token lacks the project scope, then
   `./factory/setup.sh` — it tells you what's still missing and caches the
   board ids the escalation write needs.

Factory sessions run with `PERMISSION_MODE="bypassPermissions"` (config.env):
unattended sessions cannot click "approve", so a permission wall dead-ends the
run — the first live attempt proved it. Your interactive sessions are
untouched. This makes the next paragraph more than a nicety:

Strongly recommended, one command: require the CI check on the work repo's
`main` (branch protection). With it, a red PR cannot merge even if an agent disobeys
its prompt; without it, the merge gate is the loop-prompt rule "merge only on
a green `gh pr checks` exit".

## Landing on an existing project (minimal)

Already have agents filing issues in GitHub, and no appetite for the full
setup? The minimum is:

1. Add two Status columns to your existing board: `Approved` and `Blocked`
   (`In Progress` and `Done` usually already exist).
2. Point `factory/config.env` at your existing repo and board — `TRACKING_REPO`
   may be the work repo itself; a separate repo is a recommendation, not a
   requirement. Map the status names to your actual column names.
3. `./factory/setup.sh && ./factory/run.sh tal --once`.

That's all: the loop prompts carry the board duties themselves, so nothing
needs seeding — headed mode neither knows nor cares that a factory exists.
Do create the `question`/`bug` labels early (step 2 above, two commands):
they are load-bearing — the loop refuses cards carrying them, which is the
only thing stopping a bug report dragged to `Approved` by mistake from being
"worked" as a task. Until they exist, that guard is inert.

## Which tasks the factory picks up

One switch: **status `Approved`**. That column means exactly "the factory may
work this now" — nothing enters it except by a human's drag, and everything a
human or Tal files starts in `Backlog`. Tasks you track for yourself simply
never go to `Approved`. Question/bug issues are conversation places, never
tasks: loops refuse them even if one lands in `Approved` by mistake.

When the factory gives up on a card (3 stalled sessions), it comments and
parks the card as `Blocked` — the one time a script touches the board — so
the retry gesture is the same as everywhere else: drag back to `Approved`.
The counter resets at escalation, so a dragged-back card gets three fresh
attempts, and it resumes its conversation — the agent remembers what already
failed (add a steering comment before dragging to point it somewhere new).
If the repeated failure smells like the *conversation* is the problem — the
agent stuck in a wrong mental model — close the issue and file a fresh one
referencing it: new number, new conversation, genuinely clean start.

## Use

```bash
# Fill the backlog — that's Tal's job, in a regular session:
#   "Compare smoke/ and the WebQA folders against tests/ and file a Backlog
#    card in the tracking repo for every case that has no spec yet."
# …then drag the ones you approve to Approved, and:
./factory/run.sh               # work them until the board is empty
```

Ctrl-C stops it; nothing is lost. Each issue owns one conversation per agent
(id derived from the issue number, posted on the issue). The loop always tries
to resume it, and starts fresh under the same id if it doesn't exist yet, has
expired, or you moved machines — the thread carries the history either way.

**Blocked cards.** The parking comment names what the task waits on
(`Waiting on #63 #64`); each child names its task. Handle the children however
fits: answer a question in its thread, close a fixed bug, close an irrelevant
one as not-planned, or comment handling guidance on a real bug and **leave it
open**. Then the one gesture that matters: **drag the task back to
`Approved`** — the factory never guesses whether your answering is finished;
you say so with the drag. Dragged-back cards **jump the queue** (existing
conversations before fresh cases), and the agent resumes warm, reading the
children's threads for your answers and decisions.

**One conversation per issue, never two.** For history, read the issue thread
(that's what the work log is for). To steer, comment on the thread — the agent
re-reads it on every resume. To go hands-on: stop the loop,
`claude --resume <id>` from the factory's directory, work with the agent,
exit, restart the loop. (Issue comments never include that directory — they
are public; the operator knows where the factory runs.) Never resume while the loop is running, and never
fork — a second context on one issue diverges silently.

Don't move or rename the work-repo folder while cases are open: the directory
is part of conversation identity. If you do, the loop stops and tells you,
rather than silently restarting every case from scratch.

## When a coped-with bug finally gets fixed

A bug left open with handling guidance means some merged tests are coping with
it (isolated soft-asserts, adjusted flows). When it gets fixed for real:

1. Find what coped with it — the bug's thread names the task that filed it,
   and the rest are one search away:
   `gh issue list --search '"Waiting on #64" in:comments' -R <tracking-repo>`
2. **Reopen** the affected task and **drag it to `Approved`** — the same
   gesture as every other wake; a card's past doesn't matter to the queue.
   The factory resumes the task's original conversation, which remembers
   exactly what was masked and why. Comment "bug #64 is fixed — restore the
   real asserts", and close the bug.
3. Prefer a fresh card when the rework's scope differs from the original task
   (one bug touching five tests) — file it referencing the bug; old tasks
   stay closed history.

## Several agents at once

A loop = an agent + a queue filter + a prompt: `factory/loops/<name>.env`
(`AGENT`, `QUERY`, `POLL`, optional `WORKDIR`) and `factory/loops/<name>.md` —
the agent's complete unattended prompt: who it is, what changes with no human
present, its mission, and what `Done` means. Every session's dispatch is that
file plus one line naming the issue. Subagents never see it: they get their
own agent definitions and hook-injected context, exactly as in interactive
mode.

```bash
./factory/run.sh              # loops/tal.env — Tal on Approved cases
./factory/run.sh sage         # loops/sage.env — another agent, its own queue
./factory/run.sh --all        # every loop in loops/ at once; Ctrl-C stops all
```

Each loop sets its own cadence via `POLL` (`30s`/`5m`/`1h`): with it, an empty
queue means "sleep, check again" at zero token cost; without it, the run ends.

**Queue disjointness is your job — and an empty `QUERY` is a catch-all.**
`QUERY` terms are ANDed onto every queue read; Tal with `QUERY=""` takes every
card in his trigger column, including ones meant for a specialized loop. Pair
each specialized filter with its negation on the catch-all: sage
`QUERY="label:repro"` ⇒ tal `QUERY="-label:repro"` (negation verified against
a live board). A loop can also react to a **different column entirely** —
`STATUS_READY="Repro"` in its `.env` overrides the trigger per loop (any
config.env value can be overridden per loop; the env is sourced after it).

**Exclusive loops**: `EXCLUSIVE=1` makes a loop wait until every other loop's
current session finishes, then hold a lock while each of its own sessions
runs — all other loops pause at the gate meanwhile. For work that must never
run in parallel with anything (schema migrations, repo-wide refactors). Locks
are PID-stamped and stale-swept, so a killed loop never deadlocks the fleet.

If two loops **write code** at the same time, give each its own clone via
`WORKDIR` — two agents editing one working tree collide in git. Conversation
ids include the agent name (`repo#issue#agent`), so different agents get
different conversations even on the same card — a sage repro conversation and
a later Tal automation conversation on one issue never mix. Two loops sharing
one agent share conversations per issue, which is exactly why their queues
must not overlap.

## Cardless loops — missions on a cadence, no card needed

Not everything is card-driven. `CARDLESS=1` in a loop's `.env` skips the
queue entirely: the loop runs its mission on the `POLL` cadence and sleeps —
no claims, no attempts, no outcome reads. First use: intake
(`loops/EXAMPLE-intake.*`) — scan the TMS source for un-automated cases on a
6-hour tick and file Backlog cards (capped per run, deduped by title against
open AND closed issues; a human still approves every card by dragging).
Whatever a cardless mission files lands on the board like anything else.

One persistent conversation per cardless loop (id derived from the loop
name), so the agent remembers previous ticks — but its real dedup is always
against the board, so long-term memory decay is harmless. Renaming the loop
file starts a fresh conversation; nothing else changes. Cardless loops honor
the exclusive gate like everyone else, and join `--all`.

## What each piece is

| File | Does | Writes to board? |
|---|---|---|
| `config.env` | the facts: repos, board, statuses, caps | — |
| `SEED.md` | optional: board awareness for interactive sessions (→ profile.md); mirrors the loop prompts' conventions | — |
| `loops/<name>.md` | the loop agent's full prompt: unattended deltas + mission + what Done means | — |
| `loops/<name>.env` | the loop's mechanics: agent, filter, cadence, `CARDLESS`/`EXCLUSIVE` flags | — |
| `run.sh` | pick card → run the agent → read outcome | only to park an escalated card |
| `setup.sh` | preflight checks + caches board ids | no |
| `state/` | local runtime — pids, claims, attempt counters, last logs, the cached board ids (`board.json`, re-cached by `run.sh` at startup when older than a day). Gitignored; never share between machines. | — |

Factory agents move statuses themselves, per their loop prompts. The loop reads
the board, launches sessions, and comments; its single write is parking a card
the agent can no longer park itself. Judgment lives in prose (the seed and the
loop prompts); scripts do only what a script can check.
