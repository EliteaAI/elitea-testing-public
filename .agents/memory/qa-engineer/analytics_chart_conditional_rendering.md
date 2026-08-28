---
name: Elitea Analytics charts are conditionally rendered per project
description: Agents/Tools bar charts and the user-detail area chart vanish entirely on an empty project — assert the precondition off the response, not with a locator wait
type: feedback
aliases: [chart missing, agentChartData, toolChartData, empty project analytics]
tags: [area/settings-analytics, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

Confirmed live 2026-08-28: project **"Elitea Testing Team"** over `Last 30d` had
`0 agents & pipelines` -> the Agents tab rendered **no bar chart at all**
(`agentChartData.length > 0` guard). Project **"Private"** had 899 and rendered it.
Same guard shape on Tools (`toolChartData.length > 0`) and on the user-detail
`Daily Activity` chart (`daily_activity.length > 0`).

**Consequence for specs:** capture the tab's response body and assert
`len(response["rows"]) >= N` (N=2 when the case needs a second data point) as an explicit
precondition. Otherwise an unsuitable fixture project fails as a confusing locator timeout instead
of a clear "this project has no data" message.

Second conditional worth remembering: the Overview `Daily Activity` chart drops its **`Active Users`**
series (and the right-hand YAxis) on a **personal project** (`!isPersonalProject`) — 4 series on
"Elitea Testing Team", 3 on "Private". Derive the expected series list from the rendered
`.recharts-area-area` count instead of hardcoding it.

Related: [[recharts_chart_tooltip_automation]]
