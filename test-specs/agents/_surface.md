# Agents surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent detail page
(`/agents/all/{id}?viewMode=owner`) — VERSION area + Run History + LLM Model Settings dialog.
Not a substitute for execution — verify a handle as you use it. One writer at a time; last
confirmed by: qa-engineer analyst, ELITEA-1878/1879 run.

## VERSION selector (all pre-existing, confirmed live repeatedly across ELITEA-1888/1889/1892/1890/1891)
- `agent-version-selector-trigger` — combobox trigger, text = current version name only (no date/status).
- `version-option-{version_name}` — dynamic per-option testid (`AgentDetailPage.VERSION_OPTION` template).
  Option text = `"{name} - {DD.MM.YYYY}"` (date baked into the SAME node's text, no separate handle; no
  time-of-day shown despite some case text saying "date/time").
- `agent-actions-menu-button` → overflow menu; `publish-version-menuitem` / `unpublish-version-menuitem` /
  `set-as-a-default-menuitem` all derive automatically from `DotMenu.jsx`'s `testId: item.key` mechanism
  (`ApplicationControls.jsx`'s menu-item `key` fields) — confirmed live for all three.

## Sort order (VersionSelect.jsx `versionSelectOptions`, code-confirmed + live-confirmed)
`[pinned/default version] → [everything else by created_at DESCENDING, Published/Draft interleaved, NO
status tier] → [base, ONLY if base is not itself pinned]`. A freshly created agent's `meta.default_version_id`
already equals its own base version's id, so **base is pinned (and sorts FIRST) on a brand-new agent** —
it only moves to last once a different version is explicitly pinned. Case text that implies "Published
always sorts above Draft" or "base always sorts last" is stale — see
EliteaAI/elitea-testing-public#1091 for the full write-up.

## Pin ("Set as a default") flow
- Trigger: `agent-actions-menu-button` → `set-as-a-default-menuitem` (aria-disabled="true" when the
  currently-viewed version IS already default).
- Opens `SetDefaultVersionDialog` — **NO testid on its confirm button** ("Set as a default", plain text
  match only) or Cancel button. **Testid gap** — needed by any case that must actively re-pin a version.
- Pin icon (`PinIcon`) renders inside the option list (`buildVersionOption`'s `IconBlock`, no testid) AND
  inside the closed trigger's `customRenderValue` (`VersionSelect.jsx`, no testid). **Testid gap** on
  both; only the option-list one has been needed/flagged so far (ELITEA-1891) — flag the trigger one too
  if a future case needs to assert the pin icon on the CLOSED selector specifically.
- `PUT/POST .../default_version/prompt_lib/{project}/{agentId}` fires on confirm.

## Save As Version / Publish (fully testid'd, see ELITEA-1888/1892 AFS for the complete handle table)
- `agent-save-as-version-button` → `agent-version-dialog-name-input` → `agent-version-dialog-save-button`.
- `publish-version-menuitem` → 3-step wizard (`agent-publish-version-name-input`,
  `agent-publish-category-select`, `agent-publish-agree-checkbox`, `agent-publish-continue-button` →
  AI `publish_validate` gate → `agent-publish-confirm-button`). Publish clones the version rather than
  flipping status in place; auto-navigation after Publish is unreliable (issue #614) — always
  explicitly re-select the new version by name afterward, never trust the URL to land there.
- AI validation gate needs: non-empty Tags + substantive (non-trivial) Instructions to pass on the first
  attempt — seed both directly in the agent-creation API payload to avoid throwaway `422` round-trips.

## Known defects reproduced (not new, don't re-file)
- #611 — Publish-wizard Stepper leaks MUI boolean props onto `<svg>`, 4 console warnings, cosmetic only.
- #614 — post-Publish/re-pin client-side status staleness (VERSION trigger, overflow-menu Publish/Unpublish
  item can lag the true server state for a beat); `select_version_by_name()` / `wait_for_publish_status_menuitem()`
  on `AgentDetailPage` already harden against it with retry+reload+API-tie-breaker patterns.

## LLM model catalog contents (project `Private`/399, ELITEA-1882 run, 2026-08-06)
- `GET /api/v2/configurations/models/399?include_shared=true` → `total: 11` — full
  live inventory (name/display_name): `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
  "Anthropic Claude 4.5 Sonnet" (default), `eu.anthropic.claude-sonnet-4-6` "Anthropic
  Claude 4.6 Sonnet", `eu.anthropic.claude-haiku-4-5-20251001-v1:0` "Anthropic Claude
  Haiku 4.5", `global.anthropic.claude-sonnet-5` "Anthropic Sonnet 5",
  `claude-sonnet-4-5` "Azure Claude Sonnet 4.5", `claude-sonnet-4-6` "Azure Claude
  Sonnet 4.6", `claude-sonnet-5` "Azure Claude Sonnet 5", `gpt-5-mini` "GPT-5 mini"
  (low-tier default), `gpt-5.2` "GPT-5.2" (high-tier default), `gpt-5.4` "GPT-5.4",
  `gpt-5.4-mini` "GPT-5.4-mini". OpenAI entries carry NO vendor prefix in
  `display_name` (unlike Anthropic/Azure, which are all vendor-prefixed) — match
  `"GPT-5 mini"` literally, not `"OpenAI GPT-5 mini"`.
- **No `GPT-4.1` anywhere in the catalog** — confirmed twice independently (this run,
  and the `settings-ai-providers/_surface.md` capture the day before on the same
  project). A TMS case naming `GPT-4.1` as an available model is stale — the
  platform's OpenAI lineup has moved to the GPT-5 family. Filed as clarification
  [EliteaAI/elitea-testing-public#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285).
  Don't assume this list is exhaustive-forever — re-verify live per case, this is a
  handle cache not a frozen catalog.
- `model-selector-option-{name}` dynamic testid (added ELITEA-1881) covers ALL 11
  entries, OpenAI included — no new testid work needed for OpenAI-model cases.

## LLM Model Settings dialog (gear icon, ELITEA-1880 run, 2026-08-02)
- Trigger: gear-icon button next to `model-selector-button`/`model-selector-name`, `aria-label="model settings menu"`.
  **No testid** — `LLMModelSelector.jsx` default-variant `ButtonGroup` branch (the widget's `field` variant has an
  equivalent gear button too, also untestid'd). Testid needed: `model-settings-button` (generic — this is a shared
  widget, `src/[fsd]/widgets/llm-model-selector/`, used by ChatBox/TestSettings/etc, same generic-naming precedent
  as the pre-existing `model-selector-button`).
- Opens `LLMSettingsDialog.jsx` → MUI `Modal.BaseModal`, title **"Model settings"**. `Modal.BaseModal` itself
  ALREADY supports `data-testid`/`titleTestId`/`closeButtonTestId`/`cancelButtonTestId`/`confirmButtonTestId` props
  (`EliteaUI/src/[fsd]/shared/ui/modal/BaseModal.jsx:32-36`) but `LLMSettingsDialog.jsx` doesn't wire any of them —
  purely a threading gap, not a missing-capability gap. Also: `LLMSettingsDialog` supplies its OWN `actions` JSX
  (Cancel/Apply/Reset-to-defaults) rather than using BaseModal's built-in `onConfirm`-driven action row, so those
  buttons' testids need to be added at the `Button.BaseBtn` call sites inside `LLMSettingsDialog.jsx`, not via the
  BaseModal props.
- Dialog content, top to bottom: **Reasoning** slider (Low/Medium/High, only when `model.supports_reasoning` is
  true — a NON-reasoning model gets a Creativity/Temperature slider instead, `LLMSettings.jsx`'s
  `model?.supports_reasoning ? <ReasoningSlider/> : <CreativitySlider/>` branch) → **Max Completion Tokens**
  section (always present regardless of model type; 2-way toggle labeled **"Default" / "Custom"** — NOT "Auto",
  despite the internal value being `'auto'`) → **Capabilities** chips (e.g. "Reasoning") → Cancel/Apply buttons
  (no Reset-to-defaults on the agent-page instance — `onResetToDefaults` isn't wired there). None of these
  sub-elements have testids yet. Opening/toggling the dialog fires NO network request — pure client-side React
  state (`LLMSettingsDialog`'s `localSettings`), only pushed to the parent on Apply.
- Reload-based persistence (page.reload() + `wait_for_page_load()`) correctly shows the previously-saved model in
  `model-selector-name` — confirmed live, no defect. (ELITEA-1881's existing test only asserts persistence via the
  Save PUT's 201 status, never via an actual reload — this was the first live confirmation of reload-level
  persistence for the model selector specifically.)
- **Tooling note:** no Playwright MCP server was available this session; explored via a standalone
  `sync_playwright` script driving `AgentDetailPage`/`AgentAPI` directly (not committed, scratch-only).

## Agent creation payload gotcha (still open, #524)
`temperature` + a non-`"none"` `reasoning_effort` 400s on the project's default reasoning-capable model.
Every disposable-agent fixture in this area uses `reasoning_effort: "none"` and omits `temperature`.

## Run History panel (ELITEA-1877 run, live + code confirmed)
- Trigger: `pipeline-history-tab` (shared `ViewRunHistoryButton.jsx`, `src/[fsd]/shared/ui/button/` —
  also used by Pipelines/MCP/Toolkit run history; the name is a naming-precedent smell — feature-scoped
  string hardcoded in a shared component — but it's pre-existing on `main` and reused as-is, not a new
  violation to fix here). Lives in `ConfigurationTab.jsx`'s `ConfigurationRightContent`, which is the
  right-panel content shown only while `!showHistory` — clicking it opens `RunHistoryContainer`, which
  REPLACES the whole form+chat grid (not a tab, not an overlay).
- `RunHistoryContainer` = `RunHistoryList` (left, the entries) + `RunHistoryChat` (right, selected
  entry's messages). Default sort = Date **descending** (`RunHistoryList.jsx`
  `useRunHistorySorting(SORT_TYPES.DATE)`) — index 0 is always the most recent entry, so "not the most
  recent" = `.nth(1)` or higher, no need to read dates.
- **Testid gaps (needs-adding):** `RunHistoryListItem.jsx`'s row `Box` has ZERO testid and zero
  `data-*` state attribute — selection is pure `sx` styling (`styles.selected`). Add
  `data-testid="run-history-list-item"` (same literal on every row — rows are positionally
  distinguished) + `data-selected={selectedItem === item.id}` on that `Box`.
- **No new testid needed for the selected run's messages** — `RunHistoryChat.jsx` renders the SAME
  shared `ChatMessageList` component the main embedded chat uses, so `chat-message-list` /
  `chat-message-item` (both on-main ✓, pre-existing) work unchanged inside the History panel too
  (confirmed live). Don't add a wrapper testid just to "scope" it — only one instance of
  `chat-message-list` exists on the page while History is open (the main embedded chat is unmounted).
- **STALE — #1093 now appears FIXED (re-verified live, ELITEA-1876 run, 2026-08-06):**
  the ELITEA-1877 note below described `EliteaAI/elitea-testing-public#1093` (no UI way to
  close/exit Run History) as confirmed-open. Re-checked live this run
  (`manual_test_agent`, agent id 5189): `RunHistoryContainer.jsx` now renders a wired
  `aria-label="close run history"` `IconButton` whenever `onClose` is passed, and clicking it
  correctly closes the panel and restores the Configuration form + embedded chat. Flagged for
  a human to verify/close #1093 — not re-opened, not re-filed. *(Original note, kept for
  history: "no UI way to close/exit Run History once opened... only exits: 'Restore chat' on a
  row's overflow menu, or leaving the page" — no longer accurate.)*
- **Row content = exactly 3 columns, no conversation preview (ELITEA-1876 run, 2026-08-06,
  live + code confirmed):** each `run-history-list-item` row renders **Date** (format
  `dd-MM-yyyy, hh:mm a`, e.g. `17-07-2026, 05:57 PM`) + **Version** (agent version name,
  e.g. `base`) + **Duration** (e.g. `9.33 s`) — `RunHistoryList.jsx`'s `tableHeaderItems`
  literally is `['Date', 'Version', 'Duration']`. There is NO first-message/title preview
  anywhere in the row — that content only ever appears in the right-hand `RunHistoryChat`
  panel after a row is clicked. A case expecting a per-row "preview (first message or
  title)" is describing a different (ChatGPT-sidebar-style) design than what's implemented;
  treat as case-text drift, not a defect — filed as clarification
  `EliteaAI/elitea-testing-public#1282`. All three columns are readable from the row's own
  `text_content()` — no per-cell testid needed, `RUN_HISTORY_LIST_ITEM_SELECTOR` already
  exposes them.
