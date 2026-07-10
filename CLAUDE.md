# elitea-testing — Elitea AI Platform Test Automation

Playwright + pytest automation for [Elitea](https://elitea.ai), an AI collaboration
platform. Working branch: **`automation/base`** (never PR `main` directly).

## Layout (three sibling clones — parent dir is NOT a git repo)

```
<parent>/                        ← "$LOCAL_ELITEA_FOLDER" — this repo's parent folder
├── .env  .env.test              master secrets — NEVER commit, NEVER print
├── elitea-testing-public/       THIS repo · branch automation/base · .venv (Python 3.13)
├── EliteaUI/                    UI fork · branch automation/testids · npm run dev → :5173
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

- **Primary test target is `http://localhost:5173`** — the EliteaUI fork on
  `automation/testids` (points at the DEV backend). Deployed envs (dev/next.elitea.ai)
  are CI's job, not the local loop's.
- **PRs target `automation/base`**, never `main`. Testid edits commit to EliteaUI
  `automation/testids` — never open a PR to `EliteaAI/EliteaUI` yourself.
- **Locators are testid-only**: `LocatorDescriptor(testid="agent-form-save-button")`.
  `fallback` is dead code — never populate it. Naming: `{section}-{element}-{type}`.
  Locators live **only as page-object class fields** — never inside methods or specs.
- **Test steps wrapped in `with allure.step("Step N — …"):`** so they reach reports.
- **`.env.test` beats shell env vars** (`config.py` orders dotenv first). Edit the file,
  don't export.
- `APP_PREFIX` is empty on localhost, `/app` on deployed envs.
- Keycloak login field is `input[name="username"]`, NOT email. On localhost,
  `auth_state` skips login entirely (uses `VITE_DEV_TOKEN`).
- AI responses arrive over WebSocket with ~2s delay — use waits, never sleeps.
- Never commit or print `.env` / `.env.test` contents.
- Coding rules auto-applied from `.claude/rules/` (page-objects, ui-tests,
  api-patterns, mui-patterns, api-tests).

## Key Paths

- Tests: `automation/tests/{ui,api,unit}/` — grouped by feature
- Page objects: `automation/pages/` (testid-only `LocatorDescriptor`)
- Config: `automation/config.py` + `automation/.env.test` (symlink to `../../.env.test`)
- Markers: `automation/pytest.ini` (p0–p3, smoke, regression, per-feature)

## Team & Way of Work

Seeded config in `.agents/`: `profile.md` (systems, PR policy, credentials map),
`workflow.md` (the two-branch dance), `testing.md` (framework detail),
`test-automation.yaml` (TMS intake/back-write policy), `team-comms.md` (roster).

## Full Reference

See `AGENTS.md` for stack, structure, and team agreements.
