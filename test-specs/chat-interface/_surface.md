# Chat-interface surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Chat surface (`/chat`).
Not a substitute for execution — verify a handle as you use it. One writer at
a time; last confirmed by: qa-engineer analyst, ELITEA-2086/2087/2088,
2026-08-03 (supersedes nothing below — new section, other sections unchanged;
previous confirmer: ELITEA-2075, 2026-08-03).

## Table/diagram/code canvas editing — the "Edit table"/"Edit diagram" family (ELITEA-2086/2087/2088)
- **Entire component tree has ZERO `data-testid` anywhere** — confirmed via
  full-file reads + `git grep -c "data-testid\|testId"` returning 0 on both
  `origin/main` and `origin/automation/testids` for: `MarkdownTableBlock.jsx`,
  `Canvas.jsx`, `CanvasEditHeader.jsx`, `MarkdownTableEditor.jsx`,
  `EditingPlaceholder.jsx`, `MermaidCodeBlock.jsx`, `CanvasEditor.jsx`. This is
  a large, previously-undiscovered testid gap on a heavily-used chat feature.
- **Shared chrome across ALL canvas-edit types (table/diagram/code)** —
  `Canvas.jsx`'s `CanvasContent` + `CanvasEditHeader.jsx` + `EditingPlaceholder.jsx`
  render identically regardless of `type`/`language` (`'table'`/`'diagram'`/`'code'`),
  only the TEXT content changes (`editButtonTitle`/`editingTitle` computed via a
  ternary in `Canvas.jsx`). One set of testids covers all three:
  `chat-canvas-title` (heading, dynamic text "Edit table"/"Edit diagram"/"Edit
  code"), `chat-canvas-close-button` (X, first button in the header row, no
  aria-label today), `chat-canvas-editing-indicator` (the conversation-pane
  placeholder, dynamic text "Table editing..."/"Diagram editing..."/"Code
  editing..."). **Add these ONCE** — whichever of ELITEA-2086/2087/2088
  implements first should add them; the others just consume, don't
  re-request/duplicate.
- **Per-type edit-icon trigger is a SEPARATE `IconButton` per source component**
  (not shared): `MarkdownTableBlock.jsx`'s own icon (Tooltip "Edit table") vs
  `MermaidCodeBlock.jsx`'s own icon (Tooltip "Edit diagram") — each needs its
  own testid (`chat-table-edit-button` / `chat-diagram-edit-button`), even
  though the resulting CANVAS chrome they open is the shared one above.
- **Interim (pre-testid) reachable handle, confirmed live, NOT for shipped
  automation**: `[aria-label="Edit table"] button` / `[aria-label="Edit
  diagram"] button` both resolved to the correct edit `IconButton` live —
  exact origin of the `aria-label` not independently traced to source (MUI
  `Tooltip` wrapping, not a literal `aria-label` prop anywhere in
  `MarkdownTableBlock.jsx`/`MermaidCodeBlock.jsx`/`Canvas.jsx` — worth a closer
  look if reused, but per policy this is scaffolding-only, not a shipped
  locator).
- **Table editing** (ELITEA-2086/2087): the canvas grid is MUI X `DataGrid`
  (`MarkdownTableEditor.jsx`). Cells addressable via MUI-provided
  `data-field="<ColumnName>"` (NOT custom testids); row-selection checkbox
  column is `data-field="__check__"`. **`.MuiDataGrid-columnHeader`'s own
  `innerText` reads EMPTY** — the visible label lives one level deeper
  (`.MuiDataGrid-columnHeaderTitle`) or just read `data-field` directly
  (more stable). Pagination footer text confirmed exact: `"Rows per page: 50"`
  / `"1–10 of 10"` (MUI default `.MuiTablePagination-root`, not custom-built).
  Cell-edit mechanism: **`dblclick()` required** (single click only
  selects/focuses); the nested cell editor's `input`/`textarea` DOES accept
  plain Playwright `fill()` (unlike the general MUI-form-field `fill()`
  caveat in `mui-patterns.md` — DataGrid's own cell editor wires `onChange`
  directly to input events). **Declared improvisation flagged for reviewer
  sign-off**: DataGrid's per-cell/`data-field` DOM is treated as analogous to
  the #579 sanctioned-exception categories (not a 1:1 match — DataGrid renders
  app data per cell, unlike ReactFlow/CodeMirror) — recommend ONE testid on
  the DataGrid's containing `Box` (`chat-table-canvas-grid`), then scope raw
  `data-field` selectors as children, mirroring the CodeMirror pattern below.
