# Role Overrides — project-specific hard rules (this file wins)

_This is the bundle's designed override channel (`.agents/role-overrides.md`,
hook-injected into every session and every subagent). Where anything here
conflicts with a skill's **defaults or examples** — including the
`test-automation-workflow` "UI example" locator ladder — **this file wins.**
Seeded by scout 2026-07-14 after the framework-alignment audit; the team's own
ruling (elitea-testing-public PR #23, "Enforce testid-only locators") is the
source of the locator policy._

## Every role — locator policy (the #1 override)

**This project has NO locator ladder. The ladder is one rung: `data-testid`.**
The `getByRole → testid → label → text → CSS` sequence in
`test-automation-workflow` is a generic *example* that does **not** apply here —
`.agents/testing.md` § Locator policy is the authority the skill itself defers to.

Why (team goal, first-class): **the team wants `data-testid` on every element new
tests touch, and will measure UI-automation coverage by testid presence.** A
role/label/CSS handle is not just brittle here — it is *invisible to the coverage
metric*. Every raw handle silently shrinks measured coverage.

- Element lacks a testid? That is **work to do, not a reason to rung down**: the
  implementer adds one via `add-data-testid` (dual-target flow). The escalation
  test is OR, not AND: *missing testid alone* ⇒ add it. Only "testid genuinely
  cannot be placed" (outside `EliteaUI/src`, third-party widget) escalates to the
  lead.
- **The scope is exactly the elements the case's test touches — NEVER blanket-add**
  (team ruling 2026-07-14): testids on elements no test uses are front-end noise
  AND corrupt the coverage metric — the "highlight what has a testid" visualization
  is honest only while *presence ≈ tested*. Adding testids "while you're in there"
  to untouched elements = `CHANGES_REQUESTED`. (Optional testid PROPS on shared
  components are fine — they render nothing unless a caller opts in — but each new
  prop is a component-API change the UI team reviews as a pattern.)
- **Fresh ground truth (hard rule).** Any verification against `origin/*` refs —
  promotability greps, "does this testid exist on main", branch-state checks —
  is preceded by `git fetch origin` in that repo, in the same command block. A
  verification against a stale clone is not a verification (#19 rework shipped a
  false "0 of 12 on main" row exactly this way; truth was 5/12, added by the UI
  team's own EL-5400). Name the ref you checked and PASTE the command output.
- **Declared-improvisation protocol (canon gaps).** When the canon has NO pattern
  for your case: pick the most spirit-compliant option AND declare it explicitly —
  in the Run Report and the PR description — as a proposed pattern with reasoning
  ("no sanctioned shape for X; chose Y because Z"). A DECLARED improvisation is a
  canon-gap escalation: the reviewer verifies the reasoning, the auditor reports it
  as a `question` — it can never solo-FAIL a delivery. An UNDECLARED improvisation
  is a violation, full stop. (Origin: #19 FAIL-1 — a semantically-correct
  improvisation was indistinguishable from a violation because it was silent.)
- **The surrounding code is NOT precedent.** `automation/pages/` contains ~350
  pre-policy raw handles (tracked tech debt, issues #25/#42). Matching the
  neighbors is how the debt grew; never cite existing code to justify a new raw
  handle.

## Every role — before filing a UI "doesn't work" bug: the interaction-discovery ladder

A case text that under-specifies HOW a control activates is normal — never
assume your first guess (e.g. live filtering) is the intended mode. Before
declaring UI behavior broken, exhaust, in order:
1. **Wait out a debounce** (~1.5s after typing) — some controls are just slow.
2. **Press Enter** in the field.
3. **Look for an adjacent activation control** — search/submit icon or button
   (check `aria-label`s near the field in the DOM snapshot).
4. **Blur the field** (Tab out) — some inputs commit on blur.
5. **Compare with the nearest working analog** in the app (e.g. how does the
   Agents list search behave?).
6. **Read the source — this is the decisive step.** `../EliteaUI/src` is checked
   out locally; the component's handlers state the INTENDED mode as fact:
   `grep -rn "<placeholder or label text>" ../EliteaUI/src/` → open the
   component → `onChange` handler filtering = live; `onKeyDown` + `Enter` /
   an `onClick={onSearch}` button = explicit activation. (Worked example:
   #44 — SearchBar.jsx activates on Enter/icon-click, not on typing.)

Then, and only then:
- **Intended mode (per code) fails** ⇒ CONFIRMED product `bug` — the report
  MUST name the intended activation mode with the code pointer, so nobody
  re-litigates it.
- **An alternative mode works but the case text implied otherwise** ⇒ NOT a
  product bug: file a case-text **clarification** issue (the #40 pattern) so
  the TMS case gets fixed; optionally note a UX-discoverability concern as
  its own observation. Filing it as `bug` creates false red and wastes a
  repro cycle (#44 is the cautionary example).

## Every role — screenshot evidence ATTACHES, never local paths

A screenshot referenced by a machine path (`.playwright-mcp/…`,
`automation/screenshots/…`) is evidence only you can see — useless on the
tracker (the #51 anti-pattern). When an issue/comment cites a screenshot,
UPLOAD it and embed it inline:

```bash
env -u GITHUB_TOKEN gh release upload evidence <file.png> --clobber --repo EliteaAI/elitea-testing-public
# then embed in the issue body/comment:
# ![what it shows](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/<file.png>)
```

The `evidence` prerelease is the attachment store (create once with
`gh release create evidence --prerelease --title "Evidence store" …` if
missing). Name files `<CASE-ID>-<step>-<what>.png` — the store is flat, names
are the only namespace. Local paths may ACCOMPANY the embed (for on-machine
lookup), never replace it.

## Every role — live-UI browser discipline (Playwright MCP)

- **Snapshot first, act second** — element refs go stale after EVERY action;
  re-snapshot before each interaction. Big page: save snapshot to a file, Grep it.
- **Simplest dedicated tool** (`browser_click`/`browser_type`/`browser_wait_for`).
  On "ref not found" / "not an input" / timeout: re-snapshot and retarget — never
  escalate to `browser_evaluate`/`run_code`, EXCEPT the documented overlay quirks
  (qa-engineer memory: e.g. Support Assistant launcher needs a JS-evaluate click).
- **Browser-driving Bash commands: timeout=600000 (10 min)** — the 120s default
  false-fails on Keycloak + SPA navigation + WebSocket AI waits (2–30s).

## Every role — batch shell round-trips (time-audit finding, 2026-07-16)

- **Combine related read-only shell commands into ONE Bash call** (`git status &&
  git log --oneline -3 && grep -c X file`) instead of one call each. Measured across
  35 delivered cases: misc-bash + git turns alone were **45% of all model time**
  (~5,700 turns × ~5 s each — the round-trip itself costs ~5 s regardless of how
  trivial the command is). Halving them saves ~7 min/case. Same for `gh` reads.
- **Scope file reads** — `Read` with offset/limit or a targeted `Grep`, not whole
  files: file-reading turns carry the largest payloads (12 KB avg) and the biggest
  context growth (~8.6k cache-creation tokens/turn), making them the slowest turns.
- Keep WRITE-side commands (commits, pushes, board writes) separate and reviewable —
  batching is for reads/checks, not for irreversible actions.
- Playwright MCP needs no such economy — its turns are the cheapest in the stack
  (3.3 s avg, compact snapshots); don't avoid it for "weight" reasons.

## Analyst slot (qa-engineer)

- The AFS **Handles Reference must list testids as the only primary handles.** An
  element without one is specced as `testid needed: {section}-{element}-{type}` —
  never "resolve by accessible role/name", never a CSS/role handle as primary.
- **Every handle row carries a PROVENANCE column**, verified at analysis time with
  a fresh fetch (`cd ../EliteaUI && git fetch origin` first): `on-main ✓` /
  `on-automation/testids only (awaiting human promotion to main)` / `needs-adding`.
  The implementer and the
  closure record inherit this verified data instead of re-deriving it — and the UI
  team adds testids in parallel (75+ on main already), so never assume "we didn't
  add it" means "it doesn't exist".
- Do not soften a testid demand into a MINOR defect or a note; it is implementer
  work, and the AFS is its work order.
- **State is specced as a `data-*` attribute filter, never as a state-dependent
  testid** (`.agents/testing.md` § Locator policy, PR #581 ruling). If the case
  asserts an element's state (expanded/selected/disabled), the handle row names the
  stable testid + the state attribute (`[data-testid="x"][data-expanded="false"]`)
  — never `testid needed: x-expanded` / `x-collapsed` variants.

## Implementer slot (test-automation-engineer)

- An AFS row saying `testid needed: X` means: run `add-data-testid`, add `X` to
  EliteaUI, use `LocatorDescriptor(testid="X")`. Never substitute a role/text
  handle "for now".
- **Amending an analyst's testid request away** (the ELITEA-1735 pattern: "the
  accessible name is stable, no testid needed") is out of contract — a testid
  request is satisfied by a testid or escalated to the lead, never re-scoped down.
- Locators are class-level `LocatorDescriptor(testid=…)` fields ONLY — no
  `fallback=`, no `locator=`, nothing built in method bodies, no raw selector
  chained off an existing field (`self.x.locator(".css")`). Scoped sub-selectors
  and **dynamic testids** use UPPER_CASE `[data-testid="…"]` string/template
  constants per `.claude/rules/page-objects.md` and `.agents/testing.md`
  § Locator policy (inline `get_by_test_id(f"…")` is NOT the compliant shape).
- **Self-check before handoff:** run the reviewer's mechanical grep (below) on
  your own diff and PASTE its output in the Run Report — an empty result is the
  evidence, a missing paste is a gap. Catching your own hit costs minutes; a
  review round costs a session.
- **`locator_descriptor.py`'s `locator=`/`fallback=` params are LEGACY** — kept so
  old code imports; never valid in new code, whatever any docstring example shows.

## Reviewer slot (qa-engineer, fresh session)

- **Any non-testid handle ADDED in `automation/pages/` or `automation/tests/` is
  `CHANGES_REQUESTED`.** Not a nit, not a non-blocking tech-debt note, not waived
  for neighborhood consistency. Mechanical check on every PR:
  `git diff <base>... | grep -nE '^[+].*(get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|get_by_test_id|query_selector|page\.locator|\.locator\()'`
  (`get_by_test_id` included: inline Playwright calls are also banned — locators are
  class-level `LocatorDescriptor` fields)
  — a hit is COMPLIANT only if the line contains a literal `[data-testid=` selector
  OR references an UPPER_CASE class constant whose class-level definition is a
  `[data-testid=` string/template (one-hop check — look it up). Everything else blocks.
- **Show your grep to the orchestrator.** Include the mechanical grep's actual
  command + output in the verdict you return to Tal — command (so scope/pattern
  is auditable) + result (hits verbatim, or explicit "0 hits / (no matches)" for
  empty). This is how Tal (and you) know it was really run on the full diff, not
  a weak subset — the #19 FAIL-2 lesson. (The delivery audit does NOT require this
  paste to survive into the tracker: the auditor re-runs the grep itself. It's
  reviewer discipline, not a tracker-artifact gate.)
- **Testid-convention check on any EliteaUI JSX in the case's diff** (PR #581
  ruling, `.agents/testing.md` § Locator policy): a state-conditional testid
  (`data-testid={cond ? … : …}` / `… : undefined`), a feature-scoped testid
  hardcoded in a shared component (`src/components/`, `src/[fsd]/shared/`), or a
  `dataTestId`-style prop name is `CHANGES_REQUESTED`.
- **Declared improvisations** (see § Every role): verify the reasoning and say so
  explicitly in the verdict; if sound, APPROVED + recommend the canon addition —
  do not block solely for the gap the canon itself left.
- "Selector stability per testing.md" in the review checklist means **this**
  policy, not the skill's example ladder.

## Orchestrator slot (test-automation-lead)

- **Dispatch-prompt contract:** every implementer and reviewer dispatch prompt
  MUST carry the line: *"Locator policy: testid-only (`.agents/role-overrides.md`
  + `.agents/testing.md` § Locator policy). The workflow skill's example ladder
  does not apply. New non-testid handles are CHANGES_REQUESTED."* The dispatch
  prompt is the gate — put the policy where it cannot lose.
- **Closure records state verified facts.** Before writing the promotability row:
  `cd ../EliteaUI && git fetch origin` FIRST (a stale clone produced the #19
  rework's false 0-of-12 row — truth was 5/12, the UI team's own EL-5400 testids),
  then check which testids the case's tests use (`grep` the diff) against **main**
  vs `automation/testids` (`git grep` both), and PASTE the output into the record
  (verbatim block in `.agents/workflow.md` § Closure record). Never copy the
  AFS/implementer's claim — #35/#36/#37 shipped false rows exactly that way.
- Run `sync-base-branches` before dispatching the first case of a session, not
  after the batch.
- **Never dispatch `ui-test-orchestrator` or `failure-investigator`.** They are
  installed for the HUMAN team's direct use only — their flows bypass the pipeline's
  gates (AFS, fresh-session review, merge gate, closure record). Every stage they
  cover has a canonical owner in your pipeline.
