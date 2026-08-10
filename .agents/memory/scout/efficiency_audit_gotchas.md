---
name: Efficiency-audit gotchas on this project
description: Three recurring traps when running /efficiency-audit here — read before quoting any dollar
type: preventive
---

Confirmed across the 2026-08-04, 2026-08-05, 2026-08-06 and 2026-08-09 audits.
Check all of them **before** quoting a figure; each one has produced a wrong
number, a wrong comparison, or a wrong *finding* at least once.

## 1. `externalOk: false` is benign HERE — but verify, don't assume

The skill calls `reconciliation.externalOk: false` a red flag. On this project it
is almost always the **date-window artifact**: the flattened metering dir picks up
hard-linked transcripts from *prior audits* still on disk, so
`ccusageMeteredSum` (~$6.7k, 2239 files) dwarfs the window total and
`orphanFiles` runs ~1800.

**The check that distinguishes benign from broken:**
- `costMethod: metered` (NOT `allocated`) → per-file metering ran. Benign.
- `internalOk: true` → ledger = byRole = byDay = byProject sums. Benign.
- `costMethod: allocated` **on a session that dispatched sub-agents** → genuinely
  broken; the total is parent-only and is a floor, not the cost. Do not quote it.

## 2. `--resolved-from` only scans ONE level under `.agents/automation/`

It finds `.agents/automation/<slug>/report.json` and **misses**
`.agents/automation/<campaign>/wave-*/report.json`. Hit twice (2026-08-04,
2026-08-06). It silently under-counts the denominator — the delivery section just
reports fewer cases, with no warning.

**Always** run `find .agents/automation -name report.json` and compare the count
against `delivery.batches.length` before trusting `perDelivered` / `perExamined`.

## 3. Multi-day sessions land on their START date — this makes or breaks comparisons

A session started 08-01 and run through 08-04 contributes **$0** to a
`--since 2026-08-03` window. This cuts both ways:

- It silently drops long campaign sessions out of a window you thought covered
  them.
- It is also what lets you compare two operating eras cleanly — but only if you
  *prove* the boundary.

**Proof required before claiming two windows are comparable:** confirm the other
era's orchestrator session id appears in the ledger as neither `id` nor
`parentId`, and that the first in-window session starts after the prior era's
last report closed. Both were verified for the 08-06 era comparison.

## 4. `skills` in the ledger is NOT "skills the agent used" — it inherits

The rollup builds each unit's `skills` from **two** sources: real `Skill` tool
calls **and** the host's `attributionSkill` record field, which sub-agents
**inherit from whatever skill the parent had active**. On 2026-08-09 this made
`sync-base-branches` the window's #1 "skill" (103 units) and nearly produced a
headline waste finding ("94 sub-agents each re-syncing 3 OneDrive repos").
Truth: **4,313 inherited attributions, ZERO actual invocations** in the
campaign's 252 workflow agents.

**Always verify before treating `skills` as behaviour:**
```bash
# real invocations only
grep -ho '"skill":"[a-z-]*"' <session>/subagents/**/*.jsonl | sort | uniq -c
# the contaminating field
grep -ho '"attributionSkill":"[a-z-]*"' <same> | sort | uniq -c
```
Converse trap: a skill can be *consumed* without being *loaded* —
`test-case-analysis` showed 1 invocation while 121 of 252 agents `Read`
`spec-format.md` directly. Absence in `skills` is not evidence of skipping.

## 5. Workflow-tool agents live 3 levels deep — `<session>/subagents/workflows/<wf_id>/`

Not `<session>/subagents/`. A campaign session shows only ~3 files there while
the ledger reports 250+ children. `find <session> -name 'agent-*.jsonl'` to
locate them; the `workflows/*.json` files beside them are run manifests, not
transcripts.

## 6. "Since the last audit" ≠ "since the last audit FILE'S date" — check for a gap

An audit run at 15:45Z on day N does not cover sessions that *start* later that
day. The 2026-08-06 week audit (run 15:45Z) and the 2026-08-07 overnight audit
(one session only) left **3 lead sessions / $58.91 covered by neither**. Before
setting `--since`, list top-level sessions for the prior audit's day and confirm
none started after that audit's own session began.

## Bonus: role labels collide on this team

`qa-engineer` and `test-automation-engineer` both end in `-engineer`. Any quick
grouping by `role.split("-").pop()` silently merges the analyst and implementer
slots — which are the two biggest cost lines. Match on the full role string.
