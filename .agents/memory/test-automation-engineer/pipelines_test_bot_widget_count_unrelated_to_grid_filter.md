---
name: Pipelines dashboard "Test Bot" widget count is unrelated to grid filter state
description: The floating bottom-right "Pipelines: N" counter is a static per-project total from an unlabeled widget, not the filtered-grid count — never use it to assert filter/clear behavior.
type: project
---

On `/pipelines/all` (and likely the same shared widget on other entity dashboards),
a floating card bottom-right shows a "TB / Test Bot" avatar + `Pipelines: N` text.
It has **no `data-testid`** and does not appear anywhere in `EliteaUI/src` under
that literal text (grepped, zero hits) — it's rendered from data, not a
findable JSX string.

Confirmed live (ELITEA-2013 fix round 1): clicking a Tags-panel chip narrowed the
grid from 12 cards to 2, but this widget's count stayed at `12` — it is a
**static per-project total, unrelated to the Tags filter panel or grid state**.

If an AFS Coverage Map row cites a "dashboard's own 'Pipelines: N' counter …
returns to its pre-filter value" as the proof for a filter-clear/restore step,
that's AFS drift, not a real signal — don't implement it literally. Use
`get_card_names()` (`entity-card-name` testid) set-equality against a baseline
captured before the filter was ever applied instead; it's testid-backed and
actually reflects the grid.
