---
name: Console-error filter idiom, and seed-vs-document for an undocumented ambient-data dependency
description: The established page.on("console", ...) + known-artifact-filter-function + Side-channel-check-step idiom this repo uses to automate an AFS's "no console errors" claim; and the judgement call for an undocumented ambient test-data dependency (seed a throwaway vs document reuse-existing) when no fixture actually guarantees the ambient state — now confirmed TWICE (ELITEA-2095, ELITEA-2132), i.e. established team convention, not a one-off call.
type: feedback
---

From ELITEA-2095 (PR #693) fix-only pass, reviewer findings #1 and #2.

## Finding #1 — an AFS's "console-error check" claim must be a REAL assertion, not a manual-observation note

An analyst's manual exploration checking DevTools for console errors after
every navigation/click is NOT the same as an automated test asserting it —
even when the AFS's own Coverage Map Pass-criteria row and an Axis 2 bullet
both cite "console-error check" as backing the `asserted` disposition. If
the shipped test never calls `page.on("console", ...)`, that claim is false
advertising the reviewer will (correctly) catch as BLOCKING.

The established repo idiom (see `test_credential_create.py`'s
`_is_known_554_warning`/`_is_known_518_warning`/`_is_known_291_warning`,
`test_pipeline_mcp_node_*.py`, `test_skill_export_import.py`):

1. A module-level `_is_known_<ISSUE>_<shape>(msg) -> bool` filter function
   per known artifact, with a full docstring citing the ticket/root cause.
   Match on BOTH `msg.text` and `(msg.location or {}).get("url", "")` — a
   text-only match risks over-filtering a coincidentally-similar NEW error;
   a location-only match misses artifacts with no location (e.g. some
   React dev warnings).
2. Register `page.on("console", _on_console)` immediately after the page
   object is constructed — BEFORE the first case step — so every step's
   output is captured, not just a later step's (a listener registered
   mid-flow silently misses everything before it — see the existing
   `console_listener_registered_after_flow_start_gap` entry).
3. A dedicated `allure.step("Side-channel check — ...")` near the end
   (before cleanup) asserting `not console_messages`.

**Verify the filter is genuinely exercised, don't just trust the logic.**
Added temporary debug instrumentation (a parallel unfiltered list + a
print of `msg.text`/`msg.location` for every raw error) for ONE throwaway
run, confirmed the known artifact actually fires and is actually filtered,
THEN removed the debug code before the official reruns. A filter that's
never proven to match anything real is unverified, not fixed — the AFS's
own project-471 `secrets` 403 fired exactly 4× per run (once per page
load: project switch, +Chat seed, post-navigate reload, reopened
conversation) with the exact shape
`Failed to load resource: the server responded with a status of 403
(Forbidden)` / `location.url=".../secrets/secrets/default/471"`.

## Finding #2 — an undocumented ambient-data dependency: seed a throwaway, don't just document it, unless something ELSE actually guarantees it

`ChatPage.click_first_other_conversation(exclude_id)` needs at least one
OTHER conversation to exist in the sidebar to click away to. The original
AFS/implementation silently relied on project 471 ("Elitea Testing Team")
already having ≥2 conversations — true by observation during one
implementation session, but never a guaranteed invariant: every OTHER test
in this suite cleans up its own conversations (`finally: delete_conversation`),
so there's no fixture or long-lived seed that actually keeps a second
conversation alive in that project between runs.

The workflow skill's Hard Rule 10 (read-only-by-default) says prefer NOT
seeding IF a stable existing record already satisfies the observable — but
that's conditional on the stability actually being real. Before choosing
"document as `reuse-existing`" vs "seed a throwaway," grep for a fixture
that would make the ambient claim durable (`grep -rln "471" automation/tests/
automation/fixtures/ automation/conftest.py`). If nothing guarantees it,
documenting `reuse-existing` just launders an unreliable assumption into
the AFS as if it were a fact — seed a minimal, self-cleaning throwaway
instead. Here: `team_conversation_api.create_conversation(name)` (plain API
create, zero messages, no `+Chat`/UI flow) — confirmed via the pre-existing
`test_navigate_between_conversations` (in `test_conversation_management.py`)
that a zero-message, API-created conversation renders in the sidebar and is
clickable. Defect #691 (sending the FIRST UI message to a zero-message
conversation silently creates a new one instead) does NOT apply, because no
message is ever sent to this throwaway — it exists purely to be clicked.
Cleaned up in the same `finally` block as the primary seeded conversation.

## Confirmed a second time — ELITEA-2132 (PR #698) fix-only round 2

