---
name: A [FIX] card's auto-generated body can instruct a policy violation
description: The CI-failure-intake generator writes generic Playwright advice into [FIX] card bodies — it can directly contradict a hard project rule; override it explicitly in the dispatch, don't just silently ignore it
type: feedback
aliases: [fix card locator instruction, regular locators instead of testid, auto-generated card instructions, test failure intake pipeline]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`[FIX]` cards are auto-filed by the "Test Failure Intake Pipeline" from a CI run.
Their body includes a generic "Work Scope / Instructions" block written by the
generator, not by a human who knows this project's canon. Issue #2049
(ELITEA-1898) carried: *"3. Use regular locators — When fixing tests, use
standard Playwright locators (role, text, label) instead of data-testid
attributes."*

That is the exact opposite of this project's hard rule: locator policy is
testid-only, no fallback ladder at all (`.agents/role-overrides.md`,
`.agents/testing.md` § Locator policy). A dispatch that quotes the card body
verbatim — or an implementer that follows it because "the task said so" —
ships a `CHANGES_REQUESTED`-guaranteed diff, or worse, merges a role/text
handle that's invisible to the testid-presence coverage metric.

## The move

Read the full card body before dispatching, not just the failure summary.
When its "Instructions" section conflicts with project canon:

1. **State the override explicitly in the dispatch prompt** — name which line
   of the card is wrong and which project doc wins. Don't just silently do the
   right thing; a silent override is indistinguishable from having missed the
   instruction entirely if anyone later checks.
2. **Say so in the work-log/closure comment too** — so a human skimming the
   card later isn't confused about why the delivered fix doesn't match the
   card's own stated instructions.
3. The rest of a `[FIX]` card's boilerplate ("do not trigger workflows",
   "work locally") is usually fine and matches the normal local loop — only
   the locator-strategy line has been seen contradicting canon so far. Check
   each instruction against `.agents/role-overrides.md` / `.agents/testing.md`
   rather than assuming the whole block is either all-trustworthy or
   all-suspect.

## Why this keeps happening

The generator is downstream of a generic Playwright-test-fixing template — it
has no visibility into a project's own locator ruling (here: PR #23, "Enforce
testid-only locators"). Expect this on any project whose canon deviates from
generic framework advice, not just this one line, on any future auto-filed
card from this pipeline.

Related: [[sibling_fix_cards_can_have_different_root_causes]]
