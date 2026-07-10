# Coding Conventions

Descriptive (what IS), detected 2026-07-10.

## Authoritative rule files (auto-applied — read them, they win)

The repo ships enforced coding rules in `.claude/rules/`, referenced from
`automation/CLAUDE.md`:

| File | Governs |
|---|---|
| `.claude/rules/page-objects.md` | Page-object structure, `LocatorDescriptor` usage |
| `.claude/rules/ui-tests.md` | UI test style, waits, assertions |
| `.claude/rules/api-patterns.md` | API client patterns |
| `.claude/rules/api-tests.md` | API test style |
| `.claude/rules/mui-patterns.md` | Interacting with MUI components |

This file only records what those don't.

## Detected patterns

- **Naming:** `snake_case` files/functions, `PascalCase` classes (`TestAgentConfiguration`),
  test files `test_*.py`, page objects `<surface>_page.py`.
- **Selectors:** live in page objects ONLY — one `data-testid` appears in exactly one
  file. No raw selectors in spec files. **Locators are class-level `LocatorDescriptor`
  fields, never constructed inside method bodies.**
- **Step reporting:** test steps wrapped in `with allure.step("Step N — …"):` so they
  surface in Allure reports (see `.agents/testing.md` § Step reporting).
- **Config:** everything through `from config import settings` (pydantic-settings);
  no `os.environ` reads scattered in tests; `.env.test` is authoritative over shell env.
- **Lint:** ruff — `E,F,I,W,UP`, line length 120, target py311. Run
  `../.venv/bin/ruff check .` before PR.
- **Types:** mypy configured (`warn_return_any`, `warn_unused_configs`).
- **Imports:** stdlib → third-party → local (ruff `I` enforces).
- **Page navigation:** page objects call `navigate("/skills/all")` with bare paths;
  `settings.app_base_url` injects the `APP_PREFIX` correctly per environment.

## Git

- Work branches from `automation/base`: `automation/<case-id>-<slug>` / `tests/<id>-<slug>`
- Commits: conventional-ish — `test: (5199) …`, `fix: …`, `refactor: …`, `docs(afs): …`
- PRs: small, one per test/feature area, target `automation/base`, squash merge
- Testid commits in the UI fork: direct to `automation/testids`, message describing
  the testids added

## Hard don'ts

- Never populate `LocatorDescriptor(fallback=…)` — dead code, strictly forbidden
- Never build locators inside methods or spec files — class fields only
- Never ship a test whose steps aren't wrapped in `allure.step`
- Never commit/print `.env` / `.env.test`
- Never edit anything outside `src/` in the EliteaUI repo
- No `sleep`/`waitForTimeout` — framework waits only
- No defect masking (`pytest.skip`, weakened asserts) — see AGENTS.md bundle block
