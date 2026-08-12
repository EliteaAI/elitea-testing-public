---
name: ReactFlow canvas pan requires real mouse events
description: Synthetic JS-dispatched PointerEvents do nothing on ReactFlow's pane-drag handler — only real page.mouse events pan/drag
type: feedback
---

Confirmed live (ELITEA-2019, 2026-08-08) on the pipeline canvas
(`@xyflow/react`'s `.react-flow__pane`): dispatching a synthetic
`PointerEvent` sequence via `page.evaluate()`
(`pointerdown`/`pointermove`×N/`pointerup`, `isPrimary: true`, `bubbles: true`)
produces **zero** viewport transform change — confirmed twice, on two
different browser engines/sessions (Playwright MCP page-context evaluate AND
a raw CDP `Input.dispatchMouseEvent`-free JS dispatch). ReactFlow's own
pane-drag handler simply ignores untrusted synthetic events.

Real input — either Playwright's `page.mouse.move/down/up` (what
`move_node()`/`connect_nodes()` already use for node drags in this suite) or
CDP-level `Input.dispatchMouseEvent` (trusted-equivalent, what
`browser-verify`'s `drag` command and manual probes use) — pans/drags
correctly and px-perfectly (a (+100,+150) drag produced an EXACT
(+100,+150) transform shift, confirmed live).

**Implication:** when probing or implementing ANY ReactFlow canvas
drag/pan/connect interaction, never reach for `page.evaluate()` +
`dispatchEvent()` to simulate the drag — it will silently no-op (no error,
just zero effect) and waste a debugging cycle. Use `page.mouse` (test code)
or a CDP client's real `Input.dispatchMouseEvent` (live probing) from the
start.
