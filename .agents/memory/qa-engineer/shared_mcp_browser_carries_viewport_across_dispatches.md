---
name: Shared MCP browser carries viewport size across dispatches
description: A prior session's browser_resize (e.g. 4000px-tall) persists into the next dispatch sharing the MCP browser — resize back before any scrollability check.
type: feedback
---

The Playwright MCP browser instance is shared across sequential analyst dispatches
in a batch (no per-dispatch fresh browser). A prior session's `browser_resize` call
(e.g. ELITEA-2142/2143/2144/2145 resizing to 1280×4000 while probing drag-and-drop
autoscroll) persists into the NEXT dispatch that reuses the same browser — there is
no automatic reset between dispatches.

**Failure mode confirmed live (ELITEA-2146/2147/2148, 2026-08-15):** navigated to
`/chat` at the inherited 1280×4000 viewport and read the sidebar list container's
`scrollHeight === clientHeight === 3928` — i.e. NOT scrollable. This is a FALSE
NEGATIVE purely from the oversized viewport (everything fits without scrolling at
4000px tall), not a real product/test finding. Resizing to a normal viewport
(1440×900) immediately produced the expected `scrollHeight=2946 > clientHeight=828`.

**Rule of thumb:** before asserting or exploring ANY scrollability/overflow
behavior (a container's `scrollHeight` vs `clientHeight`, "does this list scroll"),
check `window.innerWidth`/`innerHeight` first, or just call `browser_resize` to a
known-normal size unconditionally. Don't trust the ambient viewport size — it's
whatever the last dispatch left it at.
