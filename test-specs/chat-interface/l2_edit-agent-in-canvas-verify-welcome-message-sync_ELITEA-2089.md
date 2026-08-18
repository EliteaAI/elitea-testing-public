# AFS — ELITEA-2089: Chat – Edit Agent in Canvas Mode – Verify Changes Synchronize to Agent

**Status:** ready-for-automation
**Priority:** p2 (high)
**Module:** chat-interface
**Surface key:** chat-canvas-edit-agent

---

## Summary

Verify that editing an owned agent's Welcome Message through the chat canvas and saving
correctly synchronises the change back to the agent in the Agents section.

**Coverage gap:** New — no existing spec covers editing an owned agent's welcome message
via the chat canvas and verifying cross-section sync. Neighbours cover read-only canvas
(ELITEA-2075) and create-new-agent canvas (ELITEA-2166); neither closes this flow.

---

## Fidelity Declaration

No substitutions. All observables produced by the live system. The test data agent
("echo" in the case; any owned agent created via the test fixture in automation) is
an implementation choice — the observed behaviour is agent-name-independent.

**Transit note:** The precondition (an open conversation with an owned agent as
participant) is set up via the UI using the existing `plus-menu-button → agents-menuitem`
flow (same flow validated in ELITEA-2166 and directly observed here). The case's own
observable — the welcome message sync — is observed against the live Agents section.

---

## Test Data

| Field | Value |
|---|---|
| Agent | Any owned agent reachable from Private project (fixture creates or finds one) |
| Case text specifies | `echo` / `echo base` |
| New welcome message | `edited from canvas` |
| Restoration | Fixture must restore the original welcome message after the test |

---

## Handles Reference

| Handle | testid | Provenance | Notes |
|---|---|---|---|
| Participants badge button | `chat-participants-badge-button` | on main ✓ | Opens/collapses PARTICIPANTS panel |
| Plus menu button | `plus-menu-button` | on main ✓ | Composer "+" menu |
| Agents menu item | `agents-menuitem` | on main ✓ | "Agents" item in plus menu |
| Agent menu item (dynamic) | `agents-menu-item-agent-{project_id}-{agent_id}` | on main ✓ | Dynamic; fixture selects by name |
| Edit agent button | `chat-participant-edit-view-button` | on main ✓ | Pencil/edit icon; appears on hover of participant row |
| Participant settings chip | `chat-participant-settings-button` | on main ✓ | Shows "Editing..." when owned agent canvas open |
| Canvas close button | `agent-canvas-close-button` | on main ✓ | X button in canvas header |
| Canvas title | `agent-canvas-title` | on main ✓ | Agent name in canvas header |
| Canvas subtitle | `agent-canvas-subtitle` | on main ✓ | Version label ("base") in canvas header |
| Discard button | **testid needed:** `agent-discard-button` | MISSING | `Button.DiscardButton` in `EditorHeader.jsx` has no testid; add `discardButtonTestId` prop, wire in `AgentEditor.jsx` |
| Save button | `agent-save-button` | on main ✓ | Save button in canvas header |
| Welcome message textarea | `agent-welcome-message-input` | on main ✓ | Textarea in Welcome message accordion |
| Toast message | `toast-message` | on main ✓ | Success notification text container |

---

## Steps

### Step 1 — Navigate to Chats; add an owned agent as participant

**Action:** Navigate to `/chat` in Private project (project 399). Click `plus-menu-button`,
select `agents-menuitem`, then select the owned test agent by its
`agents-menu-item-agent-{project_id}-{agent_id}` testid.

**Observable:** Agent chip appears in the composer. `chat-participants-badge-button` shows
badge count "1".

**Testids:** `plus-menu-button`, `agents-menuitem`, `agents-menu-item-agent-{…}-{…}`,
`chat-participants-badge-button`

---

### Step 2 — Open PARTICIPANTS panel and click Edit agent

**Action:** Click `chat-participants-badge-button` to open the PARTICIPANTS panel. Hover
over the participant row, then click `chat-participant-edit-view-button` (the pencil icon).

**Observable:** Edit canvas slides open. URL appends `?edited_participant_id={agent_id}`.
`agent-canvas-title` shows the agent name; `agent-canvas-subtitle` shows the version label.

**Testids:** `chat-participants-badge-button`, `chat-participant-edit-view-button`,
`agent-canvas-title`, `agent-canvas-subtitle`

---

### Step 3 — Verify "Editing..." chip in the composer

**Action:** Observe the composer area (no user interaction needed).

**Observable:** `chat-participant-settings-button` contains text "Editing..." (not "Viewing...").
This confirms the canvas is in edit mode for an owned agent.

**Assertion:**
```python
expect(chat_page.chat_participant_settings_button).to_contain_text("Editing...")
```

**Testids:** `chat-participant-settings-button`

---

### Step 4 — Locate Welcome Message section

**Action:** Locate the "Welcome message" accordion in the edit canvas. It is expanded by
default.

**Observable:** `agent-welcome-message-input` textarea is visible.

**Testids:** `agent-welcome-message-input`

---

### Step 5 — Click into the Welcome Message field

**Action:** Click `agent-welcome-message-input`.

**Observable:** Field becomes active (text cursor visible).

---

### Step 6 — Type "edited from canvas"

**Action:** Clear the field and type `"edited from canvas"`.

**Observable:** `agent-welcome-message-input` has value `"edited from canvas"`.

**Assertion:**
```python
expect(agent_canvas_page.welcome_message_input).to_have_value("edited from canvas")
```

---

### Step 7 — Verify Save and Discard buttons become active

**Action:** Observe the canvas header after typing.

**Observable:** Both `agent-save-button` and `agent-discard-button` are enabled
(not disabled).

