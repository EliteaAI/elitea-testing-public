# Test Case: MCP Integration in Agent — Nested Agent with MCP

## Metadata
- **TMS ID**: ELITEA-1951
- **Linked Story**: none
- **Priority**: l3 (medium, per case metadata — matching the sibling
  `priority: medium` → `l3` precedent set by ELITEA-1950)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  `automation/testids` branch → DEV backend, project `Private`/`${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost: `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — executed end-to-end live (attach sub-agent
  → verify version selector → verify auto-save → execute → verify nested MCP
  tool output in parent's response), no blockers. One testid gap found
  (version-selector trigger/menu on attached-tool cards — see § Concrete
  Handles) and one case-text-drift pattern confirmed to extend to the Agent
  tool type (same root cause as the already-filed
  [EliteaAI/elitea-testing-public#530](https://github.com/EliteaAI/elitea-testing-public/issues/530) —
  cited, not re-filed; see § Known Defects).

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A parent agent exists — **case-text drift**: the case's example name
  ("ParentAgent") does not exist as project data; created a fresh agent
  `autotest_nested_mcp_parentagent` (id `7828`) via the UI create form.
- A sub-agent with an MCP configured is available — **case-text drift**: the
  case's example ("EliteaMCPAgent") does not exist as project data. Created a
  fresh agent `autotest_nested_mcp_subagent` (id `7827`) via the UI create
  form, with the existing project MCP `autotest_mcp_run_tool`
  (`https://mcp.deepwiki.com/mcp`, tool `read_wiki_structure` — the same
  no-OAuth, genuinely-runnable fixture confirmed live by ELITEA-1937's AFS)
  attached to it via the standard "+ MCP" flow (see ELITEA-1950's AFS for
  that sub-flow's own handle table — reused unchanged here).
  **Both fixture agents were left in the project (`Private`/399) after this
  run** as ready-to-reuse fixtures (ids `7827`/`7828`), matching this
  project's established pattern of persistent `autotest_*`-prefixed fixtures
  (e.g. `autotest_mcp_run_tool`, `autotest_remote_mcp_full`) — the implementer
  may reuse them directly, or build an equivalent pair via `AgentAPI` fixtures
  if full per-run isolation is preferred (see § Automation Hints for the
  `#524` gotcha that applies to the API path but did NOT fire via this run's
  UI-form creation).

## Test Data

### reuse-existing
- MCP: `autotest_mcp_run_tool` (existing Remote MCP toolkit in project `399`,
  no OAuth required, confirmed live to execute and return real, non-empty
  content — same fixture ELITEA-1937 and ELITEA-1950 already use).

### reuse-existing (created this run, left as persistent fixtures — see Preconditions)
- Sub-agent: `autotest_nested_mcp_subagent` (id `7827`). Instructions field:
  `When invoked, always call the read_wiki_structure MCP tool with
  repoName="AsyncFuncAI/deepwiki-open" and return its raw result verbatim in
  your response, prefixed with "MCP_TOOL_OUTPUT:".` — has `autotest_mcp_run_tool`
  attached as its only Tool.
- Parent agent: `autotest_nested_mcp_parentagent` (id `7828`). Instructions
  field: `When the user asks you anything, always invoke the
  autotest_nested_mcp_subagent tool and return its full response verbatim,
  unmodified.` — has `autotest_nested_mcp_subagent` attached as its only Tool
  (via the "+ Agent" picker).

### Message wording — determinism-critical (see § Known Defects / Axis 2)
The exact chat message sent to the parent agent materially affects whether
the full nested-invocation → nested-tool-call chain fires in one pass. The
**live-confirmed reliable** message is:
`Ask autotest_nested_mcp_subagent to use its read_wiki_structure tool for
repoName="AsyncFuncAI/deepwiki-open" and return its full response to me
verbatim.` — this single message, sent once, deterministically produced the
full chain (parent invokes sub-agent → sub-agent calls its MCP tool → parent
relays the tool output) in this run. A vaguer message (e.g. "Please help me
with this task.") produced a generic clarifying-question reply with **no**
tool invocation at all — expected LLM behavior given ambiguous input, not a
product defect (see § Known Defects for the full reasoning and the distinction
from the unrelated, confirmed-different defect #1127).

## Test Steps

1. Create the parent agent `autotest_nested_mcp_parentagent` via the Agents
   "Create" form (Name/Description/Instructions), Save.
   - **Verify — PASSES.** Agent saves, redirects to
     `/agents/all/{id}?destTab=configuration&viewMode=owner`, `agent-save-button`
     click produced a 201 on `POST .../elitea_core/applications/prompt_lib/399`.
2. Scroll to the "Tools" section; click the "+ Agent" add button
   (`agent-add-agent-button`, existing testid).
   - **Verify — PASSES, with case-text drift (CLARIFICATION — cite #530, do
     not re-file).** The case describes this as an "Agent tab" that becomes
     "active". The live product instead opens a `UnifiedDropdown` popper
     directly on click (same 4-independent-buttons, no-tabs pattern #530
     already documents for the Toolkit/MCP buttons — confirmed here to extend
     identically to the Agent button).
3. Search/select the sub-agent `autotest_nested_mcp_subagent` from the
   popper's menu items (`role="menuitem"`, matched by exact accessible name —
   same `Popper.select_menuitem` helper `AgentDetailPage.attach_agent()`
   already uses, confirmed working unchanged in this run).
   - **Verify — PASSES.** Popper closes; a toast/alert confirms attachment
     (`"The toolkit has been successfully added to the agent."` — same
     generic copy the Toolkit/MCP flows use, confirmed live); the sub-agent
     immediately appears as a card in the Tools section (see step 4). The
     underlying request is `PATCH
     /api/v2/elitea_core/application_relation/prompt_lib/399/{sub_agent_app_id}/{sub_agent_version_id}`
     → `201 Created` — **a distinct endpoint from the Toolkit/MCP attach flow's
     `PATCH .../tool/prompt_lib/{project}/{tool_id}`** (new discovery this
     run, not previously documented in `test-specs/agents/_surface.md`).
4. Verify the sub-agent appears in the Tools list with a version selector.
   - **Verify — PASSES, testid gap found (see § Concrete Handles).** The
     card renders via the same shared `agent-toolkit-card` testid used by
     Toolkit/MCP cards (confirmed: `textContent` = `"autotest_nested_mcp_subagentbase"`).
     Clicking the version area (`.version-text`, rendered by
     `AgentPipelineVersionSelector.jsx`) opens a MUI menu with a "Versions"
     header and one option, `"base"` (the sub-agent's only version) —
     live-confirmed both the trigger text and the menu contents. **No
     `data-testid` exists anywhere on this component** (confirmed via source
     read of `EliteaUI/src/pages/Applications/Components/Tools/AgentPipelineVersionSelector.jsx` —
     zero `data-testid` occurrences in the whole file) — testid needed, see
     § Concrete Handles.
5. Save/confirm the parent agent's configuration.
   - **Verify — PASSES, with case-text drift (CLARIFICATION — same #530
     pattern, confirmed to extend to the Agent tool type; do not re-file).**
     Attaching the sub-agent auto-persists the instant the popper selection
     resolves (step 3's PATCH). The agent-level `agent-save-button` stays
     **disabled** throughout (confirmed via `.disabled` property read
     immediately after attach) — there is nothing to click; the live-accurate
     equivalent is asserting the PATCH response status (already covered in
     step 3), not a Save click.
6. Send a message to the parent agent via the embedded chat and verify it
   invokes the sub-agent.
   - **Verify — PASSES with the determinism-critical message from § Test
     Data.** The response's `chat-answer-thought-accordion` (existing testid)
     contains a nested accordion (`<h3>` inside it) whose heading text is the
     sub-agent's name, `autotest_nested_mcp_subagent` — this is the concrete,
     stable signal that the parent invoked the sub-agent as a tool. A vaguer
     message (tried first) produced only a top-level `chat-answer-tool-chip`
     reading `"autotest_nested_mcp_subagent"` with **no** further nesting
     (because the sub-agent, invoked, chose not to call its own tool that
     time) — i.e. **the UI's chosen representation (flat chip vs. expandable
     nested accordion) itself depends on whether the invoked agent made a
     further tool call**, confirmed live across two otherwise-identical runs.
     Automation must use the reliable message to get the nested-accordion
     shape deterministically, not assert on chip-vs-accordion as a fixed
     constant.
7. Verify the parent's response references the MCP tool output from the
   nested agent.
   - **Verify — PASSES.** Expanding the nested `autotest_nested_mcp_subagent`
     accordion (click its `AccordionSummary` button; `aria-expanded`
     `false`→`true`) reveals, in DOM order: a `chat-answer-model-chip`
     reading `"Anthropic Claude 4.5 Sonnet (autotest_nested_mcp_subagent)"` →
     a `chat-answer-tool-chip` reading
     `"autotest_mcp_run_tool: read_wiki_structure (autotest_nested_mcp_subagent)"`
     (the nested agent's own MCP tool call — note the `"{toolkit}: {tool}
     ({originating_agent_name})"` text shape, which disambiguates a
     nested-agent's own tool call from a top-level one) → a second
     `chat-answer-model-chip` (the sub-agent's follow-up completion). The
     parent's own final answer text (`chat-answer-content`-equivalent
     container below the accordion) contains the literal string
     `"MCP_TOOL_OUTPUT:"` (the sub-agent's own instructed prefix) followed by
     the real DeepWiki-Open wiki-structure listing (non-empty, matches the
     live content ELITEA-1937 already confirmed for this exact fixture/tool/
     parameter combination) — proving the tool's real output, not a
     hallucinated summary, reached the parent's response verbatim.

## Expected Results
- The parent agent successfully executes and returns a response that
  includes MCP tool output from the nested sub-agent, when given an
  unambiguous instruction that names the sub-agent, its tool, and the tool's
  required parameter.
- No console errors attributable to the flow (confirmed: 0 console errors
  across the whole run).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create or use ParentAgent | Agent is available | step 1 | step 1: agent saves, redirects to detail page | asserted, with data substitution *(no "ParentAgent" project fixture exists — created `autotest_nested_mcp_parentagent`)* |
| 2 In Tools section, click Agent tab | Agent tab is active | step 2 | step 2: `agent-add-agent-button` click opens popper | clarification *(no "tab"/"active" state exists — same #530 pattern, cite not re-file)* |
| 3 Attach a sub-agent that has an MCP configured | Sub-agent is selected | step 3 | step 3: popper closes, toast confirms, PATCH .../application_relation/... → 201 | asserted, with data substitution *(no "EliteaMCPAgent" fixture exists — created `autotest_nested_mcp_subagent` with `autotest_mcp_run_tool` attached)* |
| 4 Verify sub-agent appears in tools list with version selector (e.g. "base" dropdown) | Sub-agent is listed with version selector | step 4 | step 4: `agent-toolkit-card` text + version menu opens showing "base" | asserted, testid gap flagged *(version selector has zero `data-testid` — see § Concrete Handles)* |
| 5 Save ParentAgent | Operation completes successfully | step 5 | step 5: `agent-save-button.disabled === true`, attach already persisted at step 3 | clarification *(attach is auto-save; same #530-pattern Save-stays-disabled behavior, now confirmed for the Agent tool type too — cite, don't re-file)* |
| 6 Execute ParentAgent — verify it can invoke the sub-agent which uses MCP tools | ParentAgent executes and invokes the sub-agent | step 6 | step 6: nested `autotest_nested_mcp_subagent` `<h3>` inside `chat-answer-thought-accordion` | asserted |
| 7 Verify response references MCP tool output from nested agent | Response includes output from the MCP tool | step 7 | step 7: `chat-answer-tool-chip` = `"autotest_mcp_run_tool: read_wiki_structure (autotest_nested_mcp_subagent)"` + final answer text contains `"MCP_TOOL_OUTPUT:"` + real wiki-structure content | asserted |
| Expected Final State: parent returns response including nested MCP tool output | — | step 7 | step 7 | asserted |

### Axis 2 — Analyst additions

- **Message-wording determinism note (added — not in case text).** The case
  text gives no example message. Live exploration across three attempts
  showed the flow's determinism is entirely a function of message
  specificity: a vague message → no invocation at all; a message that
  invokes the sub-agent but doesn't relay the tool's required parameter → the
  sub-agent is invoked but silently skips its own tool and answers generically;
  only a message naming the sub-agent, its tool, AND the tool's required
  parameter reliably produced the full chain. This mirrors the team's
  existing precedent (ELITEA-2211 vs. ELITEA-2215's message-wording finding)
  and is **not** the same defect as
  [EliteaAI/elitea-testing-public#1127](https://github.com/EliteaAI/elitea-testing-public/issues/1127)
  (which is about a tool-call *intent* leaking as raw visible text — never
  observed in this run; every non-invoking response here was a normal,
  well-formed conversational reply, i.e. the model choosing not to call a
  tool, not the platform mis-rendering a call it tried to make). Automation
  must use the reliable message from § Test Data verbatim, not a case-text
  paraphrase, to avoid reproducing a flaky spec.
- **Distinct attach endpoint discovery (added).** Documented `PATCH
  .../application_relation/prompt_lib/{project}/{app_id}/{version_id}` as the
  Agent/Pipeline-type tool-attach endpoint, distinct from
  `.../tool/prompt_lib/{project}/{tool_id}` used by Toolkit/MCP attach — *added:
  useful for a network-response-based persistence assertion, mirroring
  ELITEA-1950's PATCH-201 pattern.*
- **Chip-vs-accordion representation nuance (added).** Documented that the
  UI's choice between a flat `chat-answer-tool-chip` and an expandable nested
  accordion for the SAME sub-agent invocation depends on whether the
  sub-agent itself made a further tool call — *added: prevents the
  implementer from hardcoding "always a chip" or "always an accordion" as the
  nested-invocation signal.*

## Cleanup
1. No teardown performed this run — the two fixture agents
   (`autotest_nested_mcp_subagent` id `7827`, `autotest_nested_mcp_parentagent`
   id `7828`) and the MCP attachment were intentionally left in place as
   reusable project fixtures (see § Preconditions). If the implementer
   instead builds fresh per-run fixtures via `AgentAPI`, standard
   create-in-setup/delete-in-teardown discipline applies (mirrors
   `test_import_agent_zip_nested_agent_dependencies.py`'s existing use of
   `attach_agent()` for cleanup-pattern precedent).
2. No artifact-bucket, credential, or other entity is created by this flow.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Tools accordion section | `LocatorDescriptor(testid="agent-toolkits-section")` (existing, `AgentDetailPage.toolkits_section`) | on-main ✓ | none |
| "+ Agent" add button | `LocatorDescriptor(testid="agent-add-agent-button")` (existing, `AgentDetailPage.add_agent_button`) | on-`automation/testids` only (awaiting human promotion to main) | none |
| Agent picker popper | `components.mui.Popper` (existing shared helper); page-object method `AgentDetailPage.open_agent_picker()` / `attach_agent()` already implement the full click→search→select flow (from ELITEA-1902) | on-main ✓ (component itself) | none |
| Sub-agent menu item (select by name) | `Popper.select_menuitem(popper, agent_name, page)` (existing shared helper, confirmed working for Agent-type items in this run) | on-main ✓ | none |
| Attached sub-agent card | `LocatorDescriptor(testid="agent-toolkit-card")` filtered `.filter(has_text=sub_agent_name)` (existing, shared with Toolkit/MCP cards, confirmed same component renders Agent-type tools too) | on-main ✓ | none |
| **Version selector trigger on a tool card** | **testid needed**: `agent-tool-version-selector-trigger-{tool_id}` (dynamic, mirrors `SKILL_VERSION_TRIGGER_SELECTOR` pattern in `agent_detail_page.py`) — add via `add-data-testid` to `EliteaUI/src/pages/Applications/Components/Tools/AgentPipelineVersionSelector.jsx`'s `selector` `Box` (the `.version-text`-containing clickable element). Zero `data-testid` in this file today (confirmed via source read). | needs-adding | none — testid-only policy |
| **Version selector menu / options** | **testid needed**: `agent-tool-version-selector-menu-{tool_id}` on the `Menu`, `agent-tool-version-option-{tool_id}-{version_id}` per `MenuItem` (dynamic, same templated-constant pattern as `SKILL_VERSION_MENU_SELECTOR`) | needs-adding | none |
| Agent-level Save button (to assert `.disabled`) | `LocatorDescriptor(testid="agent-save-button")` (existing) | on-main ✓ | none |
| Chat message input | `LocatorDescriptor(testid="chat-message-input")` (existing, `ChatPage`) | on-main ✓ | none |
| Chat message list | `LocatorDescriptor(testid="chat-message-list")` (existing, `ChatPage`) | on-main ✓ | none |
| Answer's outer thought accordion | `LocatorDescriptor(testid="chat-answer-thought-accordion")` (existing, added by the ELITEA-2211..2215 batch) | on-`automation/testids` only (awaiting human promotion to main) | none |
| Nested sub-agent accordion heading | **No dedicated testid** — the nested accordion's `<h3>` text equals the invoked agent's exact name; scope via `chat-answer-thought-accordion >> h3` text match (confirmed live shape; a future `add-data-testid` pass could add a dynamic `chat-answer-nested-agent-accordion-{agent_name}` if per-name addressing beyond text-match is needed — not required for this case since only one nested agent is ever attached) | n/a (element carries no testid by design today) | none — testid-only policy honored via a scoped text match under the existing parent testid, not a free-floating raw handle |
| Model chip(s) inside the (possibly nested) accordion | `LocatorDescriptor(testid="chat-answer-model-chip")` (existing, added by the ELITEA-2211..2215 batch) | on-`automation/testids` only (awaiting human promotion to main) | none |
| Tool-call chip inside the (possibly nested) accordion | `LocatorDescriptor(testid="chat-answer-tool-chip")` (existing, added by the ELITEA-2211..2215 batch); text shape for a NESTED agent's own tool call is `"{toolkit}: {tool} ({originating_agent_name})"` vs. a top-level call's `"{toolkit}: {tool}"` (no suffix) — confirmed live, distinguish by suffix presence, not by DOM depth alone | on-`automation/testids` only (awaiting human promotion to main) | none |
| Final answer text container | scoped inside the accordion, DOM-order-after the chip row (same established pattern ELITEA-2215's AFS already documents — no dedicated testid observed there either) | n/a | none |

## Network Behavior
- `PATCH /api/v2/elitea_core/application_relation/prompt_lib/399/{sub_agent_app_id}/{sub_agent_version_id}`
  — fires on sub-agent selection from the "+ Agent" popper, `201 Created` on
  success. This is the Agent/Pipeline-type tool-attach persistence signal —
  **distinct** from the `PATCH .../tool/prompt_lib/{project}/{tool_id}`
  endpoint the Toolkit/MCP attach flows use (ELITEA-1950's AFS).
- Chat execution uses the standard WebSocket `chat_predict` envelope
  (consistent with every other embedded-chat case in this suite;
  `.agents/testing.md` — AI responses arrive ~2s+ after send, condition
  waits required, never a fixed sleep). For this nested-tool-call flow,
  observed round-trip time was **up to ~40s** ("Thought for 40 secs") — a
  longer wait budget than a simple single-tool call needs; automation should
  use a generous timeout (60s+) on the final-answer wait, not the ~10-15s
  budget sufficient for a flat single-tool-call flow.
- No additional GET refetch was required before the sub-agent's card
  rendered — same synchronous-with-PATCH-response behavior ELITEA-1950
  already documented for MCP cards.

## Known Defects Found During Exploration
- None (no product defect). Two findings, both handled as CLARIFICATIONS
  per the reverse-masking guard, neither newly filed:
  1. The "Agent tab is active" / explicit-Save case text (steps 2, 5) is the
     same stale-tabs-paradigm pattern already filed and confirmed live for
     Toolkit/MCP in
     [EliteaAI/elitea-testing-public#530](https://github.com/EliteaAI/elitea-testing-public/issues/530)
     — this run confirms the identical pattern extends unchanged to the
     Agent tool type. Cited, not re-filed (same root cause, same fix).
  2. The message-wording-determinism behavior (§ Axis 2) is normal LLM
     behavior given ambiguous natural-language instructions, not a platform
     defect — explicitly distinguished from the unrelated, confirmed-different
     defect #1127 (a tool-call-intent-leaks-as-text rendering bug never
     observed in this run).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- `AgentDetailPage.attach_agent(agent_name)` already exists (ELITEA-1902) and
  covers steps 2–3 verbatim — no new page-object method needed for the attach
  flow itself.
- New page-object work needed: (a) `add-data-testid` pass for the
  version-selector trigger/menu (§ Concrete Handles gap), (b) a helper to
  read the nested-agent accordion's chip contents — e.g.
  `ChatPage.get_nested_agent_tool_chips(agent_name)` that scopes into
  `chat-answer-thought-accordion >> h3:has-text(agent_name)`'s parent
  accordion, expands it if collapsed, and returns the `chat-answer-tool-chip`
  / `chat-answer-model-chip` texts inside — generalizes beyond this one case
  to any future "nested agent's own tool call" assertion.
- **`#524` (agent-create 400 on API path) did NOT fire via this run's UI-form
  agent creation** — both fixture agents saved cleanly through
  `agent-save-button`. If the implementer prefers an `AgentAPI`-created
  fixture instead of reusing the two left-in-place agents, the existing
  `reasoning_effort: "none"`-omit-`temperature` workaround
  (`.agents/memory/qa-engineer/open_cross_cutting_defects.md` #1) still
  applies to that path.
- Reuse `components.mui.Popper` — do not write new popper handling for the
  Agent picker, `attach_agent()` already wraps it correctly.
- The chat-execution steps (6–7) are the flow's slow part (~40s observed) —
  budget accordingly and use `wait_for` on the final answer text rather than
  a fixed sleep, per `.claude/rules/ui-tests.md`.
