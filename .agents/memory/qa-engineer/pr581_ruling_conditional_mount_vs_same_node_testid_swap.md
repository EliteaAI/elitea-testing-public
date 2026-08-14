---
name: PR #581 ruling — conditional-mount empty-state vs same-node testid-swap
description: How to tell a compliant conditionally-mounted testid apart from the state-conditional-testid anti-pattern the PR #581 ruling actually targets, plus the shared-dir literal-scope boundary
type: feedback
---

## The distinction

`.agents/testing.md` § Locator policy (PR #581 ruling) bans a testid whose
**presence or value changes with component state on the same DOM node** —
its own examples are `data-testid={!isExpanded ? id : undefined}` and
`data-testid={done ? 'x-complete' : 'x-preview'}`: one semantic widget,
toggling its testid identity as the user interacts with it (expand/collapse,
in-progress/done).

That is a different shape from: a component conditionally **mounts or
doesn't mount a whole subtree** based on a prop/branch (e.g. `isMCP ? <Foo
data-testid="x">…</Foo> : undefined`), where the mounted branch always
carries the SAME fixed testid. Every conditionally-rendered empty-state /
error-message / modal-body element in a normal React app has this shape —
if this counted as a violation, virtually no conditionally-rendered element
could ever get a testid. Reviewed and approved this exact case in PR #634
(ELITEA-1921): `ToolkitTypeSelector.jsx`'s `isMCP ? <Typography
data-testid="mcp-type-picker-local-empty-state">...</Typography> :
undefined` — compliant, because the testid identity never swaps; only
mount/unmount does, driven by a page-level prop, not runtime interaction
toggling on that node.

**Test:** does the SAME node's testid VALUE change across states (bad), or
does a node with ONE fixed testid simply exist-or-not depending on which
prop/branch is active (fine)?

## The shared-dir scope is literal, not "anyone who imports this twice"

The ruling's "shared components never hardcode feature-scoped testids" half
is scoped textually to `src/components/` and `src/[fsd]/shared/`. A
component living elsewhere (e.g. `src/pages/Toolkits/ToolkitTypeSelector.jsx`)
that happens to be imported by two different pages does NOT automatically
trip this rule — check the literal path first. Even when reused across call
sites, if the testid's semantic name stays accurate at every call site (here:
"mcp-type-picker" is true regardless of whether it's embedded via
`CreateToolkit.jsx` or `NewChat/ToolkitEditor.jsx`), it isn't the
`agent-search-clear-button`-on-shared-SearchBar anti-pattern (where the name
became WRONG once reused outside its first caller). Flag only when either
(a) the file is genuinely under one of the two shared dirs, or (b) the name
becomes misleading/wrong at a second call site.
