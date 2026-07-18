---
name: Publish/Unpublish wizard implementer quirks
description: create_agent_full() tags-must-be-objects payload gotcha, the #614 post-publish auto-navigation reversion (network-trace-confirmed) generalized into a poll+API-tie-breaker pattern applied at BOTH select_version_by_name() and the actions-menu status check, the two-distinct-React-warning-shapes gotcha for #611, the already-filed #554 toolkits-404 noise confirmed to leak in from a page's OWN initial navigate() (not just a mid-test reload), two real bugs found while hardening (int/str id-comparison mismatch silently defeating an API tie-breaker; an unguarded wait_for_network() leaking a raw TimeoutError past a method's AssertionError contract), and the closeout-round #614 root-cause trace confirming a genuine shared client-side mechanism (formik.values.version_details raced against ApplicationVersionSelect.jsx's async cache-invalidation refetch) for the same-page case, honestly flagged unconfirmed for the post-reload residual
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

## Round 2 (PR #615 review): the SAME #614 staleness also hits `select_version_by_name()` itself, not just the actions menu

A 14-run independent verification batch of round 1's fix came back ZERO
menu-poll timeouts, but surfaced `select_version_by_name()`'s OWN
post-reload `wait_for_function` timing out (1/14) — i.e., even the
"belt-and-braces" reload documented above isn't always enough on its own.
This is the identical staleness class, just a different call site — the
fix generalizes cleanly:

1. **POM level**: the method now retries a bounded 2 FULL select+reload
   cycles (re-open dropdown, re-click option, reload — not just re-polling
   an already-reloaded page) and raises a clean `AssertionError` (never a
   raw Playwright `TimeoutError`) on exhaustion, mirroring
   `wait_for_publish_status_menuitem`'s contract exactly.
2. **Test level**: catch that `AssertionError`, then ask the API
   (`_confirm_new_version_via_api(agent_api, agent_id, version_name,
   exclude_version_id=base_version_id)`) whether a DISTINCT `published`
   version with the expected name already exists server-side — if yes,
   soft-assert as confirmed #614 (same `soft_failures` bucket as #611); if
   no, hard-fail (reverse-masking guard — don't blanket-downgrade every
   timeout to "known defect").
3. Any LATER step whose assertions depend on the SAME DOM state that just
   failed to converge (here: Step 6c re-opening the VERSION dropdown) must
   be skipped/gated on a `_dom_converged` flag, not re-attempted — it would
   just re-fail on the identical staleness under a different assertion
   message, fragmenting one root cause into what looks like two.

**General lesson**: when a #614-class staleness assertion gets hardened at
one call site, actively check whether OTHER call sites reading the same
kind of version-scoped client state share the same exposure — this defect
is a property of the app's state-sync timing, not of any one component.

## Two real bugs found while generalizing the pattern (both worth checking for elsewhere)

- **int/str id-comparison mismatch silently defeats an API tie-breaker.**
  `AgentDetailPage.get_version_id()` (DOM) returns a `str`; the API's
  `version["id"]` is a JSON number (`int`). A tie-breaker function comparing
  them with bare `==` (`version.get("id") == version_id`) is ALWAYS `False`
  regardless of whether they actually match — meaning every CONFIRMED
  known-defect occurrence silently false-hard-fails instead of soft-
  asserting. Not caught by review or by 14 runs because the affected code
  path (an already-converged menu, so the tie-breaker was never invoked)
  happened not to fire in that sample — an untested branch, not a
  passing one. Fix: normalize both sides with `str()` before comparing.
  **Check this pattern anywhere an API-tie-breaker compares a DOM-sourced
  id against a JSON-sourced id.**
- **An unguarded `wait_for_network()` inside a method with its OWN
  AssertionError contract leaks a raw exception straight past it.** This
  app keeps persistent WebSocket connections open, so `networkidle` can
  legitimately never fire — `BasePage.navigate()` already wraps this exact
  wait in try/except for that reason. A NEW escalation path added later
  (a post-reload settle inside `wait_for_publish_status_menuitem`) called
  `self.wait_for_network(...)` unguarded, so its own `networkidle` timeout
  raised a raw `playwright.TimeoutError` instead of flowing into the
  method's carefully-designed `except Exception: ... raise AssertionError`
  ending — bypassing every caller's `except AssertionError` handling
  entirely. **Any new code added inside a method that promises a clean
  exception contract must route ALL its exit paths through that
  contract — a single unguarded call anywhere inside is enough to break
  it for callers.**

## Register-console-listener-then-reload trap (and: verify it's actually THAT known defect before filtering)

