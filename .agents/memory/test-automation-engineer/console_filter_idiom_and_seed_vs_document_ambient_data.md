---
name: Console-error filter idiom, and seed-vs-document for an undocumented ambient-data dependency
description: The established page.on("console", ...) + known-artifact-filter-function + Side-channel-check-step idiom this repo uses to automate an AFS's "no console errors" claim; and the judgement call for an undocumented ambient test-data dependency (seed a throwaway vs document reuse-existing) when no fixture actually guarantees the ambient state.
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