- **AI-generated table content is NON-DETERMINISTIC across generations** —
  confirmed live, two separate runs of the identical prompt ("generate a
  table of top 10 IT companies") produced DIFFERENT row orders (run 1: Apple
  first; run 2: Microsoft first) and a differing column set (a 5th "Market Cap
  (Approx.)" column present in one run, absent the other). **Never assert
  fixed row index or a fixed exact column list** — assert set-membership /
  core-column-presence instead. This applies to any case built on an
  AI-generated-content prompt, not just this cluster.
- **Diagram editing** (ELITEA-2088): the canvas code editor is CodeMirror
  (`.cm-editor`/`.cm-content`/`.cm-line`, one `.cm-line` per source line) —
  a **direct match to the existing #579 sanctioned exception** (same category
  as `mcp_form_page.py:121`'s precedent, no reviewer escalation needed): add
  ONE real testid on the editor's container (`chat-canvas-mermaid-editor-content`),
  scope `.cm-line` raw selectors as children.
- **Real-time Mermaid syntax validation is CONFIRMED WORKING and genuinely
  live** — editing the diagram-TYPE declaration line (`flowchart TD` →
  `flowchart TD edited`, NOT a node-label line) breaks Mermaid syntax and
  immediately surfaces a red error panel: exact text `"Syntax error: Missing
  semicolon, new line, or unexpected characters (Line 1)"` +
  `"Problematic code: <text>"` + a "Quick Fix" affordance (AI-assisted,
  backed by `useGenerateContentBlockingMutation`/`MERMAID_QUICK_FIX` service
  prompt, not exercised live) + `mermaid version 11.16.0` shown. **For a
  happy-path automation assertion (valid re-rendered diagram, not an error
  state), edit a NODE-LABEL line instead of line 1** — confirmed live that
  editing the type-declaration line is what triggers the error, this is a
  case-text ambiguity ("edit one block of text" doesn't specify which),
  not a defect.
- **Canvas→conversation sync on close is CONFIRMED for the error-path edit**
  (closing after the type-line edit above: the conversation's OWN diagram
  render shows the identical error state/text the canvas did) — the
  MECHANISM (canvas state persists to conversation on close) is proven; the
  specific "valid edit → diagram re-renders normally" sub-path was not
  independently re-verified in the same session (time went to the more
  informative real-time-validation discovery) — flagged for the ELITEA-2088
  implementer's first pass, not a blocker.
- **Wait-strategy trap, confirmed live**: a bare `page.wait_for_selector("svg")`
  after sending "generate a mermaid diagram" false-positive-matches an
  unrelated icon SVG elsewhere on the page (nav/sidebar icons) well before the
  actual diagram renders — produced a false "edit icon not found" on the
  first live attempt. Use `wait_for_ai_response()` +
  `wait_for_message_content_stable()` (existing `ChatPage` methods) instead,
  same as any other AI-generated-content wait on this surface.
- **CodeMirror `.cm-line` re-reads can go stale** — an `all_inner_texts()`
  snapshot captured before a `.keyboard.type()` edit, then reused without
  re-querying, read as unchanged even though the live DOM (confirmed via
  screenshot) had updated. Always re-query `.cm-line` fresh after an edit,
  don't reuse a pre-edit locator handle/array.

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

## Agent Hub ("Catalog") participant read-only canvas + per-conversation LLM override (ELITEA-2075)
- **Naming drift, case-text only**: the sidebar nav item is **"Catalog"**
  (`EliteaCatalog.jsx`, route `/elitea-catalog`), NOT "Agent HUB" — `AgentHub`
  is only a legacy redirect source (`RouteDefinitions.AgentHub = '/agents-hub'`
  → redirects to `/elitea-catalog`). The agent detail modal's action button
  is **"Start Chat"**, not "Start conversation". Both are stale case-text,
  not defects — assert the live labels.
- **CONFIRMED DEFECT, already tracked #1043** (re-encountered, not re-filed):
  the Catalog agent-detail modal's "Start Chat" button has no loading guard —
  clicking it before `AgentModal.jsx`'s own `getPublicApplicationDetail` fetch
  resolves throws `TypeError: Cannot read properties of null (reading
  'version_details')` and silently no-ops (no navigation, no toast). Confirmed
  live 2/2 on a fast click, 0/2 on a click after a ~1.5s wait. Automation must
  wait for the modal's own content (e.g. the "Show instructions" link or
  conversation-starters block) to render before clicking Start Chat — this is
  synchronization, not defect-masking.
- **"View settings" is the SAME `EditParticipantButton`/`#EditButton` as
  "Edit agent"** (`ParticipantActions.jsx`) — its tooltip and aria-label swap
  to "View settings" specifically when `canEdit` is false (public/Agent-Hub
  agent + no edit permission on it). Reached via: expand collapsed Participants
  badge (`chat-participants-panel-toggle-button`) → hover the agent row → click
  `#EditButton` (no dedicated testid on this button itself — it's a raw `id`
  attribute, not `data-testid`; confirmed `aria-label="View settings"` is
  present and stable, but per project locator policy this element still
  **needs a real `data-testid`** — e.g. `chat-participant-edit-view-button` —
  since it's on this case's own executed path).
- **The canvas that opens is `AgentEditor.jsx`/`CreateAgentForm`'s shared
  edit surface** (SAME component tree as the "+ Create New Agent" canvas
  ELITEA-1920/2166 already documented above), NOT a separate read-only view.
  `isPublic={!canEditIt}` (passed to `BaseEditor`/`EditorHeader`) is what:
  (a) renders the "Public" label (plain `Typography`, text "Public", **no
  testid**) instead of Discard+Save buttons, (b) sets `canEditModel =
  canEditIt || !!onPublicLlmOverride` — TRUE for a public agent specifically
  *because* the chat canvas passes a `onConversationLlmOverride` callback, so
  the LLM selector is the ONE editable control by design, not an oversight.
  Confirmed live: `model-selector-name`/`model-selector-button`/
  `model-settings-button` (all pre-existing, on-main, shared with
  `AgentDetailPage` — same `LLMModelSelector.jsx` widget) all present and
  clickable; `agent-canvas-title`/`agent-canvas-subtitle`/
  `agent-canvas-close-button` (pre-existing) show "Reflexion"/"v1.0".
- **Model change is saved to the chat PARTICIPANT's `entity_settings.llm_settings`
  (`onChangeParticipantSettings`), never PUT to the agent's own version** —
  confirmed live: selecting a model or clicking Apply in the settings dialog
  fires ZERO `PUT`/`PATCH`/`POST` request containing "application" in the URL.
  Confirmed persistence: closing the canvas (`agent-canvas-close-button`) and
  reopening it (View settings again) in the SAME conversation still shows the
  overridden model — this is the case's "changes are saved per conversation
  only" contract, live-verified both halves (persists in-conversation, never
  reaches the backend agent record).
