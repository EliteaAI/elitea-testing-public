# Test Case: Remote MCP — Test Settings — Fullscreen Mode

## Metadata
- **TMS ID**: ELITEA-1939
- **Linked Story**: none
- **Priority**: l3 — TMS frontmatter `priority: medium`; same `medium → l3_`
  precedent this folder's ELITEA-1937 / ELITEA-1947 AFS files set.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with
  ELITEA-1938 + ELITEA-1940 (shared session; every case's steps executed and
  observed individually — this case DIVERGED from the family and carries its
  own status)
- **Status**: blocked
- **Filed**: #1726 (`question` + `case-text-drift`)

## Why this case is `blocked`, in one line

**The fullscreen toggle the case exists to test was deliberately removed from
the toolkit/MCP test surface by the EL-5947 redesign.** Steps 2–6 — the whole
case — depend on a control that no longer renders, so the observable cannot be
produced honestly and the call belongs to a human
(`.agents/testing.md` § Fidelity policy).

## Preconditions (as executed)

- Authenticated on localhost (automatic via `VITE_DEV_TOKEN`).
- Remote MCP `autotest_mcp_run_tool` (id **2140**, `Private` project), fixture
  `https://mcp.deepwiki.com/mcp`, tools loaded `3 / 3` this session.

## What was actually executed

| Case step | What was done | What was observed |
|---|---|---|
| 1 Open a Remote MCP detail page with Test Settings panel visible | `/mcps/all/2140` → **Load Tools** → **Save** → **Test** → `/mcps/all/2140/test` | Test page loads as a **two-column split**: left header `Test Settings`, right header `Results`. Confirmed in all three panel states (empty-state, tool-selected, post-run). |
| 2 Click "Fullscreen mode" button in test panel header | Full DOM inventory of **every** `<button>` on the page, in each of the three states | **BLOCKED — no such control exists.** No fullscreen/expand icon, no `aria-label` matching fullscreen, no button of any kind in either column header. The only buttons on the page belong to the sidebar, breadcrumb, connection status (`toolkit-connection-login-button`), the Model Settings gear, `toolkit-test-run-tool-button`, and (post-run) `chat-copy-button`. |
| 3 Verify test panel expands to fullscreen | not reachable | — |
| 4 Verify tool selection + chat remain functional in fullscreen | not reachable | — |
| 5 Click fullscreen toggle again | not reachable | — |
| 6 Verify panel returns to normal split-pane size | not reachable | — |

