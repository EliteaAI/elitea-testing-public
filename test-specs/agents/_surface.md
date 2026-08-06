# Agents surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent detail page
(`/agents/all/{id}?viewMode=owner`) — VERSION area + Run History + LLM Model Settings dialog.
Not a substitute for execution — verify a handle as you use it. One writer at a time; last
confirmed by: qa-engineer analyst, ELITEA-1880 run.

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
- **Confirmed defect (filed EliteaAI/elitea-testing-public#1093, MINOR, doesn't block ELITEA-1877):**
  no UI way to close/exit Run History once opened. `RunHistoryContainer` accepts an `onClose` prop
  (`ConfigurationTab.jsx` passes `handleCloseHistory`) but never renders anything that calls it —
  `header`/`iconClose` styles are defined but never applied in the JSX. The button that opened History
  (`pipeline-history-tab`) unmounts along with the rest of `ConfigurationRightContent`, so re-clicking
  it is impossible without navigating away. Only exits: "Restore chat" on a row's overflow menu, or
  leaving the page.
- Test-data trick to get 2 distinct run-history entries for one agent without 2 agents/sessions: send a
  message (conversation A persists server-side) → click **Clear chat** (`chat_clear_button` —
  `ChatBox.jsx` `onClickClearChat`, `isAgentsPage` branch starts a fresh **local, unsaved**
  `isNew: true` conversation, it does NOT touch conversation A) → send a second message (persists as
  conversation B). Both now list as separate Run History rows.
- Endpoints: list = `GET /elitea_core/conversations/prompt_lib/{projectId}?source=agent&entity_name=application&entity_meta_id={agentId}&...`;
  detail (on row click) = `GET /elitea_core/conversation/prompt_lib/{projectId}/{conversationId}`.

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
