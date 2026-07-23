# elitea-testing — Elitea AI Platform Test Automation

Playwright + pytest automation for [Elitea](https://elitea.ai), an AI collaboration
platform. Working branch: **`automation/base`** (never PR `main` directly).

## Layout (three sibling clones — parent dir is NOT a git repo)

```
<parent>/                        ← this repo's parent folder (sibling clones; no env var needed)
├── .env  .env.test              master secrets — NEVER commit, NEVER print
├── elitea-testing-public/       THIS repo · branch automation/base · .venv (Python 3.13)
├── EliteaUI/                    EliteaAI/EliteaUI (NO fork) · branch automation/testids · npm run dev → :5173
└── onetest-ai-tm-Elitea/        TMS repo (test cases as markdown + GitHub issues)
```

## Essential Commands

```bash
# Install (repo-local venv; system python3 may be too old — need 3.11+)
.venv/bin/pip install -e ".[reporting]"     # reporting extra is MANDATORY (allure in addopts)

# Run tests (always from automation/)
cd automation
../.venv/bin/pytest tests/ui/smoke/test_ui_smoke.py -v          # one file
HEADLESS=true ../.venv/bin/pytest -m smoke -v                   # smoke suite
# Headed is the default (config.py: headless=False). HEADLESS=true for quiet runs.

# Start local UI under test (or use the start-ui-localhost skill)
cd ../EliteaUI && npm run dev                                    # → http://localhost:5173
```

## Critical Conventions

- **Primary test target is `http://localhost:5173`** — `EliteaAI/EliteaUI` on
  `automation/testids` (points at the DEV backend). Deployed envs (dev/next.elitea.ai)
  are CI's job, not the local loop's.
- **Test PRs target `automation/base`**, never `main`.
- **Testids: dual-target.** `automation/testids` is a permanent **integration branch
  on `EliteaAI/EliteaUI`** (no fork) holding every testid — merged *and* still in
  review; the dev server always serves them ALL. Commit testids **straight onto
  `automation/testids`** (HMR live), then cherry-pick them onto `testids/<case>-<slug>`
  cut from **fresh `origin/main`** (in a worktree) and open a **draft PR to `main`**
  for the UI team. The PR branch is built on `main` — never on the integration
  branch — which is what keeps its diff a clean single case.
- **Never rebase or force-push `automation/testids`** — it's a shared org branch.
  Sync it with `git merge origin/main`. If review changes a testid, resolve the next
  merge **in favour of `main`**.
- **Locators are testid-only — there is NO fallback ladder**: missing testid ⇒ add it
  via `add-data-testid` (team measures UI coverage by testid presence).
  `LocatorDescriptor(testid="agent-form-save-button")`; `fallback`/`locator` params are
  forbidden. Naming: `{section}-{element}-{type}`. Locators live **only as page-object
  class fields** — never inside methods or specs. Overrides: `.agents/role-overrides.md`.
- **Test steps wrapped in `with allure.step("Step N — …"):`** so they reach reports.
- **`.env.test` beats shell env vars** (`config.py` orders dotenv first). Edit the file,
  don't export.
- `APP_PREFIX` is empty on localhost, `/app` on deployed envs.
- Keycloak login field is `input[name="username"]`, NOT email. On localhost,
  `auth_state` skips login entirely (uses `VITE_DEV_TOKEN`).
- AI responses arrive over WebSocket with ~2s delay — use waits, never sleeps.
- Never commit or print `.env` / `.env.test` contents.
- **Tracker writes: prefix `env -u GITHUB_TOKEN gh …`** — the shared env token is the
  wrong identity and lacks `project` scope; the keyring account is correct.
- Coding rules auto-applied from `.claude/rules/` (page-objects, ui-tests,
  api-patterns, mui-patterns, api-tests).

## Key Paths

- Tests: `automation/tests/{ui,api,unit}/` — grouped by feature
- Page objects: `automation/pages/` (testid-only `LocatorDescriptor`)
- Config: `automation/config.py` + `automation/.env.test` (symlink to `../../.env.test`)
- Markers: `automation/pytest.ini` (p0–p3, smoke, regression, per-feature)

## Team & Way of Work

Seeded config in `.agents/`, imported below so every session and every dispatched
subagent gets it in full (uncapped — see `.claude/hooks/sdlc-skills/config.sh` for
why this replaced the hook's inline delivery): system design (`architecture.md`),
coding standards (`conventions.md`), systems/PR policy/credentials map
(`profile.md`), per-role locator/testid overrides (`role-overrides.md`), roster
(`team-comms.md`), TMS intake/back-write policy (`test-automation.yaml`),
framework detail (`testing.md`), the two-branch dance (`workflow.md`).

@.agents/architecture.md
@.agents/conventions.md
@.agents/profile.md
@.agents/role-overrides.md
@.agents/team-comms.md
@.agents/test-automation.yaml
@.agents/testing.md
@.agents/workflow.md

## Full Reference

See `AGENTS.md` for stack, structure, and team agreements.
