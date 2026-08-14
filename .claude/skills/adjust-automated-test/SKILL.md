---
name: adjust-automated-test
description: Repair a merged test that went red because the product changed — triage the failure (UI drift vs product bug vs data pollution vs promotion gap), re-execute the case live, update the test/page object/AFS/TMS case to match current behaviour WITHOUT weakening what it verifies, gate it, and raise PRs for a human to accept. Use when a previously-green automated test fails and the cause looks like an intentional UI/behaviour change ("this test broke, the UI changed", an [Adjust][ELITEA-<id>] task, a red test in a CI report, a stabilization pass).
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Skill
---

# Adjust an automated test (product changed — the test must follow)

The forward pipeline (`test-automation-workflow`) turns a case into a merged test. **This
is the repair path for a test already merged that went red because the product moved.**

**Scope: one drifted test, end to end.** Which tests to work, in what order or grouping,
and how many at once is the **orchestrator's/implementer's** decision — not this skill's.
Apply it per test; it makes no assumptions about how you got here beyond one thing:
**someone suspects drift, and this skill's job is to confirm or refute that before
changing anything.**

How you got here is irrelevant to the method, but for reference the usual entries are: a
human-created tracking task titled **`[Adjust][ELITEA-<id>] <what changed>`** (the
repair counterpart to `[Automate][ELITEA-<id>]` new-coverage tasks), a free-form attended
ask ("this test broke, the UI changed"), a red test in a CI report, or a stabilization
pass over a subset/suite. The task, when there is one, records a human's *suspicion* — it
is not a verdict, and it never substitutes for Step 2.

**The invariant everything serves:** *what* a test verifies is frozen; only *how* it
reaches and identifies things may change (§ The preserve-the-nature rail).

## Role-agnostic — whoever the operator points at this

Any role may be asked to run this: an analyst (qa-engineer), an implementer
(test-automation-engineer), or the lead — in a live attended session or an unattended
dispatch. The method below does not change; **your own slot contract does.** So:

- **Run the steps your slot covers, in order, and stop at its edge.** Hand the rest back
  with the evidence you gathered rather than overstepping. Triage (Steps 1–2) is inside
  every slot's remit — it is diagnosis, not code change.
- **A reviewer slot is static** (no execution, no code change): it can *audit* an
  adjustment against the rail in Step 3, not perform one.
- **No commit/PR authority for this branch?** Produce the diagnosis, the updated AFS, and
  the concrete proposed diff, then report — do not push.
- **Solo/attended run:** the operator in the room is the human sign-off referred to
  throughout. **Unattended:** a decision that needs a human becomes a parked `question`
  issue plus a stop — never a guess (`factory/loops/*` deltas).
- Whatever the role, the **triage verdict and the preserve-the-nature rail are binding** —
  they are the point of the skill, not a stage that can be skipped for speed.

## Step 1 — Ground truth BEFORE any diagnosis

1. **Sync**, or you diagnose against stale UI: `sync-base-branches` (merges `main` into
   `automation/base`, and into `automation/testids` on EliteaUI + connected
   `elitea_assistant`). Guard first — never sync over another agent's in-flight work.
2. **Pick the environment — DERIVE it, never assume:**

   | Situation | Diagnose on |
   |---|---|
   | The test is on `main` and its testids are deployed (e.g. a DEV CI failure) | **`https://dev.elitea.ai`** — Keycloak login, `TEST_USER_EMAIL`/`_PASSWORD` from `.env.test`, field `input[name="username"]` |
   | The test lives on `automation/base` (not yet promoted) | **`http://localhost:5173`** (`start-ui-localhost`) — its testids may exist only on `automation/testids` |
   | A **new** testid will be needed | **localhost** — a new testid cannot exist on DEV yet |
   | Any testid the test uses is **not on EliteaUI `main`** | **localhost — DEV is impossible for this test** (step 4) |

3. **Reproduce** in that environment, clean process:
   ```bash
   cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider
   ```
   **Green locally but red in CI ⇒ NOT drift** — env/infra/data (class **D**).
