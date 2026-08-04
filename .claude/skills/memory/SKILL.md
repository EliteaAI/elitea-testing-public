---
name: memory
description: Per-role persistent memory — durable facts, preferences, decisions, and a daily log, as plain markdown. Use when the user says "remember this" or "log this", asks "what did you learn yesterday", or whenever you discover something worth keeping across sessions.
license: Apache-2.0
metadata:
  authors:
    - Artem Rozumenko <artem_rozumenko@epam.com>
  version: "0.3.0"
---

# Memory

Persistent per-role memory as plain markdown. You — the agent — read and
write these files directly using your `Read`, `Write`, `Edit`, and `Glob`
tools. No CLI, no script, no shell-path fragility. Works on any host, from
any working directory.

## File layout

Under `.agents/memory/<role>/` (where `<role>` matches your agent's
`name:` frontmatter — e.g. `project-manager`, `python-dev`, `scout`):

```
.agents/memory/<role>/
├── MEMORY.md                ← index of the entries worth INJECTING (not all of them)
├── <slug>.md                ← individual curated entries (frontmatter + body);
│                              an entry may exist with no index line — that is normal
├── project_briefing.md      ← seeded by scout at install time (type: project)
├── daily/
│   └── YYYY-MM-DD.md        ← episodic daily logs, append-only
└── snapshot.md              ← host-generated convenience (often absent)
```

Create directories with `mkdir -p` on first use. Do not write
`snapshot.md` yourself — a host launch hook *may* generate it, but nothing
regenerates it automatically on every host. If it's absent, that's normal:
you read memory directly when you need it.

`.agents/` is an IDE-neutral path so the same memory works whether this
agent is running under Claude Code, Cursor, Gemini CLI, Windsurf, or
Copilot CLI.

## Legacy paths (one-time migration)

If you find memory under one of these older locations and `.agents/memory/<role>/`
doesn't exist, migrate it before your first write:

| Old location | New location |
|---|---|
| `.claude/memory/<role>/` (directory) | `.agents/memory/<role>/` — move the whole dir |
| `.agents-legacy/memory/<role>/` (directory, older install) | `.agents/memory/<role>/` — move the whole dir |
| `.claude/memory/<role>.md` (flat file, from the former `project-seeder` skill) | `.agents/memory/<role>/project_briefing.md` — wrap the existing content with `type: project` frontmatter (see "Write" op below) and add an index line — a project briefing is preventive by definition, so it earns one |

Migrate with `Bash` (`mv` for directories) or `Read`/`Write` (for the flat
file → curated entry conversion). Do this once; afterwards ignore the old
paths.

## Three tiers, by what they cost

Writing is cheap. The scarce thing is a line in `MEMORY.md`, because that file
is injected into **every dispatch** — so an index line is paid for by every
agent, forever, whether or not the fact is relevant to what they're doing.
Keep the two decisions separate: *write the entry* and *index the entry* are
not the same act.

| Tier | Costs | Found by | Use for |
|---|---|---|---|
| **Daily log** (`daily/<today>.md`) | nothing | the last 3 days are read on demand | what happened today — episodic, transient |
| **Entry, no index line** (`<slug>.md`) | **nothing** | `Grep` over the memory dir | the default for a durable fact: real, kept, retrieved when the task touches it |
| **Entry + index line** | **injected into every dispatch** | already in context | only a *preventive* fact (below) |

**An entry without an index line is not a lesser entry** — it is the normal
case. It is on disk, it is permanent, and it is found the moment someone greps
for the surface it belongs to.

### What earns an index line: it must be preventive

Ask: **would having this in front of me change my FIRST move, on a task where I
wouldn't know to look for it?**

- *"PRs target `automation/base`, never `main`"* — yes. You act on it before you
  would ever think to search. → index line.
- *"The MUI popover doesn't close after `window.open()`"* — no. It only matters
  once you are already on that surface, and then you'd grep for it. → entry only.

This is a test you can actually apply to your own finding, unlike "has it
recurred?" — you see one task and cannot know what other tasks hit. Recurrence
is judged later, by the compaction pass that sees many.

Most findings are of the second kind. In one campaign, all 176 of a role's
entries were surface-specific lookups, and all 176 took an index line anyway —
that is how a 124 KB index happens.

**If unsure: log it, or write the entry without an index line.** Both are cheap
and reversible. Promotion is the compaction pass's job.

