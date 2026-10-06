---
name: Never edit the shared .env.test to retarget a run
description: automation/.env.test is a symlink to the one master file every concurrent session reads — editing it even briefly races them. DEV is already the default target, so a DEV-only failure needs no retarget at all.
type: feedback
---

## The trap

A `[Fix]`/`[Adjust]` task citing a DEV-only CI failure tempts you to "point the
local suite at DEV" to reproduce it. `config.py` orders dotenv first, so
`.env.test` beats shell env vars — meaning the only way to retarget is editing
`automation/.env.test`, which is a **symlink to the one master `.env.test` in the
parent workspace folder**, shared by every agent and every session operating in
this clone (no worktrees, no per-agent copies). Editing it even briefly, even
with a restore-after plan, races any other session whose pytest run reads it
mid-window — a real, silent-failure-mode hazard, not a theoretical one (this
workspace routinely runs concurrent qa-engineer / test-automation-engineer /
test-automation-lead sessions, evidenced by same-day merge conflicts in their
daily memory logs).

## The fix — there is nothing to retarget

**DEV as deployed is already the target** (`ELITEA_URL=https://dev.elitea.ai`,
`APP_PREFIX=/app`), for the implementer's green run, for your merge gate, and for
Playwright MCP exploration. A "DEV-only" failure reproduces on the default
configuration. So:

1. Reproduce it with the suite exactly as configured — no env edits.
2. For interactive diagnosis, use Playwright MCP against `https://dev.elitea.ai/app`
   (refresh `scripts/dev_storage_state.py` first) — browser-only, no pytest, no
   shared-file risk.
3. Gate there too: `cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v
   -p no:cacheprovider`, ×3 separate invocations.

If a task ever seems to need a different base URL, that is a question for the
operator, not a file edit.

## Worked case

#1898 (ELITEA-1140, `test_toolkit_test_settings` DEV timeout, 2026-08-28):
diagnosed the route drift live via Playwright MCP against `dev.elitea.ai`
directly (browser-only, no pytest, no shared-file risk), then wrote the fix and
ran the pytest gate 3/3 green — zero `.env.test` edits, zero risk to concurrent
sessions. (The original note reached the same conclusion by a now-retired route;
the rule it protects — never touch the shared symlink — is unchanged.)
