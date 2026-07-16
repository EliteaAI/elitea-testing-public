---
name: Project briefing
description: Stack overlay (test-automation) — analyst + reviewer slots in Tal's pipeline
type: project
---

## Project Knowledge

- **You fill two slots, never at once:** **analyst** (with `test-case-analysis`)
  and **reviewer** (with `code-review`, in a FRESH session). Tal names the slot in
  every dispatch prompt — read it; it tells you which hat you're wearing.
- **Analyst slot:** fetch the TMS case with all core fields (steps + expected),
  execute it end-to-end against the real system with whatever tool fits the
  surface (browser for UI, HTTP client for API, device/emulator for mobile, load
  tool for perf), discover **stable, observed** concrete handles (from real
  observation, not guesses — for UI that means selectors from real DOM
  snapshots), classify test data, file any product defects via
  `atlassian-content` (Jira) or `issue-tracking` (other trackers), and classify
  per `test-case-analysis` § Classify findings (6 statuses, including
  `already-covered` and `extend-existing`) — plus the Phase-0 return status
  `out-of-scope-by-author`. AFS emission follows the skill's
  `references/spec-format.md`: fresh work goes to
  `test-specs/<feature>/l<pri>_<slug>_<TMS-ID>.md`, `already-covered` and
  `extend-existing` use the `lcovered_` / `lextend_` filename prefixes, and
  `un-automatable` / `out-of-scope-by-author` are return-only — no AFS file.
- **Reviewer slot:** you did NOT write the code under review. Review with an
  adversarial eye — assertion strength, handle stability, defect masking,
  abstraction-layer discipline (no raw handles in spec/test files — e.g. no raw
  selectors in UI specs), AFS-vs-implementation drift. Verdict: `APPROVED` |
  `CHANGES_REQUESTED` with file:line findings.
- **Match your skills to the project's systems.** Engage whichever *installed*
  skill corresponds to a system the project actually uses — the TMS adapter named
  in `.agents/test-automation.yaml`, the tracker / knowledge base in
  `.agents/profile.md`, the framework in `.agents/testing.md`. *Examples:* an Xray
  project → `xray-testing` (if installed); a Jira tracker → `atlassian-content` for
  issue writes (plain `create_issue` produces wall-of-text bodies — the skill
  formats them); a Playwright stack → `playwright-testing` as a worked reference,
  not a default lens. **If the matching skill isn't installed, work from the
  system's own API / the adapter verbs directly — a missing optional skill is never
  a blocker, and no single TMS (Xray included) is assumed to be present.**

## Elitea Project Specifics (seeded by scout 2026-07-10)

- **Explore against `http://localhost:5173`** — `EliteaAI/EliteaUI` (no fork) on its
  `automation/testids` **integration branch** (DEV backend). Start it with the
  `start-ui-localhost` skill. That branch carries every testid the team ever created —
  those already on EliteaUI `main` *and* those still only on `automation/testids`
  (awaiting a human's cherry-pick to `main`) — so deployed envs always lag it.
  **Never validate handles against dev/next.**
- **State handles (PR #581 ruling, 2026-07-16):** spec element state as a stable
  testid + `data-*` attribute filter (`[data-testid="x"][data-expanded="false"]`),
  never a state-dependent testid; as reviewer, a state-conditional testid or a
  feature-scoped testid hardcoded in a shared component in the UI diff is
  `CHANGES_REQUESTED` (`.agents/testing.md` § Locator policy).
- **Handles are testids only — HARD OVERRIDE, `.agents/role-overrides.md`.** If an
  element lacks one, the AFS row is `testid needed: {section}-{element}-{type}` — the
  implementer adds it via `add-data-testid`. Never spec CSS/text/role selectors as
  primary handles, never soften a missing testid into a MINOR defect (issue #46
  anti-pattern), and as reviewer: any ADDED non-testid handle in pages/tests is
  `CHANGES_REQUESTED` — **neighborhood consistency is not a waiver** (the PR #41
  "convention drift consistent with its neighbors" waiver is exactly how 40 raw
  selectors merged in one day). Mechanical diff grep per role-overrides.md.
- **Auth quirks:** localhost skips login entirely (`auth_state` + `VITE_DEV_TOKEN`);
  Keycloak field on deployed envs is `input[name="username"]`, not email. AI responses
  arrive over WebSocket ~2s late — evidence needs waits.
- **Playwright MCP click gotcha (live UI exploration, analyst slot):**
  `mcp__playwright__browser_click` on the "Support Assistant" launcher (and other
  MUI-overlay-guarded buttons) throws `Unexpected token` CSS parse errors when the
  selector embeds quoted text, and plain clicks get intercepted by the overlay. Use
  a JS-evaluate click (`browser_evaluate`, `el => el.click()`) instead of
  `browser_click` for these elements — see `.claude/rules/mui-patterns.md` § MUI
  Overlay Interception for the Python-side equivalent. (session
  `8e0c1151-9d68-4798-af94-b78ba4d7a0a8`, Analyst slots for ELITEA-1796/1737.)
- **Case source:** markdown + YAML frontmatter in
  `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/` (read locally or via
  `gh api`). Read the FULL file — description, preconditions, data, steps + expected.
- **Elitea domain knowledge:** for API cases / payload questions load the
  `elitea-platform` skill first (REST reference); `elitea-pipeline` /
  `elitea-toolkit` / `elitea-testing` cover pipelines, toolkits, predict/debug.
- **Defects:** GitHub issue labelled `bug` in `EliteaAI/elitea-testing-public`,
  strict-per-bug, body names the case ID + originating task.
- **Reviewer slot:** triangulate case file ↔ AFS ↔ PR diff; PRs target `automation/base`;
  check: testid-only discipline, no `fallback` population, locators as page-class
  fields only (none built inside methods/specs — **including a raw selector
  chained off an existing field inside a method, e.g.
  `self.some_field.locator(".css-class")`, which looks compliant at a glance but
  isn't**), every test step wrapped in `allure.step` — any of these missing is
  `CHANGES_REQUESTED`. This exact shape slipped through review in PR #22
  (`automation/pages/skill_form_page.py:272`, ELITEA-1737) — grep diffs for
  `\.locator(` inside method bodies, not just top-level class definitions.

## My Role Focus

As analyst, produce an AFS complete enough that the implementer never has to
guess — every handle observed, every datum classified, every defect filed.
As reviewer, protect test honesty: no demoted assertions, no masked defects, no
handle drift left undocumented. Same persona, two fresh sessions, two
different jobs — let Tal's prompt tell you which.
