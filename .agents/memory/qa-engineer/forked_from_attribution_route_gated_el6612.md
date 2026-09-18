---
name: Forked-from attribution is route-gated to /agents (EL-6612)
description: Where the "Forked from" indicator actually renders on DEV after EliteaUI#996, so a missing entity-card-forked-from-link on pipelines/skills is not a backend regression
type: project
aliases: [entity-card-forked-from-link, forked from icon, EL-6612, fork attribution, DataTableRow dead code]
tags: [area/pipelines, area/agents, area/fork, status/verified]
created: 2026-09-17
updated: 2026-09-17
---

## Where the indicator renders (verified live on dev.elitea.ai build 0.4.2247, 2026-09-17, card #2343)

| Surface | `entity-card-forked-from-link` present? |
|---|---|
| Agents dashboard, CARD view | YES — `<a aria-label="Forked from - Original agent" aria-disabled="true">`, no href |
| Agents dashboard, TABLE view | no |
| Pipelines dashboard, CARD view | no (card otherwise complete) |
| Pipelines dashboard, TABLE view | no |
| Forked pipeline detail → Information | `Forked from: <source name>` as `<a aria-label="Go to original pipeline">`, no href, no own testid, inside `agent-information-section` |

Source: `src/components/Card.jsx` — `showForkedFromLink = isForked && useIsFrom(RouteDefinitions.Applications)` (EliteaUI#996, EL-6612).
`src/[fsd]/widgets/data-table/ui/DataTableRow.jsx:161` still renders `IconLinkWithToolTip`, but it is **dead code**: `DataTable.jsx` renders `GridTableRow` + `DataTableNameCell` (only `index.js` exports DataTableRow). Confirmed in the deployed bundle via React fiber — the row prop carries `is_forked: true` and no icon renders.

Backend is NOT involved: list payload (`GET /applications/prompt_lib/{pid}?agents_type=pipeline`) carries `is_forked: true` and `meta.{parent_entity_id, parent_project_id, parent_version_id}`.

## Why it matters
ELITEA-2051 Step 9 asserts the card-view link on `/pipelines/all` — deterministically 0 since #996 (merged 2026-09-13). Intentional-vs-accidental is a human decision (question card); do not "fix" the spec by pointing it at the detail page's Information row without that ruling.

Related: [[project_briefing]]