- **Model dropdown option text drift**: the case's literal "Anthropic Claude
  4.5 Sonnet" does not exist verbatim in this environment; the live option is
  named **"Azure Claude Sonnet 4.5"** (11 total models in the
  `model-selector-option-*` list this session). Match by a partial/case-
  insensitive "sonnet" + "4.5" filter, not the exact case string.
- **TOOLS module toggles are functionally inert, not just visually greyed**:
  confirmed live — the `<input type="checkbox" role="switch">`'s `checked` JS
  property (read via `page.evaluate`) is unchanged before/after BOTH a raw
  `page.mouse.click()` at its bounding-box center AND a Playwright
  `.click(force=True)`, and zero network calls fire. **Do NOT assert via the
  `disabled`/`aria-disabled` HTML attributes** — neither is actually set on
  the raw `<input>` in this component (MUI disables it through a different
  mechanism); assert via the `checked` property staying constant across a
  click attempt instead. 4 toggles visible without scrolling (Attachments,
  Data Analysis, Image creation, Agents & Pipeline Builder) + a "Show all"
  expander; no testid on any of the 4 (each only has an icon + label text).
- **Model Settings dialog (`model-settings-dialog`, pre-existing, shared
  `LLMSettingsDialog.jsx`) — REASONING slider + MAX COMPLETION TOKENS +
  CAPABILITIES all confirmed live** for this model: `model-settings-
  reasoning-slider` (pre-existing) renders Low/Medium/High; MAX COMPLETION
  TOKENS shows a Default/Custom radio pair (`model-settings-max-tokens-section`
  pre-existing, container only — the two radios themselves have no testid);
  a "Capabilities" section (own `CapabilitySection.jsx`, **zero testid**,
  conditionally rendered only when the model supports vision and/or
  reasoning) showed "Image analysis" + "Reasoning" chips for this model.
  **Selecting "High" reasoning has no dedicated per-level testid or click
  target** — `ReasoningSlider.jsx`/`DiscreteSlider.jsx` renders one invisible
  click-trigger `Box` per mark, absolutely positioned by percentage
  (`left: {(value-min)/(max-min)*100}%`) OVER the slider control, each with
  `pointerEvents: 'none'` at the CURRENTLY-selected mark (so it can't be
  re-clicked, only dragged). Confirmed live mechanism: click within the
  `model-settings-reasoning-slider` container's bounding box at
  `x = box.x + box.width - 5` (rightmost ≈ 100% position = "High") — this is
  a bounding-box-relative click, not a stable handle; needs a `data-testid`
  per mark (e.g. templated `model-settings-reasoning-level-{level}`) if this
  becomes a recurring automation need beyond this one case.
