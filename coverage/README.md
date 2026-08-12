# Runtime coverage — how to measure what the UI tests actually execute

Measures which EliteaUI code (statements/branches/functions, per file, per feature
area) really runs in the browser while the Playwright tests drive it.
No EliteaUI changes, no test changes — one env switch.

## The idea in 30 seconds

Chrome has a built-in counter. It knows exactly which lines of the app's code
executed. We just turn it on.

1. Run tests like always, but add one word: `COVERAGE=1 pytest ...`
2. `node coverage/report.mjs` → translates Chrome's counters back to our `.jsx` files
3. `python coverage/area_rollup.py --branches` → one table: coverage % per feature area

**Who does what:** Chrome itself does the counting (via CDP, its debug port). One
fixture in `conftest.py` flips it on and saves the counts. One Node lib (monocart)
translates. One tiny Python script makes the table. Zero changes to the app, zero
changes to tests. Off switch: don't type `COVERAGE=1` — nothing persists.

## Why monocart — Chrome answers in the wrong language

What Chrome hands us per file is raw byte ranges:

```json
{ "url": ".../src/[fsd]/features/agent/ui/AgentCard.jsx",
  "functions": [ { "ranges": [ { "startOffset": 313, "endOffset": 890, "count": 0 } ] } ] }
```

"Bytes 313–890 never ran." Bytes of *what*, though? Not your `.jsx` — Vite
transforms every file before serving (JSX → plain JS, HMR wiring injected), and
the offsets point into that transformed text nobody ever reads. What we want is:
"in `AgentCard.jsx`, the `if` branch on line 42 never executed."

Monocart does the four translation steps between those two:

1. **Offsets → lines** — reads the sourcemap embedded in each served file, maps
   byte ranges back to line/column in the original `.jsx`
2. **Ranges → statements/branches/functions** — V8 only says "this byte span ran
   N times"; monocart converts that into the classic coverage model
3. **Merge** — unions all per-test fragments into one dataset, no double-counting
4. **Render** — HTML report, `coverage-summary.json` (the rollup reads it), console table

Skipping it would mean hand-gluing `v8-to-istanbul` + sourcemap decoding + AST
branch analysis + istanbul reporters — several fragile pieces vs one dependency.
Chrome counts, Python captures, **monocart translates**, Python summarizes.

## Prerequisites (once)

1. EliteaUI dev server running: `cd ../EliteaUI && npm run dev` → http://localhost:5173
   (or use the `start-ui-localhost` skill)
2. `ELITEA_URL=http://localhost:5173` in `automation/.env.test` (normally already there)
3. One-time tool install: `cd coverage && npm install`

## Measure

```bash
# 0. BEFORE a long run — check prereqs and the area map (cheap; saves hours):
node coverage/campaign.mjs preflight --tests 400   # dev server, esbuild, monocart, disk
node coverage/campaign.mjs lint-areas              # areas.json still matches the src tree?
node coverage/campaign.mjs archive <prev-label> --wipe   # snapshot the OLD report, clean slate

# 1. Run ANY pytest selection with the switch on (from automation/):
cd automation
HEADLESS=true COVERAGE=1 ../.venv/bin/pytest tests/ui/agents/   # or any file/marker/node-id

# 2. Translate browser counts -> per-file coverage (from repo root):
node coverage/report.mjs

# 3. Roll up into the per-area table:
.venv/bin/python coverage/area_rollup.py             # statements view
.venv/bin/python coverage/area_rollup.py --branches  # branch view  <- THE honest number
.venv/bin/python coverage/area_rollup.py --files chat  # per-file detail for one area

# 4. Compare against a previous campaign (NOT by eyeballing two tables — see Gotcha 2):
node coverage/campaign.mjs compare ../coverage-archive/2026-07-24-baseline
```

Line-by-line HTML: `open coverage/report/index.html`

### `campaign.mjs` — the lifecycle helpers

| Command | What it prevents |
|---|---|
| `preflight [--tests N]` | Starting a 4-hour run that dies on a missing dev server / esbuild / disk. |
| `lint-areas` | A moved feature silently re-bucketing into another area (Gotcha 2). |
| `archive <label> [--wipe]` | Wiping the old report with nothing to compare against later. |
| `compare <baseline>` | Diffing two tables built with *different* area maps (Gotcha 2). |

