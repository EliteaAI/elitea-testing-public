# Agents surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent detail page
(`/agents/all/{id}?viewMode=owner`) — VERSION area + Run History + LLM Model Settings dialog +
Tools section's Agent/Pipeline sub-tool version selector + nested-agent chat execution.
Also covers Agent Hub Catalog modal (`/elitea-catalog`) — agent card detail modal with like button.
Not a substitute for execution — verify a handle as you use it. One writer at a time; last
confirmed by: qa-engineer analyst, ELITEA-2358 run (2026-08-10).

## Attached Agent/Pipeline tool card — version selector (ELITEA-1951 run, 2026-08-07)
- Rendered by `EliteaUI/src/pages/Applications/Components/Tools/AgentPipelineVersionSelector.jsx`
  inside `ToolCard.jsx`, for any tool whose `tool.type === 'application'` (i.e. an attached
  sub-agent OR sub-pipeline). **Zero `data-testid` anywhere in this file** — confirmed via source
  read, not just live DOM. Testid gap: `agent-tool-version-selector-trigger-{tool_id}` (dynamic,
  mirrors `SKILL_VERSION_TRIGGER_SELECTOR`'s templated-constant pattern) on the `.version-text`
  clickable `Box`, plus `agent-tool-version-selector-menu-{tool_id}` / `agent-tool-version-option-{tool_id}-{version_id}`
  on the MUI `Menu`/`MenuItem`s.
- Live behavior confirmed: trigger text = the tool's currently-bound version name (e.g. `"base"`
  for a fresh sub-agent with only one version); clicking it opens a `Menu` with a "Versions"
  header + one `MenuItem` per version, checkmark on the selected one. Card's own testid
  (`agent-toolkit-card`) is shared unchanged with Toolkit/MCP cards — confirmed the SAME
  component renders Agent-type sub-tools too, `.filter(has_text=sub_agent_name)` finds it.
- Attach endpoint for Agent/Pipeline-type tools is **`PATCH
  .../elitea_core/application_relation/prompt_lib/{project}/{app_id}/{version_id}` → 201**,
  DISTINCT from Toolkit/MCP's `PATCH .../tool/prompt_lib/{project}/{tool_id}`. Version-switch
  (clicking a different `MenuItem`) uses `useUpdateApplicationRelationMutation` — same endpoint,
  atomic single-call switch (source comment cites issue #5716: avoids a delete-then-add race that
  could orphan the tool on a rejected switch).

## Build with AI (GenerateAgentModal) — modal-open + static-controls confirmation (ELITEA-1905 run, 2026-08-08)
- Navigating to `/agents/create?viewMode=owner` and clicking
  `generate-agent-open-button` (in the General accordion section header,
  right after the Tags field) opens `dialog [active]` with heading "Build
  with AI". Confirmed live, all pre-existing testids (no `add-data-testid`
  needed): `generate-agent-prompt-input` (textarea, accessible-named
  "Describe your agent's goal, key tasks, and preferred tone or behavior."),
  `generate-agent-submit-button` (label **"Generate Draft"**, NOT "Generate
  agent" — rendered `[disabled]` by default, `disabled={!description.trim()}`
  in `GenerateEntityModal.jsx:213`, enables once the prompt is non-empty),
  `generate-agent-cancel-button`, `generate-agent-close-button` (X icon).
  Zero console errors on open. No network call fires until Generate is
  clicked with a non-empty prompt (`generate_application_draft` endpoint).
- **Button-label mismatch is a recurring case-text drift class** for this
  modal family — TMS case text tends to say "Generate agent"/"Generate";
  the live label is always "Generate Draft" (shared `GenerateEntityModal.jsx`
  across Agent/Skill Build-with-AI). Check case wording against the live
  label before asserting `inner_text()` equality.

