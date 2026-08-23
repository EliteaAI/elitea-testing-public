---
name: Network-capture timing can manufacture a false "not implemented" bug
description: "No request observed" is only evidence if the collector was armed at the moment the feature actually fires — and on the right transport
type: feedback
aliases: [no POST observed, feature not implemented false bug, upload fires on send, websocket not post, false defect network evidence]
tags: [area/defect-triage, type/technique]
created: 2026-08-22
updated: 2026-08-22
---

## The failure

A prior analysis concluded the Support Assistant's file attachment was an unimplemented
**stub UI** — *"network requests show no file upload to backend"* — and filed a bug
(#1584) that a live re-run disproved point by point. Two independent timing/transport
mistakes produced it:

1. **Wrong moment.** The upload fires on **Send**, not on attach. Attaching only puts a
   `PENDING` chip into local React state. A capture armed around the attach click
   legitimately sees nothing.
2. **Wrong transport.** The message itself goes out as a **Socket.IO frame**, not a POST.
   "No POST observed" was never evidence that nothing was sent. (Also: the upload used
   `XMLHttpRequest`, not `fetch` — `page.on("response")` catches it, a fetch-scoped
   `expect_request` would not.)

The verdict scaled a local observation into an architectural claim ("stub UI", "not
connected to the backend") that source-reading would have refuted in one grep.

## The rule

**Absence of traffic is the weakest evidence there is.** Before writing "not implemented":

- Read the handler and find *where* the call actually fires — an attach may defer to send,
  a save may debounce, a fetch may live in a mount effect rather than the click.
- Identify the **transport**: HTTP fetch, XHR, WebSocket frame, SSE, beacon. Arm a
  collector for the right one, page-level and before navigation.
- Prefer a **positive** oracle over an absence: assert what the system *did* produce (see
  [[plant_a_token_to_prove_content_grounding]]) rather than what you failed to observe.
- "Feature not implemented" is a claim about **source**, so support it from source or
  do not make it.

## Cost

A false bug is expensive twice: a developer is sent to rebuild something that works, and
the case sits parked as `defect-found` instead of being automated. This one blocked
ELITEA-2421 for four days, alongside sibling false bug #1581 from the same pass.

Related: [[plant_a_token_to_prove_content_grounding]]