- Test-data trick to get 2 distinct run-history entries for one agent without 2 agents/sessions: send a
  message (conversation A persists server-side) → click **Clear chat** (`chat_clear_button` —
  `ChatBox.jsx` `onClickClearChat`, `isAgentsPage` branch starts a fresh **local, unsaved**
  `isNew: true` conversation, it does NOT touch conversation A) → send a second message (persists as
  conversation B). Both now list as separate Run History rows.
- Endpoints: list = `GET /elitea_core/conversations/prompt_lib/{projectId}?source=agent&entity_name=application&entity_meta_id={agentId}&...`;
  detail (on row click) = `GET /elitea_core/conversation/prompt_lib/{projectId}/{conversationId}`.
- **Possible flakiness in ELITEA-1877's existing merged test (observed, not investigated,
  2026-08-06):** 2 consecutive clean `pytest` re-runs of
  `test_select_past_run_loads_chat_messages` both FAILED, with 2 different signatures — once
  empty text in the selected historical run's detail panel, once the embedded chat's "last
  message" not containing the just-sent message text. Looks like AI-response/timing
  flakiness in the message-content assertions, unrelated to the row-level Date/Version/
  Duration content this digest entry and ELITEA-1876's AFS document. Flagging for whoever
  next touches this spec / the next hardening gate — not chased further here (out of
  ELITEA-1876's scope).

## "+ Skill → Create new" round-trip from the Agent editor (ELITEA-1999 run, 2026-08-02)
- `agent-add-skill-button` → `UnifiedDropdown` popper → "Create new" item (plus-icon, label "Create new")
  is a **bare `<MenuItem>` with NO testid** (`src/components/UnifiedDropdown.jsx`, shared with the
  Toolkit picker's identically-shaped, identically-testid-less item). **Testid gap** — thread a
  `createNewTestId` prop through `UnifiedDropdown` (mirrors its existing `showCreateNew`/`onCreateNew`/
  `createNewLabel` trio); `SkillMenu.jsx` should pass `agent-add-skill-create-new-button` (same pattern
  ELITEA-2166 already used for `agents-create-new-button` on a different shared submenu).
- Clicking it navigates to `/skills/create?source_application_id={agentId}&return_url={encoded /agents/all/{agentId}?viewMode=owner&name=... }`.
  Both the manual Save path (`CreateSkillTabBar.onSave()`) and the Build-with-AI approve path
  (`GenerateSkillModal.jsx`) check these two params and, if present, redirect back to `return_url` with
  `?newSkillId={id}` appended instead of going to the Skill's own details page — same "round-trip"
  shape the source comments call "mirrors the toolkit newToolkitId round-trip" (untested toolkit analog,
  `ToolMenu.jsx`, likely has the identical testid gap — not verified this run, flagging for whoever
  automates the Toolkit-picker analog).
- **Auto-attach after redirect is ASYNC, ~4s, and NOT gated on the Agent's own Save button.**
  `SkillMenu.jsx`'s `useEffect` reads `newSkillId` from the URL, does `GET .../skill/prompt_lib/{proj}/{id}`
  → `PATCH .../skill/prompt_lib/{proj}/{id}` (attach) → the skills list refetches
  (`GET .../application_skills/prompt_lib/{proj}/{agentVersionId}`) → THEN the UI's counter/`skill-card-{id}`
  update and the `newSkillId` param is stripped from the URL. Measured live: still 0/5 + no card at t≈2-4s
  post-redirect, 1/5 + card visible by t≈5.5s. **Asserting immediately after the redirect is a guaranteed
  false negative** — wait on the card/counter with a real timeout (~10s), never a short/no wait. The
  attachment PATCH persists server-side the instant it resolves 201 — reload alone (no Save click) shows
  it; Save is NOT the causal mechanism, just what the case's own steps happen to do next.
- Fixture-agent gotcha: use `AgentAPI.create_agent()`'s default `_default_llm_settings()` (temperature=null,
  reasoning_effort="medium") — already avoids the #524 400 gotcha, no override needed for a disposable
  Skill-attachment fixture agent.

## Tags field (ELITEA-1878/1879 run, 2026-08-06)
- Combobox accessible name "Tags", part of the same shared `ApplicationEditForm.jsx`
  → `TagEditor.jsx` → `AutoCompleteDropDown.jsx` component the Pipeline form uses
  (`pipeline_form_page.py`'s `pipeline-tags-input`/`pipeline-tags-chip`). **Agent
  branch has NO testids today** — `ApplicationEditForm.jsx:182-183` sets
  `inputTestId`/`chipTestId` to `undefined` for the non-pipeline (Agent) case,
  by explicit design ("canon #511 scope discipline: no case exercises Agent's
  Tags yet" — that comment is now stale as of this run).
- `AutoCompleteDropDown.jsx` already supports `chipTestId`/`chipDeleteTestId` as
  **either a static string or a function of the option** (`typeof x === 'function'
  ? x(option) : x`, lines 213-214 / 240-249) — the Pipeline form only uses the
  static-string form (one shared testid for every chip), but the Agent
  implementation should use the function form (`option => \`agent-tags-chip-${option.name}\``)
  since a case that must verify TWO specific tags (ELITEA-1878) or delete ONE
  specific tag among several (ELITEA-1879) needs per-tag addressability, not just
  "N chips exist." See ELITEA-1878/1879 AFS for the full testid-needed table.
- Interaction: click the Tags input, `press_sequentially(tag_name)`, `Enter` commits
  it as a chip — pure client-side Formik state (`TagEditor`'s `onChangeTags` →
  `formik.setFieldValue('version_details.tags', ...)`), no network request until
  Save. Chip renders as `role="button"` with an `img` delete icon inside
  (clicking either the chip or its delete icon removes it via `onDelete`).
- Save (`agent-save-button`) → `PUT .../application/prompt_lib/{proj}/{id}` → `201`,
  persists `version_details.tags`. Reload (`GET` same endpoint) correctly reflects
  the saved tag set — confirmed live, both add-two-tags and remove-one-tag-keep-
  the-other round trips work with no functional defect.
- **Tags-autocomplete option-list fetch**: `GET /elitea_core/tags/prompt_lib/{proj}?...&entity_coverage=application`
  fires on field mount (project-wide existing-tag suggestions) — irrelevant to
  freeSolo-typed new tags, noted for completeness only.
- **manual_test_agent (id 5189) was used for this run's live exploration and Save
  was clicked repeatedly** (unlike ELITEA-1873's Discard exploration, which never
  saved) — fully reverted to zero tags before handoff; confirmed via a final
  reload. Future analysts reusing this shared agent for other UI-only checks:
  its Tags field should read empty as of 2026-08-06.

## Discard flow (ELITEA-1873 run, 2026-08-06)
- `discard-button` (tab-bar) IS wired up live on the Agent detail page —
  re-confirmed via DOM probe (`document.querySelector('[data-testid="discard-button"]')`),
  disabled by default, enabled once `isFormDirtyExcluding` is true. This
  **contradicts a prior implementer note** on
  `automation/tests/ui/agents/test_agent_save_as_version.py` (ELITEA-1888)
  claiming the testid was "confirmed absent from the DOM" — that note is now
  stale (left as-is, not this case's file to touch); the testid is present
  and correctly wired today.
- The confirmation modal (MUI "Warning", "Are you sure you want to discard
  changes?") and its Discard confirm button carried **zero testids** prior
  to this run — `ApplicationTabBar.jsx`'s `<Button.DiscardButton
  dataTestId="discard-button">` call site never threaded `DiscardButton`'s
  `modalDataTestId`/`confirmButtonDataTestId` props through to
  `Modal.BaseModal`, even though `BaseModal` already supports both (same
  threading-gap shape ELITEA-1971 fixed for `CredentialsTabBar.jsx`).
  **Resolved during ELITEA-1873 implementation:** added
  `modalDataTestId="discard-confirm-modal"` +
  `confirmButtonDataTestId="discard-confirm-button"` to `ApplicationTabBar.jsx`
  (generic names — this component is SHARED between `EditApplication.jsx`
  (Agents) and `EditPipeline.jsx` (Pipelines), confirmed via `git grep`, so a
  feature-scoped name would misrepresent it, matching the pre-existing
  generic `discard-button`). Live-confirmed via HMR: both testids render
  correctly, and the full edit→discard→revert round trip works for Name,
  Description, and Instructions (single-field AND simultaneous three-field
  edits both tested). EliteaUI commit `EliteaAI/EliteaUI@cc327ec9` on
  `automation/testids` (pushed).
- `discardApplicationChanges` (`useDiscardApplicationChanges.js`) is a pure
  client-side Formik `resetForm()` — no network request fires on discard
  (source-confirmed). Don't look for a PUT/GET to assert against for the
  discard action itself, unlike Save.

## Build with AI from the in-chat "+ Create New Agent" canvas (ELITEA-1920 run, 2026-08-02)
- The canvas (`AgentCanvasPage`, ELITEA-2166) renders the exact same `CreateAgentForm.jsx` as
  `/agents/create`, confirmed to include the SAME `GenerateAgentButton`/`generate-agent-open-button` —
  zero new testids needed to drive Build-with-AI from inside the chat canvas.
- Completion wiring is genuinely different from `/agents/create`, though: chat-hosted creation goes
  through `src/hooks/chat/useAgentCreation.js` (NOT a page navigation) — it turns the created agent into
  a participant via `addNewParticipants(...)` and auto-activates it. URL stays on
  `/chat?edited_participant_id={id}`; it never navigates to `/agents/all/{id}` the way the standalone
  create-page flow does. An implementer reusing `GenerateAgentModalPage.approve_button.click()` inside
  the chat canvas must NOT wait for an `/agents/all/{id}` navigation (ELITEA-1909's pattern) — wait on
  `AgentCanvasPage.title` switching to the agent's name, or on the Participants popover, instead.
- `ChatPage.switch_project()` to the ALREADY-active project can hang the composer in a permanent loading
  spinner (`MuiCircularProgress` inside a `css-*` overlay Box that then blocks `plus-menu-button` clicks)
  in a from-scratch `sync_playwright` script — skipping the redundant switch when already on the target
  project avoided it. Not confirmed as a real product defect (never reproduced through the normal pytest
  fixture chain, only this ad-hoc script) — flagging as a possible transit-path fragility, not filed.

## Conversation starter chips in the EMBEDDED chat (Agent Detail page, ELITEA-1886 run, 2026-08-06)
- **Two DIFFERENT React call sites render "starter chips in a chat area" — do not conflate them.**
  Both use the same shared `EllipsisTextWithTooltip` (`src/components/ConversationStarters.jsx`):
  1. `src/pages/NewChat/NewConversationView.jsx:1020` — the standalone `/chat/{id}` "start new
     conversation" landing view (Agent Hub → Start Chat flow, ELITEA-2369). **Wired**:
     `testId="chat-conversation-starter-tile"`, already backs `ChatPage.CHAT_STARTER_TILE`.
  2. `src/pages/NewChat/ChatConversationStarters.jsx` — rendered by `ChatBox.jsx` (the EMBEDDED chat
     mounted directly on `/agents/all/{id}` and other feature pages that host the same `ChatBox`).
     **NOT wired** — confirmed via source read, no `testId` prop passed at all. This is the call site
     ELITEA-1886 exercises. `automation/pages/chat_page.py` (lines 642-653) already documents this split
     in a comment above `CHAT_STARTER_TILE`. **Testid needed**: `chat-conversation-starter-tile` (reuse
     the literal — same visual/functional concept, the two call sites never co-render on one page) on
     `ChatConversationStarters.jsx`'s `<EllipsisTextWithTooltip>` call — not yet added as of this run.
- **Starter chips render live/reactively in the embedded chat as you type into the agent-form starter
  fields — before Save.** Same live-preview behavior already documented for the welcome message
  (see the welcome-message section above / ELITEA-1885) — not a defect, just don't mistake the pre-Save
  preview for the persisted-state proof point.
- **Clicking a chip is pre-fill-ONLY, never auto-send.** `ChatBox.jsx`'s `onSendConversationStarter`
  (line ~1853) does `setHasStarterBeenSent(true)` + `chatInput.current.setValue(starter)` — no send call.
  The chip row disappears immediately on click (`hasStarterBeenSent` flips permanently true, hiding
  `conversation_starters={hasStarterBeenSent || isTheUserChattingNow ? [] : conversationStarters}`,
  lines 2359-2362) regardless of whether the pre-filled message is ever actually sent. An explicit
  `chat-send-button` click is required afterward to get an actual agent response — same decomposition
  ELITEA-2369's test already uses for the sibling `/chat/{id}` flow (click tile → assert input → click
  Send → wait for response).
- Confirmed live end-to-end this run (agent id 6732, `elitea-1736-conversation-agent` — a shared fixture
  agent; starters added+removed again to leave it clean): 2 starters via
  `agent-conversation-starter-add`/`agent-conversation-starter-input` → `agent-save-button` (`201`) →
  chips visible pre-message → click chip → `chat-message-input` pre-filled → `chat-send-button` → real,
  contextually-relevant agent response, zero console errors, zero 4xx/5xx throughout.

**Resolved/added during ELITEA-1886 implementation (2026-08-07):**
- **Testid added.** `testId="chat-conversation-starter-tile"` is now wired on
  `ChatConversationStarters.jsx`'s `<EllipsisTextWithTooltip>` call (EliteaAI/EliteaUI
  `automation/testids`, commit `afb48435`), reusing the literal already backing
  `ChatPage.CHAT_STARTER_TILE`. `AgentDetailPage` now carries the mirror-shape
  `CHAT_STARTER_TILE` constant + `get_chat_starter_tiles()` / `click_chat_starter_tile()`
  (same duplicated-field pattern the class already uses for `chat_message_input` /
  `chat_send_button` — two distinct routes, same testid literal by design, not a
  page-object violation).
- **`reasoning_effort: "none"` payload agents do NOT reliably complete an actual chat
  predict round trip** — distinct from the `#524` temperature/reasoning_effort 400,
  which is about agent *creation/save*, not *chatting*. Live-probed against the shared
  fixture agent 6732 (model: Anthropic Claude 4.5 Sonnet) vs. a disposable
  `reasoning_effort: "none"` / `model_name: gpt-5.2` agent: on the `"none"` agent,
  clicking `chat-send-button` left the composer populated with the pre-filled starter
  text and produced **no** `POST .../conversations/prompt_lib/{project}` at all (silent
  client-side no-op, zero console/network errors — nothing to catch). Switching the
  disposable agent to plain `AgentAPI.create_agent()` (which uses `_default_llm_settings()`:
  `reasoning_effort: "medium"`, `temperature: null` — the documented "matches UI default"
  shape, same one `test_agent_embedded_chat_send_message.py` already uses successfully)
  fixed it immediately. **Implementer takeaway:** the `reasoning_effort: "none"` payload
  shape (`test_agent_remove_variable.py`'s pattern) is safe ONLY for save/reload-only
  tests that never exercise a real predict; any test that sends a chat message and
  expects a response should use plain `create_agent()` instead.
- **`agent-conversation-starter-counter` renders for at most ONE field at a time** — it's
  gated on `isFocused(...)` in `ConversationStarters.jsx`, so when starter field 2 is
  focused, `conversation_starter_counter` (the LocatorDescriptor collection) has exactly
  one element in the DOM, always at `.nth(0)` — NOT `.nth(1)`, regardless of which
  starter's counter it actually belongs to. Query with `index=0` for whichever field is
  currently focused (matches the existing single-field usage pattern in
  `test_agent_character_limits.py`).

## "Share" (Copy Link) — Agent Actions overflow menu (ELITEA-1898 run, 2026-08-06/07)
- **No standalone "Copy Link" button exists** — the case-text label doesn't match the live UI. The
  three-dot `agent-actions-menu-button` overflow menu has **two separate "Share" items** (both built
  from `useCopyLinkMenu({ label: 'Share', ... })` in `CopyLinkToEntityButton.jsx`, which overrides the
  hook's own default label "Copy link" — `ApplicationControls.jsx`):
  - `share-version-menuitem` (VERSION group) — copies `.../agents/all/{agentId}/{versionId}?viewMode=owner&name=...`
    (version id as its own trailing path segment). **This is the one ELITEA-1898 needs.**
  - `share-agent-menuitem` (AGENT group) — copies `.../agents/all/{agentId}?viewMode=owner&name=...`
    (no version segment at all). Visually identical label "Share" — easy mis-click target for automation,
    use as a negative control when asserting the version segment is specifically attributable to the
    VERSION-group action.
  - Both testids derive from `DotMenu.jsx`'s `testId: item.key` mechanism (same mechanism backing
    `publish-version-menuitem`/`unpublish-version-menuitem`/`set-as-a-default-menuitem` — no new EliteaUI
    work needed for either).
- **Visual confirmation is a toast, not a tooltip/icon-change** — the menu closes immediately on click
  (`DotMenu.jsx`'s `withClose(item.onClick)`), so the icon-swap behavior `CopyLinkToEntityButton`'s
  standalone icon-button variant has is never observable through this menu-item path. Toast text: "The
  link has been copied to the clipboard." (`toast-message`/`toast-alert[data-severity="info"]`, pre-existing
  app-wide shared testids — NOT yet fields on `AgentDetailPage`, add them there, no EliteaUI work needed).
- **Copied link carries a leading `/{projectId}` segment** (`useProjectEntityLink`'s `projectPath` =
  `PROJECT_ID_URL_PREFIX + route`, e.g. `http://localhost:5173/399/agents/all/7598/7820?...`). This
  segment is NOT itself a matched app route — a catch-all `/:projectId/*` route
  (`ProtectedRoutes.jsx`) renders `<ProjectSwitcher/>`, which validates the id against the user's
  project list, switches the selected project, strips the `/{projectId}` prefix, and does a **hard
  `window.location.replace()`** reload at the stripped path. Cross-cutting (affects every
  `useProjectEntityLink`-based Share link on any entity type, not just Agents) and pre-existing —
  confirmed live, not a defect. **Automation implication:** after navigating to any copied
  Share/copy-link URL, wait for a real page-load signal (e.g. `VERSION:` combobox text), never assert
  immediately post-`goto()` — there's an extra hard-reload hop in between.
- **Route param name is `version`, not `versionId`** — despite `BLOCK_NAV_PATTERNS`' string literal
  `${RouteDefinitions.ApplicationsDetail}/:versionId` implying otherwise, the actual nested route
  registered in `ProtectedRoutes.jsx` (for any path ending `/:agentId` or `/:skillId`) is
  `path=":version"`. `VersionSelect.jsx` defensively reads `urlParams.version || urlParams.versionId`
  to cover both. Confirms navigating directly to a version-suffixed URL DOES select that specific
  version (`getVersionDetailQuery` fires off `versionFromParams` on mount) — not just cosmetic.
- **Clipboard read via Playwright MCP's `navigator.clipboard.readText()` can hang** on a permission
  prompt in this environment (observed this run, had to abort after idle timeout). Workaround used:
  monkey-patch `navigator.clipboard.writeText` via `page.evaluate()` BEFORE the click, capture the
  copied string into a `window` variable. For a real pytest fixture, prefer
  `context.grant_permissions(["clipboard-read", "clipboard-write"])` before the click instead (avoids
  the interactive-prompt hang entirely — the standard Playwright pattern).
- Filed as CLARIFICATION (case-text drift, not a defect):
  [EliteaAI/elitea-testing-public#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288)
  — sibling of [#1218](https://github.com/EliteaAI/elitea-testing-public/issues/1218) (ELITEA-2356, same
  "Copy Link" → "Share" pattern, different surface: Agent Hub modal overflow menu).
