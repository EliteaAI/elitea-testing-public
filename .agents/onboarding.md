# Onboarding record — 2026-07-10 (scout / Kit)

## What was found

- **Repo:** `EliteaAI/elitea-testing-public`, working branch `automation/base` (new,
  no PR history; `main` has 15 merged PRs sampled for conventions).
- **Framework (verified live):** Playwright 1.61.0 + pytest 9.1.1, Python 3.13.13
  repo-local `.venv`. 25 test files (`tests/ui/<feature>/`, `tests/api/`, `tests/unit/`),
  22 page objects, testid-only `LocatorDescriptor` (fallback confirmed dead code).
  Coding rules auto-applied from `.claude/rules/` (5 files).
- **TMS:** onetest — MCP server `onetest-tms` in `.mcp.json`; cases as markdown+YAML
  in `EliteaAI/onetest-ai-tm-Elitea/tests/automated-full-regression-ui/`
  (sampled `ELITEA-1739` to verify frontmatter schema).
- **Tracker:** GitHub Issues + Projects board #9 (owner EliteaAI); status machine with
  human-only `Approved`; `question`/`bug` labels load-bearing.
- **Topology (verified):** three siblings — this repo, `../EliteaUI` fork
  (`automation/testids`, upstream `EliteaAI/EliteaUI` read-only, full clone),
  `../onetest-ai-tm-Elitea` (`.onetest/` present). Symlinks intact
  (`automation/.env.test`, `EliteaUI/.env`).
- **Skills:** all 7 upstream-main skills already present on `automation/base` plus the
  22-skill SDLC bundle. Additionally **copied 4 Elitea domain-knowledge skills from
  `bermudas/EliteaSkills`** (operator request): `elitea-platform` (REST API reference),
  `elitea-pipeline`, `elitea-toolkit`, `elitea-testing` — 33 skills total. Secret-scanned
  clean (placeholders only), no name collisions.
- **CLAUDE.md drift:** old file referenced `~/Development/venv` (Python 3.12),
  nonexistent paths, `stage.elitea.ai` as target, flat test layout, stale pins
  (pytest 9.0.2 / playwright 1.58.0 vs actual 9.1.1 / 1.61.0) → rewritten.

## What was generated / modified

| File | Action |
|---|---|
| `CLAUDE.md` | rewritten (operator-approved) — local-loop way of work |
| `AGENTS.md` | project sections added; `BUNDLE:test-automation` block preserved verbatim |
| `.agents/profile.md` | created — systems map, board discipline, PR policy, credential key names |
| `.agents/workflow.md` | created — two-branch dance, per-test loop, batch ops (human-triggered) |
| `.agents/testing.md` | created — framework, run commands, testid-only locator policy, AFS location |
| `.agents/conventions.md` | created — pointers to `.claude/rules/*` + detected patterns |
| `.agents/architecture.md` | created — three-repo topology, app surfaces, why-the-fork |
| `.agents/team-comms.md` | created — Claude Code roster + dispatch syntax |
| `.agents/test-automation.yaml` | created — onetest adapter (MCP), intake + back-write policy |
| `.agents/memory/{test-automation-lead,qa-engineer,test-automation-engineer,scout}/project_briefing.md` | adjusted — project-specific sections added; generic overlay kept |

Roles tuned: none (default personas fit a Playwright/pytest engagement exactly).
Steps skipped: 6.8 tool-wiring (Claude Code host), 6.9 role-overrides (all slots
have dedicated agents), Step 7 persona rewrite (defaults fit).

## Late additions (same session)

- **Conventions added on operator input:** (1) locators live ONLY as page-object
  class fields (never inside methods/specs), `LocatorDescriptor` strictly without
  `fallback`; (2) every test step wrapped in `with allure.step(...)` so steps reach
  reports. Captured in `testing.md`, `conventions.md`, `CLAUDE.md`, role briefings.
- **`.claude/rules/page-objects.md` corrected** — its "testid + fallback" section
  recommended populating `fallback` (dead code, now forbidden); rewritten to
  testid-only + class-fields-only with updated examples.
- **4 Elitea knowledge skills copied** from `bermudas/EliteaSkills` (see above).

## Operator decisions on record

- No `env.sh` — docs use repo-relative paths (`../EliteaUI`, `../onetest-ai-tm-Elitea`).
- No onboarding GitHub issue — this file is the audit trail.
- Memory briefings adjusted, not replaced.
- Seed leaves room for expansion beyond UI (test-type recorded as `mixed`, ui primary).

## Late additions (round 2 — board/identity review)

- **Identity rule seeded (portable):** the shared `GITHUB_TOKEN` env var (shared
  token, no `project` scope) overrides the keyring login. All tracker/board writes
  MUST be prefixed `env -u GITHUB_TOKEN` so they run as **the operator's own
  keyring account** — whoever runs the agents on whatever machine, never the shared
  token, never a hardcoded person. Per-machine setup: `gh auth login` once with
  your own account (`repo`, `project`, `read:org` scopes). On this machine the
  keyring account was switched to the operator's own. Captured in `profile.md`,
  `workflow.md`, `test-automation.yaml`, Tal's briefing, `CLAUDE.md`.
- **Dedup rule hardened:** intake dedup now uses the real-time list API instead of
  `--search` (search-index lag caused duplicate filings #17/#18; #17 closed).
- **Board auto-add:** operator configured the project workflow themselves — the
  yaml's `board_placement: auto-add` policy stands.

## Open items

1. ~~`gh` token lacks `project` scope~~ — superseded by the identity rule above:
   board ops run via `env -u GITHUB_TOKEN` (keyring account has the scope).
2. No known-flaky-test list yet — `.agents/testing.md` § Known issues collects them.
3. `automation/base` has no PR history — `.agents/workflow.md` § Unconfirmed notes the
   review-approval count; refresh after ~10 PRs land.
4. API-test conventions are thinner than UI — follow `.claude/rules/api-tests.md`,
   flag gaps to the lead.

## First recommended task

Run an intake tick: launch Tal (`claude --agent test-automation-lead`) and ask him to
intake from `tests/automated-full-regression-ui/` per `.agents/test-automation.yaml`
§ intake (≤10 cards, dedup, no status). A human then drags approved cards to
`Approved`, and the pipeline can start on the first case.

---

## Revision — 2026-07-13: EliteaUI fork retired

The topology recorded above is **superseded**. The `bermudas/EliteaUI` fork was
dropped; `automation/testids` now lives on **`EliteaAI/EliteaUI` directly** (we have
push, not admin) as a permanent **integration branch** accumulating every testid —
merged and still-in-review alike.

Testids are now **dual-targeted per case**, not batched: a `testids/<case>-<slug>`
branch is cut from fresh `origin/main`, merged immediately into `automation/testids`
(no review — unblocks agents), and opened as a **draft PR to `main`** for the UI team.
Cutting from `main` rather than the integration branch is what keeps that PR to a clean
single-case diff. Agents may now open those PRs (as drafts) — the old blanket ban on
PRing `EliteaAI/EliteaUI` is repealed.

`automation/testids` is a shared org branch: **merge `origin/main` into it; never
rebase, never force-push.**

The **test** side is deliberately unchanged (branch off `automation/base`, reviewed PR,
periodic batch promote) — testids are leaf additions that don't compose, whereas test
code is a layered shared substrate, and per-case review already happens on the
`automation/base` PR.

Migration performed: fork demoted to a `fork` remote; `automation/testids` rebuilt on
fresh `main` + the 3 pending testids; catch-up draft PR EliteaAI/EliteaUI#525 opened.
Docs/skills rewritten accordingly. See `.agents/workflow.md`.
