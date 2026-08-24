# Test Case: MCP Dashboard — Filter by Type (Local only)

## Metadata
- **TMS ID**: ELITEA-1943
- **Linked Story**: none
- **Priority**: l1 (case frontmatter `priority: high`; body says "medium" — TMS inconsistency)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with ELITEA-1942 (batch `mcp-w03`)
- **Status**: **blocked** — two independent blockers (unsatisfiable precondition + product defect #1737)
- **Filed**: bug **#1737** (Local filter does not filter), question **#1738**
  (no Local MCP exists or can be created in DEV)
- **Sibling case**: ELITEA-1942 (Remote-only filter) — `ready-for-automation`,
  `test-specs/mcp/l1_mcp-dashboard-filter-by-type-remote_ELITEA-1942.md`

## Why this AFS exists even though the case is blocked

The case was executed live end-to-end; the analysis below is the evidence and
is preserved so nobody re-derives it. **No test is to be written from this AFS
until both blockers clear.** Automating it now would either assert the broken
behaviour (reverse-masking) or assert nothing at all.

## Preconditions (as authored, and what is actually true)

| Case precondition | Live reality (2026-08-24) |
|---|---|
| User logged in | ✅ satisfied (localhost auto-auth) |
| **Local MCPs (ADO, FileSystem, PlaywrightMCP) exist in the project** | ❌ **impossible here.** `GET /api/v2/elitea_core/toolkit_types/prompt_lib/399?mcp=true` → `{"rows": ["mcp"], "total": 1}` — the only MCP toolkit type is `mcp` (= Remote). `/mcps/create` renders exactly one type card, `toolkit-type-card-mcp` ("Remote MCP"): **there is no UI path to create a Local MCP**, and none exists to find. Local MCPs are the pre-built `mcp_*` toolkits, provisioned by the backend, not by a test. → question **#1738** |
| Remote MCPs exist | ✅ 19 present, all Remote |

## Blocked Steps

| Case step | What could not be produced | Blocker |
|---|---|---|
| 3 — "only MCPs with Local type badge are displayed (ADO, FileSystem, PlaywrightMCP)" | No Local MCP exists or can be created in this environment, so there is nothing that *should* be displayed. Even the degenerate honest form (zero results + empty state) is unreachable — see the defect below. | **#1738** (environment/scope decision, human) |
| 2/3/4 — "Local filter is applied … only Local shown … Remote hidden" | With the Local chip selected the product **shows all 19 Remote MCPs**. The filter is visibly active (URL `?tags[]=Local`, chip lit, `tags-panel-clear-all` present) yet the list is the unfiltered list. | **#1737** (product defect, OPEN) |
| 5 — "Remove filter — all MCPs return" | ✅ works (verified live: re-click and Clear-all both restore `/mcps/all` with all 19 cards, clear-all unmounts) — but it is the only step that passes, and it is already covered by ELITEA-1942 step 6/7. | — |

## What was executed (evidence)

1. `GET http://localhost:5173/mcps/all` → 19 MCP cards, every one badged
   `Remote`; Types panel shows exactly two chips, `tags-panel-chip-Local` and
   `tags-panel-chip-Remote`; no `tags-panel-clear-all`.
2. Clicked `tags-panel-chip-Local` → URL becomes
   `/mcps/all?tags%5B%5D=Local`, the chip renders selected, and
   `tags-panel-clear-all` appears — **but the list still shows all 19 Remote
   MCPs** (`set(entity-card-tag-chip texts) == {"Remote"}`, count 19). No
   empty state, no zero-results copy.
3. Repeated from a **pristine context** — fresh `page.goto('/mcps/all?tags[]=Local')`
   — identical result (2/2). Screenshot:
   `.playwright-mcp/ELITEA-1943-local-filter-shows-remote-mcps.png`, uploaded and
   embedded in #1737.
4. Network: selecting Local fires the list query **without any `toolkit_type`
   parameter** — byte-identical to the unfiltered request. (Selecting *Remote*
   correctly adds `&toolkit_type=mcp`.)
5. Console: 0 errors on `/mcps/all` throughout.

**Root cause, read from source** (`src/[fsd]/features/toolkits/lib/hooks/useLoadToolkits.hooks.js:88-96`):
the Local selection resolves to `toolkitTypesData.rows.filter(t => t !== 'mcp')`
= `[]` when the project has no pre-built `mcp_*` type, and an empty selection
is treated as "no filter" rather than "match nothing". The chip list itself is
**hardcoded** to Local+Remote (`tagList`, same file, `isMCP` branch), so Local
is always offered even where it can never match.

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: Local MCPs exist | — | Preconditions table | n/a | **blocked** — #1738 |
| 1 Navigate to MCP list page | page loads | executed (evidence 1) | — | verified live, no test written |
| 2 Click "Local" filter button | filter applied | executed (evidence 2) | — | verified live (URL + clear-all) |
| 3 Only Local-badged MCPs displayed | only Local shown | executed (evidence 2/3) | — | **defect** — all Remote MCPs shown, #1737 |
| 4 Remote MCPs hidden | Remote not visible | executed (evidence 2/3) | — | **defect** — #1737 |
| 5 Remove filter — all MCPs return | all visible | executed (evidence 2) | — | passes live; covered by ELITEA-1942 steps 6-7 |
| Expected Final State: all MCPs return after removal | — | executed | — | passes live |

**Axis 2 — Analyst additions.**

- Pristine-context re-run (fresh navigation with the query param, no prior
  interaction) — *added: gates the finding per the defect-filing pristine-repro
  rule, so #1737 can't be dismissed as stale client state.*
- Network-level check that the Local request carries no `toolkit_type` — *added:
  separates "UI renders a stale list" from "the request itself was never
  filtered"; it is the latter, which points the fix at the hook, not the view.*
- Source read of `useLoadToolkits.hooks.js` — *added: proves the behaviour is
  data-independent (empty type set ⇒ no filter), i.e. it would misbehave the
  same way on any project whose Local type list is empty, not just this one.*

## Un-blocking conditions

1. **#1737 fixed** — selecting Local must issue a filtered query (or render the
   zero-results empty state), never the unfiltered list.
2. **#1738 answered** — either a Local (pre-built `mcp_*`) MCP becomes
   provisionable in the automation project (then the case automates as
   authored, mirroring ELITEA-1942 with `Local` as the parameter), or the case
   is rescoped to "selecting Local with no Local MCPs shows the empty state"
   (then it automates against `empty-state-title`, no test data needed).

Handles are already fully known and on `main` — see ELITEA-1942's AFS
§ Concrete Handles; nothing needs adding when this unblocks.

## Cleanup

None — read-only case, no data created.
