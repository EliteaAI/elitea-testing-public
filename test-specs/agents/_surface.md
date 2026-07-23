# Surface digest: Agent Detail Page (`/agents/all/{id}`)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

## Navigation

- **Always use `?viewMode=owner`**: bare `/agents/all/{id}` 404s locally
  ("Page not found. Try Home page") — confirmed live 2026-07-24. The
  existing `AgentDetailPage.navigate(agent_id)` already appends
  `?viewMode=owner` correctly (`agent_detail_page.py:414-424`) — don't
  regress this if you touch that method. Matches the documented
  `public_application` vs `application` endpoint-split quirk in
  `.agents/role-overrides.md` § 4xx/5xx cross-check.
- `wait_for_page_load()` waits on `information_section` + the Name input
  having a non-empty value — reliable, reuse it.

## Embedded chat (right panel, `ConfigurationTab.jsx` → `ConfigurationRightContent`)

All testids confirmed on-main, already wired as `LocatorDescriptor` fields on
`AgentDetailPage` (no gap):

| Purpose | Testid | Page-object field |
|---|---|---|
| Message list container | `chat-message-list` | `chat_message_list` |
| Individual message | `chat-message-item` | `chat_message_item` |
| Message input | `chat-message-input` | `chat_message_input` |
| Send button | `chat-send-button` | `chat_send_button` |
| Clear/new-conversation button | `chat-clear-button` | `chat_clear_button` |

- `send_chat_message(text)` — fills input, clicks send. Existing method,
  reliable.
- `wait_for_chat_response(initial_count, stable_duration_ms=3000, timeout=60000)`
  — polls message count, then waits for the last message's text to stabilize.
  AI responses arrive over WebSocket ~2–8s after send in this env (observed
  5–7s "Thought for N secs" + streaming) — always use this wait, never a
  fixed sleep.
- **`chat-clear-button` ("Clear the chat") starts a brand-new conversation —
  it does NOT delete/overwrite the previous one.** Confirmed live: the prior
  conversation remains intact and reappears as its own entry in Run History.
  This is the mechanism to use to manufacture "≥2 distinct runs" test data
  for any case needing it (send msg → wait response → `clear_embedded_chat()`
  → send different msg → wait response ⇒ 2 runs).
  - **Aria-label footgun (pre-existing, documented in code already):**
    `RunHistoryContainer.jsx`'s close ("X") button carries
    `aria-label="clear the chat"` too (copy-paste leftover, unrelated to the
    actual Clear-chat button) — don't pick by aria-label/role text across
    these two; use the testids (`chat-clear-button` vs the run-history
    close button, which itself has NO testid — see gap below, not needed
    unless a future case tests closing the panel).

## Run History panel (`RunHistoryContainer` / `RunHistoryList` / `RunHistoryChat`, `entities/run-history/`)

Opened via the clock icon in the embedded-chat toolbar; **mutually exclusive**
with the embedded chat view (`ConfigurationTab.jsx`:
`{showHistory && <RunHistoryContainer/>} {!showHistory && <ConfigurationRightContent/>}`)
— only one of the two chat views is ever mounted at a time.

