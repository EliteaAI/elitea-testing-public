# Surface digest: Toolkit Indexes (`/toolkits/:tab/:toolkitId` → Indexes accordion → index routes)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during GAP-042 analysis, 2026-07-24,
project `Private`/399, local `http://localhost:5173`, EliteaUI
`automation/testids` branch).

## Route map — READ THIS FIRST, it corrects a coverage-gap false positive

The "Indexes" feature has **two unrelated implementations in the codebase**:

1. `src/[fsd]/features/toolkits/indexes/ui/IndexDetails/*` (`IndexDetails`,
   `IndexViewToggler`, `IndexViews`, `IndexConfig`, `IndexHistory`,
   `IndexActions`, `IndexChat`, ...) — a tab-toggler pattern (Run /
   Configuration / History tabs inside ONE view). **DEAD CODE as of this
   session** — confirmed via `git grep -n "<IndexesContainer" EliteaUI/src`
   (exactly 1 hit, `src/pages/Toolkits/ConfigurationTab.jsx:68`, and that call
   site hardcodes `listOnly` — the only branch that would render
   `IndexDetails` never fires). Do not target this tree for new coverage; do
   not add testids to it (see GAP-042's AFS,
   `test-specs/toolkits-indexes/l3_toolkit-index-edit-view-toggler-dead-code_GAP-042.md`,
   for the full grep evidence).
2. `src/[fsd]/pages/indexes/{CreateIndex,RunIndex,IndexHistoryPage}.jsx` (+
   `RunIndexPanel.jsx`, `RunIndexSettingsPanel.jsx`,
   `RunIndexGeneralSection.jsx`, `RunIndexScheduleContent.jsx`,
   `RunIndexResultsPanel.jsx`, `RunIndexBanner.jsx`, `RunIndexConfigSection.jsx`,
   `RunIndexScheduleAction.jsx`) — the ACTUAL live implementation, wired as
   three separate ROUTES, not a tab toggle:

   | Route | Component | Purpose |
   |---|---|---|
   | `/toolkits/:tab/:toolkitId/index/new` | `CreateIndex.jsx` | Create a new index |
   | `/toolkits/:tab/:toolkitId/index/:indexName` | `RunIndex.jsx` | Run/view an existing index |
   | `/toolkits/:tab/:toolkitId/index/:indexName/history` | `IndexHistoryPage.jsx` | Index history (separate page, NOT a tab) |

   (`ProtectedRoutes.jsx:241-243`; same routes serve both `/toolkits/...` and
   `/mcps/...` via `EditToolkit`/`isMCP` — see below, though MCP toolkits
   never reach these routes in practice.)

**Any future case targeting "Indexes" behavior must explore tree #2 fresh —
none of tree #1's testid names, tab labels, or tooltip strings carry over.**

## MCP toolkits NEVER show the Indexes tab

`EditToolkit.jsx`'s `shouldHideIndexesTab`: `if (mcpId) return true;`
unconditionally — before it even checks the toolkit's tool schema. Confirmed
in source (`src/pages/Toolkits/EditToolkit.jsx:~203`). **A case that wants to
exercise Indexes must use a non-MCP toolkit type** (Artifact confirmed
working as a fixture — see below; GitHub/Confluence/SharePoint etc. likely
also qualify if their tool schema includes `index_data` in
`selected_tools.items.enum`, not verified this session).

`EditToolkit` (`src/pages/Toolkits/EditToolkit.jsx`) is the SAME component for
both `/toolkits/:tab/:toolkitId` and `/mcps/:tab/:mcpId`
(`ProtectedRoutes.jsx:240,250` — `<EditToolkit />` vs `<EditToolkit isMCP />`),
just with `isMCP` flipping the indexing-hidden gate and a couple of other
props. Not a separate `McpFormPage`-style component for this purpose.

## Indexing-availability gate (`disableIndexingReason`, `EditToolkit.jsx`)

