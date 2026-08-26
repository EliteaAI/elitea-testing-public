---
name: An AFS's Automation Hints can recommend a technique that contradicts its own Coverage Map/Cleanup
description: ELITEA-1916's Automation Hints suggested a synthetic-second-mock for a retry step "for CI determinism," but the same AFS's Coverage Map row and Cleanup section's "MUST" language specified a real (unmocked) backend call + agent_api cleanup. Resolve toward the Coverage Map's asserted disposition + Cleanup MUST wording, not the Hints suggestion — Hints is advisory technique, Coverage Map/Cleanup is the work order.
type: feedback
---

## What happened

ELITEA-1916's AFS (Build with AI creation-failure recovery) had two sections
disagreeing about how Step 6's retry should hit the create endpoint:

- **Automation Hints**: "recommend registering a second, call-counted route
  handler... mock 500 on the 1st POST, 200/201 with a synthetic created-agent
  JSON on the 2nd... for CI determinism... the synthetic-second-mock approach
  is what should ship."
- **Coverage Map row 6**: "real (unmocked) backend call resolves 201, modal
  closes, auto-navigation... all fields verified against the draft."
- **Cleanup**: "An automated test MUST clean this up the same way every other
  Approve-clicking test in this file does: capture `created_agent_id`...
  delete via `agent_api.delete_agent(...)` in a `finally` block."

A synthetic mock produces no real agent — nothing to delete, and the
subsequent detail-page navigation would need ITS OWN mock too (the frontend's
GET for the created id would 404 against a synthetic id on the real backend).
That's a materially bigger technique change than "hints" implies, and it
directly contradicts the Coverage Map's asserted disposition + Cleanup's MUST.

## Resolution

Went with **clear the mock, let Step 6 hit the real backend, clean up via
`agent_api.delete_agent` in `finally`** — matching the Coverage Map + Cleanup
+ every sibling Approve-clicking test in the file (ELITEA-1909/1911/1912/1914/1908
all use real backend + `agent_api` cleanup, zero use a synthetic double-mock).
Documented the alternative and the reasoning in the Run Report / PR rather
than silently picking one.

## Rule for next time

When an AFS's **Automation Hints** section (technique suggestions) conflicts
with its own **Coverage Map** (asserted disposition) or **Cleanup** (MUST
language), the Coverage Map + Cleanup win — they are the work order; Hints is
advisory and can drift from the rest of the document (written from a
different vantage point, e.g. "what would make CI faster" vs "what was
actually live-verified"). Cross-check Hints against Coverage Map + Cleanup
before adopting a Hints suggestion that changes what gets asserted or
cleaned up, not just how a step is technically achieved. Note the conflict
and the resolution explicitly (Run Report / PR) — this is Phase 2 technique
latitude, not a scope change, so it does NOT require `needs-analyst-rerun`.
