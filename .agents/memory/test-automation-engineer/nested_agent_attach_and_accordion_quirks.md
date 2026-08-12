---
name: Nested agent attach and accordion quirks
description: ELITEA-1951 — 4 distinct root causes chained on the "+Agent" attach flow + nested-accordion assertions — attach_agent() click interception, capture_requests_matching() missing a PATCH response, two chat-answer-tool-chip elements sharing one accordion, and the sub-agent's relay prefix not surviving reliably.
type: feedback
---

## What happened (ELITEA-1951, 2026-08-07)

Implementing "parent agent invokes a nested sub-agent with an MCP tool"
(`test_nested_agent_with_mcp_tool_output.py`) took 7 straight RED runs before
GREEN — every single one a real, distinct, reproducible cause (verified live
via Playwright MCP each time), never a flake. Each fix is durable for any
future case touching the "+ Agent" picker or the nested-invocation accordion.

### 1. `AgentDetailPage.attach_agent()` can silently fail to click

`attach_agent()` → `Popper.select_menuitem()` uses a raw
`li[role="menuitem"]:has-text("{name}")` CSS locator + a plain Playwright
`.click()`. For a long/truncated agent name (the item's visible text ellipses
and a `TypographyWithConditionalTooltip` renders on hover), the click
reliably **hovers but never registers** — no attach request fires (or the
backend rejects a stale reference), the popper never closes, no exception is
raised. Reproduced identically against a freshly-created AND an
already-existing persistent agent — not about agent freshness. A role-based
click (`getByRole('menuitem', {name}).click()`), a raw JS
`element.click()`, and a **testid-scoped** Playwright click
(`[data-testid="toolkit-menu-item"]:has-text(...)`) all landed reliably
against the SAME picker/agent live — points at a MUI Tooltip-portal overlay
intercepting the CSS-located click's computed coordinates specifically.

**Fix:** new additive `AgentDetailPage.attach_agent_by_testid()` — same
shape as `attach_agent()` but calls `Popper.select_menuitem_by_testid()`
(already existed, added for ELITEA-1735, was just never wired to the Agent
picker before). `attach_agent()` itself was NOT touched — other merged
callers depend on it unchanged. Use `attach_agent_by_testid()` for any new
caller; prefer it over `attach_agent()` going forward for agent names that
might truncate.

### 2. `capture_requests_matching()` can miss a response event for this PATCH

Set up `detail_page.capture_requests_matching("application_relation/prompt_lib",
method="PATCH")` before the attach click (same idiom `test_mcp_attach_via_
tools_section.py` uses successfully for a DIFFERENT endpoint). The
**request** was captured correctly every time, but its **response** handler
sometimes never fired — `status` stayed `None` forever — even though the
attach genuinely succeeded server-side (confirmed via the UI's own success
toast + card appearing). This is a real race in the manual
`page.on("request"/"response")` listener-list pattern for this specific
endpoint, not a usage mistake (same code shape works for the CREATE POST in
the same test, same file).

**Fix:** switched to `page.expect_response(lambda resp: ..., timeout=...)`
around the action (same idiom `test_agent_self_attachment_blocked.py`
already uses) — Playwright's own request/response-correlation primitive,
immune to this specific race. Prefer `expect_response()` over
`capture_requests_matching()` for any single-action-single-response
assertion; the latter is still fine for "did ANY matching request fire" over
a longer window (e.g. counting retries).

### 3. TWO `chat-answer-tool-chip` elements share the SAME nested-accordion details container

Not documented by the ELITEA-1951 AFS. Inside a `SubAgentAccordion`'s
details, in DOM order:
1. The **PARENT's own** "I called this agent as a tool" chip — text is just
   the bare agent name (e.g. `"autotest_nested_mcp_subagent"`), never
   changes (it's an agent call, not a toolkit/tool call — no `{toolkit}:
   {tool}` segment to fill in).
2. The **sub-agent's OWN nested MCP tool-call** chip — text
   `"{toolkit}: {tool} ({agent})"` (e.g. `"autotest_mcp_run_tool:
   read_wiki_structure (autotest_nested_mcp_subagent)"`).

Both carry `data-testid="chat-answer-tool-chip"`. A naive `.first` (or the
`get_nested_agent_tool_chip_texts()`/`get_nested_agent_tool_chip_locator()`
helpers WITHOUT the `toolkit_name` filter) silently reads chip (1) and never
updates, looking exactly like a stuck/never-resolving tool call.

**Fix:** both helpers on `AgentDetailPage` now take an optional
`toolkit_name` param — pass it to filter (`.filter(has_text=toolkit_name)`)
to chip (2) specifically. Always pass it when asserting the ACTUAL tool call
(not the agent-invocation marker).

### 4. Nested accordion's expand state resets mid-stream (re-collapse race)

`wait_for_chat_response()` only guarantees the PARENT's own top-level turn
is "done" (its own completion signal: "Clear chat" button visible, loading
phrases gone) — the response can keep **streaming/re-rendering for several
more seconds** after that, as the sub-agent's own nested tool call resolves
and gets relayed. `SubAgentAccordion`'s `expanded` is local `useState`
(default `false`) — if the component **remounts** during one of those later
re-renders, the expand state resets, silently re-collapsing an accordion you
already expanded and read `aria-expanded="true"` from moments earlier.

**Fix:** wait for the TRUE completion signal — the final answer text
containing content that can only exist once the ENTIRE chain (including the
nested tool call) has resolved — BEFORE expanding the accordion, not just
for `wait_for_chat_response()`'s weaker parent-level signal. See #5 below
for what "the right content signal" turned out to be.

### 5. The sub-agent's own relay-prefix instruction ("verbatim, unmodified") isn't 100% reliable

Sub-agent instructed: `"...return its raw result verbatim...prefixed with
'MCP_TOOL_OUTPUT:'."` Parent instructed: `"...return its full response
verbatim, unmodified."` Confirmed live across multiple runs: the REAL,
non-hallucinated DeepWiki-Open content reaches the parent's final answer
**every time**, but the literal `"MCP_TOOL_OUTPUT:"` marker does **not**
always survive the parent's relay — sometimes the parent prepends a framing
sentence ("The sub-agent returned:"), sometimes it drops the prefix
entirely, while the real payload is untouched. Ordinary LLM
instruction-following non-determinism on an exact-formatting instruction,
not a platform defect (same class as the message-wording-determinism note
already in this case's own AFS § Test Data).

**Fix:** anchor the anti-hallucination proof on a REAL, repo-specific
content marker instead of the literal prefix (here: `"DeepWiki-Open
Overview"`, an actual section name from the real wiki-structure result — an
LLM can't guess/hallucinate this exact string). Treat the literal
instructed-prefix's presence as a soft/logged signal only, never a hard
assertion, for any case relying on an agent's own "return verbatim, exact
prefix X" instruction being followed literally by a downstream relay.

## Rule of thumb for future nested-agent / accordion / picker cases

- Any "+Agent"/"+Pipeline" picker attach on a name that might visually
  truncate → use `attach_agent_by_testid()`, not `attach_agent()`.
- Any single-action network assertion → `page.expect_response()`, not
  `capture_requests_matching()`.
- Any nested-accordion chip read → pass `toolkit_name` to disambiguate from
  the agent-invocation chip sharing the same testid.
- Any nested-accordion expand+read → wait for the FINAL, fully-resolved
  content signal first, expand second — never expand right after
  `wait_for_chat_response()` returns.
- Any "assert the LLM followed an exact literal-text instruction" case →
  prefer a content-based proof (something an LLM can't fabricate) over the
  literal instructed string, and treat the literal string as informational.