## Nested-agent invocation in chat — chip vs. accordion representation (ELITEA-1951 run, 2026-08-07)
- When a parent agent invokes an attached sub-agent as a tool, the response's
  `chat-answer-thought-accordion` (existing testid, ELITEA-2211..2215 batch) shows the
  invocation as EITHER a flat `chat-answer-tool-chip` reading the sub-agent's bare name, OR a
  nested expandable accordion (an `<h3>` whose text is the sub-agent's exact name) — confirmed
  live that **which shape renders depends on whether the invoked sub-agent itself made a further
  tool call**: no further call → flat chip; sub-agent called its own tool → nested accordion.
  Don't hardcode either shape as fixed — check for the accordion first, fall back to the chip.
- Inside the nested accordion (once expanded — starts collapsed, `aria-expanded="false"`):
  `chat-answer-model-chip` → `chat-answer-tool-chip` → `chat-answer-model-chip`, i.e. the
  sub-agent's own reasoning-then-tool-call-then-completion chain, all pre-existing testids
  (ELITEA-2211..2215 batch). A NESTED agent's own tool-call chip text carries a suffix the
  top-level shape doesn't: `"{toolkit}: {tool} ({originating_agent_name})"` vs. top-level's
  `"{toolkit}: {tool}"` — `ActionView.jsx`'s title-builder appends the originating agent's name
  in parens when the call happened inside a nested agent context. Use the suffix to
  disambiguate a nested tool call from a top-level one, not DOM depth alone (DOM depth is
  reliable too, but the text shape is the more direct, spec-legible assertion).
- **Message-wording is determinism-critical for BOTH invocation and the sub-agent's own tool
  use** — same finding class as ELITEA-2211 vs. ELITEA-2215 (chat-interface surface). A vague
  parent-facing message ("Please help me with this task.") produced zero invocation at all; a
  message naming the sub-agent but not its tool's required parameter invoked the sub-agent but
  the sub-agent then silently skipped its own configured MCP tool and answered generically; only
  a message naming the sub-agent, its tool, AND the tool's required parameter reliably produced
  the full chain, repeatably. This is normal LLM behavior given ambiguous input — NOT the same
  defect as #1127 (chat-interface's tool-call-intent-leaks-as-raw-text bug), which was never
  observed here (every non-invoking response was a well-formed, normal conversational reply).
  Automation exercising a nested-agent-invokes-tool flow should always use a fully-specified
  message, never rely on the agent inferring missing parameters.
- Round-trip time for a 2-level nested tool-call chain (parent → sub-agent → sub-agent's MCP
  tool → parent relays) was observed up to ~40s ("Thought for 40 secs") — budget a 60s+ final-
  answer wait for this shape, more than a flat single-tool-call flow needs.
- Fixture agents left in project `399` after this run (reusable, `autotest_`-prefixed):
  `autotest_nested_mcp_subagent` (id `7827`, has `autotest_mcp_run_tool` MCP attached,
  instructed to always call `read_wiki_structure`) and `autotest_nested_mcp_parentagent`
  (id `7828`, instructed to always invoke the sub-agent). Both created via the UI form —
  `#524`'s temperature+reasoning_effort 400 did NOT fire on this path.

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

## Build with AI (GenerateAgentModal) — review-form Name field, 32-char validation (ELITEA-1913 run, 2026-08-08)
- `generate-agent-review-name-input` (`GenerateAgentReviewForm.jsx`, existing `LocatorDescriptor`) enforces
  `MAX_NAME_LENGTH=32` via `validateAgentDraft()` (`agentDraftValidation.helpers.js`) — `helperText`/`error` on the
  field ("Name must be 32 characters or less") + `generate-agent-approve-button` disabled while invalid; both clear
  at exactly 32 chars. `aria-invalid` on the EXISTING `review_name_input` locator is a testid-free, compliant way to
  read the invalid state — no new handle needed for that half.
- **`Input.InputBase` (`EliteaUI/src/[fsd]/shared/ui/input/InputBase.jsx`) silently drops any `slotProps` the
  CALLER passes** — confirmed via source read, not guesswork. It destructures only `inputProps` from its own props
  (line 85), builds its OWN internal `slotProps` object (line 260-277, `htmlInput: inputProps` etc.), and spreads
  that AFTER `{...leftProps}` on `<MuiTextField>` (line 257 vs 260) — JSX later-prop-wins means any `slotProps` the
  caller passed (landing in `leftProps` since it's not explicitly destructured) is fully overwritten. This is why
  `GenerateAgentReviewForm.jsx`'s `slotProps={{ htmlInput: { maxLength: MAX_NAME_LENGTH } }}` on the Name field has
  ZERO effect — live-confirmed (`el.maxLength === -1`, no native attribute at all; 40 real keystrokes all land in
  the DOM value, no truncation). **Any `Input.InputBase` caller relying on `slotProps` passthrough is affected, not
  just this field** — a broader latent gap, out of scope to fix here (doesn't affect ELITEA-1913's own Pass
  criteria — the JS-validation path is independent and correct) but worth knowing before assuming `slotProps` works
  through this wrapper. The FIX pattern for adding testids to slots THIS way: a NEW prop `InputBase` itself
  explicitly destructures (matching its existing `tooltipTestId`/`tooltipContentTestId` pattern) threaded into its
  own internal `slotProps` construction — never a caller-passed raw `slotProps`.
- **Reconciles, doesn't contradict, ELITEA-1993's Skill-form finding** (`daily/2026-08-02.md`): the SKILL review
  form's Name field (`GenerateSkillReviewForm.jsx`) calls MUI's raw `<TextField slotProps={{htmlInput:{maxLength}}}>`
  DIRECTLY (no `Input.InputBase` wrapper) — so its `maxLength` DOES reach the DOM and DOES truncate natively (both
  `.fill()` and keystrokes, confirmed that run). Two different components, two different outcomes — not a
  contradiction. Skill form's error-text testid precedent: `generate-skill-review-name-helper-text` (via
  `slotProps.formHelperText`, EliteaUI commit `8e78723b`) — naming convention this AFS's `needs-adding` recommendation
  for the Agent form mirrors (`generate-agent-review-name-helper-text`).

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

## Create Agent form (`/agents/create`, ELITEA-1900 run, 2026-08-07)
- `agent-name-input` / `agent-description-input` / `agent-save-button` all pre-existing on **main**
  AND `automation/testids` — confirmed via `git grep` this run, no testid work needed for this area.
- Name field enforces `MAX_NAME_LENGTH = 32` (`EliteaUI/src/common/constants.js:66`) via the native
  HTML `maxlength` attribute on `agent-name-input` (`CreateAgentForm.jsx:135`) — purely client-side,
  synchronous, no network round-trip. Confirmed both via `fill()` (bulk truncation) and real
  keystroke-by-keystroke typing past the boundary (extra chars silently rejected, value stays fixed).
  **No length-based validation error exists for Name at all** — only the `required`-empty case sets
  `formik.errors.name`; `aria-invalid` stays `"false"` all the way up to and at the 32-char limit.
- Name field's character counter (`Text.CharacterCounter`, `CreateAgentForm.jsx:139-146`) shows
  "0 characters left" at the boundary but has **no `data-testid`** wired at this call site — the
  shared `CharacterCounter.jsx` component DOES support a `dataTestId` prop
  (`EliteaUI/src/[fsd]/shared/ui/text/CharacterCounter.jsx:12,20`), so it's a threading gap, not a
  missing-capability gap. Not needed for length/error assertions (use `aria-invalid` on the input
  itself instead) — only add a testid here if a future case needs to assert the counter text directly.
- Save button gating is independent per-field: disabled until BOTH Name and Description are non-empty
  (both `required`); Name being at-limit (32/32) does not itself disable Save.

## "Build with AI" open button — placement + RBAC gating (ELITEA-1903 run, 2026-08-08)
- `generate-agent-open-button` (existing `LocatorDescriptor` field, `generate_agent_modal_page.py`)
  is **not** inside a "creation tab bar" despite the case text — live-confirmed it renders as a
  pill button pinned to the top-right of the **General accordion section's header row** (same row
  as the "GENERAL" chevron/title), separate from the top page-level `tablist` that holds the single
  "New Agent" tab. Case-text location drift, not a product defect — the button itself is genuinely
  present/visible. See `EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/GenerateAgentButton.jsx`.