## Size limits — what a compaction pass enforces

`MEMORY.md` is injected into every dispatch, so it has a hard budget. You are
not asked to police these while working — write what you learn. A periodic
**compaction pass** (`session-retrospective` § Compaction) brings the set back
under them:

| What | Limit |
|---|---|
| An index line | **≤120 characters** including the link — a hook for deciding whether to open the entry, not a summary of it |
| A curated entry | **≤4 KB** — past that a reader gets a truncated view instead of the fact |
| A fact scoped to one ticket, case, or file | not an entry at all — a `daily/` line |

Two habits keep the pass cheap, and both cost nothing at write time:

- **Replace, don't append.** When a fact recurs, rewrite the entry body and
  leave its index line alone. An entry that lists its own occurrences
  ("fifteen confirmed instances: …") has become a log, and logs go in `daily/`.
- **Name entries by what you'd search for later** — the surface, component or
  symptom (`login_stale_prefill.md`), not the ticket you happened to hit it on.

Field evidence for the budget: one role's index reached **124 KB across 171
entries** — a mean of 723 characters per "one-line" entry — because every
recurrence was appended to its description. Past ~48 KB the launch hook can no
longer inject it, so **302 of 302 dispatches in one campaign silently ran on a
2 KB preview** of their own memory. Dense technical text runs ~2.2 bytes/token,
not the usual ~4, so a "small" 147 KB entry is ~67,000 tokens.

## Four curated types

Every curated entry carries a `type:` field:

| Type | Holds |
|---|---|
| `user` | Who the user is — role, expertise, preferences, working style |
| `feedback` | Corrections and validated approaches. Always include *why* |
| `project` | Goals, deadlines, constraints, in-flight initiatives. Decays fast — re-verify before acting. **Scout seeds one here at install time (`project_briefing.md`)** covering stack, conventions, and role-specific gotchas. |
| `reference` | Pointers to external systems (Linear projects, Slack channels, dashboards) |

---

## Committing memory: where you stand, or the base branch — by pipeline

**In the serial batch pipeline (one working tree, one writer at a time):
commit what you produce, by exact path, on the branch you are on.** The
analyst commits memory with its AFS on the batch trunk; the implementer and
reviewer commit theirs with their work on the case branch; the merge carries
it to the trunk, and a parked unit's memory is landed by the merge agent
anyway. This is safe *because* units are serial: the next branch is cut only
after the previous one merged, so it inherits the day's memory and **appends**
— a modify, never an add/add collision. Never leave entries as loose files:
uncommitted knowledge sat untracked for a whole campaign under the old rule,
and one wholesale `git stash --include-untracked` swept six entries mid-wave
(field incident 2026-08-03) while every later agent ran without them.

**How you know which regime you are in: your dispatch says so — and when it
doesn't, assume parallel.** The pipeline announces itself in the prompt: a
batch-workflow dispatch opens with "dispatched from the batch workflow", and a
lead's sequential dispatch hands you the batch geometry — a trunk, a case
branch that is yours alone, an AFS path. Exclusive tree ownership is the
defining property, and only the dispatch can grant it; you cannot infer it
from `git status`. No such grant — you were launched standalone, picked up a
task on a mission board, or work beside a feature team — means you must assume
other branches exist in parallel. The default errs the cheap way: wrongly
treating a pipeline dispatch as parallel costs one lesson being reported
instead of committed; wrongly treating a parallel context as the pipeline
recreates the add/add conflict disaster below.

**Outside that pipeline — anywhere parallel branches may exist — the old
caution stands.** `MEMORY.md` and `daily/<today>.md` are append-at-the-end
files every role touches at the same spot; committed from concurrent branches
they collide on every merge. Measured on one campaign of that era: **26 of 32
merge conflicts came from exactly these two files** (81% of all conflict
work). In parallel contexts, commit memory on the **base branch** or put the
lesson in your returned result for the orchestrator to record — one recorded
lesson beats the same lesson committed on twelve branches.

## Operations

### Log — append to today's daily log

To record `<text>`:

