# Test Case: Remote MCP — Test Settings — Clear Chat

## Metadata
- **TMS ID**: ELITEA-1938
- **Linked Story**: none
- **Priority**: l3 — TMS frontmatter `priority: medium`; same `medium → l3_`
  precedent this folder's ELITEA-1937 / ELITEA-1947 AFS files set.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with
  ELITEA-1939 + ELITEA-1940 (shared session; every case's steps executed and
  observed individually — this case DIVERGED from the family and carries its
  own status)
- **Status**: blocked
- **Filed**: #1725 (`question` + `case-text-drift`)

## Why this case is `blocked`, in one line

**The control the case exists to test was deliberately removed from the product
by two successive redesigns.** There is no "clear the chat" button on the Remote
MCP Test surface, so the case's own observable (steps 4–6) cannot be produced
honestly — and per `.agents/testing.md` § Fidelity policy that is a **human
decision** (retire/rewrite the case, or rule the removal a regression), never
something automation engineers around.

## Preconditions (as executed)

- Authenticated on localhost (automatic via `VITE_DEV_TOKEN`).
- Remote MCP `autotest_mcp_run_tool` (id **2140**, `Private` project) —
  pre-existing residue from the ELITEA-1937 analysis session, reused here.
  Fixture URL `https://mcp.deepwiki.com/mcp` (3 tools), re-confirmed live this
  session: **Load Tools** returned `3 / 3`.
- Case Precondition *"At least one tool run has been performed"* — satisfied
  live: `read_wiki_structure` with `repoName = "AsyncFuncAI/deepwiki-open"`
  returned `✅ read_wiki_structure (1.182s)` plus the real DeepWiki page list.

## What was actually executed

| Case step | What was done | What was observed |
|---|---|---|
| 1 Open a Remote MCP with Test Settings panel | Opened `/mcps/all/2140`, clicked **Load Tools** (3/3), **Save** (the Test button is gated on `isTestDisabled={dirty}` — see § Automation Hints), then **Test** in the action bar → `/mcps/all/2140/test` | Test page loads: a **two-column** layout, left header `Test Settings`, right header `Results`. **Neither header carries any button.** |
| 2 Run a tool to generate a chat message | `Select Tool` → `read_wiki_structure` → filled `toolkit-test-param-repoName-input` → **Run Test** | ✅ `read_wiki_structure (1.182s)` + real DeepWiki content rendered in the Results column (`chat-message-list`, 1 `li.MuiListItem-root`) |
| 3 Verify a response message is visible | Read `[data-testid="chat-message-list"] li.MuiListItem-root` | Confirmed visible — 1 message item |
| 4 Click "clear the chat" (trash icon) | Full DOM inventory of **every** `<button>` on the page, in the post-run state | **BLOCKED — no such control exists.** The only button attached to the results area is `chat-copy-button` ("Copy to clipboard"). No trash icon, no `aria-label` matching clear, nothing in either column header. |
| 5 Verify all messages removed | not reachable | — |
| 6 Verify welcome message reappears | not reachable | — |