- **The button's visibility IS permission-gated, confirmed at the source**:
  `GenerateEntityButton.jsx` does `if (!checkPermission(permission)) return null;` — for the agent
  variant `permission={PERMISSIONS.applications.update}` = `'models.applications.application.update'`
  (`common/constants.js`). No permission ⇒ the button is absent from the DOM entirely (not just
  disabled). `useCheckPermission` reads `state.user.permissions` (or `publicPermissions` for the
  public project), populated from `GET /api/v2/auth/permissions/prompt_lib/{project_id}` on
  project switch/login. This is the mechanism ELITEA-1903 is actually testing.
- **`${TEST_USER}` is admin-equivalent in every project checked** — live-confirmed
  `models.applications.application.update` present in the permissions response for BOTH project
  `399` (Private, owner) and `400` ("UI Testing" team project) — the latter also carries
  `configuration.roles.roles.create/edit/delete` + `configuration.users.users.create/edit/delete`,
  i.e. TEST_USER is project-admin there too, not merely a member. No project this account belongs
  to exercises a non-admin role.
- **No editor-role login path exists locally** — `.env.test` defines only `TEST_USER_EMAIL/PASSWORD`
  (§ Roles & sample users has no editor credential key). Settings → Users on project 400 DOES list
  an `editor`-role row (`elitea-batch-edit-test2-45c8fb8d@example.com`) and a `viewer`-role row
  (`elitea-batch-edit-test2-70fda701@example.com`), but both are leftover pending-invite fixtures
  from an unrelated prior batch-edit-user-role test (`Last login: "-"`, never accepted) — no known
  password, not usable as a live login. Self-downgrading TEST_USER's own role via the "Edit user
  role" action was considered and rejected: project 400 is shared test data another merged suite
  relies on for a fixed 2-user/role shape (`admin_users_page.py` docstring, ELITEA-2292), and an
  editor role may lack `configuration.users.users.edit` needed to self-restore back to admin —
  no safe, verified rollback. **Testability gap, not a product question**: automating the editor
  half needs either a dedicated `EDITOR_TEST_USER_EMAIL`/`PASSWORD` fixture (real Keycloak account,
  fixed editor role in a stable project) or an accepted API-level permissions-endpoint proxy.