**Assertion:**
```python
expect(agent_canvas_page.save_button).to_be_enabled()
expect(agent_canvas_page.discard_button).to_be_enabled()
```

**Testids:** `agent-save-button`, **`agent-discard-button` (needs adding)**

---

### Step 8 — Click Save; verify success notification

**Action:** Click `agent-save-button`.

**Observable (primary):** `toast-message` appears containing text `"The agent has been updated"`.

**Observable (secondary):** `agent-save-button` and `agent-discard-button` return to
disabled state (form is clean again).

**API evidence:** `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}`
returns 201 Created.

**Assertion:**
```python
expect(page.get_by_test_id("toast-message")).to_contain_text("The agent has been updated")
# or assert Save returns to disabled:
expect(agent_canvas_page.save_button).to_be_disabled()
```

**Testids:** `agent-save-button`, `toast-message`

**Note — secondary 404:** During live execution, `PUT entity_settings/prompt_lib/399/undefined/9327`
returned 404 (undefined in path = missing parameter in AgentEditor.jsx secondary call).
The main save (PUT application) succeeded with 201. This secondary 404 is a **potential UI
bug** but does not affect the case outcome — the test should NOT assert absence of console
errors for this step, or should filter `entity_settings` from its console-error check.

---

### Step 9 — Close the canvas

**Action:** Click `agent-canvas-close-button`.

**Observable:** Canvas slides closed. URL returns to `/chat` (no `?edited_participant_id`
query param).

**Assertion:**
```python
expect(page).to_have_url(re.compile(r"/chat$"))
```

**Testids:** `agent-canvas-close-button`

---

### Step 10 — Verify "Editing..." chip is gone

**Action:** Observe the composer chip area after canvas close.

**Observable:** `chat-participant-settings-button` no longer contains "Editing..." text.

**Assertion:**
```python
expect(chat_page.chat_participant_settings_button).not_to_contain_text("Editing...")
```

---

### Step 11 — Navigate to Agents section

**Action:** Click the "Agents" button in the sidebar (or navigate to `/agents/all`).

**Observable:** Agents list page opens; agent card is visible.

---

### Step 12 — Click on the test agent

**Action:** Click the agent's card (by `entity-card-name` testid filtered by agent name,
or by navigating directly to `/agents/all/{agent_id}?viewMode=owner`).

**Observable:** Agent detail/edit form opens.

---

### Step 13 — Scroll to Welcome Message section

**Action:** Scroll to the "Welcome message" accordion. It is expanded by default.

**Observable:** `agent-welcome-message-input` textarea is visible.

---

### Step 14 — Verify Welcome Message displays "edited from canvas"

**Action:** Read the value of `agent-welcome-message-input`.

**Observable:** The textarea value equals `"edited from canvas"` — confirming the change
made in the chat canvas was synchronised to the agent record.

**Assertion:**
```python
expect(agent_form_page.welcome_message_input).to_have_value("edited from canvas")
```

**Testids:** `agent-welcome-message-input`

---

## Blocked Steps

None — all 14 steps executed against the live system without blockers.

---

## Observations

1. **`agent-discard-button` missing.** `Button.DiscardButton` in
   `EditorHeader.jsx` (line 85) is rendered without a `data-testid`. The fix is:
   - Add `discardButtonTestId` prop to `EditorHeader`
   - Wire it: `<Button.DiscardButton data-testid={discardButtonTestId} …>`
   - Pass `discardButtonTestId="agent-discard-button"` from `AgentEditor.jsx`
   Steps 7 and 9 use this button; without the testid, only text-label matching
   is available (non-compliant with the locator policy).

2. **Secondary 404 on `entity_settings`.** After a successful agent save
   (`PUT application` → 201), a second call `PUT entity_settings/prompt_lib/399/undefined/9327`
   fires with `undefined` as a URL segment and returns 404. This indicates the
   `entity_settings` endpoint is being called with a missing parameter (likely
   `folder_id` or `entity_type_id`). The main save is unaffected. Filed for triage:
   the automated test should exclude `entity_settings` from console-error assertions.

3. **"echo" agent not present in Private project.** The case specifies agent name `echo`,
   but no such agent exists in project 399 (Private). The test data strategy should
   use a dedicated automation fixture agent (created via API before the test, restored
   after). Alternatively, create the "echo" agent in the target project as a one-time
   setup step.

4. **"Editing..." vs "Viewing..." state.** The chip state is determined by agent ownership:
   owned agents show "Editing...", public agents show "Viewing...". The testid
   `chat-participant-settings-button` is stable in both modes; the text content
   changes. This is confirmed in `AgentEditorPanel.jsx:291`.

---

## Page Objects Needed

| Page object | Class / file | Status |
|---|---|---|
| `ChatPage` | `automation/pages/chat_page.py` | Existing — add `participant_settings_button` LD |
| `AgentCanvasPage` | `automation/pages/agent_canvas_page.py` | Existing — add `discard_button` LD (after testid added) |
| `AgentFormPage` | `automation/pages/agent_form_page.py` | Existing — `welcome_message_input` already present |

New `LocatorDescriptor` fields needed:
```python
# In ChatPage
chat_participant_settings_button = LocatorDescriptor(testid="chat-participant-settings-button")

# In AgentCanvasPage (after agent-discard-button is added to EliteaUI)
discard_button = LocatorDescriptor(testid="agent-discard-button")
```

---

## Test File Target

```
automation/tests/ui/chat/test_chat_canvas_edit_agent.py
```

Class: `TestChatCanvasEditAgent`
Method: `test_edit_agent_welcome_message_syncs_to_agents_section`

Markers: `@pytest.mark.p2`, `@pytest.mark.chat`, `@pytest.mark.regression`
