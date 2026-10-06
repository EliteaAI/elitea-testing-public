# Role Overrides — project-specific hard rules (this file wins)

_This is the bundle's designed override channel. Where anything here conflicts
with a skill's **defaults or examples** — including the
`test-automation-workflow` "UI example" locator ladder — **this file wins.**
Seeded by scout 2026-07-14 after the framework-alignment audit. **Locator policy
rewritten 2026-10 (dev-targeted factory):** the factory builds against DEV with a
ladder and never touches EliteaUI; the `testid-migrator` owns testids. This
supersedes the PR #23 "testid-only" ruling and every memory/AFS built on it._

> ⚠️ **Delivery: this file reaches agents ONLY via the `@`-import block in
> `CLAUDE.md`.** The bundle's hook *can* inject it, but this project sets
> `SDLC_SHARED_DOCS=__none__` (`.claude/hooks/sdlc-skills/config.sh`) because the
> hook's ~10 KB `additionalContext` cap truncated the shared docs. **Removing
> `@.agents/role-overrides.md` from `CLAUDE.md` silently deletes the override
> channel** — every hard rule below stops reaching every agent, with no error.
> Verified 2026-08-10 (scout): the hook injects only per-role memory
> (`RULES.md` + `MEMORY.md` + `project_briefing.md`), never this file.

## Every role — locator policy (the #1 override)

**The factory targets the DEV env as deployed and uses a locator LADDER; it never
adds testids and never touches EliteaUI or localhost:5173.** The ladder is:
existing testid on DEV → `role`+`name` → `label` → stable `css` → declared `xpath`,
every non-testid declaration carrying `suggested_testid=`. The
`test-automation-workflow` example ladder (which puts role first and allows text)
does **not** apply — this one does.

