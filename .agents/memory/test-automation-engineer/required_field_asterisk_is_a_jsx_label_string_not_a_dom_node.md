---
name: Required-field asterisk is a JSX label STRING, not its own DOM node — declared-gap narrowing beats testid restructuring
description: SecretField.jsx/ToolBaseProperty.jsx's required-field "*" indicator is a literal character concatenated into a label prop/string (two different branches depending on tooltipDescription), driven by the SAME `required` boolean that gates Save — no sanctioned shape exists to testid it without restructuring a component shared by every secret/token field app-wide; narrowing the AFS Coverage Map row to the asserted half plus a declared-gap note is the correct, reviewer-sanctioned fix, not a new testid.
type: feedback
---

ELITEA-1978 third implementer dispatch (fix round on PR #1008). Reviewer
finding: AFS Coverage Map Row 6 claimed BOTH "Save stays enabled" AND "no
asterisk next to Access Token" were asserted at Step 8, but the code only
asserted the Save-gating half — the asterisk half was never independently
checked, and the gap wasn't disclosed anywhere (no AFS narrowing, no PR-body
mention).

**Source trace before picking a fix:** `ToolBaseProperty.jsx` passes
`required={required}` into `SecretManagementInput`/`SecretField.jsx`.
`SecretField.jsx` has TWO label-rendering branches:
- `tooltipDescription` set → `<Box component="span">{label}{required ? ' *' :
  ''}</Box>` (plain JSX children, a `<Box>` wrapper exists but the asterisk
  itself is just a template-literal-adjacent string, not its own node)
- `tooltipDescription` unset → `label={`${label}${required ? ' *' : ''}`}`
  passed as a STRING to MUI's `TextField` `label` prop — MUI's `InputLabel`
  renders it internally; no JSX span exists to tag at all in this branch.

Either branch: the asterisk is driven by the EXACT SAME `required` boolean
that `validateRequiredFields()` reads to gate Save (confirmed via
`ToolBaseProperty.jsx:337`, `SecretManagementInput.jsx:16,71`) — same root
cause, so asserting Save-gating already proves the underlying defect
signature. `SecretField.jsx` is shared by every secret/token field app-wide
(API keys, passwords, tokens) — restructuring its label-rendering to expose
a testid-able asterisk node, just to independently assert a cosmetic
sub-observable of an already-proven defect, is disproportionate blast radius
for a documentation-completeness finding.

**Resolution chosen (reviewer had offered it as equally acceptable):**
narrow the AFS Coverage Map row's "Asserted where"/Disposition to the
implemented Save-gating assertion, add a "Row 6 disposition note" declaring
the asterisk half as a justified, narrowed gap per
`.agents/role-overrides.md` § Declared-improvisation protocol (source-traced
reasoning, not a hand-wave), cross-reference the same reasoning in the Step 8
code comment, and disclose it in the PR body (the reviewer's finding also
faulted MISSING disclosure, not just the coverage-map claim itself). No test
assertion or application code touched — same deterministic RED, reverified
across 2 local runs post-fix.

**Reusable rule for the next "no visual indicator" style finding in this
codebase's form fields:** before defaulting to `add-data-testid`, grep the
component tree for how the label/indicator is actually rendered — if it's a
string concatenation inside a `label` prop (common in this MUI-form-field
codebase, see also `mui_form_field_quirks.md`'s wrapper-testid gotchas),
adding a testid means restructuring a shared component, which is a real cost
to weigh against "just narrow the AFS row + declare the gap" — especially
when the underlying defect signature is provably identical either way.
