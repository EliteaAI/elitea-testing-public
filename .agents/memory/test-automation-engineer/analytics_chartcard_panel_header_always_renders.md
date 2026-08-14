---
name: Analytics chartCard-style panel header row always renders
description: get_panel_summary's split lines include the table-header row (uppercase column labels) even in the empty-state branch — index past it before checking for "No X data"
type: project
---

`AnalyticsUserDetailed.jsx` / `AnalyticsAgentDetailed.jsx`'s Users/Tools
(and Models/Agents) `chartCard`-style panels always render their column
header row (`tableCell` style, `text-transform: uppercase`) regardless of
whether the item list is populated or empty. `get_panel_summary(panel)`'s
line split therefore looks like:

```
lines[0] = panel title            ("Users" / "Tools")
lines[1] = count subtitle         ("{N} tools used by this agent / pipeline")
lines[2:N] = UPPERCASE column headers   ("TOOL", "CALLS") or ("USER", "RUNS", "AVG LATENCY", "ERRORS")
lines[N:] = per-item rows, OR a single empty-state line ("No tool data" / "No runs recorded")
```

ELITEA-2321's first implementation attempt asserted `lines[2:] == ["No tool
data"]` for the empty-state branch and got
`['TOOL', 'CALLS', 'No tool data']` — the header labels are NOT stripped
just because the body is empty. Fix: assert the header tuple explicitly
(`tuple(lines[2:4]) == ("TOOL", "CALLS")`), then slice past it
(`lines[4:]`) before checking populated-vs-empty body content. Same
2-column vs 4-column header-width applies per panel (Tools = 2, Users /
Models / Agents = 4) — check the panel's own JSX for its column count
before hardcoding the slice index.
