---
name: MUI icons-material auto-testid on icon svg
description: "@mui/icons-material icon components auto-carry data-testid={ExportName} on their <svg>, even with zero app-authored data-testid prop — usable as a scoped, declared-improvisation sub-selector for state (e.g. VisibilityIcon vs VisibilityOffIcon), never as a substitute for the parent button's own testid"
type: project
---

Confirmed live (ELITEA-2343 analysis, 2026-08-05, `/settings/secrets` row-level
Show/Hide toggle): every `@mui/icons-material` icon component renders its
`<svg>` with `data-testid` automatically set to the icon's own export name —
`<VisibilityIcon/>` → `<svg data-testid="VisibilityIcon">`,
`<VisibilityOffIcon/>` → `<svg data-testid="VisibilityOffIcon">` — **with zero
app-authored `data-testid` prop at the call site** (confirmed by reading
`SecretsTable.jsx`: neither icon receives one). This is a library behavior,
not `add-data-testid` work, and it exists for EVERY MUI icon component in the
app, not just these two.

**Useful for:** verifying which of two conditionally-swapped icon components
is currently rendered (e.g. an open-eye vs crossed-eye toggle, an
expand/collapse chevron pair) via a scoped `[data-testid="<IconName>"]`
sub-selector chained off the REAL (app-authored) testid on the parent
interactive element — the parent keeps ONE static testid per
`.agents/testing.md`'s "testid = stable identity" ruling; only the CHILD
icon's own auto-testid differs, because it's a genuinely different React
component being swapped in, not a value-ternary on one element.

**Not a substitute for:** the parent element's own testid. The button/icon
container itself still needs `add-data-testid` if it has none — this is
purely a bonus handle for the icon's identity once the parent is locatable.

**Not yet canon-sanctioned:** flagged as a DECLARED IMPROVISATION in
ELITEA-2343's AFS (`test-specs/settings-secrets/l3_secret-eye-icon-reveal-and-mask-toggle_ELITEA-2343.md`
§ Concrete Handles) — no existing role-overrides/testing.md ruling explicitly
addresses a vendor-auto-generated (not `add-data-testid`-added) `data-testid`.
Reviewer should verify the reasoning holds; if rejected, the safe fallback is
to assert only the functionally-primary observable (e.g. the value-cell text
swap) and drop the icon-shape assertion rather than reach for a role/CSS
handle.
