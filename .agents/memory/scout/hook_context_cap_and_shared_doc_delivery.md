---
name: Hook additionalContext cap and how shared docs actually reach agents
description: Claude Code hard-caps SessionStart/SubagentStart additionalContext at 10,000 chars, so the sdlc-skills hook silently truncated shared docs AND role memory. Shared docs now reach every session via CLAUDE.md @-imports (uncapped); role memory still rides the hook, so MEMORY.md + project_briefing.md must together fit the cap.
type: project
---

## The cap

**Claude Code hard-caps hook `additionalContext` at 10,000 characters**
(doc- and transcript-verified, 2026-07-23). `sdlc-skills`'
`build_capped_context` assumed Claude Code was uncapped and therefore
silently truncated both the shared docs and each role's own memory into a
`<persisted-output>` preview-plus-file-pointer. Affected sessions ran on a
~2 KB preview of their own memory without any error surfacing.

## The fix that shipped

- **Shared docs no longer go through the hook.** `.claude/hooks/sdlc-skills/config.sh`
  sets `SDLC_SHARED_DOCS=__none__` — a **sentinel, not an empty string**. An
  empty string does NOT work: `shared_doc_names()`'s own `${VAR:-default}`
  treats `""` identically to unset and restores the defaults.
- **`CLAUDE.md` `@`-imports all 8 root `.agents/*` docs instead.** Uncapped,
  reaches every dispatched subagent, survives compaction — strictly more
  robust than the hook ever was.
- **Consequence for memory:** role memory still rides the hook, and the
  payload is `MEMORY.md` + `project_briefing.md` (+ `snapshot.md` if present)
  concatenated. So the real per-role budget for `MEMORY.md` is roughly
  `10000 − project_briefing − 250`, not the 32,768 the hook reports.
  As of 2026-07-30 the briefings are 5.4–7.6 KB, i.e. **61–76% of the whole
  payload** — they are now the binding constraint, and are themselves ~80%
  verbatim restatement of docs `CLAUDE.md` already imports. Trimming them is
  the next win.

## Corollary — anything you add to `.agents/*.md` is paid for by every session

Because the 8 root docs are `@`-imported everywhere, a memory entry that
merely restates one of them costs twice. The 2026-07-30 compaction found
~19 such entries across three roles. Before writing a durable fact to
memory, grep the shared docs first.

## Related, same date

- **Board is `EliteaAI/projects/9` "Test Automation Factory"** — NOT
  `ProjectAlita/9`, which is Support. Easy and costly to confuse.
- `automation_test_id` canon is **Form C** (dotted, `tests.`-rooted) —
  verified by correlation replay, issue #598, now written into
  `.agents/test-automation.yaml`.
- `.agents/**` pushes direct to `automation/base`; no PR needed.

## Loops built for this, and their status

- `factory/loops/memory-guard.{env,md}` — **authored 2026-07-23, never run**
  (no `factory/state/last-memory-guard.log`, no pid, no crontab entry as of
  2026-07-30). Its strategy is also wrong for curation: it archives
  **oldest-first, verbatim, and explicitly forbids merging or rewording**, so
  it would archive old durable rules while keeping recent one-off lookups.
  Retire or rewrite it rather than starting it — see the 2026-07-30
  retrospective.
- `factory/loops/EXAMPLE-docs-compaction.{env,md}` — STAGED, propose-only
  draft-PR. Measured 10.2% safe redundancy across the 8 shared docs. Prose
  compaction is not mechanically verifiable the way a memory archive-move is,
  which is why it is not autonomous.
