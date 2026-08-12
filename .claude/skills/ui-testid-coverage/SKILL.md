---
name: ui-testid-coverage
description: Measure UI test-automation coverage via data-testids — inventory the testids a React/JSX UI renders, cross-reference them against the testids a Playwright/pytest automation repo references, and emit a segmented coverage report (binding health, orphans, dead page-object fields, per-area interactive-element coverage). Use when asked about UI test coverage, testid coverage, "what % of the UI is automated", which flows/components are tested, finding/locating testids, orphan or broken/dead locators, or comparing the UI repo against the test repo.
---

# UI testid coverage

Cross-references two repos — a **UI** (`data-testid`s in JSX) and an **automation** repo
(`LocatorDescriptor(testid=...)` in page objects/tests) — to answer *what does automation
actually cover*. Static analysis ⇒ measures interaction **breadth**, not flow/branch
execution (that needs runtime JS coverage — see REFERENCE.md § Runtime).

## Quick start

```bash
python3 {skill}/scripts/testid_coverage.py \
  --ui ../EliteaUI/src ../elitea_assistant/src --auto automation \
  --out ../docs/ui-testid-coverage-$(date +%F).md   # omit --out to print
```

Point `--ui` at the UI source root(s) — the branch(es) that are the **superset** of testids. For
Elitea that is EliteaUI on `automation/testids` **plus any connected first-party repos** whose
components render in the app (e.g. `../elitea_assistant/src`, the Support Assistant — see
`.agents/workflow.md` § Connected repos); pass several dirs to `--ui`. `--auto` is the automation
repo root (must contain `pages/` and `tests/`). Reads `REPORT_DATE` env to stamp a fixed date.

## What it reports

- **Binding health** — % of automation-referenced testids that exist in the UI.
- **No-backing set** — referenced but absent from UI; classify before trusting (below).
- **Orphans** — UI testids no test references.
- **Dead page-object fields** — `LocatorDescriptor` fields no page-object method *or* test
  uses; inert, but cruft that can mask missing testids.
- **Segmented interactive coverage** — % of interactive elements exercised, by *class*
  (FEATURE / SHARED-UI / OTHER / PRESENTATIONAL / ADMIN) and by *area* (agents, skills,
  chat, …). This is the honest "user-facing coverage" number, per area.

## Reading the results — do not trust raw counts

A naive "referenced but not in UI" count massively over-reports gaps. Every no-backing
entry is one of four things — **classify each**:

| Bucket | Tell | Real gap? |
|---|---|---|
| dynamic template | UI renders `` `x-${k}` ``, test uses concrete `x-foo` | no — covered at runtime |
| external page | e.g. `login-button` (Keycloak, not this repo) | no — out of scope |
| dead page-object field | field no test/method references | no — inert |
| genuine | none of the above | **yes** — broken locator; confirm live |

The **matched %** and **per-area coverage** are trustworthy; absolute breadth %s are
order-of-magnitude (the interactive denominator undercounts custom-wrapper controls).

## Finding testids (the part that trips people up)

testids hide in **six** syntactic forms — a `grep 'data-testid="'` misses most. The script
handles all six; if you extract by hand, cover them all. See
[REFERENCE.md](REFERENCE.md) § Testid forms for the catalog and regexes.

## Segmentation & admin

Icons (presentational) and hooks/layout (infra) are excluded from the meaningful
denominator; shared-UI primitives are counted but are covered *indirectly*. **Per-user
settings** (secrets/tokens/ai-providers) are **user-facing**, not admin. A true
platform/instance **admin console** (an `/admin/*` app) is usually a *separate repo* —
track it separately, never fold it into feature coverage. Tune `classify()` in the script
for a different app's areas.

## Extending to true flow/branch coverage

testids give breadth only. For which of the (reported) branches/routes actually execute,
add a runtime pass — Playwright `page.coverage` (V8/CDP) or an Istanbul-instrumented dev
build dumped per test. REFERENCE.md § Runtime sketches the harness.
