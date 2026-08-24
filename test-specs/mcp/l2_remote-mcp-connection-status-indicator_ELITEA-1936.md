# Test Case: Remote MCP — Connection Status Indicator

## Metadata
- **TMS ID**: ELITEA-1936
- **Linked Story**: none
- **Priority**: l2 — TMS frontmatter `priority: medium`, consistent with the
  case body's own "Priority: medium" line (no drift on this one).
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend, project id `399`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with
  ELITEA-1935 (shared login/navigation/discovery only — **every step of this
  case was executed and observed individually**)
- **Status**: ready-for-automation
- **Clarification filed**: [#1723](https://github.com/EliteaAI/elitea-testing-public/issues/1723)
  — case step 2 asserts a list-card connection badge that does not exist in the
  product.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project context is set (project id `399` this session).
- At least one Remote MCP exists in the project (the spec seeds its own — see
  § Test Data).
- **Browser context must be fresh, or `sessionStorage` cleared** — see the
  isolation note in § Automation Hints. This is the single most important
  precondition for this case and the case text does not mention it.

## Test Data

### generate-per-test (seed in setup, delete in teardown)
- Toolkit Name: `autotest_conn_status_<uuid4-hex-4>` (base is 21 chars; the
  32-char `maxLength` silently truncates, so keep the suffix short).
- Url: `https://mcp.deepwiki.com/mcp` — **must be a real, reachable, auth-free
  MCP server.** This case's steps 5-7 require the connection check to genuinely
  succeed; a placeholder URL (`https://mcp.example.com/sse`) would leave the
  status at "Not Connected" forever. DeepWiki is the project's standard fixture
  for exactly this.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all` and wait for the MCP list to render.
   - **Verify**: at least one `[data-testid="entity-card"]` is present.

2. **(Case-text drift — assert the ABSENCE, per clarification #1723.)** Verify no
   Remote MCP card renders a connection-status badge.
   - **Verify**: the list page contains **no** text matching `Disconnected`.
     Assert with an absence assertion (`to_have_count(0)` /
     `not_to_be_visible()`) so the claim stays guarded rather than silently
     dropped.
   - **Context**: the case expects every card to show a `Disconnected` badge.
     Confirmed live across 18 cards that a card contains exactly
     `entity-card-icon`, `entity-card-name`, `entity-card-tag-chip` (whose text
     is the **type** `Remote`, not a connection state) and
     `mcp-pin-toggle-button-<id>`. Confirmed in source: the literal
     `Disconnected` does not exist in any MCP list/card component. **Do not
     assert the case as written** — that would reverse-mask a stale case.

3. Open the seeded Remote MCP's detail page (click its card, or navigate to
   `${BASE_URL}/mcps/all/{toolkit_id}`) and wait for it to render.
   - **Verify**: `[data-testid="toolkit-detail-title"]` shows the toolkit's own
     name, not the `Edit MCP` placeholder. Use
     `McpFormPage.wait_for_page_load()`.
   - ⚠️ If arriving via `McpListPage.open_card_by_name()`, that helper does
     **not** wait for the destination page — always follow it with
     `wait_for_page_load()`.

4. Verify the connection-status area shows "Not Connected" with a Login button.
   - **Verify**: `[data-testid="toolkit-connection-status"]` has text exactly
     `Not Connected`.
   - **Verify**: `[data-testid="toolkit-connection-login-button"]` is visible,
     **enabled**, and its text is exactly `Login`.
   - **Verify (analyst addition, Axis 2)**: the status area renders its state
     icon — the `OnlineIcon` svg is a sibling of the status text inside the
     status container. The case says "with icon" only for the (non-existent)
     card badge; asserting it here is where the icon actually lives.

5. Click the Login button.
   - **Verify**: the click is accepted (button was enabled).
   - **What actually happens** (source-confirmed, `McpAuthStatus.jsx` →
     `useMcpAuthCheck`): `onLogin` calls `runAuthCheck`, which emits a
     **`test_mcp_connection` socket event** carrying the toolkit config. For a
     server that needs no OAuth this is a plain protocol-level `tools/list`
     round-trip — **no external browser window, no redirect, no OAuth modal.**

6. Verify the connection flow initiates and completes.
   - **Verify**: the button passes through / settles out of its in-flight state.
     While `isRunning` the label is `Logging in...` and the button is disabled.
     **Observed live: the round-trip against DeepWiki was faster than a 500 ms
     poll** — do not assert that `Logging in...` is *observed*, only that the
     terminal state is reached. Asserting the transient label would be a
     guaranteed flake.
   - **Verify**: no error toast (`[data-testid="toast-message"]`) appears.

7. Verify the status changes to "Connected".
   - **Verify**: `[data-testid="toolkit-connection-status"]` has text exactly
     `Connected!` — note the **trailing exclamation mark**; the case text says
     "Connected". Assert the product's literal.
   - **Verify**: `[data-testid="toolkit-connection-login-button"]` text flips to
     `Logout`.
   - Use a retrying web-first assertion
     (`expect(status).to_have_text("Connected!")`), never a bare
     `text_content()` read.
   - **Verify (analyst addition, Axis 2)**: `sessionStorage["elitea_mcp_tokens_v1"]`
     now holds an entry keyed by the server URL with
     `"access_token": "__connection_verified__"` and `"connection_verified": true`.
     This is the *system-produced* record behind the label — see § Automation
     Hints for why it matters and why reading it is an addition, not a
     substitution.

## Expected Results

- MCP list cards carry **no** connection-status badge (clarification #1723).
- The detail page shows `Not Connected` + an enabled `Login` button before any
  connection attempt.
- Clicking `Login` performs a real connection check and flips the indicator to
  `Connected!` with the button becoming `Logout`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: at least one Remote MCP exists | fixture exists | Setup | Setup | covered — spec seeds its own (case allows any existing MCP; a seeded one makes the "Not Connected" baseline deterministic) |
| 1 Navigate to MCP list page | MCP list loads | step 1 | step 1 | asserted |
| 2 Each Remote MCP card displays "Disconnected" badge | All cards show Disconnected badge | step 2 | step 2 (**inverted**) | **clarification** — no such badge exists in the product; filed as [#1723](https://github.com/EliteaAI/elitea-testing-public/issues/1723). Asserted as an ABSENCE so the claim stays guarded. See § Known Defects. |
| 3 Open a Remote MCP detail page | Detail page loads | step 3 | step 3 | asserted |
| 4 Status area shows "Not Connected" + "Login" button | Status area displays correctly | step 4 | step 4 | asserted (exact text on both) |
| 5 Click "Login" button | Auth/connection flow initiates | step 5 | step 5 | asserted |
| 6 Verify auth/connection flow initiates | Login flow or redirect appears | step 6 | step 6 | asserted — **with a case-text nuance**: there is no "redirect" for a no-OAuth server; the flow is an in-page socket round-trip. Asserted as the terminal state + no error toast, not as a redirect. |
| 7 Status changes to "Connected" upon success | Status updates to "Connected" | step 7 | step 7 | asserted — product literal is `Connected!` (trailing `!`) |
| Expected Final State: shows "Connected" after successful auth | — | step 7 | step 7 | asserted |

### Axis 2 — Analyst additions

- `step 4` asserts the **status icon** is rendered alongside the text — *added:
  the case demands "with icon" but attaches it to the card badge that does not
  exist. The icon genuinely exists here, and a regression that dropped it would
  otherwise go unnoticed.*
- `step 4` asserts the Login button is **enabled** — *added: `isButtonDisabled`
  is a real derived state (`!canLogin || isRunning || patInvalid`). A regression
  that rendered the button permanently disabled would satisfy the case's literal
  "Login button is present" while making the feature unusable.*
- `step 7` asserts the button label flips to **`Logout`** — *added: the label and
  the status text derive from the same `hasLoggedInToMcp` flag but are rendered
  by different branches; asserting both catches a half-applied state.*
- `step 7` asserts the **`sessionStorage` connection record** — *added: it is the
  system's own durable evidence that the connection check really succeeded, as
  opposed to a label flipped optimistically. This is a **read** of state the
  product wrote, never a write — no substitution.*
- `step 6` asserts **no error toast** — *added: `useMcpAuthCheck` routes error
  socket frames to `toastError`. Without this, a run where the check errored but
  the label happened to be stale from a prior context would pass.*

## Cleanup

Delete the seeded toolkit in teardown. Also **clear
`sessionStorage["elitea_mcp_tokens_v1"]`** (or simply let the context close) so a
following test in the same context does not inherit a `Connected!` baseline.

## Concrete Handles (discovered during exploration)

All handles below were exercised live this session. **PROVENANCE verified
2026-08-24 with a fresh `git fetch origin` in `../EliteaUI`.**

| Element | Handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Connection-status text | `toolkit-connection-status` | **on-`automation/testids` only** — EliteaAI/EliteaUI@a467c0ac, added for ELITEA-1934; **NOT yet on `main`** (human cherry-pick pending) | `McpAuthStatus.jsx:136`. Text is `Not Connected` / `Connected!` |
| Login / Logout button | `toolkit-connection-login-button` | **on-`automation/testids` only** — same commit; **NOT yet on `main`** | `McpAuthStatus.jsx:149`. Label `Login` → `Logging in...` (transient) → `Logout` |
| MCP list card | `entity-card` | on-main ✓ | |
| MCP list card name | `entity-card-name` | on-main ✓ | |
| Card type chip | `entity-card-tag-chip` | on-main ✓ | text is `Remote` — the **type**, not a connection state |
| Detail title | `toolkit-detail-title` | on-main ✓ | `Edit MCP` placeholder until data lands |
| Error toast | `toast-message` | on-main ✓ | app-wide `Toast.jsx` |
| Remote MCP type card (setup) | `toolkit-type-card-mcp` | on-main ✓ | mounts asynchronously — **3.5 s observed** this session |
| Toolkit Name input (setup) | `toolkit-form-name-input` | on-main ✓ | |
| Url input (setup) | `toolkit-field-url-input` | on-main ✓ | |
| Create-form Save (setup) | `toolkit-form-save-button` | on-main ✓ | create form only — the detail page uses `toolkit-detail-save-button` |

**AMENDED at implementation (2026-08-24, implementer): ONE new testid WAS
required.** Step 4's Axis-2 icon assertion has no compliant handle — the
`OnlineIcon` svg is an unlabelled sibling of the status `Typography` inside
`McpAuthStatus.jsx`'s status container, and chaining a raw `svg` selector off
`toolkit-connection-status` is forbidden (`.agents/testing.md` § Locator
policy). Added via `add-data-testid` discipline:

| Element | Handle | Provenance |
|---|---|---|
| Connection-status state icon | `toolkit-connection-status-icon` | **added during implementation** — EliteaAI/EliteaUI@55dc4f66 on `automation/testids`, **NOT on `main`** (human cherry-pick pending). One additive attribute on the existing `<OnlineIcon>`; no new DOM node, no hook, no removed markup. |

⚠️ **Promotability:** the two handles this case
depends on most (`toolkit-connection-status`, `toolkit-connection-login-button`)
live on `automation/testids` only. This spec will be **green on localhost and red
on any deployed env** until a human cherry-picks EliteaAI/EliteaUI@a467c0ac to
`main`. The closure record must say so.

## Network Behavior

| Trigger | Request | Observed |
|---|---|---|
| Detail page open | `GET /api/v2/elitea_core/tool/prompt_lib/399/{id}?` | 200 |
| Login click | socket event `test_mcp_connection` (localhost socket.io) | success frame in < 500 ms against DeepWiki |
| Create (setup) | `POST /api/v2/elitea_core/tool/prompt_lib/399` | 200, redirects to `/mcps/all/{id}` |

## Known Defects Found During Exploration

**No product defect found.** Case steps 1 and 3-7 all completed successfully
against the live local environment; the connection indicator behaved exactly as
the case describes.

**One case-text drift, filed as a CLARIFICATION (not a bug) —
[#1723](https://github.com/EliteaAI/elitea-testing-public/issues/1723):**

> Case step 2 requires every Remote MCP card in the list to display a connection
> status badge showing `Disconnected` with an icon. **No such badge exists.**
> Verified live across 18 cards (a card's full testid inventory is
> `entity-card-icon`, `entity-card-name`, `entity-card-tag-chip`,
> `mcp-pin-toggle-button-<id>`; a page-wide text probe for
> `Disconnected` / `Not Connected` / `Connected!` returned false for all three)
> and confirmed in source (`grep -rn "Disconnected" src/` hits only the chat
> participants feature and the guided-tour markdown — never the MCP list).
> The status the case wants lives only on the detail page, which its own step 4
> already covers correctly.

Per `.agents/testing.md` § reverse-masking guard the live product is correct and
the case text is stale, so this is a clarification. The AFS asserts the
**absence** rather than dropping the step, so the claim remains test-enforced.

Two adjacent, already-tracked items — noted, not re-filed:
- [#687](https://github.com/EliteaAI/elitea-testing-public/issues/687) covers a
  `Server is disconnected!` warning on the **chat participant** surface. Different
  surface, different string, already open — not this case.
- The `Connected` vs `Connected!` wording gap is a case-text imprecision, folded
  into #1723 rather than filed separately.

## Blocked Steps

None. **In particular, steps 5-7 are NOT blocked.** The obvious risk on reading
the case ("triggering authentication" implying an external OAuth window) does not
apply to a no-OAuth MCP server: `onLogin` → `runAuthCheck` performs an in-page
socket `test_mcp_connection` round-trip and, on success,
`McpAuthHelpers.setConnectionVerified(url)` flips the indicator. Fully automatable
against a real server with no external window, no popup handling, and no
credential.

*(A server that genuinely requires OAuth would open `McpAuthModal` instead — that
path is a different case and is already covered by the credentials-surface OAuth
work, e.g. ELITEA-1982/1984.)*

## Automation Hints

- **Isolation is the whole ballgame for this case.** The verified-connection
  record lives in **`sessionStorage`** under `elitea_mcp_tokens_v1`, keyed by
  server URL:

  ```json
  {"https://mcp.deepwiki.com/mcp": {"access_token": "__connection_verified__",
    "issued_at": ..., "expires_at": ..., "connection_verified": true}}
  ```

  `sessionStorage` is per-browser-context, so a **fresh Playwright context starts
  clean** and step 4's `Not Connected` baseline is honest. But **any earlier test
  in the same context that connected to the same URL will have already flipped
  it**, and step 4 then fails (or worse, step 7 passes vacuously). Either take a
  fresh context, or clear the key in setup. Because the entry is keyed by URL, a
  per-test unique toolkit name does **not** isolate you — the DeepWiki URL is
  shared across the whole MCP suite.

- **Do not assert the transient `Logging in...` label.** The DeepWiki round-trip
  completed faster than a 500 ms poll this session. Assert only the terminal
  state.

- **Assert `Connected!`, not `Connected`.** The product literal carries a
  trailing `!` (`McpAuthStatus.jsx:140`). The case text omits it.

- Reading `sessionStorage` in step 7 is an **observation of product-written
  state**, not a substitution — nothing is injected and the label assertion stands
  on its own. If the reviewer prefers a strictly DOM-only spec, the
  `sessionStorage` check is the one droppable assertion here; the case's own
  observable is the status text.

- **`McpListPage.open_card_by_name()` does not wait for the detail page** —
  follow it with `McpFormPage.wait_for_page_load()`.

- Wrap each step in `with allure.step("Step N — …"):` per
  `.agents/testing.md` § Step reporting.
- Markers: `ui`, `toolkits`, `mcp`, `p1`, `regression`.
- Suggested spec: `automation/tests/ui/toolkits/test_mcp_connection_status_indicator.py`.
- **Fidelity**: no substitution is specced. Every asserted value — the status
  text, the button label, the absence of a card badge, the `sessionStorage`
  record — is produced by the system against a real MCP server over a real socket
  round-trip.