Archives land in `../coverage-archive/<label>/` — **outside the repo on purpose**:
`coverage/report/` and `coverage/.v8/` are gitignored, but an in-repo archive dir
would not be, and these reports are ~6 MB each.

`COVERAGE=1` exists only for that one command — nothing is persisted, normal runs
are untouched (verified: without it, zero overhead, zero files written).

## The denominator — always the WHOLE codebase (default since 2026-07-22)

Chrome only reports on code the browser actually *loaded* — and Vite loads lazy
route chunks only when a test visits that page. Left alone, that makes the
denominator "code the suite happened to load," which flatters the % and makes
campaigns incomparable (visiting a new page grows the denominator).

So `report.mjs` uses monocart's `all` option by default: it scans the sibling
`../EliteaUI/src` tree and enters every never-loaded file at 0%. Result:
**denominator = all ~1,850 source files, constant across campaigns — only
actual execution moves the number.**

Cautionary tale from the first run: with the loaded-only denominator, `settings`
showed 50% branch coverage. With the full denominator it's **3%** — only 92 of
its 1,696 branches had ever been loaded. The 50% was an illusion.

Mechanics: never-loaded `.jsx` can't be branch-parsed raw, so `report.mjs`
compiles them with **EliteaUI's own esbuild** (`../EliteaUI/node_modules` — no
extra dependency; run `npm install` in EliteaUI once). If esbuild is missing it
degrades gracefully: those files still enter at 0% with byte/line metrics only,
and a `[warn]` is printed.

**Which numbers are canonical:** the rollup table (`area_rollup.py`, backed by
`coverage-summary.json`) — its denominator is stable across campaigns (verified:
Δ3 branches out of ~40k between campaigns). Monocart's *console header* counts
V8-native units that inflate as more files get loaded — fine within one run,
do not compare it across campaigns.

## Reading the numbers — the one thing people get wrong

- **Branch %** is the truth. It only moves when logic actually executes.
- **Statement %** has a ~25–30% "load floor" everywhere: importing a module at app
  boot executes its top-level code (imports, constants, component *declarations*)
  even if nothing ever renders. `stmts > 0, branches = 0, functions = 0` = file was
  merely loaded, not used.
- Nonzero branches in a "foreign" area is usually REAL (agent pages embed chat
  components and toolkit hooks) — the app's areas aren't islands.

## Gotchas — three ways this tool has produced a WRONG number

All three were found in the 2026-08-10 campaign. Each is **silent**: the report
generates cleanly and looks plausible. None throws an error.

### 1. Vite HMR duplicates inflate the denominator (fixed — keep the fix)

monocart normalises the served URL into a filesystem-safe `distFile`, turning
`?` into `-`. Vite's HMR cache-buster therefore arrives as a trailing
`-t=<epoch-ms>`, so a `sourcePath` that only does `.split('?')[0]` never matches
it. Every file touched by an HMR reload mid-run becomes a **second entry**,
splitting its coverage across the pair:

| | entries | HMR dupes | branches | covered |
|---|---:|---:|---:|---:|
| 2026-07-24 | 1,877 | 0 | 40,995 | 14,376 |
| 2026-08-10 *before fix* | 2,607 | **569** | 61,895 | 20,249 |
| 2026-08-10 *after fix* | 2,038 | 0 | 42,996 | 20,249 |

It read **32.7%** instead of **47.1%** — i.e. it looked like a *regression*.
Dropping the dupes loses 10,215 covered branches; keeping them double-counts the
denominator. They must be **merged**, which is what stripping the suffix does.

**Why 2026-07-24 had none:** nothing edited EliteaUI during that campaign. A
long campaign is exactly when other agents are pushing testids to
`automation/testids`, so HMR fires repeatedly. **Expect this on every multi-hour
run.** `report.mjs` now strips the suffix and warns if any entry still lacks a
source extension.

### 2. `areas.json` drift silently merges whole areas

`analytics` was mapped to `src/[fsd]/features/analytics/`. That directory was
deleted upstream and analytics moved *under* `src/[fsd]/features/settings/ui/`.
Since `settings` maps the parent path and match order is first-wins, every
analytics file silently re-bucketed as **settings** — inflating settings' apparent
recovery and making the `analytics` row read 0/0.

