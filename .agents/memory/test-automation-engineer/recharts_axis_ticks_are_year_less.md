---
name: Recharts axis ticks are year-less — never difference them arithmetically
description: MM-DD tick labels go -331 days across New Year; resolve each tick against the response's own YYYY-MM-DD series instead.
type: feedback
aliases: [recharts ticks, chart span, MM-DD, year boundary, tick span days]
tags: [area/charts, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

Recharts XAxis in this app renders `tickFormatter={d => d?.slice(5)}`, i.e. **year-less
`"MM-DD"`** labels (`AnalyticsOverview.jsx`, `AnalyticsAgents.jsx`). Computing an axis span
from those parts —

```python
(last_month - first_month) * 30 + (last_day - first_day)
```

— is correct only inside one calendar year. A Last-30d window straddling New Year renders
`12-11…01-10` and scores **(1-12)*30 + (10-11) = -331**, so any `span >= N` assertion fails
deterministically for the ~30 days after every New Year. Caught in review on ELITEA-2317
(2026-08-28); the spec was green in August and would have gone red in January.

## The fix

Resolve each rendered tick back to the FULL `YYYY-MM-DD` date in the response's own series
before differencing (`_response_dates` + `_chart_tick_span_days` in
`test_analytics_date_filter_content_refresh.py`). Two wins: it is year-correct, and the span is
derived from the **system's payload** rather than a calendar the test computed for itself
(`.agents/testing.md` § Fidelity policy). A tick outside the response's series then fails
loudly instead of being silently date-mathed.

## Measured thinning (project 399, 2026-08-28)

`Last 30d` → 26 `chat_daily` entries spanning 29 days → 13 rendered ticks spanning **28** days.
Recharts thinned only 1 day off the span, so a 10-day slack is generous while still catching a
chart frozen on the previous range (24h series = 1-day span).

Related: [[chart_presence_is_not_chart_data]]
