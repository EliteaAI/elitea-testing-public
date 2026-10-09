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
  file. No raw selectors in spec files. **Locators are class-level `LocatorDescriptor` /
  `ScopedLocator` fields on the ladder (2026-10), never constructed inside method
  bodies; every non-testid one carries `suggested_testid=`** (validated at import).
- **Step reporting:** test steps wrapped in `with allure.step("Step N — …"):` so they
  surface in Allure reports (see `.agents/testing.md` § Step reporting).
- **TMS traceability:** a case-derived test carries `@pytest.mark.tms("ELITEA-<id>")`
  (several ids, or per-`pytest.param`, when one test covers several cases) — see
  `.agents/testing.md` § TMS case marker. Tests with no backing TMS case (framework
  unit tests, helper/smoke tests) carry no `tms` marker.
- **Config:** everything through `from config import settings` (pydantic-settings);
  no `os.environ` reads scattered in tests; `.env.test` is authoritative over shell env.
- **Lint:** ruff — `E,F,I,W,UP`, line length 120, target py311. Run
  `../.venv/bin/ruff check .` before PR.
- **Types:** mypy configured (`warn_return_any`, `warn_unused_configs`).
- **Imports:** stdlib → third-party → local (ruff `I` enforces).
- **Page navigation:** page objects call `navigate("/skills/all")` with bare paths;
  `settings.app_base_url` injects the `APP_PREFIX` correctly per environment.

## Git

- Work branches from `automation/factory`: `tests/<case-id>-<slug>` (canonical; older
  `automation/<case-id>-<slug>` branches exist historically — don't create new ones)
- Commits: conventional-ish — `test: (5199) …`, `fix: …`, `refactor: …`, `docs(afs): …`
- PRs: small, one per test/feature area, target `automation/factory`, squash merge
- Every artifact a case produces lands in **this** repo — one branch, one PR, one repo

## Hard don'ts

- Never populate `LocatorDescriptor(fallback=…)` — dead code, strictly forbidden
- Never build locators inside methods or spec files — class fields only
- Never ship a test whose steps aren't wrapped in `allure.step`
- Never ship a case-derived test without its `@pytest.mark.tms("ELITEA-<id>")`
- Never commit/print `.env` / `.env.test`
- Never edit the frontend source — it is a read-only reference, not a work surface
- No `sleep`/`waitForTimeout` — framework waits only
- No defect masking (`pytest.skip`, weakened asserts) — see AGENTS.md bundle block