- **The Apply button in `LLMSettingsDialog.jsx` has NO testid** (confirmed —
  `AgentDetailPage`'s own docstring already flagged this as "out of scope,
  only Cancel exercised" for ELITEA-1880/1881; THIS case is the first that
  needs to click it). Located this session via `get_by_role("button", name=
  "Apply")` (single match, MUI `Button.BaseBtn` text "Apply") — needs a real
  `model-settings-apply-button` testid added. Same gap for "Reset to
  defaults" (only rendered when `onResetToDefaults` is passed, i.e. only in
  this per-conversation-override flow — not exercised by this case's steps).
- **Composer participant-chip text is "Viewing..." for a public/Agent-Hub
  agent** while its own canvas is open — a THIRD state alongside the already-
  documented "Editing..." (own agent) — confirmed live, `chat-{participant}-
  v{version}-chip` area. Same transient-state family as issue #709
  (clarified, not a defect).

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

## In-chat "Create New X" canvas family — Pipeline/MCP (ELITEA-2079/2085, 2026-08-03)

Covers the `+` menu's **Pipelines** and **MCPs** submenus → their respective
"Create New …" in-chat canvases. Both canvases are the SAME shared
`BaseEditor`/`EditorHeader` chrome + entity-specific form, exactly like the
Agent canvas (ELITEA-2166) — confirm-as-you-go still required, but the shape
below is now load-bearing precedent for any sibling case in this family
(Toolkit-from-chat, ELITEA-2080-2083, is the one remaining unexplored
sibling and should follow the identical pattern).

