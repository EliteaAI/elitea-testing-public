# Test Case: Artifacts Landing Page – Collapse and Expand Panels

## Metadata
- **TMS ID**: ELITEA-1807
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- At least one bucket is present so both panels are visible — satisfied by the
  project's **existing** buckets (766 rendered live in `Private`/399). **No
  seeding at all**: this case observes panel chrome, not bucket data, so it is
  fully read-only (workflow skill Hard Rule 10).

## Test Data
### existing-stable (read-only)
- Any bucket rows already present in the project — only their *presence* and
  *visibility* are read, never their contents.
- Sidebar entries rendered for this user (live-confirmed 2026-08-21):
  `Chats, Agents, Pipelines, Skills, Toolkits & Indexes, MCPs, Credentials,
  Applications, Artifacts` (nav items) + `Settings` + `Catalog` (bottom buttons).

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| BUCKETS panel `<<` / `>>` toggle | `artifacts-buckets-panel-toggle-button` (+ `data-collapsed` state attr) | **added this run**, `BucketHeader.jsx`, EliteaAI/EliteaUI@9062dff0 — on `automation/testids` only (awaiting human promotion to main) |
| Sidebar `<` / `>` toggle | `sidebar-collapse-toggle-button` (+ `data-collapsed` state attr) | **added this run**, `Sidebar.jsx`, same commit — `automation/testids` only |
| Sidebar Settings button | `sidebar-settings-button` | **added this run** via a caller-supplied `testId` prop on the shared `SidebarButton` (shared-component rule, `.agents/testing.md` § Locator policy) — same commit |
| Sidebar Agent HUB / Catalog button | `sidebar-agent-hub-button` | **added this run**, `AgentHubButton.jsx` — same commit |
| Sidebar nav items | `sidebar-menu-item-{value}` (`chat`, `agents`, `pipelines`, `skills`, `toolkits`, `mcps`, `credentials`, `applications`, `artifacts`) | **pre-existing** — `SidebarBody.jsx` already passes `testId={\`sidebar-menu-item-${i.value}\`}`; on-main status inherited from that commit |
| BUCKETS heading | `artifacts-buckets-heading` | on `automation/testids` (EliteaAI/EliteaUI@6449a5c4 era / pre-existing) |
| Storage selector | `artifacts-storage-selector` | pre-existing (ELITEA-1803 run) |
| Buckets footer count | `artifacts-buckets-footer-count` | pre-existing (ELITEA-1803 run) |
| Any bucket row | `[data-testid^="artifacts-bucket-row-"]` (`ArtifactsPage.BUCKET_ROW_ANY_SELECTOR`) | pre-existing |

