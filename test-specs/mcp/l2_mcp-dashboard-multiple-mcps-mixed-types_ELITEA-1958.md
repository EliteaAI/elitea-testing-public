# Test Case: MCP Dashboard — Multiple MCPs with Mixed Types

## Metadata
- **TMS ID**: ELITEA-1958
- **Linked Story**: none
- **Priority**: l2 (case frontmatter + body both say `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with ELITEA-1945 (batch `mcp-w03`)
- **Status**: **blocked** — two independent blockers, both already tracked
- **Blockers**: bug **[#1737](https://github.com/EliteaAI/elitea-testing-public/issues/1737)** (Local type filter does not filter) · question **[#1738](https://github.com/EliteaAI/elitea-testing-public/issues/1738)** (no Local MCP exists or can be created in DEV). **Nothing new was filed** — both were re-reproduced live today and the occurrence was commented onto each existing issue (dedup: same object, same trigger, same expected/actual).
- **Sibling cases**: ELITEA-1942 (Remote filter, `ready-for-automation`), ELITEA-1943 (Local filter, `blocked` on the same two issues), ELITEA-1945 (pin/unpin, `ready-for-automation` — unrelated flow, clustered only for the session)

## Why this AFS exists even though the case is blocked

The case was executed live end-to-end today; the evidence below is preserved so
nobody re-derives it. **No test is to be written from this AFS until both
blockers clear.** Writing one now would either assert the broken arithmetic
(reverse-masking) or assert nothing at all — with zero Local MCPs in existence,
"Remote + Local == total" degenerates to "19 + 19 == 19", which is false *because
of* #1737, and the type-badge step can only ever see one of the two types.

## Preconditions (as authored, and what is actually true)

| Case precondition | Live reality (2026-08-24, project 399) |
|---|---|
| User logged in | ✅ satisfied (localhost auto-auth) |
| **Both Local MCPs (ADO, FileSystem, PlaywrightMCP) AND Remote MCPs exist in the project** | ❌ **impossible here.** 19 MCPs, **every one badged `Remote`**; `/mcps/create` offers exactly one type card (`toolkit-type-card-mcp` = "Remote MCP") and `GET /api/v2/elitea_core/toolkit_types/prompt_lib/399?mcp=true` → `{"rows": ["mcp"], "total": 1}`. Local MCPs are pre-built backend-provisioned `mcp_*` toolkits — a test cannot create one and none exists to find. → question **#1738** |

The case's entire subject is the **coexistence** of the two types. With one type
present, there is no honest degenerate form: unlike ELITEA-1942 (where "no Local
card is rendered" is a meaningful absence assertion under a Remote filter), this
case's observables are *"both types are visible"* and *"the two filtered counts
sum to the total"* — neither survives the missing half.

## Blocked Steps

| Case step | What could not be produced | Blocker |
|---|---|---|
| 2 — "MCPs of both types coexist (Local: ADO, FileSystem, PlaywrightMCP; Remote: Web Search, EliteaMCP, Github)" | No Local MCP exists or can be created. Only the Remote half is observable. | **#1738** (environment/scope decision, human) |
| 3 — "Every card shows a type badge matching its actual type" | Verifiable for Remote only (19/19 badged `Remote`, badge count == card count). The *matching* half of the assertion — that a Local MCP is badged `Local` — is unreachable. Partially covered already by ELITEA-1942 step 4. | **#1738** |
| 6 — "Apply Remote filter — count visible Remote MCPs" | ✅ **works** (19 cards, all `Remote`, request gains `&toolkit_type=mcp`). Already automated by ELITEA-1942. | — |
| 7 — "Apply Local filter — count visible Local MCPs" | ❌ The Local filter **does not filter**: URL becomes `?tags[]=Local`, the chip lights, `tags-panel-clear-all` appears — and the list still shows **all 19 Remote MCPs**. The list request is byte-identical to the unfiltered one (no `toolkit_type` parameter at all). The count read here is meaningless. | **#1737** (product defect, OPEN) |
| 8 — "Remove filter — total == Remote + Local" | ❌ Live this reads **19 == 19 + 19**. The case's final observable is false for as long as #1737 stands, regardless of #1738. | **#1737** |
| Expected Final State: total equals sum of the two filtered counts | ❌ Same as step 8. | **#1737** |

*(The case's step numbering jumps 3 → 6 in the TMS source; steps 4 and 5 do not
exist. Recorded as authored, no content is missing — noted so a reader does not
hunt for two dropped steps.)*

## What was executed (evidence, live 2026-08-24)

1. `GET http://localhost:5173/mcps/all` → **19** MCP cards. `entity-card-name`
   count 19, `entity-card-tag-chip` count **19**, badge set **`{"Remote"}`**.
   Types panel renders exactly two chips (`tags-panel-chip-Local`,
   `tags-panel-chip-Remote`); `tags-panel-clear-all` absent.
2. Clicked `tags-panel-chip-Remote` → URL `/mcps/all?tags%5B%5D=Remote`,
   `tags-panel-clear-all` present, **19** cards, badge set `{"Remote"}`.
   Request: `…/tools/prompt_lib/399?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0`
   **`&toolkit_type=mcp`**.
3. Clicked `tags-panel-clear-all` → back to `/mcps/all`, 19 cards.
4. Clicked `tags-panel-chip-Local` → URL `/mcps/all?tags%5B%5D=Local`,
   `tags-panel-clear-all` present, **19 cards, badge set `{"Remote"}`**, no
   empty state. Request: **byte-identical to the unfiltered query — no
   `toolkit_type` parameter.** → #1737 reproduced (3rd independent reproduction,
   counting ELITEA-1943's two).
5. Clicked `tags-panel-clear-all` → `/mcps/all`, 19 cards, clear-all unmounted.
6. Count identity as the case defines it: **total 19, Remote 19, Local 19 ⇒
   19 ≠ 38.**
7. Console: **0 errors** on `/mcps/all` throughout.

**Root cause (unchanged from ELITEA-1943's analysis, re-confirmed in source):**
`src/[fsd]/features/toolkits/lib/hooks/useLoadToolkits.hooks.js` resolves the
Local selection to `toolkitTypesData.rows.filter(t => t !== 'mcp')` = `[]` when
the project holds no pre-built `mcp_*` type, and an empty selection is treated
as "no filter" rather than "match nothing". The chip list itself is **hardcoded**
to Local+Remote (`tagList`, `isMCP` branch), so Local is always offered even
where it can never match.

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: both Local and Remote MCPs exist | — | § Preconditions | n/a | **blocked** — #1738 |
| 1 Navigate to MCP list page | page loads | executed (evidence 1) | — | verified live; already asserted by ELITEA-1942 step 1 |
| 2 Both Local and Remote MCPs visible | both types present | executed (evidence 1) | — | **blocked** — only Remote exists, #1738 |
| 3 Every card's type badge matches its type | badges correct | executed (evidence 1) | — | **partial / blocked** — Remote half true (19 badges, set `{Remote}`, badge count == card count) and already asserted by ELITEA-1942 step 4; Local half unreachable, #1738 |
| 6 Apply Remote filter, count | count noted | executed (evidence 2) | — | verified live; automated by ELITEA-1942 steps 3-4 |
| 7 Apply Local filter, count | count noted | executed (evidence 4) | — | **defect** — filter is a no-op, all 19 Remote listed, #1737 |
| 8 Remove filter — total == Remote + Local | identity holds | executed (evidence 5-6) | — | **defect** — 19 ≠ 19 + 19, #1737 |
| Expected Final State: total == sum of filtered counts | — | executed | — | **defect** — #1737 |

**Axis 2 — Analyst additions.**

- Asserted `badge count == card count` alongside the badge set — *added while
  executing step 3: `set(badges) == {"Remote"}` alone passes if a card renders
  no badge at all. (Carried by ELITEA-1942's merged assertion, recorded here so
  the observation is not lost.)*
- Captured the **request** for each filter state, not just the rendered count —
  *added: it is the request diff (`&toolkit_type=mcp` present for Remote,
  absent for Local) that distinguishes "the filter ran and matched everything"
  from "the filter never ran", and it is the evidence #1737 needs.*
- Console-error check across the whole flow — *standard side-channel check; 0
  errors.*

## Concrete Handles (confirmed during exploration — for whoever picks this up post-fix)

| Element | Handle | Provenance (verified 2026-08-24, `cd ../EliteaUI && git fetch origin` first) | Notes |
|---|---|---|---|
| Types-panel chip (dynamic) | `[data-testid="tags-panel-chip-{TypeName}"]` | **on-main ✓** | Already `McpListPage.TYPE_FILTER_CHIP`. Hardcoded to `Local` + `Remote`. |
| Types-panel "Clear all" | `tags-panel-clear-all` | **on-main ✓** | Already `McpListPage.tags_clear_all_button`. Unmounted when no chip is selected ⇒ assert absence with `to_have_count(0)`. |
| Card type badge (page-wide) | `entity-card-tag-chip` | **on-main ✓** | Already `McpListPage.entity_card_tag_chip`; `get_visible_type_badges()` shape ported from `CredentialsListPage`. |
| MCP card name | `entity-card-name` | **on-main ✓** | `McpListPage.get_card_names()` — the count source. |
| Zero-results empty state | `empty-state-title` | **on-main ✓** | `McpListPage.empty_state_title`. **Never reached** under the Local filter today — that is the defect, and it is the handle the post-fix test would assert if the project still had no Local MCPs. |

**No new testids are required.** Every handle this case would need already
exists on `main` and is already wired into `McpListPage` by ELITEA-1942's
implementation. The blocker is data + product behaviour, not tooling.

## Network Behavior

| State | Request |
|---|---|
| unfiltered | `GET /api/v2/elitea_core/tools/prompt_lib/399?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0` |
| Remote filter | same **+ `&toolkit_type=mcp`** (server-side filtering) |
| **Local filter** | **byte-identical to unfiltered — no `toolkit_type`** ⇒ #1737 |
| Types panel data | `GET /api/v2/elitea_core/toolkit_types/prompt_lib/399?mcp=true` → `{"rows": ["mcp"], "total": 1}` (the chip list is NOT derived from it) |

## Unblock criteria (what has to be true before this case is automatable)

1. **#1738 resolved** — a Local MCP exists in the target project (backend
   provisioning, or a documented seeding path), *or* a human rules the Local
   half out of scope and the TMS case is rewritten accordingly.
2. **#1737 fixed** — the Local chip actually filters (either to the Local set,
   or to a zero-result empty state when none exist).

With **only #1737 fixed and still no Local MCP**, a degenerate honest version
becomes possible: Local ⇒ 0 cards + `empty-state-title`, and `total == Remote +
0`. That is a materially weaker test than the case describes and is a human's
scope call, not the analyst's — it is offered here, not assumed.

## Known Defects Found

- **#1737** (OPEN, `bug`) — re-reproduced live, occurrence commented on the
  issue with today's table. Not re-filed.
- **#1738** (OPEN, `question`) — re-verified live, occurrence commented on the
  issue. Not re-filed. It now gates three cases: ELITEA-1942 (partially),
  ELITEA-1943, ELITEA-1958.

## Cleanup

None — read-only case, no data created. Project left as found (19 MCPs, no
filter active, nothing pinned).
