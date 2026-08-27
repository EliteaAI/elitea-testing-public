# A new testid inside a CI-red fix is self-defeating

**Learned:** 2026-08-27 (ELITEA-1866 / #1815, toolkit-detail drift repair)

## The situation

Repairing a test that was red in GHA against `dev.elitea.ai`. Review correctly found
that a case-mandated observable (a guidance message) had been **relocated, not removed**
— so the honest fix was to restore its assertion. The reviewer's preferred remedy was
`add-data-testid` + assert, per `.agents/testing.md` § Locator policy ("a missing testid
is work to do, not a reason to rung down").

## Why that remedy was wrong HERE

A new testid is born on `automation/testids` and reaches EliteaUI `main` only by a
**human cherry-pick**. So asserting on it makes the test:

- **green on localhost** (dev server runs `automation/testids`)
- **red on `dev.elitea.ai`** until a human promotes it and it deploys

In a card whose entire purpose is to clear a `dev.elitea.ai` red, that trades a
documented coverage gap for a **new deployed-env red**. Net negative.

And the escape hatch is closed: adding the testid **without** the assertion is barred by
canon ruling #511 (unreferenced testids inflate the presence-based coverage metric).

## The rule

> Before ordering `add-data-testid` inside a **repair** of an already-promoted test, ask
> where the fixed test will RUN. If it runs against a deployed env, a new testid is a
> promotion gap, and a promotion gap in a repair is a regression.

Correct disposition: **tell the truth, change no coverage, file a card that owns
testid + assertion + promotion sequencing together** (here: #1857). The gap becomes
*visible* instead of *explained away*, and nothing goes red.

## The generalisation

The locator policy's "missing testid ⇒ add it" is stated for **new coverage**, where the
test and the testid ship together and localhost is the gate. It does not carry unchanged
into repairs of promoted tests, where the test already runs somewhere the testid isn't.
Two policies (locator policy, promotion ordering) that never conflict on the forward path
**do** conflict on the repair path — and promotion ordering wins, because it is the one
with a red-CI consequence.

The reviewer conceded this himself: *"I named the policy without carrying it through to
the promotion sequence."* Worth expecting: a slot reasoning purely from the locator rail
will reach the wrong remedy here, so the ORCHESTRATOR has to supply the promotion axis.
