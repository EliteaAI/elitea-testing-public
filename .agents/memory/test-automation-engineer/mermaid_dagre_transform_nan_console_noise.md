---
name: Mermaid dagre transform-NaN console noise
description: Mermaid-rendered diagrams can emit a transient `<g> attribute transform: translate(undefined, NaN)` console error — library render-race, not a defect, if functional steps still pass.
type: feedback
---

## What it is

`EliteaUI/src/components/MermaidDiagramOutput/DiagramOutput.jsx` mounts a
FRESH Mermaid SVG target on every render (`getDiagramId()` increments a
module-level counter) and immediately re-initializes `svg-pan-zoom` on it.
Mermaid/dagre's cluster and edge-label `<g>` nodes are a documented upstream
case (mermaid-js/mermaid#1846 and siblings) where a `getBBox()`-derived
translate is computed one paint before the label's real dimensions are
available, producing:

```
Error: <g> attribute transform: Expected number, "translate(undefined, NaN)".
```

Any flow that mounts/unmounts multiple independent Mermaid instances in one
test (e.g. conversation render + a canvas's own live preview + a post-close
re-render) multiplies the chance of hitting this race.

## How to tell it's noise, not a defect

Check the SAME run's own functional assertions (node/edge counts, edited
text present, etc.) — if they all passed while only the console side-channel
step failed, the invalid SVG transform was silently dropped per spec and
never affected the rendered result. Confirmed on ELITEA-2088
(`test_generate_mermaid_diagram_and_edit_in_canvas.py`): allure result
showed all 11 functional steps `passed`, only the console check `failed`;
4 further standalone reruns came back completely clean.

## Fix

Add a scoped known-noise filter matching on both substrings
(`"<g> attribute transform"` and `"translate(undefined, NaN)"`) — see
`_is_known_mermaid_transform_nan_warning` in that test file for the full
worked example and docstring idiom (same shape as `_is_known_secrets_403`).
Before adding, `grep -rn "translate(undefined" automation/` — as of
2026-08-04 there was no prior instance anywhere in the suite, so this is a
NEW noise category, not yet a recurring pattern to just copy from elsewhere.
Any OTHER Mermaid-diagram test hitting the same signature should reuse this
exact filter shape rather than reinvent it.
