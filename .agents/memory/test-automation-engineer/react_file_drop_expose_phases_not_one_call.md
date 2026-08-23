---
name: React file-drop helpers expose PHASES, not one enter-over-drop call
description: A drag-over affordance can only be asserted to revert mid-gesture if the page object splits the gesture
type: feedback
aliases: [drag and drop file, DataTransfer, dragenter dragleave, drop zone helper, drop overlay]
tags: [area/ui, type/pattern]
created: 2026-08-22
updated: 2026-08-22
---

## The pattern

`ChatPage.drag_and_drop_file()` is one monolithic call (`dragenter` → `dragover` → `drop`).
That is fine when the only observable is the resulting chip — but it **cannot** express
"the drag-over overlay appears, then reverts when the drag leaves", which is the only DOM
proof the drop zone actually RECEIVED the drag.

Shipped shape (`SupportAssistantPage`, ELITEA-2420) — three thin phases over one private
`_dispatch_drag_events(path, event_types, timeout)` helper holding a single JS blob:

- `drag_file_over_composer(path)` → `["dragenter", "dragover"]`
- `drag_leave_composer(path)` → `["dragleave"]`
- `drop_file_on_composer(path)` → `["dragenter", "dragover", "drop"]`

Each phase builds its own `DataTransfer`; no phase depends on another's JS state. Pass the
path even to the leave phase — the handler ignores the payload, but a uniform signature keeps
one JS blob instead of three near-copies.

## Why the drop phase re-sends dragenter

React drag handlers usually keep a **counter ref** (`dragCounterRef`) so nested children don't
flicker the overlay: `dragenter` increments, `dragleave` decrements, overlay clears at 0. If
`handleDrop` resets the counter to 0 unconditionally (it does in `MessageInput.tsx`), a
self-contained drop phase is safe and the counter cannot leak between phases. **Read the
handler before assuming this** — a drop handler that only decrements leaves the overlay stuck
after the second gesture.

## Fidelity

This is **transit** substitution — the input gesture only. Every observable (overlay render,
chip, Send state, upload status, WS frame, reply) stays product-produced. The `.evaluate(` hit
in the provenance grep is disposition 2; say so in the Run Report and put the reasoning in the
method docstring, not only the AFS.

Related: [[dnd_kit_drag_gesture_needs_settle_check]]
