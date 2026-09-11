# Seed: work tracking (OPTIONAL — interactive board awareness)

> **Sync contract:** this file and `factory/loops/*.md` state the SAME
> conventions (labels, parking lines, parent references, board duties) —
> they differ only in stance (human present vs not). Change a convention in
> one place, change it in both, or the board becomes bilingual and the
> factory's child-issue guard misses reports.

**Factory mode does not need this file.** The loop prompts carry all board
duties; headed sessions neither know nor care that a factory exists.

Copy the section below into `.agents/profile.md` § Project systems ONLY if
you also want interactive sessions board-aware — e.g. so a headed Tal files
cards straight into the tracking repo by habit, sweeps Blocked cards on
request, or answers "what's on the board?". The session hooks inject
`profile.md` into every session, so seeding makes both modes speak the same
tracking language. No skill is modified either way.

---

## Work tracking (board)

All task tracking lives in **<TRACKING_REPO>** (issues + Projects board
**#<N>**, owner **<OWNER>**) — never in this repo. The board's `Status`
column is the state machine:

| Status | Meaning | Who sets it |
|---|---|---|
| `Backlog` | Filed, not yet approved | whoever files it |
| `Approved` | A human approved it; may be worked | human only |
| `In Progress` | Being worked right now | you, when you start |
| `Blocked` | Waiting on a human — the last comment says why | you, when you park it |
| `Done` | The PR is merged. Nothing else counts as done | you, after the merge |

Rules you follow in every session:

- **Track what you work.** When you take a task: assign yourself if not
  already assigned, move it to `In Progress`, and keep a work log in comments
  (🔧 started / 📝 update / 🚫 blocked / ✅ done).
- **You never move a card to `Approved`.** Approval is a human gesture — the
  drag. `Approved` means exactly "the factory may work this now"; tasks a
  human tracks for themselves simply never go there. When you file new tasks (intake, planning),
  just create the issue in <TRACKING_REPO> — the board's auto-add workflow
  places it in `Backlog`. Leave it unassigned.
- **Parking (questions and bug).** Blocked on a decision: file a separate
  issue **labelled `question`** in <TRACKING_REPO> (the question, the options
  you see, your recommendation). Found a product bug: file a separate issue
  **labelled `bug`** (steps, expected vs actual, evidence) — and never mask
  it: no `test.fail()`, skip, or weakened assert to force a green. The two
  labels are load-bearing: they mark these issues as conversation places the
  factory must never work as tasks. Either way the child's body must name
  where it came from — "Found while working #<task>" — so a human reading it
  can find the task and its conversation. Then park the task: move its card to `Blocked`
  and comment which issues it waits on (`Waiting on #63 #64`) so the human
  knows what to answer. **A human wakes the task by dragging its card back to
  `Approved`** — only after that do you see it again. On resume, read the
  referenced children's threads first: the answers, fixes, or "not relevant /
  handle it this way" decisions live there (a bug may stay OPEN with handling
  guidance — e.g. isolated `expect.soft()` with the ticket linked — never a
  hidden green). First move your card out of `Blocked`, then continue.
- **Board mechanics** (when you need to move a status): find your card through
  the ISSUE, never by listing the board — `gh project item-list` costs about one
  GraphQL point per card requested (`--limit 1100` → 1111 points, measured
  2026-09-11), out of the 5000-point hourly pool every
  session and every factory loop of the same user share. One point instead:
  `gh api graphql -F n=<issue> -f query='query($n:Int!){ repository(owner:"<OWNER>",name:"<REPO>"){ issue(number:$n){ projectItems(first:10){ nodes{ id project{ number id } fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue { name optionId } } } } } } }'`
  (the node whose `project.number` is <N> carries the item id, project id and
  status). Status option ids: `factory/state/board.json` (0 points; cached by
  run.sh/setup.sh — `gh project field-list` costs ~100). Then `gh project
  item-edit`. Verify with the same issue query.
  Look ids up when needed; never hardcode them in memory.

In an **interactive session** the human in the room authorizes work — look at
whatever they ask, plan, triage, file cards freely (into `Backlog`).
In **factory mode** (the dispatch says so) there is no human: work only the
one issue your dispatch names — it reached you because a human dragged it to
`Approved`.
