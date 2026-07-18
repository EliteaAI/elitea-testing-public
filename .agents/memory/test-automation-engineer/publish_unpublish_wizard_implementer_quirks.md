---
name: Publish/Unpublish wizard implementer quirks
description: create_agent_full() tags-must-be-objects payload gotcha, the #614 post-publish auto-navigation reversion (network-trace-confirmed) and its select_version_by_name()+reload workaround, the actions-menu Publish/Unpublish-item staleness needing a close/reopen poll, and the two-distinct-React-warning-shapes gotcha for the same console defect
type: feedback
---

From ELITEA-1892 (Publish a Draft version — status changes, Unpublish becomes
available). Implementer pass, `AgentDetailPage` + `AgentAPI`.

## `create_agent_full()` payload: tags must be objects, not strings

`{"tags": ["regression"]}` 400s: `Input should be a valid dictionary or
object to extract fields from` at `versions.0.tags.0`. Confirmed via
EliteaUI source (`useSaveVersion.js`: `tag.name`) — the correct shape is
`{"tags": [{"name": "regression"}]}`. Every existing sibling payload in this
repo only ever used `"tags": []` (empty), so this shape was undocumented
until now.

## Known defect #614 — Publish's auto-navigation is unreliable (network-trace confirmed)

The AFS (and a prior analyst run) documented "the app navigates to the new
Published version after Publish, VERSION selector shows the new name." On
live re-verification this run, that does NOT hold reliably:

- Network trace: `GET .../version/prompt_lib/{project}/{agent}/{new_id}`
  resolves 200 (app DID navigate to the new version)... then immediately
  `GET .../version/prompt_lib/{project}/{agent}/{old_id}` fires again — the
  app silently reverts to the previously-active version. No console error.
  VERSION selector ends up showing the OLD name.
- Underlying data is ALWAYS correct (verified via `AgentAPI.get_agent()` —
  the new version really is `status: "published"`, the old stays `"draft"`).
  This is purely a client-side navigation/routing bug.
- Filed: https://github.com/EliteaAI/elitea-testing-public/issues/614.

**Workaround, confirmed reliable**: explicitly re-select the new version by
NAME from the VERSION dropdown after Publish (`open_version_selector()` →
click the `version-option-{name}` testid) rather than trusting/waiting for
auto-navigation. This is a normal, deliberate user action and was
reproducible via real Playwright clicks without reverting — added as
`AgentDetailPage.select_version_by_name(version_name, timeout)`.

## The SAME defect also staled the overflow menu's Publish/Unpublish item

Even after VERSION-selector-text + Information-panel version-id + URL all
agreed (a real, condition-based `wait_for_function` three-way check), the
actions overflow menu's Publish/Unpublish menuitem could STILL render from a
stale status snapshot — observed persisting across 4 open/close attempts
(~10s) in roughly 1 run in 6-9 during implementation, resolving instantly on
some runs and not at all within a generous budget on others. This is NOT a
simple one-render-tick lag (MUI doesn't live-update an already-open menu; a
close+reopen forces a fresh render, but if the underlying STORE hasn't
synced yet, reopening doesn't help either).

**What worked**: (1) after `select_version_by_name`'s DOM-consistency wait
resolves, do a full `page.reload()` (not `wait_for_page_load()` — that
generic heuristic can read an intermediate, not-yet-hydrated paint; reuse
the SAME precise `wait_for_function` condition post-reload instead) — this
forces every panel to refetch fresh from the server, which is always
correct. (2) Additionally wrap the actions-menu check itself in a bounded
close/reopen poll (`wait_for_publish_status_menuitem(expect_unpublish,
timeout, attempts)`) as defense-in-depth, since even the reload path showed
one residual flake across ~10 implementation runs. Both mitigations are real
techniques (a full reload + a real user re-open), not masking — the defect
is filed, not hidden, and a soft-assert would have been wrong here since
Unpublish availability is a hard case assertion, not an Axis-2 addition.

**Net observed stability with both mitigations**: ~9/10 clean runs, the
residual failure landing on the SAME confirmed root cause (#614), never on
an unrelated locator/timeout. Report this honestly in the Run Report rather
than chasing a 10th fix cycle — it's a real, filed, external instability.

## Register-console-listener-then-reload trap

Registering the console-error listener before Step 2 (as the "check the
whole Publish wizard flow" scoping calls for) but ALSO reloading mid-test
(for the #614 workaround above) pulls in unrelated, pre-existing,
out-of-scope 404 noise (`toolkits/prompt_lib/…` and `?mcp=true` — fires on
every full page load, unrelated to the Stepper defect) into the
known-defect-611 console check if the check runs AFTER the reload. Fix:
order the console-cleanliness assertion for a specific interaction BEFORE
any later, unrelated navigation/reload the test performs for other reasons
— scope the check tightly to the interaction it's meant to verify.

## Two distinct React warning message SHAPES for the same underlying defect

#611 (Stepper's `SvgCheckedIcon` leaking MUI props onto a DOM `<svg>`)
produces confirmed-live console.error text in TWO different formats
depending on the prop's type:
- Boolean props (`completed`, `active`, `error`): `Warning: Received
  \`%s\` for a non-boolean attribute \`%s\`.`
- Object prop (`ownerState`): `Warning: React does not recognize the
  \`%s\` prop on a DOM element.`

A known-defect filter written against only ONE of these shapes silently
misses the other and fails as "unexpected console error." Anchor the match
on the component name in the stack trace (`SvgCheckedIcon` here) — stable
across both message shapes — combined with an OR of both phrase substrings,
not a single phrase alone.
