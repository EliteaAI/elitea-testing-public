---
name: Agent self-attachment client-side-only filter quirk
description: ELITEA-1887 — agent-to-self-attachment is blocked ONLY client-side in ToolMenu.jsx:401, backend returns the self row; "+ Toolkit" picker is the wrong button for agent self-attachment cases, use "+ Agent"
type: feedback
---

## What

`EliteaUI/src/pages/Applications/Components/Tools/ToolMenu.jsx` renders the
Tools-section "+ Agent" popper's list via:

```js
agentsData.rows
  .filter(agent => agent.id !== applicationId)   // line 401 — self-exclusion
  .filter(agent => !agent.has_swarm)              // line 402
```

Confirmed live (ELITEA-1887): the backend `GET
/api/v2/elitea_core/applications/prompt_lib/{project}?agents_type=classic&query=<own-name>`
DOES return the self-agent row (`{"total":1,"rows":[{"id":3,"name":"Test
Agent",...}]}`). The UI shows "No agents found" only because of the
client-side filter above. **This means an automation assertion coupled to
the network response being empty is WRONG** — it would pass/fail for the
wrong reason if either layer changes independently. Assert DOM menu-item
absence (`get_by_role("menuitem", name=agent_name)` not visible/count==0),
not API-response emptiness.

## Case-text trap: "+ Toolkit" vs "+ Agent"

The Tools section has 4 independent add buttons: Toolkit / MCP / Agent /
Pipeline (confirmed twice now — ELITEA-1950, ELITEA-1887). Each opens its
own `UnifiedDropdown`-family popper scoped to ONE entity type. A case
written before this became a written convention may say '"+ Toolkit"
picker' generically when it actually means whichever picker searches the
entity under test — for self-attachment-of-an-Agent, that's the **"+
Agent"** button, not "+ Toolkit" (the Toolkit popper only lists Toolkit-type
entities and is unrelated to agents; with zero toolkits in a project it just
shows "No toolkits available", which would look like a false-positive
"pass" for a self-attachment case if you didn't notice you were searching
the wrong picker entirely). Reclassify as CLARIFICATION (case-text drift,
not a defect) and target the live-accurate button — don't file the "wrong
button" wording as a product bug.

## Testid family (as of ELITEA-1887, EliteaUI@ce74cd40)

- `agent-add-toolkit-button` — existing (ELITEA-1950)
- `agent-add-mcp-button` — existing (ELITEA-1950)
- `agent-add-agent-button` — **added ELITEA-1887**, pushed straight to
  `automation/testids` (no PR under current policy)
- Pipeline button — still has NO testid as of this run; needed if a future
  case exercises pipeline self-attachment or any Pipeline-picker flow.
- Popper search input across all four: shared `toolkit-search-input` testid
  (same `UnifiedDropdown`/MUI `FormControl` wrapper regardless of entity
  type — confirmed via DOM ancestor walk, not just for MCP as ELITEA-1950
  noted, also confirmed for Agent this run).
- Menu items: `role="menuitem"`, no per-item testid, matched by accessible
  name (agent/toolkit/mcp name) — established pattern, don't file this as a
  testid gap, it's the accepted handle shape for dynamically-named list
  items in this codebase.
