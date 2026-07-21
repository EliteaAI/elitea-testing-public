---
name: AFS Axis 2 claims need a grep, not just row presence
description: An AFS Coverage Map row can name a check ("console-error check") as its justification for an `asserted` disposition while the shipped test contains zero code implementing that check — the row existing and citing Axis 2 isn't proof the assertion exists.
type: feedback
---

PR #693 (ELITEA-2095): the AFS's Coverage Map Pass-criteria row said `asserted`,
justified as `"console-error check (Axis 2) + all above"`, and the Axis 2 list
itself said "Console-error check after every navigation/click — *added*...
confirmed clean (0 errors)". Reads as a real, shipped assertion. It wasn't:
`grep -n "console\|page\.on(\"console\|ConsoleMessage" <test file> <page object>`
returned zero hits in both files, and there was no autouse conftest fixture
doing it globally either. What actually happened: the analyst verified "no
console errors" *manually* during exploration and wrote it up as an Axis 2
addition, but the implementer never translated it into `page.on("console", ...)`
+ an assertion — and neither the implementer's Run Report/PR self-checks nor
the AFS amendment pass caught the gap, because the Coverage Map row itself
looked complete (it had a row, it named a source, it said "asserted").

**Durable technique**: when a Coverage Map row's "Asserted where" column names
something as generic as "console-error check" or "side-channel discipline",
don't accept the row's existence as proof — grep the actual test file (and any
page-object methods it calls) for the concrete mechanism (`page.on("console"`,
`console_messages`, `ConsoleMessage`, or whatever the framework's equivalent
is) before ticking that row off. This is the same "asserted row whose
assertion isn't in the code is CHANGES_REQUESTED" standing rule from
test-automation-workflow's Reviewer slot section — but it's easy to satisfy
the letter of "the row exists and cites an Axis 2 bullet" while missing that
the bullet itself was never implemented. Treat every row's citation as a claim
to verify mechanically, not a citation to trust.

Secondary, same-PR finding worth generalizing: a page-object method
(`click_first_other_conversation()`) silently required "at least one OTHER
pre-existing conversation in the target project" to not raise
`AssertionError`, and the implementer's own inline code comment confirmed this
was load-bearing (not incidental) — yet the AFS's Test Data section (which is
supposed to classify every datum into reuse-existing/generate-per-test/
generate-shared-with-cleanup) never listed it. When a new page-object method
depends on ambient environment state to avoid throwing, check whether that
dependency is named anywhere in the AFS's Test Data inventory — an implicit
dependency discovered only by reading the method's own guard clause is a real,
unclassified flake risk, not a nitpick.