4. **Promotion-gap pre-check — mandatory before calling any DEV failure "drift."** A test
   can be entirely correct and still red on DEV because its testid was never promoted.
   Fresh fetch, then compare refs (the closure-record grep, `.agents/workflow.md`):
   ```bash
   cd ../EliteaUI && git fetch origin
   for t in <every testid the failing test uses>; do
     printf "%-34s main:%-4s testids:%s\n" "$t" \
       "$(git grep -- "$t" origin/main -- src/ 2>/dev/null | grep -qE "(data-testid|testid.*=.*$t)" && echo YES || echo no)" \
       "$(git grep -- "$t" origin/automation/testids -- src/ 2>/dev/null | grep -qE "(data-testid|testid.*=.*$t)" && echo YES || echo no)"
   done
   ```
   `main:no` + `testids:YES` ⇒ **class F. Stop — do not touch the test.**

## Step 2 — TRIAGE. The heart of this skill.

**A red test is not evidence that the test is wrong.** Classify from the evidence trio —
**the TMS case** (`onetest-ai-tm-Elitea`: the specified behaviour), **the AFS**
(`test-specs/<feature>/`: what the analyst observed), **the automation code** (what it
asserts) — plus **`../EliteaUI/src`**, which states the product's *intended* behaviour as
fact. Run `.agents/role-overrides.md` § interaction-discovery ladder and § 4xx/5xx before
any verdict.

| # | Class | Signal | Action |
|---|---|---|---|
| **A** | **UI drift** | Locator times out / element renamed, moved, restructured; the intended flow still works but differs from the case | **Adjust** → Steps 4–8 |
| **B** | **New product bug** | The flow intended per `src/` is genuinely broken | File a local `bug`; test stays red, or `expect.soft()` + `# Known defect: #N`. **Do NOT adjust.** |
| **C** | **Known bug persisting** | Matches an OPEN `bug` issue | Keep red, link `# Known defect: #N`, record as sanctioned RED. **Do NOT adjust.** |
| **D** | **Data pollution / flake / infra** | Leftover entities skew a baseline or count; timing; CI-only; environment | Fix **hygiene and robustness** (unique data, scoped queries, cleanup, condition waits) — **never the assertion.** |
| **E** | **Testid gone, no replacement** | Element exists but carries no testid | `add-data-testid` on localhost (or the connected repo), then adjust. Cannot be placed ⇒ `blocked`. |
| **F** | **Promotion gap** | Testid on `automation/testids` but not `main` (step 1.4) | **Nothing to fix.** Report it; red on DEV is expected until a human promotes. |

> **Worked example — why D is not optional.** CI run 30532379296 mixed both in one run: 4
> toolkit failures were `Locator.wait_for` timeouts (class **A**), while a skills failure
> was `Expected 23 cards (baseline 20+3), got 20` — and the returned list was full of
> prior-run debris (`el-1795-skill-*`, `elitea-1790-*`), i.e. class **D**. Lowering that
> expected count would have masked a data-hygiene defect. **Same run, opposite actions.**

Only **A** (and **E**, once the testid lands) proceeds to adjustment. Everything else is
reported with its evidence (Step 9) — **never silently adjusted.** If triage refutes the
suspicion, say so plainly and stop; that is a successful outcome, not a failure.

## Step 3 — The preserve-the-nature rail (the anti-masking contract)

| Free to change (*how* it reaches/identifies) | Requires explicit human sign-off (*what* it verifies) |
|---|---|
| `LocatorDescriptor` testids, class-level selector constants | Deleting an assertion, or a whole step |
| Step order, navigation, added condition waits | Weakening a comparison (`==` → `in`, exact → substring) |
| Page-object method internals, new helper methods | Lowering a count/threshold, or making a check conditional |
| Renamed handles after a restructure | Replacing a state assertion with a mere presence check |

An assertion may change **only** because the *case's expected result* genuinely changed —
and then the TMS case changes in the same PR pair (Step 8). Record every such change in the
AFS and under **"Expected-result changes"** in the PR body; if there are none, **say so
explicitly.** Markers, docstring TMS links, and `allure.step("Step N — …")` structure are
preserved verbatim — only internals move.

## Step 4 — Locate the test and its record

`ELITEA-<id>` → TMS case (`onetest-ai-tm-Elitea`; MCP `get_test_case` or the case file) →
its `automation_test_id` (dotted, `tests.`-rooted Form C) → the file:
`tests.ui.agents.test_x.TestY.test_z` ⇒ `automation/tests/ui/agents/test_x.py::TestY::test_z`.
Open the AFS (`test-specs/<feature>/`) and the page objects it uses. If the file is missing
or the id doesn't resolve, report `blocked` **and** flag the stale `automation_test_id` —
that is its own defect (it silently breaks TMS correlation).

## Step 5 — Re-execute the case live and capture the deltas