## Build with AI — plain-approve (no suggested resources) network contract (ELITEA-1914 run, 2026-08-08)
- A draft generated from a plain, non-resource-implying prompt renders **zero** "Suggested
  {Category}:" sections (`generate-agent-resource-section-*` never appears), and clicking
  **"Create Agent"** fires **only** `POST /api/v2/elitea_core/applications/prompt_lib/{project}`
  → `201` — no `PATCH .../tool/...`, `PATCH .../application_relation/...`, or `GET`/`PATCH
  .../skill/...` calls fire at all. **`GenerateAgentModalPage.click_approve_and_wait_for_creation()`
  and `click_approve_and_wait_for_skill_creation()` (`generate_agent_modal_page.py:262-342`) will
  hang/timeout on a plain-approve draft** — both enter all their `expect_response` waits in one
  `with` block, unconditionally. A plain-approve test needs a narrower helper that waits only on
  the base create POST.
- The UI auto-navigates to `/agents/all/{id}?destTab=configuration&name=...&viewMode=owner`
  immediately on the `201` — always carries `viewMode=owner` and the created name, confirmed live.
- **Gotcha (filed as elitea-testing-public#1316, sibling of #638):** a bare hard-navigation to
  `/agents/all/{id}` with **no** `?viewMode=owner` query param (i.e. NOT the app's own
  auto-navigation — a fresh page load / typed URL) can silently render a **different, unrelated**
  agent's data when the numeric id collides between the private (`application`) and public
  (`public_application`) id spaces (`useViewMode.js`'s fallback can resolve to `Public` on a hard
  reload before the real project is restored). Never hard-navigate to a bare agent detail URL in a
  test — always drive there via an in-app click (or include `?viewMode=owner` explicitly) if a
  test genuinely needs a direct deep link.
- `AgentsListPage.agent_exists_in_list(name)` (`agents_list_page.py:263-279`, pre-existing) is the
  handle for asserting a newly-created agent appears in `/agents/all` — no Build-with-AI test used
  it before ELITEA-1914.

## Build with AI — edited review-form values persist into the created agent (ELITEA-1912 run, 2026-08-08)
- Editing all 5 review-form fields (Name/Description/Instructions/Welcome
  Message/first Chat-starter, via the existing `.click()`+`.fill()` on their
  testid-only locators) and THEN clicking "Create Agent" produces a created
  agent whose detail-page fields carry the EDITED values, not the original
  generated-draft values — live-confirmed end-to-end (real `applications`
  POST → 201, no mocking of the create step). No functional defect.
- The auto-navigation URL's `name` query param already reflects the edited
  name (`?...&name=<edited>&viewMode=owner`), an early live signal usable
  before the detail page even finishes mounting.
- Same network contract as ELITEA-1914's plain-approve finding above: only
  `generate_application_draft` + `applications` POSTs fire, no relation
  calls — editing the fields first doesn't change which calls fire.
- Welcome Message and the first Chat-starter both have a SECOND,
  independent confirmation channel beyond the detail-page form field: the
  embedded chat panel on the created agent's own page renders the edited
  Welcome Message as its greeting text, and the edited starter as a
  clickable starter tile — useful as an extra assertion if a test wants
  UI-rendered confirmation, not just `input_value()`.
- `AgentDetailPage`'s "Delete agent" flow needs the typed-name confirm
  dialog: `agent-actions-menu-button` → `delete-agent-menuitem` → type the
  exact agent name into `delete-confirm-name-input` (enables
  `delete-confirm-button`, disabled until the typed name matches) →
  confirm. Redirects to `/agents/create` on success.

## Build with AI — Cancel click from the prompt step (ELITEA-1917 run, 2026-08-08)
- **Don't confuse `generate-agent-open-button` with `agent-form-icon-button`.**
  Both sit near the "General" accordion's top area but are unrelated: the
  Magic Wand ("Build with AI") trigger is the accordion header's
  `summaryAction` (`CreateAgentForm.jsx:106`, right of the "General" title,
  same row as the chevron); `agent-form-icon-button` is the agent
  avatar/icon-picker sitting directly beside the Name field
  (`CreateAgentForm.jsx:111`). Clicking the icon-picker produces no modal —
  confirmed live this run after an initial mis-click on it did nothing.
- Clicking `generate-agent-cancel-button` (footer "Cancel", input step)
  closes the modal **immediately, no confirmation/"discard changes?"
  interstitial** — the `generate-agent-modal` dialog is fully removed from
  the DOM (not merely hidden), even with a non-empty, never-submitted
  prompt already typed. Confirmed live: zero network calls to either
  `generate_application_draft` or `applications/prompt_lib` (POST) fire
  anywhere in an open→type→cancel sequence, and the outer New Agent form's
  own Name/Description fields (`agent-name-input`/`agent-description-input`)
  are untouched by anything typed into the modal's prompt textarea — the two
  are entirely separate inputs, no bleed-through either direction. This was
  the suite's first `.click()` on `cancel_button` — ELITEA-1905 had only
  ever asserted `.is_visible()` on it.

## Build with AI (GenerateAgentModal) — REVIEW step has NO "Cancel" button (ELITEA-1918 run, 2026-08-08)
- `GenerateEntityModal.jsx`'s `renderActions()` renders a genuinely different
  button set per step — NOT a fixed Cancel+Generate/Approve pair. INPUT step:
  "Cancel" (`generate-agent-cancel-button`) + "Generate Draft"
  (ELITEA-1917's territory). **REVIEW step: only "Back to prompt"
  (`generate-agent-back-button`, ELITEA-1919's separate case) + "Create Agent"
  (`generate-agent-approve-button`) — no Cancel button exists here at all.**
  Confirmed both by source (lines 173-198 vs 201-224) and live accessibility
  snapshot of the open review-step dialog (footer = exactly those two
  buttons).
- The only review-step control that closes the modal without creating an
  agent is the modal header's **X ("Close") icon**
  (`generate-agent-close-button`, `Modal.BaseModal`'s `closeButtonTestId`) —
  confirmed via source (`BaseModal.jsx:154`, `onClick={onClose}`) that it
  calls the EXACT SAME `handleClose()` the INPUT-step Cancel button calls:
  same abort/reset/close semantics, no confirmation interstitial, even with
  a fully-populated draft (5 fields + starters) about to be discarded.
  `close_button` had been `.click()`ed once before (ELITEA-1913, end-of-test
  cleanup only, zero assertions) — ELITEA-1918 is the first test to actually
  assert what it does.
- Filed as CLARIFICATION (case-text drift — case says "Click Cancel", no
  such control exists on this step):
  [EliteaAI/elitea-testing-public#1318](https://github.com/EliteaAI/elitea-testing-public/issues/1318).
- Live-confirmed this run: a real (unmocked) `generate_application_draft`
  call reliably produces a usable draft within existing timeout constants
  (no need to mock for this shape of case) — generated "Billing Support
  Agent" from a billing-support prompt, 4 chat starters, all real AI output.

## Build with AI — Suggested Resources have NO client-side display cap (ELITEA-1910 run, 2026-08-08)
- **`ResourceSuggestions.jsx` renders every item in its `items` array unconditionally**
  (`items.map(...)`, no `.slice()`/count guard) — confirmed by source grep across
  `ResourceSuggestions.jsx`, `GenerateAgentReviewForm.jsx`, and `GenerateAgentModal.jsx` (only
  unrelated `MAX_*` constants exist, for name/description/welcome-message/conversation-starter
  fields). **Live-reproduced**: mocking `generate_application_draft` with 7 `suggested_skills`
  items rendered all 7 `[data-testid^="generate-agent-resource-item-skill-"]` cards, not 5. Filed
  as `EliteaAI/elitea-testing-public#1317` (frontend gap; backend response schema is undocumented
  in `/shared/openapi/?all=true`, so whether the backend itself ever sends >5 is unverified from
  this repo — no prior live exploration, ELITEA-1907/1911 included, ever observed >2 suggestions
  per category). Applies to **all five** suggestion categories (toolkit/mcp/pipeline/agent/skill)
  — one shared component, one root cause.
- **Real suggestion counts cannot be reliably driven past ~2 via live fixtures** (LLM
  relevance-matching, per ELITEA-1907/1911's own precondition audits) — testing any cap/count
  boundary on this surface needs the `mock_generate_success()` route-mocking technique
  (`GenerateEntityModalPageBase`, already sanctioned for ELITEA-1907/1915), not live fixture
  creation. Don't burn fixture-creation effort trying to coax >5 real Skills/Toolkits into
  suggestion relevance — it's nondeterministic and the mock answers deterministically in one call.

## Build with AI — "Back to prompt" (`back_button`) confirmed: pure client-side state reset, prompt preserved (ELITEA-1919 run, 2026-08-08)
- **`generate-agent-back-button` had never been `.click()`ed anywhere in the suite before this
  run** — only `.is_visible()`-checked (`TestAgentBuildWithAICreationFailureRecovery`, asserting
  the review step's action buttons survive a creation failure). ELITEA-1918's AFS explicitly
  disclaimed covering it. Confirms genuinely unexercised territory.
- **Source-level mechanism** (`GenerateEntityModal.jsx`'s `handleBack()`, lines 85-89): resets
  `step` to `STEPS.INPUT` and `draftData` to `null`, and calls `resetGenerate()` — but **never**
  calls `setDescription('')`. The sibling `handleClose()` (INPUT-step Cancel + review-step X icon,
  per ELITEA-1917/1918) DOES clear `description`. This asymmetry is exactly why "Back to prompt"
  preserves the typed text while Cancel/Close discard it — a deliberate design choice, confirmed
  by reading both functions side by side, not inferred from behavior alone.
- **Live-confirmed, full round trip**: opened modal → typed a prompt → real (unmocked)
  `generate_application_draft` call → reached review step (draft "Ticket Summary Verifier") →
  clicked `back_button` → modal returned to the INPUT step with the EXACT original prompt text
  still in `generate-agent-prompt-input` (character-for-character), `back_button`/
  `approve_button`/all review-form field testids (`generate-agent-review-name-input` etc.) fully
  removed from the DOM (not merely hidden — `renderContent()` re-renders a different branch).
- **Zero network side effect from the Back click itself**: `browser_network_requests` filtered to
  `generate_application_draft`/`applications/prompt_lib` showed the identical 1-vs-0 split before
  and after clicking Back (the 1 being Step 1's own Generate) — `handleBack()` is purely
  client-side, confirmed both by source and by network capture.
- **Console**: only the pre-existing, documented `disableUnderline` baseline warning
  (ELITEA-1906/1913/1916/1918) — unchanged by the Back click, no new errors.

## Agent Hub Catalog modal — like button (ELITEA-2358 run, 2026-08-10)
- **Where**: Catalog view (`/elitea-catalog`) → click any agent card → modal overlay opens with agent details + like button
- **Like button location**: modal header, right side, next to overflow menu and close button
- **Testids**: 
  - `catalog-agent-modal-like-button` (pre-existing per ELITEA-2356 AFS analysis) on the like button element
  - `data-liked="true"` or `data-liked="false"` attribute on the same button (state attribute, follows same pattern as ELITEA-2354 card-list like button)
- **Behavior confirmed live (ELITEA-2358)**: 
  - Button text displays the current like count (e.g., "8")
  - Clicking the button toggles the liked state and updates the count immediately in the modal header
  - Button shows `data-liked="true"` when agent is liked by the current user, `data-liked="false"` when not liked
  - Like count state is persisted across modal close/reopen — closing the modal and reopening shows the same updated count
  - Like count also updates on the agent card in the Catalog grid list view (not just in the modal)
- **Known issue**: Redux console warning on like click — "non-serializable value was detected in an action, in the path: `payload.updateFn`" (appears to be a Redux Toolkit serialization enforcement warning, but the UI state updates correctly despite the warning). Does not block the feature — automation should proceed with normal assertions.
- **Pre-existing from ELITEA-2356 analysis**: modal structure, agent name, description, CHAT STARTERS section, Welcome Message section, Start Chat button — all pre-existing handles, see ELITEA-2356 AFS § Concrete Handles for full reference.

## Agents list empty state — search with no matches (ELITEA-2367 run, 2026-08-10)
- **Where**: Agents list page `/agents/all?viewMode=owner` (card-list view, right panel with search input)
- **Search input**: `textbox "search"` with `placeholder="Let's find something amazing!"`; input element itself has no `data-testid` (TBD add-data-testid candidate)
- **Search behavior**: live/reactive, debounced ~300ms (per `useDebounceValue(query, 300)` in `AgentsTab.jsx`). No Enter key needed, but implementer should wait for debounce + network latency (recommend 500–1000ms total) before asserting empty state
- **Autocomplete/suggestion UI**: Typing into the search opens a tooltip/popover with list items including "No Agents Match" and "No Tags Match" options (observed in live snapshot) — these are suggestions/indicators, not action buttons; the main content area filtering happens independently
- **Empty state location**: discovered to render in the main card-grid area (left/center panel), NOT in the search input or right panel
- **Empty state message**: TBD exact text — case text says "No agents found" + helper "Try adjusting your search terms", but live code (`PrivateAgentsList.jsx`) renders `"Nothing found. Create yours now!"` for search-no-match cases (lines 56–60). Implementer should capture actual rendered text and verify against case intent
- **Clear/Reset mechanism**: two clickable elements observed next to the search input (`[ref=f11e603]` and `[ref=f11e606]`), likely clear/reset buttons (exact purpose TBD); clicking clears the search and agents should reappear
- **Right panel during empty state**: Tags section remains visible, showing "No tags to display." and the footer count "Agents: 19" (or current total) — confirms the right panel is not hidden during empty state, only the main content area filters
- **API call for empty results**: likely `GET /api/v2/elitea_core/applications/prompt_lib/{projectId}?query={searchTerm}&...` returning `{ total: 0, rows: [] }` or similar; implementer can use network capture to verify the backend's response structure
- **Testid gaps (needs-adding)**: Search input itself has no `data-testid` (TBD); empty-state message container/heading may need a testid for reliable querying depending on implementation
- **Known issue**: Category/tag filter variant mentioned in case text ("Apply a category filter that has no agents") is NOT yet explored — the Tags section on the right is currently non-interactive (shows "No tags to display."), so it's unclear whether tag filtering exists on this page or only on the Catalog. Filed as clarification in ELITEA-2367 AFS.