A dead mapping **does not error**. Run `node coverage/campaign.mjs lint-areas`
before every campaign, and **never diff two printed tables** — use
`campaign.mjs compare`, which re-buckets *both* datasets with the *current* map.

### 3. The denominator spans two repos

`src/lib/**` and `src/EliteaAssistant.tsx` are the **Support Assistant**
(`../elitea_assistant`), reaching the browser via the `VITE_ASSISTANT_LOCAL`
alias — not EliteaUI. ~312 branches. They are legitimate executed code, so they
are mapped to a `support-assistant` area rather than hidden. Note that the
`all` full-codebase scan only walks `../EliteaUI/src`, so connected-repo files
enter **only when executed** — their denominator is not fixed the way EliteaUI's
is. `lint-areas` reports anything in this category.

### Sanity checks before quoting any %

1. `campaign.mjs compare` prints the denominator drift and warns above ±10%.
   Real source growth is a few percent (2026-08-10: +4.9% for 129 new files).
2. Entry count in the report ≈ source-file count. A big jump means duplicates.
3. `costMethod`-style trust rule: if a number surprises you, check the
   denominator *before* believing the numerator.

## HTML report legend (`coverage/report/index.html`)

Header, per metric: **% chip** (green good / yellow middling / red poor), then
three boxes: **green = covered, red = uncovered, plain = total**; the ⊙ crosshair
jumps to the next uncovered range. **Top Hits** pills (`x1.77K`) = the file's
most-executed ranges with their V8 call counts.

In the code view:

| Marker | Meaning |
|---|---|
| Gutter bar 🟩 / 🟥 / 🟨 | Line executed / never executed / **partially** (e.g. declaration ran, body didn't) |
| Pink text background | Exact byte ranges that never ran |
| Green `x82` pill | Execution count — that function ran 82 times |
| Red `E` badge | "else path uncovered" — this `if`'s else side never taken |
| Far-left pastel strip | Minimap of the whole file's coverage |

Classic pattern worth recognizing: component renders thousands of times (huge Top
Hits) while its validator/handler bodies sit solid pink — the screen was *visited*
but its logic never *exercised*. That gap is what this tool exists to expose.

## Facts & mechanics

| Thing | Value |
|---|---|
| Overhead | ~13% runtime (~3s on a 22s run) |
| Fragments | ~25 MB per test in `coverage/.v8/` (gitignored) — see Cleanup section |
| Merging | Union: fragments from any number of runs/shards combine, no double-count |
| Failed tests | Still emit coverage (capture is in fixture teardown) — they count what ran before dying |
| Skipped tests | Contribute **zero** — an always-skipping test shows up as coverage it doesn't add |
| Retries (`--reruns`) | Extra fragments, harmless (union) |
| Full-campaign cost | 397 UI tests ≈ 3h56m runtime, 10 GB fragments (396), ~30 s report generation. Rate is steady at ~1.7 tests/min — scale linearly to size a campaign |
| Browser | Must be Chromium (it is — see `fixtures/session_fixtures.py`) |

How it works, one paragraph: the `page` fixture in `automation/conftest.py` (the
env-gated block) opens a raw CDP session — Playwright Python has no `page.coverage`
helper — starts V8 precise coverage, and at teardown saves the counters PLUS each
`src/**` script's source text (`Debugger.getScriptSource`; the text carries Vite's
inline sourcemap). `coverage/report.mjs` (monocart-coverage-reports) remaps those
to original `.jsx` files — `sourcePath` restores full paths from the served URL
because Vite's per-module sourcemaps hold bare filenames only — and filters out
node_modules/svg-icon stubs. `coverage/area_rollup.py` buckets files into feature
areas via `coverage/areas.json` (substring match, first hit wins, `shared` last).

## Cleanup — fragments are campaign scratch, wiped manually

Nothing auto-deletes. `coverage/.v8/` grows ~25 MB per test (a 60-test campaign
≈ 1.5 GB); both it and `coverage/report/` are gitignored, so the only cost is
local disk.

