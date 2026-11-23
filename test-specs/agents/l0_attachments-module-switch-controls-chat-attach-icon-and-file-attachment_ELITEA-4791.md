# Test Case: Attachments module switch in "+ Modules" controls the agent chat attach icon and file attachment

- **TMS:** ELITEA-4791 (requirement elitea_issues#7380) - priority critical
- **Status:** ready-for-automation
- **Surface:** `agent-modules-dropdown` + embedded agent chat (Test Agent panel)
- **Executed:** 2026-11-23 on DEV (`https://dev.elitea.ai/app`), fresh fixture agent (`agent_id` fixture), 1920x1080, scripted headless Playwright (MCP chrome binary absent on host; repo-venv Playwright + dev storage state). Every step run live end to end.
- **Spec home (suggested):** `automation/tests/ui/agents/test_agent_modules_attachments_switch.py` (new file; page objects `AgentDetailPage` + existing chat locators). Use fixture `agent_id` (fresh agent, deleted afterwards - no cleanup needed).
- Neighbours checked: ELITEA-4789/4790 specs (modules dropdown open/toggle/persist; never touch chat attach -> not coverage); ELITEA-2197/2200/2877 (standalone /chat attach button; different surface, different gating) -> not coverage. Pipeline-level ELITEA-2066/2059 are cited by the case as the only existing coverage; not agent-level.

## Where the "attach icon" lives (case drift, important)
The case says "Open the Agent chat panel". On the agent detail page the chat is the **Test Agent side panel**: click `agent-test-button` -> `agent-test-panel`/`chat-message-input`. Inside it the attach icon is a **direct toolbar IconButton `chat-attach-button`** (aria-label "attach files", 28px, next to model selector) - NOT the plus-menu "Attach Files" item used on standalone /chat (`chat-attach-menuitem-button`). Existing `ChatPage.attach_files_button` points at the plus-menu item: do not reuse it here.

## Gating mechanism (source-confirmed + live-confirmed)
`useAgentAttachments.js`: `disableAttachments = !agentVersionDetails.meta.internal_tools.includes('attachments')` - based on the **saved** version, so the chat state follows the switch only AFTER Save (and the chat reflects it after reload/reopen; probes always did Save -> reload -> open panel).

## Steps (as executed) and observations
0. Fresh agent (API fixture). Open `/agents/all/{id}?viewMode=owner`, dismiss `platform-banner-close` if visible. Default: Attachments switch OFF; open Test Agent panel: `chat-attach-button` is `disabled`, computed `pointer-events:none`.
1. Click `agent-add-modules-button` -> `agent-modules-menu`. Turn Attachments ON (see quirk below). `agent-canvas-tools-toggle-attachments` checked, `agent-save-button` enabled. Escape, click Save, wait `agent-save-button` disabled (saved). Reload.
2. Click `agent-test-button`, wait `chat-message-input`: `chat-attach-button` count 1, `disabled=false`, `pointer-events:auto`.
3. `with page.expect_file_chooser(): click chat-attach-button`; `set_files(sample.txt)`. Chip appears: `chat-attachment-chip-0` text "sample.txt" (chip testid is index-based, existing ChatPage constants `CHAT_ATTACHMENT_CHIP_PREFIX`). Fill `chat-message-input` "Summarize the attached file", click `chat-send-button`. Chip clears on send; user message item shows the file name; assistant reply (`chat-message-item`, 2nd) contains `chat-answer-tool-chip` "Attachments: read_multiple_files" and text based on the file. **Reply observed within ~4s model + tool.** NOTE: `chat-answer-content` was NOT found in the embedded panel in this run (wait on it timed out at 90s); wait instead on the 2nd `chat-message-item` / `chat-answer-tool-chip` / `chat-regenerate-button`. Existing `AgentDetailPage.wait_for_chat_response` should be checked by the implementer.
   - Data advice: first probe with a trivial "hi" file produced a reply that quoted the file text ("hi") but the LLM also hedged. Make sample.txt contain a unique marker (e.g. `ELITEA4791-MARKER-<uuid8>`) and assert reply `inner_text` contains it OR the tool chip "Attachments: read_multiple_files" is present (prefer both; the marker is the true "based on the file" proof; model may paraphrase - pick a prompt "Summarize the attached file and quote its first word exactly" is NOT in case; keep case prompt and assert chip + marker softly decided by implementer on first run).
4. Reopen `agent-add-modules-button`, toggle Attachments OFF, Escape, Save (enabled -> disabled), reload.
5. Open Test Agent panel: `chat-attach-button` `disabled=true`, `pointer-events:none`. A real click is blocked by Playwright actionability (cannot click); no file chooser.
6. Attach attempt: click is impossible (disabled); **drag-and-drop** onto the composer: dispatch dragenter/dragover/drop DragEvent with a DataTransfer containing `sample.txt` on `chat-message-input` and each ancestor (bubbles) -> toast `toast-message` text **"Attachments are not allowed."** (existing testid `toast-message`), and `chat-attachment-chip-*` count stays 0. (Source: `NewChatInput.jsx` onDrop short-circuits to `toastError` when `disableAttachments`.) Real OS drag cannot be driven by Playwright; synthetic DragEvent with DataTransfer is the sanctioned route (this is the exact event the handler reads) - declared improvisation.

## Quirk: row click centre hits the (i) icon
`row.click()` (centre) on `agent-module-menu-item-attachments` does NOT toggle (tooltip (i) stops propagation near row centre; "Attachments" row, 239px wide). `click(position={"x": 40, "y": 10})` toggles reliably; Space on the focused row also toggles. `AgentDetailPage.toggle_module()` uses a centre `row.click()` - works for pyodide/web_search (ELITEA-4790) but NOT attachments. Implementer: extend `toggle_module` with a left-offset click position (or click the name text) and verify `aria-checked` flipped. Poll `agent-module-menu-item-attachments[aria-checked]` / switch `checked`.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| + Modules button | 1 | `agent-add-modules-button` (`add_modules_button`) | - | testid on DEV |
| Modules menu | 1 | `agent-modules-menu` | - | testid on DEV |
| Attachments row | 1 | `agent-module-menu-item-attachments` (`MODULES_MENU_ITEM`), state `aria-checked` | - | testid on DEV; click at left offset |
| Attachments switch | 1 | `agent-canvas-tools-toggle-attachments` input `checked` | - | testid on DEV |
| Save / Discard | 1 | `agent-save-button` / `discard-button` | - | testid on DEV |
| Banner close | 1 | `platform-banner-close` | - | testid on DEV |
| Test Agent button | 1 | `agent-test-button` (`test_agent_button`) | - | testid on DEV |
| Chat input / send | 1 | `chat-message-input` / `chat-send-button` | - | testid on DEV |
| **Chat attach icon** | 1 | `chat-attach-button` (aria-label "attach files"); state = DOM `disabled` | - | testid on DEV (NEW page-object field needed on AgentDetailPage; not the dead ChatPage one) |
| Attachment chip | 1 | `chat-attachment-chip-{i}` (`ChatPage.CHAT_ATTACHMENT_CHIP_PREFIX`) | - | testid on DEV |
| Error toast | 1 | `toast-message` text "Attachments are not allowed." | - | testid on DEV |
| Assistant tool chip | 1 | `chat-answer-tool-chip` "Attachments: read_multiple_files" | - | testid on DEV |
| Chat messages | 1 | `chat-message-item` | - | testid on DEV |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | saved with Attachments ON | steps 1 | switch checked after reload; Save disabled after save | asserted |
| Step 2 | attach icon displayed + enabled | step 2 | `chat-attach-button` visible, `to_be_enabled` | asserted |
| Step 3 | file attached+sent; Agent replies based on file | step 3 | chip shows file, reply has tool chip + marker | asserted |
| Step 4 | saved with OFF | step 4 | switch unchecked after reload | asserted |
| Step 5 | attach icon disabled | step 5 | `to_be_disabled` | asserted |
| Step 6 | not attached + error message | step 6 | drop -> toast "Attachments are not allowed.", 0 chips | asserted (drag-drop route; click route impossible because disabled) |
| Pass/Fail "file attaches while OFF" | no chip | step 6 | chip count 0 | asserted |
| Axis 2: icon enabled->disabled gating persists across reload | | steps 2/5 | after reload | added (gating is saved-version based) |

## Clarifications (case-text drift, not defects)
1. "Chat panel" = Test Agent side panel; attach icon is the toolbar `chat-attach-button`, not plus menu.
2. Step 6 "click the icon": icon is truly disabled (no click possible); the error message only arises on drag-and-drop. Not a defect: "disabled icon + error on drop" is the contract.
3. Fresh agent default is Attachments OFF; 4790 note says `elitea_builder`/`ask_user` start ON - irrelevant here.
4. Save is required before the chat reflects the switch (version-details based).

## Known Defects
None.

## Risks
- LLM reply wording non-deterministic; assert chip + marker, not a specific sentence. Budget 60s.
- Platform banner intercepts clicks: dismiss first.
- Wait for Save completion via `agent-save-button` disabled before reload.