- **Entry-point testids, both confirmed on-main ✓**: `pipelines-menuitem` /
  `mcps-menuitem` (hover-triggered, `PlusChatButton.jsx`'s static
  `EXPANDABLE_ITEMS`), then `pipelines-create-new-button` /
  `mcps-create-new-button` (`PlusChatSubmenu.jsx`'s
  `${sectionKey}-create-new-button` pattern — `sectionKey` = the raw
  `SUBMENU_KEYS` value, i.e. `"pipelines"`/`"mcps"`, NOT a display label).
- **Pipeline-canvas Flow Editor is the SAME `EditorPanel` component the
  standalone `/pipelines/all/{id}` page uses** (`PipelineEditor.jsx` imports
  `@/pages/Pipelines/Components/EditorPanel`) — `PipelineDetailPage`'s
  existing methods (`add_node`, `switch_to_yaml_view`/`switch_to_flow_view`,
  `get_yaml_content`, `get_node_count`) work UNCHANGED on the chat canvas.
  Same reuse pattern for the MCP-canvas form: `ToolkitEditor.jsx` renders the
  identical `ToolkitForm`/`ToolkitTypeSelector` the standalone
  `McpFormPage`/toolkit-creation flow uses — `toolkit-form-name-input`,
  `toolkit-field-url-input`, `toolkit-field-client_secret-input-field`,
  `toolkit-type-card-mcp`, `toolkit-connection-status`, `category-filter-tab`
  ("Local"/"Remote", 2 instances — disambiguate with `.filter(has_text=...)`)
  all confirmed **on-main ✓**, identical testids, zero new form-field work.
- **`get_yaml_content()` MUST be used for YAML-line assertions — never raw
  `inner_text()` on the editor.** CodeMirror's gutter renders line-numbers
  BEFORE the content lines in DOM order, so `inner_text()` on the whole
  editor yields `"1\n2\n3...19\nentry_point: LLM 1\nnodes:\n..."` — numbers
  first, content after. A naive read silently misaligns "line N" assertions.
  `PipelineDetailPage.get_yaml_content()` (existing, `.cm-line`-scoped)
  already avoids this.
- **Four-way canvas-chrome testid gap, confirmed across BOTH Pipeline and
  MCP canvases (BaseEditor/EditorHeader-level, not entity-specific code):**
  `BaseEditor`/`EditorHeader` already support optional `titleTestId` /
  `subtitleTestId` / `closeButtonTestId` props (wired end-to-end, confirmed
  by reading `EditorHeader.jsx`) — ELITEA-2166 supplied them ONLY at
  `AgentEditor.jsx`'s call site (`agent-canvas-title` /
  `agent-canvas-close-button`). Neither `PipelineEditor.jsx` nor
  `ToolkitEditor.jsx` supplies them at all — confirmed live: the close-X
  button (first header button, no text, no aria-label) and the post-save
  canvas title both resolve via testid on the Agent canvas but NOT on
  Pipeline/MCP. `testid needed` on each remaining call site:
  `pipeline-canvas-close-button` (Pipeline; title not needed by any case yet);
  `mcp-canvas-title` + `mcp-canvas-close-button` (MCP — `ToolkitEditor.jsx`
  ALSO renders the plain-Toolkit-creation canvas through the same component,
  so both must be threaded conditionally: `isMCP ? 'mcp-canvas-*' :
  undefined`, leaving the Toolkit path's own future testid for whichever
  case first touches it).
- **Canvas create-mode Save/Create buttons are two DIFFERENT components with
  different gaps**: `CreateApplicationSaveButton.jsx` (Agent/Pipeline
  create-mode) still has ZERO testid on `main` despite ELITEA-2166's AFS
  recommending `agent-save-button` — re-flag if you hit it, the fix hasn't
  landed yet. `CreateToolkitButton.jsx` (Toolkit/MCP create-mode, a
  DIFFERENT component) also has zero testid — `testid needed:
  mcp-canvas-create-button` (`isMCP`-conditional, same shape as above). The
  EDIT-mode Save button (`SaveApplicationButton.jsx`) already carries
  `agent-save-button` unconditionally and DOES work as-is inside both the
  Pipeline and (presumably) Toolkit/MCP chat canvases — confirmed live for
  Pipeline. This misleading-name quirk is already tracked as issue #1040.