Evidence: `test-results/screenshots/ELITEA-1938-1939-mcp-test-page-no-clear-no-fullscreen.png`
(also uploaded to the `evidence` release and embedded in #1725).

## Root cause — the case was authored against a retired UI

Git archaeology in `EliteaAI/EliteaUI` (verified after `git fetch origin`):

```
src/[fsd]/features/toolkits/ui/test-tools/TestTools.jsx  @ 0cff136d^  (pre 2026-07-30)
  191:  <FullScreenToggle isFullScreenChat={...} ... />        ← ELITEA-1939
  195:  <ChatButton.ClearChatButton onClear={handleClearChat} /> ← THIS CASE
  196:  {onShowHistory && <ViewRunHistoryButton .../>}          ← ELITEA-1940
```

The pre-EL-5947 Test panel header rendered exactly the trio ELITEA-1938/1939/1940
describe. Two deliberate feature commits dismantled it:

1. **EliteaAI/EliteaUI@0cff136d** — `Feat/el 5947/new toolkit run UI (#663)`,
   2026-07-30. `ClearChatButton` (and `FullScreenToggle`) leave the toolkits
   feature entirely; `handleClearChat` survives only as an unlabelled
   **back-arrow** inside the then-new "Run Results" view (this is the state the
   2026-08-01 ELITEA-1937 AFS documented).
2. **EliteaAI/EliteaUI@cb030b7d** — `feat: [EL-6277] move indexes into the
   details right panel (#803)`, 2026-08-20. The panel becomes its own route
   (`/mcps/all/{id}/test`) and is rewritten as `ToolkitTestPanel.jsx`, a
   two-column *Test Settings | Results* split. **`handleClearChat` is no longer
   consumed by any UI control** — `useToolkitTestRunner` still exposes it,
   `ToolkitTestPanel.jsx` never destructures it.

So the removal is intentional product work, not a defect: the reverse-masking
guard applies in its strongest form — the case text is stale, the product is
behaving as its authors intended. Classified `blocked` (needs a human ruling),
**not** `defect-found`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | met | Preconditions | — | satisfied |
| Precondition: Remote MCP with Test Settings panel available | met | Preconditions | executed step 1 | satisfied — **panel is now a separate ROUTE, not a detail-page region** (EL-6277) |
| Precondition: at least one tool run performed | met | executed step 2 | executed step 2 | satisfied live |
| 1 Open a Remote MCP with Test Settings panel | detail page + panel | executed step 1 | executed step 1 | asserted (with the route correction above) |
| 2 Run a tool to generate a message | ≥1 message visible | executed step 2 | executed step 2 | asserted — real DeepWiki result |
| 3 Verify a response message is visible | message confirmed | executed step 3 | executed step 3 | asserted |
| 4 Click "clear the chat" button (trash icon) | clear triggered | — | — | **blocked** — control does not exist (#1725) |
| 5 Verify all messages removed | chat empty | — | — | **blocked** — depends on step 4 |
| 6 Verify welcome message reappears / chat blank | welcome or blank | — | — | **blocked** — depends on step 4; note also that no "welcome message" state exists on this surface at all (pre-existing clarification #1086, re-confirmed this session) |
| Expected Final State: messages removed, area empty/welcome | — | — | — | **blocked** |
| Pass/Fail: all messages cleared | — | — | — | **blocked** |

### Axis 2 — Analyst additions

- None. Adding assertions around a case whose subject has been removed would
  invent coverage the case never asked for; the honest output here is the
  routed decision, not a substitute test.

## Blocked Steps

- **Steps 4, 5, 6 — and therefore the case's entire Pass criterion.** What is
  needed to unblock, *either*:
  - **(a)** a human ruling that the case is retired or rewritten against the
    post-EL-6277 two-column Test page (the likely answer — the redesign shipped
    twice and is clearly deliberate); **or**
  - **(b)** a human ruling that losing "clear results" is a capability
    regression to restore, which escalates to `EliteaAI/elitea_issues` via the
    `file-app-bug` skill — **on an explicit request only**, never on agent
    initiative (`.agents/profile.md` § Bug filing).
- Tracked on **#1725**. No test is written and no assertion is weakened —
  there is nothing to soft-assert, because the element never renders.

## Known Defects Found During Exploration

- **[CLARIFICATION #1725 — this case's blocker]** as above.
- **[Pre-existing, re-confirmed]** #1086 (no pre-run welcome/chat area on this
  surface) still holds after the EL-6277 refactor — the Results column simply
  renders nothing (`ToolkitTestResults.jsx`: `if (!messages.length) return null`)
  until a run produces a message. Case step 6's "welcome message reappears"
  branch is therefore doubly unreachable.
- **[No new defect]** Zero console **errors** during the whole flow (1 warning
  only). The removal is silent and clean.

## Concrete Handles (discovered — for whoever rewrites this case)

Recorded so a rewrite doesn't re-explore. All verified live 2026-08-24, all
already on `origin/main` (fresh `git fetch origin` before checking).

| Element | Locator | PROVENANCE |
|---|---|---|
| Detail action bar | `[data-testid="toolkit-action-bar"]` | on-main ✓ |
| **Test** button (opens the Test route) | `[data-testid="toolkit-test-button"]` (aria-label `Test MCP`) | on-main ✓ |
| Test page — empty-state tool select | `[data-testid="toolkit-test-empty-tool-select"]` | on-main ✓ |
| Test page — Run button | `[data-testid="toolkit-test-run-tool-button"]` (label "Run Test") | on-main ✓ |
| Results message list | `[data-testid="chat-message-list"]` | on-main ✓ |
| Results message item | `[data-testid="chat-message-list"] li.MuiListItem-root` | scoped constant, existing |
| Copy-to-clipboard (the ONLY results-area control today) | `[data-testid="chat-copy-button"]` | on-main ✓ |
| Clear-the-chat control | **DOES NOT EXIST** — do not request a testid; there is no element to attach one to | n/a |

## Automation Hints (for the rewrite, if one is ordered)

- **The Test surface is now a route**, `/mcps/all/{id}/test`, reached from the
  detail action bar's `toolkit-test-button` — not a right-hand region of
  `/mcps/all/{id}`. Direct navigation to the URL also works.
- **`toolkit-test-button` is disabled while the detail form is dirty**
  (`ToolkitForm.jsx`, `isTestDisabled={dirty}`). Clicking **Load Tools** makes
  the form dirty, so any flow that loads tools must **Save** and wait for the
  Test button to re-enable before navigating. Confirmed live this session.
- Reuse `McpFormPage` (create/Load Tools/Save) + `ToolkitTestSettingsPage`
  (tool select / param fill / run / wait) — both already model this surface;
  `ToolkitTestSettingsPage.wait_for_tool_result()` polls the `[✅❌]` marker,
  no sleeps.

## Cleanup

- No entity created this session (reused MCP id 2140). Nothing to tear down.
