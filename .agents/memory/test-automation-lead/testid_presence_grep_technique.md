---
name: Proving a testid is present — grep technique
description: EliteaUI wires testids through object literals, forwarded props and template literals, so no single grep shape proves presence or absence; bare-substring first, read the matched line, component-scope reused names, and trace composed testids to their fragment.
type: feedback
---

## Rule

Presence is proven by reading the construction site. One grep shape never suffices.

- **Two-stage, in this order** (now canon in `.agents/workflow.md`, updated
  2026-07-23 — the old literal `data-testid="$t"` snippet is **superseded**):
  stage 1 `git grep -n -- "$t" <ref> -- src/`; stage 2 filter to
  `(data-testid|testid.*=.*$t)`. The literal form false-negatives on
  `'data-testid': 'x'` object literals, `inputProps`/`slotProps`/
  `SelectDisplayProps`, `buttonTestId="x"`-style prop threading (literal and
  `data-testid={…}` may be in different files), and `data-testid={cond ? … }`.
- **Always `-n`, always read what matched.** Bare substring over-matches:
  prefix collisions (`entity-card` hitting `data-testid="entity-card-name"`) and
  import paths (`…/generate-skill-modal'`). Structural, not rare — the
  `{section}-{element}-{type}` convention guarantees prefix families. Confirm a
  suspicious YES with the exact `data-testid="$t"` form for that testid only.
- **Component-scope any reused testid NAME.** The same string can be on `main`
  in a *different* component than the test drives:
  `git grep '"<t>"' origin/main -- '*UsersParticipantDropdown*'`. Name presence
  anywhere is not promotability.
- **Both quote prefixes** for template forms: `git grep -e '"<t>' -e '` + backtick + `<t>'`.
- **Composed testids never exist as a literal string.** DotMenu needs a 3-hop
  trace: locator literal → the `id="agent-actions"` / `key: 'delete-agent'`
  fragment at the call site → grep the FRAGMENT per ref. Same for
  `${columnTestIdPrefix}-column-header-${field}` (grep the prop name) and
  `${dataTestId}-combobox`.
- **Empty on BOTH refs ≠ absent.** Escalate: bare grep → find the owning
  component → `git diff origin/main origin/automation/testids --stat -- <file>`.
  **Zero diff on the owning file ⇒ pre-existing shared mechanism, already
  promotable, blocked on nothing.** Only a non-zero diff justifies a `git log -S`
  blocker trace.
- **Calibrate before trusting.** Sanity-check the technique against a
  known-true/known-false testid from an already-merged sibling before running it
  on a new case.
- **A contradiction with the AFS/implementer's "already exists" claim is a
  methodology tell, not a gap** — re-check the grep before writing "gap".

## Seen 6×

- #26/ELITEA-1735 — `slotProps` object literal + ternary; literal grep said no/no while the test ran green.
- #62/#66/#128/#162 — runtime-composed: `${id}-menu-button`, `${columnTestIdPrefix}-…`, `buttonTestId` forwarding, MUI `SelectDisplayProps`.
- #73/#95/#166/#175/#262 — `workflow.md`'s literal snippet under-reported 5 deliveries (canon issue #553; canon now fixed).
- #30/EliteaUI#544, #101/ELITEA-1988 — bare-grep false positives: prefix collision, then an import path.
- #370/ELITEA-2167 — reused name present on main in a *different* component; caught by a reviewer, not by me.
- #150/ELITEA-1892, #67/ELITEA-1889 — DotMenu 3-hop; zero-diff-on-owning-file proved "already promotable".

See also: promotability_grep_false_negative.md ·
promotability_grep_false_positive_prefix.md ·
promotability_grep_must_be_component_scoped_and_catch_prop_template_testids.md ·
testid_grep_quoting_gotcha.md · dynamic_testid_promotability_grep.md ·
dynamic_testid_promotability_needs_3hop_trace.md ·
promotability_generic_mechanism_not_gated_by_testid_pr.md
