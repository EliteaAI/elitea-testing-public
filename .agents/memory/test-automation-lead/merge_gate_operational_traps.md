---
name: Merge gate — operational traps on top of the canon
description: What .agents/testing.md § Merge gate does NOT say — an isolated flake restarts the count, extend-existing sanctioned-RED needs a per-step allure check, gh pr diff lags a base push, junit archives corroborate timing, and finite test-data pools only fail at run 3+.
type: feedback
---

`.agents/testing.md` § Merge gate already states N=3, three separate invocations,
lead-run, strictly pre-merge, plus the sanctioned-RED rules. **This entry adds only
what that doc doesn't cover.**

## Rule

- **An isolated non-reproducing flake restarts the count.** A lone timeout with a
  verified-healthy server is not a defect (fails every sanctioned-RED criterion)
  and not a block — but "2 green + 1 red + 1 green" is not the gate. Discard it and
  count 3 fresh consecutive greens from the next clean run. Record it explicitly in
  the closure record so the run count reconciles. If it *reproduces*, route it
  through the normal Debug-phase table instead of re-rolling.
- **`extend-existing` onto an already sanctioned-RED covering test needs a
  step-level check.** `expect.soft()` failures aggregate and re-raise, so the
  overall result is `failed` on every run regardless of what the new steps did —
  3/3 identical RED is necessary but not sufficient. Read
  `automation/reports/allure-results/*result.json` yourself and confirm each NEW
  step's own `status == "passed"`, in each of the 3 runs:
  `for s in json.load(open(f))['steps']: print(s['status'], s['name'])`.
- **`gh pr view` / `gh pr diff` file counts lag a base-branch push.** Before
  squash-merging, verify scope locally: `git fetch origin <base>` →
  `git log --oneline origin/<base>..<base>` (local ahead? FF-push it) →
  `git diff origin/<base> <pr-branch> --stat`. That is the truth; an inflated
  count would otherwise comingle unrelated commits into the squash.
- **Corroborating gate timing (yours or an audited one):** `conftest.py` archives
  EVERY invocation to `automation/reports/archive/junit_*.xml`.
  `grep -l "<test_method>" …/archive/*.xml`, then `timestamp="…"`,
  `tests="1" time="…"`, `failures="…"`. Durations match pasted values to the
  millisecond; convert local tz → UTC and confirm run 3 finishes *seconds before*
  `mergedAt`. With many candidates (a shared covering test), derive the tz offset
  from a post-merge commit's `git log --format=%aI` vs `mergedAt`, then fingerprint
  by failure-signature *order*, not just the day.
- **Finite test-data pools fail only at run 3+.** "Reuse a leftover resource,
  delete at teardown" against a non-replenishing pool is deterministic green until
  the pool empties, then deterministic red — the implementer's and reviewer's
  2-run greens structurally cannot catch it. Ask at AFS time whether the pool
  replenishes; prefer create-and-clean via a raw-payload API path that dodges the
  blocking defect. If the gate catches it, it is an infrastructure finding, not an
  R2 charge: fix-only round → fresh reviewer on the delta → restart YOUR gate from
  zero (pre-fix greens don't count).
- **The mechanical locator grep is two orthogonal clauses**, and a clean lexical
  alternation is not a clean gate: lexical (banned handle functions) *plus*
  structural (`get_by_test_id` constructed inline in a spec or method body instead
  of a class-level `LocatorDescriptor`). Both belong in the dispatch prompt and in
  the reviewer's independent re-verify.

## Seen 6×

- #29/ELITEA-1739/PR#208 — run 3 timed out, non-reproducing; counted 3 fresh greens after.
- #240/ELITEA-1827/PR#658 — extend-existing onto #649's sanctioned RED; per-step allure JSON distinguished it.
- #19/PR#24 — `gh pr diff` showed 18 files vs 1 real, from a local base 2 commits ahead of origin.
- …plus 3 earlier occurrence(s) — full per-case detail in the source entries below.

See also: isolated_flake_restarts_merge_gate_count.md ·
merge_gate_extend_existing_sanctioned_red_needs_step_level_check.md ·
merge_gate_gh_pr_diff_staleness.md ·
archived_junit_cross_check_for_merge_gate_timing.md ·
finite_test_data_pool_exhaustion_caught_by_gate.md ·
mechanical_grep_gate_coverage.md · live_run_gate_is_pre_merge_not_post.md (excluded)