| Moment | Action | Why |
|---|---|---|
| **Start of the NEXT measurement** | `node coverage/campaign.mjs archive <label> --wipe` | The standard cleanup point. **Archive first** — wiping without archiving destroys the only thing the next campaign can be compared against |
| After reporting, optionally | Same command | Only if you need the disk back — the report itself is small and self-contained |
| Never automatically | — | See below |

Why no auto-cleanup — two deliberate reasons:

1. **Accumulation is a feature.** Separate pytest runs (waves, CI shards,
   "one more test") drop fragments into the same `.v8/` and merge as a union
   into one report. A session-start auto-wipe would erase the previous wave.
2. **Fragments allow re-reporting without re-running tests.** Changing a filter
   or the area map costs a 1-minute `node coverage/report.mjs` against existing
   fragments — deleting them early makes the same answer cost the full test
   runtime again. Keep them until you're done slicing the campaign's data.

## Campaign history

Archived under `../coverage-archive/<label>/` (report + rollups + `PROVENANCE.txt`).
Always quote the **rollup** number, never monocart's console header.

| Campaign | Tests | Runtime | Branches | Statements |
|---|---:|---:|---:|---:|
| `2026-07-24-baseline` | ~180 | ~2h10m | 14,376 / 40,995 = **35.1%** | 54.7% |
| `2026-08-10-campaign` | 397 | 3h56m | 20,249 / 42,996 = **47.1%** | 66.9% |

**2026-08-10 per area** (branch view, both sides re-bucketed with the current map):

| area | base | new | Δpp | | area | base | new | Δpp |
|---|---:|---:|---:|---|---|---:|---:|---:|
| **settings** | 3% | **34%** | **+32** | | shared | 40% | 49% | +9 |
| catalog | 0% | 43% | +43 | | credentials | 51% | 60% | +8 |
| notifications | 0% | 37% | +37 | | mcp | 24% | 27% | +4 |
| pipelines | 28% | 45% | +17 | | toolkits | 41% | 45% | +3 |
| chat | 41% | 55% | +14 | | skills | 32% | 34% | +2 |
| artifacts | 39% | 54% | +14 | | **onboarding** | 5% | **5%** | **0** |
| resources | 0% | 12% | +12 | | **auth** | 10% | **10%** | **0** |
| agents | 32% | 43% | +11 | | analytics | 0% | 39% | +39 |

`onboarding` and `auth` gained **zero** branches across 217 additional tests —
they have no tests at all. That, plus `skills`/`mcp`/`toolkits` being near-flat,
is the ranked test-writing backlog.

> **Both campaigns are floors, not ceilings.** 2026-08-10 ran 348 passed / 38
> failed / 4 errors / 7 skipped, with 26 reruns all on `502 Server Error` (an
> intermittently unhealthy DEV backend). Failed tests still emit coverage for
> whatever ran before they died, so the number is valid — a healthy run scores
> higher. Skipped tests contribute exactly zero.

> **Note on the old figure.** This section previously read "32.7% of 40,338
> branches" for the 2026-07-22 campaign. The archived report's own rollup says
> **35.1% of 40,995**. The lower figure appears to have been monocart's console
> header, which this README elsewhere says never to compare across campaigns.
> The table above uses the rollup for both, so the +12.0 pp delta is like-for-like.

Excluded from both campaigns: `test_guardrails_live_reload.py` (3 admin tests) —
they mutate shared DEV-backend guardrail config.

## Maintenance

- **Before every campaign** → `node coverage/campaign.mjs lint-areas`. It fails
  on a mapped path that no longer exists (the silent re-bucketing of Gotcha 2),
  and warns about files landing in `other` — including runtime-only files from a
  connected repo, which the `all` tree-scan cannot see.
- **New feature folder in EliteaUI** → add its path to `coverage/areas.json`.
  Remember **first match wins**: a specific path must come *before* the generic
  parent that would otherwise swallow it (`analytics` sits above `settings` for
  exactly this reason), and `shared` must stay last.
- **Report empty / 1 file only** → dev server not in dev mode (needs sourcemaps),
  or monocart API drift — check `coverage/report.mjs` comments.
- Full trial write-up & design rationale: `docs/runtime-execution-coverage-approach.md`
  and `docs/coveragetrial.md` (in the parent factory repo's docs/).
