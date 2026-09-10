---
name: A DEV-only locator timeout can be a PROMOTED testid whose value main overwrote — diff the value expression across refs before dispatching anyone
description: Two git diffs in the UI repo root-cause this class offline; and check the chronology, because "ours never promoted" and "ours promoted then clobbered" invert which canon rule applies
type: feedback
aliases: [DEV only red, testid value divergence, chat-participant-row, promoted testid overwritten, locator timeout on DEV, value expression not name]
tags: [area/test-repair, area/branching, area/ci, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

## The class

A `[FIX]` card whose signature is a **locator timeout on a testid that plainly exists**
(the name greps `YES` on both refs), red **only** on `dev.elitea.ai`: the two refs render the
same testid **name** with a different **value expression**. localhost serves
`automation/testids` and passes; DEV serves `main` and can never match.

`sync-base-branches`' testid-loss guard **cannot see it** — it diffs testid *names*, which are
unchanged, and correctly reports `0 lost`. A testid can break without its name changing.

## Root-cause it offline — no browser, no analyst, two commands

```bash
cd ../EliteaUI && git fetch origin
git diff origin/main origin/automation/testids -- <the component file>
git show origin/main:<helper file>        # what each expression actually returns
```

#2142 / ELITEA-1793: `ParticipantNormalCard.jsx` renders `chat-participant-row-` +
`getChatParticipantUniqueId(participant)` on `automation/testids` (→ `application_9249_399`)
but + `participant.id ?? participant.entity_meta?.id` on `main` (→ `9249`), while the page
object builds the composite form on both refs. Proven before any dispatch.

## Then check the CHRONOLOGY — it picks the canon rule, and the reflex is wrong

I read this as *"our change never got cherry-picked"* and was **wrong**. It **had been
promoted**; a UI-team refactor overwrote it in passing (`b4d00fcc`, EL-6405 — an unrelated
commit subject that split one component in two), and our next sync re-added it.

```bash
git show <refactor-sha>^:<file> | grep data-testid    # what main had BEFORE the refactor
```

Per `.agents/workflow.md` § Divergence rule:

| Chronology | Rule | Resolution |
|---|---|---|
| Ours, never promoted | — | human cherry-picks `automation/testids` → `main` |
| Ours, promoted, then clobbered | **bullet 1** (take main's structure, re-add ours) | `automation/testids` is **correct**, `main` is **degraded** |
| UI team deliberately renamed it | **bullet 2** (favour `main`) | fix our `LocatorDescriptor` |

Bullet 2 is the reflex and it is wrong for the middle row. Tell for "accident": the helper is
still used elsewhere in the same feature on `main`, i.e. `main` contradicts itself.

## Why this parks rather than delivers

The fix is one line in a repo where promotion to `main` is **human-only** (§ Testid flow,
2026-07-16), and the correct expression is *already* on `automation/testids` — nothing for an
implementer to build. Test-side alternatives either forfeit a real property (ratifying the bare
id makes agent `N` and pipeline `N` collide, and those methods already take
`entity_type="pipeline"`) or settle the open canon question by routing around it — above the
§ Declared-improvisation **ceiling**. File a `question` card with options + recommendation, park.

## Count the LATENT casualties, and enumerate by METHOD CALL

Exposure differs per ref *and* per marker. On #2142 `origin/main` had 2 affected specs — but
one carried `pytest.mark.new`, which CI filters out, so **it was broken with no signal at
all**; that marker was the only reason CI showed one red instead of two.
`origin/automation/base` had 4, so the bill grows at the next promotion.

`git grep -l <method names> origin/<ref> -- automation/tests/` — never enumerate by the
spec's apparent subject: a chat-participant method breaks specs filed under *skills*.

Related: [[main_and_base_can_carry_different_variants_of_one_spec]] · [[ci_red_check_base_for_an_existing_fix_first]] · [[three_of_three_within_one_invocation_is_not_determinism]] · [[testid_promotability_grep_misses_multiline_ternary_composed_values]]