Evidence: `test-results/screenshots/ELITEA-1938-1939-mcp-test-page-no-clear-no-fullscreen.png`
(also uploaded to the `evidence` release and embedded in #1726).

**Interaction-discovery ladder** (`.agents/role-overrides.md`) was exhausted
before this verdict: no debounce/Enter/adjacent-control/blur path applies to a
non-existent button, the nearest working analogs were compared (the Skill test
panel and the Toolkit-Index chat DO still ship the toggle — see below), and the
decisive step — reading the source — was performed. The intended mode per code
is "this surface renders no fullscreen toggle".

## Root cause — removed by EL-5947, still present on sibling surfaces

Git archaeology in `EliteaAI/EliteaUI` (verified after `git fetch origin`):

```
src/[fsd]/features/toolkits/ui/test-tools/TestTools.jsx  @ 0cff136d^  (pre 2026-07-30)
   22:  import FullScreenToggle from '@/components/Chat/FullScreenToggle';
  191:  <FullScreenToggle isFullScreenChat={isFullScreenChat} setIsFullScreenChat={...} />
```

- **EliteaAI/EliteaUI@0cff136d** — `Feat/el 5947/new toolkit run UI (#663)`,
  2026-07-30 — removed `FullScreenToggle` from the toolkits feature entirely.
- **EliteaAI/EliteaUI@cb030b7d** — `feat: [EL-6277] move indexes into the
  details right panel (#803)`, 2026-08-20 — rewrote the panel as
  `ToolkitTestPanel.jsx` on its own route. No fullscreen state, no toggle, no
  `isFullScreenChat` anywhere in the component tree.

`FullScreenToggle.jsx` **still exists and is still wired** on other surfaces —
`SkillTestPanel.jsx`, `IndexChat.jsx`, Applications `ConfigurationTab.jsx`. It
is the MCP/toolkit *test* surface specifically that lost it. A defensible read
is that the new two-column layout supersedes the need (results already occupy a
dedicated half-pane rather than sharing the settings column) — but that is a
product judgement, not an automation one.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | — | satisfied |
| Precondition: Remote MCP detail page with Test Settings panel open | met | executed step 1 | executed step 1 | satisfied — **panel is now a separate ROUTE** (EL-6277) |
| 1 Open a Remote MCP detail page with Test Settings panel visible | page loads with panel | executed step 1 | executed step 1 | asserted (with the route correction) |
| 2 Click "Fullscreen mode" button in test panel header | panel expands | — | — | **blocked** — control does not exist (#1726) |
| 3 Verify panel expands to fullscreen | full-screen occupancy | — | — | **blocked** — depends on step 2 |
| 4 Verify tool selection + chat functional in fullscreen | dropdown + chat usable | — | — | **blocked** — depends on step 2 |
| 5 Click fullscreen toggle again | exits fullscreen | — | — | **blocked** — depends on step 2 |
| 6 Verify panel returns to split-pane size | standard layout | — | — | **blocked** — depends on step 2 |
| Expected Final State: returns to split-pane after toggling off | — | — | — | **blocked** |
| Pass/Fail: toggle works both directions | — | — | — | **blocked** |

### Axis 2 — Analyst additions

- None — same reasoning as ELITEA-1938: inventing assertions around a removed
  subject would manufacture coverage the case never asked for.

## Blocked Steps

- **Steps 2–6 (the entire case).** To unblock, *either*:
  - **(a)** a human ruling that the case is retired or rewritten for the
    post-EL-6277 two-column Test page; **or**
  - **(b)** a human ruling that this is a feature-parity gap against the
    Skill / Toolkit-Index / Agent chat surfaces that still ship the toggle —
    which escalates to `EliteaAI/elitea_issues` via `file-app-bug`,
    **on an explicit request only**.
- Tracked on **#1726**. Nothing masked, nothing soft-asserted — no element
  exists to assert against.

## Known Defects Found During Exploration

- **[CLARIFICATION #1726 — this case's blocker]** as above.
- **[Sibling, already tracked]** #1363 — *"Pipeline chat panel has no Fullscreen
  Mode toggle (ELITEA-2071)"*. Same missing control, **different class**: there
  the toggle was **never implemented** on that surface (a real parity gap, filed
  `bug`, `isFullScreenChat: false` hardcoded); here it **existed and was removed
  on purpose**. Cross-linked both ways rather than folded into one issue —
  `.agents/profile.md` § Bug filing: *same pattern, different object ⇒ sibling,
  not duplicate*.
- **[No new defect]** Zero console **errors** across the whole flow.

## Concrete Handles (discovered)

All verified live 2026-08-24, all already on `origin/main` (fresh
`git fetch origin` before checking). Same table as ELITEA-1938's AFS —
`toolkit-action-bar`, `toolkit-test-button`, `toolkit-test-empty-tool-select`,
`toolkit-test-tool-select`, `toolkit-test-param-{key}-input`,
`toolkit-test-run-tool-button`, `chat-message-list`, `chat-copy-button`.

| Element | Locator | PROVENANCE |
|---|---|---|
| Fullscreen toggle on the MCP Test surface | **DOES NOT EXIST** — do not request a testid; no element to attach one to | n/a |
| Fullscreen toggle on the surfaces that DO have it | `FullScreenToggle.jsx` renders a bare MUI `IconButton` with **no testid at all** (only a `Tooltip title="Fullscreen mode"` / `"Exit fullscreen mode"`) | needs-adding — *only if* a future case targets one of those surfaces |

## Automation Hints (for the rewrite, if one is ordered)

- Same route + dirty-gating notes as ELITEA-1938's AFS § Automation Hints: the
  Test surface is `/mcps/all/{id}/test`, and `toolkit-test-button` is disabled
  while the detail form is dirty (`isTestDisabled={dirty}`) — **Save** after
  **Load Tools**.
- If a case ever targets the fullscreen toggle on a surface that still has it
  (Skill test panel / Toolkit-Index chat / Agent config), it needs a **new
  testid** via `add-data-testid` on `FullScreenToggle.jsx` — the component
  currently carries none, and the two tooltip strings are its only handle.

## Cleanup

- No entity created this session (reused MCP id 2140). Nothing to tear down.
