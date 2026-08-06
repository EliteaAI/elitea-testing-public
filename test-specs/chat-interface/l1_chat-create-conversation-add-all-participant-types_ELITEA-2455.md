# Test Case: Chat – Create New Conversation and Add Agent, Pipeline, Toolkit, and MCP as Participants

## Metadata
- **TMS ID**: ELITEA-2455
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l1 (case priority: critical)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, batch `elitea-2455-chat-participants`)
- **Status**: **defect-found** — executed live end-to-end through Step 13 (all
  four addable participant types individually confirmed workable); a real,
  reproducible product defect (filed EliteaAI/elitea-testing-public#1279)
  BLOCKS reliably combining an Agent participant and a Pipeline participant in
  the same conversation, which the case's own flow requires before Steps
  14–20 (section order, distinct icons, no-duplicates, Send, owner icon, "all
  participants visible", misconfiguration warning) become meaningfully
  assertable. Per `.agents/testing.md` § Merge gate's analysis-time-entry
  bullet, this is genuinely **blocking** (prevents reaching later steps), not
  an isolable tail assertion — `defect-found`, not a soft-asserted
  `ready-for-automation`.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has NOT yet created the conversation under test (case creates a fresh one).

## Test Data
### Case's own table says "(none required)" — INCOMPLETE for Step 20
The case's own Test Data table has a single row, "(none required) — —". Live
exploration shows this is insufficient: Step 20 ("verify any misconfigured
entities display a yellow warning indicator") has NOTHING to verify unless at
least one participant is genuinely misconfigured — none of the case's example
entities ("agent", "ALL Pipeline Nodes", "storage" toolkit, "Aha!" MCP) are
misconfigured by default. See § Known Defects Found and § Automation Hints for
the declared test-data addition this needs (a toolkit with a deliberately
invalid credential, reusing the existing `github_toolkit_with_invalid_credential`
fixture — no new fixture required).

### reuse-existing (this suite's project — 399, Private)
- `agent_id` fixture (existing, healthy agent)
- `pipeline_with_llm_id` fixture (existing, healthy executable pipeline —
  chosen over the bare `pipeline_id` fixture specifically to avoid
  incidentally tripping the ALREADY-KNOWN #684 orphaned-version defect,
  which is a DIFFERENT bug from this AFS's #1279 finding)
- `artifact_toolkit` fixture (existing, healthy toolkit)
- `mcp_toolkit_with_tools` fixture (existing, healthy remote MCP — public
  `mcp.deepwiki.com` endpoint, 3 real tools)
- `github_toolkit_with_invalid_credential` fixture (existing — deliberately
  broken GitHub PAT) — reused as the ONE genuinely-misconfigured entity Step
  20 needs; NOT relied on for the case's OTHER steps

## Test Steps
1. Navigate to the Chats section and click the + Chat button
   - **Verify**: a new, blank conversation opens
2. Verify a new conversation is created with "Type your message..." placeholder in the input field
3. Verify the PARTICIPANTS panel is visible on the right and initially shows no participants
4. Click the + icon at the bottom left of the message input area
5. Verify a popup menu opens with options: Attach Files (showing "10 left"), Modules, Agents, Pipelines, Toolkits, MCPs, Invite Users
6. Click Agents, verify a submenu opens with a search field and "+ Create New Agent" option plus a list of available agents
7. Select an agent (e.g. "agent") and verify it appears in the AGENTS section of the PARTICIPANTS panel with name, version, and icon
8. Click + again, click Pipelines, verify a submenu with "+ Create New Pipeline" and available pipelines
9. Select a pipeline (e.g. "ALL Pipeline Nodes") and verify it appears in the PIPELINES section of the PARTICIPANTS panel
10. Click + again, click Toolkits, verify a submenu with toggle switches for each toolkit
11. Enable a toolkit by clicking its toggle switch (e.g. "storage") and verify it appears in the TOOLKITS section of the PARTICIPANTS panel
12. Click + again, click MCPs, verify a submenu with toggle switches for each MCP
13. Enable an MCP (e.g. "Aha!") and verify it appears in the MCPS section of the PARTICIPANTS panel
14. Verify all four sections are visible in order in the PARTICIPANTS panel: AGENTS, PIPELINES, TOOLKITS, MCPS
15. Verify each participant type shows a distinct icon (agent icon, pipeline icon, toolkit icon, MCP icon)
16. Verify no duplicate entries appear and no error messages are displayed
17. Type "Hi" in the message field and click Send
18. Verify the conversation is created and the owner icon is added in the PARTICIPANTS panel
19. Verify all added participants are visible under their respective type sections
20. Verify any misconfigured entities display a yellow warning indicator

## Expected Results
- All four participant types (Agent, Pipeline, Toolkit, MCP) can be added to
  one conversation simultaneously and each renders under its own section, in
  a fixed order (AGENTS → PIPELINES → TOOLKITS → MCPS).
- A genuinely misconfigured entity shows the yellow misconfiguration-warning
  indicator; healthy entities do not.
- No console errors, no duplicate participant entries.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats, click + Chat | new conversation opens | live step 1 | `sidebar-create-button` click + `chat-new-conversation-greeting` visible | asserted |
| 2 Verify "Type your message..." placeholder | placeholder text shown | live step 2 | `chat-message-input`'s `placeholder` attribute | **clarification** — confirmed live INTERMITTENT: reads empty (`""`) immediately after mount in some checks, correct text in others (screenshot + later live re-check both showed it correctly). Not confirmed as a hard, reliably-reproducing defect (unlike #1279) — filed EliteaAI/elitea-testing-public#1278 as a lower-confidence finding, soft-checked (not hard-asserted) if/when this AFS is re-attempted |
| 3 Verify PARTICIPANTS panel visible, initially empty | no participants shown | live step 3 | `expand_participants_panel_via_toggle()` + `PARTICIPANT_ROW_PREFIX` count == 0 | asserted |
| 4 Click + icon | popup menu opens | live step 4 | `plus-menu-button` click | asserted |
| 5 Verify popup menu items | Attach Files (10 left), Modules, Agents, Pipelines, Toolkits, MCPs, Invite Users | live step 5 | `chat-attach-menuitem-button` text, `internal-tools-menuitem`/`agents-menuitem`/`pipelines-menuitem`/`toolkits-menuitem`/`mcps-menuitem` visible, `get_open_plus_menu_item_count() == 5` | asserted, WITH clarification: **Invite Users is absent, not merely present-but-disabled**, for this suite's Private project (`PlusChatButton.jsx`'s `!isPrivateProject` guard — source-confirmed, not a defect) |
| 6 Click Agents, verify submenu | search field + "+ Create New Agent" + agent list | live step 6 | `agents-search-input` visible, `agents-create-new-button` visible | asserted (in isolation — see row 7/9 below for the coexistence blocker) |
| 7 Select an agent, verify AGENTS section | agent appears with name/version/icon | live step 7 | `agents-menu-item-agent-{project}-{id}` click → `chat-participant-row-application_{id}_{project}` visible | asserted WHEN the agent is added ALONE or added AFTER the pipeline (see #1279); **NOT reliably asserted when added BEFORE the pipeline** — confirmed live 2/2 times in that order the SECOND add (pipeline) silently no-ops, and even in the working order the automated pytest run itself intermittently failed to render the agent row within 10s (once observed) — this is the core #1279 finding |
| 8 Click +, Pipelines, verify submenu | "+ Create New Pipeline" + pipeline list | live step 8 | `pipelines-search-input` visible, `pipelines-create-new-button` visible | asserted (in isolation) |
| 9 Select a pipeline, verify PIPELINES section | pipeline appears | live step 9 | `pipelines-menu-item-pipeline-{project}-{id}` click → `chat-participant-row-pipeline_{id}_{project}` visible | **blocked** — see #1279: Agent-then-Pipeline order is a confirmed SILENT NO-OP (pipeline never added, no error); Pipeline-then-Agent order adds both but throws a console error/exception (`version/prompt_lib` 400 + `icon_meta` TypeError) during the Agent add, and even that order's overall reliability was NOT reproduced 2/2 in the automated pytest harness (see row 7) |
| 10 Click +, Toolkits, verify toggle submenu | toggle switches per toolkit | live step 10 | `toolkits-search-input` visible (via `open_toolkits_submenu()`) | asserted (in isolation, confirmed with a freshly-created toolkit both via a scratch script and inside the fixture chain) |
| 11 Enable a toolkit, verify TOOLKITS section | toolkit appears | live step 11 | `toolkits-menu-item-toolkit-{project}-{id}` click → `chat-participant-row-toolkit_{id}_{project}` visible | asserted in isolation; **not independently re-verified in COMBINATION with a stable agent+pipeline pair**, since row 9 blocks reaching that combined state reliably |
| 12 Click +, MCPs, verify toggle submenu | toggle switches per MCP | live step 12 | `mcps-search-input` visible | asserted (in isolation) |
| 13 Enable an MCP, verify MCPS section | MCP appears | live step 13 | `mcps-menu-item-mcp-{project}-{id}` click → `chat-participant-row-toolkit_{id}_{project}` (MCP participants share the toolkit row-id shape) visible | asserted in isolation; known risk of the ALREADY-FILED #687 false-positive "Server is disconnected!" warning (cited, not re-diagnosed) |
| 14 Verify 4 sections in fixed order | AGENTS, PIPELINES, TOOLKITS, MCPS | — | — | **blocked** — depends on reliably reaching the combined 4-participant state row 9 blocks. Source-confirmed fixed order exists (`ExpandedPerticapantsList.jsx`/`CollapsedPerticapantsList.jsx`'s identical literal `ENTITY_SECTIONS` array), but not independently re-verified live in combination |
| 15 Verify distinct icon per type | 4 distinct icons | — | — | **blocked** — same dependency as row 14. Handle identified (`chat-participants-badge-icon-{section}`, collapsed-badge-only — the EXPANDED panel's per-row icon carries no testid, confirmed by reading `ParticipantItem.jsx`) but not exercised against the full combined state |
| 16 Verify no duplicates, no errors | clean state | — | — | **blocked** — the #1279 console error (`version/prompt_lib` 400 + `icon_meta` TypeError) IS an error this step would need to classify; can't complete "no errors" meaningfully while #1279 is open |
| 17 Type "Hi", Send | message sent | — | — | **blocked** — downstream of the above; not attempted against an unstable base state |
| 18 Verify conversation created + owner icon | conversation persists, owner shown | — | — | **blocked** for the owner-icon half AND for reachability: separately, source-confirmed the owner/Users section NEVER renders for a Private project (`showUsersSection = !isPrivateProject`, both collapsed AND expanded) — a case-text clarification independent of #1279, but moot until #1279 is resolved anyway |
| 19 Verify all participants visible under sections | all 4 types shown | — | — | **blocked** — same dependency chain |
| 20 Verify misconfigured entities show warning | yellow warning shown | — | — | **blocked** — this is the case's own headline objective; needs a stable base state to add the deliberately-misconfigured toolkit (test-data addition, see § Test Data) on top of, which #1279 prevents reaching reliably |

### Axis 2 — Analyst additions
- Console-error capture across the whole flow (filtered only for the two
  KNOWN, already-filed signatures — #1279's `version/prompt_lib` 400 +
  `icon_meta` TypeError) — *added: standard side-channel defect-detection
  guard, this is what surfaced #1279 in the first place.*
- Deliberately-misconfigured toolkit participant (`github_toolkit_with_invalid_credential`)
  — *added: the case's own Test Data table provides no misconfigured entity,
  so Step 20 has nothing to verify without one (see § Test Data).*

## Cleanup
- Conversation deleted via `ConversationAPI.delete_conversation()` once created.
- Agent/pipeline/toolkits deleted by their respective fixtures' teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| +Chat button | `[data-testid="sidebar-create-button"]` | **on-main ✓** | pre-existing (`ChatPage.click_create_conversation()`) |
| New-conversation greeting | `[data-testid="chat-new-conversation-greeting"]` | **on-main ✓** | pre-existing |
| Message input | `[data-testid="chat-message-input"]` | **on-main ✓** | pre-existing; `placeholder` attribute intermittent, see #1278 |
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing |
| Attach Files popper row | `[data-testid="chat-attach-menuitem-button"]` | **on-`automation/testids` ✓** (already wired, `AttachmentButton.jsx`'s `testId` prop) | text = `"Attach Files{N} left"` |
| Modules/Agents/Pipelines/Toolkits/MCPs menu items | `[data-testid="internal-tools-menuitem"]` / `agents-menuitem` / `pipelines-menuitem` / `toolkits-menuitem` / `mcps-menuitem` | **on-main ✓** | pre-existing, hover-triggered |
| Agents/Pipelines search inputs | `[data-testid="agents-search-input"]` / `[data-testid="pipelines-search-input"]` | **on-`automation/testids` ✓`** — generic `PlusChatSubmenu.jsx` template (`${sectionKey}-search-input`), already renders for every section, not newly added | |
| Agent/Pipeline item rows (dynamic) | `[data-testid="agents-menu-item-agent-{project_id}-{agent_id}"]` / `[data-testid="pipelines-menu-item-pipeline-{project_id}-{pipeline_id}"]` | **on-`automation/testids` ✓** — same generic template, confirmed live via `useDropdownData.jsx`'s `agentMenuItems`/`pipelineMenuItems` `key:` fields (`agent-${project_id}-${id}` / `pipeline-${project_id}-${id}`) | select-and-close semantics (click auto-closes the popper) |
| Toolkit/MCP item rows (dynamic) | `[data-testid="toolkits-menu-item-toolkit-{project_id}-{toolkit_id}"]` / `[data-testid="mcps-menu-item-mcp-{project_id}-{toolkit_id}"]` | **on-`automation/testids` ✓** — pre-existing (ELITEA-2094/2203 prior passes) | toggle-switch semantics (does NOT auto-close the popper) |
| Participant row (dynamic, per type) | `[data-testid="chat-participant-row-{uniqueId}"]`, `uniqueId` = `application_{id}_{project}` (agent) / `pipeline_{id}_{project}` / `toolkit_{id}_{project}` (toolkit AND MCP share this shape) | **on-main ✓** | ONLY rendered for a non-misconfigured participant — a misconfigured one renders via the attention branch instead (below) |
| Misconfiguration warning | `[data-testid="chat-participant-warning-icon"]` | **on-main ✓** | shared/static across ALL misconfigured participant types |
| Collapsed badge, per section | `[data-testid="chat-participants-badge-{section}"]` (`section` ∈ agents/pipelines/toolkits/mcp/users) | **on-main ✓** | ONLY renders while the panel is COLLAPSED |
| Collapsed badge entity icon, per section | `[data-testid="chat-participants-badge-icon-{section}"]` | **on-`automation/testids` ✓** — commit `8971529f`, added ahead of ELITEA-2094's now-parked implementation | the only per-type-distinct-icon signal with a testid at all — the EXPANDED panel's row icon (`ParticipantItem.jsx`) has none |
| Participants panel toggle | `[data-testid="chat-participants-panel-toggle-button"]`, state via `data-expanded` | **on-main ✓** | pre-existing |

## Network Behavior
- Adding a participant fires the participant-update mutation; `wait_for_network()`
  (networkidle) after each add is sufficient in isolation.
- The #1279 defect surfaces via `GET /elitea_core/version/prompt_lib/{project}/{agent_id}/{version_id}`
  returning 400 when the Agent is added AFTER the Pipeline.

## Known Defects Found During Exploration
- **[BLOCKING]** EliteaAI/elitea-testing-public#1279 — Adding a Pipeline
  participant after an Agent participant is a silent no-op; the reverse
  order works but throws a console error/exception, and was not reliably
  reproduced 2/2 even in the automated harness. Sibling of #684 (same
  participant-state `version_id` mixup family the parked ELITEA-2094
  investigation documented — "can crash immediately, crash later at Send,
  silently misclassify a badge into the wrong PARTICIPANTS section, or
  resolve with ZERO VISIBLE SYMPTOM depending on timing"). This is the
  blocker driving this AFS's `defect-found` status.
- **[MINOR, low-confidence]** EliteaAI/elitea-testing-public#1278 — the
  composer's `placeholder` attribute reads empty (`""`) immediately after a
  new conversation mounts, in some checks; other checks (a screenshot, a
  later live re-check) showed the correct `"Type your message..."` text.
  Not confirmed as a hard, reliably-reproducing defect — flagged
  lower-confidence, worth a fresh, dedicated timing investigation if
  re-attempted, not a blocker.
- Pre-existing, cited not re-diagnosed: EliteaAI/elitea-testing-public#684
  (pipeline orphaned-version silent-crash-no-warning) and #687 (healthy
  remote MCP false-positive "disconnected" warning) — both from the
  ELITEA-2094 investigation, both in the same participant-state instability
  family as #1279.

## Blocked Steps
- Steps 9, 14–20 (see Coverage Map) — blocked by EliteaAI/elitea-testing-public#1279.
  Re-attempt once #1279 is fixed; the Concrete Handles table above and the
  page-object method shapes named in § Automation Hints below should still
  be valid and save significant re-discovery time.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Fixtures: `agent_id`, `pipeline_with_llm_id` (NOT the bare `pipeline_id` —
  avoids incidentally tripping #684), `artifact_toolkit`,
  `mcp_toolkit_with_tools`, `github_toolkit_with_invalid_credential` (for
  Step 20's test-data gap) — all pre-existing, no new fixture needed.
- New `ChatPage` methods a re-attempt should add (verified working
  individually during this pass, NOT committed — see session notes):
  `agents_search_input` / `pipelines_search_input` LocatorDescriptors;
  `AGENT_PARTICIPANT_MENU_ITEM` / `PIPELINE_PARTICIPANT_MENU_ITEM` dynamic
  template constants (`'[data-testid="agents-menu-item-agent-{}-{}"]'` /
  `'[data-testid="pipelines-menu-item-pipeline-{}-{}"]'`);
  `open_agents_submenu()` / `open_pipelines_submenu()` /
  `select_agent_participant(project_id, agent_id)` /
  `select_pipeline_participant(project_id, pipeline_id)` — select-and-close
  analogues of the existing toggle-switch `add_toolkit_participant_via_slash_menu()`;
  `chat_attach_menuitem_button` LocatorDescriptor (consumes the pre-existing
  `chat-attach-menuitem-button` testid); `PARTICIPANTS_BADGE_ICON` template +
  `get_visible_participants_badge_sections()` / `is_participants_badge_icon_visible()`
  for Steps 14–15; `close_plus_menu_popper_on_new_conversation()` (the
  existing `close_plus_menu_popper()` requires `chat-message-list`, which
  does NOT render on a brand-new, unsent conversation — confirmed live,
  needs the `chat-new-conversation-greeting` container as the outside-click
  target instead).
- Row-lookup gotcha: `agent_id` and `pipeline_with_llm_id` fixtures BOTH
  derive their entity name from the identical `f"autotest_{request.node.name}"[:32]`
  pattern — their display names collide. Resolve participant rows by
  UNIQUE-ID testid (`chat-participant-row-application_{agent_id}_{project_id}`
  / `chat-participant-row-pipeline_{pipeline_id}_{project_id}`), never by
  `get_participant_row_by_name()`'s text filter, when both are present.
- No testids needed adding to EliteaUI for this case — every handle above
  already exists on `automation/testids`.
