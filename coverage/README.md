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

## Measure (3 commands)

```bash
# 1. Run ANY pytest selection with the switch on (from automation/):
cd automation
rm -rf ../coverage/.v8 ../coverage/report            # clean slate (skip to ACCUMULATE across runs)
HEADLESS=true COVERAGE=1 ../.venv/bin/pytest tests/ui/agents/   # or any file/marker/node-id

# 2. Translate browser counts -> per-file coverage (from repo root):
node coverage/report.mjs

# 3. Roll up into the per-area table:
.venv/bin/python coverage/area_rollup.py             # statements view
.venv/bin/python coverage/area_rollup.py --branches  # branch view  <- THE honest number
.venv/bin/python coverage/area_rollup.py --files chat  # per-file detail for one area
```

Line-by-line HTML: `open coverage/report/index.html`

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
| Full-campaign cost | ~180 UI tests ≈ 2h10m runtime, ~4.7 GB fragments, ~1 min report generation |
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
| **Start of the NEXT measurement** | `rm -rf coverage/.v8 coverage/report` (step 1 of the recipe above) | The standard cleanup point — keeps the new number unpolluted |
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

## Baseline — 2026-07-22, full available UI suite (~180 tests, localhost)

Reference point for future campaigns (branch view, full-codebase denominator):

| | branch % | | branch % |
|---|---:|---|---:|
| credentials | 47% | skills | 29% |
| artifacts | 39% | pipelines | 23% |
| shared | 39% | mcp | 19% |
| toolkits | 38% | auth / onboarding | 5–10% |
| chat | 35% | **settings** (1,696 br) | **3%** |
| agents | 34% | **resources / analytics / notifications / catalog** | **0%** |

**OVERALL: 32.7% of 40,338 branches** (52.6% of statements). Excluded from the
campaign: 3 admin tests (they mutate shared DEV-backend guardrail config).
The 0% rows are areas with no tests at all — the ranked test-writing backlog.

## Maintenance

- **New feature folder in EliteaUI** → add its path to `coverage/areas.json`.
  Unmapped files land in an `other` bucket in the table — if `other` grows, the
  map needs a refresh (`--files other` shows what's in it).
- **Report empty / 1 file only** → dev server not in dev mode (needs sourcemaps),
  or monocart API drift — check `coverage/report.mjs` comments.
- Full trial write-up & design rationale: `docs/runtime-execution-coverage-approach.md`
  and `docs/coveragetrial.md` (in the parent factory repo's docs/).