| Purpose | Testid | Status |
|---|---|---|
| "View run history" button (clock icon) | `pipeline-history-tab` | **on-main ✓** (pre-existing). Misleadingly named (leftover from the Pipelines call site) — shared by `ViewRunHistoryButton.jsx`, reused identically by Agent/Pipeline/Toolkit/MCP. Not a new finding; out of scope to rename per-case. |
| Run History list row (click to select a run) | — | **needs-adding** (`RunHistoryListItem.jsx:141-144`, the outer clickable `Box`). Grepped the entire `entities/run-history/` tree — zero `data-testid` anywhere. Suggested: dynamic `run-history-item-{conversationId}` (generic name — shared component, not agent-specific) + `data-selected="true"/"false"` state attribute (per `.agents/testing.md` state-via-data-attribute policy). |
| Run History chat pane (shows selected run's messages) | `chat-message-list` / `chat-message-item` | **on-main ✓, no gap** — `RunHistoryChat.jsx` reuses the same shared `ChatMessageList` component as the live embedded chat; since the two views are mutually exclusive, the existing `chat_message_list` field/`_embedded_chat_messages()` helper work unchanged while the panel is open. |
| Run History panel close ("X") button | — | needs-adding IF a case ever tests closing the panel; not needed for ELITEA-1877. Aria-label is `"clear the chat"` (copy-paste bug, see above) — don't rely on it. |
| Sort headers (Date/Version/Duration) | — | needs-adding IF a case ever tests sorting; not needed for ELITEA-1877. |
| 3-dot row menu (Share link / Delete / Restore chat) | `run-history-menu-menu-button` (via shared `DotMenu` component, static `id="run-history-menu"` — same non-unique-static-id pattern as `ConversationItem.jsx`'s DotMenu, tracked tech debt elsewhere) | needs-adding IF a case ever tests these actions; not needed for ELITEA-1877. |

**Row-selection behavior confirmed correct (live, ELITEA-1877 exploration,
2026-07-24):** clicking a specific past (non-most-recent) run correctly
highlights only that row and loads only that run's messages into the chat
pane; switching back and forth between two runs re-verified in both
directions. See the AFS's debugging note
(`l2_select-past-run-loads-chat-messages_ELITEA-1877.md`) for a documented
false-alarm caused by an ambiguous raw CSS selector during exploration
(`.css-1o16zsr` is shared by both unselected rows — MUI-emotion hashes
identical computed `sx` to the same class; **never use this as a locator**,
it's exactly the kind of handle the testid-only policy exists to prevent).

## LLM model selector + Settings dialog (embedded chat panel, `LLMModelSelector.jsx` widget)

Confirmed live 2026-07-24 (ELITEA-1880 exploration, project `Private`/399, "Test
Agent" id 3). `LLMModelSelector.jsx` is a **shared widget** (docstring: "Used
across different parts of the application like ChatBox, TestSettings, etc.") —
its existing testids are deliberately generic, not agent-page-scoped; follow
that precedent for any new ones (don't prefix `agent-`).

| Purpose | Testid | Status |
|---|---|---|
| Model selector button group | `model-selector-button` | on-main ✓ (ELITEA-1881) |
| Model selector current-name button | `model-selector-name` | on-main ✓ (ELITEA-1881) |
| Model dropdown option (dynamic, keyed by API `name`) | `model-selector-option-{name}` | on-main ✓ (ELITEA-1881) |
| **Settings (⚙️) gear button** — opens the Model settings dialog | — (only `aria-label="model settings menu"`) | **needs-adding**: `LLMModelSelector.jsx` (`src/[fsd]/widgets/llm-model-selector/ui/LLMModelSelector.jsx`, the `<Button aria-label="model settings menu">`) — no `data-testid` at all. Suggested: `model-settings-button` (generic, matches the `model-selector-*` naming family). |
| **Model settings dialog** (container) | — | **needs-adding**: `LLMSettingsDialog.jsx` renders `Modal.BaseModal` with NO `data-testid`/`titleTestId`/`closeButtonTestId` props wired, even though `BaseModal` (`src/[fsd]/shared/ui/modal/BaseModal.jsx`) already accepts all three. Suggested: `model-settings-dialog` / `model-settings-dialog-close-button`. Pure prop-wiring, no new component code. |
| **Reasoning slider** (Low/Medium/High, only rendered for reasoning-capable models) | — | **needs-adding**: `ReasoningSlider.jsx` wraps the shared `DiscreteSlider` (`src/[fsd]/shared/ui/slider/DiscreteSlider.jsx`). `DiscreteSlider` forwards extra props (`...sliderProps`) onto the inner MUI `<Slider>` only — NOT onto its outer container `Box` that also holds the low/medium/high labels row. A testid passed straight through today would land on the slider control but not scope the labels. Suggested: add a `containerTestId`-style prop to `DiscreteSlider` (or hardcode nothing at that shared-component level — thread from the caller) so `ReasoningSlider.jsx` can pass `model-settings-reasoning-slider` covering the whole labeled section. **Not a generic `DiscreteSlider`-level hardcode** — it's reused by the differently-labeled "Creativity" slider (1–5, non-reasoning models) and a shared testid would collide/be ambiguous between the two. |
| **Max Completion Tokens radio group** (Default/Custom) | — (dynamic, ready to wire) | **needs-adding, but trivial**: the underlying `Checkbox.RadioButtonGroup` (`src/[fsd]/shared/ui/checkbox/RadioButtonGroup.jsx`) ALREADY supports a `testId` prop that yields `${testId}-${item.value}` per option — `MaxTokensSection.jsx` (`src/[fsd]/widgets/llm-model-selector/ui/settings/MaxTokensSection.jsx`) just isn't passing it. Suggested: pass `testId="model-settings-max-tokens-mode"` → yields `model-settings-max-tokens-mode-auto` / `model-settings-max-tokens-mode-custom` (item values are already lowercase `'auto'`/`'custom'`). No new component code, one prop to wire. |
| Dialog "Capabilities" chips (Image analysis / Reasoning) | — | not touched by ELITEA-1880 (case doesn't assert these) — no gap filed. |
| Dialog footer Cancel/Apply buttons | — | not touched by ELITEA-1880 (case closes via the header Close (X), doesn't Apply) — no gap filed; `LLMSettingsDialog.jsx` renders its own custom `actions` (not `BaseModal`'s built-in `onConfirm` path), so these would need their own `data-testid` on the `Button.BaseBtn`s if a future case clicks them. |

**Case-text clarification (not a defect):** the case text (ELITEA-1880) says
Max Completion Tokens options are "Auto/Custom" — the live UI labels them
**"Default"/"Custom"** (`MaxTokensSection.jsx` — `items` array, `label: 'Default'`,
internal `value: 'auto'`). Cosmetic case-text drift; assert the live label.

**Model-type-conditional dialog contents (platform behavior, confirmed live):**
the Model settings dialog's top section is genuinely conditional on the
selected model's declared capabilities (from
`GET /api/v2/configurations/models/{project_id}`): models with `"Supports
reasoning"` in their dropdown chip (e.g. GPT-5.4, GPT-5.2, GPT-5.4 -not- mini,
all Anthropic/Azure Claude variants) show the **Reasoning** slider (3 discrete
levels: Low/Medium/High); models WITHOUT that capability (e.g. `GPT-5 mini`,
`GPT-5.4-mini`) show a **Creativity** slider instead (5 discrete levels:
Low(0.2)/Mid-Low(0.4)/Medium(0.6)/Mid-High(0.8)/High(1), temperature-based).
Max Completion Tokens (Default/Custom) and the Capabilities chip row appear
for both types. ELITEA-1880's case text ("Reasoning slider ... for standard
models") is testing the reasoning-capable-model path specifically — pick a
model with the "Supports reasoning" chip (e.g. `GPT-5.4`) to exercise it.

## `verify_tabs_visible()` — dead code, not this surface's real mechanism

`AgentDetailPage.verify_tabs_visible()` (`agent_detail_page.py:473-479`)
references `self.configuration_tab`/`self.history_tab`, which are defined
only on `PipelineDetailPage`/`ToolkitDetailPage`, NOT on `AgentDetailPage` or
its parents. No test calls this method (`grep -rln "verify_tabs_visible"
automation/tests/` → no hits) — it doesn't affect anything currently, but if
you're tempted to use it for an agent-page case: don't, it will raise. The
Agent page's actual "history" UI is the toggle panel documented above, not a
Configuration/History tab pair (that pattern exists only for
Pipelines/Toolkits).
