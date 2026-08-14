# Role Overrides — project-specific hard rules (this file wins)

_This is the bundle's designed override channel. Where anything here conflicts
with a skill's **defaults or examples** — including the
`test-automation-workflow` "UI example" locator ladder — **this file wins.**
Seeded by scout 2026-07-14 after the framework-alignment audit; the team's own
ruling (elitea-testing-public PR #23, "Enforce testid-only locators") is the
source of the locator policy._

> ⚠️ **Delivery: this file reaches agents ONLY via the `@`-import block in
> `CLAUDE.md`.** The bundle's hook *can* inject it, but this project sets
> `SDLC_SHARED_DOCS=__none__` (`.claude/hooks/sdlc-skills/config.sh`) because the
> hook's ~10 KB `additionalContext` cap truncated the shared docs. **Removing
> `@.agents/role-overrides.md` from `CLAUDE.md` silently deletes the override
> channel** — every hard rule below stops reaching every agent, with no error.
> Verified 2026-08-10 (scout): the hook injects only per-role memory
> (`RULES.md` + `MEMORY.md` + `project_briefing.md`), never this file.

## Every role — locator policy (the #1 override)

**This project has NO locator ladder. The ladder is one rung: `data-testid`.**
The `getByRole → testid → label → text → CSS` sequence in
`test-automation-workflow` is a generic *example* that does **not** apply here.

**→ The full policy is `.agents/testing.md` § Locator policy — the single source,
and the authority the skill itself defers to. Read it; this section only states
that it OVERRIDES the skill.** It covers, in full: why (coverage is measured by
testid presence, so a raw handle is invisible to the metric); missing testid ⇒
add it via `add-data-testid`, never rung down; the #579 sanctioned exceptions and
their discipline; the blanket-add ban and the #511 "referenced = called on the
executed path" ruling; #277 conditional pairs; dynamic-testid and state-attribute
shapes; connected first-party repos; and why `automation/pages/`' ~350 pre-policy
raw handles (#25/#42) are tech debt, never precedent.

The per-slot consequences are below (§ Analyst / § Implementer / § Reviewer slot).

## Every role — fresh ground truth (hard rule)

Any verification against `origin/*` refs — promotability greps, "does this testid
exist on main", branch-state checks — is preceded by `git fetch origin` in that
repo, **in the same command block**. A verification against a stale clone is not a
verification (#19 rework shipped a false "0 of 12 on main" row exactly this way;
truth was 5/12, added by the UI team's own EL-5400). Name the ref you checked and
PASTE the command output.

## Every role — fidelity policy (the #2 override)

**An assertion is evidence only if the value it reads was produced by the SYSTEM,
not by the test.** Fabricated responses, injected state, wrong-interface
preconditions, replaced clients and bypassed subjects are all **substitutions**.

**→ The full policy is `.agents/testing.md` § Fidelity policy — the single source.
Read it; this section only states that it OVERRIDES every skill's defaults and
examples**, including the AFS template's "Engineer: decide whether to stub or
escalate" line (`test-case-analysis/references/spec-format.md`), which is a generic
example this project does not follow.

The short form every slot must know:

- **Transit substitution** (only to *reach* the step under test; the case's own
  observable still comes from the system) — allowed, **must be declared**.
- **Terminal substitution** (the case's observable is read off the substituted
  thing) — **forbidden**, unless the case text itself asks for simulation.
- **Cannot be produced honestly ⇒ route to a human** (`blocked` → lead →
  `question` card). Never engineer around it.
- Delaying a *real* response for timing control is NOT substitution.

Per-slot consequences: § Analyst / § Implementer / § Reviewer / § Orchestrator slot
below. (Origin: the 2026-08-14 drift audit — ~15 tests across 3 files asserted
against hand-authored payloads for cases that never asked; no gate objected.)

## Every role — precedent is not authority

**Neighbours are authority on CONVENTION, never on DEVIATION.** A merged, reviewed,
green example is not a norm — it may simply be a deviation nobody had a rule to
block. This generalises the locator-specific rule in `.agents/testing.md`
(*"Never cite neighbors to justify a new raw handle"*) to every decision you make.

- If you cannot cite a rule in `.agents/*`, `.claude/rules/*` or a skill, you have a
  **canon gap** — not a precedent. Handle it per the protocol below.
- "The same technique this file already uses", "consistent with the neighbouring
  tests", "already sanctioned and merged" are **not** authorities. Naming a merged
  example is a starting point for the question, never the answer to it.
- Watch the word **"sanctioned"** especially: it is only true if you can name the
  document and section that sanctions it. Borrowing an authority-word from an
  adjacent, unrelated rule is how the 2026-08-14 drift passed four gates.

## Every role — declared-improvisation protocol (canon gaps)

When the canon has NO pattern for your case: pick the most spirit-compliant option
AND declare it explicitly — in the Run Report and the PR description — as a
proposed pattern with reasoning ("no sanctioned shape for X; chose Y because Z").
A DECLARED improvisation is a canon-gap escalation: the reviewer verifies the
reasoning, the auditor reports it as a `question` — it can never solo-FAIL a
delivery. An UNDECLARED improvisation is a violation, full stop. (Origin: #19
FAIL-1 — a semantically-correct improvisation was indistinguishable from a
violation because it was silent.)

**A declaration makes a deviation VISIBLE — it does not make it PERMITTED.** Three
limits, added 2026-08-14 after the drift audit found declaration being used as a
bypass token (an elaborately reasoned AFS made a forbidden choice unblockable,
because the protocol above forbids a solo FAIL):

1. **Ceiling — what a declaration can never authorise.** It covers *how* you do
   something the canon left unshaped. It never covers a change to **what is being
   verified**: a terminal substitution (§ fidelity policy), dropping or weakening a
   case's observable, or swapping the subject of the case. Those are **human
   decisions** — route them (`blocked` → lead → `question` card), don't declare
   your way past them. A declaration in this territory is a violation, not an
   escalation.
2. **Obligation — a declaration is an open loop, not a receipt.** It must produce a
   `question` card proposing the canon addition **before the batch closes**. The
   lead owns this at close. An improvisation declared and never escalated is how a
   one-off becomes doctrine.
3. **Second use is a blocker, not a declaration.** The protocol covers the FIRST
   encounter with a gap. If the same unshaped pattern is being applied again, the
   gap is known and the answer is the canon card from (2) — repeating the
   declaration instead is laundering, and the reviewer treats it as
   `CHANGES_REQUESTED`.

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

## Every role — 4xx/5xx from the UI: cross-check the OpenAPI contract before verdict

A repro that surfaces a `4xx`/`5xx` (network tab, console) is **not** classified
as backend-vs-UI from the status code alone. Consult the OpenAPI spec before
declaring "backend bug" or "UI bug" — the same status can be either, depending
on the endpoint's declared parameter contract.

The `pylon_main` `shared` plugin hosts:
- `GET /shared/openapi/?all=true` — raw OpenAPI JSON (`?plugins=a,b` filters)
- `GET /swagger/?all=true` — Swagger UI

Same base URL as the app under test (localhost dev-proxy or the deployed env).

**Procedure when a UI action produces a 4xx/5xx:**
1. Note the endpoint + full query/body from Playwright MCP's network capture.
2. Fetch `/shared/openapi/?all=true` and locate that endpoint's parameter list.
3. Classify:
   - **Documented + params match declared required set** → response is
     expected-per-contract. The bug (if any) lives in the UI: wrong endpoint,
     wrong viewMode, missing query param, silent fallback to a public endpoint
     for an authenticated user, no redirect for bare deep links.
   - **Documented + params satisfy the spec** but backend still returns 4xx/5xx
     → backend bug. Quote the spec row.
   - **Undocumented endpoint (spec silent)** → say so explicitly; classify by
     the response body's error text plus the calling code (grep
     `../EliteaUI/src` for the endpoint string, read the RTK-Query slice). The
     `public_application` vs `application` split in `applications.js` is the
     canonical example — bare `/pipelines/all/{id}` without `?viewMode=owner`
     silently hits the public endpoint, which returns 400 for owner-only
     resources; the backend is correct, the UI defaults wrong.

**Verdict must quote either the spec parameter row or the calling-code line** —
"the API returned 400" is not a classification, it's an observation. (Origin:
canonical question #512, 2026-07-22 — the first-pass verdict missed the
public/private endpoint split because it stopped at the status code.)

## Every role — screenshot evidence ATTACHES, never local paths

**The rule is positive, not a blocklist: ANY local path OR bare `.png` filename
in an issue/comment must be uploaded + embedded.** This covers *every* on-disk
form — `.playwright-mcp/…`, `automation/screenshots/…`, `test-results/screenshots/…`,
**and a naked `ELITEA-1933-step-08-tool.png` with no path at all**. Don't reason
"my path isn't in the forbidden examples" — if a reader on GitHub can't click it
and see the image, it isn't evidence (the #51/#526/#595 anti-pattern: local paths
and bare names shipped to the tracker where nobody but the author can open them).
When an issue/comment cites a screenshot, UPLOAD it and embed it inline:

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

