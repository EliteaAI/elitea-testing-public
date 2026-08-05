# Settings → Personal Tokens surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Personal
Tokens surface (`/settings/tokens`, renders `PersonalTokens.jsx`). Not a
substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2277, 2026-08-05.

## Route & component tree
- `/settings/tokens` (bare path, `APP_PREFIX` empty on localhost) routes to
  `TokensSettings` = `src/[fsd]/pages/settings/PersonalTokens.jsx` via
  `ProtectedRoutes.jsx:352-353`. Reachable directly, no drawer-click needed —
  same pattern as `/settings/notifications` and `/settings/project-context`.
- Component tree: `PersonalTokens.jsx` → `DrawerPageHeader` (shared, title +
  search + add-button) + `TokensSection` → `TokensTable.jsx` (built on the
  shared `grid-table` components, same family as `NotificationTable.jsx`) +
  `SettingsPreview` (opens in a `react-split` pane on eye-icon click) +
  `GeneratedTokenDialog` (opens via a separate route, `CreatePersonalToken.jsx`,
  on add-button click — `onAddPersonalToken` navigates to
  `RouteDefinitions.CreatePersonalToken`, doesn't open an inline modal).

## Three page states (important — case authors/testers must account for these)
1. **Loading** (`isFetching || isFetchingTokens`): a `CircularProgress` only.
2. **Empty** (`tokens.length === 0`): `EmptyStatePage` ("No tokens yet" /
   "Create your first API token") — the table, its columns, and the 4 action
   icons DO NOT EXIST in this state. A case asserting table layout needs at
   least one token present first.
3. **Populated** (`tokens.length > 0`): the table renders, per below.

## `showDownload` gating — the icon-count precondition
`TokensSection`'s `showDownload` prop = `!!model.configuration_uid &&
selectedProjectId !== PUBLIC_PROJECT_ID` (`PersonalTokens.jsx:265`). This is
a **single page-level boolean**, not per-row — every row shows the same set
of icons. When `true` (default model resolved + non-Public project): all 4
icons (eye, VSCode, JetBrains, trash) render on every row. When `false`
(Public project, or zero model configurations): only the trash icon renders
(1 icon). Confirmed live on `${ELITEA_PROJECT_ID}` (399, "Private") —
`showDownload` is `true`, all 5 existing rows show all 4 icons identically.

## Live data available (Private project / `${ELITEA_PROJECT_ID}` = 399)
5 persistent personal tokens observed 2026-08-05: `for_ui_tests`, `Levon`,
`Marian` (expired), `New` (expired), `uautomate`. Real leftover test data,
not a fixture — same risk class as `settings-notifications`'s live-history
dependency: if bulk-deleted, a test relying on "table has rows" precondition
needs its own setup (create a token via UI/API first). Prefer reading this
existing data over seeding for read-only layout assertions.

## Testid status — ZERO in the personal-tokes component tree (confirmed 2026-08-05)
`grep -rn "data-testid\|testId" "src/[fsd]/features/settings/ui/personal-tokes/"`
→ no hits. `DrawerPageHeader.jsx` (shared across 14+ settings pages) also has
NO testid threading today for title/search/add-button — any case touching
those needs new props added (see below), not a hardcoded testid in the
shared file.

## Reusable shared-component testid mechanisms (cheaper than a real add)
Two `grid-table` primitives already accept testid props that `TokensTable.jsx`
simply doesn't wire yet — same "wire an existing prop" pattern documented in
`test-specs/settings-notifications/_surface.md`:
- `GridTableHeader` accepts `columnTestIdPrefix` → generates
  `{prefix}-column-header-{field}` per column. Confirmed in source
  (`GridTableHeader.jsx`).
- `GridTableRow` accepts `'data-testid': dataTestId` (static, one value
  repeated per row — confirmed in source, `GridTableRow.jsx`).
- `DeleteEntityButton` accepts a `testId` prop (`data-testid={testId}` on its
  wrapping `Box`) — confirmed in source (`DeleteEntityButton.jsx`), same
  component used across the app's other delete-with-confirmation flows.
- `SimpleSearchBar` (`src/[fsd]/shared/ui/input/SimpleSearchBar.jsx:59`)
  already reads `props['data-testid']` and wires it onto the native
  `<input>` via `inputProps` — but `DrawerPageHeader.jsx` doesn't forward
  `slotProps.searchInput.testId` to it yet (a `DrawerPageHeader` prop-thread
  gap, not a `SimpleSearchBar` gap).

## `DrawerPageHeader.jsx` gaps (shared component, used by 14+ settings pages)
No `titleTestId` prop, no `slotProps.addButton.testId` prop, no
`slotProps.searchInput.testId` forwarding — all three need adding. Since
this is a SHARED component (`.agents/testing.md` § "shared components never
hardcode feature-scoped testids"), the fix is caller-supplied testid props,
not a hardcoded value. Once added, every OTHER page built on
`DrawerPageHeader` (`SecretsContent`, `ProjectGeneralContent`,
`AIProvidersContent`, `Users.jsx`, `EnvironmentSettings.jsx`, indexes pages,
etc.) can reuse the same props — future cases on those surfaces should check
this digest / grep the component before re-requesting the same prop-thread.

## Gotchas
- The add-button's `onAdd` handler **navigates to a separate route**
  (`RouteDefinitions.CreatePersonalToken`, `/settings/create-personal-token`
  presumably) — it does NOT open an inline dialog on this page. A future
  case that clicks "+" should expect a navigation, not a modal.
- `TOKENS_COLUMNS` (`TokensTable.jsx`) is a static 4-entry config array
  (`name`, `token`, `expires`, `actions`) — no responsive column-hiding logic
  observed for this table (unlike some other grid-table consumers); a
  narrower/mobile viewport was not tested live, flag if a future case needs
  responsive-breakpoint coverage.
- Console: 0 errors, 0 warnings on page load with 5 populated rows.