**Why `data-collapsed` and not a state-switched testid.** Both toggles are ONE
live element whose *icon* flips (`<<`→`>>`, `<`→`>`); the icons are untagged
SVGs. `.agents/testing.md` § Locator policy (PR #581 ruling) forbids a testid
whose value or presence changes with state and prescribes exactly this shape:
one stable testid + a `data-*` state attribute, asserted by filtering on it.
`data-collapsed` is rendered from the same `collapsed` / `sideBarCollapsed`
value that selects which icon renders, so asserting it IS asserting the icon
swap the case describes.

## Test Steps
1. Navigate to `/artifacts` (viewport 1600x900), wait for page load
   - **Verify**: both panels are visible — `artifacts-buckets-heading` visible,
     at least one `artifacts-bucket-row-*` visible, the buckets toggle reads
     `data-collapsed="false"`, the sidebar toggle reads `data-collapsed="false"`,
     and every enumerated sidebar entry is visible **with its label text**.
2. Click `artifacts-buckets-panel-toggle-button` (the `<<` icon)
   - **Verify**: the toggle now reads `data-collapsed="true"` (i.e. it renders
     `>>`) and is still visible; the panel is fully collapsed — the heading, the
     storage selector and the footer count are **unmounted** (count 0, live:
     `BucketsPanel.jsx` gates all three on `!collapsed`) and no bucket row is
     visible any more (rows stay in the DOM behind
     `display: collapsed ? 'none' : 'flex'` — asserted as *not visible*, not as
     count 0).
3. Click the same toggle again (now the `>>` icon)
   - **Verify**: `data-collapsed="false"`; the heading, storage selector and
     footer count are back; a bucket row is visible again.
4. Click `sidebar-collapse-toggle-button` (the `<` icon)
   - **Verify**: the toggle reads `data-collapsed="true"`; the sidebar is in
     icon-only mode — every `sidebar-menu-item-*` (plus Settings and Agent HUB)
     is **still visible** but its **label text is empty** (live:
     `showLabel={!sideBarCollapsed}` unmounts the label `<Typography>`, the icon
     stays).
5. Click the same toggle again (now the `>` icon)
   - **Verify**: `data-collapsed="false"` and every enumerated entry is visible
     again **with its label text**: `Chats, Agents, Pipelines, Skills,
     Toolkits & Indexes, MCPs, Credentials, Applications, Artifacts, Settings,
     Catalog`.
   - **CLARIFICATION #1619** — the case text lists `Toolkits` and `Agent HUB`.
     Live the labels are **`Toolkits & Indexes`** (`SidebarBody.jsx`) and
     **`Catalog`** (`AgentHubButton.jsx`). Nothing is broken; the case copy is
     stale, so the live contract is asserted (reverse-masking guard) and the
     case-text drift is filed. Sibling: #1208 (same rename, Catalog page header).
6. With the sidebar expanded, collapse and then expand the BUCKETS panel
   - **Verify**: across both toggles the sidebar's `data-collapsed` stays
     `"false"` and its labels stay visible — the BUCKETS panel state does not
     leak into the sidebar.
7. Toggle the sidebar while the BUCKETS panel is in each of its two states
   - **Verify (a)**: with BUCKETS expanded, collapsing then expanding the
     sidebar leaves the buckets toggle at `data-collapsed="false"` with the
     heading visible throughout.
   - **Verify (b)**: with BUCKETS **collapsed**, collapsing then expanding the
     sidebar leaves the buckets toggle at `data-collapsed="true"` and the
     heading unmounted throughout — the stronger direction of the same
     independence claim (a state that could be *reset* by the other panel's
     re-render).
   - Finally restore both panels to expanded (the case's expected final state).

## Expected Results
- The BUCKETS panel collapses fully (`<<` → `>>`) and restores completely
  (heading, storage selector, footer, bucket list).
- The navigation sidebar collapses to icon-only (`<` → `>`) and expands back
  with every icon **and** label.
- Each panel's state is unaffected by the other panel's toggling, in both
  directions and from both starting states.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: ≥1 bucket present so both panels visible | both panels visible | step 1 | ≥1 `artifacts-bucket-row-*` visible + heading visible | asserted *(existing project buckets, read-only)* |
| Test Data: sidebar item list | items present | steps 1/4/5 | per-testid label map | asserted *(2 labels corrected per CLARIFICATION #1619)* |
| 1 Navigate with both panels visible | both panels visible | step 1 | heading + bucket row + both toggles at `data-collapsed="false"` + labels | asserted |
| 2 Click `<<` → panel collapses fully, `>>` appears | collapsed + icon flip | step 2 | `data-collapsed="true"` (icon flip) + heading/storage/footer count 0 + rows not visible | asserted |
| 3 Click `>>` → panel restored, bucket list visible | expanded + list back | step 3 | `data-collapsed="false"` + heading/storage/footer visible + bucket row visible | asserted |
| 4 Click `<` → sidebar icon-only, `>` appears | icon-only + icon flip | step 4 | `data-collapsed="true"` + every item still visible with **empty** label text | asserted |
| 5 Click `>` → full mode, icons AND labels | all labels visible | step 5 | each testid's text == its live label, all visible | asserted |
| 6 BUCKETS toggling does not affect the sidebar | sidebar unchanged | step 6 | sidebar `data-collapsed` + label visibility re-read after each BUCKETS toggle | asserted |
| 7 Sidebar toggling does not affect the BUCKETS panel | BUCKETS unchanged | step 7 | buckets `data-collapsed` + heading state re-read after each sidebar toggle, from BOTH buckets states | asserted |
| Expected Final State: both independently toggleable, labels/list visible after each expansion | — | steps 1-7 + restore | the assertions above | asserted |

### Axis 2 — Analyst additions
- **Independence tested from BOTH starting states** (step 7b): the case only asks
  that toggling one doesn't change the other, which a test could satisfy while
  never checking the direction that actually breaks in practice — a re-render
  *resetting* a collapsed BUCKETS panel back to expanded. Cheap, and it is the
  half a regression would hit.
- **Collapse asserted as unmount-vs-invisible, deliberately split** (step 2):
  heading/storage/footer are asserted `count == 0` (they really are unmounted)
  while bucket rows are asserted **not visible** (they remain in the DOM under
  `display: none`). Asserting the wrong one of these two would be a test that
  passes for the wrong reason.
- **Labels asserted as text on the item's own testid**, not as page-level text —
  a page-wide `get_by_text("Artifacts")` would match the breadcrumb and the
  page heading too.
- **NOT asserted: console errors.** Same reasoning as the ELITEA-1803/1804/1805
  spec — `.agents/testing.md` § Unconfirmed records a confirmed recurring
  environmental console-500/404 flake class on this project; importing it into a
  pure chrome-toggling test would buy noise, not signal.
- **NOT asserted: pixel widths / animation.** The panel widths (`3.75rem`
  collapsed vs `leftPanelWidth`) are styling the case never mentions; asserting
  computed CSS would bind the test to the theme.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| *(none)* | — | The test performs **no** substitution: no seeding, no `page.route`, no injected state. Every observable (panel collapse state, mounted/visible chrome, sidebar label text) is rendered by the product from its own React state in response to real clicks. Preconditions are satisfied by data that already exists in the project. |

## Blocked Steps
None.
