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
- **The surrounding code is NOT precedent.** `automation/pages/` contains ~350
  pre-policy raw handles (tracked tech debt, issues #25/#42). Matching the
  neighbors is how the debt grew; never cite existing code to justify a new raw
  handle.

## Analyst slot (qa-engineer)

- The AFS **Handles Reference must list testids as the only primary handles.** An
  element without one is specced as `testid needed: {section}-{element}-{type}` —
  never "resolve by accessible role/name", never a CSS/role handle as primary.
- Do not soften a testid demand into a MINOR defect or a note; it is implementer
  work, and the AFS is its work order.

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
  use UPPER_CASE `[data-testid="…"]` string constants per
  `.claude/rules/page-objects.md`.

## Reviewer slot (qa-engineer, fresh session)

- **Any non-testid handle ADDED in `automation/pages/` or `automation/tests/` is
  `CHANGES_REQUESTED`.** Not a nit, not a non-blocking tech-debt note, not waived
  for neighborhood consistency. Mechanical check on every PR:
  `git diff <base>... | grep -nE '^[+].*(get_by_role|get_by_label|get_by_text|get_by_placeholder|get_by_title|get_by_alt_text|get_by_test_id|query_selector|page\.locator|\.locator\()'`
  (`get_by_test_id` included: inline Playwright calls are also banned — locators are
  class-level `LocatorDescriptor` fields)
  — every hit must be a `[data-testid=` selector or it blocks.
- "Selector stability per testing.md" in the review checklist means **this**
  policy, not the skill's example ladder.

## Orchestrator slot (test-automation-lead)

- **Dispatch-prompt contract:** every implementer and reviewer dispatch prompt
  MUST carry the line: *"Locator policy: testid-only (`.agents/role-overrides.md`
  + `.agents/testing.md` § Locator policy). The workflow skill's example ladder
  does not apply. New non-testid handles are CHANGES_REQUESTED."* The dispatch
  prompt is the gate — put the policy where it cannot lose.
- **Closure records state verified facts.** Before writing the promotability row,
  check it: which testids the case's tests use (`grep` the diff), and which of
  those exist on `EliteaAI/EliteaUI` **main** vs only on `automation/testids`
  (`git grep` both). Never copy the AFS/implementer's claim — #35/#36/#37 shipped
  false "fully promotable" rows exactly that way.
- Run `sync-base-branches` before dispatching the first case of a session, not
  after the batch.