The "Indexes" accordion in the Configuration tab renders
`"Indexing is not available for now"` instead of the index list whenever:
- `needToSelectIndexData` — the toolkit's `selected_tools` doesn't include
  `index_data` (`IndexesToolsEnum.indexData`), OR
- `loading` — `!settings.pgvector_configuration` (falsy/null) OR
  `!settings.embedding_model` OR the schemas/config are still fetching.

**Confirmed live, this session, project `Private`/399: `pgvector_configuration`
has NO available option other than `"None"`.** The dropdown is fed by
`GET /configurations/models/{projectId}?section=vectorstorage&include_shared=true`,
which returned `{"total": 0, "items": [], "default_model_name": null,
"default_model_project_id": null}` — **zero vectorstorage/pgvector
configurations exist anywhere this project can see, private or shared.**
Neither of the 2 toolkits that existed in this project
(`ToolkitAPI.list_all_toolkits()`) had one configured either.

**This is a standing environment/test-data gap for THIS project, not specific
to GAP-042** — any future case needing a working (`completed`/`in_progress`/
history-populated) index cannot proceed until a vectorstorage credential is
provisioned somewhere this suite's project can reach. Re-run the
`GET /configurations/models/{projectId}?section=vectorstorage` check above as
a fast precondition probe before investing in a live index-creation flow —
if it comes back empty, stop and flag rather than debugging further.

## Fast fixture setup — API, index-capable toolkit in 3 calls

Mirrors the pattern `test-specs/mcp/_surface.md` documents for MCP toolkits.
For any case whose precondition is "a toolkit with Indexes enabled" (not
specifically "created via the UI"):

```python
from api.client import ArtifactAPI, ToolkitAPI
import uuid

art = ArtifactAPI(browser_cookies=[])   # ELITEA_API_TOKEN Bearer auth, no cookies needed
tk = ToolkitAPI(browser_cookies=[])

bucket_name = f"autotest-idx-{uuid.uuid4().hex[:8]}"
art.create_bucket(bucket_name)
art.upload_file(bucket_name, "sample.txt", b"...", content_type="text/plain")

toolkit = tk.create_artifact_toolkit(
    name=f"autotest_idx_{uuid.uuid4().hex[:6]}",
    description="...",
    bucket_name=bucket_name,
)
# toolkit["id"] -> navigate to /toolkits/all/{id}, expand "Indexes" accordion.
```

Confirmed live: the Indexes accordion IS present and auto-expanded
(`Mui-expanded` class) for an Artifact toolkit with `index_data` selected —
gated only by the `pgvector_configuration` check above, not by anything
about the Artifact type itself.

**Cleanup gap, confirmed this session:** `ToolkitAPI.delete_toolkit(id)`
works (204, confirmed). `ArtifactAPI.delete_bucket(bucket_name)` 404'd on
BOTH the bare-name URL and the `p--{project}.{bucket_name}` id-format retry
for a bucket created via `create_bucket()` this same session — worth a fresh
look before relying on it for teardown of a bucket-with-contents (this
bucket had exactly one small file). Toolkit deletion alone is confirmed
sufficient to stop it appearing in `list_all_toolkits()`; the orphaned
bucket is harmless leftover test data, not a correctness blocker.

## No testids anywhere on the Indexes accordion (Configuration tab)

Confirmed via live DOM walk: the "Indexes" accordion header, its
"Indexing is not available for now" placeholder, and the Pgvector
Configuration / Embedding Model selects all render with **zero
`data-testid` attributes** — same `add-data-testid` gap as everything else
in this feature area. Not yet flagged by any prior case (first analyst to
reach this section live, per this digest being newly created).

## Open questions for whoever automates the real flow next

- Does the GitHub/Confluence/SharePoint toolkit type also expose `index_data`
  in its tool schema (i.e., qualify for the Indexes tab)? Not checked this
  session — only Artifact was verified.
- Is there ANY project in this DEV environment (org-shared or another
  team project) with a working vectorstorage credential already configured?
  Not checked — would unblock testing the real `RunIndex.jsx`/
  `IndexHistoryPage.jsx` flow without needing new infrastructure.
