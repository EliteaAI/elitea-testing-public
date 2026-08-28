---
name: DEV repro — use localhost, never edit the shared .env.test
description: Reproducing a dev.elitea.ai-only CI failure doesn't require editing the shared .env.test — localhost:5173 already serves automation/testids against the same DEV backend.
type: feedback
---

## The trap

A `[Fix]`/`[Adjust]` task citing a DEV-only GHA failure tempts you to point
the local suite AT dev.elitea.ai to reproduce it. `config.py`'s `.env.test`
wins over shell env vars, so the only way to do that is editing
`automation/.env.test` — which is a **symlink to the one master `.env.test`
in the parent workspace folder**, shared by every agent and every session
operating in this same clone (no worktrees, no per-agent copies). Editing it
even briefly, even with a restore-after plan, races any other agent whose
pytest session reads it mid-window — a real, silent-failure-mode hazard, not
a theoretical one (this workspace runs concurrent qa-engineer /
test-automation-engineer / test-automation-lead sessions routinely, evidenced
by same-day merge conflicts in their daily memory logs).

## The fix — check this FIRST

`.env.test`'s own comment plus `profile.md` § Environment & access both say
it: **`http://localhost:5173` (`EliteaAI/EliteaUI` on `automation/testids`)
already points at the DEV backend** (`ELITEA_API_BASE=https://dev.elitea.ai/api/v2`).
It is not an isolated sandbox — it is the same data plane, same auth, same
product code (the `automation/testids` integration branch carries everything
on `main` plus whatever's still in review) as `dev.elitea.ai` itself. So:

1. Confirm the dev server is up (`curl -s -o /dev/null -w '%{http_code}' http://localhost:5173`,
   or `start-ui-localhost`).
2. Confirm the UI element/route/testid you're chasing exists on
   `origin/automation/testids` (or `origin/main`) via `git grep` — if it does,
   localhost already serves it.
3. Reproduce and gate there. Zero edits to the shared `.env.test`.

Only reach for an actual `dev.elitea.ai` target (Playwright MCP live browsing,
or a genuinely temporary `.env.test` edit) when the failure is specific to the
DEEPLOYED env itself — e.g. verifying a testid's promotion state, or a
Keycloak-login-path issue localhost's `auth_state` bypass can't surface.

## Worked case

#1898 (ELITEA-1140, `test_toolkit_test_settings` DEV timeout, 2026-08-28):
diagnosed the route drift live via Playwright MCP against `dev.elitea.ai`
directly (browser-only, no pytest, no shared-file risk), then wrote the fix
and ran the actual pytest gate (3/3 green) against `localhost:5173` — same
DEV backend, same fixed UI code, zero `.env.test` edits, zero risk to
concurrent sessions.
