---
name: Credentials list — TYPES filter, table view and pagination testids
description: How to drive /credentials/all's type filter and card/table toggle, plus the render race that bites on filter removal
type: project
aliases: [credentials type filter, tags-panel-chip, credentials table view, credentials pagination, view toggle credentials]
tags: [area/credentials, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## TYPES panel is data-derived — seed before you filter

`GET /configurations/types/{project}` returns ONLY the credential types that
actually exist in the project. Project 399 carries a single
`s3_api_credentials` credential, so Github/Jira/Confluence chips simply are
not there until a test seeds credentials of those types.

Chips: `tags-panel-chip-{Label}` (`github`→`Github`,
`s3_api_credentials`→`S3 api credentials`), clear-all: `tags-panel-clear-all`
— both already on `main`. Click = direct activation, URL `?tags[]=Github`,
server-side re-fetch with `&type=github` (RAW key, not the label — wait on
the raw key). Selection is a toggle.

`StyledChip`'s `isSelected` is a styled-prop filtered out of the DOM, so the
chip's own selected state is **not assertable** — use `tags-panel-clear-all`'s
presence as the "a filter is active" signal instead.

## The render race that cost run 1

The list `GET` that follows a filter REMOVAL resolves before React re-renders
the cards — a synchronous card read right after `wait_for_network()` sees
`[]`. `CredentialsListPage._settle_unfiltered_list()` settles on network +
`entity_card.first.wait_for(visible)`. The applying direction does not show it.

## Table view / pagination testids added 2026-08-22

EliteaAI/EliteaUI@84446b15 (`automation/testids`) wired, attribute-only:
`credentials-table-column-header-{name,type,author,created_at,actions}`,
`credentials-table-row-name`,
`credentials-pagination-{page-info,prev-button,next-button}`.
Mechanism: `DataTable.jsx`'s existing `columnTestIdPrefix` mcp-branch extended
to credentials, and `GridTablePagination`'s already-supported testid props
(previously `undefined` for every `DataTable` caller) gated on `isCredentials`.
Side effect of the shared prefix prop: `credentials-table-sort-icon-*` also
appears, unreferenced — same as the pre-existing `mcp-table-sort-icon-*`.

Pagination is only observable above 20 rows: `GridTablePagination` disables
BOTH arrows when `total <= pageSize`. Top up to 21 via
`credential_api.create_credential` (github + `base_url` only — no token).
Page changes put NO page param in the URL. Credentials rows are server-paged,
not client-sliced.

Related: [[vite_hmr_stale_module_on_onedrive]]
