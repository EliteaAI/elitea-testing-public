# ui-testid-coverage — reference

## Testid forms (the extraction catalog)

A testid is not always `data-testid="x"`. Missing these forms is the #1 cause of
false "not covered" results. All six occur in real React code:

| # | Form | Example | Notes |
|---|---|---|---|
| 1 | JSX attribute, literal | `data-testid="agent-name-input"` | the obvious one |
| 2 | Object property | `{ 'data-testid': 'agent-name-input' }` | inside `inputProps`/`slotProps` — uses `:` not `=` |
| 3 | Prop-wired | `titleTestId="x"`, `testId="x"`, `toggleTestId="x"` | the optional-testId-prop convention; value at the *call site*, not the leaf |
| 4 | Template literal | `` data-testid={`tags-panel-chip-${name}`} `` | dynamic; base pattern only |
| 5 | Multi-line conditional | `data-testid={\n cond ? 'a' : 'b'\n}` | **line-based grep misses this** — two different testids by state |
| 6 | Helper-computed | `const t = \`version-option-${n}\`` then `data-testid={t}` | value computed away from the attribute |

**Match-all regex family** (what the script uses):
- literal/object: `[Tt]est[Ii]d['"]?\s*[=:]\s*(['"])([^'"]+)\1`
- braced expr (multiline, `re.DOTALL`): `[Tt]est[Ii]d['"]?\s*[=:]\s*\{(.*?)\}` → pull all `'…'`/`"…"`/`` `…` `` inside
- object-form ternary (no braces): `[Tt]est[Ii]d['"]?\s*:\s*[^,}\n]*\?[^,}\n]*` → pull literals

**Automation side** (Python page objects/tests): `testid\s*=\s*f?(['"])([^'"]+)\1`
covers `LocatorDescriptor(testid="x")` and f-string templates `testid=f"x-{v}"`.

**Normalization:** collapse dynamics so both sides compare — `${…}` → `*` **first**, then
`{…}` → `*` (order matters, or `${k}` becomes `$*`). Keep only kebab tokens
(`^[a-z0-9]+(-[a-z0-9*]+)+$`) to drop noise strings (labels, classNames).

## The two coverage directions

- **used ∩ present** — binding health: automation locators that resolve to a real testid.
- **used − present** — no-backing: referenced but absent (classify — see SKILL.md table).
- **present − used** — orphans: instrumented UI the suite ignores.

## Dead page-object fields & skip-masking (two silent-failure patterns)

- **Dead field**: a `LocatorDescriptor` class field that no page-object method *and* no
  test references via `.field`. Never resolved ⇒ never fails ⇒ passes review + green gate.
  Detect: field defined (`name = LocatorDescriptor(`) but `\.name\b` appears nowhere in
  `pages/` + `tests/`. These accumulate when page objects are generated broader than the
  test needs.
- **Skip-masking**: a `pytest.skip` inside a `try/except` around a `wait_for` turns a
  *missing* element into a green **skip**, not a failure — so a broken/absent testid hides
  behind a passing run. Grep tests for `try:` … `wait_for` … `except …: pytest.skip`.
  Legitimate for truly-optional elements; a trap when the testid simply doesn't exist.

## Segmentation (`classify()` in the script)

Path → `(class, area)`. Defaults tuned for Elitea; edit for another app:
- `PRESENTATIONAL` — `Icons/`, `*Icon.jsx` → exclude from denominator.
- `ADMIN` — `/admin/*` platform console → **separate app**, track separately, never fold in.
- `FEATURE` — user-facing flows: agents, skills, chat, toolkits/mcp, credentials, pipelines,
  artifacts, notifications, onboarding, **settings** (per-user secrets/tokens/ai-providers
  are user-facing config, *not* admin).
- `SHARED-UI` — design-system primitives (`ComponentsLib`, `/shared/`, `/components/`):
  covered *indirectly*; don't put in the headline denominator alone.
- `OTHER` — layout/infra.

Interactive = tag in a known interactive set (`Button`, `TextField`, `MenuItem`, `input`, …)
OR carries an `on[A-Z]…=` handler. Undercounts custom wrappers (`<PrimaryButton>` with a
prop-passed handler) — so absolute %s are order-of-magnitude; relative ranking is solid.

Denominators also reported for context: component files, component defs, `<Route>`/`path:`
entries (flows), and `?`/`&&`-JSX conditional branches (UI complexity).

## Runtime — the real flow/branch coverage (what testids can't give)

testids prove a control is *reachable*, not which branch *ran*. For execution coverage,
collect JS coverage during the Playwright run:

- **Playwright V8/CDP** — `await page.coverage.startJSCoverage()` before, `stopJSCoverage()`
  after each test; merge the ranges; map to source via sourcemaps (`v8-to-istanbul`).
- **Istanbul-instrumented build** — build the dev bundle with `vite-plugin-istanbul` /
  `babel-plugin-istanbul`, read `window.__coverage__` after each test, merge with `nyc`.

Report statement/branch/function coverage per file/component against the branch/route
denominators this skill already prints. That is the definitive flow-coverage number;
this skill is the breadth half of the same dashboard.

## Gotchas

- Point `--ui` at the **superset** branch (every testid ever added), or you'll over-report
  gaps for testids merged elsewhere. For Elitea: EliteaUI on `automation/testids`; `git
  fetch` first — a stale clone invents phantom gaps.
- `login-button` and other Keycloak/external handles are legitimately absent from the UI
  repo — the script's `EXTERNAL` set whitelists known ones; extend it per project.
- Re-run after any locator/page-object change; commit the report next to the code or under
  `docs/` so the series is diffable over time.