1. Determine today's date. Use the `Today's date is …` line in your
   environment context. If not present, run `date -u +%Y-%m-%d`.
2. Target path: `.agents/memory/<role>/daily/<today>.md`.
3. If the file **does not exist**, `Write` it:
   ```
   # Daily log — <today>

   - [HH:MM] <text>
   ```
4. If the file **already exists**, `Edit` to append a single new line at
   the end: `- [HH:MM] <text>`.

Use 24-hour `HH:MM`. One observation per line. Keep it terse — full
sentences are fine; paragraphs belong in curated entries.

### Write — create or replace a curated entry

To record a curated entry named `<name>` with `<type>`, `<description>`,
and `<content>`:

1. **Slugify** `<name>`: lowercase, replace non-alphanumerics with `_`,
   strip leading/trailing underscores. Example: `User Timezone` →
   `user_timezone`.
2. **Target path**: `.agents/memory/<role>/<slug>.md`.
3. **`Write`** the file with this exact frontmatter (`name`, `description`,
   `type` are parsed by memory tooling — don't omit them, don't
   add extra keys, keep each on one line):
   ```markdown
   ---
   name: <name>
   description: <description>
   type: <type>
   ---

   <content>
   ```
4. **The index is a separate decision — not an automatic step.**

   **Default: stop here.** The entry is written, permanent, and findable by
   `Grep`. It costs nothing. Most facts belong exactly here.

   Add an index line **only if the fact is preventive** (§ Three tiers) — it
   would change someone's first move on a task where they would not know to
   look for it. If it does:

   - **If a line already refers to `<slug>.md`**, `Edit` that single line
     to the new description. One entry = one line, no duplicates.
   - **If `MEMORY.md` doesn't exist**, `Write` it:
     ```markdown
     # Memory index — <role>

     - [<name>](<slug>.md) — <description>
     ```
   - **Otherwise**, `Edit` to append one new line at the end:
     `- [<name>](<slug>.md) — <description>` — **≤120 characters**, a hook that
     helps a reader decide whether to open the entry, never a summary of it.

   Updating an existing entry: rewrite its **body**. Leave its index line alone
   unless the hook itself is now wrong — never append the new occurrence to the
   description.

### Read — recall memory on demand

1. **If snapshot content is already in your context** (some hosts inject
   `.agents/memory/<role>/snapshot.md` at launch), you already have curated
   memory and recent daily logs — don't re-read them.
2. **Otherwise** (the common case — many hosts never generate a snapshot),
   read memory directly:
   - `Read .agents/memory/<role>/MEMORY.md` for the curated index.
   - `Read .agents/memory/<role>/<slug>.md` for any entry the index
     points you at. Scout's `project_briefing.md` is usually the most
     load-bearing on a new project.
   - `Glob .agents/memory/<role>/daily/*.md`, sort by filename
     descending, and `Read` the most recent 3 files.
   - **`Grep` the memory dir when the index doesn't answer you.** A compaction
     pass demotes narrow entries — the file stays, its index line goes — so
     those are reachable *only* this way. Search by what you are touching: a
     surface, a component, a file path, an error string.

Bounded recall keeps your context small — don't tail the whole daily log
history.

### Rename / delete

- **Rename** a curated entry: `Write` the new `<new-slug>.md`, remove the
  old file, `Edit` `MEMORY.md` to replace the single line.
- **Delete**: remove `<slug>.md`, `Edit` `MEMORY.md` to drop its line.
- **Never edit a daily-log entry after the fact.** Log a correction as a
  new line instead — the audit trail is the point.

---

## What belongs in memory vs. somewhere else

- **Memory** — durable facts and ephemeral working notes that matter *to
  you as an agent* across sessions: user preferences, project constraints,
  lessons from corrections, references to external systems.
- **Not memory** — anything a human other than you should be able to find.
  That goes in the user's knowledge base (e.g. `obsidian-vault`), the
  project's docs, the issue tracker, or the code itself.

Some agents also keep role-specific operational state in this directory
(e.g. personal-assistant's `people-pending.md`). That's fine — the layout
is yours to extend, as long as `MEMORY.md`, `<slug>.md`, and `daily/`
follow the spec above.

---

## Snapshot.md — a host convenience that may be absent

`snapshot.md` is an optional host artifact: a launch hook *may* generate it
by inlining `MEMORY.md`, curated entry bodies, and recent daily logs into a
single file it injects at startup. Nothing regenerates it automatically on
every host, so expect it to be missing or stale.

You never write `snapshot.md` yourself. When it isn't in your context, the
`MEMORY.md` index is your map to the entry bodies: read
`project_briefing.md` and the other entries it lists on demand — no error,
no interruption.
