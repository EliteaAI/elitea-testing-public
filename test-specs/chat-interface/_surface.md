# Chat Interface — exploration digest

Seeded 2026-07-24 (GAP-018, first case in this batch to touch the chat voice
mini-player sub-surface in depth). A handle *cache*, not a substitute for
execution — verify each handle live as you use it.

## Core chat handles (confirmed live)

- **New-conversation trigger**: sidebar `[data-testid="sidebar-create-button"]`
  (labelled "Chat" in the sidebar) — existing `ChatPage.click_create_new_conversation()`.
- **Message input**: `[data-testid="chat-message-input"]` (a `<textarea>`) —
  existing `ChatPage` send-message flow. Enter submits.
- **Message list items**: `[data-testid="chat-message-item"]` (one per user OR
  AI message, alternating) — existing `ChatPage.messages_container`. A
  conversation with N prompts has 2N message items (user + AI pairs); AI-only
  elements (e.g. `chat-read-out-button`) render inside a subset of these, so
  don't assume `messages_container.nth(i)` maps 1:1 to "AI answer #i".
- **Conversation URL**: `/chat/{conversation_id}?name=...` — id extractable via
  regex `r"/chat/(\d+)"` on `page.url` (existing `capture_conversation_id()`
  helper pattern in `test_voice_configuration.py`).

## Voice / TTS mini-player sub-surface (GAP-018 — full findings)

- **Source**: `EliteaUI/src/[fsd]/features/chat/ui/voice-control-button/VoiceControlButton.jsx`,
  `.../voice-mini-player/VoiceMiniPlayer.jsx`,
  `.../lib/hooks/useReadAloud.hooks.js` + `useTextToSpeech.hooks.js`.
  Read-out trigger lives in `.../chat-box/ApplicationAnswer.jsx`.