Same judgment call, independent occurrence: step 3's positional check ("new
folder entry renders above the 'Today' date-group heading") needed a
guaranteed date-group heading to compare against. Live investigation (a
throwaway pytest script hitting `localhost:5173`, per the dispatch's explicit
"check live before assuming untestable" instruction) confirmed the shared
project DOES have real ambient content (3 pre-existing conversations under
"Today") — so the naive move would have been "document it as `reuse-existing`
and assert against it directly." Went with seed-a-throwaway instead, same
reasoning as above: nothing in this suite guarantees that ambient state
survives future runs. This time the seed was even cheaper — the pre-existing
`conversation_id` **fixture** (function-scoped, auto-create-and-delete,
already used by several other chat tests) covered it exactly, no manual
`conversation_api.create_conversation()`/`finally`-block bookkeeping needed
at all; just add `conversation_id` as a test parameter. **Two confirmed
instances now = treat "seed via the cheapest available fixture, don't lean on
undocumented ambient shared-project state" as house style for this suite**,
not a case-by-case judgment call to re-derive each time.

### Related, smaller lesson from the same round: bool-returning helper vs Locator-returning accessor

`ChatPage.is_conversation_group_visible(group)` (from ELITEA-2095) already
existed and wraps the exact same `CONVERSATION_GROUP_HEADER` testid template
this fix needed — but it returns `bool`, and the new caller needed the
Locator itself for a `bounding_box()` comparison. Rather than change
`is_conversation_group_visible`'s return type (would break existing
bool-callers) or reach into the page object's internals from the test
(`chat.page.locator(chat.CONVERSATION_GROUP_HEADER.format(...))` — no other
test in this suite calls `.page.locator()` directly, that would have been a
new anti-pattern), added a small sibling method,
`get_conversation_group_header(group)`, that returns the Locator and shares
the same handle. General pattern worth reusing: when an existing page-object
method's return type doesn't fit a new caller's need, add a same-name-family
sibling accessor rather than widening/changing the existing method's
contract.

## Confirmed a third time — ELITEA-2361 fix-only pass (commit 39686d78), plus a new sub-lesson

Third independent occurrence of the filter idiom itself (module-level
`_is_known_<ISSUE>_<shape>(msg)`, match on BOTH `msg.text` and
`(msg.location or {}).get("url", "")`, filter at assertion time via list
comprehension) — this time for a genuinely NEW known-noisy resource
(elitea-testing-public#1434: an intermittent Google Fonts CDN 404 for a
Montserrat `.woff2`, app-wide via `index.html`'s `<link>` tag, not tied to
any specific feature). Reproduced via the same temp-debug-print technique:
1 hit in 6 fresh re-runs of the target spec.

**New sub-lesson: a known-noisy resource can trip MORE THAN ONE side-channel
in the same test — filter all of them, not just the one that happened to
fail in the observed run.** This test also carried an independent
`page.on("response", ...)` → `failed_responses: list[int]` side-channel
(status-only, no URL — the same shape used identically across at least 3
sibling spec files in this batch family, e.g.
`test_agent_hub_start_conversation_creates_new_chat.py`). The SAME font 404
that logs a console error also surfaces there as a bare `404` int with no
URL to filter by. Fixing only the console-error assertion (the one that
happened to fail in the gate) would have left the network-status assertion
still exposed to the exact same flake — just relocated it to a different
line, not fixed it. Changed `failed_responses` to
`list[tuple[status, url]]` LOCALLY in the one file being fixed (a test
file's own inline `page.on(...)` listener has no external callers, so this
is not a shared-caller-file edit — no additive-only constraint applies) and
added a second filter, `_is_known_<ISSUE>_<shape>_response(status, url)`,
mirroring the console-message one but keyed on the (status, url) tuple
`page.on("response", ...)` actually gives you. **When root-causing an
intermittent red, grep the test for every side-channel assertion sourced
from the SAME underlying resource/event before declaring the fix
complete** — not just the one line named in the failure message.

### Sanity-checking a new assertion isn't tautological — cheap, worth doing on every "add a missing assertion" fix

Before counting the fix as done, temporarily inverted the new comparison
(`>=` an impossible offset instead of the real `<=`), reran the test once,
confirmed a real `AssertionError` fired with the expected box values in the
message, then reverted to the correct form. Costs one extra `pytest`
invocation; directly proves the added assertion can actually fail (i.e. it's
wired to something real, not silently short-circuited by a bad boolean or an
always-true guard) — the exact class of bug the review findings in this file
exist to catch in the first place, so it's worth catching in your own new
code before shipping it.
