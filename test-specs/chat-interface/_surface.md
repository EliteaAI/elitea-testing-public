# Chat-interface surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Chat surface (`/chat`).
Not a substitute for execution — verify a handle as you use it. One writer at
a time; last confirmed by: qa-engineer analyst, ELITEA-2218, 2026-08-03
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: ELITEA-2211..2215 cluster run, 2026-08-03).

## Context Management / Auto-Summarization — settings location, autosave defect (ELITEA-2218)
- **Global settings moved**: Context Management + Automatic Summarization now
  live at `/settings/memory` (tab id `memory`), NOT `/settings/personalization`
  (that route 404s via `SettingsRedirect.jsx` — `personalization` isn't in its
  `VALID_TABS` list). `UserProfileSettingsPage.navigate_to_profile()` still
  points at the dead route — fix before reuse.
- **CONFIRMED DEFECT, filed #1129**: on `/settings/memory`, the THREE numeric
  fields (Max Context Tokens, Preserve Recent Messages, Target Summary
  Tokens) do not autosave — typed value shows on-screen, zero network calls
  fire on blur, value reverts on reload. Toggle controls on the SAME form
  (Context Management toggle, Context Editing toggle) autosave correctly
  (`PUT /api/v2/social/author/`, confirmed persists). Root cause:
  `useFormikAutoSaveOnBlur` (blur+dirty gated, in `MemoryFormContent.jsx`) vs
  the toggles' `onChange` handlers calling `onAutoSaveRequested()` directly —
  the three numeric fields' `onChange` handlers (`handleNumericInputChange`,
  `handleMaxTokensChange`) never call `onAutoSaveRequested()`. Do not use
  these fields to configure a custom threshold; use the per-conversation
  "Edit context settings" modal instead (below), or accept the default
  (confirmed live: 10,000 tokens).
- **Context Management + Automatic Summarization are ON by default** for a
  fresh session/user (`context_enabled: true`, `enable_summarization: true`
  confirmed via both the settings form and a new conversation's
  `meta.context_strategy.enabled: true`).
- **Missing testids** (none of these have `data-testid` in source, confirmed
  via file read of `MemoryContextManagement.jsx`/`MemorySummarization.jsx`):
  Automatic Summarization toggle, Summarization Instructions textarea, Target
  Summary Tokens input. Also the Preserve Recent Messages input — the
  existing `UserProfileSettingsPage.preserve_recent_messages_input` field
  CLAIMS `testid="preserve-recent-messages-input"` but this does not exist in
  source (dead/aspirational testid, existing tech debt, uses a forbidden
  `fallback=`).