## Every role — NO git worktrees for regular work (operator ruling 2026-07-24)

Plain branching, **one thing at a time**, no concurrent checkouts. Never create a
`git worktree` in ordinary analysis, implementation, review, or promotion —
**only on an explicit human ask.**

**→ `.agents/workflow.md` § No git worktrees** is the single source: the rationale
(a confirmed-twice hazard, PRs #608/#693) and the replacement table for every
"I need a worktree" moment — none of which needs a checkout.

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

- **You choose the fidelity of the whole case — nobody downstream re-opens it.** The
  implementer builds what the AFS specifies and the reviewer triangulates against the
  AFS, so a substitution you design is invisible to every later gate (all three
  artifacts agree). Decide it deliberately, per `.agents/testing.md` § Fidelity policy.
- **A substitution is never a way to make a case tractable.** Determinism, speed,
  fixture cost and LLM variance are *reasons to want* one — they are not authority to
  take one. If the case's observable cannot be produced by the real system, the AFS is
  `blocked` (§ Blocked Steps naming exactly what could not be produced), and the lead
  routes it to a human. Convenience never converts into `ready-for-automation`.
- **Any substitution you do spec requires an AFS § Fidelity Declaration** — one row
  per substitution: what is substituted, transit-or-terminal, and the authority
  (quoted case line for a simulation case, or "transit only" with the real observable
  named). Terminal substitution with no quoted case line must not be written into an
  AFS at all.
- **Cost arguments belong in the declaration, not in the verdict.** "Coaxing the live
  system into this state is expensive/nondeterministic" is exactly the sentence that
  should trigger the `blocked` route, not justify a workaround.
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

- **An AFS specifying a terminal substitution is NOT executable — it is returned.**
  The AFS is your work order for *what* to assert, not a waiver of
  `.agents/testing.md` § Fidelity policy. If the AFS tells you to fabricate the very
  thing the case came to observe, and the case text does not ask for simulation,
  return it to the lead (`needs-analyst-rerun`-shaped) instead of building it. This is
  the mirror of the existing rule that you may not amend a testid request *away* —
  here you may not build a fidelity violation *in*.
- **Self-check before handoff (same discipline as the locator grep):** run
  ```bash
  git diff <base>...HEAD -- automation/ | grep -nE '^[+].*(\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\()'
  ```
  and PASTE the output in the Run Report. Empty output is the evidence; a missing
  paste is a gap. Each hit must be justified in the Run Report as transit-only or
  case-authorised (quote the case line).
- **Declare in the docstring, not only in the AFS.** Any substitution the test
  performs gets one line in the test docstring naming what was substituted and why —
  the next person reads the test, not the AFS.
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

- **Provenance check — ask of every asserted observable: WHAT PRODUCED THIS VALUE?**
  Your standing checks verify that an assertion *exists*, is *strong*, and *matches
  the AFS*. None of them asks where the value came from — a fabricated payload
  satisfies all three, and typically scores *better* (exact-equality assertions,
  perfectly deterministic). This check is the missing axis. Mechanical half, run on
  every PR and PASTE command + output (or explicit "0 hits"), same discipline as the
  locator grep:
  ```bash
  git diff <base>...HEAD -- automation/ | grep -nE '^[+].*(\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\()'
  ```
  A hit is COMPLIANT only if one of these holds, and you say which:
  1. **Case-authorised** — the TMS case text asks for simulation; quote the line.
  2. **Transit only** — the substitution merely reaches the step under test, and the
     case's own observable is still produced by the system; name that observable.
  3. **Timing control** — a *real* response delayed to expose a transient state.

  Anything else is **`CHANGES_REQUESTED`**, including a substitution the AFS
  specifies — *"the AFS said so"* is not a disposition. An AFS that authored a
  terminal substitution is the classic triangulation blind spot: all three artifacts
  agree and all three are wrong (row 1 of the triangulation table green-lights it).
  Judge fidelity against the **TMS case**, which is the upstream contract.
- **Do not let a declaration close the question.** Per § declared-improvisation
  protocol, a declaration cannot authorise a terminal substitution or any change to
  *what* is verified. A well-argued explanation for a forbidden choice is still a
  forbidden choice — verify the reasoning, then block anyway and say why.
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
  whose VALUE flips as component state changes on the SAME live element
  (`data-testid={isExpanded ? A : B}` on an element that expands in place), a
  feature-scoped testid hardcoded in a shared component (`src/components/`,
  `src/[fsd]/shared/`), or a `dataTestId`-style prop name is `CHANGES_REQUESTED`.
- **Same-element conditional pair check (canon ruling #277, 2026-07-22).** A
  `data-testid={cond ? A : B}` on a single JSX node where `cond` is a per-mount
  prop discriminating two mutually-exclusive JSX renders (e.g. `isOverflow` on
  `CardTagSectionItem` — the same component renders EITHER a real tag chip OR
  a "+N" overflow badge, never one that becomes the other) is distinct from
  the PR #581 anti-pattern and MAY be compliant. Exactly two shapes pass:
  (a) only the used branch is named, the other is `undefined`; OR (b) both
  branches are named AND both are referenced by locators on the test's
  executed code path — the untested branch via an absence assertion
  (`to_have_count(0)`/`not_to_be_visible()`) on the elements the test
  exercises. A documentation-only justification (docstring / AFS PROVENANCE
  row explaining why the untested branch exists) is NOT compliant on its own
  — `CHANGES_REQUESTED`. Absence assertions are caught by the existing
  mechanical grep (they use `.locator(`/`get_by_*` the same as positive
  assertions), so no new grep is needed.
- **Zero-functional-impact check on any EliteaUI JSX in the diff (origin: EliteaUI PR
  #753, 2026-08-11).** A new DOM node, a replaced MUI built-in, a new/moved hook call,
  a render-prop form change, or product state frozen into `useState` — added in order to
  host a testid — is `CHANGES_REQUESTED`. Mechanical check: run the three Step-5.5 greps
  from `add-data-testid` § Step 5.5 on the PR diff and paste command + output (or explicit
  "0 hits") per the existing reviewer paste discipline:
  ```bash
  git diff origin/main...HEAD -- src/ | grep -nE '^\+.*\buse(State|Effect|Memo|Callback|Ref)\('
  git diff origin/main...HEAD -- src/ | grep -nE '^\+.*<(Box|div|span|Fragment)'
  git diff origin/main...HEAD -- src/ | grep -nE '^-' | grep -vE 'testid|TestId'
  ```
  A hit is a blocker unless the commit body names the mandatory-plumbing exception
  (`add-data-testid` § Mandatory-plumbing exceptions) and explains why it was unavoidable.
  An undeclared hit is a violation (§ Declared-improvisation protocol).
- **Declared improvisations** (see § Every role): verify the reasoning and say so
  explicitly in the verdict; if sound, APPROVED + recommend the canon addition —
  do not block solely for the gap the canon itself left.
- "Selector stability per testing.md" in the review checklist means **this**
  policy, not the skill's example ladder.

## Orchestrator slot (test-automation-lead)

- **NEVER prescribe a technique that substitutes the system under test.** Your
  dispatch prompt is the strongest signal in the pipeline: an IC treats it as settled
  and the reviewer ends up judging work *you ordered*, which removes the last
  independent axis. Suggesting a mock/stub/injection to "sidestep a live-data
  dependency" is how the 2026-08-14 drift began (three dispatches on one batch).
  Name the *observable* and the *constraint*; let the analyst determine fidelity, and
  route a `blocked` return to a human instead of unblocking it with a technique.
- **Dispatch-prompt contract:** every implementer and reviewer dispatch prompt MUST
  carry the fidelity line verbatim alongside the locator line: *"Fidelity policy:
  the observable must be produced by the system (`.agents/testing.md` § Fidelity
  policy). Terminal substitution — fabricated responses, injected state, replaced
  clients — is CHANGES_REQUESTED unless the case text asks for simulation."*
- **At batch close, resolve every declaration.** Each declared improvisation in the
  run must have produced a `question` card proposing the canon addition (§
  declared-improvisation protocol, limit 2). An unresolved declaration is not a
  closed batch — it is a pattern about to become doctrine.
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