Walk the **original case steps** against the live UI (Playwright MCP: snapshot → act →
re-snapshot, refs go stale after every action; browser-driving Bash `timeout=600000`).
Record precisely: steps added/removed/reordered, testids renamed/removed/replaced, changed
expected values or states, new elements needing assertions. Screenshot each delta and
**embed** it per `.agents/role-overrides.md` § screenshot evidence (`embed-evidence` does
the upload) — never a bare local path.

## Step 6 — Update the AFS

Amend the existing AFS in place (`test-specs/<feature>/`, `test-case-analysis`
spec-format) so it describes current behaviour as the new source of truth. Keep the Handles
Reference **testid-only**, every row carrying a verified PROVENANCE (`on-main ✓` /
`on-automation/testids only` / `needs-adding`). Add an **Adjustment** section: what changed,
why, the triage class, and any Expected-result changes.

## Step 7 — Update the code

Branch `tests/adjust-ELITEA-<id>-<slug>` from fresh `origin/automation/base`. **Plain
branching, one thing at a time — no git worktrees** (`.agents/workflow.md` § No git
worktrees).

- **Update existing code only** — no new test files, no new test classes.
- Locators stay class-level `LocatorDescriptor(testid=…)` or UPPER_CASE `[data-testid="…"]`
  constants. No `fallback=`/`locator=`, nothing built in a method body, no raw handle
  chained off a field (`.agents/testing.md` § Locator policy — testid-only, no ladder).
- Need a testid ⇒ `add-data-testid` (localhost; **the connected repo's own source** if the
  element ships from `elitea_assistant`), commit + push `automation/testids`. Genuinely
  cannot be placed ⇒ `blocked`.
- Obey the preserve-the-nature rail (Step 3).
- **Self-check before handoff** — run the reviewer's mechanical grep on your own diff and
  paste the output (an empty result is the evidence):
  ```bash
  git diff origin/automation/base... | grep -nE '^[+].*(get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|get_by_test_id|query_selector|page\.locator|\.locator\()'
  ```

## Step 8 — Gate, then raise the PRs

**Gate** (`.agents/testing.md` § Merge gate): **3 separate consecutive invocations of the
same node id**, clean process each time:
```bash
cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider   # ×3
```
Red during the gate ⇒ **re-triage** (Step 2). Never re-adjust to force green. A class
**B/C** defect may merge **sanctioned RED** only under `.agents/testing.md`'s criteria
(deterministic 3/3 identical, single-cause or an enumerated closed set, linked OPEN defect,
soft-asserted) — name which members fired.

**Then two PRs — this skill prepares, a human accepts:**

1. **Test PR → `automation/base`** · `test(adjust): ELITEA-<id> — <what changed>`. Body:
   the originating task link, **triage class + evidence**, what drifted (old→new),
   **Expected-result changes** (or "none"), gate evidence 3/3, testid provenance, and the
   self-check grep output.
2. **TMS PR → `onetest-ai-tm-Elitea`** — the case's steps/expected results updated to
   current behaviour. **Keep `automation_test_id` unchanged** (same test, same dotted path);
   set `automation_pr` to the test PR URL. Edit case files **by exact path** — several cases
   can share an `ELITEA-<id>`-looking name, so never glob by id.

Never merge either PR; merging is always human.

## Step 9 — Report

Report the outcome for the test, whatever the class — an unadjusted test is a result, not a
gap:

| Class | What the report must carry |
|---|---|
| A drift | old→new handles, Expected-result changes (or "none"), PR links, gate 3/3 |
| D pollution | the debris/timing observed, the robustness fix, and that assertions were untouched |
| B / C bug | repro + `src/` pointer, the issue number, sanctioned-RED justification |
| E blocked | which element, why no testid could be placed |
| F promotion gap | the ref-grep output, and that a human testid promotion is what unblocks it |

Leave board routing and issue closure to the orchestrator/human
(`.agents/profile.md` § Issue tracker: `Approved`/`Done` are human-only).

## Never

- Never adjust a test to make a **product bug** or a **data-pollution** failure go green.
- Never weaken an assertion, drop a step, or lower a count without explicit human sign-off
  recorded in the PR body.
- Never write a new test file here — that is `[Automate]` work (`test-automation-workflow`).
- Never file to `EliteaAI/elitea_issues` — local `bug` issues only; escalation there is
  attended + explicitly requested (`.agents/profile.md` § Bug filing).
- Never create a git worktree; never rebase or force-push a shared branch.
- Never trust a stale clone — `git fetch origin` before any ref comparison.