- **Context Budget panel (chat side) is behind a COLLAPSED-by-default
  Participants panel** — must call `ChatPage.expand_participants_panel()`
  first (existing method; a from-scratch reimplementation of its click
  heuristic did not reproduce the same result on the first try in this
  session — reuse the merged method, don't re-derive).
- **"Edit context settings" per-conversation modal** (`context-settings-button`,
  opens `ContextStrategyModalContent`) has its OWN explicit Save button +
  `submitForm()` — a DIFFERENT code path from the broken global-settings
  blur-autosave. Source-reviewed only (not click-verified this session) as
  the recommended path to set a custom low threshold without hitting #1129.
  **None of this modal's fields or its Save button have a `data-testid`
  either** (confirmed via file read — zero hits) — needs `add-data-testid`
  work across the board if this path is used.
- **Not reached live this session** (time budget, after isolating #1129): the
  actual max-token summarization trigger, the "Summarizing the chat history"
  indicator (no handle found anywhere in `chat_page.py` or discovered live),
  and the warning-state affordance near the token bar as it approaches max.
  First implementer pass on ELITEA-2218 should confirm these.

## File attachments — 10-file limit, unsupported-type rejection, toast severity (ELITEA-2197/2200)
- **The real "Attach Files" control lives INSIDE the "+" (plus-menu) popper,
  not as a standalone visible button.** `ChatPage.attach_files_button`
  (`automation/pages/chat_page.py:55-58`, `testid="chat-attach-button"`) is
  **dead — that testid does not exist anywhere in `EliteaUI/src`** (confirmed
  `git grep` against both `origin/main` and `origin/automation/testids`, zero
  hits); the field only "works" today via its (forbidden-in-new-code)
  `fallback=`. Reach the real control via: click `[data-testid="plus-menu-button"]`
  (pre-existing, on-main) to open the popper, then click the "Attach Files"
  row inside it (`button[aria-label="attach files"]` — 2nd match of that
  selector on the page; the 1st match, bbox `28×28` at the composer's bottom
  toolbar, is a separate, functionally-hidden `AttachmentButton` instance
  with `pointerEvents:none` — do not target it).
- **`AttachmentButton` (`PlusChatButton.jsx`) renders THREE times**: (1)
  hidden/`pointerEvents:none` instance at `PlusChatButton.jsx:336` (ref'd,
  never click-targeted), (2) the real popper item at `PlusChatButton.jsx:373`
  (`showLabel`, text = `"Attach Files\n{N} left"`) — THIS is what
  ELITEA-2197/2200 touch, (3)+(4) separate instances in `UserMessage.jsx`
  (edit mode) and `NewChatInput.jsx` — not explored this pass. Needs a
  `testId` prop threaded through the shared component, set ONLY at the
  popper call site (`chat-attach-menuitem-button`) — per the shared-component
  testid rule, don't hardcode a feature name inside `AttachmentButton` itself.
- **The popper does not auto-close after a file-chooser selection.** Its
  `isOpen` state persists across the native OS dialog. A second click on
  `plus-menu-button` right after selecting files **toggles it CLOSED**
  (don't re-click to "confirm" the menu is still open — just re-query the
  existing, still-open popper's elements).
- **The "Attach Files" popper item becomes `disabled` once `attachments.length
  >= 10`** (`isAtMaxCapacity` in `AttachmentButton.jsx`), showing
  `"Attach Files\n0 left"`. A disabled MUI button never fires `onClick` — no
  file picker, no toast. This means the case-text flow "attach 10, then
  separately attempt an 11th" is **unreachable** live — filed as a
  clarification, issue #1122. The `toastWarning`
  (`"You've reached the {N}-file limit. Only the first {N} will be
  processed."`) only fires from `validateAttachmentFiles()`'s count check
  **inside a single file-chooser selection** that itself exceeds remaining
  capacity (e.g. select 11 files in ONE action when 0 attached, or select 2
  when 9 are already attached) — confirmed live: selecting 11 `.txt` files at
  once correctly triggers the warning and keeps exactly the first 10
  (selection order, `fileArray.splice(allowedCount)`).
- **`FileList.jsx` (`EliteaUI/src/components/Chat/FileList.jsx`) renders the
  attachment chips — ZERO testids anywhere in this component** (confirmed via
  full-file read, not just grep). Per-chip `Box` (no testid), its remove (X)
  icon (no testid), the `"+N"` overflow `Button.BaseBtn` (no testid,
  `aria-label="Show more files"`), and the overflow `Menu`'s per-item
  `MenuItem`s (no testid, **not** `keepMounted` — items only exist in the DOM
  while the overflow menu is open) all need `add-data-testid` work. The
  visible-vs-overflow split is **container-width-dependent**
  (`useGetComponentWidth` + `Math.floor(availableWidth / 208)`, confirmed
  live: `1700px`-wide viewport → 4 visible + `"+6"` overflow for 10 total) —
  automation must assert the SUM (visible + parsed overflow number), never a
  hardcoded "N visible" count.
- **Toast severity/dismiss have no testid either** (`EliteaUI/src/components/Toast.jsx`).
  `[data-testid="toast-message"]` (pre-existing, on-main) covers only the
  message TEXT node — the outer `Alert` (which carries `severity` as a CSS
  class, e.g. `MuiAlert-colorWarning`/`MuiAlert-colorInfo`) and its
  auto-rendered MUI default close button (`aria-label="Close"`, from the
  `onClose` prop) both need new testids: `toast-alert` +
  `data-severity={severity}` on the `Alert` (state-via-`data-*` on a stable
  identity, matching this project's own established pattern), and
  `toast-dismiss-button` via a custom `action` prop (MUI's default close
  icon has no prop path for a testid without one).
- **CONFIRMED DEFECT, filed #1121**: the unsupported-file-type toast
  (`"Invalid file types detected: {file} ({ext}). Only {allowed} files are
  allowed."`) renders with `severity="info"` (blue, info icon) — NOT an
  error-level severity, despite the feature's own naming and the case's
  "error banner" framing. Root cause: `AttachmentButton.jsx`'s
  `displayErrorMessages()` calls `toastInfo(...)` for the invalid-type
  branch while its sibling 10-file-limit branch (same function) correctly
  uses `toastWarning(...)`. Message text/dismiss/non-attachment are all
  correct — only the severity color/icon is wrong.
- **Allowed extensions are backend-driven and dynamic** (`useAllowedExtensions()`
  → `GET` document-loaders query) — don't hardcode the full list in an
  assertion; match the toast's stable prefix/suffix instead (`"Invalid file
  types detected: {file} ({ext}). Only "` … `" files are allowed."`).
- **Non-attachment check ordering matters**: the rejected-file toast's own
  message TEXT contains the filename substring, so a naive
  `page.get_by_text(filename)` "not attached" check will false-positive
  while the toast is still open. Dismiss the toast first, then check.

## Users participant type — mention, removal, avatar overflow (ELITEA-2168)
- **"All users" dropdown footer item is BROKEN — filed #1119.** Clicking it
  inserts nothing into the composer and a follow-up send goes through the
  normal LLM path (message count +2, not +1). Root cause: `DropdownFooter.jsx`
  passes the literal string `'All users'` into `ChatBox.jsx`'s
  `onSelectParticipant`/`NewChat.jsx`'s `onSelectThisParticipant`, which
  expects a real participant object and has no `@everyone` special case (that
  only exists in `onSelectUserMention`, the handler for the COMPOSER'S OWN
  typed-`"@"` popper). **Working alternative, confirmed live**: type `"@"` in
  the composer, select "Everyone" from `UserMentionList` — inserts
  `"@Everyone "` correctly and correctly suppresses the LLM response.
- **Individual user mention DOES work both ways**: clicking a user's row in
  the participants dropdown inserts `"@Name "` into the composer (confirmed
  live) — same mechanism as typing `"@"` and picking that user from
  `UserMentionList`.
- **"No LLM response" is a structural, not timing, fact.** `isSendingToUser`
  sends (to one user or `@everyone`) never create an assistant-message
  placeholder at all (`initializeNewMessages()` in
  `src/common/initializeNewMessages.js`) — assert via message-count delta
  (+1, not +2), never a timed "nothing appeared" wait.
- **Composer's typed-`"@"` mention popper (`UserMentionList`/
  `UserMentionItem`) has ZERO testids anywhere** — needs
  `chat-user-mention-list` (container) + `chat-user-mention-item-{id}`
  (dynamic; the "Everyone" row's id is the literal string `@everyone`).
- **"Users" dropdown rows (`UserMenu.jsx`) have no per-row testid** — unlike
  `ParticipantItem.jsx` (Agents/Pipelines/Toolkits/MCP), which already carries
  `chat-participant-row-{uniqueId}`. Needs
  `chat-participant-row-user_{userId}_{projectId}` (same
  `getChatParticipantUniqueId()` shape) so the already-existing, already-
  shared `chat-participant-remove-button` can be scoped to one specific row.
  The "Remove user?" confirm dialog itself is the SAME shared
  `Modal.DeleteEntityModal` agent-removal already uses — no new dialog handle
  needed, `components.mui.Dialog` works as-is.
- **Residual-hover gotcha reproduces for user rows too** (previously only
  documented for `remove_agent_participant()`): after confirming a removal,
  `page.mouse.move(0, 0)` before hovering the NEXT row is needed or the
  delete icon may not reveal (same fix, same root cause: a lingering
  real-mouse `:hover` on the now-gone element).
- **"Add users" modal chip delete icon has no testid.** Each chip
  (`add-users-chip-{userId}`, pre-existing) has a nested untestid'd
  `<svg class="MuiChip-deleteIcon">` — needs
  `add-users-chip-remove-{userId}` (dynamic). Clicking it removes the chip
  from the pending selection (never exercised by ELITEA-2167, which only
  ever adds chips, never deselects one before confirming).
- **Blind-Escape trap on `click_add_users_confirm()` after a chip removal.**
  That helper unconditionally presses `Escape` first to close a results
  popper — fine after a fresh option SELECTION (a popper is genuinely open),
  but if the immediately-prior action was a chip DELETION (no popper open at
  that point), the same `Escape` instead closes the whole "Add users" dialog,
  discarding the selection. Click `add_users_confirm_button` directly in that
  sequence instead.
- **Expanded USERS section (5-avatar + "+N" overflow)** — separate component
  (`ExpandedParticipantsList.jsx`) from the collapsed badge
  (`CollapsedPerticapantsList.jsx`); only visible once the Participants panel
  is expanded, and needs > 5 total "users"-type participants to show the
  overflow. `usersToDisplay = users.slice(0, componentWidth <= 200 ? 3 : 5)`,
  overflow text = `` `+${users.length - usersToDisplay.length}` `` (no
  testid on the overflow `Typography` — needs
  `chat-participants-users-overflow-count`). Avatar itself already has
  `chat-participants-users-avatar` (pre-existing).
- **Expanding the panel HIDES the collapsed-badge testid entirely** — while
  expanded, `chat-participants-badge-users` (and its nested `-button`) is not
  rendered at all (`ExpandedParticipantsList.jsx` doesn't emit it), so any
  `get_participants_badge_count()`/`open_participants_popover()` call after
  expanding will time out until the panel collapses back.
  `collapse_participants_panel()` (legacy raw-JS heuristic) FAILED live this
  session (`expand_participants_panel()` worked); `page.reload()` is a
  working interim fallback. The panel's own expand/collapse `IconButton`
  (`Participants.jsx`) has NO testid — needs
  `chat-participants-panel-toggle-button` with a `data-expanded` state
  attribute (testid=identity/state=data-* ruling), since this case's own
  steps directly depend on the toggle, not just incidental exploration.
- **Live user roster for search** (client-side substring filter, confirmed
  this session): `Hrach Sargsyan`, `Levon Dadayan`, `Mariam Hakobyan`,
  `Tatiana Bontsevich` (same four ELITEA-2167 already uses), plus
  `Daniyar Chambylov`, `Ihar Bylitski` (new this session) — six distinct
  users now confirmed live in this environment, enough to exercise the
  5-avatar-plus-overflow case without reusing the same four names twice.

## Conversation context menu — "Move to" submenu (ELITEA-2135/2137)

## Conversation context menu — "Move to" submenu (ELITEA-2135/2137)
- **CONFIRMED DEFECT, filed EliteaAI/elitea-testing-public#1117**: the "Move
  to" menu item's submenu (Create folder / Back to the list / existing
  folders) does NOT open reliably. Hovering it (even real mouse movement +
  1.5s dwell, 0/2) and keyboard `ArrowRight` (0/1, after `ArrowDown`×2 focus)
  never open it. A plain click — the item's own coded activation gesture
  (`ConversationItem.jsx`: `hasSubMenu: true`, `DotMenu.jsx`'s
  `BasicMenuItem`: `onClick={subMenuItems?.length ? onClickMenu : onClick}`)
  — opened it on the first attempt in roughly half of ~6 isolated repros and
  needed a second click the rest of the time; clicking again while it IS
  open closes it (backdrop click-away). **Automation workaround**: click,
  poll for `.MuiPopover-root` count to go 1→2 (or for
  `chat-move-to-create-folder-menuitem` to become visible) within ~350ms,
  retry the click if not — reaches the open state reliably within 1–2
  attempts every time. See `ChatPage.open_move_to_submenu()` (specced,
  ELITEA-2135's AFS).
- Submenu items previously rendered ZERO testids regardless of `key` — a
  SEPARATE, purely cosmetic gap from the defect above: `DotMenu.jsx`'s
  `BasicMenuItem` nested-submenu rendering (`subMenuItems.map(...)`) never
  forwarded `testId` to `subCommonProps` at all. Fixed this pass (commit
  `cf348d32`, `automation/testids`): `chat-move-to-create-folder-menuitem`,
  `chat-move-to-back-to-list-menuitem`, `chat-move-to-folder-{folder_id}-menuitem`
  (dynamic, one per existing folder — the `folderItems.map()` call in
  `Conversations.jsx` had NO `key` field at all before this pass, which ALSO
  meant two same-named folders — e.g. two default-named "New folder"s —
  collided on React's fallback key (`subMenuItem.key || subMenuItem.label`),
  producing a live-confirmed "two children with the same key" console
  warning; fixed by the same `key` addition).
- Toast on move: `Chat moved to "${targetFolder.name}" folder successfully`
  (source: `useMoveToFolderConversation.hooks.js`) — WITH quote marks around
  the folder name; the case texts' paraphrase ("Chat moved to [folder name]
  folder successfully") omits them — cosmetic case-text drift, not a defect.
- "Move to" is DISABLED while the conversation is pinned
  (`ConversationItem.jsx`: `disabled: isPinned || ...`) — a pin/move-to test
  pairing needs an UNPINNED conversation.
- "Move to" > "Create folder" seeds a CLIENT-SIDE-ONLY placeholder folder
  (`isNew: true`, default name "New folder") the instant it's clicked; the
  REAL server-side folder + the actual conversation move only happen on
  confirm (`moveTargetConversationToNewFolder()`: `createFolder()` THEN
  `onMoveToFolderConversation()`) — same two-phase shape ELITEA-2132 already
  documented for the CHATS-header create-folder button, but this entry
  point's confirm ALSO moves a conversation in the same action (and DOES
  show a toast) — the two "Create folder" entry points are similar-looking
  but functionally different flows, don't conflate them.

## Pin conversation (ELITEA-2149)
- `chat-conversation-menu-pin-menuitem` (pre-existing, ELITEA-2114) — single
  click, no submenu, NOT affected by the "Move to" defect above (0 flake
  across every repro this pass).
- "Pin on top" is DISABLED when the conversation is already inside a folder
  AND not currently pinned (`disabled: !isPinned && !!conversation.folder_id`)
  — pin tests need an conversation that's NOT inside a folder.
- ADDED this pass (commit `cf348d32`): `data-pinned="true"/"false"` on
  `chat-conversation-item-{id}` (mirrors the pre-existing `data-active`
  attribute, ELITEA-2114); `chat-pin-icon` testid on the inline `PinIcon`
  usage inside `ConversationItem.jsx` (conditionally rendered
  `{isPinned && !isPlayback && <PinIcon .../>}` — confirmed live 0→1 count
  transition on pin, not a static/always-present icon).
- Panel order (source-confirmed, `Conversations.jsx`'s literal JSX order):
  pinned folders → `<PinnedConversations>` → unpinned folders →
  date-grouped/ungrouped conversations. Live-verified 2 of these 4 tiers
  (pinned conversation Y=56, well above "Today" heading Y=178–260 across
  repro runs) — a full 4-tier live check needs a seeded pinned FOLDER, which
  no case so far has needed; flagged as a follow-up opportunity, not done.
- No success toast on pin (`usePinConversation.hooks.js`'s
  `onPinConversation` only calls `toastError` on FAILURE) — don't wait for
  one.

## Conversation search (ELITEA-2162)
- `conversation-search-button` (on-main) opens `conversation-search-input`
  (on-main) + an X/clear icon — but the folder/date-group list is **not**
  replaced on click alone; it stays visible until a query is actually typed
  (500ms debounce). Case text sometimes implies immediate replacement — it
  isn't (issue #1114).
- The X/clear icon (`IconButton onClick={handleSearchClear}` in
  `Conversations.jsx`) has **no testid** — needs `add-data-testid`
  (`conversation-search-clear-button`).
- Filtering is server-driven: `GET /elitea_core/folder/prompt_lib/{projectId}
  ?...&query=<value>&grouped=true`, case-insensitive substring match on
  conversation name. Matching rows get testid
  `chat-conversation-item-{conversation.id}` — **on `automation/testids`
  only**, not yet on `main` as of 2026-08-03.
- Clicking a result: URL becomes `/chat/{id}?name=<name>`, search input stays
  visible (doesn't auto-close).

## Modules panel / internal tools toggle (ELITEA-2162)
- `plus-menu-button` (on-main) → **hover** (not click) the `Modules`
  menuitem, testid `internal-tools-menuitem` (on-main; same-element
  conditional pair, `undefined` on the unused branch — compliant #277
  shape (a)). Existing `ChatPage.internal_tools_menuitem` field uses a raw
  `has-text("Modules")` locator instead of this testid — pre-existing tech
  debt, worth fixing when next touched.
- 7 toggle switches render (`role="switch"`, MUI `Switch.BaseSwitch`), each
  with **zero testid** — only locatable via accessible name (`label` prop =
  the tool's `title`). Stable underlying keys (from
  `internalTools.constants.js`): `image_generation`, `data_analysis`,
  `internal_mcp`, `planner`, `pyodide`, `swarm`, `lazy_tools_mode`. Needs
  `add-data-testid` with a dynamic pattern: `modules-toggle-{tool_key}`.
- Toggling any switch PUTs `meta.internal_tools` via
  `useConversationEditMutation` (same endpoint family as
  `ConversationAPI.rename_conversation`), then shows the app-wide
  `toast-message` toast with text **`"Modules configuration updated"`**
  (lowercase "u" — case text across ELITEA-2162/2464 says "Updated", issue
  #1115).
- **`Escape` does NOT close the panel** (live-confirmed: switch count stayed
  at 7 after `Escape`). Closing requires an outside click (anywhere in the
  main chat/message area) — that took the switch count to 0.

## Slash-mention ('/') toolkit/MCP picker (ELITEA-2202/2203/2204)
- Component tree: `SlashSuggestionList.jsx` (`EliteaUI/src/[fsd]/features/chat/ui/slash-suggestion-list/`)
  renders `NewParticipantList` (`EliteaUI/src/pages/NewChat/Recommendations/`,
  **shared** with `RecommendationList`/`SearchResultList`) for the toolkit-pick
  phase, and its own `ToolList`/`ToolItem` (NOT shared elsewhere — confirmed via
  `git grep -rl "ToolList"` inside `src/`) for the tool-pick phase. **Every one
  of these 4 files has ZERO testids** — confirmed via full-file read AND
  `git grep -c "data-testid\|testId"` returning empty for all four against both
  `origin/main` and `origin/automation/testids`.
- Trigger: typing `/` as the first character of an empty composer (via
  `chat-message-input`, pre-existing on-main) opens the picker. Dropdown title
  DOM text is title-case `"Mention Toolkit or MCP"` (CSS-uppercased on screen to
  "MENTION TOOLKIT OR MCP" — assert the title-case string, not the visual caps).
  Empty-state body text (zero toolkit/MCP participants): exact string
  `"No matching results"`.
- Closes via **outside click** (`ClickAwayListener`, confirmed live). Do **not**
  use `Escape` — same architecture as the Modules panel documented above, which
  is live-confirmed NOT to close on `Escape`; not independently isolated for
  THIS popper, but the shape is identical, so treat as the same quirk.
- Only conversation **participants** of type Toolkit/MCP ever appear
  (`filteredParticipants` filters `activeConversation.participants` client-side
  — a toolkit that exists in the project but isn't a participant never shows).
- Selecting a toolkit: composer becomes `/{toolkit_name}` (no trailing space),
  and a SECOND list appears titled `` `{toolkitName} available tools` `` (DOM
  text lowercase, CSS-uppercased on screen), populated from
  `toolkitDetails.settings.selected_tools` (non-MCP) or
  `settings.available_mcp_tools` (MCP) — i.e. whatever `selected_tools` the
  toolkit was CONFIGURED with, not a fixed list. `useToolkitsDetailsQuery` has a
  brief `isToolsFetching` loading state before the list renders.
- Selecting a tool: composer becomes `/{toolkit_name}/{tool_name} ` — **WITH a
  trailing space** (`onSlashCommitMention`'s replacement is
  `` `${mentionToken} ` ``) — assert the trailing space, it's the confirmed
  mechanism, not incidental whitespace.
- **Add-participant mechanism differs from the AGENT flow** (existing
  `ChatPage.add_toolkit_participant()`, `chat_page.py:3910-3952`, is NOT
  reusable here): Toolkits/MCPs entries in the plus-menu (`toolkits-menuitem`/
  `mcps-menuitem`, both **on-main**) render as **toggle switches**
  (`showToggle: true` in `PlusChatSubmenu.jsx`) — clicking a row toggles
  participant membership WITHOUT closing the submenu (contrast with Agents'
  select-and-close). The search inputs (`{section}-search-input`) and per-row
  items (`` `${sectionKey}-menu-item-${item.key}` ``, live-confirmed concrete
  shape: `toolkits-menu-item-toolkit-{project_id}-{toolkit_id}` /
  `mcps-menu-item-mcp-{project_id}-{toolkit_id}`) are all real testids —
  **on `automation/testids` only**, commit `73595e8d` ("add data-testid for
  plus-menu entity items/rows (ELITEA-2094)"), not yet on `main`.
- **Quirk, confirmed live**: closing the plus-menu popper (`Escape`) and
  re-clicking `plus-menu-button` to switch from the Toolkits submenu to the
  MCPs submenu **toggles the whole popper CLOSED** instead of reopening it —
  same "second click on an already-open popper closes it" shape already
  documented above for the Attach-Files popper. Fix: go directly from Toolkits
  to MCPs by clicking `mcps-menuitem` within the SAME already-open outer
  popper (these top-level items are `onMouseEnter`-triggered, and Playwright's
  `.click()` hovers first, so a plain `.click()` on `mcps-menuitem` works
  without needing to reopen anything).
- `mcps-menuitem`'s visibility is gated by `useIsMcpVisible()` (platform
  settings `mcp_exposure_enabled`/`mcp_in_menu_enabled`) — confirmed live via
  `GET /elitea_core/platform_settings/prompt_lib`: both `true` in this
  environment.
- **CLARIFICATION filed, issue #1125**: ELITEA-2204's case text names an
  expected tool `list_collections`, which is not a valid tool name in this
  environment (backend rejects it — corroborated by a pre-existing error
  already in this repo's own `automation/reports/archive/junit_20260722_212653.xml`,
  from before the suite's `create_artifact_toolkit()` factory was fixed). The
  live, correct tool name for the same capability is `list_indexes`.
- Icon differentiation per participant type (`EntityIcon.jsx`) has real,
  different SVG components per type but **zero testids on any of them** — out
  of scope to testid (shared across many unrelated call sites); the type-label
  TEXT ("Toolkit"/"MCP"/"agent"/"pipeline", `NewParticipantCard.jsx`'s
  `participant.type` ternary) is the practical, in-scope assertion signal
  instead.
- **Environment note (569+ stale artifact buckets already present)**: this
  project's `/artifacts/buckets/default/{project_id}` list already carries
  500+ `autotest-*` buckets from prior sessions before this pass added one more
  — `ArtifactAPI.delete_bucket()` 404'd on both the plain-name and compound-ID
  URL forms for a bucket created and confirmed-existing minutes earlier in the
  SAME session (toolkit cleanup via `ToolkitAPI.delete_toolkit()` succeeded
  fine). Not independently root-caused this pass (pre-existing, wide-spread
  pattern, not a new regression) — flagging for whoever next does bucket
  hygiene, not filed as a defect.

## Sibling TMS cases — near-duplicate scope
ELITEA-2463 (search) and ELITEA-2464 (Modules panel) are both still
`draft`/unautomated (tracking cards #971/#972) and are, respectively, a more
granular breakdown of ELITEA-2162's steps 1–4 and 5–9. Once ELITEA-2162's
spec merges, both should very likely resolve `already-covered` /
`extend-existing` against it — sequence their analysis after this one lands.

## Streaming / in-progress response widget (ELITEA-2181)
- The "loading indicator" shown between Send and content-arrival is
  `RotatingMessages.jsx` — text-cycling placeholder ("Waking the agent…", …),
  NOT a `CircularProgress` spinner. No testid.
- Once content starts, a "Thought for `<n>` secs" accordion
  (`ApplicationThinkView.jsx` → `ActionView.jsx`) carries the model-name chip
  AND the "Pause scroll"/"Resume scroll" toggle — both scoped to that
  accordion, not the message bubble or page level. Neither has a testid.
  Clicking the toggle flips its own label (confirmed) — that's the stable
  automation signal, not a scrollTop delta (only proves out when the
  conversation's content genuinely overflows the viewport).
- Message action icons (Read-out/speaker, Copy, Regenerate, Delete) only
  render **on hover** over the message block. Confirmed testids:
  `chat-read-out-button`, `chat-delete-button` (both on `main`). Copy has
  NO testid but does get an MUI-auto-injected `aria-label="Copy to
  clipboard"` (its `StyledTooltip` wraps the `IconButton` directly).
  **Regenerate has NEITHER testid NOR aria-label** — its `StyledTooltip`
  wraps a bare `<Box>`, breaking MUI's auto aria-label injection. The page
  object's existing `copy_message_button`/`regenerate_button`
  `LocatorDescriptor`s reference stale, nonexistent testids
  (`message-copy-button`/`message-regenerate-button`) — pre-existing tech
  debt (not introduced by ELITEA-2181), still functioning today only via
  their `fallback=` role/aria-label lookups. Don't reuse those dead names
  when adding real testids — follow the live sibling convention instead
  (`chat-copy-button`/`chat-regenerate-button`).
- The last message's `Answer` block carries a **same-element,
  state-conditional testid** (`ApplicationAnswer.jsx:640`):
  `data-testid={isLastMessage ? 'skill-test-last-response' :
  'chat-answer-content'}` — pre-existing tech debt (not this case's
  anti-pattern to fix). For any single-exchange test the value will be
  `skill-test-last-response` (misleadingly named — unrelated to Skills).
  Scope through the parent `chat-message-item` container instead of either
  literal string.
- This environment's default chat participant answered "write a poem"
  requests by invoking a file-writing TOOL (visible via "I'll create this
  poem in a file for you." + an artifact reference), not a plain text
  completion — full generation took 34–54s across 4 live runs. Don't assume
  a short prompt like this completes quickly; size waits ≥90s.

## "+ Create New Agent" canvas + Build with AI (ELITEA-1920/2166)
- `ChatPage.open_create_new_agent_canvas()` (plus_menu_button → hover
  agents_menuitem → click agents-create-new-button) opens `AgentCanvasPage`,
  which renders the SAME `CreateAgentForm.jsx` as `/agents/create` — including
  its conditional `GenerateAgentButton` (`generate-agent-open-button`,
  entityType !== 'pipeline'). Build-with-AI works identically inside the
  canvas as on the standalone create page (same testids, same network
  contract) — confirmed live, ELITEA-1920.
- **Completion wiring differs by host page.** `/agents/create`'s
  `onAgentCreated` auto-navigates to `/agents/all/{id}` (ELITEA-1909). The
  chat canvas's `onAgentCreated` is `src/hooks/chat/useAgentCreation.js`
  instead: it adds the created agent as a chat participant
  (`addNewParticipants`) and auto-activates it — URL stays on
  `/chat?edited_participant_id={id}`, NO navigation away. Don't reuse
  ELITEA-1909's "wait for /agents/all navigation" pattern here; wait on
  `AgentCanvasPage.title` (switches to the agent's name post-creation) or the
  Participants popover instead.
- Participants panel: `ChatPage.open_participants_popover(timeout, section="agents")`
  (pre-existing, ELITEA-2166) — reuse directly, don't re-derive.
- Composer shows `"Editing..."` (not the agent name) while that agent's own
  canvas/editor is still open — a transient state, already documented +
  clarified (issue EliteaAI/elitea-testing-public#709). Don't mistake it for
  a broken participant-name display.

## Fragility note — `switch_project()` to an already-active project
In a from-scratch `sync_playwright` script (no pytest fixture chain),
calling `ChatPage.switch_project(<already-active-project-id>)` was observed
once to leave the composer stuck behind a permanent `MuiCircularProgress`
loading overlay that then blocks `plus-menu-button` clicks entirely (30s
timeout, `<div class="MuiBox-root css-1qkypnf">` intercepts pointer events).
Skipping the redundant switch (project was already correct) avoided it
entirely. Not reproduced through the normal pytest fixture chain — flagging
as a possible transit-path fragility for a from-scratch driver, not filed as
a product defect (never observed via the real test suite's own fixtures).

## HITL sensitive-action authorization card + direct-toolkit-call chip rendering (ELITEA-2211..2215)
- **Admin UI Guardrails (`${ELITEA_URL}/admin/app/configuration#guardrails`)
  is NOT served on `localhost:5173`** — confirmed live this pass
  (`page.goto()`, body text literally `"Page not found. Try Home page"`,
  under the normal app shell/sidebar). This is a pre-existing, ALREADY
  DOCUMENTED constraint (`tests/ui/admin/test_guardrails_cleanup_only.py`'s
  own comment: "Admin UI isn't served on localhost"); every case in this
  cluster whose precondition is "toolkit configured with HITL authorization"
  (ELITEA-2211/2212/2213/2214) needs the SAME `pytest.mark.guardrails`
  marker + CI-against-deployed-env execution path the existing
  `TestSensitiveToolLiveReload` (ELITEA-1696) already uses — not a new gap.
- **Sensitivity is toolkit-TYPE scoped, not per-toolkit-instance.**
  `GuardrailsAdminPage.add_sensitive_tool(toolkit_type, tool_name)` marks
  the tool sensitive for EVERY toolkit of that type project-wide. Any new
  test using this must clean up (`remove_sensitive_tool` + `save_configuration`)
  or it silently breaks unrelated tests that call the same tool name on a
  different toolkit instance of the same type.
- **`ChatHitlActions.jsx` (`EliteaUI/src/[fsd]/features/chat/ui/chat-hitl-actions/`)
  is the sensitive-action card's source** (read in full this pass, not just
  grepped). Confirmed testids: `sensitive-action-panel` (container, only
  rendered when `guardrail_type` is `sensitive_tool`/`parallel_sensitive_tools`),
  `sensitive-action-authorize-button`. **NO testid exists** on: the "Block"
  button (same component, `variant="alarm"`), or ANY element in
  `BlockWithCommentControl.jsx` (collapsed trigger, expanded textarea,
  Cancel button, Submit button) — confirmed via full-file read of both
  components, zero `data-testid` occurrences outside the two named above.
  These testids currently exist ONLY on `AgentDetailPage`
  (`sensitive_action_panel`/`sensitive_action_authorize_button` fields,
  `pages/agent_detail_page.py:188-189`) — `ChatPage` (the main chat, used
  by this cluster's "no agent" flow) has ZERO HITL/sensitive-action
  `LocatorDescriptor`s today; they need to be added there too (same
  underlying React component, same testids apply).
- **The Block-with-Comment collapsed trigger and its expanded-state Submit
  button are TWO SEPARATE DOM elements with the SAME visible label**
  ("Block with Comment") — `BlockWithCommentControl.jsx` swaps its entire
  return branch on `open` state (not a same-element ternary, so canon
  ruling #277's same-element-pair rule does not apply here). Each needs its
  own distinct testid; text-based disambiguation would be ambiguous/fragile.
- **Toolkit/tool-call chip has NO testid** (`ActionView.jsx:360`,
  `data-testid={toolkitType === 'model' ? 'chat-answer-model-chip' : undefined}` —
  only the `model` branch is named). Confirmed live (direct toolkit call,
  no agent, `delete_file` on a fresh artifact toolkit): the rendered chip
  text is `"{toolkit_name}: {tool_name}"` (colon-separated, via
  `ActionView.jsx`'s `buildTitle(': ', true)`) — e.g.
  `"autotest-hitl-tk-749815: delete_file"`. A turn can render **multiple**
  model chips (2 observed live for one multi-step reasoning chain: Sonnet +
  Haiku) alongside exactly ONE toolkit/tool chip — don't assert a fixed
  chip count without accounting for the model-chip count being
  data-dependent.
- **Message-composer mechanics (from-scratch script, not the `ChatPage`
  fixture chain):** `page.keyboard.press("Enter")` after typing into the
  composer does NOT submit the message — confirmed live, the text just sat
  in the composer. Must click the actual send button
  (`[data-testid="chat-send-button"]`) — matches `ChatPage.send_message()`'s
  own default (`use_enter=False`), so this is a from-scratch-script pitfall,
  not a real page-object gap.
- **Reloaded/history conversation view collapses the thought accordion by
  default** (`aria-expanded="false"`) and shows a plain-text summary
  (`data-testid="skill-test-last-response"`) instead of the live chip row —
  the model/toolkit chips only render once the accordion is (re-)expanded
  (`[data-testid="chat-answer-thought-accordion"] button` click). Don't
  assert chip presence on a freshly-reloaded/history-navigated conversation
  without first expanding it.
- **Test-data-hygiene finding (not a defect in scope for this cluster):**
  the project had **588 artifact buckets** at analysis time. A throwaway
  bucket created this pass could NOT be deleted via `ArtifactAPI.delete_bucket()`
  — both the bucket-name and the `p--{project_id}.{bucket_name}` fallback
  paths returned 404 immediately after creation. `artifact_bucket` fixture's
  teardown swallows this (`logger.warning`, non-fatal,
  `fixtures/data_fixtures.py:487-489`), so failures accumulate silently
  across runs. Likely root cause of the 588-bucket pileup; worth its own
  investigation outside this cluster.
- **An unambiguous, single-target chat message is required to reach a real
  tool-call attempt** when the toolkit is scoped to a project with many
  buckets — confirmed live: the literal ELITEA-2211 case text ("remove from
  the bucket all files") produced a CLARIFYING QUESTION from the LLM
  ("you have 588 buckets... which one?"), never a tool call, given the
  ambient bucket-count noise above. Naming the bucket explicitly in the
  message reliably reaches a real tool-call attempt (confirmed live twice).