**→ The full policy is `.agents/testing.md` § Locator policy — the single source,
and the authority the skill itself defers to. Mechanics (enforced at import time)
are in `.claude/rules/page-objects.md` § Locator Strategy.** It covers: the two
processes and their owners (factory vs `testid-migrator`), the rung order, the
class-level-only rule, the mandatory `suggested_testid=` hint, the positional
ban, the locator-debt metric (`scripts/locator_inventory.py scan`), and the
testid canon (#581 state attributes, #277 pairs, #511 scope, shared-component and
connected-repo rules, #579 third-party internals) — which now binds **only the
migrator**, the sole role that adds testids.

**Precedence:** any memory, briefing, AFS, skill reference or historical ledger
entry dated before 2026-10 that says "testid-only", "testid needed ⇒ add it",
"run against localhost:5173" or "coverage = testid presence" is **superseded** for
factory work. Pre-ladder raw handles in `automation/pages/` (#25/#42) remain debt,
never precedent.

The per-slot consequences are below (§ Analyst / § Implementer / § Reviewer slot).

## Every role — fresh ground truth (hard rule)

Any verification against `origin/*` refs — branch-state checks, the migrator's
"is this testid on main" (`locator_inventory.py check-ui-ref`) — is preceded by `git fetch origin` in that
repo, **in the same command block**. A verification against a stale clone is not a
verification (#19 rework shipped a false "0 of 12 on main" row exactly this way;
truth was 5/12, added by the UI team's own EL-5400). Name the ref you checked and
PASTE the command output.

## Every role — declared-improvisation protocol (canon gaps)

When the canon has NO pattern for your case: pick the most spirit-compliant option
AND declare it explicitly — in the Run Report and the PR description — as a
proposed pattern with reasoning ("no sanctioned shape for X; chose Y because Z").
A DECLARED improvisation is a canon-gap escalation: the reviewer verifies the
reasoning, the auditor reports it as a `question` — it can never solo-FAIL a
delivery. An UNDECLARED improvisation is a violation, full stop. (Origin: #19
FAIL-1 — a semantically-correct improvisation was indistinguishable from a
violation because it was silent.)

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
6. **Read the source — this is the decisive step.** Read it as DEV ships it —
   `cd ../EliteaUI && git fetch origin && git grep -n "<placeholder or label text>" origin/main -- src/`
   (read-only; never edit, never check out — the factory does not work in that
   repo) → `git show origin/main:<path>` → `onChange` handler filtering = live; `onKeyDown` + `Enter` /
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

Same base URL as the app under test — the DEV env (`https://dev.elitea.ai`).

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
- **Session start: refresh the DEV storage state** —
  `cd automation && ../.venv/bin/python scripts/dev_storage_state.py` — before the
  first browser call. The MCP runs `--isolated --storage-state
  .playwright-mcp/dev-storage-state.json`; a stale file lands you on the Keycloak
  login page. Never type credentials into the browser, never print the file.
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

- **Handles Reference = one row per element, verified on DEV at analysis time**
  (Playwright MCP snapshot/DOM of `https://dev.elitea.ai`): `rung` | `handle` |
  `suggested_testid` | `provenance`. Provenance is `testid on DEV ✓` (rung 1 — use
  it) or `ladder — no testid on DEV` with the rung you verified **unique** on the
  page/scope the test uses. Name the hint as the testid would be named
  (`{section}-{element}-{type}`, call-site section, dynamic `-{}`).
- **Never spec a testid as work.** `testid needed: …` rows are retired — the factory
  does not add testids. A missing testid is a ladder rung + hint; the migrator picks
  it up from the ledger.
- **No positional handles in the AFS.** If the only way to reach an element is
  "the 3rd button" / "last item", say so as a `question` for the lead (it becomes a
  priority migrator row) rather than speccing a positional pick.
- **State is specced as an attribute/ARIA-state filter, never as a state-dependent
  handle** (`aria-expanded`, `aria-selected`, `disabled`, or a `data-*` attribute DEV
  already renders) — never `x-expanded` / `x-collapsed` variants.

## Implementer slot (test-automation-engineer)

- **Use the AFS rung; climb if DEV allows.** Take the Handles Reference row as the
  work order; if DEV now serves a testid for it, use `testid=` (rung 1 always wins).
  Never descend below the AFS rung "for now" — a lower rung than specified is
  escalated to the lead, not shipped.
- **Never touch EliteaUI** — no `add-data-testid`, no commits on
  `automation/testids`, no localhost runs. Your PR is the only artifact.
- Locators are class-level `LocatorDescriptor` / `OptionalLocatorDescriptor` /
  `ScopedLocator` fields (or UPPER_CASE `[data-testid="…"]` constants) ONLY — no
  `fallback=`, no `locator=`, nothing built in method bodies, no raw selector
  chained off an existing field, no positional picks. Every non-testid one carries
  `suggested_testid=` (import fails otherwise). Scoped/dynamic handles:
  `ScopedLocator(...).within(scope, *args)` per `.claude/rules/page-objects.md`.
- **Touching a legacy method that builds a locator inline?** Declare that handle at
  class level on the ladder as part of the change (unmanaged handles never grow).
- **Self-check before handoff:** run the reviewer's mechanical grep (below) on
  your own diff, plus `cd automation && ../.venv/bin/python scripts/locator_inventory.py scan`
  on the base and on your branch, and PASTE both in the Run Report (declared-total,
  non-testid and unmanaged-handles deltas). Unmanaged handles must not increase.
- **`locator_descriptor.py`'s `locator=`/`fallback=` params are LEGACY** — kept so
  old code imports; never valid in new code, whatever any docstring example shows.

## Reviewer slot (qa-engineer, fresh session)

- **Locator mechanical check on every PR** (ladder policy, `.agents/testing.md`
  § Locator policy):
  `git diff <base>...HEAD -- automation/pages automation/tests | grep -nE '^[+].*(get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|get_by_test_id|query_selector|page\.locator|\.locator\(|\.nth\(|locator=|fallback=)'`
  A hit is COMPLIANT only if it (a) passes a literal `[data-testid=` selector or an
  UPPER_CASE class constant whose definition is a `[data-testid=` string/template
  (one-hop check), or (b) is `.nth(i)` **enumerating every match** of a declared
  locator (a loop over its count) — never picking one. `locator=` / `fallback=`,
  any raw call in a spec, and any raw call in a method body are `CHANGES_REQUESTED`.
- **Declaration check (read every added `LocatorDescriptor(` / `ScopedLocator(`):**
  the rung matches the AFS Handles Reference (or is higher); a non-testid rung
  carries a well-formed, call-site-named `suggested_testid=`; `xpath=` has a
  `description=` saying why rungs 1–4 failed; no MUI generated/structural classes
  (`css-*`, `Mui*-root`) as a `css=` rung; no text that embeds user data, counts or
  the selected model. Import-time validation catches syntax; you catch judgment.
- **No EliteaUI in the diff.** A factory PR that changes or depends on a new
  EliteaUI testid is `CHANGES_REQUESTED` — that is migrator work.
- **Show your grep to the orchestrator.** Include the mechanical grep's actual
  command + output in the verdict you return to Tal — command (so scope/pattern
  is auditable) + result (hits verbatim, or explicit "0 hits / (no matches)" for
  empty). This is how Tal (and you) know it was really run on the full diff, not
  a weak subset — the #19 FAIL-2 lesson. (The delivery audit does NOT require this
  paste to survive into the tracker: the auditor re-runs the grep itself. It's
  reviewer discipline, not a tracker-artifact gate.)
- **Testid canon checks (#581 state-switched testids, #277 conditional pairs,
  shared-component scoping, `dataTestId` prop names, zero-functional-impact Step-5.5
  greps) apply ONLY when reviewing a `testid-migrator` batch** — see
  `.claude/skills/migrate-locators-to-testids/SKILL.md` § Review. Factory PRs carry
  no JSX.
- **Declared improvisations** (see § Every role): verify the reasoning and say so
  explicitly in the verdict; if sound, APPROVED + recommend the canon addition —
  do not block solely for the gap the canon itself left.
- "Selector stability per testing.md" in the review checklist means **this**
  policy, not the skill's example ladder.

## Orchestrator slot (test-automation-lead)

- **Dispatch-prompt contract:** every analyst, implementer and reviewer dispatch
  prompt MUST carry the line: *"Target: DEV (`https://dev.elitea.ai`, refresh
  `scripts/dev_storage_state.py` first). Locator policy: ladder — existing testid →
  role+name → label → stable css → declared xpath, every non-testid with
  `suggested_testid=`, class-level only, no positional handles
  (`.agents/testing.md` § Locator policy). Do not touch EliteaUI or localhost."*
  The dispatch prompt is the gate — put the policy where it cannot lose.
- **Closure records state verified facts.** The factory closure record has no
  testid/promotability row any more — it cites the merged PR and the **locator
  delta** (`locator_inventory.py scan` before/after, pasted) and confirms
  `sync-ledger` registered the new non-testid declarations as `raw` rows. Never
  copy the implementer's numbers — re-run the scan on `automation/base` after merge.
- Sync `automation/base` with `main` (test repo only) before dispatching the first
  case of a session. The EliteaUI half of `sync-base-branches` is the migrator's job.
- **Never dispatch `testid-migrator` from a factory batch** — it runs on request, in its
  own session (`.claude/skills/migrate-locators-to-testids`), on already-merged tests.
  When a migrator phase-A PR lands on `automation/base`, review it with a fresh
  `qa-engineer` per that skill's § Review — not the factory reviewer checklist.
- **Never dispatch `ui-test-orchestrator` or `failure-investigator`.** They are
  installed for the HUMAN team's direct use only — their flows bypass the pipeline's
  gates (AFS, fresh-session review, merge gate, closure record). Every stage they
  cover has a canonical owner in your pipeline.

## Testid migrator slot (testid-migrator, 2026-10)

The locator-migration agent (runs on request). Procedure: `.claude/skills/migrate-locators-to-testids/SKILL.md`.

- **The only role that adds testids or touches `../EliteaUI` / `../elitea_assistant`.**
  It follows the full testid canon in `.agents/testing.md` § Testid-migrator rules
  and the `add-data-testid` skill (Step 5.5 zero-functional-impact greps included).
- **Deployment gate:** a page-object declaration is swapped to `testid=` only for a
  ledger row in state `on-dev` — testid on EliteaUI `main` (after `git fetch origin`,
  same command block) **and** observed in the DEV DOM. Main is not DEV.
- **Behaviour-preserving only:** phase A diffs touch `automation/pages/**` + the
  ledger; specs, fixtures, conftest and assertions are out of bounds. A swap that
  turns a test red is reverted and reported, never "fixed" in the spec.
- **Every ledger move goes through `scripts/locator_inventory.py`** (`sync-ledger`,
  `mark … --evidence`) — never a hand edit of `ledger.json`.
- Testid commits land on `automation/testids` and are pushed (merge, never rebase /
  force-push); a human cherry-picks to `main`. No EliteaUI `main` PR.
