---
name: How project context actually reaches agents here (and how to break it)
description: Measured 2026-08-10 — CLAUDE.md @-imports are the ONLY channel for .agents/* docs; the hook carries per-role memory only. Read before touching either.
type: project
---

Measured, not assumed (2026-08-10). Re-measure before trusting these numbers again.

## The two channels

| Channel | Reaches | Carries | Cap |
|---|---|---|---|
| `CLAUDE.md` `@`-imports | every session **and** every sub-agent | the 8 `.agents/*` docs (~95 KB ≈ 24k tok) | none |
| `SessionStart` / `SubagentStart` hook | per role | `RULES.md` + `MEMORY.md` + `project_briefing.md` **only** | nominally 10,240 B |

**`SDLC_SHARED_DOCS=__none__`** in `.claude/hooks/sdlc-skills/config.sh`. The hook
injects **zero** shared docs — they were moved to `@`-imports precisely because the
10 KB cap truncated them. Putting them back is a regression, not an optimization.

## The trap that nearly fired

`role-overrides.md` used to claim in its own header that it was *"hook-injected into
every session and every subagent."* **False.** It arrives only via the `@`-import.
Deleting `@.agents/role-overrides.md` from `CLAUDE.md` silently removes every hard
rule in it — no error, no warning. A corrective warning block now sits in that file;
don't remove it.

## Numbers to compare against

- Median first-turn context prefix, this project: **83.7k tokens**. Other projects on
  this machine: 16–52k. The delta is CLAUDE.md + imports.
- Hook injection after the 2026-08-10 compaction: lead 18.0 KB, impl 13.5 KB,
  qa 11.6 KB, scout 6.8 KB. **All three pipeline roles exceed the nominal 10 KB cap,
  and it is NOT enforced on this host** — verified: the lead's transcript record is
  22 KB and contains the last line of `project_briefing.md`. `lib.sh` warns a host
  *may* drop an oversized payload to a ~2 KB preview; that failure would be silent.

## How to measure it yourself

```bash
# per-role hook payload, exactly as the agent receives it
export CLAUDE_PROJECT_DIR="$PWD"; source .claude/hooks/sdlc-skills/lib.sh
build_capped_context "$PWD" test-automation-lead "" "" | wc -c
```
First-turn prefix: read the first record with a `usage` block in a session's
`.jsonl` and sum `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.

## What the budget lever actually is

**The memory INDEX, not `CLAUDE.md`.** In 2026-08-10 the three pipeline
`MEMORY.md` files held 151 index lines over 606 entry files; compacting to 83 lines
cut the injected store 45%. Cross-file duplication in `.agents/*` looked large by
mention count but was worth only ~3 KB in bytes — those docs are big because they
carry unique operational detail, not because they repeat each other.

## `AGENTS.md` is NOT loaded on this host — don't treat it as a cheaper shelf

**Proven 2026-08-10 by a zero-tool-call sub-agent probe.** Positive controls
(`CLAUDE.md` § Layout, `.agents/testing.md` § Locator policy) came back YES;
`AGENTS.md`'s top heading and its unique sections (Repository Structure / Build & Run
/ CI/CD) came back **NOT IN CONTEXT**. Structurally confirmed: no `@`-import, no hook
(`lib.sh:134` — *"the full AGENTS.md manual is NOT injected"*), no setting.

`AGENTS.md` exists for **humans browsing the repo and for hosts that auto-load it**
(Codex / Cursor / Copilot). On Claude Code it costs zero tokens and delivers zero
context.

⚠️ **Consequence:** the bundle block *"Test Automation Team — shared conventions"*
(8,326 B) is duplicated verbatim in `CLAUDE.md` and `AGENTS.md`, and it is tempting to
"move the prose to AGENTS.md" for a −6.8 KB/unit win. **That is deletion with extra
steps** — agents on this host would simply stop receiving it, including the standing
Workflow opt-in the lead depends on. The duplication is deliberate cross-host design,
not waste. Bundle-owned too, so `init --update` may revert any edit.

**Standing rule: "it's duplicated, so one copy is free to delete" is only true once
you have PROVEN which copy is actually loaded.** The zero-tool-call probe above is the
cheap way to prove it — reuse it before proposing any context cut.