Registering the console-error listener before Step 2 (as the "check the
whole Publish wizard flow" scoping calls for) but ALSO reloading mid-test
(for the #614 workaround above) — or simply having the listener start
before the test's OWN initial `navigate()`, which is itself a full page
load — pulls in unrelated, pre-existing, out-of-scope 404 noise into the
known-defect-611 console check. Confirmed this round (PR #615 review round
2): that noise is the ALREADY-FILED, unrelated
https://github.com/EliteaAI/elitea-testing-public/issues/554 (an
RTK-Query `toolkitTypes` timing race 404ing on `.../toolkits/prompt_lib/`
with an empty projectId — first filed from `test_credential_search_by_name.py`,
now confirmed reproducible on a completely different page, matching that
issue's own note that it's "likely reproducible on any page render").
**Don't just assume/blanket-filter "any 404" here** — verify which
resource 404'd (via `msg.location.url`, not `msg.text` alone, which has no
URL) and confirm it matches an ALREADY-FILED issue's exact endpoint before
filtering; a blanket 404 filter would mask a genuinely new defect. Fix:
either order the console-cleanliness assertion for a specific interaction
BEFORE any later, unrelated navigation/reload the test performs for other
reasons (scope the check tightly to the interaction it's meant to verify —
round 1's fix), OR — when the noise source is the test's OWN necessary
setup navigation (unavoidable, as here) — filter the specific known,
already-filed defect by URL, the same technique
`test_credential_search_by_name.py` established first.

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

## Round-2 closeout: #614's "same root cause" claim — investigated, confirmed (with one honest caveat)

Round 2's commit message asserted the actions-menu staleness and the
`select_version_by_name` staleness were "the same root cause" — but this was
pure pattern-matching ("both respond to a reload"), never actually traced,
and issue #614 had zero comments recording it. A dedicated closeout round
traced the actual EliteaUI source (sibling `EliteaUI/` clone,
`automation/testids` branch) rather than re-asserting the claim:

- `agent-version-selector-trigger` / `copy-version-id`
  (`ApplicationVersionSelect.jsx`) and the actions-menu's Publish/Unpublish
  gates (`usePublishVersion.hooks.js`'s `canShowPublish`,
  `useUnpublishVersionMenu.hooks.jsx`'s `canUnpublish`) ALL read the SAME
  `formik.values.version_details`/`.versions`, which Formik re-syncs from
  `useApplicationDetailsQuery`'s RTK-Query cache via
  `EditApplication.jsx`'s `enableReinitialize`.
- The actual race: `ApplicationVersionSelect.jsx`'s post-navigate
  `useEffect` reconciles the URL's `version` route param against the
  (possibly stale) `versions` array — if the newly-published clone isn't in
  it yet, the effect treats the URL as invalid and REDIRECTS BACK
  (`navigate({..., replace: true})`). This races against the publish/
  unpublish mutations' own async `invalidatesTags` refetch (the tag
  invalidation itself is NOT broken — `applicationDetails` provides the
  bare/general `TAG_TYPE_APPLICATION_DETAILS` tag, which matches regardless
  of the mutation's `arg.id` always being `undefined` — a latent-but-inert
  code smell, not the bug). If the synchronous effect runs before the async
  refetch resolves, it loses the race and reverts.
- Confirmed this is the IDENTICAL code path whether triggered by the app's
  own post-publish `navigate()` or by a user's manual dropdown reselect
  (`VersionSelect.jsx` ALSO calls `navigate()`, via `replaceVersionInPath`,
  before invoking `onVersionChange`) — explains why the manual-reselect
  workaround is usually reliable but not always (the ~1/10 residual
  `select_version_by_name` needed a 2nd cycle for).
- **What's genuinely NOT confirmed**: the staleness that survives a FULL
  `page.reload()` in both methods' escalation paths. A hard reload discards
  the entire client-side Redux/RTK-Query store, so the async-refetch-vs-
  effect race above cannot explain it — that residual case is flagged as
  unconfirmed (plausibly backend-side read-after-write lag), not folded
  into the "confirmed" claim.

Posted the full evidence trail to
https://github.com/EliteaAI/elitea-testing-public/issues/614#issuecomment-5011102217.
AFS amended (it had NOT been amended in round 2, despite the round-2 PR
checklist claiming otherwise — corrected in the same closeout).

**General lesson**: "both symptoms respond to the same workaround" is not
evidence of "same root cause" — it's evidence the workaround happens to
cover both. A same-cause claim needs an actual pointer to shared code/state;
absent that, say "related, not confirmed identical" rather than overclaim.
When a commit message makes a causal claim about two failure modes, either
back it with a code citation or scope the claim down to what's actually
known.