- **Participant infra is fully generic and needs NO new work for
  Pipeline/MCP participant types**: `PARTICIPANTS_BADGE`/`PARTICIPANT_ROW`
  dynamic templates already in `chat_page.py` work unchanged —
  `chat-participants-badge-pipelines`/`-mcp`,
  `chat-participants-badge-icon-pipelines`/`-mcp`, and
  `chat-participant-row-{pipeline,mcp}_{id}_{project_id}` all confirmed live.
  PARTICIPANTS panel groups by entity-type heading exactly as case text
  describes ("PIPELINES" / "MCPS" sections, confirmed verbatim).
- **Disconnected-participant warning icon has NO testid**: `ParticipantWarning.jsx`
  (shared between MCP and Pipeline misconfigured-participant rendering per
  issues #684/#687) has zero `data-testid` anywhere. `testid needed:
  chat-participant-warning-icon` — UNconditional (component is already
  entity-agnostic, not a per-caller hardcode situation). Exact confirmed
  live text for a disconnected Remote MCP: `"Server is disconnected!
  Reconnect it to use. Log in."`
- **Known test-robustness gotcha (issue #1085) reproduces easily on THIS
  surface** if you drive a brand-new conversation via a raw
  `sidebar-create-button` click without the `conversation_id` fixture's
  readiness handling: the center message-pane can show a persistent loading
  spinner (an overlay `MuiBox` that swallows clicks/covers the composer)
  for far longer than a short fixed wait — reproduced live, root-caused to
  the SAME class of issue as #1085 (conversation-list load time under
  accumulated local test data), NOT a defect in whatever feature you're
  actually testing. The real fixture-driven suite (`conversation_id` +
  `navigate_to_chat(conversation_id=...)`) does NOT hit this — verified live
  by re-running `test_chat_interface.py::TestSendingMessages` (5/5 passed)
  in the identical environment immediately after reproducing the hang in a
  raw script. **Always use the `conversation_id` fixture for message-send
  assertions on this surface**, never a bare `+Chat` button click + short
  wait, regardless of which entity/canvas the case is actually about.
- **Known pre-existing console noise, dedup-checked, do not re-file:**
  issue #656 ("unique key prop" React warning in `CategorySection.jsx`)
  fires on EVERY toolkit-type-picker render (Toolkit AND MCP creation,
  chat-canvas AND standalone) — filter it the same way `test_edit_instructions`
  filters its own known #538 noise.

## Agent + Pipeline participant coexistence — BLOCKING instability (ELITEA-2455, 2026-08-06)
- **CONFIRMED BLOCKING DEFECT, filed EliteaAI/elitea-testing-public#1279**
  (sibling of #684 — same participant-state `version_id` mixup family the
  parked ELITEA-2094 investigation documented): adding an Agent participant
  THEN a Pipeline participant to the same conversation is a **silent
  no-op** on the Pipeline add — the item resolves, clicks, the popper's
  network-idle wait completes, no error is shown, but no Pipeline
  participant is ever created. The REVERSE order (Pipeline first, then
  Agent) DOES add both, but throws `GET
  /elitea_core/version/prompt_lib/{project}/{agent}/{version}` → 400 +
  `TypeError: Cannot read properties of undefined (reading 'icon_meta')`
  at `ChatBox.jsx:1601` during the Agent add — and even THAT order was not
  reliably reproduced 2/2 in the automated pytest harness (worked live via
  manual Playwright MCP driving, failed once inside the real pytest run
  with the identical page-object methods). This matches ELITEA-2094's own
  characterization exactly: "can crash immediately, crash later at Send,
  silently misclassify a badge into the wrong PARTICIPANTS section, or
  resolve with ZERO VISIBLE SYMPTOM depending on timing."
- **Any case needing an Agent AND a Pipeline as SIMULTANEOUS chat
  participants is currently blocked by this** — not just ELITEA-2455.
  Re-check this instability first before spending analysis time on such a
  case; consider the same `defect-found`/park classification ELITEA-2094
  reached until #1279 (and its siblings #684/#687/#689) are resolved.
- **Agent-only, Pipeline-only, Toolkit-only, and MCP-only adds are all
  independently reliable** (each confirmed live, both via a scratch
  Playwright MCP script and inside the real fixture-driven pytest harness)
  — the instability is specifically about Agent+Pipeline COEXISTENCE, not
  the individual add mechanisms.
- **Testid patterns confirmed for the Agents/Pipelines submenus** (select-
  and-close semantics, mirroring the already-documented Toolkits/MCPs
  toggle-switch shapes above): `agents-search-input` / `pipelines-search-input`
  (generic `PlusChatSubmenu.jsx` `${sectionKey}-search-input` template, no
  new testid needed); `agents-menu-item-agent-{project_id}-{agent_id}` /
  `pipelines-menu-item-pipeline-{project_id}-{pipeline_id}` (same generic
  `${sectionKey}-menu-item-${item.key}` template, `item.key` confirmed via
  `useDropdownData.jsx`'s `agentMenuItems`/`pipelineMenuItems`:
  `agent-${project_id}-${id}` / `pipeline-${project_id}-${id}`). Both
  already render on `automation/testids` — no `add-data-testid` work
  needed for this whole surface.
- **`chat-attach-menuitem-button` is ALREADY wired** (`AttachmentButton.jsx`'s
  `testId` prop, consumed at the plus-menu popper call site in
  `PlusChatButton.jsx`) — supersedes this file's earlier File-attachments
  section note that it "needs a `testId` prop threaded through" (that work
  had already landed by this pass; only newly CONSUMED, not added).
- **`chat-participants-badge-icon-{section}`** (collapsed-badge-only,
  commit `8971529f`, pre-dates this pass) is the ONLY testid-backed
  distinct-icon-per-participant-type signal anywhere in this component
  family — the EXPANDED panel's per-row `EntityIcon` (`ParticipantItem.jsx`)
  carries no testid or per-type attribute at all (confirmed via full-file
  read). A case needing "distinct icon per type" while the panel stays
  EXPANDED has no in-panel testid signal; must toggle to collapsed
  specifically for that check.
- **`close_plus_menu_popper()`'s `chat-message-list` outside-click target
  does not exist on a brand-new, UNSENT conversation** (`NewConversationView`
  renders `chat-new-conversation-greeting` instead, confirmed live) — a case
  driving the plus-menu popper before the first Send needs a different
  outside-click target (e.g. the greeting container itself, confirmed live
  to correctly trigger the same `ClickAwayListener` dismissal).
- **`agent_id` and `pipeline_with_llm_id` fixtures produce COLLIDING display
  names** — both derive from the identical `f"autotest_{request.node.name}"[:32]`
  pattern (`data_fixtures.py`). `ChatPage.get_participant_row_by_name()`'s
  text-filter can't disambiguate them when both are participants in the
  same conversation — resolve by the row's UNIQUE-ID testid instead
  (`chat-participant-row-application_{agent_id}_{project_id}` /
  `chat-participant-row-pipeline_{pipeline_id}_{project_id}`).
- **Composer placeholder attribute race, low-confidence** (filed
  EliteaAI/elitea-testing-public#1278): `[data-testid="chat-message-input"]`'s
  `placeholder` HTML attribute read empty (`""`) in 4/4 dedicated checks
  early in this session, but correctly showed `"Type your message..."` in a
  later screenshot AND a later live re-check (same session, more elapsed
  time / more page interactions before the check). Not confirmed as a
  hard, reliably-reproducing defect — likely a timing race resolved by
  some async condition (participant list load? user-settings fetch?) not
  yet isolated. Worth a dedicated, isolated repro (fresh page, immediate
  check, then poll at fixed intervals) if picked up again — don't hard-
  assert the placeholder text without a wait-for-condition, and don't treat
  a single early-check failure as proof.
