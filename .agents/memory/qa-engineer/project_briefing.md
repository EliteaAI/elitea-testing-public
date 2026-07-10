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

- **Explore against `http://localhost:5173`** — the EliteaUI fork on `automation/testids`
  (DEV backend). Start it with the `start-ui-localhost` skill. Every team-added testid
  exists THERE; deployed envs lag behind — never validate handles against dev/next.
- **Handles are testids only.** If an element lacks one, that's a finding for the AFS
  ("testid needed: `{section}-{element}-{type}`") — the implementer adds it via
  `add-data-testid`. Never spec CSS/text selectors.
- **Auth quirks:** localhost skips login entirely (`auth_state` + `VITE_DEV_TOKEN`);
  Keycloak field on deployed envs is `input[name="username"]`, not email. AI responses
  arrive over WebSocket ~2s late — evidence needs waits.
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
  fields only (none built inside methods/specs), every test step wrapped in
  `allure.step` — any of these missing is `CHANGES_REQUESTED`.

## My Role Focus

As analyst, produce an AFS complete enough that the implementer never has to
guess — every handle observed, every datum classified, every defect filed.
As reviewer, protect test honesty: no demoted assertions, no masked defects, no
handle drift left undocumented. Same persona, two fresh sessions, two
different jobs — let Tal's prompt tell you which.
