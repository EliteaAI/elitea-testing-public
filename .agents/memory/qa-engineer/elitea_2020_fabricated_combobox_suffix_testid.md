---
name: ELITEA-2020 "-combobox" suffix testid — real, but only on automation/testids (not fabricated)
description: agent-version-selector-trigger-combobox DOES render (SelectDisplayProps in SingleSelect.jsx, dynamically suffixed) — but only on automation/testids, not main. Grepping the literal concatenated string always returns 0 hits by construction; that is not proof of non-existence.
type: feedback
---

**Self-correction, 2026-08-07 re-review round.** My own prior finding on this
case (below, preserved for the record) was WRONG on the "fabricated" claim,
though the DIRECTIVE it gave (use `agent-version-selector-trigger`, no
suffix) was still the right call for a different reason — see "What's
actually true" below.

## What's actually true (fresh `git fetch origin` + `git grep`, both refs)

`SingleSelect.jsx` (the shared MUI wrapper `VersionSelect.jsx` composes)
DOES contain `-combobox`-suffixing logic:

```
data-testid={dataTestId}
SelectDisplayProps={dataTestId ? { 'data-testid': `${dataTestId}-combobox` } : undefined}
```

`SelectDisplayProps` is a real MUI `<Select>` prop — it lands on the
"display" div MUI renders internally (the actual `role="combobox"` element,
confirmed in `node_modules/@mui/material/Select/SelectInput.js:472,486`),
which is a DIFFERENT DOM node from the outer `Input`/`OutlinedInput` wrapper
that receives the plain `data-testid={dataTestId}` prop (spread via
`...other` in `Select.js`). So the shared component genuinely renders TWO
distinct `data-testid`-bearing elements, one nested inside the other — the
original "renders TWO testids" claim this case's AFS made was accurate, not
fabricated.

**Why it still greps as zero hits — this is the actual lesson**: the
`-combobox` suffix is built via a template literal at render time
(`` `${dataTestId}-combobox` ``), so the exact concatenated string
(`agent-version-selector-trigger-combobox`) will NEVER appear as a literal
in source — grepping for it is checking the wrong thing. This is the same
"dynamic testid" shape `.agents/testing.md` § Locator policy already
documents (data-parameterized testids), just parameterized by the BASE
TESTID rather than by test data. The correct check is to grep for the
*mechanism* (`SelectDisplayProps`, or the substring `-combobox` — which DOES
appear literally in the template) — not the fully-instantiated string.

**And it's ref-specific**: `git grep -n -- "-combobox" origin/automation/testids -- src/`
→ 1 hit (`SingleSelect.jsx:661`). `git grep -n -- "-combobox" origin/main -- src/`
→ 0 hits. The `SelectDisplayProps` line is on `automation/testids` only, not
yet promoted to `main` — a `needs-adding`→`on-automation/testids only`
PROVENANCE case (`.agents/role-overrides.md` § Analyst slot), not a
non-existent testid.

## Why `agent-version-selector-trigger` (no suffix) was still the right fix

Even though the `-combobox` variant is real, the NO-suffix testid is the
better choice for THIS case, for a reason unrelated to existence:
`agent-version-selector-trigger` is confirmed on **both** `main` and
`automation/testids`, and it's the one `AgentDetailPage.get_version_selector_value()`
already uses across many merged, passing tests (ELITEA-1888/1889/1890/1891/1892
and others) — reading `.text_content()` off the OUTER wrapper still returns
"base" because DOM `textContent` includes descendant text (the inner
`-combobox` div's text included). So the fix's OUTCOME was correct; only its
stated JUSTIFICATION ("no `-combobox`-suffix derivation logic exists
anywhere", "the prior claim was fabricated") was false, and shipped into 4
permanent artifacts (AFS, `_surface.md`, page-object docstring, and a
cross-case shared memory addendum) as verified fact.

## The check that actually catches this class of case

Before declaring a claimed testid "fabricated" from a grep-zero-hits result,
ask: could this string be TEMPLATE-CONSTRUCTED rather than literal? If the
claimed testid is `<known-real-testid>-<suffix>` or
`<prefix>-<known-real-testid>`, grep for the KNOWN-REAL base string plus
`SelectDisplayProps`/template-literal patterns (`` `${ `` near a testid
prop), not just the exact concatenated form — and check BOTH `main` and
`automation/testids` separately (never collapse "checked both, zero on
either" into one claim without pasting both grep outputs separately, the way
the closure-record two-stage-grep discipline already requires elsewhere).

---

## Original (2026-08-07, round 1) — preserved, largely superseded above

Reviewing ELITEA-2020 (PR #1305), the AFS / `_surface.md` digest / page-object
docstring all claimed `ApplicationVersionSelect.jsx`'s VERSION selector
"renders TWO testids": the outer `agent-version-selector-trigger` (called a
"non-interactive wrapper") and an inner `agent-version-selector-trigger-combobox`
(the actual `role="combobox"` element, claimed as "confirmed live"/"on-main ✓").
I flagged this as fabricated based on a literal-string grep returning zero
hits on both refs, and directed the implementer to switch to the no-suffix
testid, citing `AgentDetailPage.get_version_selector_value()` as precedent.
The directive was right; "fabricated" was wrong (see above) — the literal
grep cannot detect a template-constructed suffix, and the `-combobox` variant
does exist, on `automation/testids`.