- **State machine (important — do not assume "click Read-out = playback starts"):**
  1. Click `chat-read-out-button` → **stages** the answer's text and reveals
     `chat-voice-mini-player` in the **idle/Play** state. Audio has NOT started.
  2. Click `chat-voice-play-stop-button` (idle) → `onPlay()` → `speak()` →
     `isPlaying` becomes `true`: icon flips to Stop (SVG path
     `M12 4.72727V11.2727...`, from `stop_record.svg`), tooltip "Stop speaking",
     `chat-voice-settings-button` becomes disabled, and **every**
     `chat-read-out-button` on the page (not just other messages') becomes
     disabled (`!!speakingMessageId` in `ApplicationAnswer.jsx`, unconditional —
     no `messageId !== speakingMessageId` guard).
  3. Click `chat-voice-play-stop-button` (Stop) → `isPlaying` false → the
     `useReadAloud` cleanup effect **unmounts** `chat-voice-mini-player`
     entirely (not a visual reset to Play) and clears `speakingMessageId`,
     re-enabling every read-out button + the settings button (which is gone
     along with the mini-player).
  4. Playback also ends naturally on its own once the TTS audio finishes —
     same cleanup effect fires. **A short one-sentence answer can finish in
     under ~1 second** — use a longer answer (6+ sentences) if a test needs a
     reliable window to assert the Stop state, or wait on the DOM condition
     itself rather than a fixed poll/sleep.
- **Icon disambiguation** (tooltips are timing-fragile — MUI only renders
  tooltip text in the DOM while actually hover-shown): the two SVG `<path d>`
  values are stable and cheap to compare —
  Play = `M13 8C13.0003 8.11753...` (`play.svg`),
  Stop = `M12 4.72727V11.2727...` (`stop_record.svg`).
- **Testids** (all four already on `main`, `EliteaAI/EliteaUI@a3f9b260`, fresh-fetched 2026-07-24):
  `chat-read-out-button` (per-AI-answer, N instances coexist),
  `chat-voice-mini-player` (single container, mounts/unmounts — not just hidden),
  `chat-voice-play-stop-button`, `chat-voice-settings-button`.
- **Existing page-object coverage** (`automation/pages/chat_page.py`):
  `click_read_out()`, `is_voice_mini_player_visible()`, `wait_for_tts_controls()`,
  `open_voice_settings_from_tts()`, `trigger_tts_and_open_settings()`,
  `is_tts_playing()` (misnomer — actually just checks the play/stop button is
  *present*, not that `isPlaying` is true). **Gap**: no existing method clicks
  `chat-voice-play-stop-button` itself, and no method reads its
  Play-vs-Stop icon state or any button's `disabled` state — see
  `l3_voice-mini-player-play-stop-toggle-and-disabled-controls_GAP-018.md`
  § Automation Hints for the exact methods to add.
- **Existing test coverage** (`automation/tests/ui/voice/test_voice_configuration.py`,
  merged to `automation/base`): TC1–TC5 cover the Voice Settings **dialog**
  (voice/speed/volume selection, Apply/Cancel, Personalization↔Chat sync,
  mini-player-absent-by-default) — none of them click or inspect the
  play/stop toggle's own state or any disabled-state assertion. Different
  observable, not overlapping — confirmed by full-file read, 2026-07-24.

## Folders + conversation-item reuse (ELITEA-2098)

- **`ConversationItem.jsx` is the SAME component whether rendered under a date-group
  (`DateGroup.jsx`, e.g. "Today") or inside a folder accordion (`FolderAccordion.jsx`)** — the
  `chat-conversation-item-{id}` testid and its `data-active` state attribute (from ELITEA-2114) work
  identically in both contexts, confirmed live. No folder-aware variant of `CONVERSATION_ITEM` /
  `is_conversation_active()` is needed — just scope the `.locator()` chain off
  `chat.get_folder_item(folder_id)` instead of `chat.get_conversation_group_header(group)`.
- **A folder auto-renders EXPANDED (`data-expanded="true"`) whenever it contains the conversation
  the current URL points at** — this is re-derived on every navigation/reload, not a one-time
  default. A test that needs a genuine collapsed→expanded transition for its own "click to expand"
  step must force-collapse first (click the scoped `chat-folder-icon` — confirmed to toggle
  reliably in both directions) rather than assume the folder starts collapsed.
- **Click-target risk for `expand_folder()`/`get_folder_item(folder_id).click()` on a
  EXPANDED + NON-EMPTY folder**: the testid sits on the whole outer accordion (header + body, per
  the ELITEA-2132 design). Collapsed, or expanded-but-empty (ELITEA-2132's only tested shape), a
  center-click safely lands on the header. Expanded AND non-empty (this case's shape), the
  bounding box spans the conversation list too — a blind center-click risks landing on a
  conversation row instead of the header. Untested in the suite so far (no existing test does this);
  scope to `chat-folder-icon` instead when a future test needs to COLLAPSE a non-empty, already
  expanded folder.
- **Moving a conversation into a folder via a direct API `PUT`** (`/elitea_core/conversation/
  prompt_lib/{project_id}/{id}` body `{"folder_id": <id>}`, the SAME endpoint the app's own
  `useMoveToFolderConversation.hooks.js` calls via the `conversationEdit` RTK mutation) is safe —
  it's a metadata edit, not a message send, so ELITEA-2095's defect #691 (first-message-to-
  zero-message-conversation) does not apply. **Requires a `page.reload()` afterward** — the app's
  Redux/RTK state doesn't reactively pick up a side-channel API mutation.
- **API inconsistency (not a defect)**: `ConversationAPI.get_conversation(id)` (the singular
  single-conversation endpoint) returns `folder_id: null` even for a conversation genuinely inside a
  folder; the folder-list endpoint's nested `conversations[].folder_id` is correct. Use the latter
  if a future case needs to verify folder membership via API.
- **Doc-drift (not a product defect)**: `automation/CLAUDE.md`'s API-quirks table claims conversation
  delete uses a PLURAL path; the real, merged `ConversationAPI.delete_conversation()` uses SINGULAR
  (confirmed live: plural 404s, singular succeeds `204`). Trust the client code, not that table row.

## Expanded PARTICIPANTS panel (distinct from the collapsed badge's popper — don't confuse the two)

- **Two entirely different UI surfaces render a "Users" list, and only one had a testid'd avatar
  before ELITEA-2098:**
  1. **Collapsed badge → click → small popper** (`chat-participants-badge-users` →
     `chat-participants-badge-button` → `chat-participants-popper`). Renders via
     `UsersParticipantDropdown/UserMenu.jsx`, whose own `<UserAvatar>` call carries **NO testid at
     all** (confirmed live — genuine, still-open gap, not touched by ELITEA-2098 since that case
     didn't need this surface).
  2. **The real "Participants" panel** (title "Participants", collapse/expand toggle with
     `DoubleLeftIcon`/`DoubleRightIcon`), which switches between `CollapsedPerticapantsList` (icon
     rail) and `ExpandedParticipantsList` (full names — this is where `UserParticipantItem.jsx`'s
     `chat-participants-users-avatar` testid, added back in ELITEA-2095, actually lives). Before
     ELITEA-2098, the ONLY way to reach this expanded state was `chat_page.py`'s legacy `expand_
     participants_panel()`/`is_participants_panel_expanded()` — raw `get_by_text("Participants")` +
     JS-evaluate button-hunting (tracked tech debt, still present, not removed by this pass).
- **ELITEA-2098 added 2 real testids** closing that gap: `chat-participants-panel` (container,
  `data-expanded` state attribute) + `chat-participants-panel-toggle-button` (the collapse/expand
  `IconButton` — one stable testid regardless of which chevron icon renders, per the
  testid=identity/icon-choice=cosmetic-state ruling). `EliteaAI/EliteaUI@d1b89d8a` on
  `automation/testids`, confirmed live via HMR both directions.
- **Project choice is load-bearing for BOTH participants surfaces**: `showUsersSection =
  !isPrivateProject` in `CollapsedPerticapantsList.jsx` omits the whole Users section for the
  account's own default Private project (`399`). Use the Team project (`471`, "Elitea Testing
  Team") for any case that needs a real participant to render — same precondition ELITEA-2095/2094
  already established, re-confirmed live by ELITEA-2098.

## File attachments, drag-and-drop, and model-selector checkmark (ELITEA-2091 — full findings)

Extended 2026-07-24. The "+" menu's **"Attach Files"** row is NOT a `role="menuitem"` `<li>`
like its six siblings (Modules/Agents/Pipelines/Toolkits/MCPs/Invite Users) — it's a separate
`<button aria-label="attach files">` (component: `AttachmentButton.jsx`,
`src/[fsd]/features/chat/ui/chat-button/`) rendered ABOVE the `<ul role="menu">`, and it carries
**ZERO `data-testid` anywhere** — confirmed via full-file source read on both `main` and
`automation/testids`. This is a genuine gap, not a naming drift: the existing page object's
`ChatPage.attach_files_button` field claims `testid="chat-attach-button"`, but that string does
not exist in source at all (`git grep` on both refs: zero hits) — the field has always been
aspirational/stale, which is why the one existing test touching attachments
(`test_attach_files_button_sends_file_with_message`) bypasses the page object with a raw
`aria-label` locator instead.

- **TWO simultaneous `AttachmentButton` instances render while the "+" menu is open**, both
  testid-less, both wired to the SAME `onAttachFiles` callback (so end-user-visible RESULT is
  consistent regardless of which one processes a file):
  1. An ALWAYS-MOUNTED, invisible instance (`sx={styles.hiddenAttachment}` in
     `PlusChatButton.jsx:316`) — holds the `ref` (`attachmentButtonRef`) that drag-and-drop
     routes through (`NewChatInput.jsx`'s `onDrop` calls `attachmentButtonRef.current.onDrop()`).
  2. The VISIBLE, `showLabel` instance inside the open `.MuiPopper-root`
     (`PlusChatButton.jsx:353`) — this is what step-by-step "click Attach Files" user flows
     actually click; it has NO `ref` at all.
  Each instance mounts its OWN hidden `<input type="file">` with its own dynamically-generated
  `id` — **the id is NOT stable across re-renders**: `id = 'file-upload-input' + new
  Date().getTime()` is a default-parameter expression re-evaluated on every render when no `id`
  prop is passed, so attaching one file changes BOTH instances' ids on the very next render
  (confirmed live: `...366936`/`...366937` → `...539442`/`...539448` after a single attach).
  Any locator strategy that captures this id once and reuses it across multiple attach actions
  will silently break after the first attach.
- **Recommended fix (implementer work, not yet done)**: add a `testId` prop (+ `inputTestId`) to
  `AttachmentButton.jsx`, wired as `data-testid={testId}` on the `IconButton` and
  `data-testid={inputTestId}` on the input; pass `testId="chat-attach-files-button"` +
  `inputTestId="chat-attach-files-input"` ONLY at the visible (`showLabel`) call site — leave the
  always-hidden instance untouched (no case exercises it as a direct target; drag-and-drop
  doesn't need it testid'd, see below). Counter text ("N left", inside the `showLabel` block
  only — no collision risk): `chat-attach-files-counter`.
- **Attached-file chips have no testid either.** `FileList.jsx` (`src/components/Chat/`) — used
  only by chat surfaces (`UserInput.jsx`, `PlaybackToolBar.jsx`), so chat-scoped naming is fine
  despite the `src/components/` location. Recommend a REPEATED `chat-attachment-item` testid
  (same pattern as `chat-message-item`) per visible chip, `chat-attachment-remove-button` scoped
  to its "X", `chat-attachment-overflow-button` for the "+N" overflow trigger
  (`aria-label="Show more files"`, currently testid-less), and `chat-attachment-overflow-item` /
  `chat-attachment-overflow-remove-button` for the overflow popover's own per-file rows. The
  overflow surface is NOT optional to test — any case attaching more than ~2-3 files (default
  viewport) needs it to verify every filename actually rendered.
- **Counter mechanics (confirmed live, linear)**: `remainingAttachments = limits.MAX_ATTACHMENTS
  (10, from `common/constants.js`'s `ATTACHMENT_LIMITS`) - attachments.length` — confirmed at
  three points this run (10→9→8 across 2 file attaches). Cap-boundary (10th/11th file, toast
  warning) confirmed only via source citation, not independently pushed to live.
- **Drag-and-drop routes through the HIDDEN instance, not the visible button** — see above. The
  actual DOM drop-zone is an untestid'd `<Box onDrop=...>` in `UserInput.jsx` (~line 396), but
  its DOM descendant `[data-testid="chat-input"]` (the MUI `TextField` root, `UserInput.jsx:420`,
  on-`main`) works as a drop target via ordinary native event bubbling — confirmed live via a
  capture-phase diagnostic listener showing the real handler's `preventDefault()` fired on both
  `dragover` and `drop`. **No new drop-zone testid is needed.** A synthetic `DataTransfer` + ONE
  continuous `dragenter→dragover→drop` gesture (Synthetic Input Hygiene discipline) reliably
  attaches the file, producing a chip structurally identical to a picker-attached one (same
  `FileList` component, no origin distinction in the DOM).
  - **Self-inflicted-artifact trap (tooling note, not a product finding)**: adding EXTRA
    `document`-level event listeners between successive drop dispatches (done here purely for
    diagnostics) can produce a duplicate attachment from a SINGLE drop (observed once: the app's
    own silent same-name-rename-on-duplicate kicked in, producing two entries from one file). A
    clean, uninstrumented single dispatch immediately afterward produced exactly one new
    attachment with no duplicate — confirms the extra listeners were the cause, not the app.
    Never add extra document-level listeners inside an actual automated test's drag-drop step.
- **Model selector's "selected" checkmark has no stable signal.** `LLMModelsMenu.jsx:48`'s
  existing `data-testid={\`model-selector-option-${item.name}\`}` template IS on `main` — but
  `aria-selected` is `null` on every option, and the only visible "this one's selected" signal is
  an `Mui-selected` CSS class (hashed, unstable) + a trailing checkmark SVG with no discriminating
  attribute. Recommend a `data-selected="true"/"false"` attribute alongside the existing testid
  (state via `data-*`, not a second testid, per the testid=identity/state=data-* ruling) —
  `automation/pages/chat_page.py`'s existing `select_model()` method also doesn't use this
  template at all yet (uses a `:has-text()` locator instead) — worth switching while touching
  this area, since model DISPLAY NAMES drift across environments/deploys but the template's
  `item.name` key is the stable internal model id.
- **`conversation-menu-menu-button` / `chat-conversation-menu-*-menuitem` are prop-indirected,
  NOT literal strings — a naive full-string `git grep` finds ZERO hits for either on ANY ref**,
  which looks like "needs-adding" but is a false negative. Both compose via a shared
  `DotMenu.jsx` component: `data-testid={id ? \`${id}-menu-button\` : undefined}` (line 346, fed
  `id="conversation-menu"` from `ConversationItem.jsx`) and `data-testid={testId ? \`${testId}-
  menuitem\` : undefined}` (line 57, fed `testId: item.key` per menu entry, e.g. `item.key =
  'chat-conversation-menu-delete'`). **Always grep the BASE identifier fed into the template
  (`"conversation-menu"`, `"chat-conversation-menu-delete"`), never the fully-composed final
  string**, when checking provenance for anything rendered through `DotMenu`. Confirmed present
  on BOTH `main` and `automation/testids` (same file/line) for the conversation 3-dot menu and
  its Delete item specifically.

## Network / timing

- Model-TTS playback is **Socket.IO-driven** (`tts_start`/`tts_audio_chunk`/
  `tts_done`/`tts_stop`), not HTTP — no XHR/fetch to `wait_for_response()` on
  for play/stop transitions; wait on the DOM/icon state instead.
- Auth on localhost is fully transparent (`VITE_DEV_TOKEN` build-time env) —
  works identically whether driven via Playwright MCP or a fresh CDP
  (`browser-verify`) session with no storage state at all; no login flow to
  navigate around for chat cases.

## In-chat "New Toolkit" canvas (ELITEA-2082/2083/2080 — full findings)

Extended 2026-07-24 (cluster analysis, batch `cov60`). The `+` menu's
Toolkits → "+ Create New Toolkit" flow opens `ToolkitEditor.jsx`
(`src/pages/NewChat/ToolkitEditor.jsx`) in the SAME right-side canvas slot
`AgentEditor`/`PipelineEditor` use (`useMutuallyExclusiveEditors.js` /
`useEditToolkit.js` own the create/edit-mode state machine). It renders the
SAME shared `ToolkitTypeSelector.jsx` + `ToolkitForm`/`ToolBaseProperty.jsx`
components the standalone `/toolkits/create` wizard uses — every
`ToolkitCreationPage` field (`type_search_input`, `TOOLKIT_TYPE_CARD`,
`name_input`, `TOOLKIT_FIELD_INPUT`) works AS-IS in this context, confirmed
live. Don't redeclare them on a new page object — compose
`ToolkitCreationPage(page)` alongside a small canvas-chrome-only page
object, exactly the pattern `AgentCanvasPage` already established for the
sibling "Create New Agent" canvas (ELITEA-2166).

- **`+` menu → Toolkits submenu handles** (all confirmed live, provenance
  `automation/testids`-only — awaiting human promotion to `main`):
  `toolkits-menuitem` (hover reveals submenu, same `onMouseEnter` mechanism
  as `agents-menuitem`), `toolkits-create-new-button` (template
  `${sectionKey}-create-new-button` in `PlusChatSubmenu.jsx`,
  `sectionKey='toolkits'`), `toolkits-search-input` (template
  `${sectionKey}-search-input`, same component — searches the SUBMENU's
  existing-toolkit list, NOT the type-picker below; don't confuse the two).
- **Type-picker search is a plain substring match against each card's own
  label — GOTCHA for "Artifact" specifically**: the Storage-category plain
  toolkit type is labeled exactly `"Artifact"` (singular); a SEPARATE,
  unrelated MCP-category entry is labeled `"Elitea Artifacts"` (plural,
  different entity). Searching `"Artifacts"` (plural) matches ONLY the MCP
  card (`toolkit-type-card-mcp_Elitea Artifacts`) — the plain
  `toolkit-type-card-artifact` card does NOT match, because "Artifacts"
  (9 chars) isn't a substring of the label "Artifact" (8 chars). Search
  `"Artifact"` (no trailing s) to reach both, distinguishing by the exact
  testid. Filed as case-text-drift clarification `#1010` (reverse-masking —
  live search behavior is correct/consistent, a case that literally says
  "type Artifacts" will silently filter out the plain Artifact card).
- **Create-mode action button reads "Create", not "Save"** — this canvas's
  save-slot renders ONE of two DIFFERENT components depending on
  `isCreating`: `CreateToolkitButton.jsx` (create mode, text hardcoded
  `"Create"`, ZERO testid/props) or `SaveToolkitButton.jsx` (edit mode —
  i.e. AFTER a successful create, text `"Save"`). A case that says 'click
  Save' while the toolkit doesn't exist yet is describing the button's
  POST-click label, not its actual label at click-time — clarification
  `#1011`. The label flip itself (`"Create"` → `"Save"`) is a reliable,
  cheap, independent confirmation that a create actually persisted, usable
  alongside/instead of racing the ~3s-lived success toast.
- **`ToolkitEditor.jsx`'s own `<BaseEditor>` call passes NONE of
  `titleTestId`/`subtitleTestId`/`closeButtonTestId`** — confirmed via
  source read (zero occurrences in the file) AND live DOM query (0 testid
  matches on the canvas title, the X/close button, or anywhere in the
  Discard-button + its confirm-dialog subtree). This is a straight gap, not
  a design choice: `AgentEditor.jsx` ALREADY passes the sibling
  `agent-canvas-title`/`agent-canvas-subtitle`/`agent-canvas-close-button`
  props to the exact same `BaseEditor` — mirror that shape 1:1 for Toolkit
  (`toolkit-canvas-title`/`toolkit-canvas-close-button`; subtitle unused by
  any case so far, skip it per scope discipline until a case needs it).
- **Live trap: the canvas's X (close) button has NO usable `aria-label`
  either.** A DIFFERENT, unrelated icon elsewhere on the same page ALSO
  carries `aria-label="close"` (not this canvas) — a selector built on that
  attribute silently clicks the wrong element with no error. DOM-position
  disambiguation was needed this session (confirmed live: the correct
  button sits at a distinct `(x,y)` in the header row, distinguishable from
  every other page-wide button by its bounding box) — but position is not a
  durable locator; this is exactly what the `needs-adding`
  `toolkit-canvas-close-button` testid fixes.
- **Discard button + its confirm dialog: zero testids anywhere, but the
  FIX is a pure threading gap, not new capability.** `EditorHeader.jsx`'s
  `<Button.DiscardButton onDiscard={...} />` call (shared by every editor:
  Agent/Pipeline/Toolkit/Artifact) never passes the THREE testid props
  `DiscardButton.jsx` itself ALREADY natively supports
  (`dataTestId`/`modalDataTestId`/`confirmButtonDataTestId` — these thread
  straight through to the button, the warning `Modal.BaseModal`, and its
  confirm button respectively). Confirming via Discard shows a "Warning"
  dialog, body text `"Are you sure you want to discard changes?"`
  (`ModalConstants.WARNING_MESSAGES.DISCARD_CHANGES`), confirm button text
  `"Discard"` (`WARNING_BUTTONS.DISCARD`) — exact, stable, hardcoded
  strings if a text-based interim assertion is ever needed, but the
  compliant fix is threading `toolkit-canvas-discard-button` /
  `toolkit-canvas-discard-confirm-dialog` /
  `toolkit-canvas-discard-confirm-button` through ONLY the Toolkit call
  site (this shared component's OTHER editors get nothing added — no case
  anywhere yet exercises Agent/Pipeline/Artifact's own Discard flow).
- **Discard resets ALL THE WAY back to the type-picker step**, not just a
  blanked config form — confirmed live (typed Name/Bucket → Discard →
  confirm → canvas shows "Choose the toolkit type" again, search field
  empty, Discard/Create both disabled). Formik `resetForm()` +
  `editToolDetail`/`formikInitialValues` local-state reset together produce
  this; no network call fires on Discard (confirmed via network capture —
  entirely client-side).
- **Toolkit participant row testid, once created**: same
  `chat-participant-row-{entity_name}_{id}_{project_id}` composition
  documented above for Agents — entity_name literal for a toolkit
  participant is `"toolkit"` (singular; confirmed live e.g.
  `chat-participant-row-toolkit_1755_399`), giving
  `chat-participant-row-toolkit_{id}_{project_id}`. The PARTICIPANTS
  panel's "TOOLKITS" section accordion header itself
  (`ParticipantsAccordion.jsx`) accepts NO testid prop at all currently —
  the row's own presence is the pragmatic proxy for "the TOOLKITS section
  rendered" (`ParticipantSection` only renders when its group is
  non-empty), until a `chat-participants-section-{key}` testid is added.
- **Toolkit-create endpoint**: `POST /elitea_core/tools/prompt_lib/{project_id}`
  → `201 Created` on success (mirrors the existing
  `test_toolkit_creation_create_bucket_verify_list_files.py` network-capture
  idiom — filter by URL containing `/tools/prompt_lib/`). Toolkit-delete
  (cleanup): `DELETE /elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}`
  → `204` (note: singular `tool`, not `tools`, for delete — confirmed live).
- **Console noise, already tracked, NOT this flow's bug**: the React
  key-prop warning at `ToolkitTypeSelector.jsx`/`CategorySection.jsx`/
  `GroupedCategory.jsx` (`#291`) fires on every visit to "Choose the
  toolkit type" — exclude from any "no new console errors" assertion on
  this surface.

## Editing an EXISTING agent participant via the pencil icon (ELITEA-2089 — full findings)

Extended 2026-07-24. The expanded PARTICIPANTS panel's per-row hover actions
(`ParticipantActions.jsx`, `src/[fsd]/features/chat/participants/ui/ParticipantActions/`)
open the **SAME `AgentEditor`/`AgentCanvasPage` canvas** ELITEA-2166 already built a
page object for — confirmed live: `agent-canvas-title`/`agent-canvas-subtitle`/
`agent-canvas-close-button`/all 5 `agent-canvas-section-*` testids render identically
whether the canvas was opened via "+ Create New Agent" (create-mode) or via this
row's pencil icon (edit-mode, URL gains `?edited_participant_id={id}`). **No new
canvas-chrome page object needed for edit-mode — `AgentCanvasPage` is reusable
as-is.**

- **Participant row hover reveals TWO icon buttons, only one has a testid.**
  `chat-participant-row-{uniqueId}` (existing `ChatPage.PARTICIPANT_ROW` template)
  shows, on hover: a pencil "Edit" button (`id="EditButton"`, `aria-label` varies by
  entity type — "Edit agent"/"Edit pipeline"/"Edit mcp"/"Edit toolkit" — **ZERO
  `data-testid`**, confirmed by full-file read of `EditParticipantButton.jsx`) and a
  trash "Remove" button (`chat-participant-remove-button`, already testid'd, already
  wired as `ChatPage.PARTICIPANT_REMOVE_BUTTON`). The sibling
  `DeleteParticipantButton.jsx` (same directory) already hardcodes its testid
  directly on the `IconButton` — the Edit button's fix is a straight mirror of that
  existing pattern (`data-testid="chat-participant-edit-button"`), not new capability.
  One testid covers both the button's visual states (pencil when `canEdit`, gear/
  settings icon when not — cosmetic, not identity).
- **The expanded PARTICIPANTS panel itself has testids that are NOT yet wired into
  `chat_page.py`.** `chat-participants-panel` (container, `data-expanded` state
  attribute) and `chat-participants-panel-toggle-button` (ELITEA-2098) exist live on
  `automation/testids` but no page-object field references them yet — the legacy
  text-based `expand_participants_panel()`/`is_participants_panel_expanded()` is
  still the only way any MERGED test reaches this panel. First case that actually
  needs the pencil-icon edit flow should add the two `LocatorDescriptor` fields
  rather than reach for the legacy text-based method.
- **Composer chip is a 3-button `ButtonGroup[aria-label="Model Selector Menu"]`,
  not 2.** `chat-switch-participant-button` (icon-only, `aria-label="Switch Agent"`)
  + `chat-version-selector-trigger` (icon-only, `aria-label="version selector menu"`)
  + a THIRD button (`aria-label="agent settings menu"`, **NO testid**) that carries
  the actual visible TEXT: `echo`/`base`-style labels normally, or the literal
  string `"Editing…"` while that same agent's own canvas (create OR edit mode) is
  open. This confirms ELITEA-2166's `#709` finding generalizes to the edit-entry
  point too, not just create-mode — same mechanism, same fix (assert the live text,
  don't assume the case's literal "name + Editing..." combined wording). The first
  two buttons stay icon-only regardless of editing state; only the third button's
  text changes. `testid needed: chat-agent-settings-menu-button` if a future case
  wants to assert this without scoping off the `ButtonGroup`'s aria-label.
- **`toast-message` is a suite-wide generic success/error toast testid** — already
  used by `artifacts_page.py`/`skill_detail_page.py`/`skills_list_page.py`, and
  confirmed here to ALSO cover the agent-edit-save toast ("The agent has been
  updated", exact text, byte-for-byte match to case ELITEA-2089's literal wording).
  Any future chat/agent case needing a save-confirmation toast should reuse this
  testid rather than hunt for a new one — it's a single shared snackbar mount point.
- **Toast timing trap for analyst tooling** (not a product issue): a naive
  click-Save → `wait-network-idle` → THEN check-for-toast sequence can miss it
  entirely — the toast can dismiss before the check runs. Click-Save →
  IMMEDIATELY wait on `[data-testid="toast-message"]` becoming visible, don't
  interleave a network-idle wait first.
- **Standalone Agent detail page (`/agents/all/{id}`) and the in-chat canvas share
  the EXACT SAME `agent-welcome-message-input` testid** — confirmed live: a value
  saved via the in-chat edit-mode canvas reads back identically on the standalone
  page with zero transformation, no separate re-derivation needed by a future case
  touching either surface.
- **Cross-AFS test-data collision risk**: ELITEA-2166 and ELITEA-2089 BOTH create a
  dedicated agent literally named `echo` (matching each case's own literal Test Data
  table). Both AFS's fixtures are self-contained (create-in-setup, delete-in-
  teardown) so sequential runs are safe; a genuine collision is only possible under
  PARALLEL (xdist) execution of both specs at once. Neither AFS resolves this by
  suffixing the name (deferred to implementer/lead, consistent with ELITEA-2166's
  own note) — flag again if a THIRD case ever wants a fixture agent named "echo".

## Removing a "Users" participant via the collapsed badge popper (ELITEA-2170 — full findings)

Extended 2026-07-24. This is a DIFFERENT sub-surface from ELITEA-2089's expanded-panel
pencil-icon edit flow above — same popper mechanism (`chat-participants-badge-users` →
`chat-participants-badge-button` → `chat-participants-popper`), but the USERS section's
own row renderer (`UsersParticipantDropdown/UserMenu.jsx`) is a THIRD component, distinct
from both `ParticipantItem.jsx` (expanded panel, agent/pipeline/toolkit/mcp rows) and
`UserParticipantItem.jsx` (expanded panel's inline avatar-group display).

- **Which sub-component renders the USERS trigger is layout-branched, traced to source
  (`Participants.jsx`):** `showCollapsedParticipants = collapsed && !isSmallWindow`. At
  Playwright's default viewport (~1280×720, not "small window") with a FRESH browser
  context (no persisted panel-collapse state), the collapsed icon-rail form
  (`CollapsedPerticapantsList.jsx`) renders by default — this IS what
  `chat-participants-badge-users`/`open_participants_popover(section="users")` already
  targets, confirmed live. A narrower viewport or a persisted-expanded panel state
  instead renders `ExpandedParticipantsList.jsx`'s own un-wrapped trigger (same
  `chat-participants-badge-button`/`chat-participants-popper` testids, different DOM
  parent, NOT reachable via the `chat-participants-badge-users` container) — a risk to
  flag, not yet hit in practice at the project's standard automation viewport.
- **`UserMenu.jsx`'s per-user row has NO container testid — genuine, confirmed-live
  collision.** Each row's `DeleteParticipantButton` (imported from the SAME
  `ParticipantActions/DeleteParticipantButton.jsx` file ELITEA-2089 already covers)
  hardcodes `data-testid="chat-participant-remove-button"` — but since `UserMenu.jsx`'s
  row `<Box>` wrapper carries no testid of its own, this button testid resolves to **N
  elements simultaneously** whenever N users are listed (confirmed live via
  `query-all`: 3 participants → 3 identical-testid buttons, positionally distinguishable
  only by DOM order/`rect`, not by any stable handle). Same for the row's `UserAvatar` —
  `UserAvatar.jsx` (`src/components/UserAvatar.jsx`) already ACCEPTS + wires a `testId`
  prop straight onto `data-testid`, but `UserMenu.jsx`'s call site doesn't pass one (pure
  prop-threading gap, same shape as ELITEA-2082's toolkit-canvas-title finding).
- **The fix is a one-line, zero-new-constants mirror of an already-shipped sibling
  pattern**: `ExpandedParticipants/ParticipantItem.jsx:256` already does
  `data-testid={`chat-participant-row-${getChatParticipantUniqueId(participant)}`}` for
  the OTHER participant types. Applying the identical line to `UserMenu.jsx`'s row
  `<Box>` (uniqueId = `user_{entity_meta.id}_{project_id}`, since
  `ChatParticipantType.Users === 'user'`, confirmed in `common/constants.js:971`) reuses
  the EXISTING `ChatPage.PARTICIPANT_ROW` template + `PARTICIPANT_REMOVE_BUTTON`
  constant — no new page-object fields, just a new `remove_user_participant(user_id,
  project_id)` method mirroring the existing `remove_agent_participant()`
  (`chat_page.py:3374`) verbatim in structure.
- **Confirm-dialog wording (shared `DeleteEntityModal`, entity-type `'user'`):** title
  `"Remove user?"`, tooltip `"Remove user"`, body **`"Are you sure to remove the {name}
  user from chat?"`** (word is "chat", never "conversation" — filed as case-text-drift
  clarification #1020 when a case's literal text said "conversation"). `{name}` resolves
  via `getParticipantName()` → `participant.meta.user_name` for Users-type participants.
- **Removal is genuinely server-persisted**, confirmed via a full page reload after
  clicking Remove: participants-badge count and popper contents both survive the reload
  at the decremented count — not merely an optimistic client-side splice.
- **Self-removal is not blocked at the UI-affordance level**: the current user's own row
  ("Test Bot") renders the identical (also-unscoped) remove button — no special-casing
  observed. Untested by any case so far; would need the same row-scoping fix above.
- **Browser-lane contamination trap (tooling note, not a product finding):** the shared
  `.claude/skills/browser-verify/scripts/chrome-launcher.sh` hardcodes a GLOBAL
  `CHROME_USER_DATA=/tmp/chrome-cdp-profile` + `CHROME_PID_FILE=/tmp/chrome-cdp-verify.pid`
  regardless of the `--port`/`CDP_PORT` argument — two concurrent sessions each launching
  "their own isolated instance" via this script can end up sharing the SAME Chrome
  process/profile/tab (observed live this session: a mid-flow tab got silently
  hijacked into an unrelated Pipeline-create flow from another concurrent analyst).
  Workaround used: launch Chrome directly with a private, session-specific
  `--user-data-dir` (bypassing the shared script entirely) rather than trusting the
  script's `--port` flag to guarantee isolation.

## In-chat "Create New Pipeline" canvas (ELITEA-2079 — full findings)

Extended 2026-07-24 (batch `cov60`). The `+` menu's Pipelines → "+ Create New
Pipeline" flow opens `PipelineEditor.jsx` (`src/pages/NewChat/PipelineEditor.jsx`)
in the SAME right-side canvas slot `AgentEditor`/`ToolkitEditor` use — same
`useMutuallyExclusiveEditors.js` state machine already documented above for the
Toolkit canvas. Unlike Toolkit, Pipeline's canvas has a real **mode split**:
create-mode renders only the reused `CreateAgentForm` fields (`entityType="pipeline"`)
plus a "Save the pipeline to access the flow editor." placeholder where the Flow
Editor tab would go; only AFTER the first Save (which assigns the pipeline an id
and flips `isCreateMode` false) do the "Configuration"/"Flow editor" tabs — and the
real Flow/Yaml/Add-node/State toolbar — render at all. This is the exact same
create-vs-detail-form split `test-specs/pipelines/_surface.md`'s ELITEA-2021
section already documented for the standalone `/pipelines/create` vs
`/pipelines/all/{id}` pages — same root component (`CreateAgentForm`), same
"case text interleaves create-time and detail-only fields" trap.

- **`+` menu → Pipelines submenu handles** (all confirmed live): `pipelines-menuitem`
  (top-level item, `automation/testids`-only — the whole `PLUS_MENU_ITEMS` array
  with all 5 `*-menuitem` testids, one commit, none yet on `main`),
  `pipelines-create-new-button` (template `${sectionKey}-create-new-button` in the
  SHARED `PlusChatSubmenu.jsx`, `sectionKey='pipelines'` wired at
  `PlusChatButton.jsx:296` — same mechanism as `agents-create-new-button`/
  `toolkits-create-new-button`, `automation/testids`-only), `pipelines-search-input`
  (same shared component, searches the SUBMENU's existing-pipeline list). **The
  submenu's pick-list excludes pipelines already added as a participant to the
  CURRENT conversation** — confirmed live (a just-added pipeline vanished from its
  own submenu's search results in that same conversation, but reappeared
  immediately when searched from a brand-new conversation) — don't mistake this
  for a broken create/search flow if a just-created entity seems to "disappear."
- **The embedded `EditorPanel` (Flow/Yaml/State toolbar, Add-node menu, ReactFlow
  canvas) is the EXACT SAME component the standalone Pipeline Detail page uses** —
  confirmed live, zero behavioral differences: `pipeline-flow-view`/
  `pipeline-yaml-view`/`pipeline-add-node-button`/`rf__wrapper`/`rf__node-{id}`/
  `pipeline-yaml-editor` all work identically inside the chat canvas. Every
  finding already recorded in `test-specs/pipelines/_surface.md` (LLM node fields,
  YAML sync, node delete, Add-node menu's 11 types, etc.) applies here unchanged —
  read that digest first, don't re-derive.
- **Canvas chrome (title/subtitle/close/discard/tabs) is a confirmed, mirror-the-
  sibling gap — same shape already fixed for Agent (ELITEA-2166) and Toolkit
  (ELITEA-2082/2083/2080), just not yet done for Pipeline.** `PipelineEditor.jsx`'s
  own `<BaseEditor>` call passes NONE of `titleTestId`/`subtitleTestId`/
  `closeButtonTestId`/`discardButtonTestId` (confirmed via source read — zero
  occurrences in the file), despite `BaseEditor.jsx` already supporting all four as
  plain optional props. The canvas's X (close) button also has NO usable
  `aria-label` (confirmed live, same "Live trap" already documented above for
  Toolkit — a bounding-box-position heuristic was needed this session, not a
  durable locator). `testid needed: pipeline-canvas-close-button` (this case's own
  scope — title/subtitle/discard are untouched by ELITEA-2079's steps, leave those
  to whichever future case actually asserts on them, per the "touches = executed
  code path" scope ruling).
- **The "Configuration"/"Flow editor" tabs are feature-local to `PipelineEditor.jsx`
  itself (plain MUI `<Tab>`s, not a shared component)** — zero `data-testid` today;
  `testid needed: pipeline-canvas-configuration-tab` / `pipeline-canvas-flow-editor-tab`,
  a direct one-line addition on each `<Tab>`, no threading needed.
- **The create-mode Save button has NO testid either — a distinct gap from the
  edit-mode one.** `CreateApplicationSaveButton.jsx` forwards `...buttonProps` (same
  mechanism `AgentEditor.jsx` already uses to wire `agent-save-button`), but
  `PipelineEditor.jsx`'s own call site passes nothing. `testid needed:
  pipeline-save-button` for this one specifically — do NOT reuse `agent-save-button`
  here (that name is reserved for Agent's own create-mode button per ELITEA-2166's
  declared exclusion).
- **The EDIT-mode Save button (`SaveApplicationButton.jsx`) hardcodes
  `data-testid="agent-save-button"` directly in the shared component itself** —
  confirmed via source read, shared by Agent AND Pipeline (AND
  `ApplicationTabBar.jsx`/`ToolkitsTabBarPlaceholder.jsx`/`usePin.hooks.js`).
  Functional but misleadingly named for a Pipeline — filed `#1040` (MINOR, not
  blocking). **Automation should reuse `agent-save-button` as-is for a Pipeline's
  edit-mode Save click** — it works, and fixing the mislabel is a cross-cutting
  shared-component change out of scope for any single case.
- **PARTICIPANTS-panel Pipelines section is fully pre-existing, zero new work
  needed.** `chat-participants-badge-pipelines` (template
  `` `chat-participants-badge-${entity.section}` `` in `CollapsedPerticapantsList.jsx`,
  confirmed on-main ✓) + the existing generic
  `ChatPage.open_participants_popover(section="pipelines")` method already handle
  this end-to-end — confirmed live, popper text reads "Pipelines" (title case) +
  the pipeline's name + version.
- **CONFIRMED PRODUCT DEFECT (`#1039`, MAJOR): a bare LLM node (added via
  "+ Add Node → LLM" with zero further configuration) used as a chat participant
  does not respond — 400 `messages.0: user messages must have non-empty content`,
  reproduced 2/2.** Critically, the IDENTICAL bare-LLM-node YAML (via
  `PipelineAPI.create_pipeline_with_llm_node()`) DOES produce a real response
  through the standalone Pipeline Detail page's own embedded chat (confirmed by
  re-running the merged `test_pipeline_execution.py::test_pipeline_response_is_meaningful`
  live — it passes). This narrows the defect to the **chat-participant invocation
  path specifically** — any future case sending a message through a freshly-added,
  unconfigured LLM-node pipeline AS A CHAT PARTICIPANT should expect this same
  failure and soft-assert it against `#1039`, not re-discover/re-file it.
- **Tooling gotcha (analyst-only): a shell loop that builds a `git show <ref>:<path>`
  argument containing the literal `[fsd]` path segment inside a variable-interpolated
  double-quoted string can silently mis-glob and return "not found" even though the
  content is genuinely present** — confirmed by re-running the identical `git show`
  with the path written as a single-quoted literal (no variable expansion touching
  the brackets), which found the content correctly both times. If a provenance grep
  against a `src/[fsd]/...` path comes back suspiciously empty, retry with the path
  hardcoded/quoted directly before concluding "needs-adding" — this cost real time
  this session (briefly misread `chat-participants-badge-pipelines` as
  entirely-missing before catching it).

## In-chat Pipeline canvas — Discard mechanism + testid landings since ELITEA-2079 (ELITEA-2078, 2026-07-24)

Extended 2026-07-24 (batch `cov60`). This session re-verified the ELITEA-2079
section above and found several of ITS `needs-adding` gaps have already
**landed live** on `automation/testids` (the ELITEA-2079 implementer's
in-flight work) — future cases on this surface should use the ACTUAL landed
names below, not re-derive or re-propose them:

- **`pipeline-save-button`** (create-mode Save) — LANDED, confirmed live.
- **`pipeline-canvas-close-button`** — LANDED, confirmed via source read of
  `PipelineEditor.jsx`'s `<BaseEditor closeButtonTestId="pipeline-canvas-close-button" …>`;
  **now also confirmed LIVE** (ELITEA-2079 redispatch spot-check, 2026-07-24 —
  resolved via `document.querySelector` immediately after opening the canvas,
  before this row had ever been live-clicked by any prior pass).
- **`pipeline-canvas-configuration-tab`** / **`pipeline-canvas-flow-editor-tab`** —
  LANDED, confirmed live.
- **`pipeline-add-node-menu-item-{type}`** — LANDED (ELITEA-2030's work), but
  under a DIFFERENT name than ELITEA-2079's own AFS proposed
  (`pipeline-add-node-type-{type}`) — confirmed live via DOM query
  (`item.type` = e.g. `llm`, `hitl`, `mcp`, …). **Use the landed name**,
  `AddNodeMenu.jsx:119/142` (`` data-testid={`pipeline-add-node-menu-item-${item.type}`} ``,
  template — false-negative under literal `git grep`, confirmed via source
  read instead, on-`automation/testids` only as of this session).

**Still NOT landed** (confirmed via source read of `PipelineEditor.jsx`'s
`<BaseEditor>` call on `origin/automation/testids` HEAD `d879a966…`):
`titleTestId`, `subtitleTestId`, `discardButtonTestId` — none of these three
are wired yet, only `closeButtonTestId` is. ELITEA-2078 is the first case in
this batch to touch the Discard button, so it owns adding
`discardButtonTestId`/`discardModalTestId`/`discardConfirmButtonTestId`
(mirroring `agent-canvas-discard-button`/`toolkit-canvas-discard-button`) —
`title`/`subtitle` remain untouched-by-any-case gaps, per scope discipline.

**Canvas-header Discard mechanism — fully traced source-to-DOM, confirmed
live twice on independent pipeline instances.** `PipelineEditor.jsx` wires
`onDiscard={handleDiscard}` into `<BaseEditor>`, which forwards it through
`EditorHeader.jsx` to the shared `DiscardButton.jsx`. The button's `disabled`
prop is `!isFormDirty && !isYamlCodeDirty` (`useIsPipelineYamlCodeDirty()` —
tracks the pipeline's YAML/graph state via Redux, independent of Formik) —
so the SAME canvas-header Discard button governs BOTH create-time form-field
edits AND Flow-editor graph edits (adding/removing/reconfiguring a node).
Confirmed live: button is `disabled: true` immediately after the Setup
Save (clean baseline), flips to `disabled: false` the instant an LLM node is
added via "+ Add node" (zero form fields touched), and returns to
`disabled: true` after a successful Discard-confirm.

Clicking it opens `DiscardButton.jsx`'s own built-in confirm dialog (generic
`Modal.BaseModal`, NOT the `DeleteEntityModal.jsx` used by node-delete —
different component, same "Warning" styling): title **"Warning"**, body
**"Are you sure you want to discard changes?"**, buttons **"Cancel"** /
**"Discard"** (exact text, `ModalConstants.WARNING_MESSAGES.DISCARD_CHANGES`
/ `WARNING_BUTTONS.DISCARD` — same shared strings the Toolkit canvas's
Discard dialog already uses, confirmed byte-identical). Confirming calls
`useDiscardApplicationChanges`'s `discardApplicationChanges` = Formik
`resetForm()` + the passed `handleDiscard` (`dispatch(actions.resetPipeline())`
+ `dispatch(editorActions.resetPipelineEditor())`) — **100% client-side, zero
network request**, confirmed via source read (no API call anywhere in
`handleDiscard`'s body) — matches the identical "no network call on Discard"
finding already established live for the Toolkit canvas (ELITEA-2080 section
above) and for node-delete (`test-specs/pipelines/_surface.md`, ELITEA-2018).

**Zero testids anywhere on this Discard button + its dialog + its 2 buttons**
— confirmed via full live DOM enumeration both before-add (disabled) and
after-confirm (dialog gone) states, on two independent pipeline ids (`5856`,
`5860`). `testid needed: pipeline-canvas-discard-button` /
`pipeline-canvas-discard-confirm-dialog` / `pipeline-canvas-discard-confirm-button`
— trivial threading, zero shared-component edits (`EditorHeader.jsx`/
`DiscardButton.jsx` already accept all three as props, same mechanism
Agent/Toolkit already use).

**Untested interaction with the `DeleteEntityModal.jsx` MUI-ancestor-testid
quirk** (`test-specs/pipelines/_surface.md` § "Node delete" — MUI's `Dialog`
sometimes applies `data-testid` to an ancestor wrapper, not the inner `Paper`
carrying `role="dialog"`): this Discard dialog uses the SIMPLER
`Modal.BaseModal` component, not `DeleteEntityModal.jsx` — untested whether
the same ancestor-vs-inner-Paper quirk applies here once `discardModalTestId`
is wired. Flag for the implementer to verify empirically; `get_by_role("dialog")`
is the documented-safe fallback either way (only one dialog is ever open at a
time in this flow).

**LLM node structure, confirmed live (case ELITEA-2078's own step 7
assertion):** a freshly-added `rf__node-{id}` contains a real `<svg>` icon, a
`.MuiTypography-root` label matching the node's display name (e.g. `"LLM 1"`),
and exactly 2 `.react-flow__handle` connection-port elements (ReactFlow's own
convention, zero app-source touches). Since a single-node pipeline's one node
always auto-becomes the entry point (`test-specs/pipelines/_surface.md` §
"Entry Point node"), its config panel additionally shows a `Trigger` field —
expected, not specific to this case.

**A pipeline saved via create-mode Save with ZERO real nodes ever added shows
EMPTY `Yaml`-tab content, not a stub `nodes: [END]` YAML** — confirmed live
twice. Consistent with `PipelineEditor.jsx`'s own source comment ("empty
string is valid - will create just an END node"): the visible `End` node is a
client-side rendering default for empty/absent `instructions`, not a
persisted YAML entity. Not a defect — a future case asserting on YAML content
in this exact state (saved, zero nodes ever added) should expect empty
content.

## In-chat "New MCP" canvas (ELITEA-2085 — full findings)

Extended 2026-07-24 (batch `cov60`). The `+` menu's **MCPs** submenu
(`mcps-menuitem`, sectionKey `'mcps'` — a DISTINCT top-level submenu from
**Toolkits**, not a filter within it; `PlusChatButton.jsx`'s
`SUBMENU_KEYS.MCPS = 'mcps'`, gated by `useIsMcpVisible()`) → "Create New MCP"
(`mcps-create-new-button`) opens the **SAME** `ToolkitEditor.jsx` canvas the
ELITEA-2082/2083/2080 cluster already documented for plain Toolkit creation —
just with `isMCP=true` threaded all the way down
(`handleCreateMCP` → `onCreateToolkit(true)` →
`onShowToolkitEditorCreator(isMCP)` → `editingToolkit={isCreating:true, isMCP:true}`).
Confirmed live: canvas title reads `"New MCP"` before a type is picked, `"New
Remote MCP"` after — vs. plain Toolkit's `"New Toolkit"`/`"New {Type} Toolkit"`.
Every CONFIGURATION-form testid is **identical to the standalone `/mcps/create`
page** (`toolkit-type-card-mcp`, `mcp-type-picker-local-empty-state`,
`toolkit-form-name-input`, `toolkit-field-url-input`,
`toolkit-field-client_secret-input-field`, …) — `automation/pages/mcp_form_page.py`
(`McpFormPage`) composes onto this canvas AS-IS for every CONFIGURATION field;
do not redeclare them on a new page object. **Do not reuse
`McpFormPage.save_button`** though — the in-chat canvas's action button is a
DIFFERENT testid, `toolkit-form-create-button` (`CreateToolkitButton.jsx`,
create-mode only; flips to `SaveToolkitButton.jsx`/no-new-testid-needed once
persisted — the standalone page's `toolkit-form-save-button` belongs only to
that page, never to this canvas).

- **The "Remote"/"Local" split is section headers, not tabs** — same finding
  ELITEA-1921 already made for the standalone page, re-confirmed here for the
  in-chat canvas. A case that says "click the Remote tab" is describing the
  section heading text, not a separate clickable element; one click on
  `toolkit-type-card-mcp` satisfies the whole intent.
- **Connection-status widget (`McpAuthStatus.jsx`) renders inside this canvas
  immediately after a successful create — no reload needed.** Two testids,
  BOTH already present on `automation/testids` as of this session (no
  `add-data-testid` work needed for them): `toolkit-connection-status`
  (container, `data-connected="true"/"false"` state attribute, text "Not
  Connected"/"Connected!") and `toolkit-connection-auth-button` (the
  Login/Logout button inside it). A freshly-created Remote MCP with a Client
  Secret configured starts `data-connected="false"`, text "Not Connected",
  button "Login" — matches the `remoteMcpLoggedOut` participant-warning state
  below, not `mcpIsDisconnected` (see next bullet).
- **Two distinct "MCP is broken" states exist in `ParticipantWarning.jsx`, gated
  by different flags, with different message text** — do not conflate them:
  - `mcpIsDisconnected` → `"The {name} mcp server is disconnected. Reconnect it
    to use."` (no "Log in." link).
  - `remoteMcpLoggedOut` → `"Server is disconnected!  Reconnect it to use. "` +
    a `McpLogInLink` rendering `"Log in."` — **this is the state a
    freshly-created Remote MCP with a Client Secret actually renders**,
    confirmed live twice (ids `1789`, `1790`). Note the JSX source has a
    literal DOUBLE space after "disconnected!" that survives verbatim into
    `textContent` — assert with whitespace normalization
    (`" ".join(text.split())`), not an exact `==` against a single-spaced
    literal.
- **Disconnected/warning-state participant rows had ZERO testids before this
  session — now fixed.** `ParticipantItem.jsx` renders participants through
  TWO mutually-exclusive branches: a "normal" branch (has
  `chat-participant-row-{uniqueId}` + reachable via `ParticipantActions`'
  edit/remove buttons) and an "attention/warning" branch
  (`StyledTipsContainer`, entered whenever `mcpIsDisconnected` /
  `remoteMcpLoggedOut` / `someToolsAreUnavailable` / `isVersionUnavailable` /
  `isPublishedAgentGone` / misconfiguration-errors is true) which previously
  had NO testid anywhere — not the row, not the warning icon, not the warning
  message. Added `chat-participant-row-{uniqueId}` (same existing template,
  just threaded onto the other branch), `chat-participant-warning-icon`, and
  `chat-participant-warning-message` this session —
  `EliteaAI/EliteaUI@6b5aa80d` on `automation/testids`, re-verified live via
  HMR against a second fixture (id `1790`) before this digest was written. Any
  FUTURE case touching a participant in ANY attention state (misconfigured
  agent, blocked toolkit, gone-published-agent, …) can now use the same three
  testids — this was a structural gap, not MCP-specific.
- **MCP participant `entity_name` is `"toolkit"`, not `"mcp"`** — same finding
  the ELITEA-2082 cluster already made for plain Toolkit participants,
  reconfirmed here: `getChatParticipantUniqueId()` yields
  `toolkit_{mcp_id}_{project_id}` for an MCP row (`meta.mcp === true`
  distinguishes it for icon/rendering purposes only, not at the
  `entity_name`/uniqueId level).
- **Provenance-tooling gotcha (process note, not a product finding):** the
  standard two-stage grep
  (`git grep -- "$t" <ref> -- src/ | grep -E "(data-testid|testid.*=.*$t)"`)
  under-reports for TWO reasons hit this session: (1) object-literal
  `testId: 'foo'` props (camelCase, colon not `=`) don't match the stage-2
  filter even case-insensitively — e.g. `mcps-menuitem`'s entry in
  `PlusChatButton.jsx`'s `EXPANDABLE_ITEMS` array; (2) every
  `toolkit-field-{k}-*`/`toolkit-type-card-{key}`/`{sectionKey}-*` handle is a
  template literal — the RENDERED string never appears verbatim in source, only
  the template does. Grep the template (`` `toolkit-field-${k}-input` ``), not
  the rendered value, for any dynamic testid; a bare "no matches" on the
  rendered string is not evidence of absence.
- **Toolkit-create endpoint is shared, chat-canvas and standalone page alike**:
  `POST /elitea_core/tools/prompt_lib/{project_id}` → `201` (confirmed via
  source read of `api/toolkits.js`'s `useToolkitCreateMutation` — same mutation
  regardless of entry point). No MCP-specific or chat-specific create endpoint
  exists.
- **Console noise, already tracked, NOT this flow's bug**: `#291` (React
  `key`-prop warning, `ToolkitTypeSelector.jsx`/`CategorySection.jsx`) fires on
  this canvas's type-picker too, same as the standalone page and the plain
  Toolkit canvas — exclude from any "no new console errors" assertion here.

## In-chat "Edit table" content-canvas (ELITEA-2086 — full findings)

A **completely different canvas component** from every other canvas
documented above (Agent/Toolkit/MCP/Pipeline entity-creation canvases all
compose `AgentEditor.jsx`/`ToolkitEditor.jsx` in the same right-side slot).
This one is `CanvasEditor.jsx` + `CanvasEditHeader.jsx`
(`src/pages/NewChat/`) — it edits MESSAGE CONTENT (a code block, an
AI-generated markdown table, a mermaid diagram, or the whole AI response),
opened via a per-content-type pencil/edit icon rendered directly in the
message bubble (`MarkdownTableBlock.jsx` for tables, `CodeBlock.jsx` for code
blocks — same toolbar pattern, both call the same `onEdit` prop up to
`CanvasEditor`). **Zero testids exist anywhere in this whole component
tree** — confirmed via full-file reads of `MarkdownTableBlock.jsx`,
`CanvasEditHeader.jsx`, `CanvasEditor.jsx`, `MarkdownTableEditor.jsx`,
`SplitButton.jsx`, and the sibling `CodeBlock.jsx` — not tracked tech debt,
genuinely virgin ground, first case to touch it.

- **The canvas header (`CanvasEditHeader.jsx`) is SHARED across 4 content
  modes** and its title text changes accordingly: `"Edit response"` (whole
  AI message, `isBlock: false`), `"Edit code"` (generic code block),
  `"Edit table"` (markdown table — this case), `"Edit diagram"` (mermaid).
  Name any testid on this header GENERICALLY (`canvas-edit-header-title`,
  not `table-canvas-title`) — a future case touching another mode reuses the
  SAME testid, only the asserted text differs.
- **Opening the canvas is NOT a navigation** — confirmed live, the URL
  (`/chat/{id}?name=...`) is byte-identical before and after clicking the
  edit icon. It's a pure client-side state change (`selectedCodeBlockInfo`
  passed down from the message-list component); wait on the canvas header
  text becoming visible, not on any URL/network event.
- **The original message's content swaps to an `EditingPlaceholder`
  ("Table editing...") while its canvas is open** (`isBlockEditing` gate in
  `MarkdownTableBlock.jsx`, keyed by `canvasId`/`blockId` via
  `useCheckIsBlockEditing` from `CodeBlock.jsx`) — confirmed live. Useful
  regression guard: the message area shouldn't show a duplicate/stale table
  while the canvas edits it.
- **MUI X DataGrid virtualizes off-screen rows** (`MarkdownTableEditor.jsx`)
  — even though the pagination footer reads "1–10 of 10", only ~9
  `.MuiDataGrid-row` elements exist in the DOM at any one scroll position.
  Never assert an exact rendered-row-element count as the logical row count;
  read the pagination footer text instead.
- **Pagination footer text uses an EN DASH, not a hyphen**: MUI's
  `MuiTablePagination-displayedRows` renders `"1–10 of 10"` (U+2013) — a
  literal ASCII-hyphen `"1-10 of 10"` string match will NEVER succeed. Same
  trap for any other MUI `TablePagination` instance in the app, not just
  this canvas.
- **`.MuiDataGrid-columnHeader button` double-counts** — each column header
  renders TWO buttons: the app's own custom sort `IconButton`
  (`ColumnHeader` component in `MarkdownTableEditor.jsx`, wraps
  `SortUpwardIcon`, parent class `MuiBox-root`) AND MUI's own native
  `.MuiDataGrid-menuIcon` column-menu button (hover-reveal, but still present
  in the DOM / matched by `offsetParent !== null`). A broad
  `.MuiDataGrid-columnHeader button` selector returns 2× the real sort-icon
  count (10 vs. the actual 5 data columns, this run). Scope tightly to the
  app-owned sort button only once it has a testid
  (`canvas-table-column-sort-button`, needs-adding).
- **Row-selection checkboxes are `@mui/x-data-grid`-internal, not app JSX**
  (`GRID_CHECKBOX_SELECTION_COL_DEF`, imported straight from the library) —
  same reasoning shape as `#579`'s "third-party widget subtree" exception
  (ReactFlow's `rf__wrapper` is the canon's own worked example) even though
  the canon doesn't explicitly name `@mui/x-data-grid`. Declared as a
  scoped-raw-handle improvisation in ELITEA-2086's AFS, chained off the
  REAL `canvas-table-editor` testid parent — never a free-floating handle.
  Same reasoning would apply to the pagination footer's internal DOM, but
  that assertion doesn't need a selector at all (see next bullet).
- **Prefer a single `.inner_text()` content read over chained selectors for
  MUI-internal text** (pagination footer, "Rows per page:" label): call
  `.inner_text()` directly on the real `canvas-table-editor` testid field
  and assert substrings on the returned string — no `.locator()`/
  `.get_by_text()` chaining, so the raw-handle question doesn't even arise.
- **LLM table-generation content is non-deterministic** — column
  names/count and exact company data vary run-to-run (this run: `Rank`,
  `Company`, `Headquarters`, `Primary Business Areas`, `Notable
  Products/Services` — 5 data columns, 10 rows). Automate against
  structural properties (pagination-derived row count, an any-of match on a
  short known-values list) rather than a hardcoded column/value set — a
  case's own "such as"/"e.g." wording in its expected results is usually the
  tell that the author already knew this.
- **`SplitButton.jsx` (shared component, `src/components/`) has TWO call
  sites for "Download as xlsx"**: the message-toolbar copy
  (`MarkdownTableBlock.jsx`, pre-edit) and the canvas copy
  (`MarkdownTableEditor.jsx`, this case's step 11). No testid/prop exists on
  either yet — needs a `testId` prop threaded per call site
  (`canvas-table-download-button` for the canvas one this case touches;
  leave the message-toolbar one for whichever future case touches THAT
  button, per the scope-only-what-you-touch rule).
- **No network call fires when the canvas opens** — confirmed via
  `get-network --status error` and a full request list, both empty on the
  edit-icon click. Table generation itself is the ordinary WebSocket
  chat-predict path (`.agents/testing.md`'s standard ~2s+ wait), not a
  dedicated "generate table" endpoint — the table is just markdown that
  happens to parse into a grid.

## In-chat "Build with AI" (Agent) — ELITEA-2073 full findings

- **The Build-with-AI modal is the SAME shared component/testids** whether
  opened from the standalone `/agents/create` page (merged
  `test_agent_build_with_ai.py`, ELITEA-1907/1909/1911/1915) OR from the
  in-chat "Create New Agent" canvas (`AgentEditor.jsx` →
  `CreateAgentForm.jsx` → `GenerateAgentButton` — same component tree,
  `entityType !== 'pipeline'` is the only gate). Every `generate-agent-*`
  testid (`generate-agent-open-button`, `-modal`, `-prompt-input`,
  `-cancel-button`, `-submit-button`, `-loading-indicator`,
  `-back-button`, `-approve-button`) is already **on-main ✓** and resolves
  identically in both contexts — confirmed live. `GenerateAgentModalPage`
  is reusable as-is in the chat-canvas context; no new testid work needed
  for the modal itself.
- **"Create Agent" performs a REAL backend save even from the chat
  canvas** — don't assume it's a local-only draft populate.
  `GenerateAgentModal.jsx`'s `handleApprove` always calls the real
  `POST .../applications/prompt_lib/{project_id}` (same endpoint/contract
  the standalone-page merged suite already asserts `201` on); only the
  POST-creation side effect differs via `onAgentCreated` — standalone page
  navigates to `/agents/all/{id}`, chat canvas instead populates the LOCAL
  Formik view of the ALREADY-SAVED entity in place (confirmed live via a
  follow-up `GET .../applications/...?name=...` query — the entity is
  immediately queryable) and auto-attaches it as a conversation participant
  (visible under PARTICIPANTS → AGENTS). This is why the canvas's Save
  button reads `disabled === true` immediately after — there's nothing left
  to save.
- **Cancel resets the modal's local state completely** — reopening after a
  Cancel shows an EMPTY prompt textarea (confirmed live), and zero
  `generate_application_draft` network requests fire between typing and
  Cancel (confirmed via full network-log inspection — the strongest
  available proof of "no generation took place").
- **A previously-undocumented testid**: `chat-agent-settings-menu-button`
  (on `automation/testids` only, `AgentEditorPanel.jsx:281`) — a single
  stable testid whose CONTENT (not value) toggles between a settings-gear
  icon and "Editing…"/"Viewing…" text, based on
  `isActiveParticipantBeingEdited`/`canEdit`. This is DIFFERENT from
  ELITEA-2166's CLARIFICATION #709 finding (`chat-switch-participant-button`
  itself shows "Editing…" as a placeholder in the MANUAL-fill flow, because
  no real agent exists pre-Save there) — in the Build-with-AI flow the real
  agent already exists, so `chat-switch-participant-button` shows the REAL
  name/version AND this separate badge shows "Editing…" simultaneously.
  Don't conflate the two patterns; check which flow (manual-fill vs.
  Build-with-AI) a future case is testing before reusing either assertion.
- **Review-form fields (`GenerateAgentReviewForm.jsx`: Name/Description/
  Instructions/Welcome Message/Conversation Starters) still have ZERO
  testids** on either branch (re-confirmed this session, `git grep -i
  "testId\|data-testid"` → no hits) — a pre-existing gap first flagged by
  ELITEA-1915's AFS as out-of-scope there. Still not blocking for
  content-only assertions (read the modal's aggregate `.text_content()`),
  but a future case that EDITS review-form fields before approving will
  need `add-data-testid` here.
- **[INFO] Issue #1050** — React "does not recognize the `disableUnderline`
  prop" console warning fires whenever `GenerateAgentReviewForm.jsx`'s Name
  field renders, traced to the shared `InputBase.jsx` unconditionally
  forwarding `disableUnderline` regardless of `variant` (only valid for the
  `standard` MUI variant, not `outlined`). Cosmetic/dev-mode-only, no
  functional impact — likely reproducible on ANY `Input.InputBase` caller
  using the outlined variant, not just this form.
