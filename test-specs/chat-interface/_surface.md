# Chat-interface surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Chat surface (`/chat`).
Not a substitute for execution — verify a handle as you use it. One writer at
a time; last confirmed by: test-automation-engineer (combined analyst+
implementer), ELITEA-2078, 2026-08-20 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2217, 2026-08-19
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: qa-engineer analyst, ELITEA-2208/2470, 2026-08-19
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: qa-engineer analyst, ELITEA-2207/2469, 2026-08-19
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: qa-engineer analyst, ELITEA-2206, 2026-08-19
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: qa-engineer analyst, ELITEA-2205/2468, 2026-08-19
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2198, 2026-08-19 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2196, 2026-08-19 (supersedes nothing
below — new section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2089, 2026-08-18
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2179/2466, 2026-08-15 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2192/2193/2194,
2026-08-15 (supersedes nothing below — new section, other sections unchanged;
previous confirmer: qa-engineer analyst, ELITEA-2189/2190/2191,
2026-08-15 (supersedes nothing below — new section, other sections unchanged;
previous confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2175/2176, 2026-08-15 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2171/2172, 2026-08-15
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2460, 2026-08-15 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2461, 2026-08-15
(supersedes nothing below — new section, other sections unchanged; previous
confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2157/2158, 2026-08-15 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2155/2156, 2026-08-15 (supersedes nothing
below — new section, other sections unchanged; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2152/2153, 2026-08-15 (supersedes nothing
below — new section, other sections unchanged; previous confirmer: qa-engineer analyst,
ELITEA-2146/2147/2148,
2026-08-15 (supersedes nothing below — new section, other sections unchanged;
previous confirmer: qa-engineer analyst, ELITEA-2142/2143/2144/2145,
2026-08-15 (supersedes nothing below — new section, other sections unchanged;
previous confirmer: test-automation-engineer (combined analyst+
implementer), ELITEA-2136/2138/2139/2140/2141, 2026-08-15 (supersedes nothing
below — new section, other sections unchanged; previous confirmer:
test-automation-engineer (combined analyst+implementer), ELITEA-2128/2129,
2026-08-15 (supersedes nothing below — new
section, other sections unchanged; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2123/2127, 2026-08-15; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2122, 2026-08-15; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2121/2130, 2026-08-15; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2457, 2026-08-15; previous confirmer: test-automation-engineer
(combined analyst+implementer), ELITEA-2133/2134, 2026-08-15; previous confirmer:
test-automation-engineer (combined analyst+implementer), ELITEA-2118/2119/2120, 2026-08-15; previous confirmer:
test-automation-engineer (combined analyst+implementer), ELITEA-2163/2164/
2165/2463, 2026-08-15; previous confirmer:
test-automation-engineer (combined analyst+implementer), ELITEA-2115/2116/
2117/2456, 2026-08-15; previous confirmer:
qa-engineer analyst, ELITEA-2111, 2026-08-15;
previous confirmer: ELITEA-2105/2106/2107/2108/2109, 2026-08-15;
ELITEA-2103/2104, 2026-08-14; ELITEA-2101/2102, 2026-08-14;
ELITEA-2100, 2026-08-14; ELITEA-2099, 2026-08-14; ELITEA-2091, 2026-08-14;
ELITEA-2458, 2026-08-07; ELITEA-2086/2087/2088, 2026-08-03)))))))).

## ELITEA-2217 — Context Management ON / Auto-Summarization OFF: token
## tracking continues past max (warning icon fires) but Summaries stays 0
## and no "Summarizing" indicator ever appears; third leg of the
## {2216, 2217, 2218} context-management family. ONE new testid needed,
## ONE non-blocking product defect filed (#1605).
- Settings > Memory (`/settings/memory`): `automatic-summarization-toggle`
  (`UserProfileSettingsPage`) toggled OFF independently of
  `context-management-toggle` (stays ON) — confirmed live both toggles
  default ON for a fresh session; `disable_automatic_summarization()` /
  `enable_automatic_summarization()` autosave correctly (`PUT
  /api/v2/social/author/` → 200), same as the Context Management toggle.
- Per-conversation "Edit context settings" dialog (`context-budget-edit-button`
  → `ContextStrategyModalContent`): reused ELITEA-2218's low-threshold
  technique (`context_modal_max_tokens_input` + `context_modal_save_button`)
  to reach >100% utilization in ~5 long exchanges instead of the account's
  full ~6,400-token default. **New product defect confirmed + filed (#1605,
  non-blocking):** when Automatic Summarization is globally OFF, the
  dialog's Target Summary Tokens field is correctly disabled but its STALE
  value still cross-field-validates against a new Max Context Tokens value —
  Save stays disabled unless the new Max Context Tokens is ≥ the frozen
  Target Summary Tokens value. Workaround: read the live Target Summary
  Tokens value first and pick a Max Context Tokens ≥ it (`5000` worked
  against a `4096` frozen target this session), or configure the desired
  low pair while summarization is still ON, then disable it after.
  **Do not reuse `set_context_strategy_thresholds()` unmodified for this
  case** — it also fills the disabled Target Summary Tokens field, which
  Playwright errors on ("element is not enabled").
- The dialog's OWN "Enable automatic summarization" switch
  (`ContextStrategySummarization.jsx`) mirrors the global toggle's state and
  disables its own child fields (Summarization Instructions, Target Summary
  Tokens) when unchecked — confirmed live (`.checked === false`) — but
  carries **NO testid** (confirmed via source read + a live
  `querySelectorAll('[data-testid]')` sweep of the open dialog, zero hits),
  unlike its sibling `context-modal-management-toggle` one section up in
  the same dialog. `testid needed: context-modal-summarization-toggle`.
- `context_budget_warning_icon`/`is_context_budget_warning_visible()` fires
  identically whether Automatic Summarization is ON (ELITEA-2218) or OFF
  (this case) — it is driven purely by utilization %, not by the
  summarization flag. `chat-answer-model-chip` never reads "Summarizing the
  chat history" when Automatic Summarization is OFF, confirmed by polling it
  after all 5 sends (stays plain model-name text throughout).
- Full AFS: `test-specs/chat-interface/l3_auto-summarization-disabled-no-trigger-at-max-tokens_ELITEA-2217.md`.

## ELITEA-2208/2470 — `#` hash-search SELECT-A-PIPELINE adds it to
## PARTICIPANTS + composer active-participant chip + pipeline responds,
## family AFS, direct pipeline-flow sibling of ELITEA-2207/2469 (same
## session), ZERO new testids, ZERO defects, TWO case-text clarifications
## (mention is a composer CHIP not literal text; a dynamically-selected
## ambient pipeline may respond with a genuine execution-error card)
- **Same session as ELITEA-2207/2469 (this digest's section immediately below) —
  reused ALL of its handles directly (`chat-switch-participant-button`,
  `chat-participants-badge-{section}`, `chat-participant-row-{uniqueId}`,
  `chat-participant-icon`, `chat-participant-remove-button`,
  `delete-confirm-button`) plus ELITEA-2206's hash-search-item handles —
  zero re-derivation needed for anything except the pipeline-specific
  `uniqueId` prefix (below).**
- **Pipeline participant `uniqueId` prefix is `pipeline_` (singular), NOT
  `application_`** — confirmed via BOTH a live Playwright-generated locator
  (`chat-participant-row-pipeline_8056_399`, from a real hover interaction)
  AND source (`getChatParticipantUniqueId()` in
  `EliteaUI/src/[fsd]/features/chat/participants/lib/helpers/participants.helpers.js`):
  a participant's `entity_name` resolves to `ChatParticipantType.Pipelines`
  (`'pipeline'`) whenever `entity_settings.agent_type === 'pipelines'`,
  distinct from an agent's `'application'`. **`get_agent_participant_row()` /
  `remove_agent_participant()` both hardcode the `application_` prefix and
  cannot resolve a pipeline row as-is** — this family's implementation needs
  an additive generalization (optional `entity_type` param, or a sibling
  method), same shape as the `agent_project_id` param ELITEA-2207/2469 already
  added to the same two methods for a different reason. Not yet built as of
  this analysis pass — implementer's job, spec'd in the AFS's Automation Hints.
- **Version-text shape DIFFERS from the agent family — do not reuse its
  regex.** The agent family's popover row shows a "ver"/"vX.Y" auto-generated
  string; a PIPELINE's row shows its own **version's literal NAME** instead
  (e.g. "base" this session, both in the popover row text and in the
  composer's own "version selector menu" button). Pipeline versions are
  user-named (e.g. "base", "prod", "v2-experimental"), so
  `re.match(r"v(er\b|\d)", ...)` would be a false constraint here — assert
  only that a non-empty version-text remainder exists after the pipeline's
  name.
- **CASE-TEXT CLARIFICATION 1 (same pattern as ELITEA-2207/2469, reconfirmed
  for pipelines) — the pipeline "mention" is NOT inserted as text into the
  message input.** After clicking a pipeline card, `chat-message-input` stays
  completely empty; the pipeline instead renders as a composer chip
  (`chat-switch-participant-button`, accessible name "Switch Pipeline" this
  session vs "Switch Agent" for the agent case — same physical testid, text
  differs per active participant type).
- **CASE-TEXT CLARIFICATION 2, pipeline-specific, NEW this session — a
  dynamically-selected ambient pipeline may respond with a genuine
  EXECUTION-ERROR card instead of a substantive answer, and that still
  satisfies "the pipeline processes and responds."** Live-confirmed: selected
  "AutoTest_Pipeline_probe_2020" (ambient DEV probe-test pipeline data),
  sent "hello", received "Pipeline has no nodes to execute. Please add at
  least one node to the pipeline before running it." — a REAL, complete,
  non-transient response (Copy button present) genuinely produced by the
  system (the pipeline genuinely attempted execution and correctly reported
  its own empty-node precondition), attributed to the pipeline in the message
  header, immediately followed by the PIPELINES badge still reading "1".
  Not a substitution, not a defect. **Implementer implication**: assert
  generically (message count grows by 2, response attributed to the selected
  pipeline's name, badge persists) — never assert specific response TEXT,
  since which ambient pipeline gets dynamically selected (and whether it has
  configured nodes) is account-data-dependent.
- **Zero new testids** — every handle needed already exists: pre-existing
  `chat-switch-participant-button`/`chat-participants-badge-pipelines`
  (section: 'pipelines', confirmed via `git grep` in
  `CollapsedPerticapantsList.jsx`)/`chat-participant-row-{uniqueId}`/
  `chat-participant-icon`/`chat-participant-remove-button` (all **on-`main`
  or `automation/testids` ✓** per the same provenance ELITEA-2207/2469
  already established) plus `chat-hash-search-item-{}_{}`/`{testId}-type`
  from ELITEA-2206 — reused verbatim, zero pipeline-specific new testid.
- **Account-data hazard reconfirmed a SECOND time this session, worse this
  time**: bare `/chat` navigation left the composer blocked by a persistent
  `MuiCircularProgress`/`MuiBox` overlay for 15+ seconds straight (>15 retry
  cycles across two separate click attempts, never cleared) — same class as
  ELITEA-2207/2469's own "8+ retry cycles" entry below, but this attempt
  never resolved at all within the session's patience budget. Worked around
  identically (navigate directly to an existing conversation id instead of
  bare `/chat`); the shipped test's `conversation_id` fixture sidesteps this
  by construction, same as the agent family.
- **Cleanup performed live**: removed the added pipeline participant via
  hover → "Remove pipeline" (note: accessible name is "Remove pipeline", NOT
  "Remove agent" — same physical `chat-participant-remove-button` testid,
  text is component-driven per entity type) → confirmed "Remove" in the
  "Remove pipeline?" dialog (`delete-confirm-button`, same testid as the
  agent family's "Remove agent?" dialog) — `chat-participants-badge-pipelines`
  confirmed gone from the DOM afterward. Sent "hello" + the pipeline's
  error-response remain in `/chat/9082`'s history (removing a participant
  does not delete prior messages) — cosmetic only.
- AFS (family, both TMS ids, same `afs_path`):
  `test-specs/chat-interface/lextend_hash-search-select-pipeline-adds-participant-and-responds_ELITEA-2208.md`.

## ELITEA-2207/2469 — `#` hash-search SELECT-AN-AGENT adds it to PARTICIPANTS
## + composer active-participant chip + agent responds, family AFS, ZERO new
## testids (pure reuse of ELITEA-2206's just-landed hash-search handles +
## pre-existing composer/participants-panel machinery), ZERO defects, ONE
## case-text clarification (mention is a composer CHIP, not literal text in
## the message field)
- **Same session as ELITEA-2206 (this digest's section immediately below) —
  reused its freshly-landed `chat-hash-search-item-{}_{}` /
  `{testId}-type` testids directly, zero re-derivation needed.** Confirms the
  digest's own "read the neighbours first" discipline pays off across units
  in the SAME batch, not just across sessions.
- **`test_add_participant_via_hash_search` (covering, merged) proves
  open→select→close and NOTHING ELSE** — it clicks whatever the FIRST result
  happens to be (agent or pipeline, unscoped) and asserts only that the
  dropdown closes. It never opens the participants popover, never inspects
  the composer, never sends a message. This family's entire subject —
  participant-panel update, composer chip, message delivery, agent response,
  participant persistence — is a clean, previously-untouched gap on the SAME
  selection mechanism.
- **CASE-TEXT CLARIFICATION, not a defect (reverse-masking guard) — the
  agent "mention" is NOT inserted as text into the message input.** Both
  cases say the agent name appears "in the message field" — live-confirmed
  via screenshot this session: after clicking an agent card, `chat-message-input`
  stays completely EMPTY (placeholder unchanged). Instead the selected agent
  renders as a dedicated chip in the composer's control row
  (`chat-switch-participant-button`, pre-existing testid + assertion helper
  `is_agent_participant_in_composer()` from the ELITEA-1736 rework — already
  in the page object, zero new code). This is the SAME established pattern
  every other participant-mention family in this app uses (slash-mention
  toolkit/MCP participants behave identically) — not specific to `#`-search,
  not a regression. Assert the real composer-chip observable; the case
  text's "message field" wording is the stale half.
- **Live-confirmed end-to-end, zero substitution**: selected "Agent testing
  skills" (agent-type card, `chat-hash-search-item-1_280`) on an existing
  conversation (`/chat/9082`) → `chat-participants-badge-agents` badge
  appeared (previously absent) → opened the popover → AGENTS section showed
  the agent's name + a "ver" version control + a leading icon (row is the
  SAME shared participant-row component the expanded panel uses, per
  `PARTICIPANT_ROW`) → typed "hello", sent → message header showed "Test Bot
  to Chat now Agent testing skills" (real send-to-participant attribution) →
  agent replied "Hello! How can I help?" (full round-trip, Copy button
  present, non-transient) → AGENTS badge still read "1" afterward (confirmed
  a genuine `data-testid="chat-participants-badge-agents"` element read, not
  assumed). Zero console errors throughout.
- **Zero new testids** — every handle needed already exists: pre-existing
  `chat-switch-participant-button`/`chat-participants-badge-agents`/
  `chat-participant-row-{uniqueId}`/`chat-participant-remove-button` (all
  **on-`main` ✓**, ELITEA-1736/1793 reworks) plus the just-landed
  `chat-hash-search-item-{}_{}`/`{testId}-type` from this session's own
  ELITEA-2206 unit (**on-`automation/testids` only**, awaiting human
  cherry-pick same as ELITEA-2206's own row).
- **Cleanup performed live**: removed the added agent participant via the
  existing `remove_agent_participant(agent_id)` mechanism (hover → "Remove
  agent" → confirm dialog) — badge confirmed gone from the DOM afterward
  (matches `wait_for_participants_badge_absent()`'s documented "disappears
  at count 0" contract). The sent "hello" + the agent's reply remain in
  `/chat/9082`'s message history (removing a participant does not delete
  prior messages — consistent with every other participant-removal
  precedent already in this digest) — cosmetic only.
- **Gotcha, NOT a product defect — heavy-account bare `/chat` hit a
  persistent loading-spinner block this session.** Navigating to bare
  `/chat` on this account (65+ folders, hundreds of conversations per the
  sidebar) left a `MuiCircularProgress` overlay intercepting the composer
  for 15+ seconds straight (8+ retry cycles, never resolved before this
  session gave up and switched to an existing conversation instead).
  Distinct from the already-documented "`/chat` bare redirects to
  last-viewed conversation as a delayed effect" gotcha (ELITEA-2175/2176
  section below) — this was a persistent BLOCKING overlay, not a silent
  redirect. Worked around by navigating directly to an existing conversation
  id instead of bare `/chat`. **Implementer implication**: the shipped test
  should use the `conversation_id` fixture (fresh, API-seeded — navigates to
  `/chat/{id}` directly, never touches the bare-`/chat` redirect/loading
  path at all) rather than the ambient "new chat" screen, sidestepping this
  entirely.
- AFS (family, both TMS ids, same `afs_path`):
  `test-specs/chat-interface/lextend_hash-search-select-agent-adds-participant-and-responds_ELITEA-2207.md`.

**Resolved/added during ELITEA-2207/2469 implementation (test-automation-engineer):** the "Zero new
testids" claim above held only for the ONE agent this exploration session happened to select
("Agent testing skills", a current-project agent with a custom icon). The shipped test resolves the
agent DYNAMICALLY (first agent-type card, per this AFS's own resilience requirement) instead of a fixed
name, and the account's first agent-type `#` result is routinely Agent-Hub ("Public") sourced with NO
custom icon — surfacing two gaps this exploration's one lucky pick didn't hit:
- `chat-hash-search-item-{}_{}-name` (`EliteaAI/EliteaUI@840e251d`) — the name Typography in
  `NewParticipantCard.jsx` had no testid; needed to read the dynamically-selected agent's exact name.
- `chat-participant-icon` (`EliteaAI/EliteaUI@dd44ce90`) — the pre-existing `chat-participant-avatar`
  testid is CONDITIONAL on the entity having a custom-uploaded icon (`EntityIcon.jsx`'s `imgTestId` only
  applies to the `<img>` branch); an agent with no custom icon renders a testid-less fallback SVG. Added
  an unconditional testid on `EntityIcon`'s own container instead — benefits BOTH the expanded-panel row
  and this popover row (same shared `ParticipantItem.jsx` component).
- **`application_{agent_id}_{project_id}` uses the AGENT's OWN home project, not the conversation's** —
  this exploration's picked agent happened to live in the same project as the conversation, masking that
  `get_agent_participant_row()`/`remove_agent_participant()`/`hover_agent_participant_row()` all hardcode
  `settings.elitea_project_id`. An Agent-Hub-sourced agent's real participant row uses its OWN
  `entity_meta.project_id` (the public project, e.g. `application_6_1`, not `application_6_399`).
  `get_agent_participant_row()` gained a backward-compatible optional `agent_project_id` param (default
  unchanged) rather than a body rewrite — additive, existing caller re-run and confirmed unaffected.
  **Implementer implication for future dynamic-agent-selection tests on this surface**: never assume the
  selected agent's project id equals `settings.elitea_project_id` — read it off the hash-search item's
  own testid (`chat-hash-search-item-{project_id}_{id}`) instead.

## ELITEA-2206 — `#` hash-search participant dropdown (agents+pipelines,
## mixed sources), NEW surface for THIS digest (`chat-hash-search-participants`),
## `extend-existing` against the pre-existing `TestHashSearch` class, TWO new
## testid gaps found (container + dynamic item), ZERO defects
- **First digest entry for the `#` hash-search feature** — distinct from the
  `/`-slash-mention family (ELITEA-2202/2203/2204/2205/2468, toolkit/MCP
  participants) and the `~`-skill-mention family. `#` opens a
  `SearchResultList.jsx` → shared `NewParticipantList.jsx` panel listing
  **agents AND pipelines** (not toolkits/MCPs/skills), titled literally
  `"Search results"` (component's `title` prop — DOM text is sentence-case,
  NOT all-caps; any CSS uppercase transform is visual only).
- **A merged spec already exists for this feature under a DIFFERENT, older
  TMS-id lineage** — `test_chat_interface.py::TestHashSearch` (2 methods,
  `test_hash_search_participants` / `test_add_participant_via_hash_search`)
  carries `@allure.issue` links to `ELITEA-0498`/`ELITEA-0501`, not
  `ELITEA-2206`. Grepping this digest or `test-specs/` BY TMS ID would have
  missed it entirely — found only by grepping the SUITE by behaviour
  (`hash_search`) per this skill's own § 2b discipline. Confirms the standing
  caution: search by observable/label, never by case id.
- **Covering tests only prove OPEN + select-to-close** — never inspect a
  single result card's own contents (subtitle text, icon, source label), and
  never prove the click-away-without-selecting close path. Live-confirmed gap
  assertions this session (bare `#` on an existing conversation, `/chat/9082`):
  per-card subtitle is literally lowercase `agent`/`pipeline`
  (`NewParticipantCard.jsx`'s `typeText`, case text says capitalized —
  **case-text drift, clarification not defect**, assert the real value); every
  card carries an icon (custom `img "elitea"` OR two-letter initials avatar,
  never absent); a `"Public"` chip marks Agent-Hub/public-project items,
  absent chip marks current-project items, BOTH present in one bare-`#`
  result set (`useParticipants({ projectFilter: 'all', ... })` is the
  mechanism — confirmed via source); clicking a definitely-outside element
  (sidebar nav button) closes the dropdown via `ClickAwayListener`, entirely
  independent of the covering test's select-to-close path.
- **`get_hash_search_first_option()`'s DOM-heuristic card-matching is now
  supersedable** — once the new `chat-hash-search-item-{project_id}_{id}`
  testid lands, a future pass could replace this ~30-line best-effort
  `xpath`/`filter()` heuristic with a real selector. NOT done as part of this
  extension (Hard Rule: additive-only) — flagged for a future dedicated
  migration pass, same class as the `automation/pages/` #25/#42 tech debt.
- **Separate finding, NOT filed as a defect (existing merged code, unrelated
  to this case's own scope)**: both covering tests wrap their core
  dropdown-appears wait in `try/except: pytest.skip(...)` — a genuine product
  regression on the `#`-search feature's core behavior would currently report
  SKIPPED, not FAILED. Flagged for a future hardening pass, not touched here.
- **Two new testid needs, both `needs-adding`** (neither on `main` nor
  `automation/testids` — this is genuinely virgin ground, first case to touch
  the `#`-search DOM at all): `chat-hash-search-results-list` (container) +
  dynamic `chat-hash-search-item-{project_id}_{id}` (per-card). Both wired the
  SAME way `SlashSuggestionList.jsx` already wires its own
  `slash-mention-list`/`slash-mention-item-{}_{}` pair through the identical
  shared `NewParticipantList.jsx` component (`containerTestId`/`getItemTestId`
  props) — `SearchResultList.jsx` just doesn't forward them yet. Scope the
  wiring to the `ChatBox.jsx` call site only (existing-conversation flow, the
  one both covering tests and this extension exercise) — leave
  `NewConversationView.jsx`'s own `SearchResultList` call site untouched, no
  test in this family exercises it (canon #511).
- AFS: `test-specs/chat-interface/lextend_hash-search-shows-agents-and-pipelines-from-all-sources_ELITEA-2206.md`.

## ELITEA-2205/2468 — slash-mention MCP selection + available-tools panel,
## family AFS, ZERO new testids (pure reuse of ELITEA-2202/2203/2204's
## slash-mention surface), ONE new defect filed (#1596: zero-tool
## toolkit/MCP still opens an empty "available tools" panel)
- **`select_slash_mention_toolkit()` / `slash_mention_list` / `slash_mention_tool_list`
  / `SLASH_MENTION_ITEM` / `SLASH_MENTION_TOOL_ITEM` (all from `ChatPage`, added
  ELITEA-2202/2203/2204) work UNCHANGED for MCP participants — confirmed live
  this pass, both for a 3-tool MCP (`mcp.deepwiki.com`) and a genuinely
  zero-tool MCP.** `select_slash_mention_toolkit()`'s docstring already says
  "toolkit/MCP card" — it is not toolkit-specific despite the name.
- **`select_slash_mention_toolkit()` will TIMEOUT for a zero-tool
  toolkit/MCP** — its wait strategy (ELITEA-2204's own fix) waits for the
  first tool-item row to ATTACH, which never happens when the selected
  participant has zero tools. A caller testing the zero-tools branch must
  either inline the click + container-only wait, or the method needs an
  additive `wait_for_first_tool: bool = True` parameter. Not yet fixed on
  the page object as of this pass — next implementer's job.
- **Defect [#1596](https://github.com/EliteaAI/elitea-testing-public/issues/1596):
  a Toolkit/MCP with zero configured tools (`settings.available_mcp_tools`/
  `selected_tools == []`) still opens the "{name} available tools" panel —
  header renders, zero rows, no "no tools" empty-state message.** Root cause,
  read from source: `SlashSuggestionList.jsx`'s early-return
  (`if (!isToolsFetching && toolQuery && filteredTools.length === 0) return null;`)
  only hides the panel when a **typed tool-name filter** matches nothing — it
  does NOT cover "genuinely zero tools, no filter typed", so `<ToolList>`
  (`ToolList.jsx`) always renders its header Box regardless of `tools.length`.
  Applies identically to zero-tool Toolkit participants (same component, not
  MCP-specific) — filed from the MCP case that names the expected "no tools ⇒
  no panel" behavior explicitly. Deterministic (source-confirmed, no timing
  involved), reproduced twice live (immediate + after a 2s settle).
- **Creating a zero-tools MCP toolkit is trivial and honest**: `ToolkitAPI.
  create_remote_mcp_toolkit(name=..., url=<any working MCP URL>, tools=[])` —
  passing an empty `tools` list (instead of a `sync_mcp_tools()` result)
  produces a real toolkit resource with `available_mcp_tools: []`. No new
  fixture existed for this before this pass; suggested name
  `mcp_toolkit_no_tools` (mirror `mcp_toolkit_with_tools`'s shape).
- **The "disconnected" case-text variant collapses into the same UI code
  path as "zero tools"** — `SlashSuggestionList.jsx`'s `availableTools` memo
  reads `settings.available_mcp_tools` regardless of WHY it's empty (never
  synced, or sync genuinely failed) — no separate "disconnected" UI branch
  exists, confirmed via source read. One zero-tools fixture covers both
  case-text wordings; no need to simulate a real unreachable MCP server.
- **`onSlashSelectToolkit` / `onSlashCommitMention`
  (`useSlashMention.hooks.js:80-145`) are fully participant-type-agnostic** —
  no `isMcp` branching anywhere in either handler. The trailing-space-after-
  tool-selection mechanism ELITEA-2204 confirmed live for Toolkits transfers
  to MCPs by construction (same code path), not just by analogy.

## ELITEA-2196 — attachment chip CONTENTS (icon+X button+dark/light styling),
## ONE new testid (`chat-attachment-remove-chip-{index}`), zero defects
- **First case in this cluster to assert the chip's own contents, not just
  count/name.** ELITEA-2195 only checks the popper's counter/icon (no
  attach happens); ELITEA-2197/2200 attach files and check COUNT + toast,
  never a chip's icon/X-button/styling. This case closes that gap.
- **`chat-attachment-remove-chip-{index}` added** on `FileList.jsx`'s
  per-chip remove `Box` (line ~98, direct `data-testid` attribute — no
  wrapper, no hook change, no MUI-internal replacement).
  `EliteaAI/EliteaUI@7f29c3dc`, `automation/testids` only (not yet on
  `main`). Live-confirmed via HMR: attribute present on all 4 chips,
  `.click()` on it genuinely removes exactly that one chip (functional,
  not just present) — reconfirmed a real `onDeleteFile` call, no
  substitution.
- **Naming pitfall, caught by the test's own first run (not just source
  review) — record this pattern for any future dynamic testid added under
  an existing `^=` PREFIX matcher.** The ELITEA-2197 AFS had reserved this
  exact testid as `chat-attachment-chip-remove-{index}` — that name starts
  with the SAME literal substring `ChatPage.CHAT_ATTACHMENT_CHIP_PREFIX`
  (`[data-testid^="chat-attachment-chip-"]`) matches, so every remove
  button silently became an extra "chip" to `get_attachment_chip_count()`
  (an EXISTING, MERGED ELITEA-2197 caller) — live-confirmed: attaching 4
  files resolved `CHAT_ATTACHMENT_CHIP_PREFIX`'s count to 8, not 4.
  Renamed to `chat-attachment-remove-chip-{index}` (distinct prefix, zero
  collision) and re-verified clean. **Lesson: before naming ANY new
  dynamic testid in a family that already has a `^=` prefix constant, grep
  for that prefix's existing string first** — a new testid literally
  starting with an existing prefix constant is invisible at JSX-review
  time (it looks like ordinary self-documenting naming) and only surfaces
  as a silent over-count in a DIFFERENT, unrelated test's assertions.
- **Chip structure, live-confirmed** (`getComputedStyle` + DOM read via
  `.evaluate()` scoped on the already-testid'd `chat-attachment-chip-{i}`
  parent — a read, not a new locator; same idiom as the pre-existing
  `chat.delete_confirm_button.evaluate("el => getComputedStyle(el)...")`
  pattern in `test_delete_confirmation_modal_ui_validation.py`): 3 direct
  children in fixed order — `<svg>` (file-type icon, `AttachedFileIcon`) →
  `<span>` (filename, `TypographyWithConditionalTooltip`) → `<div>` (remove
  button, now testid'd). The file-type icon itself gets NO new testid —
  its presence is verified structurally (`children[0].tagName === 'svg'`),
  same precedent as the ELITEA-2091 model-selector `CheckedIcon` check
  ("child icon count scoped under testid'd parent... no new testid
  needed").
- **"Dark background, light text" — the RAW `background-color` computed
  value does NOT by itself read as dark.** Live-confirmed:
  `getComputedStyle(chip).backgroundColor === "rgba(255, 255, 255, 0.1)"`
  (a translucent WHITE overlay) — only dark once COMPOSITED over the app's
  own near-black canvas (`document.body` computed background `rgb(14, 19,
  29)`, confirmed no light/dark toggle affects this ambient session —
  `useEliteATheme.hooks.js` resolves theme from `state.settings.mode`,
  this session's resolved mode renders the dark palette). The shipped test
  computes composited relative luminance (WCAG formula) rather than
  asserting the misleading raw string. Filename text color is
  unambiguously light on its own: `rgb(255, 255, 255)` (pure white),
  confirmed identical across every chip.
- **Chose 4 files, not 5, deliberately** — at the standard `1700×1100`
  viewport (ELITEA-2197 precedent), `FileList.jsx`'s width-driven
  `maxItemsToShow` renders exactly 4 as visible chips before overflowing a
  5th into the "+N" bucket (reconfirmed live, same arithmetic ELITEA-2091
  already documented). Using 4 keeps this case's "all files render as
  chips in a horizontal row" observable unambiguous — the visible/overflow
  split mechanism is ELITEA-2197's own dedicated scope, not re-derived
  here. All 4 chips confirmed on one shared `y` coordinate (bounding-box
  row check), `x` increasing left-to-right.
- **Case-text clarification, not a defect**: case step 2 says "files begin
  uploading" — live-confirmed (again, consistent with the already-filed
  ELITEA-2197 Network Behavior finding) that attaching is 100%
  client-side; zero network request fires at selection time. Chips
  rendering immediately IS the correct, live, self-consistent observable
  asserted instead (reverse-masking guard).
- **HMR gotcha reconfirmed**: editing `FileList.jsx` (even an additive
  `data-testid` line) triggered a full app remount, not just a component
  hot-swap — composer/attachment state reset to empty. Expected and
  harmless (add the testid FIRST, then attach files for the actual test
  drive, not the other way around) — not a product defect.
- AFS: `test-specs/chat-interface/l3_attach-files-multiple-chips-display_ELITEA-2196.md`.

## ELITEA-2199/2467 — attachment chip icon genericity + long-name truncation +
## "+N" overflow click-to-expand, both `extend-existing` against ELITEA-2196's
## covering spec, ZERO new testids, ONE clarification (icon type-genericity, #1591)
- **Icon does NOT vary by file type — confirmed via source AND live run.**
  `FileList.jsx:88` (visible chips) and `:154` (overflow-menu items) both
  render the exact same `AttachedFileIcon` SVG (`@/assets/attached-file-icon.svg`)
  unconditionally — no branching on extension/MIME anywhere in the component.
  Live-confirmed: attached `.png` + `.pdf` + `.txt` + a long `.txt` in one
  conversation — all 4 chips' `<svg>` `outerHTML` byte-identical. Contrast:
  the app DOES have a type-aware icon/preview system elsewhere
  (`EliteaUI/src/slices/fileTypes.js` + the Artifacts feature's
  `FilePreviewCanvas`) — `FileList.jsx` just doesn't reuse it. ELITEA-2199's
  case text claims "type-appropriate icon" — **case-text drift, clarification
  filed as issue #1591**, not a defect (no partial/broken type-icon wiring
  found — reads as "never built this way", not a regression). ELITEA-2467's
  case text only says "a file icon" (no type claim) — clarification does NOT
  apply to that case.
- **Truncation mechanism**: CSS `text-overflow: ellipsis` via the shared
  `TypographyWithConditionalTooltip` component (`[fsd]/shared/ui/tooltip/`).
  Live-confirmed on a 104-char filename at the standard 200px-wide chip
  (~116px name column): `scrollWidth` 731px vs `clientWidth` 116px — genuine
  visual truncation, not just a CSS rule with room to spare. The component
  ALSO shows a hover tooltip with the full name when (and only when) genuinely
  overflowing (`useTextOverflow` hook, same "conditional on real overflow"
  precedent as the chat-starter-tile tooltip) — confirmed live via
  `[role="tooltip"]`, but NOT made a required AFS assertion (no testid on
  this particular tooltip instance yet; the `scrollWidth>clientWidth` check
  alone fully satisfies both cases' literal "truncated with '...'" ask,
  scope kept proportionate — see either AFS's Automation Hints if a future
  case wants the tooltip asserted too, that would need a `testId` prop
  threaded through the SHARED `TypographyWithConditionalTooltip` component,
  set only at `FileList.jsx`'s call site, same pattern as the starter-tile's
  own `slotProps.tooltip` wire).
- **"+N" overflow button IS a real, functioning click-to-expand control** —
  confirmed live: click sets `aria-expanded` `undefined` → `"true"` on
  `chat-attachment-overflow-button` and opens a MUI `role="menu"` populated
  by the existing `chat-attachment-overflow-item-{index}` testid'd items
  (both testids pre-existing, ELITEA-2197, **on-main ✓**). At `1700×1100`
  with 7 attached files: 4 visible chips + `"+3"` button; opening it lists
  exactly `extra_file_5.txt`/`_6.txt`/`_7.txt` in order. Existing tests
  (ELITEA-2196's `get_all_attached_file_names()`, ELITEA-2197's own test)
  already click this button, but only as PLUMBING inside a helper to read
  hidden names for a total-COUNT assertion — neither asserts the
  click→expand INTERACTION itself as an observable. ELITEA-2467's case text
  explicitly asks for exactly that ("the '+N' indicator is clickable to
  expand or scroll") — genuine gap, first test to assert it directly.
- Zero new testids for either case — `chat-attachment-chip-{index}`,
  `chat-attachment-overflow-button`, `chat-attachment-overflow-item-{index}`
  all confirmed **on-main ✓** via fresh `git fetch origin` this session.
- AFS: `test-specs/chat-interface/lextend_attach-files-icon-genericity-and-truncation_ELITEA-2199.md`,
  `test-specs/chat-interface/lextend_attach-files-truncation-and-overflow-click-to-expand_ELITEA-2467.md`.

## ELITEA-2198 — sequential individual-removal (2nd X click), `extend-existing`
## against ELITEA-2196's own covering spec, zero new testids, zero defects
- **Resolved/added during ELITEA-2198 implementation:** the case's own steps
  1-2 ("attach 4, click X on the first chip, verify 3 remain") are the exact
  mechanism the ELITEA-2196 covering test already proves in its own Step 5.
  The only genuinely new observable is steps 3-4: click X on a **second,
  different** chip (index 0 again, post-renumbering) and verify exactly 2
  remain with the correct filenames. Live-confirmed: `remove_attachment_chip()`
  correctly renumbers and decrements on the SECOND click too — no ghost chip,
  no wrong-file removal, no state carried over incorrectly from the first
  removal. `get_visible_attachment_names()` after 2 sequential removals ==
  `file_names[2:]` in original order (list-equality, not a bare count —
  catches an off-by-one-after-renumbering class of bug a count-only check
  would miss).
- **Zero new testids, zero page-object additions** — every handle
  (`CHAT_ATTACHMENT_CHIP_REMOVE`, `remove_attachment_chip()`,
  `wait_for_attachment_chip_count()`, `get_visible_attachment_names()`) was
  already added by the ELITEA-2196 implementation and is reused verbatim.
- Implemented as a new sibling test method inside the SAME
  `TestAttachFilesMultipleChipsDisplay` class (additive-only — the original
  `test_attach_multiple_files_displays_chips_above_composer` is byte-identical;
  verified via `git diff | grep -E '^-[^-]'` → empty).
- AFS: `test-specs/chat-interface/lextend_attach-files-remove-individual-files-sequential_ELITEA-2198.md`.

## ELITEA-2179/2466 — composer send-button/waveform visibility toggle,
## family AFS (2466 is a granular superset of 2179), FIVE new testids added,
## `extend-existing` against the ELITEA-2181 streaming test
- **SendButton.jsx renders exactly ONE of two mutually exclusive DOM
  nodes in the composer's send-button slot, never a visibility toggle on a
  shared node** — `chat-send-button` (real Send, when the input has text)
  OR a waveform/"enter speaking mode" button (when empty, voice features
  on). Source- AND live-confirmed: typing swaps `chat-send-button` 0->1 the
  SAME tick the waveform testid's count swaps 1->0. While the response is
  streaming, UserInput.jsx swaps the ENTIRE slot to a Stop control — neither
  of the two idle-state buttons renders, confirmed live (`send_button.count()
  == 0 AND voice_mode_button.count() == 0` immediately after Send, before
  `wait_for_ai_response` returns).
- **"Waveform reappears" (both cases' final step) resolves once generation
  COMPLETES, not while the LLM is still streaming** — matches this page
  object's own pre-existing `wait_for_generation_complete()` docstring
  ("Speaking mode button appears when generation is complete... During
  generation, a stop button is shown instead"). Treated as a wording
  nuance/clarification in both AFS files, not a defect — the live,
  self-consistent behavior is asserted (reverse-masking guard).
- **`test_streaming_response_progressive_display` (ELITEA-2181, merged
  `origin/automation/base`) already proves the CORE toggle** (absent when
  empty -> visible on typing -> absent on Backspace -> Send clears input) as
  its own Step 1 — but only via `send_button.count()==0/visible`, never a
  positive assertion on WHAT renders in the empty-state slot. That gap (plus
  ELITEA-2466's bottom-bar-inventory/focus-border/sender-name-avatar asks,
  entirely untouched by the covering test) is what this family AFS closes —
  landed as a new test METHOD in the same file/class, tagged with both TMS
  IDs via two `@allure.issue` decorators, original method byte-identical.
- **Five new testids, all `EliteaAI/EliteaUI` `automation/testids` only
  (not yet on `main`, human cherry-pick pending)**:
  - `chat-voice-mode-button` — `SendButton.jsx`'s speaking-mode-entry
    branch (the waveform icon itself). `EliteaAI/EliteaUI@b84f4f8d`.
  - `chat-voice-input-button` — `VoiceButton.jsx`'s mic button (a SEPARATE
    feature from the waveform — this one dictates INTO the text field, the
    waveform button enters a live speaking conversation).
    `EliteaAI/EliteaUI@b84f4f8d`.
  - `chat-composer-focus-border` + `data-focused` state attribute — on
    `UserInput.jsx`'s PRE-EXISTING gradient-border `Box` (zero new DOM
    node). Focus glow is a `box-shadow` + gradient-background effect, NOT a
    literal CSS `border-color` — live-confirmed `boxShadow` flips
    `"none"` <-> `"rgba(21, 255, 247, 0.2) 0px -5px 20px 0px"` (cyan) with
    `data-focused`. `EliteaAI/EliteaUI@bfdc3148`.
  - `chat-message-sender-name` / `chat-message-sender-avatar` — on
    `UserMessage.jsx`'s header row (vertical-layout branch). Avatar wired
    via `UserAvatar`'s PRE-EXISTING `testId` prop (zero new DOM node), name
    on the existing `Typography`. `EliteaAI/EliteaUI@3762995c`.
  - **Self-correction mid-session**: an initial 6th testid
    (`llm-model-settings-button`) was added on `LLMModelSelector.jsx`'s
    `field` variant — then live-verified (via `document.querySelectorAll`
    against the running dev server) that the chat composer actually renders
    the component's DEFAULT (non-`field`) variant, which already carries a
    PRE-EXISTING `data-testid="model-settings-button"` with zero prior
    page-object callers (canon #511 first caller). Reverted the unused
    addition same-session (`EliteaAI/EliteaUI@293d3aee`) rather than
    shipping dead instrumentation — verify a testid RENDERS on the actual
    call site your test drives before assuming a component-source read is
    enough; two nearly-identical variants of the same shared component can
    diverge on which one a given page actually uses.
- **`+` menu button (`plus-menu-button`) and the gear/settings button
  (`model-settings-button`) were both ALREADY on `main`** (pre-existing,
  zero prior `LocatorDescriptor`/page-object callers before this case —
  canon #511 first callers, not new testids).
- **Test-data note**: `/chat` (bare, no id) redirects unpredictably to the
  LAST-VIEWED conversation rather than a genuinely blank one (same
  documented gotcha as the ELITEA-2175/2176 section below) — this AFS's
  shipped test uses the `conversation_id` fixture (fresh, API-seeded), same
  as the covering ELITEA-2181 test, rather than the ambient "new chat"
  screen this session used only for live handle-exploration via Playwright
  MCP (not the shipped test's own path).
- Family AFS (covers both TMS IDs, same `afs_path`):
  `test-specs/chat-interface/lextend_composer-send-button-visibility-toggle_ELITEA-2179.md`.

## ELITEA-2192/2193/2194 — Users-dropdown remove-control family, round 2:
## owner-attempt-toast is UNREACHABLE (clarification, not a defect), owner-
## removes-non-owner GAINS 2 new assertions (tooltip text + warning icon),
## Cancel-preserves-user is a 2nd-generation near-duplicate of ELITEA-2171
- **All three `already-covered`/`extend-existing` against the SAME two covering tests this digest's
  ELITEA-2171/2172 section already established** — `test_owner_has_no_remove_control_in_users_dropdown.py`
  (ELITEA-2172) and `test_team_users_mention_and_remove_participants.py`
  (ELITEA-2168). Zero new page-object methods needed; two new LIVE-CONFIRMED facts about existing,
  already-testid'd surfaces.
- **ELITEA-2192 ("Owner Cannot Be Removed") is `already-covered` against ELITEA-2172's test — but its
  own step 4 ("attempt delete → red error toast 'Cannot delete author of the conversation'") is
  UNREACHABLE via any real UI interaction, filed as a CLARIFICATION (not a defect).** Investigated via
  `getComputedStyle` on the owner row's `#DeleteButton` (not hover-dependent): the delete icon is
  ALWAYS in the DOM (never conditionally rendered) but `visibility: hidden` is its BASE state, and the
  `&:hover` rule only flips it to `visible` when `isSelectable` is `true` for that row — permanently
  `false` for the owner's own row. `visibility: hidden` (unlike `opacity: 0`/`pointer-events: none`
  alone) removes an element from the browser's own hit-testing, so a genuine mouse click at that
  screen position can never land on it — there is no code path by which a real user can "attempt" this
  delete at all. `useDeleteParticipant.js` DOES wire a `toastError(...)` for a failed delete mutation
  (so a server-side "cannot remove the author" guard, if any, would surface as a toast IF the request
  were ever sent) — but since the request can never be triggered through the UI for the owner's own
  row, that guard/toast is unreachable through the case's own described interaction. `grep -rn "Cannot
  delete author" src/` → 0 hits anywhere in the frontend. Filed
  [elitea-testing-public#1564](https://github.com/EliteaAI/elitea-testing-public/issues/1564).
- **ELITEA-2193 ("Owner Can Remove Non-Owner via Confirm Dialog") is `extend-existing` against
  ELITEA-2168's Step 8/9 — 2 gap assertions, both live-confirmed, zero defects.** The covering test's
  `open_remove_user_dialog()` hovers-and-clicks in one motion and only asserts the dialog's BODY text;
  it never separately checks (a) the delete icon's hover TOOLTIP text, or (b) the confirm dialog's
  ICON. Both are genuinely new, additive assertions on the SAME existing call site:
  1. **Tooltip = "Remove user"** — confirmed live via accessibility snapshot: hovering a non-owner row
     produces `button "Remove user"`, matching `DeleteParticipantButton.jsx`'s MUI `Tooltip` `title`
     prop (`` `Remove ${entityType}` ``, `entityType` resolves to `'user'` for Users-section rows).
  2. **Orange warning icon** — confirmed live via `browser_evaluate`: `delete-confirm-title` (existing
     testid, `ChatPage.delete_confirm_title`, previously UNUSED for icon inspection anywhere in the
     suite — this case is its first icon-check caller) contains exactly one `<svg>` with computed
     `fill: rgb(233, 121, 18)` — a genuine orange, matching `Modal.DeleteEntityModal`'s
     `titleIcon={ModalConstants.MODAL_ICON_TYPE.warning}` prop.
- **ELITEA-2194 ("Cancel Keeps User in List") is a SECOND near-duplicate TMS case of ELITEA-2171** —
  same wording, same 3-step flow, different TMS ID, same covering test's Step 10. Live-reconfirmed a
  SECOND time this session (different conversation/participant pair than ELITEA-2171's own repro) —
  same result: Cancel closes the dialog, badge and popover listing both stay unchanged. Reinforces the
  "near-duplicate TMS case ID" pattern this digest already documents recurring across the folder
  surface (ELITEA-2460/2148, ELITEA-2461/2149+2151, ELITEA-2123/2127/2459) — now confirmed on the
  Users-dropdown remove-control surface too.
- **Zero new testids for all three cases** — every handle needed (`chat-participants-badge-button`,
  `chat-participant-row-user_{userId}_`, `chat-participant-remove-button`, `delete-confirm-dialog`,
  `delete-confirm-title`) already exists on both `main` and `automation/testids` (fresh `git fetch
  origin` + `git grep` this session).
- **Test-data reuse**: all three cases' live exploration this session reused ONE pre-existing
  conversation from earlier in the same batch (`/chat/566` "HI Chat", owner "Test Bot" + non-owner
  "Hrach Sargsyan") rather than seeding a fresh one — zero new conversations created, zero participants
  actually removed (the one confirm dialog opened during exploration was Cancelled, not Removed, so the
  conversation's state is unchanged from before this session).
- All three AFS files:
  `test-specs/chat-interface/lcovered_conversation-owner-cannot-be-removed-attempted-delete-toast_ELITEA-2192.md`,
  `test-specs/chat-interface/lextend_owner-removes-non-owner-tooltip-and-warning-icon_ELITEA-2193.md`,
  `test-specs/chat-interface/lcovered_cancel-remove-participant-dialog-keeps-user-in-list_ELITEA-2194.md`.

## ELITEA-2175/2176 — Add users modal: middle-chip removal via X + cancel
## with TWO pre-selected users, both `extend-existing` against ELITEA-2167's
## covering file, ZERO new testids, one infrastructure gotcha found+fixed
- **Neither case was `already-covered` despite two close near-neighbors
  already proving the same mechanism CLASS** — `remove_add_users_chip()`
  (ELITEA-2168) had exactly one prior caller, removing the LAST of 4 chips;
  ELITEA-2175's own case data (3 chips, remove the MIDDLE one) is a distinct,
  live-confirmed observable — proves the removal is keyed by chip identity,
  not array position, and that BOTH surrounding selections survive in order.
  Similarly, Cancel-discards-a-selection was already proven with exactly ONE
  pre-selected chip (ELITEA-2167 Step 7, ELITEA-2168 Step 6);
  ELITEA-2176's own data (Cancel with TWO pre-selected chips, against an
  EXISTING conversation with a real participant baseline) is this digest's
  first multi-item-Cancel proof. Both live-reconfirmed this session, not
  assumed from the LAST-position/single-item precedents.
- **Zero new testids for either case** — `add-users-remove-chip-{userId}`,
  `add-users-chip-{userId}`, `add-users-cancel-button`,
  `add-users-confirm-button`, `chat-participants-badge-button` /
  `chat-participants-popper` are all already on both `main` and
  `automation/testids` (fresh `git fetch origin` + `git grep` this session) —
  confirmed by the two prior sessions (ELITEA-2167/2168) that established
  this whole modal surface.
- **Infrastructure gotcha found+fixed, reproduced 4/4 times**:
  `_open_blank_conversation()` (the covering file's own existing helper,
  single check — new-conversation greeting visible) is insufficient on this
  shared dev backend. `ChatPage.navigate_to_chat()`'s own docstring already
  documents that "the SPA may redirect to the last-viewed conversation
  stored in the browser session" — this redirect can fire as a DELAYED
  effect, AFTER the greeting and a momentary 0 message count are both
  already observed, silently snapping the view back onto a pre-existing
  conversation with real history (this session's own repeated landing spot:
  `/chat/420`, "Review attached documents" — the SAME conversation the
  ELITEA-2171/2172 section above documents as a shared-contention hot spot).
  A parallel manual Playwright MCP session, driven slowly with pauses
  between steps, reliably produced a genuinely blank conversation via the
  identical `sidebar-create-button` click — isolating this as a headless/
  fast-back-to-back-actions TIMING race, not a product defect and not
  missing test data. Fix: an ADDITIVE sibling helper,
  `_open_genuinely_blank_conversation()` (does NOT modify
  `_open_blank_conversation()` or its existing ELITEA-2167 caller — Hard Rule
  3), adds a settle window (1.5s) + re-check of BOTH message count AND URL
  before proceeding. Used by both new test classes.
- **Related finding, flagged NOT fixed (out of scope for this unit — a
  shared-caller helper with an existing merged caller)**: the ORIGINAL,
  already-merged `TestInviteUsersAddCancelClose` test (using the weaker
  `_open_blank_conversation()`) now fails CONSISTENTLY (reproduced 2/2) in
  the current live environment on this exact race — its own Step 1 assertion
  (`assert not chat.is_participants_badge_visible(...)`) fails because it
  lands on the restored conversation with participants. Not a regression
  introduced by this session's own code (that helper/test were never
  touched) — worth a follow-up fix-only dispatch to apply the same
  settle+recheck guard to `_open_blank_conversation()` itself (which would
  then need the shared-file regression protocol: enumerate + re-run every
  caller before landing).
- Both AFS files:
  `test-specs/chat-interface/lextend_remove-preselected-user-via-chip-x_ELITEA-2175.md`,
  `test-specs/chat-interface/lextend_cancel-add-users-modal-after-preselecting-users_ELITEA-2176.md`.

## ELITEA-2171/2172 — Users-dropdown remove-control: Cancel-preserves-user
## (`already-covered` vs merged ELITEA-2168) + owner-row-has-no-delete-control
## (`ready-for-automation`, new observable, zero new testids)
- **ELITEA-2171** ("Cancel Remove User Dialog Keeps User in Participants
  List") is verbatim ELITEA-2168's own Step 10 (source
  `test_team_users_mention_and_remove_participants.py` lines 560–576, merged
  `origin/automation/base`) — hover a non-owner row, click delete, click
  Cancel, verify badge count AND dropdown listing unchanged. Classified
  `already-covered`, traceability AFS only.
- **ELITEA-2172** ("Conversation Owner Cannot Be Removed") is a GENUINELY NEW
  observable — ELITEA-2168's test removes two different non-owner
  participants but never once hovers/asserts anything about the OWNER's own
  row. Classified `ready-for-automation`.
- **Mechanism, source- AND live-confirmed**: the product implements this as
  "you cannot remove **yourself**", not an explicit "conversation owner"
  role/flag. `UserMenu.jsx`'s per-row `isSelectable = selectable &&
  user.entity_meta?.id !== currentUserId` (`currentUserId` = `state.user.id`,
  the CURRENTLY LOGGED-IN session) gates the delete `IconButton`'s
  hover-visibility CSS (`'&:hover #DeleteButton': { visibility: selectable ?
  'visible' : 'hidden' }` — the `selectable` param `userItemStyles` receives
  is actually the per-row `isSelectable`). The delete button is ALWAYS
  present in the DOM (never conditionally rendered) — even for the
  "un-removable" row — it just never becomes visible on hover. **Assert via
  `not_to_be_visible()`, never `to_have_count(0)`** (same class of gotcha as
  the ELITEA-2146/2147/2148 collapsed-folder-items note above — an
  always-mounted, visibility-toggled node needs a visibility assertion, a
  count-based one passes for the wrong reason). In THIS single-account
  testing environment "yourself" and "the conversation's creator/owner"
  coincide (only one real account exists, and it always creates the
  conversations it opens) — asserting against it faithfully verifies the
  case's own intent, this is a mechanism clarification, not a defect or a
  case-text drift.
- **Live-confirmed via Playwright MCP** (conversation `/chat/420`, badge
  went 1→2 after adding Hrach Sargsyan): hovering the owner's row ("TB Test
  Bot") produced NO "Remove user" accessible button in the post-hover
  snapshot; hovering the SAME dropdown's non-owner row (Hrach Sargsyan)
  IMMEDIATELY produced `button "Remove user"` — same session, same popover
  instance, ruling out a stale-render artifact.
- **Zero new testids needed for either case** — `chat-participants-badge-button`,
  `chat-participant-row-{unique_id}` (dynamic, ELITEA-2168), and
  `chat-participant-remove-button` are all already on BOTH `main` and
  `automation/testids` (fresh `git fetch origin` + `git grep` this session).
  Owner id resolution reuses the exact same `ConversationAPI.get_conversation()`
  → `meta.user_name`/`entity_meta.id` mapping ELITEA-2168's test already
  established for non-owner rows — just matched against `${TEST_USER}`'s own
  display name instead of a searched-for name.
- **Gotcha — running pytest concurrently with manual Playwright-MCP
  exploration against the SAME localhost dev server risks cross-session
  conversation contamination.** This session ran the merged ELITEA-2168
  pytest test live (to reconfirm ELITEA-2171 unrelated to the AFS's own
  manual repro) WHILE a manual Playwright-MCP browser was also open on a
  DIFFERENT, shared conversation (`/chat/420`). Both pytest attempts failed
  at their own Setup stage before reaching Step 10 (once on the
  already-tracked #1082 stale-conversation flake, once on an "Add users"
  search timeout) — and one of them appears to have landed on and added
  participants (Daniyar Chambylov, Ihar Bylitski — ELITEA-2168's own SETUP
  users) to `/chat/420` itself rather than a fresh conversation, mid-session.
  Root cause not fully isolated (didn't chase which specific run did it —
  pytest's own browser context is separate from the MCP one, so this is
  server/backend-side conversation-list contention, not a shared browser
  session), but the practical lesson holds regardless of exact mechanism:
  **don't run pytest against localhost while a manual MCP exploration
  session is also active on the same dev server** — either serialize them,
  or expect to need extra cleanup on whichever conversation the manual
  session was using. Recovered by restoring `/chat/420` to its original
  1-participant state before ending the session.
- Both AFS files: `test-specs/chat-interface/lcovered_cancel-remove-user-dialog-keeps-user-in-participants_ELITEA-2171.md`,
  `test-specs/chat-interface/l2_conversation-owner-has-no-remove-control-in-users-dropdown_ELITEA-2172.md`.

## ELITEA-2460 — near-total duplicate of ELITEA-2148, `already-covered`
## (zero new code — the 3-observable covering test already proves all 5 steps)
- ELITEA-2460's 5 granular steps (expand folder-with-conversations → conversations
  listed → collapse → hidden → expand empty folder → "No conversations added")
  decompose 1:1 onto the 3 compound observables
  `test_folder_displays_conversations_or_empty_state` (ELITEA-2148, merged
  `origin/automation/base` commit `d2b5d1aa`, PR #1545, chat-remaining wave-07)
  already asserts. No gap — every case step maps onto an existing assertion,
  and the covering test is stricter (exact empty-state string, visibility-based
  not count-based collapse check).
- Live-reconfirmed this session: re-ran the covering test standalone, PASSED,
  `1 passed in 17.09s`.
- AFS: `test-specs/chat-interface/lcovered_folder-displays-conversations-when-expanded-and-empty-state_ELITEA-2460.md`.
- **Pattern reinforced (same class as ELITEA-2461/2457/2123/2127 below)**: this
  module's near-duplicate case pattern also recurs on the expand/collapse/
  empty-state surface — grep this digest by BEHAVIOUR ("empty state", "expand")
  before assuming a fresh case needs new code.

## ELITEA-2461 — near-total duplicate of ELITEA-2149 + ELITEA-2151 combined,
## `already-covered` (zero new code, two-spec dedup)
- ELITEA-2461's 5 steps decompose cleanly across two already-merged specs on this
  same pin/panel-order surface: steps 1–4 (hover a Today/This Week/Older
  conversation → 3-dot → Pin on top → moves out of its date group into the
  pinned section → pin icon renders) are verbatim `test_pin_conversation_via_pin_on_top`
  (ELITEA-2149); step 5 (full 4-tier panel order: pinned folders → pinned
  conversations → unpinned folders → unpinned conversations by date group) is
  verbatim `test_pinned_folder_and_conversation_render_above_unpinned_panel_order`
  (ELITEA-2151) — the SAME covering test ELITEA-2159's dedup already used for its
  own near-identical step-5 wording. This is the first case in this digest that
  needed BOTH covering tests to close its own case, rather than just one.
- Live-reconfirmed this session: re-ran both covering tests together
  (`tests/ui/chat/test_pin_conversation.py::TestPinConversationViaPinOnTop::test_pin_conversation_via_pin_on_top`
  + `::TestChatPanelOrderingPinnedFoldersAndConversations::test_pinned_folder_and_conversation_render_above_unpinned_panel_order`),
  both PASSED, `2 passed in 45.98s`.
- AFS: `test-specs/chat-interface/lcovered_pin-conversation-appears-above-folders-and-date-groups_ELITEA-2461.md`.
- **Pattern reinforced (same as the ELITEA-2457/2123/2127 sections below)**: this
  module's near-duplicate case pattern isn't confined to folder-creation/rename —
  it recurs on the pin/panel-order surface too. Always grep this digest by
  BEHAVIOUR ("pin", "panel order") before assuming a fresh case needs new code.

## ELITEA-2146/2147/2148 — folder-list & submenu SCROLLABILITY, expand/collapse +
## empty-state, ALL 3 ready-for-automation, TWO new testid gaps found, ZERO defects
- **Sidebar list scroll container genuinely overflows once enough folders exist —
  confirmed live, but at a viewport-dependent scale.** `Conversations.jsx`'s
  `ref={listRef}` `Box` (line ~731, `overflowY: 'scroll'`, `height: 'calc(100% -
  40px)'`) wraps pinned folders + pinned conversations + unpinned folders +
  date-grouped conversations ALL in one shared container — there is no
  folder-only scroll region, the whole sidebar list scrolls together. At the
  CARRIED-OVER 1280×4000 viewport (leftover from the prior ELITEA-2142/2143/
  2144/2145 session sharing this MCP browser instance) `scrollHeight ===
  clientHeight === 3928` — NOT scrollable, a false negative trap for any future
  session that inherits an oversized viewport. Resized to 1440×900:
  `scrollHeight=2946` vs `clientHeight=828` (with the account's ambient 67
  folders present) — genuinely overflowing. Collapsed folder row height
  measured at 41px (folder `279`). **testid needed**: this container has NO
  testid today — add one (e.g. `chat-conversation-list-scroll-container`) via
  `add-data-testid`, same family as the existing `chat-messages-scroll-container`
  precedent. Full spec: ELITEA-2146's AFS.
- **"Move to" submenu's folder-list popover ALSO genuinely overflows, and is a
  SEPARATE container from the sidebar** (MUI's own default `Menu`/Popover Paper
  sizing — `overflow-y: auto`, `max-height: calc(100% - 96px)` — not bespoke
  EliteaUI logic). With the submenu open and 67 ambient folders rendered:
  popover Paper `scrollHeight=2781` vs `clientHeight=802`. Confirmed
  FUNCTIONALLY wired, not just visually present: scrolled to the popover's max
  `scrollTop`, clicked the then-revealed last folder item
  (`chat-move-to-folder-88-menuitem` this run), and observed a real `PUT
  .../elitea_core/conversation/prompt_lib/399/8152 → 200` — the scrolled-to
  item genuinely moves the conversation. **testid needed**: the submenu's
  `<Menu>` Paper (`DotMenu.jsx` line ~93, the nested `subMenuItems?.length &&`
  branch) carries NO testid and NO `id` at all today (confirmed via DOM
  inspection) — add via `slotProps={{ paper: { 'data-testid':
  'chat-move-to-submenu-popover' } }}` (or equivalent MUI prop shape). Full
  spec: ELITEA-2147's AFS.
- **Expand/collapse + empty-state mechanism (ELITEA-2148) works exactly as
  cased, but the case TITLE overclaims** — "Displays Conversation Count" implies
  a numeric badge that does not exist anywhere (source-confirmed:
  `FolderAccordionItem.jsx`/`FolderAccordion.jsx` never render `folder.total`/
  `conversations.length` as visible text, only as internal pagination state).
  The case's own numbered STEPS never ask for a count badge either — only
  "expand and see the list" / "see the empty state" — and those match live
  behavior exactly, so this is a title/scope mismatch, not case-text drift
  worth a clarification filing. Live-confirmed: collapsed folder row's
  conversation items stay MOUNTED in the DOM under MUI `Collapse`
  (`.MuiCollapse-hidden` sets `visibility: hidden`, not `display:none`/unmount)
  — a future test must assert via `not_to_be_visible()`, NOT `to_have_count(0)`
  (the element IS still present, so a count-based assertion would pass for the
  wrong reason — see `.agents/memory/qa-engineer/passing_assertion_may_prove_nothing.md`).
  `chat-folder-empty-state` text reconfirmed: **"No conversations added"**
  (folder `279`, this session).
- **Page-object gap (method, not testid)**: no `collapse_folder()` exists.
  `expand_folder()` isn't safe to call a second time to collapse (it waits for
  `data-expanded="true"`, already true going in). Small addition needed,
  mirrors `expand_folder()` waiting for `[data-expanded="false"]` instead.
- **Reconfirms the ELITEA-2121/2130 pinned-folder disabled-ancestor gotcha**
  (unrelated to any of these 3 cases' own seeded data, hit only because folder
  `213` — a PINNED leftover exploration folder from that earlier session — was
  tried first and both a plain Playwright click AND a raw `element.click()`
  via `browser_evaluate` silently no-opped against it, "element is not
  enabled" despite `.disabled === false`). Not a new defect — same
  `isDragDisabled={isPinned}` ancestor already documented; switched to an
  unpinned folder and the normal click worked immediately.
- **Zero product defects found this pass** — all 3 cases' own subjects
  (scrollability ×2, expand/collapse/empty-state ×1) work correctly and
  genuinely on the real system, end to end, including a real network mutation
  chosen specifically from a scrolled-to-only-reachable submenu item.

## ELITEA-2142/2143/2144/2145 — drag-and-drop conversation<->folder, NEW
## surface (`chat-conversation-drag-drop`), mechanism confirmed real,
## TWO new defects filed (#1541 drop-target misresolution, #1542 missing
## single-item toast), one direction not pristine-confirmed (scroll)
- **Mechanism**: `@dnd-kit/core`'s `PointerSensor` (8px activation distance),
  NOT native HTML5 `draggable`/`DragEvent`. `DraggableConversationItem.jsx`
  (`useDraggable`, id = conversation numeric id) / `DraggableFolderItem.jsx`
  (`useSortable`, id = `folder-{id}`, used for folder REORDERING, a separate
  concern from conversation drops) / `DroppableFolderItem.jsx` +
  `DroppableGroupedArea.jsx` (`useDroppable`, ids `folder-{id}` /
  `'ungrouped-conversations'`). All logic in
  `src/hooks/chat/useDragAndDrop.js`.
- **Real Playwright mouse gestures DO drive the real product code — no
  substitution needed for this whole family.** Confirmed via network capture:
  a genuine multi-step `mouse.down()` → several `mouse.move(..., {steps:N})`
  → `mouse.up()` sequence (or Playwright's own `locator.dragTo()`) fires a
  real `PUT /elitea_core/conversation/prompt_lib/{project}/{id}`. A single
  big-jump `dragTo()` with NO intermediate steps risks under-shooting the
  8px `PointerSensor` activation distance or missing collision recompute —
  use several `steps` per `mouse.move()` call and re-measure the target's
  `boundingBox()` on every iteration (layout shifts — e.g. a source folder's
  accordion collapsing mid-drag — move sibling elements a few px during the
  gesture; a STALE captured target rect can miss).
- **Hover-highlight over a candidate drop folder IS implemented and
  CONFIRMED WORKING live** (screenshot evidence,
  `.playwright-mcp/w07-mid-drag-hover-folderB.png`): `DroppableFolderItem`'s
  `shouldShowDropFeedback` (`isOver && isActive && isValidDropTarget`) renders
  a `2px dashed` primary-color overlay `Box` around the hovered folder. Same
  mechanism/component (`DroppableGroupedArea`) exists for the ungrouped/
  date-group drop area. **Neither overlay carries a testid today** —
  `testid needed`: add a stable `data-testid` (e.g.
  `chat-folder-drop-zone-{folder_id}` / `chat-conversation-list-drop-zone`)
  PLUS a `data-drop-active` boolean attribute on the EXISTING outer
  `ref={setNodeRef}` Box (the wrapper `DroppableFolderItem`/
  `DroppableGroupedArea` already render, one level above the pre-existing
  `chat-folder-item-{id}` testid) reflecting `shouldShowDropFeedback` —
  state-via-`data-*`-attribute per this project's testid policy, NOT a
  state-switched testid, and NOT the conditionally-mounted anonymous overlay
  `Box` itself (that element mounts/unmounts with drag state, which is the
  wrong node to carry an identity testid).
- **CONFIRMED DEFECT, filed
  [elitea-testing-public#1541](https://github.com/EliteaAI/elitea-testing-public/issues/1541)**:
  dragging a conversation OUT OF one folder and dropping it ONTO another
  folder does NOT move it there — it lands in the ungrouped/general list
  (`folder_id: null`) instead, even though the target folder was correctly
  highlighted (dashed border, confirmed via screenshot) right up to release.
  Reproduced 3× this session, cleanest repro was a fresh page load + single
  continuous gesture with the target's `boundingBox()` re-measured
  immediately before `mouse.up()` (pristine-repro gate satisfied). Root
  cause suspected in `handleDragEnd`'s `over.id` resolution vs. the
  `getDropAreaState`-driven highlight diverging — not yet fix-verified, see
  the issue for the exact source-line reasoning.
- **CONFIRMED DEFECT (source-level, not live-UI-dependent), filed
  [elitea-testing-public#1542](https://github.com/EliteaAI/elitea-testing-public/issues/1542)**:
  `handleDragEnd`'s `toastSuccess(...)` call is gated behind
  `currentDraggedItems.length > 1` — a SINGLE-conversation drag-and-drop
  move NEVER shows a success toast, regardless of whether the move itself
  succeeds. Contradicts both the TMS cases (ELITEA-2142/2144 each ask to
  "verify a success toast confirms the move" for a single conversation) AND
  the product's own precedent — the "Move to" CONTEXT-MENU flow (a
  different code path, `test_move_conversation_to_folder.py`) DOES show a
  toast for a single-item move (`Chat moved to "X" folder successfully`).
- **NOT pristine-confirmed this session, due to environment obstacles, not
  a defect claim**: the Today/date-group → folder direction specifically
  (ELITEA-2142's own core assertion). This shared DEV account currently
  carries **65+ orphaned folders** (known, already-tracked cleanup gap —
  see the `#1309`/`#1310`/`#1533` testid-regression section below, which is
  the root cause of the leaked `delete_folder_via_menu()` cleanup failures),
  pushing the "Today" conversation list thousands of px below the folder
  list and out of simultaneous viewport reach even at a 4000px-tall resize;
  `@dnd-kit`'s autoscroll did not visibly engage for synthetic MCP pointer
  input in the time available. Given `handleDragEnd`'s folder-branch code
  is IDENTICAL for both directions (`droppedOnId.startsWith('folder-')` →
  `onMoveToFolderConversation(conversation, targetFolder)`, regardless of
  whether the drag started from `ungrouped` or another folder), there is a
  real, non-trivial risk ELITEA-2142 hits the SAME #1541 defect — but this
  was not independently proven for this exact direction. **Flagged as an
  explicit build-time check** in ELITEA-2142's own AFS, not asserted as a
  separate defect.
- **Test-data hygiene note (not new — corroborates the already-documented
  `#1309`/`#1310` sections below)**: `ConversationAPI` already has
  `create_folder(name)` / `delete_folder(id)` /
  `move_conversation_to_folder(conversation_id, folder_id)` (contrary to the
  "no FolderAPI client exists yet" note in the ELITEA-2135 AFS/section
  below — this has since been added; use it directly, don't re-add).
  This session's own exploration folders/conversations (ids 301/302,
  8404/8405) were deleted via these API methods before finishing — zero net
  pollution added by this session.

**Resolved/added during ELITEA-2142/2143/2145 implementation (implementer,
2026-08-15):**
- **`#1542` corrected — NOT a defect.** The analyst's source read covered
  only `useDragAndDrop.js`'s own `toastSuccess(...)` call (gated to
  `currentDraggedItems.length > 1`, a SEPARATE multi-select aggregate
  toast). It missed that `handleDragEnd` also calls `await
  onMoveToFolderConversation(...)` per item, and THAT hook
  (`useMoveToFolderConversation.hooks.js`, shared with the "Move to" menu
  flow) fires its own toast unconditionally on success. Live-confirmed a
  single-item drag DOES show `Chat moved to "<folder>" folder successfully`.
  Corrected via a comment on #1542 (left open, human disposition).
- **Toast auto-dismisses before a multi-step verification chain finishes.**
  Capture toast text IMMEDIATELY after the triggering action (same
  `page.expect_response` block as the drop), not several steps later — a
  step-6-style "verify toast" read that runs after 2+ intervening
  assertions (folder-removal check, folder-expand) can find the toast
  already gone. Same idiom `test_move_conversation_to_folder.py` already
  uses; drag-and-drop tests need it explicitly because the case text lists
  the toast check LAST.
- **Drag gestures need TWO distinct guards before every `mouse.move()`/
  `mouse.down()`, not just `scroll_into_view_if_needed()`:**
  1. *Off-screen:* `bounding_box()` is viewport-relative; an item below the
     fold (this shared DEV account's sidebar routinely carries 65+ folders
     ahead of the conversation list) reports a y far past the viewport
     height, and `page.mouse.move()` to that coordinate never reaches the
     element (drag silently never activates, no error).
  2. *Stale-position overlap (distinct from #1, more subtle):* even AFTER
     scrolling, `bounding_box()` can report the CORRECT rect for an
     element (matches `getBoundingClientRect()`) while a DIFFERENT,
     stale-positioned row visually overlaps that exact pixel — reproduced
     dragging a conversation OUT of a just-expanded folder: the physical
     coordinate resolved (via `document.elementFromPoint`) to an UNRELATED
     folder's collapsed header, not the conversation. A raw `page.mouse`
     sequence has no actionability check (unlike `.click()`) and silently
     presses on the wrong element. Fix: poll
     `document.elementFromPoint(cx, cy) === el || el.contains(hit)` until
     it settles before pressing/moving — `ChatPage._wait_for_pointer_target()`.
     Both guards are now baked into `start_conversation_drag()` /
     `move_drag_over_target()` — any FUTURE drag-and-drop page-object
     method should reuse those two, not raw `bounding_box()` + `mouse.move()`.
- **A conversation's OWN drag-opacity lives on its PARENT node, not the
  testid'd element itself** — `DraggableConversationItem.jsx`'s Box (style
  `opacity: isDragging ? 0.5 : 1`) wraps the `chat-conversation-item-{id}`
  testid'd Box as its immediate child. Read via
  `el => getComputedStyle(el.parentElement).opacity`, not the element's own
  computed style. Same wrapper-vs-testid-node split applies to
  `DraggableFolderItem.jsx` (used for folder reordering, not exercised by
  this cluster's own cases).

## ELITEA-2136/2138/2139/2140/2141 — "Move to" submenu family, extends
## ELITEA-2135/2137/2138's own surface: back-to-list, folder-to-folder,
## disabled self-entry, `updated_at` mechanism (all extend-existing, tag/gap-only)
- **All 5 cases extend `test_move_conversation_to_folder.py`** (ELITEA-2135/2137,
  merged `origin/automation/base` commit `37dbd948`) — purely additive: 2 tag-only/
  small-insertion extensions (ELITEA-2136 onto ELITEA-2135's own test; ELITEA-2140
  onto this session's own new ELITEA-2139 test) + 3 brand-new test methods
  (ELITEA-2138, ELITEA-2139, ELITEA-2141), zero existing method bodies modified.
- **`select_move_to_back_to_list()` did not exist before this session** — the
  `move_to_back_to_list_menuitem` LOCATOR was added by ELITEA-2135's own
  implementation but had ZERO callers (canon #511) until ELITEA-2139/2140's test.
  New method mirrors `select_move_to_folder()`/`select_move_to_create_folder()`'s
  shape exactly.
- **"Back to the list" toast is a DISTINCT template** from the move-INTO-a-folder
  toast (`Chat moved to "X" folder successfully`, `useMoveToFolderConversation.hooks.js`):
  live-confirmed exact text `Chat moved to ungrouped area successfully` — no quoted
  folder name (there isn't one), different verb phrase entirely. Don't assume the
  same template with an empty/null substitution.
- **Empirically confirmed the mechanism behind ELITEA-2140's "appears in Today"
  claim, not just inferred from source**: the "Back to the list" `PUT
  .../conversation/prompt_lib/{project}/{id}` unconditionally bumps `updated_at`
  to the request's own timestamp, regardless of the conversation's prior recency
  — verified on a conversation that had NEVER been touched between creation and
  the move (its `updated_at` jumped from creation-time to move-time, ~1 minute
  later, in the same response body). Date-group bucketing
  (`DATE_GROUP_ORDER = ['today','this_week','older']`, EliteaUI
  `conversationList.constants.js`) is server-side and keyed purely off
  `updated_at` — folder membership (`folder_id`) and date-group bucket are
  orthogonal fields with no memory of "which group before the folder move".
  **Practical consequence**: there is no way to make a "moved back to list"
  conversation land anywhere OTHER than Today via this flow — the mechanism is
  origin-independent by construction, confirmed live not assumed.
- **The API silently ignores caller-supplied `created_at`/`updated_at`** — live-
  verified: `PUT` a conversation with `{"updated_at": "2020-01-01...",
  "created_at": "2020-01-01..."}` returns `200` but the persisted timestamps are
  UNCHANGED. **There is no test-accessible way to seed a genuinely-"Older"
  conversation on demand** (no natural one existed live in the shared DEV
  project either, at time of writing — only a populated "This Week" group, zero
  Today, zero Older). Any case whose precondition specifically requires an
  Older-origin fixture (ELITEA-2140 here) needs this same treatment: reason from
  the live-confirmed mechanism instead of fabricating the precondition via
  DB/`page.evaluate()` injection (which would be a fidelity-policy substitution).
- **"Move to" submenu, when opened for a conversation ALREADY inside a folder,
  lists that folder's OWN entry — DISABLED, not absent.** Live-confirmed via
  `browser_snapshot` + `aria-disabled` read: `chat-move-to-folder-{own_id}-menuitem`
  renders with `aria-disabled="true"` (self-move prevention) rather than being
  filtered out of the list. A DIFFERENT folder's entry in the same submenu is a
  normal enabled `menuitem`. Not previously documented — no prior case (2135/
  2137) opened "Move to" on an already-in-a-folder conversation. Read via
  `get_move_to_folder_item(folder_id).get_attribute("aria-disabled")` — no new
  testid needed, same `MOVE_TO_FOLDER_ITEM` template ELITEA-2135 provisioned.
- **Context-menu item SET differs for a folder-contained conversation** vs. the
  flat-list 5-item set ELITEA-2114/2135 already document (`Rename, Move to,
  Playback, Pin on top, Delete`): live-confirmed 6 items for an in-folder
  conversation — `Rename, Move to, Playback, Duplicate, Pin on top (DISABLED),
  Delete` — "Duplicate" present, "Pin on top" present-but-disabled rather than
  absent (matches the already-documented `disabled: !isPinned &&
  !!conversation.folder_id` rule under § Pin conversation, reconfirmed here from
  the OTHER side — pin disabled specifically BECAUSE folder_id is set). None of
  ELITEA-2136/2138/2139/2140/2141's own case steps require asserting this full
  set, so no test in this pass encodes it — flagged here in case a future case
  does (don't assume the flat-list 5-item set applies unconditionally).
- **`.clear()` (Playwright's own method) correctly replaces the folder-name
  editor's default value; a raw `Control+a`+`Backspace` sequence reproduces the
  documented "append not replace" race AGAIN** (live-reconfirmed during
  ELITEA-2138 exploration — typing "Sprint Chats" after `Control+a`+`Backspace`
  produced `"Sprint ChatsNew folder"`, a REAL folder created with that wrong
  name, id 293, cleaned up). `ChatPage.set_folder_name()`'s existing
  implementation already uses `.clear()`, not a bare `Control+a` — reuse it
  verbatim, do not hand-roll the input-clearing sequence for any new
  folder/conversation-name editing code (same standing warning as the
  ELITEA-2128/2129 section below).
- **Folder-to-folder move fires the identical `PUT`+toast mechanism as
  move-from-flat-list** (`folder_id` changes in the response body, toast is the
  same `Chat moved to "X" folder successfully` template) — confirmed the prior
  container (date group vs. another folder) makes no difference to the
  move-INTO-a-folder mechanism; only "Back to the list" (moving OUT, to no
  container) has the distinct toast/mechanism documented above.
- **Setup for "conversation already inside a folder" is fastest via
  `conversation_api.create_folder()` + `conversation_api.move_conversation_to_folder()`**
  (both pre-existing on `ConversationAPI`, `api/client.py`) rather than the
  UI-driven folder creation ELITEA-2135's own test uses — real API setup, not a
  substitution (reaches a precondition state, doesn't fabricate the case's own
  observable). Used for ELITEA-2139/2140/2141's setup this session; ELITEA-2136
  reuses ELITEA-2135's existing UI-driven setup unmodified (extension, not a
  fresh test).
- **Cleanup**: all exploration conversations (4) and folders (4, ids 291-294)
  created this session were deleted via `conversation_api.delete_conversation`/
  `delete_folder` immediately after each probe — zero net pollution left by this
  session's exploration (unlike several prior sessions documented elsewhere in
  this digest).

## ELITEA-2128/2129 — folder-rename LENGTH boundary, confirms `FolderItem.jsx`
## shares `MAX_CONVERSATION_LENGTH=50` truncation with `ConversationItem.jsx`,
## `ready-for-automation` (new spec, zero existing coverage of this axis)
- **Zero existing coverage of folder-rename LENGTH/truncation anywhere on the
  trunk** — `test_chat_folder_rename_checkmark_validation.py` (ELITEA-2458 family)
  only exercises the empty/2-char/unchanged/3-char-changed/special-char/
  leading-space VALIDITY axis (regex + changed-state), never a name anywhere near
  the 50-char length boundary. ELITEA-2128 (exact-50 acceptance) and ELITEA-2129
  (51+ type / 70-char paste overflow) close that gap — mirrors the conversation-
  rename precedent (`test_conversation_rename_length_boundaries.py`,
  ELITEA-2101/2102/2103/2104) applied to the folder entity.
- **Source-confirmed AND live-confirmed this session** (both, not source-only):
  `FolderItem.jsx`'s `onChangeFolderName` (line ~180) does `event.target.value
  .slice(0, MAX_CONVERSATION_LENGTH)` on every `onChange` — the EXACT SAME
  constant/mechanism `ConversationItem.jsx`'s `onChangeConversationName` uses
  (`constants.js:74`, `MAX_CONVERSATION_LENGTH = 50`). This was NOT assumed from
  the conversation sibling — grep-confirmed independently in `FolderItem.jsx`'s
  own source, then live-verified on BOTH the create-folder editor AND the actual
  rename-existing-folder path (dot-menu → Rename): typing exactly 50 chars lands
  all 50 (no truncation); typing a 51st char is silently dropped (value stays at
  the first 50); pasting a 70-char clipboard string (real
  `navigator.clipboard.writeText()` + `Control+V`/`Meta+V`, not DOM injection)
  truncates to the first 50 identically — no separate `onPaste` handler exists on
  the input (grep-confirmed), same "reached via the same onChange path" finding
  ELITEA-2103/2104 already documented for conversations.
- **Case-text drift found in ELITEA-2129's own step 2** (its Steps table, NOT a
  cross-case drift like the "Edit"-vs-"Rename" one below): the Expected Result
  column says "Only first **64** characters accepted; 65th is not entered" —
  contradicts the case's own title ("...Beyond **50** Characters"), Test Data (a
  70-char *paste* string), and steps 3-4 (both correctly say 50). Live execution
  confirms 50 is correct and internally consistent; "64" is very likely a mix-up
  with `ConversationNameRegExp`'s SEPARATE 3-64-char CHARSET ceiling (a different
  gate — regex validity, not the length-slice truncation this step actually
  tests). AFS asserts the live, self-consistent 50-char behavior per the
  reverse-masking guard; recommend a case-text CLARIFICATION on the TMS case's
  step 2 wording, not a product bug (see ELITEA-2129's AFS § Known Defects Found
  for the full reasoning).
- **No folder equivalent of `paste_conversation_name()`/`clear_conversation_name()`
  existed before this session** — `ChatPage` only had these for the conversation
  entity. ELITEA-2129's implementation adds `paste_folder_name()`/
  `clear_folder_name()`, mirroring the conversation methods' exact idiom (real
  clipboard write + platform-aware `Control+V`/`Meta+V` keypress; isolated
  `.clear()` helper) rather than inlining either into the test body.
- **`set_folder_name()`'s documented "append not replace" race reconfirmed live
  AGAIN this session** (3rd/4th independent confirmation after ELITEA-2458's
  original finding and the pollution it already left in the shared DEV project) —
  a bare `Control+a` + typed text raced React's re-render and produced
  `"<new-text>New folder"` (append, not replace) on the FIRST attempt of this
  session, before switching to a proper select+delete clear. `set_folder_name()`'s
  own existing `.clear()` call (not a bare `Control+a`) already avoids this — the
  race only reproduces when that safeguard is bypassed, exactly as documented.
- **Cleanup**: exploration folder (id 250, `at_w06_folder_orig` → renamed through
  the type/paste-overflow sequence → deleted) via the UI's own Delete flow —
  zero net pollution left by this session's exploration. A raw `fetch()` DELETE
  to `dev.elitea.ai` from the `localhost:5173` origin was attempted first and
  CORS-blocked (4 console ERROR entries, all this analyst's own probe, not
  product errors, not reachable from the shipped test which uses
  `ChatPage.delete_folder_via_api()` — that method already has the correct base
  URL + auth-header fallback baked in, unlike an ad-hoc `fetch()`).

## ELITEA-2123/2127 — near-total duplicates of ELITEA-2459's already-merged
## special-chars/leading-space scenarios, `already-covered` (zero new code)
- **ELITEA-2123** ("...Validation Tooltip Displayed for Invalid Input") and
  **ELITEA-2127** ("...First Character Cannot Be a Space") ask for exactly
  the two scenarios `test_folder_rename_checkmark_special_chars_and_leading_space_invalid`
  (ELITEA-2459, merged `origin/automation/base` commit `5cc8647c`, PR #1313)
  already implements end-to-end — ELITEA-2123's literal test data
  (`"Folder$$%%"`) is BYTE-IDENTICAL to that test's Step 2 data, and
  ELITEA-2127's "space as first character" ask is exactly that test's
  Step 3 (`" ValidRest"` — deliberately isolating the first-char-space rule
  from the length-floor rule, a stronger proof than a bare single-space
  input). Classified `already-covered` (traceability AFS only, zero code
  change) rather than `extend-existing` — the merged-target rule permits
  either against a base-merged spec, and there is no gap left to fill: every
  case step already has a corresponding assertion in the covering test.
- **Live-reconfirmed this session, not assumed from the digest alone** (the
  "coverage judgments stand on your own execution" rule applies to dedup
  verdicts too, not just extend/ready ones): seeded a fresh folder via the
  UI dot-menu → Rename flow, drove both invalid-name scenarios
  (`"Folder$$%%"` and `" ValidRest2127"`) via `browser_fill_form` (a
  same-session live re-hit of the documented "append not replace" `Control+a`
  race — confirmed it again with a bare `Control+a`+`Backspace` sequence,
  then worked around it via `fill()`, which replaces correctly), and
  observed: the exact quoted `FolderNameWarningMessage` tooltip text (both
  cases), the confirm control's accessible name becoming the tooltip text in
  the invalid state (matching the already-documented a11y gotcha), and — via
  `browser_network_requests` — **zero** `PUT .../folder/prompt_lib/...`
  firing on either inactive-checkmark click. Cleaned up via the UI's own
  Delete flow (dot-menu → Delete → confirm) — zero net pollution.
- **Case-text drift, same as ELITEA-2121/2130/2456**: both cases' step 1 says
  "click three-dot icon, click Edit" — the real dot-menu item is labelled
  "Rename", not "Edit". Not a defect, already documented elsewhere in this
  digest; noted again here since both AFS files reference it independently.
- **TMS linkage**: both cases point their `already-covered` disposition at
  ELITEA-2459; ELITEA-2459's own case should gain "also satisfies
  ELITEA-2123, ELITEA-2127" back-references.

## ELITEA-2122 — folder-rename CANCEL/X-icon path, source-confirmed
## (no live re-drive needed — mechanism identical to two already-live-verified
## sibling cancel flows), `folder_name_cancel_button` gets its first caller
- **Zero existing coverage of folder-rename cancel anywhere on the trunk**,
  confirmed by reading `test_chat_folder_rename_checkmark_validation.py`
  end-to-end (grep for "cancel" inside that file returns 0 hits — its three
  existing test methods, ELITEA-2458/2459/2121, and the file's own
  ELITEA-2130 pinned-folder test only ever exercise the checkmark/confirm
  path). The sibling cancel flows that DO exist —
  `test_chat_folder_creation_custom_name_and_cancel.py` (ELITEA-2119/2120/
  2133/2134) and the conversation-rename cancel path (ELITEA-2100) — cover
  folder-CREATION-cancel and conversation-rename-cancel respectively, never
  folder-RENAME-cancel. ELITEA-2122 closes that one remaining gap.
- **Source-only AFS, deliberately not re-driven live** — `FolderItem.jsx`'s
  cancel `Box`'s `onClick` for an EXISTING folder (`isNewFolder === false`)
  is `handleOnCloseEditFolder`: `setFolderName(name)` (resets local editor
  state to the folder's persisted name) + `setIsFolderEditing(false)` (exits
  edit mode). Zero network calls anywhere in the handler or its dependency
  closure. Same shape, same file, as `handleOnCancelCreateFolder`
  (ELITEA-2120's already-live-verified target) and structurally identical to
  `ConversationItem.jsx`'s cancel handler (ELITEA-2100) — both already
  independently live-confirmed elsewhere in this digest as "cancel fires zero
  new requests". A third live re-drive of the mechanically same pattern
  would reconfirm, not discover.
- **`chat-folder-name-cancel-button` is on BOTH `main` and
  `automation/testids`** (fresh `git fetch origin` + `git grep` against both
  refs this session) — no new testid work needed.
- **`ChatPage.folder_name_cancel_button` (`chat_page.py:1197`) existed with
  ZERO callers before this case** — added defensively in an earlier session
  alongside the confirm button, never referenced by any test until now. This
  case is its first live caller; compliant per canon ruling #511 (a
  page-object field isn't "referenced" until something on an executed test
  path actually calls it).
- Routed `extend-existing` against `test_chat_folder_rename_checkmark_validation.py`
  (its own file, alongside the checkmark-validation/special-chars/context-menu/
  pinned-folder tests) — new test method + a second `@allure.issue` tag,
  existing three methods untouched.

## ELITEA-2121/2130 — Rename-menuitem REGRESSION found+fixed, folder Pin testid +
## data-pinned state ADDED, disabled-ancestor force-click gotcha for pinned folders
- **Blocking regression, confirmed via a LIVE test failure, not just source
  inspection.** `FolderItem.jsx`'s dot-menu "Rename" item's
  `key: 'chat-folder-menu-rename'` (added by ELITEA-2458, commit `0298860f`) was
  silently dropped by a later, unrelated main-branch feature commit (`f5e0c325`,
  "Restore user message to input field when Stop is clicked (#764)", 2026-08-13),
  which replaced the `menuItems` array wholesale to add a new "New chat" item.
  Re-ran `test_chat_folder_rename_checkmark_validation.py` (ELITEA-2458's own,
  previously-merged, previously-green test) live BEFORE touching anything this
  session — it FAILED (`TimeoutError` waiting for
  `chat-folder-menu-rename-menuitem`), proving the regression rather than assuming
  it from a diff read. Filed
  [elitea-testing-public#1533](https://github.com/EliteaAI/elitea-testing-public/issues/1533)
  (sibling to `#1309` — same failure shape, a shared `menuItems` array literal
  edited by unrelated feature work dropping a sibling item's `key`). **Fixed**
  this session (re-added the `key`) and **live-reverified**: the same test now
  passes cleanly (41s). Both ELITEA-2121 and ELITEA-2130 depend on this fix for
  their very first interactive step (open rename editor via dot-menu → Rename) —
  neither case could have been attempted at all without it.
- **New testid + new state attribute added, both in the SAME commit as the
  regression fix** — `EliteaAI/EliteaUI@be489cee` on `automation/testids` (NOT
  yet on `main`, standard human-cherry-pick pending):
  - `key: 'chat-folder-menu-pin'` on the Pin/Unpin menu item → testid
    `chat-folder-menu-pin-menuitem` (first testid ever on this item, not a
    regression). Label text toggles `"Pin on top"` ↔ `"Unpin"` per
    `folder.meta?.is_pinned` — read via `.text_content()` for a genuine
    state-correctness check, not just presence.
  - `data-pinned={isPinned}` added to `FolderAccordion.jsx`'s already-testid'd
    `StyledAccordion` (`chat-folder-item-{id}`), alongside the pre-existing
    `data-expanded`. Mirrors `ConversationItem.jsx`'s existing `data-pinned`
    convention (already consumed by `is_conversation_pinned()`) — zero new DOM
    node, testid identity unchanged, pure sibling-attribute addition. This is
    the correct locator for "is this folder pinned" — the raw `<PinIcon>` the
    collapsed header conditionally renders has NO testid and isn't sanctioned as
    a target per the project's state-via-`data-*` policy; the attribute is
    driven by the exact same `isPinned` boolean, so it's not a weaker proxy.
  - Both edits verified via the `add-data-testid` Step 5.5 discipline: `git diff`
    is testid/key lines only, `npx prettier --check` clean, `npx eslint` clean,
    all three PR #753 greps (new hooks / new DOM nodes / real deletions) empty.
- **Live gotcha, already handled by existing code, no page-object change
  needed**: a PINNED folder's `DraggableFolderItem` wrapper renders
  `isDragDisabled={isPinned}` as a genuinely HTML-`disabled` ancestor around the
  folder's title button. A PLAIN `Locator.click()` on the scoped dot-menu button
  times out ("element is not enabled") for a pinned folder specifically — even
  though the button's OWN `.disabled` DOM property is `false` and
  `pointer-events: auto` (Playwright's actionability check walks up to the
  disabled ancestor regardless). Confirmed live via Playwright MCP (which has no
  `force` option, so this had to be worked around with `element.click()` via
  `browser_evaluate` just to keep exploring) — but `open_folder_rename_editor()`'s
  and `delete_folder_via_menu()`'s EXISTING `menu_button.click(force=True)` (not
  new this session) already bypasses this correctly for real pytest runs. Worth
  knowing before "fixing" this a second time.
- **HTTP method note**: pinning a folder is `PATCH
  /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` — NOT `PUT` (the
  rename endpoint) or `POST` (create). First `PATCH` documented on this surface
  so far; every other folder mutation in this digest is `PUT`/`POST`/`DELETE`.
- **Case-text drift, same class as the already-documented ELITEA-2099/#1513
  conversation-menu drift, filed as
  [elitea-testing-public#1534](https://github.com/EliteaAI/elitea-testing-public/issues/1534)**:
  both cases' text says the folder context menu shows "Delete, Edit, Export,
  Pin/Unpin". Live-confirmed (source + `browser_snapshot`) the REAL 4-item set is
  **New chat, Rename, Pin on top (or Unpin), Delete** — "Edit" doesn't exist
  (item is "Rename"), "Export" doesn't exist at all, "New chat" is unlisted by
  either case. Not a product bug — both AFS files assert the real, live-confirmed
  set instead of the case's literal list.
- Exploration folders (`ELITEA2121RenameSource`/`New folder_edited`, id `212`;
  `ELITEA2130PinnedSource`/`Pinned Renamed Folder`, id `213`) left undeleted in
  the shared DEV project — same accepted precedent as prior sessions
  (`MCP evaluate`-injected `fetch()` to same-origin API fails, documented below
  in the ELITEA-2118/2119/2120 section; a `curl`-based cleanup attempt via
  `ELITEA_API_TOKEN` also 404'd, likely a project-id/auth-scope mismatch not
  worth chasing further given the already-extensive documented pollution).

## ELITEA-2457 — third near-total duplicate of the same ELITEA-2119/2133
## folder-creation flow, ZERO remaining gap (extend-existing, tag-only)
- ELITEA-2457 ("Chat – Create folder with custom name") is the SAME
  6-step flow as ELITEA-2119 (steps 1-5) + ELITEA-2133 (step 4, expand ->
  empty state) combined — confirming the "near-duplicate case-ID pattern"
  flagged in the ELITEA-2133/2134 section below extends even to a case ID
  far outside that range (2457 vs 2118-2120/2133-2134). Re-executed live
  this session with its OWN literal data ("My Test Folder", fresh folder id
  193 — not reused from ELITEA-2133's earlier, already-deleted run) before
  classifying: default-name-shown, custom-name-typed (replace not append),
  checkmark-active, POST 201, collapsed render, AND expand->empty-state all
  independently reconfirmed.
- Unlike ELITEA-2133 (which needed one new Step 6 to close the expand/empty
  gap), by the time this case landed **that gap was already closed** by the
  ELITEA-2133 extension itself (same trunk, earlier commit) — so ELITEA-2457
  needed literally ZERO new assertion code, only a third stacked
  `@allure.issue` tag on `test_create_folder_with_custom_name`.
- One case element (case step 2, "default name shown") is `already-covered`
  by a DIFFERENT sibling test on this trunk
  (`test_folder_creation.py::test_create_folder_default_name_checkmark_active`,
  ELITEA-2118/2132) rather than by the tag-target test itself — a Coverage
  Map row can point `already-covered` at any merged/on-trunk test, not only
  the one being tagged; worth checking BOTH the direct covering test and
  its siblings before assuming a step needs new code.
- **Pattern reinforced**: this chat-interface module's near-duplicate case
  IDs are not confined to adjacent ID ranges — always `grep -i "folder"`
  (or the relevant noun) across this digest's existing sections FIRST,
  regardless of how far the new case's ID sits from a previously-seen
  cluster.

## ELITEA-2133/2134 — near-total TMS-case duplicates of ELITEA-2119/2120,
## same session batch (extend-existing, tag-only + one small gap)
- ELITEA-2133 ("...Custom Name via CHATS Header Icon") and ELITEA-2134
  ("...Cancel Discards New Folder") are the SAME two flows as ELITEA-2119/
  2120 below — different TMS case IDs, near-identical case text, only the
  literal folder-name test data differs ("My Test Folder"/"Cancelled
  Folder" vs "My Sprint Folder"/"Temp Folder"). Both re-executed live this
  session with their OWN literal data (not assumed from the ELITEA-2119/
  2120 run) before classifying — both confirmed to behave identically.
- Routed `extend-existing` against `test_chat_folder_creation_custom_name_and_cancel.py`
  (merged onto this batch's OWN trunk `tests/batch-chat-remaining-w05`, NOT
  yet `origin/automation/base` — the merged-target rule permits
  `extend-existing` against a same-batch-trunk target, unlike
  `already-covered` which needs a base-merged target).
- ELITEA-2134: **zero** assertion gap vs ELITEA-2120 — tag-only extension
  (second `@allure.issue` decorator, no test-body change). ELITEA-2133 DOES
  have one real gap ELITEA-2119 never covers: case step 4 ("click the
  folder to expand it -> shows empty state") — the covering test only
  verifies the new folder renders COLLAPSED, never expands it. Appended a
  new Step 6 to `test_create_folder_with_custom_name` calling the existing
  `expand_folder()`/`get_folder_empty_state_text()` methods (added
  ELITEA-2098/2115, no new page-object work needed).
- **Pattern worth watching for future chat-folder cases**: this TMS module
  appears to carry near-duplicate case pairs across different ID ranges
  (2118-2120 vs 2133-2134 here). Worth a quick `grep -i "folder"` over
  upcoming case snapshots before assuming `ready-for-automation` — check
  this digest's existing sections first, they may already answer it.

## Folder creation inline editor — custom name / cancel / checkmark-active
## at creation time (ELITEA-2118/2119/2120)
- ELITEA-2118's case (open create-folder editor, leave default "New folder"
  name, confirm) is a near-total duplicate of the ALREADY-MERGED
  `test_folder_creation.py`/ELITEA-2132 test — every step except the case's
  own step 4 ("checkmark is active") is already proven there (2132 only
  asserts confirm/cancel icon VISIBILITY, never the `data-disabled` state).
  Handled as `extend-existing`: appended ONE small new test method to
  `test_folder_creation.py` that opens the editor, asserts
  `is_folder_name_confirm_enabled()` is `True` for the untouched default
  name, then cancels (no real folder created, no cleanup needed).
- `FolderItem.jsx`'s `isFolderSaveEnabled = isFolderNameValid &&
  (isNewFolder || folderName !== name)` — for a NEW folder (`isNewFolder ===
  true`) the `(isNewFolder || …)` clause short-circuits true, so the gate
  collapses to `isFolderNameValid` ALONE — no "changed" requirement, unlike
  the RENAME path (`test_chat_folder_rename_checkmark_validation.py`,
  ELITEA-2458, which needs BOTH valid AND changed). Live-confirmed: the
  confirm checkmark is active (`data-disabled="false"`) the INSTANT the
  create-folder editor opens with the untouched "New folder" default — no
  typing required.
- ELITEA-2119 (type a custom name, confirm) and ELITEA-2120 (type a name,
  cancel) had ZERO existing coverage — the only other caller of
  `click_create_folder_button()` (`test_chat_folder_rename_checkmark_validation.py`)
  only uses it as SETUP to seed a folder before opening the RENAME editor,
  never asserting the create-flow's own custom-name-save or cancel-discard
  outcome. New family AFS + new file
  `test_chat_folder_creation_custom_name_and_cancel.py`, two independent
  test methods (action diverges — confirm vs cancel — not just data).
- Both scenarios live-confirmed via Playwright MCP against
  `http://localhost:5173`: typing "My Sprint Folder" over the default via
  `set_folder_name()`'s click+clear+`press_sequentially()` idiom correctly
  REPLACES (not appends) the value; confirm fires `POST
  /elitea_core/folder/prompt_lib/399` -> `201` with `name == "My Sprint
  Folder"`. Cancel after typing "Temp Folder" fires **zero** new requests
  to `folder/prompt_lib` at all (confirmed via `browser_network_requests`,
  not just a DOM-absence check) — a genuine client-side-only discard, same
  as the already-documented conversation-rename cancel path (ELITEA-2100,
  above).
- **Gotcha, not a defect**: `browser_evaluate`-injected `fetch()` calls to
  the app's own same-origin `/api/v2/...` path fail with `TypeError: Failed
  to fetch` from the MCP evaluate context (confirmed for both GET and
  DELETE) — NOT usable as an ad-hoc exploration-session cleanup shortcut.
  Real pytest tests are unaffected (`page.request`, Playwright's
  `APIRequestContext`, is a different mechanism and works fine — see
  `ChatPage.delete_folder_via_api()`). See
  `.agents/memory/test-automation-engineer/mcp_evaluate_fetch_to_same_origin_api_fails.md`.
  Left one exploration-only folder ("My Sprint Folder") undeleted in the
  shared DEV project as a result of this — the UI delete flow was not
  attempted mid-exploration; acceptable given the project's already
  extensive pre-existing pollution (see the folder-rename section below).

## Conversation-rename tooltip content — CLOSES the gap, EXTENDS not duplicates
## the ELITEA-2110/2112/2113 family (ELITEA-2111, combined analyst+implementer)
- ELITEA-2111's entire 5-step case ("hover inactive checkmark → exact tooltip
  text → checkmark stays inactive → recover to valid → tooltip disappears,
  checkmark active") is verbatim-equivalent to assertions the ELITEA-2110/
  2112/2113 family's merged test (`test_conversation_rename_invalid_chars_and_recovery.py`,
  on this batch trunk) ALREADY makes: ELITEA-2110's row for tooltip-appears +
  exact-text-match + inactive-checkmark, ELITEA-2113's Shape B for the explicit
  "tooltip element count 0" + active-checkmark recovery assertion. Live
  re-confirmed this session with the case's own literal data hint (`$ % @`
  characters, not the existing row's `HI Chat$$%`) — same result, same
  mechanism (ONE static `ConversationNameWarningMessage` for any regex-failure
  reason, source- and now doubly live-confirmed).
- Extended (not duplicated): one new `pytest.param` row on the existing
  parametrized Shape-A test using this case's own invalid-char data, plus a
  coverage-tag-only `@allure.issue` addition to the existing Shape-B (2113)
  test for step 5 — no new assertion code needed there, its existing
  `data-disabled == "false"` + `get_conversation_name_confirm_tooltip_text()
  == ""` check already IS step 5.
- No case-text drift: the case's quoted tooltip string matches
  `ConversationNameWarningMessage` byte-for-byte (verified via DOM
  `textContent` read, not just source grep).

## Conversation-rename checkmark active/inactive threshold — CLOSES ELITEA-2099's
## own forecast, source-only confirmation (ELITEA-2105/2106/2107/2108/2109)
- Closes the gap ELITEA-2099's § Automation Hints explicitly forecast ("directly
  relevant to the sibling conversation-rename boundary cases … empty/short/
  special-char checkmark-inactive states"). All five cases confirmed via a fresh
  full-file read of `ConversationItem.jsx` this session (not re-driven live — the
  mechanism is identical to the already-live-verified `isSaveEnabled`/
  `ConversationNameRegExp` pair documented in the ELITEA-2099/2101/2102 sections
  above, so a source read is a stronger/faster confirmation than repeating a
  manual click-through against the shared DEV project).
- `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/` — 1
  mandatory first char + `{2,63}` more = **3–64 chars total, floor AND ceiling on
  the SAME regex** already documented for the folder/conversation length-boundary
  work above. 1 and 2-char inputs both fail the floor; 3 chars is the exact
  activation point (`isConversationNameValid` flips true) — this is why
  ELITEA-2109's title ("Becomes Active at 3 Characters") is a literal, precise
  description of the `{2,63}` quantifier, not an approximation to verify loosely.
  Empty string also fails (same regex, no bypass for `''`).
- `isSaveEnabled = isConversationNameValid && (isNew || conversationName !==
  name)` — for an EXISTING conversation (`isNew` false in this family's own
  setup) collapses to `isValid && changed`. ELITEA-2105's "no changes made" row
  is the ONLY one of the five that fails the `changed` half specifically (start
  from a name that is itself REGEX-VALID, e.g. 25 chars of allowed characters,
  so the disabled state is provably about "unchanged", not "invalid") —
  ELITEA-2106/2107/2108 fail the `isValid` half instead.
- **The confirm `Box`'s `onClick={isSaveEnabled ? (isNew ? onCreate : onSave) :
  null}` — when disabled, `onClick` is literally `null`.** A disabled-state click
  is therefore a genuine, un-intercepted browser no-op (no `force=True` needed,
  no suppressed handler to route around) — the honest assertion for "click has no
  effect" is that NO `PUT .../conversation/prompt_lib/...` request fires at all,
  the editor stays open, and the sidebar item keeps showing the conversation's
  ORIGINAL persisted name. Same idiom as ELITEA-2100's cancel-flow "no PUT fires"
  check: capture requests via `capture_requests_matching` BEFORE the click, then
  call `chat.wait_for_network()` (framework-native `networkidle`, not a raw sleep)
  to give any would-be async call a chance to register before reading the
  captured list.
- No new testids needed — `chat-conversation-name-input` /
  `chat-conversation-name-confirm-button` (with its `data-disabled` state
  attribute) / `chat-conversation-name-cancel-button`, all from
  `EliteaAI/EliteaUI@ff56e29d` (ELITEA-2099), cover this family completely.
- No case-text drift, no defect — all five cases automate exactly as written
  against the source-confirmed mechanism.

## Conversation-rename overflow — truncation itself, TYPE + PASTE both confirmed identical (ELITEA-2103/2104)
- Closes the gap ELITEA-2101/2102's AFS flagged ("51+/overflow/paste-truncation …
  that's ELITEA-2103/2104's territory"). Both live-confirmed this session against
  the shared "Review attached documents" conversation (id 420), each restored
  immediately after:
  - **Type 51 chars** (`press_sequentially`, real per-keystroke events): input ends
    at exactly 50 chars (`"A"*50`), 51st keystroke silently dropped. Confirm button
    `data-disabled="false"`. Save → `PUT .../conversation/prompt_lib/471/420` → `200`.
  - **Paste 60 chars** (real `navigator.clipboard.writeText()` + `Control+V`/`Meta+V`
    keypress — NOT a DOM-injected value): input ends at exactly 50 chars, same
    left-slice result. Same confirm-enabled + `PUT` 200 behavior.
  - **Why both land identically**: `ConversationItem.jsx` wires only
    `onChange={onChangeConversationName}` on the input — no separate `onPaste`
    handler exists (grep-confirmed) — so a paste's resulting native `input`/`change`
    event is caught by the exact same `slice(0, MAX_CONVERSATION_LENGTH)` logic as
    typing.
  - No error toast on either the truncation itself or the subsequent save; only
    console noise across both runs was the pre-existing `secrets/secrets/default`
    403 (3 occurrences total this session — 1 per save + 1 ambient).
  - No case-text drift, no defect — both ELITEA-2103 and ELITEA-2104 automate
    exactly as written. Family-AFS call: kept SEPARATE (not merged with each other
    or with 2101/2102) — type vs paste is a genuine interaction-technique
    difference (`test-case-analysis` § Execute: "differ in steps → separate AFS"),
    even though the underlying assertion/mechanism is identical.
  - Paste idiom precedent: `automation/pages/project_context_page.py`'s
    `set_editor_content_via_paste()` — reuse that pattern (real clipboard write +
    real keyboard paste shortcut) for any future paste-testing on this surface;
    never inject the pasted value via `fill()`/`page.evaluate()` directly into an
    input's DOM value — that would substitute the test for the browser's own paste
    event and stop proving the product's truncation handler at all.

## Conversation-rename length boundary — MAX_CONVERSATION_LENGTH source-confirmed (ELITEA-2101/2102)
- **`MAX_CONVERSATION_LENGTH = 50`** (`EliteaUI/src/common/constants.js:74`).
  `ConversationItem.jsx`'s `onChangeConversationName` does
  `event.target.value.slice(0, MAX_CONVERSATION_LENGTH)` on every change — so 49-char
  and 50-char names are NEVER truncated (slice only bites the 51st+ char); 50 is the
  boundary where truncation would first start to matter, not a rejection point.
  Live-confirmed both: typed 49 A's → input length 49, confirm enabled, `PUT` 200;
  typed 50 A's → input length 50 (no truncation), confirm enabled, `PUT` 200. No
  case-text drift, no defect — both cases automate exactly as written.
- `FolderItem.jsx` uses the SAME `MAX_CONVERSATION_LENGTH`/`ConversationNameRegExp`
  pair (see the folder-rename section below) — the two components share the
  length-cap and regex-validity mechanism, only the entity differs.
- 51+/overflow/paste-truncation behavior is NOT covered by this pass — that's
  ELITEA-2103/2104's territory (already flagged as the next sibling pair in
  ELITEA-2099's Automation Hints).

## Manual `ConversationAPI()` script vs the `conversation_api` fixture — project-id mismatch trap (ELITEA-2100)
- A standalone `ConversationAPI(browser_cookies=[])` (no fixture chain, default
  `settings.elitea_project_id`) resolved to project **399** during ad-hoc
  exploration, while the live browser session (`auth_state`/`VITE_DEV_TOKEN`) is on
  project **471** ("Elitea Testing Team") — a conversation created that way opened
  as "Conversation not found" at `/chat/{id}`. The pytest `conversation_api`
  fixture (session-scoped, browser-cookie-derived) does NOT have this problem —
  ELITEA-2099's test passes using it. Only a risk for **manual exploration
  scripts** run outside the fixture chain (as this analyst pass did, once, then
  switched to reusing a shared live conversation instead) — never copy a bare
  `ConversationAPI(browser_cookies=[])` instantiation into test setup; always go
  through the `conversation_api` fixture.

## Conversation rename editor — CANCEL path live-confirmed (ELITEA-2100)
- Clicking `chat-conversation-name-cancel-button` after typing a new name: input
  closes (`chat-conversation-name-input` → count 0), sidebar reverts to the
  ORIGINAL name, and — live-confirmed via `browser_network_requests` — **no**
  `PUT .../conversation/prompt_lib/{project_id}/{id}` fires at all (typing alone
  also fires nothing; only cancel-click was tested, no request appeared either
  before or after). Persists correctly across navigate-away/back too (re-verified
  by leaving `/chat` and returning). Symmetric with ELITEA-2099's save-path
  (`PUT` fires + resolves 200 on checkmark-click) — together the pair proves the
  editor's two exit paths are mutually exclusive at the network layer, not just
  the DOM layer.

## Conversation rename editor — checkmark/cancel testids ADDED + same a11y-snapshot gotcha as folders (ELITEA-2099)
- **`ConversationItem.jsx`'s rename editor had NO testids before this pass** — added
  this session, mirroring `FolderItem.jsx`'s existing `chat-folder-name-*` shapes
  exactly (same `Input.StyledInputEnhancer` component, same `inputProps` channel):
  `chat-conversation-name-input`, `chat-conversation-name-confirm-button` (carries
  `data-disabled="true"/"false"` off `isSaveEnabled` — testid=identity/state=data-*),
  `chat-conversation-name-cancel-button`. Committed `EliteaAI/EliteaUI@ff56e29d` on
  `automation/testids`. `isSaveEnabled = ConversationNameRegExp.test(name) &&
  (isNew || name !== originalName)` — same "valid AND changed" gate as folders.
- **Same a11y-snapshot pruning gotcha as the folder confirm button (ELITEA-2458)
  reconfirmed live for the conversation editor**: in the disabled/unchanged state
  (`cursor:default`) `chat-conversation-name-confirm-button` may not appear as a
  distinct node in a Playwright `browser_snapshot`'s accessibility tree — assert via
  the testid locator directly (`page.locator('[data-testid="..."]')`), never via a
  snapshot accessible-name read. The cancel button (always `cursor:pointer`) is
  unaffected.
- **The input pre-fills with the CURRENT name** (`value={conversationName}` synced
  from the `name` prop via a `useEffect`) — confirmed live: opening rename on
  "Review attached documents" showed that exact text in the input before any typing.
- **Clicking the confirm button, when the conversation being renamed is NOT already
  the active/open one, also navigates into and selects it** — confirmed live: URL
  went from `/chat` to `/chat/{id}?name=...` on save. Side effect of
  `onSave`→`onEdit`'s existing select-conversation behavior, not a defect; account
  for the navigation in any URL assertion made right after a checkmark click.
- **Context-menu item is labelled "Rename", not "Edit"** — the TMS case ELITEA-2099's
  own "Edit option" title/step text is stale vs the live product (same drift already
  documented for ELITEA-2114/#695 on the identical `ConversationItem.jsx`
  `menuItems` array); filed as sibling clarification **#1513**. Live-verified full
  menu-item set for project 471 (non-personal/non-public): **Rename, Move to,
  Playback, Duplicate, Make public, Share, Pin on top, Delete** (8 items) — the
  case's literal "Delete, Edit, Move to, Export, Playback, Pin on top" list is wrong
  on every count (wrong label, one item that doesn't exist, three omitted). Item
  count/set is project-dependent (#695 saw only 5 in the personal project) — don't
  assert a fixed count without pinning the project.

## Folder rename editor — checkmark enable/disable logic + a11y-snapshot gotcha (ELITEA-2458)
- **Full validation logic, read from `FolderItem.jsx` source** (grounds every
  assertion, don't re-derive): `isFolderNameValid = ConversationNameRegExp.test(folderName)`
  where `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
  (3–64 chars total). `isFolderSaveEnabled = isFolderNameValid && (isNewFolder
  || folderName !== name)` — for an EXISTING folder (rename, not create) this
  means BOTH valid AND changed are required to activate the checkmark.
  Tooltip `title={isFolderNameValid ? '' : FolderNameWarningMessage}` — shows
  ONLY when the regex fails (empty, 1–2 chars, bad first-char, bad charset),
  NEVER for "valid but unchanged". Exact tooltip copy (`src/common/constants.js:97`,
  `FolderNameWarningMessage`): `"The folder name should be 3 to 64 characters
  long. It can include letters (a-z, A-Z), numbers (0-9), underscores (_),
  brackets ([]), parentheses (()), dots (.), hyphen(-), and spaces. Please
  note that the first character should not be a space."`
- **The confirm checkmark has NO `data-*` state attribute today** — only a
  CSS `fill` color (bright=active/dim=inactive via `theme.palette.icon.fill.default`
  vs `.disabled`) and `cursor` (`pointer` vs `default`). Confirmed via full
  source read: `onClick={isFolderSaveEnabled ? handler : null}` on a plain
  `Box`, no `disabled`/`aria-disabled` anywhere. Any case asserting this
  button's active/inactive state needs a NEW `data-disabled`/`data-enabled`
  attribute added (`needs-adding`, not yet done as of ELITEA-2458).
- **Accessibility-snapshot gotcha, confirmed live (4 states compared
  side-by-side: empty / 2-char / unchanged-valid / 3-char-changed):** the
  confirm `Box`'s representation in a Playwright `browser_snapshot` CHANGES
  with state. Invalid-name states (empty, "AB") → element appears WITH the
  tooltip text as its accessible name (MUI wires non-empty `title` as
  accessible-name source). Valid-name states (unchanged OR 3-char-changed) →
  `title=''`, no accessible-name attribute, element is either a bare
  unlabeled `generic` (only distinguishable from the adjacent Cancel button
  by DOM position) or PRUNED FROM THE SNAPSHOT ENTIRELY when `cursor` isn't
  `pointer` (the inactive-but-valid "unchanged" state specifically — this bit
  once caused a real accidental misclick onto the Cancel button during manual
  exploration, since only ONE non-textbox `generic` showed up where two
  should have existed). **Only `page.locator('[data-testid="chat-folder-name-confirm-button"]')`
  resolved correctly in all 4 states** — role/label/text locators are not
  just against this project's policy here, they are functionally unreliable.
  Same likely applies to the sibling Cancel button (untested — not exercised
  by ELITEA-2458's case steps).
- **`set_folder_name()`'s documented "append not replace" race is real and
  currently causing visible data pollution** — confirmed live: the shared DEV
  project's folder list carries a `"New folder6New folder"` artifact,
  matching exactly the failure mode `ChatPage.set_folder_name()`'s own
  docstring warns about (a bare `Control+a` losing the race against React's
  re-render of the default value). Always use `.clear()` after focus, per
  that method's existing implementation — don't hand-roll a `Control+a`-only
  clear for any new folder/conversation-name editing code.
- **REGRESSION, filed EliteaAI/elitea-testing-public#1309**: the folder
  dot-menu "Delete" item's `key: 'chat-folder-menu-delete'` (→ testid
  `chat-folder-menu-delete-menuitem` via `DotMenu`'s `item.key` mechanism) has
  been added and lost TWICE in `EliteaUI` history (`de154cc2` added it,
  `8147d5c1`'s own commit message says it re-added a testid "lost by an
  earlier main merge", then `6bec1451` — "Fix rename conversation block
  behaviour" — dropped it a second time). **Absent from both `main` and
  `automation/testids` HEAD as of 2026-08-07.** This silently breaks
  `ChatPage.delete_folder_via_menu()`'s cleanup in `test_folder_creation.py`
  and `test_move_conversation_to_folder.py` (swallowed by their own
  `try`/`except`) — confirmed 19 leaked "New folder"/"New folder6" folders
  sitting in the shared DEV project as a result. **Do not assume
  `FOLDER_MENU_DELETE_ITEM`/`delete_folder_via_menu()` work** until #1309 is
  confirmed fixed — check the ticket before reusing either as a pattern.
- **The Rename dot-menu item has NEVER had a testid** (not a regression, a
  gap — Pin also has none, out of scope unless a future case touches it).
  `DotMenu`/`BasicMenuItem`'s mechanism (`testId={item.key}` →
  `data-testid={testId}-menuitem`) is generic and battle-tested (same
  mechanism powers `chat-conversation-menu-rename-menuitem` on
  `ConversationItem.jsx`'s sibling items) — adding `key: 'chat-folder-menu-rename'`
  to `FolderItem.jsx`'s menuItems array is a one-line, low-risk addition.
- **Tooltip content has no testid** — `@/ComponentsLib/Tooltip` (the specific
  Tooltip wrapper `FolderItem.jsx` uses, distinct from `@/[fsd]/shared/ui`'s
  Tooltip used elsewhere in the Folders feature) is a thin MUI `Tooltip`
  spread-through wrapper; `slotProps={{ popper: { 'data-testid': '...' } }}`
  can be set directly at the call site with no shared-component change
  needed (unlike the `toolkit-field-bucket-info-tooltip-content` precedent,
  which needed a prop threaded through several layers — this one's simpler).

**Resolved/confirmed during ELITEA-2459 implementation (extends the section
above, does not supersede any of it):** live-drove two ADDITIONAL invalid-name
scenarios beyond ELITEA-2458's own {empty, 2-char, unchanged, 3-char-changed}
set — a name with unsupported special characters (`"Folder$$%%"`) and a name
whose first character is a space (`" ValidRest"`, otherwise fully valid).
Both behaved identically to the already-documented invalid states: same
`data-disabled="true"` on `chat-folder-name-confirm-button`, same exact
`FolderNameWarningMessage` tooltip text (verbatim match, not just prefix),
same network-silent no-op click (zero new PUT requests). Confirmed this is
ONE static tooltip message shown for ANY regex-failure reason (length,
change-state, charset, or first-character) — `FolderItem.jsx` does not
differentiate WHY `isFolderNameValid` is false. Also **reconfirmed live**
that `chat-folder-menu-delete-menuitem` is still dead (issue #1309,
unresolved as of this session) — `document.querySelector` returns `null`
for it even though the visible "Delete" menuitem/confirmation dialog still
function by text/role (i.e. the UI-level Delete flow works, only the
specific testid used by `delete_folder_via_menu()` is missing — same
symptom already documented above, now reverified on a fresh session/date).
No new testids or page-object changes were needed for ELITEA-2459 — every
handle ELITEA-2458 added was reused verbatim and all resolved correctly.

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

  **Resolved during ELITEA-2151 implementation (combined analyst+implementer,
  2026-08-15):** the follow-up above is now closed and LIVE-verified. Seeded
  one pinned folder + one pinned conversation + one unpinned folder + one
  unpinned conversation (all fresh, own IDs — no ambient-data dependency) and
  asserted all 3 adjacent-tier boundaries (pinned-folder→pinned-conversation,
  pinned-conversation→unpinned-folder, unpinned-folder→unpinned-conversation)
  via bounding-box Y-position, plus the 2 non-adjacent "skip" pairs the
  case's own Step 3 asks for directly. All 4 tiers behaved exactly as
  `Conversations.jsx`'s source predicted on the FIRST live run — green,
  zero reruns, zero new console errors, zero product defects. Folder-pin
  wrapped in `page.expect_response()` for the PATCH (mirrors ELITEA-2121/
  2130's own proven idiom); conversation-pin reused the bare click +
  `is_conversation_pinned()` idiom ELITEA-2149's test already proves
  reliable — no new flake risk introduced by combining both mechanisms in
  one test. New test class appended to `test_pin_conversation.py`
  (`TestChatPanelOrderingPinnedFoldersAndConversations`); zero existing
  method bodies touched (verified: full 3-test file re-run green,
  additive-only `git diff` grep empty). Zero new testid work — every handle
  (`chat-folder-menu-pin-menuitem`, `data-pinned` on both folder/conversation
  rows, `chat-folder-item-{id}`, `chat-conversation-item-{id}`) already
  existed from prior sessions on this surface. See ELITEA-2151's AFS
  (`test-specs/chat-interface/lextend_pinned-conversation-panel-ordering_ELITEA-2151.md`)
  for the full reasoning.
- No success toast on pin (`usePinConversation.hooks.js`'s
  `onPinConversation` only calls `toastError` on FAILURE) — don't wait for
  one.
- **Resolved/added during ELITEA-2150 implementation:** unpin is the SAME
  `chat-conversation-menu-pin-menuitem` testid, label flips to `"Unpin"`.
  A PINNED conversation's row carries the same `aria-disabled="true"`
  draggable-wrapper ancestor already documented above for pinned FOLDERS
  (`isDragDisabled={isPinned}`) — confirmed live via `browser_evaluate`
  DOM-chain inspection, a plain (non-forced) click on the scoped 3-dot menu
  button times out ("element is not enabled") for a PINNED conversation
  specifically. `ChatPage.open_conversation_context_menu()` already calls
  `menu_button.click(force=True)` (pre-existing, ELITEA-2114) so this needs
  no new workaround — but it's the first case to actually exercise a pinned
  conversation's own context menu (ELITEA-2149 only ever opens the menu
  BEFORE pinning), so record it here before someone "discovers" it again.
  Unpin flips `data-pinned` `"true"`→`"false"` and `chat-pin-icon` count
  `1`→`0`; the conversation reappears scoped inside its date group
  (`is_conversation_in_group()`), same as any freshly-created conversation.

  **ELITEA-2159 ("Left Panel Order Verified After Multiple Pin Actions",
  combined analyst+implementer, batch chat-remaining-w09, 2026-08-15) is a
  near-total duplicate of ELITEA-2151** — same 4-tier fixture (pinned folder,
  pinned conversation not in a folder, unpinned folder, unpinned
  conversation), same panel-order + same-type-ordering + folders-before-
  conversations assertions, all already directly asserted by
  `TestChatPanelOrderingPinnedFoldersAndConversations::test_pinned_folder_and_conversation_render_above_unpinned_panel_order`
  (merged `origin/automation/base`). Classified `already-covered` (zero new
  code) — live-reconfirmed by re-running the covering test this session
  (`1 passed in 19.44s`), not assumed from the digest alone. See ELITEA-2159's
  AFS (`test-specs/chat-interface/lcovered_left-panel-order-after-multiple-pin-actions_ELITEA-2159.md`)
  for the full step-by-step dedup proof.

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
- **Duplicate manual TMS cases exist for this cluster (2026-08-19,
  ELITEA-2471/2472/2473 vs ELITEA-2212/2213/2214).** Different TMS case IDs,
  near-verbatim step tables, same trigger precondition ("conversation with
  only a HITL toolkit participant"), same Authorize/Block/Block-with-Comment
  buttons, same expected results — classified `already-covered` against the
  merged `test_hitl_sensitive_action_authorization.py` (commit `ddaf8b31b`)
  without re-execution (the underlying precondition needs `pytest.mark.guardrails`
  + a deployed env anyway — not reachable on localhost regardless of case ID,
  see the environment-limitation note above). **If another HITL-authorize/
  block/block-with-comment-titled case appears under yet another ID, check
  here first** — this TMS may contain more duplicate manual entries for the
  same feature. See `test-specs/chat-interface/lcovered_hitl-*-duplicate-manual-case_ELITEA-247{1,2,3}.md`.

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

**Resolved/added during ELITEA-2464 implementation (2026-08-07):** the Modules
panel documented above (ELITEA-2162 section) now renders **8** toggles, not 7 —
live-confirmed a new **"Ask User"** toggle (`data-testid="modules-toggle-ask_user"`,
tool key `ask_user`) between "Python Sandbox" and "Swarm Mode". Both ELITEA-2162's
merged spec and ELITEA-2464's case text predate it (product change, not a defect —
filed as clarification EliteaAI/elitea-testing-public#1293).
`ChatPage.MODULE_TOGGLE_ORDER` was extended with the new entry in its live DOM
position (additive; the 7 pre-existing entries are unchanged) so the covering
spec's dynamic `len(MODULE_TOGGLE_ORDER)` count assertion stays correct. The
plus-menu's full top-level item list was also live-confirmed this session (non-Team
project): exactly 6 items in DOM order — Attach Files, Modules, Agents, Pipelines,
Toolkits, MCPs (no "Invite Users" — Team-project-only, per the existing
`invite_users_menuitem` docstring).

## New-conversation-from-Team-project + drag-drop + LLM switch (ELITEA-2091)
- **Team project's plus-menu, full item set, live-confirmed**: Attach Files
  (with "N left" counter, live text child of `chat-attach-menuitem-button`,
  no separate testid), Modules, Agents, Pipelines, Toolkits, MCPs, **Invite
  Users** — the last one renders ONLY for a Team/non-Private project
  (`!isPrivateProject` guard), absent entirely (not disabled) on the default
  Private project. Confirmed by diffing the identical popper on both
  projects in the same session.
- **Multi-file attach-via-picker counter arithmetic, live-confirmed**:
  selecting 3 files in ONE `file_chooser.set_files([...])` call moves the
  "Attach Files (N left)" text from `"10 left"` → `"7 left"` in a single
  step (not 3 separate decrements) — matches `AttachmentButton.jsx`'s
  `remainingAttachments` computation, consistent with the existing
  ELITEA-2197 10-file-limit spec's confirmed mechanism.
- **Model dropdown option testid is keyed by the model's INTERNAL id, not
  its display name** — confirmed live: clicking the menu item labelled
  "Anthropic Claude 4.5 Sonnet" resolved
  (`page.getByTestId(...)`) to
  `model-selector-option-eu.anthropic.claude-sonnet-4-5-20250929-v1:0`.
  `LLMModelsMenu.jsx`: `data-testid={`model-selector-option-${item.name}`}`,
  `item.name` is the raw model id. Never hardcode a display-name-based
  testid guess for this menu.
- **Selected-model state is a genuine same-element conditional render, not
  a testid ternary** (`LLMModelsMenu.jsx`): the `MenuItem`'s OWN testid
  (`model-selector-option-{name}`) never changes; `selected={item.id ===
  selectedModel?.id}` sets MUI's `Mui-selected` class, and a `CheckedIcon`
  renders as a conditional CHILD only for the selected item (no testid on
  the icon itself). Compliant assertion shape: testid-identity + read the
  `class` attribute for `Mui-selected` (or check the child-icon count
  scoped under that one testid'd parent) — no new testid needed.
- **End-to-end flow (Team project +Chat → attach 3 files via picker →
  switch LLM → send with attachments → auto-name) fully reproduced live,
  zero defects.** URL sequence: blank composer → `/chat/{id}?name=New+Chat`
  immediately on send → resolves to `/chat/{id}?name=<generated title>`
  within ~15s. Sidebar: conversation renders under
  `chat-conversation-group-header-today` as a `"Naming"` button (nested
  `role="progressbar"`) immediately, then flips to the real title with no
  further placeholder — `ChatPage.wait_for_naming_label_to_resolve()`
  (pre-existing) already implements the correct wait, reuse verbatim. Same
  mechanism ELITEA-2095 (`test_open_conversation_today_section.py`) already
  proved in this exact project — ELITEA-2091 layers attachments+LLM-change
  on top, doesn't re-derive naming.
- **Drag-and-drop composer drop-zone has NO testid** — confirmed via source
  read (`EliteaUI/src/ComponentsLib/Chat/UserInput.jsx`): the outer `Box`
  wrapping `onDragOver`/`onDragLeave`/`onDrop` (`sx={styles.container}`,
  wired via the real `useFileDragAndDrop` hook — genuinely functional, not
  a stub) carries no `data-testid` at all. `needs-adding`
  (`chat-composer-dropzone` or similar) before this step has a stable
  handle. NOT click-verified live this session (time budget) — only
  source-confirmed as a real, working feature.
- **Provenance, freshly verified this session** (`git fetch origin` first):
  every testid this case's flow touches — `project-selector-trigger`,
  `select-option-471`, `sidebar-create-button`, `plus-menu-button`,
  `chat-attach-menuitem-button`, `invite-users-menuitem`,
  `model-selector-option-`, `chat-conversation-group-header-`,
  `chat-attachment-chip-` — is **on `main` already** (all `YES`/`YES`).
  This case needs ZERO new testids except the drag-drop drop-zone above.

**Resolved/added during ELITEA-2091 implementation:**
- **`chat-composer-dropzone` added** on `UserInput.jsx`'s outer drop-zone
  `Box` (`automation/testids` commit `dd417746`). The synthetic-`DataTransfer`
  drag-and-drop technique (dispatch `dragenter`→`dragover`→`drop`
  `DragEvent`s carrying a real in-page-constructed `File`) is
  **live-confirmed working** against this testid — chip renders, counter
  decrements, message-thread attachment list all correct end-to-end.
- **FileList.jsx's visible/overflow split is live, not just a docstring
  claim** — with the plus-menu popper open (narrowing the composer) even
  3–4 attachments can overflow into the "+N" bucket depending on viewport.
  Any assertion on attached-file count/names MUST use
  `get_total_attached_file_count()`/`get_all_attached_file_names()`
  (visible+overflow), never the visible-only
  `get_attachment_chip_count()`/`get_visible_attachment_names()` — a
  visible-only assertion silently stays flat across a real successful
  attach when the new item lands in overflow instead of a visible chip.
- **`get_overflow_attachment_names()`'s internal `Escape` key press closes
  the WHOLE plus-menu popper, not just the overflow sub-menu** — the same
  ELITEA-2203 "Escape closes more than intended" quirk
  `ChatPage.close_plus_menu_popper()`'s docstring already warns about,
  triggered here as a side effect of a read-only helper. Any caller that
  needs to read the "Attach Files (N left)" counter text AFTER calling
  `get_all_attached_file_names()`/`get_overflow_attachment_names()` must
  read the counter FIRST — the popper may already be gone afterward if an
  overflow bucket existed.
- **The composer's model-selector-name text updates one React render tick
  after the option-click closes the dropdown** — a one-shot
  `text_content()` read immediately after `select_llm_model_by_suffix()`
  can race and read the STALE (previous) model name. Use
  `ChatPage.wait_for_selected_model_name_change(previous_name)`
  (`expect(...).not_to_have_text(...)`, auto-retries) instead of a bare read.
- **Reopening the model-selector dropdown via the OUTER `model_selector`
  (`model-selector-button`) field is intermittently unreliable** — clicking
  the `ButtonGroup` container's bounding-box center doesn't always land on
  the actual interactive child. `ChatPage.open_model_selector()` (new,
  clicks `model_selector_name` directly — the real `Button.BaseBtn` with
  the `onClick` handler) is the reliable open/reopen entry point; prefer it
  over the pre-existing `click_model_selector()` for any NEW test that
  reopens the dropdown mid-flow.
- **Gotcha for implementers doing concurrent live exploration:** the
  localhost dev-token identity (`auth_state`/`VITE_DEV_TOKEN`) is a SHARED
  backend user across every browser session hitting this DEV backend — a
  live MCP/browser-verify session run WHILE a pytest run is also driving
  the app (same user identity) can cross-contaminate "current/last
  conversation" state between the two, producing a pytest failure whose
  message-thread content belongs to the OTHER (MCP) session's conversation.
  Not a product defect — confirmed by re-running the exact same pytest
  invocation in isolation (no concurrent MCP session): clean green, no
  code change needed. Don't drive live exploration and a pytest run
  concurrently against the same dev-token identity.

## Date-group bucketing (Today/This Week/Older) is SERVER-computed, not client (ELITEA-2096/2097, blocked)
- **Cannot be reproduced via client-side clock mocking.** Confirmed via
  source read: `conversationList.api.js`'s `foldersList`/`conversationsList`
  queries both send `grouped: true` as a query param to the server (lines
  47-91) — the server buckets by real `created_at`, the client never runs
  its own `isToday`/`isThisWeek` date math. `page.clock` (or any client-time
  trick) has zero effect on which bucket a conversation renders in.
- **The API cannot backdate a conversation.** `ConversationUpdate`'s
  OpenAPI schema (`GET /shared/openapi/?plugins=elitea_core&all=true` on
  `dev.elitea.ai`) has no timestamp field at all — only `name`,
  `is_private`, `folder_id`, `attachment_participant_id`, `instructions`,
  `is_hidden`, `meta`. Same for `ConversationCreate` (no `created_at`
  override). There is currently no honest way to seed a This-Week/Older
  conversation in a live test run.
- **The environment currently has zero non-today conversations** in
  either accessible project (Private/399, Elitea Testing Team/471) —
  every existing chat AFS in this feature area (ELITEA-2091/2095, this
  session's ELITEA-2098) deletes its own seeded conversations in
  `finally`, so nothing survives to age into a later bucket.
  `DEFAULT_EXPANDED_GROUP = 'today'` (`conversationList.constants.js:9`)
  — This Week/Older ARE collapsed by default, matching both case texts.
  ELITEA-2096/ELITEA-2097 are `blocked` for this reason — see
  `test-specs/chat-interface/l3_open-existing-conversation-this-week-older-sections_ELITEA-2096.md`.
  A future analyst re-probing this: check first whether the ongoing
  127-case chat-remaining campaign has organically left any conversation
  aged past today (nothing was DESIGNED to survive, but a crashed/aborted
  run's seed might have).

## Folder seeding via API + delete-endpoint gotcha (ELITEA-2098, confirmed live)
- **Folder create**: `POST /elitea_core/folder/prompt_lib/{project_id}`
  `{"name": "..."}` → 201, `{id, name, owner_id, position, meta}`. Despite
  `FolderCreate`'s OpenAPI schema listing `owner_id` as required, the
  server fills it from auth — same pattern as `ConversationCreate`'s
  `author_id`.
- **Move a conversation into a folder**: `PUT /elitea_core/conversation/
  prompt_lib/{project_id}/{conversation_id}` `{"folder_id": N}` → 200,
  instant, no propagation delay. No `automation/api/client.py` helper
  exists for either call yet (`ConversationAPI` has no folder methods) —
  implementer may want to add one rather than hand-rolling `requests`
  calls.
- **Conversation DELETE needs the SINGULAR endpoint** — confirmed live
  this session: `DELETE /elitea_core/conversations/prompt_lib/{pid}/{id}`
  (plural) returns **404**; `DELETE /elitea_core/conversation/prompt_lib/
  {pid}/{id}` (singular) returns 204. `ConversationAPI.delete_conversation()`'s
  own docstring already documents this correctly — but
  `automation/CLAUDE.md`'s "API Quirks" table claims the OPPOSITE
  ("Exception: Conversation delete uses plural path"), which is stale/wrong.
  Flagged as a doc-accuracy note for the lead, not a test defect (nothing
  in the test suite itself relies on the wrong claim).
- **`is_conversation_active()` / `data-active` correctly moves between
  rows on same-folder navigation** — live-confirmed: clicking a second
  conversation inside the same expanded folder flips `data-active` from
  the first item to the second in the same accessibility-snapshot read,
  no reload/flicker needed.

## Conversation deletion — folder-preserved, last-conversation empty state,
## modal styling/dismissal, and a project-400 sandbox discovery (ELITEA-2115/2116/2117/2456)

- **Project 400 ("UI Testing") is a genuinely empty sandbox project — use it
  for any case needing a clean/isolated conversation-count precondition.**
  Confirmed live via `ConversationAPI(browser_cookies=[], project_id="400")
  .list_conversations()` → `total: 0`, both before and after this session
  (temp data cleaned up). Distinct from the shared Team project (471, "Review
  attached documents" id 420 — repeatedly reused/restored by other analyses,
  documented above) and the default Private project (399, which already
  carries 4 non-`autotest_`-named manual/leftover conversations — origin
  unconfirmed, NOT safe to assume disposable). Bearer-token auth
  (`ConversationAPI(browser_cookies=[], project_id="400")`, no cookies) works
  fine against it — same auth mechanism already documented for the
  project-mismatch trap above, just pass `project_id` explicitly. **Any case
  needing "exactly N conversations" / "no folders" / a clean starting count
  should use project 400**, not attempt to temporarily empty a shared
  project.
- **Deleting a conversation INSIDE A FOLDER never touches the folder itself**
  (no `DELETE .../folder/...` call fires) — live-confirmed (ELITEA-2115). The
  folder renders its existing `chat-folder-empty-state` testid
  (`get_folder_empty_state_text()`) with live text **"No conversations
  added"** once its last conversation is gone. Folders on project 400
  rendered expanded-by-default with a single seeded conversation — don't
  assume this generally; call `expand_folder()` defensively for
  multi-folder scenarios.
- **A folder-scoped conversation's context menu has "Pin on top" DISABLED**
  (already documented above under § Pin conversation — reconfirmed here for
  the delete-specific menu enumeration: live 8-item set for a folder-scoped
  conversation on project 400 is Rename, Move to, Playback, Duplicate, Make
  public, Share, Pin on top (disabled), Delete).
- **`findNextConversation()` (`useDeleteConversation.js`) is scope-aware, not
  project-wide** — for an UNGROUPED (non-folder) conversation being deleted,
  it searches ONLY the project's other ungrouped conversations (the
  `conversations` Redux slice), never folder-nested ones. This means the
  "last remaining conversation" welcome-state branch triggers whenever zero
  OTHER ungrouped conversations exist, even if folders with conversations are
  still present elsewhere in the sidebar — worth knowing if a future case
  wants a narrower/faster way to reach the empty-state branch without a
  genuinely empty project (not exploited by ELITEA-2117's own AFS, which uses
  the honestly-simpler fully-empty-project route via project 400, but
  documented here for the next analyst who needs this branch).
- **CONFIRMED DEFECT, filed EliteaAI/elitea-testing-public#1523**: deleting
  the LAST remaining conversation in a project (the `dummyConversation`
  fallback branch of `onDeleteConversation`) correctly updates ALL visible
  UI state (empty sidebar, welcome greeting `chat-new-conversation-greeting`,
  active input) but **never updates the browser URL** — `page.url` stays at
  `/chat/{deleted_id}?name={deleted_name}` until a hard reload (which then
  correctly shows a "Conversation not found" dialog and resets cleanly). Root
  cause: the `else` branch in `onDeleteConversation` calls only
  `setActiveConversation(dummyConversation)`, never a router/`navigate()`
  call — contrast with the "next conversation exists" branch, which DOES
  correctly call `onSelectConversation()` (and does update the URL,
  confirmed working by the already-merged ELITEA-2114 test). Two delayed
  (~1.5s) console 400s also fire from stale background refetches against the
  dead id (`GET .../conversation/prompt_lib/{project}/{id}?...` and
  `GET .../select_conversation/prompt_lib/{project}/{id}`) — expected/
  consistent with the stale-URL root cause, not a second defect.
- **The sidebar's `"Still no conversations created."` empty-state text ONLY
  appears after a page reload/fresh mount** — within the SAME SPA session
  right after deleting the last conversation, the sidebar list region simply
  renders with zero items and no date-group headings (no explicit
  "empty" text node at all). Don't assert the reload-only text string as a
  same-session observable; assert item-count == 0 + no group headers instead
  (exactly what ELITEA-2117's AFS step 6 does).
- **Delete-confirmation dialog button styling, live-confirmed via
  `getComputedStyle`** (ELITEA-2116): Cancel button
  (`delete-confirm-cancel-button`) carries MUI classes
  `MuiButton-eliteaSecondary`/`MuiButton-colorSecondary`, computed
  `background-color: rgba(255,255,255,0.1)`. Delete button
  (`delete-confirm-button`) carries `MuiButton-eliteaAlarm`/
  `MuiButton-colorAlarm`, computed `background-color: rgb(215,22,22)` (a
  genuine red) — both buttons' semantic-role styling (secondary vs.
  destructive) is real and computed-style-assertable, not just class-name
  string matching.
- **Delete-confirmation dialog dismisses correctly via BOTH Escape and an
  outside/backdrop click** — live-confirmed (ELITEA-2116), neither dismissal
  fires the underlying `DELETE` network call, and the conversation remains
  untouched in the sidebar either way.
- **Outside-click technique gotcha**: MUI's `Dialog` renders a
  `MuiDialog-container` that visually spans the whole viewport and
  intercepts direct-locator clicks anywhere in it (Playwright reports
  `<div class="MuiDialog-container...">...intercepts pointer events` if you
  try `.click()` on `.MuiBackdrop-root` directly — the container paints
  above the backdrop). The correct honest technique is a **coordinate-based**
  `page.mouse.click(x, y)` at a point provably outside the dialog Paper's
  bounding box (e.g. viewport top-left corner `(5, 5)`) — a real Playwright
  mouse event, not a `page.evaluate()`/JS-dispatched substitution, and it
  correctly lands on `MuiDialog-container` (which still wraps/triggers MUI's
  `onClose(reason: 'backdropClick')`).

## Search gap-family (ELITEA-2163/2164/2165/2463) — extends the ELITEA-2162/2464
## covering spec, no new testids' worth of blockers except two
- **No-results state has a live defect**: typing a query that matches nothing
  on a project with OTHER, non-matching data (e.g. project 399 "Private", 45+
  pre-existing folders/conversations) shows BOTH `Conversations.jsx`'s correct
  "No conversations found / Try adjusting your search terms" AND
  `GroupedConversations.jsx`'s "Still no conversations created." — the latter
  is only supposed to render when the project has genuinely never had any
  conversation (`totalConversationsAmount === 0`), but that prop is fed the
  search-**filtered** total (0 on no-match), not the true unfiltered total.
  Filed: EliteaAI/elitea-testing-public#1525. Not blocking (case's own pass
  criteria is satisfied by the correct message also appearing), asserted as
  an `expect.soft()` regression guard, not a hard fail.
- **Two new testids added this pass** (commit `EliteaAI/EliteaUI@d5e0ba63` on
  `automation/testids`, both zero-functional-impact attribute-only adds):
  `chat-search-no-results-message` (the Box wrapping "No conversations
  found" / "Try adjusting your search terms" in `Conversations.jsx`) and
  `chat-conversations-empty-state-message` (the "Still no conversations
  created." Typography in `GroupedConversations.jsx`).
- **The X/clear icon (`conversation-search-clear-button`) fully UNMOUNTS the
  search input** on click (confirmed live via accessibility-tree snapshot —
  the input element disappears from the DOM entirely, not merely emptied),
  restoring the exact same folders+date-grouped default view and re-showing
  the magnifier button (`conversation-search-button`). Not a "clear text,
  keep field open" behavior — a full close.
- **Deleting characters re-triggers the SAME debounced filter mechanism as
  typing** — live-confirmed 1→5 match growth going from a 30-char exact name
  down to a 7-char shared prefix (`"Automat"`), matching BOTH previously
  seeded `AutomationSearch*` conversations AND 3 pre-existing
  `AutomationRenameTest` FOLDERS (which render as **disabled** buttons when
  matched by a search query — folders are shown but not clickable in search
  results, confirmed live). Clearing the field to empty (`Meta+a` +
  `Backspace` — plain `Control+a` does NOT select-all in Chromium on macOS,
  same gotcha `.claude/rules/mui-patterns.md` already documents for other
  MUI inputs) restores the exact same unfiltered default view — NOT a
  distinct "empty search" placeholder state (`isSearchMode =
  !!debouncedSearchQuery.trim()` in `Conversations.jsx` — trim()'d-empty
  means search mode itself turns off, same code path as never having opened
  search). **Correction (ELITEA-2165 implementation round 1):** this specific
  clear-to-empty transition does NOT reliably produce a NEW `folder/
  prompt_lib` network response — it's the same cache key the page loaded
  with, so it can be served from the query-client cache with zero round-trip
  (a `page.expect_response()` wait on this step times out; live-confirmed via
  a failing first attempt). Wait on the resulting UI state (polling
  `is_conversation_in_group()`), not a network event, for this ONE
  transition specifically — every OTHER query change in this family (narrow,
  broad, exact) does fire a fresh response and remains request-waitable.
- **Search results genuinely separate pinned from date-grouped tiers, live-
  confirmed via a real pin action**: pinning a conversation (`+` context menu
  → "Pin on top", `chat-conversation-menu-pin-menuitem`) then searching for a
  query that matches it renders the pinned item OUTSIDE any
  `CONVERSATION_GROUP_HEADER` container (same DOM position as
  `PinnedConversations`' non-search rendering — right after the folders
  list, before the date-grouped section), while a separately-matching
  non-pinned conversation stays correctly scoped inside its date group
  (e.g. "Today"). Root cause (source-confirmed,
  `useQueryFoldersList.hooks.js`): `pinned`/`folders`/date-grouped
  conversations all come from the SAME `folder/prompt_lib` call, with the
  SAME `query` param filtering all three tiers together — not a client-side
  post-filter on a subset. `ChatPage.is_conversation_pinned()` (pre-existing,
  `data-pinned` attribute) is the right check — it uses the page-wide
  `CONVERSATION_ITEM` testid, which resolves regardless of the item's
  pinned/grouped/foldered DOM position.
- **Project 399 ("Private", the default/settings project) is NOT a clean
  sandbox** — confirmed this pass to carry 45+ pre-existing folders (many
  named "ABC", "New folder", "New folder6", "ELITEA2459RenameTest",
  "AutomationRenameTest" ×3) plus other conversations, on top of the 4
  non-`autotest_`-named ones already documented above. This is actually
  USEFUL for search-family cases specifically (a genuine "no results on a
  non-empty project" precondition needs exactly this — see project-400's
  own caveat above, "do NOT use it for a no-results-search case, it would
  prove the wrong thing"), but any case asserting an exact conversation/
  folder COUNT on project 399 must still seed+scope its own data, never
  count on the pre-existing set staying stable.

## Toolkit-from-chat canvas — ELITEA-2080-2083 (2026-08-17)

The one remaining unexplored sibling of the "Create New X" canvas family.
`ToolkitEditor.jsx` wraps the same `BaseEditor`/`EditorHeader` chrome used
by Agent/Pipeline/MCP canvases.

- **Entry point** (`toolkits-menuitem` on-main ✓, `toolkits-create-new-button`
  on-main ✓): same `PlusChatButton.jsx`/`PlusChatSubmenu.jsx` template pattern
  as Pipeline and MCP canvases — `sectionKey="toolkits"`, static config line 47.
- **Type picker** confirms live: GitLab type card resolves to
  `toolkit-type-card-gitlab` (confirmed from the MCP analysis pattern —
  `toolkit-type-card-{type}` naming). Category "Code Repositories" rendered
  first in the picker. Selecting a type opens the configuration canvas.
- **Canvas chrome testids — three were MISSING, added in this session:**
  `ToolkitEditor.jsx` previously passed `isMcpTestIdScope ? 'mcp-canvas-*' : undefined`
  for all three chrome testids — the `undefined` side left the non-MCP Toolkit
  canvas completely testid-free on chrome elements. Added in commit
  EliteaAI/EliteaUI@441333e1 on `automation/testids` (2026-08-17, ELITEA-2083):
  - `toolkit-canvas-title` (title heading, line 250)
  - `toolkit-canvas-close-button` (close button, line 251)
  - `toolkit-canvas-create-button` (Create button via `CreateToolkitButton.jsx`, line 259)
  These follow the same `isMcpTestIdScope ? 'mcp-canvas-*' : 'toolkit-canvas-*'`
  conditional pattern. Human promotes to `main` from `automation/testids`.
- **Canvas title observable (step 1 of ELITEA-2083)**: the heading level 6
  (`data-testid="toolkit-canvas-title"`) reflects the toolkit name in the form
  — confirmed live in exploration session snapshot (text "test1" appeared in
  heading immediately when name was typed). The heading persists after save.
- **Close button (step 2 of ELITEA-2083)**: with a SAVED toolkit (no unsaved
  changes), clicking `toolkit-canvas-close-button` closes the canvas
  DIRECTLY without a confirmation dialog. The discard confirmation dialog
  ("Are you sure you want to discard changes?") only appears when there are
  unsaved changes — confirmed live by observing the dialog when discarding
  an unsaved form.
- **PARTICIPANTS panel (steps 3-5 of ELITEA-2083)**: all handles confirmed
  via source on `origin/main` (dynamic templates):
  - `chat-participants-badge-toolkits` — `CollapsedPerticapantsList.jsx` line 223
    template `chat-participants-badge-${entity.section}` where `section='toolkits'`
    (line 55). On-main ✓.
  - `chat-participants-badge-icon-toolkits` — same file line 235 template
    `chat-participants-badge-icon-${entity.section}`. On-main ✓.
  - These work identically to the already-live-confirmed MCP participant handles
    (`chat-participants-badge-mcp` / `chat-participants-badge-icon-mcp`).
- **Form fields inside the canvas**: same `ToolkitForm` / `ToolkitTypeSelector`
  as standalone toolkit creation — `toolkit-form-name-input` and type-specific
  fields. For GitHub toolkit: credential combobox (no consistent testid found —
  MUI select, use label-based disambiguation); repository field via
  `toolkit-field-repository-input` (confirmed from live DOM, `data-testid`
  present on the input). `github_credential` fixture provides the credential
  for automated tests.
- **Pre-existing console noise**: issue #656 (CategorySection unique-key-prop
  warning) fires on every type-picker render. Filter it alongside other
  known-noise patterns.

### ELITEA-2081 — Toolkit/MCP canvas Discard button + confirm modal added (2026-08-20, combined analyst+implementer)

Extends the section above with the Discard side of the Toolkit-from-chat
canvas flow — same gap ELITEA-2076 found and fixed for the sibling Pipeline
canvas (`test-specs/chat-interface/l2_pipeline-discard-changes-clears-canvas_ELITEA-2076.md`).
`ToolkitEditor.jsx` already had a working `handleDiscard` wired to
`BaseEditor`'s `onDiscard` (both create-mode and edit-mode branches), but
never supplied `discardButtonTestId`/`discardModalTestId`/
`discardConfirmButtonTestId` at its `<BaseEditor>` call site — those three
props were already threaded end-to-end through `BaseEditor.jsx` →
`EditorHeader.jsx` → `Button.DiscardButton` by ELITEA-2076's fix, so only
the call-site wiring was missing.

- **Three testids added**, `EliteaAI/EliteaUI@bc08563f` on `automation/testids`
  (awaiting human promotion to `main`): `toolkit-canvas-discard-button`,
  `toolkit-canvas-discard-confirm-modal`, `toolkit-canvas-discard-confirm-button`.
  Same `isMcpTestIdScope ? 'mcp-canvas-discard-*' : 'toolkit-canvas-discard-*'`
  conditional pattern as the pre-existing title/close/create testids — the
  `mcp-canvas-discard-*` mirrors did not exist anywhere before this session.
- **Discard is gated on Formik's `dirty` state** (`disabled={!isFormDirty && !isYamlCodeDirty}`
  in `EditorHeader.jsx`) — for the Toolkit canvas, `isYamlCodeDirty` is always
  false (a Pipeline-only concept from `useIsPipelineYamlCodeDirty`), so typing
  into the Name field alone is sufficient to enable Discard. **No type-complete
  form is needed** — selecting a type + typing a Name dirties the form; no
  credential, no repository field, no `github_credential` fixture dependency
  (unlike ELITEA-2083's create-then-close flow, which needs a fully valid,
  saveable form).
- **Create-mode Discard reverts to the type-picker, not to a blank form** —
  confirmed live: `handleDiscard()`'s `isCreating` branch does
  `setEditToolDetail(null); setFormikInitialValues({ type: '' })`, so
  confirming Discard un-selects the type entirely — the canvas title reverts
  from `"New GitHub Toolkit"` back to `"New Toolkit"` and a
  `toolkit-type-card-*` grid reappears, all while the canvas panel itself
  stays mounted/open. This is the live-confirmed shape of "canvas cleared"
  for THIS canvas — distinct from the Pipeline canvas's Discard (ELITEA-2076),
  which only resets the Name/Description fields back to `""` on the SAME
  form, never un-selecting anything (Pipeline has no type-picker step).
- **Post-discard, the X-close button closes DIRECTLY, no confirmation** —
  confirming Discard resets `BaseEditor`'s `isDirty` to `false`
  (`onDiscard?.(); setIsDirty?.(false);`), so `handleCancel`'s
  `isDirty && !isPublic` guard is false on the very next X click. Same
  "no unsaved changes → direct close" rule already documented above for the
  SAVED-toolkit case — now confirmed to extend to the discarded/cleared case
  too.
- **No product defect found** — this flow behaves exactly as ELITEA-2080/2081's
  case text describes; zero clarifications needed.
- AFS: `test-specs/chat-interface/l2_create-toolkit-from-conversation-close-canvas-without-saving_ELITEA-2081.md`.

## ELITEA-2462 — already-covered by ELITEA-2152 (word-for-word duplicate case text)

- w09 analysis (2026-08-15): ELITEA-2462 ("Chat – Pin a folder and verify it appears at the
  top of the left panel") is a verbatim re-authoring of ELITEA-2152's case text under a new
  TMS id — same title, same objective, same 6-step sequence in the same order. Covering test
  `test_pin_folder.py::TestPinFolderViaPinOnTop::test_pin_folder_via_pin_on_top` (merged to
  `origin/automation/base`, PR #1552) asserts every one of ELITEA-2462's 6 steps 1:1.
  Live-reconfirmed green this session (18.40s). AFS:
  `lcovered_pin-a-folder-and-verify-it-appears-at-top-of-left-panel_ELITEA-2462.md`. No new
  test written — `already-covered`, not `extend-existing`.

## ELITEA-2152/2153 — Pin/Unpin a FOLDER's position/icon/conversations
## (folder-pin surface's OWN subject, not incidental rename/ordering setup)

- **First case whose OWN subject is the folder-pin action's position/visibility
  effects** — ELITEA-2130 pins a folder only as setup for a RENAME test (never
  checks position or conversations); ELITEA-2151 pins a folder only as setup
  for a 4-tier ORDERING check against conversation rows (never captures a
  folder's own before/after position or touches its conversations). Reuses
  `pin_folder_via_menu()`, `is_folder_pinned()`, `get_folder_item()`,
  `is_conversation_in_folder()` (all ELITEA-2121/2130) verbatim, plus ONE
  additive change: `expand_folder(folder_id, timeout, force: bool = False)`
  gained an optional `force` param (default `False`, zero behavior change for
  ~15 existing callers) — see the expand-state bullet below for why.
- **A folder's unpinned-list position is DETERMINISTIC and returns to its
  pre-pin Y coordinate (within sub-pixel tolerance) on unpin** — live-confirmed
  across a full pin→unpin round-trip on the SAME folder (id `1091`,
  `w08_2152target`): baseline Y=138 (below unpinned sibling `1092` at Y=97) →
  pin (`PATCH → 200`) → Y=56 (now ABOVE the sibling, whose own Y shifted to 178
  as the list reflowed) → unpin (`PATCH → 200`, SAME endpoint/method, SAME
  `chat-folder-menu-pin-menuitem` toggle) → Y returns to ~138, sibling back to
  ~97 — the identical pre-pin layout, not merely "some unpinned position".
  `getBoundingClientRect()` reads of an UNMOVED element can differ by a
  fraction of a pixel between two calls (observed: 138.71875 vs 138 for the
  exact same row) — assert with a ~2px tolerance, not `==`, or the test flakes
  on zero real position change. This is a stronger, more diagnostic assertion
  than a bare `data-pinned` flag check and is what ELITEA-2152/2153's AFS files
  use for "folder moved from/returns to its original position".
- **A folder created AFTER another one renders ABOVE it** in the default
  `sort_by=updated_at&sort_order=desc&grouped=true` folder-list query — i.e.
  most-recently-created/touched first. Useful for any case needing a
  deterministic before-pin ordering baseline between two fresh sibling
  folders without depending on ambient DEV-project data.
- **CORRECTED finding — pinning (and unpinning) a folder DOES reset its
  expand state; a bare live MCP read that says otherwise is racing the
  settling re-render, not observing final state.** The first pass through
  this exploration read `data-expanded="true"` immediately after a raw click
  on the pin menu item and concluded expand state survives pinning — WRONG.
  The implementer's pytest run, using a **web-first, polling assertion**
  (`expect(locator).to_have_attribute(..., timeout=...)`) instead of a single
  synchronous read, caught the SETTLED value: `data-expanded="false"` after
  BOTH the pin and the unpin action, even though the folder was expanded
  immediately beforehand in both cases. Root cause (structural, not a flake):
  moving a folder's row between the pinned and unpinned list partitions is a
  genuine remount, not an in-place reorder, so any local component state
  (expand/collapse) resets to its default. Conversations are NOT lost —
  re-expanding after the action (`expand_folder(..., force=True)` — the
  pinned-folder disabled-ancestor gotcha applies to a plain click on the WHOLE
  row here, not only the dot-menu button) shows them intact. **Methodological
  lesson for future exploration on this surface**: a single MCP `evaluate()`
  read immediately after a click proves only "not yet false" — it is not
  evidence of the settled state. Reach for a genuinely time-separated re-check
  (several tool round-trips later, or better, drive the actual pytest
  assertion) before writing a persistence claim into an AFS. Not filed as a
  product defect — the case's own wording ("shows its conversations WHEN
  expanded") doesn't demand automatic persistence, and collapsing on a
  structural list move is a defensible, common UI pattern.
- **"Pin icon visible/removed" is asserted via `data-pinned`, per policy, not
  a raw icon locator** — same equivalence ELITEA-2121/2130's AFS already
  established (`isPinned && <PinIcon>` in `FolderAccordion.jsx`'s header has
  no testid); re-confirmed live this session, not re-derived from scratch.
- **Exploration-only console-warning artifact, NOT a product defect** (same
  class already documented under ELITEA-2121/2130's "disabled-ancestor"
  entry): driving the dot-menu button via a raw DOM `element.click()`
  (`browser_evaluate`, since Playwright MCP's `browser_click` has no `force`
  option) on a PINNED folder produced 4 transient React console warnings
  (`Invalid prop 'expanded'/'in' of type object supplied to
  ForwardRef(Accordion2)/(Collapse2)/Transition2`, `MUI: anchorEl prop
  invalid`) — an artifact of bypassing React's synthetic-event path, not
  reproduced by a real Playwright `.click(force=True)` (ELITEA-2130's own
  test already runs that exact click pattern with 0 console errors observed).
  Do not re-investigate this as a product bug if seen again during MCP-only
  exploration on this surface; it does not occur under real pytest runs.
- **Exploration folders left live, undeleted** (`w08_2152target` id
  `1091`, `w08_2152sibling` id `1092`) — same accepted precedent as
  ELITEA-2121/2130/2151 (folder-delete's UI testid is dead, tracked in
  `#1309`; MCP-`fetch()` to the same-origin API also fails — confirmed again
  this session, `TypeError: Failed to fetch` on a relative `/api/v2/...` POST
  even though the identical request made via a real UI click succeeds, e.g.
  request `#1917` `POST .../folder/prompt_lib/399 => 201`; not worth chasing
  further given the already-extensive documented pollution). Both AFS files'
  own implementations create/delete their OWN fixtures via
  `conversation_api` (cookie-authenticated, not `page.evaluate`-`fetch()`),
  so this does not affect the shipped tests' own cleanup.

## ELITEA-2155/2156 — Pin/Unpin an EMPTY folder retains its empty state,
## BOTH extend-existing onto `test_pin_folder.py` (ELITEA-2152/2153's
## classes), ZERO defects, ZERO new handles

- **Distinguishing axis vs ELITEA-2152/2153/2154 (which all seed a folder
  WITH ≥1 conversation): this pair seeds a folder with ZERO conversations
  and proves the pin/unpin mechanism doesn't special-case (or break on) the
  empty-state rendering path across the already-documented pin/unpin-
  triggered remount** (see the ELITEA-2152/2153 section above — pinning
  moves a folder's row between list partitions, a genuine remount that
  resets local expand state). Reused `get_folder_empty_state_text()`
  verbatim — pre-existing on `ChatPage` since ELITEA-2148, first REUSED
  (not just introduced) by this pair. No new page-object work at all: both
  new test methods reuse every handle ELITEA-2148/2152/2153 already
  established, with zero additions.
- **Confirmed live, both directions, via a real `pytest` run (this WAS the
  exploration — combined analyst+implementer session, executed once,
  green)**: an empty folder's `chat-folder-empty-state` text ("No
  conversations added") is byte-identical before pinning, after pinning
  (re-expanded with `force=True`), and — for the unpin case — after
  unpinning too. No blank body, no leftover/stale content, no console
  error, on either transition. Zero product defects found.
- **Landed as two new test methods in `test_pin_folder.py`** (not a new
  file, not a family AFS) — `test_pin_empty_folder_retains_empty_state` in
  `TestPinFolderViaPinOnTop` (ELITEA-2155), `test_unpin_empty_folder_retains_empty_state`
  in `TestUnpinFolderViaContextMenu` (ELITEA-2156) — mirroring how
  ELITEA-2154 extended the pin-side class. Each `extend-existing` AFS
  targets the SAME-batch-trunk spec (merged-target rule: same-batch trunk is
  a valid extend-existing target while `test_pin_folder.py` itself is not
  yet on `origin/automation/base`).
- **Cleanup**: both test methods' own `folder_empty` fixture is created and
  deleted via `conversation_api.create_folder()`/`delete_folder()` — zero
  net pollution added by this pair (distinct from the ELITEA-2152/2153
  exploration folders left live above, which predate this pair's own
  session and are unrelated to it).

**Resolved/added during ELITEA-2155/2156 implementation (implementer,
2026-08-15):** nothing new to resolve — both tests ran green on the first
attempt, reusing 100% pre-existing handles/methods; no AFS amendment was
needed.

## ELITEA-2157/2158 — Pin on top DISABLED for an in-folder conversation,
## ENABLED after "Move to" > "Back to the list"; family AFS, ZERO new
## testids, ZERO defects
- **Live-reconfirms, from BOTH sides in one session, the already-documented
  `disabled: !isPinned && !!conversation.folder_id` rule** (`ConversationItem.jsx`
  line 260) — first documented in `_surface.md` § ELITEA-2136/2138/2139/2140/2141
  as a flagged-but-unencoded gap ("None of ELITEA-2136/2138/2139/2140/2141's own
  case steps require asserting this full [in-folder menu item] set, so no test
  in this pass encodes it"). This pair closes that gap.
- **Reused an ambient leftover conversation for the live confirmation pass**
  (`W08_2152_conv seed message`, id `8514`, inside folder `w08_2152target`/id
  `1091`, both leftover fixtures from an earlier wave) rather than seeding new
  data purely to eyeball the mechanism — same "leftover exploration data is
  fair game for a quick live check, the test itself still seeds its own"
  pattern already established for the pinned-folder ancestor gotcha (§
  ELITEA-2146/2147/2148). The actual implemented test seeds its own
  `folder`/`conv_target` via `conversation_api`, per usual.
- **Testid renders unconditionally regardless of disabled state** —
  source-confirmed: `DotMenu.jsx`'s `BasicMenuItem` sets
  `data-testid={testId ? \`${testId}-menuitem\` : undefined}` unconditionally;
  `disabled` is a separate MUI `MenuItem` prop rendered as `aria-disabled`.
  So `chat-conversation-menu-pin-menuitem` is present-and-selectable either
  way — the DISABLED check is a plain attribute read on the existing
  testid-selected locator, no new locator needed.
- **A forced click on the disabled item has no network side effect** —
  live-confirmed: MUI's `ButtonBase` guards its own click handler internally
  when `disabled`, so even `force=True` (which bypasses Playwright's
  actionability check, not MUI's own guard) never fires the
  `POST .../pin/prompt_lib/...` mutation. This is EliteaUI-independent MUI
  behavior, not app-specific logic.
- **In-folder context menu is a 6-item set** (`Rename, Move to, Playback,
  Duplicate, Pin on top [disabled], Delete`), one more than the flat-list
  5-item set ELITEA-2114/2149 document (`Duplicate` present, absent
  outside a folder) — reconfirmed live this pass, matches the prior flag.
- **Zero new testids, zero new page-object methods** — every handle and
  every interaction/verification method needed already existed
  (`expand_folder`, `is_conversation_in_folder`, `open_conversation_context_menu`,
  `get_conversation_menu_item`, `open_move_to_submenu`,
  `select_move_to_back_to_list`, `is_conversation_in_group`,
  `is_conversation_pinned`, `get_pin_icon`, `click_conversation_menu_item`).
- **Zero product defects found.** Both cases' mechanisms work exactly as
  cased, end to end, live-confirmed (0 console errors across the repro).
- **Landed as ONE new test method** (not two) in
  `test_pin_conversation.py` — `test_pin_disabled_in_folder_then_moved_and_pinned`
  in a new class `TestPinDisabledInFolderThenMovedAndPinned`, tagged with
  both TMS IDs via two stacked `@allure.issue` decorators (same pattern
  ELITEA-2139/2140's family test already uses) — ELITEA-2158's own
  precondition (step 1) IS ELITEA-2157's entire subject, so one continuous
  live flow on one seeded conversation honestly satisfies both cases' full
  Pass/Fail criteria without re-deriving a second "conversation inside a
  folder" fixture.

**Resolved/added during ELITEA-2157/2158 implementation (implementer,
2026-08-15):**
- **The "Duplicate" context-menu item had NO `key` (and therefore no
  testid) at all** — `DotMenu.jsx` maps `testId: item.key` for TOP-level
  menu items (not just submenu items — confirmed by reading the same file
  the earlier ELITEA-2135 pass read for submenu items), and the
  `ConversationItem.jsx` object literal for "Duplicate" was the ONLY item
  in the 7-item array missing a `key` (every sibling item — Rename, Move
  to, Playback, Make public, Share, Pin, Delete — has one). The item
  renders and works fine (confirmed via ARIA snapshot: `menuitem
  "Duplicate"`), it's simply invisible to any `[data-testid^="chat-
  conversation-menu-"]`-prefix-based count. Added `key:
  'chat-conversation-menu-duplicate'` (one line, zero functional impact —
  no new DOM node/hook/render-prop change) on `automation/testids`,
  EliteaAI/EliteaUI commit `a53b9d4b`. Naming matches the existing
  `chat-conversation-menu-{action}` family exactly.
- **A forced click on a DISABLED MUI `MenuItem` leaves the menu OPEN** —
  MUI's `ButtonBase` guards its own click handler when `disabled`, so the
  menu's close-on-select trigger (which normally fires from the item's
  own `onClick`) never runs either. Re-hovering the SAME conversation
  immediately afterward (e.g. to open "Move to") hits the still-open
  menu's invisible `MuiBackdrop` and times out ("subtree intercepts
  pointer events") — this is NOT the same as the already-documented #1117
  "Move to doesn't open on one click" defect; it's a distinct
  after-a-disabled-click state that no prior test in this suite produced
  (every other pin/move-to test only ever clicks ENABLED items, which
  close the menu normally). Fix: explicit `page.keyboard.press("Escape")`
  after a deliberately-disabled-item click, then wait for the shared
  `FOLDER_CONTEXT_MENU_POPOVER` (`[data-testid="conversation-menu-menu"]`
  — pre-existing constant, ELITEA-2146/2147 pass, first live caller here)
  to become hidden before the next hover. Any FUTURE test that clicks a
  DISABLED context-menu item and then needs to interact with the same
  conversation again should apply the same explicit-close pattern.

**Resolved/added during ELITEA-2169 combined analyst+implementer pass (batch
chat-remaining-w10, 2026-08-15):** ELITEA-2169 ("Add Users as Conversation
Participants") is a strict subset of ELITEA-2167's own 10-step "Add users"
modal flow (already merged, `test_invite_users_add_persists_cancel_and_close_discard`)
— classified `already-covered`, no new spec written. While live-reconfirming the
covering test 3× back-to-back this session:
- **Run 1** passed every step overlapping with ELITEA-2169 (menu → modal →
  2 chips → Add → badge/popover show both) and only failed at the test's own
  FINAL, unrelated side-channel console check, on a genuinely NEW React
  `setState`-in-render warning (`UsersParticipantDropdown/index.jsx:30` setting
  state on `CollapsedPerticapantsList` mid-render of the Participants panel) —
  dedup-checked (distinct from #719's `sx`-on-svg and #625's Support-Assistant
  setState warning) and filed as MINOR issue #1556.
- **Runs 2–3** failed at the covering test's OWN Step 1 (stale conversation
  reused instead of a genuinely blank one) — this is the already-tracked #1082
  flake, reproducing here because back-to-back re-runs in one session leave no
  cleanup pause between them (self-inflicted by the re-run methodology, not a
  fresh-invocation symptom). Any future session re-running this covering test
  repeatedly for reconfirmation should expect this and treat a Step-1 failure
  on re-run N>1 as #1082 first, not a new regression, before investigating
  further.

## ELITEA-2173/2174 — Users-dropdown MENTION-BY-NAME-CLICK, NEW surface
## distinct from ELITEA-2168's composer-typed-`"@"` path, family AFS, both
## `ready-for-automation`, ZERO new testids, one CLARIFICATION filed (#1558)
- **Genuinely different mechanism from ELITEA-2168's own mention steps 7/12,
  confirmed by reading source BEFORE testing live** (interaction-discovery
  ladder step 6). ELITEA-2168 mentions a user via the COMPOSER'S typed-`"@"`
  popper (`UserMentionList.jsx`/`onSelectUserMention`, `ChatBox.jsx`). This
  family clicks a participant's NAME ROW inside the Users PARTICIPANTS
  DROPDOWN itself (`UserMenu.jsx`'s row `onClick` → `handleSelectUser` →
  ELITEA-2168's own `onSelectParticipant` wrapper → `NewChat.jsx`'s
  `onSelectThisParticipant` → `onSelectParticipant(foundParticipant, false)`,
  `NewChat.jsx:575-594`) — a call chain that (mis-)reads at first glance like
  `shouldMentionUser=false` should SKIP the mention insertion (the parameter's
  literal name), but the row branch (`participant?.entity_name ===
  ChatParticipantType.Users`) does `shouldMentionUser && mentionTarget
  ?.mentionUser?.(...)` — false means the call is skipped ONLY when true is
  needed elsewhere; **live confirmation was required and performed** (source
  reading alone would have been ambiguous/wrong here — this is exactly why the
  ladder's step 6 is "read source" not "trust source", the code path has a
  second branch (`else if (participant === 'All users')`) with the same
  `shouldMentionUser` gate that #1119 already proved broken for the FOOTER
  item specifically). Live: clicking a row DOES insert `"@Name "` into the
  composer correctly, for both a single mention (ELITEA-2173) and two
  sequential mentions that correctly APPEND rather than replace (ELITEA-2174:
  `"@Hrach Sargsyan @Levon Dadayan"` after two dropdown-reopen-click cycles).
- **`fill()` silently destroys an in-progress mention** — appending `" hi"` to
  a composer already containing `"@Hrach Sargsyan"` via Playwright's `.fill()`
  REPLACES the whole value (mention lost entirely), not appends. Fix:
  `click()` + `press("End")` + `press_sequentially(" hi")`. Not previously
  documented in this digest because ELITEA-2168's own mention flow never hit
  this exact failure mode via its own insertion mechanism.
- **CLARIFICATION filed, [#1558](https://github.com/EliteaAI/elitea-testing-public/issues/1558)**:
  ELITEA-2173's case text (step 3) expects the inserted `@mention` to be
  "highlighted/formatted" — live product inserts plain, unstyled text (same as
  the composer's own typed-`@` mechanism, which is ALSO plain text per
  ELITEA-2168's AFS). Reverse-masking case-text drift, not a defect.
- **Zero new testids needed** — the whole family reuses
  `chat-participants-badge-button`, `chat-participant-row-user_{userId}_`
  (dynamic, PARTICIPANT_ROW template), `chat-message-input`, `chat-send-button`,
  `sidebar-create-button`, and the "Add users" modal handles, ALL already added
  by ELITEA-2167/2168 and confirmed present on both `main` and
  `automation/testids` (fresh `git fetch origin` this session). One new
  page-object method only: `mention_user_via_participants_dropdown(user_id)` —
  clicks the row directly (no hover needed; the row's hover-only delete icon is
  `visibility:hidden` by default and does not intercept a plain click at the
  row's center).
- **Zero product defects on either case's own subject.** Console/network
  side-channel checked throughout both live drives — only the two
  already-documented noise sources (project-471 `secrets` 403, #719's
  `sx`-on-svg warning) fired.
- Family AFS:
  `test-specs/chat-interface/l2_participants-dropdown-click-name-inserts-mention_ELITEA-2173.md`
  (same `afs_path` for both ELITEA-2173 and ELITEA-2174).

(supersedes nothing below — new section, other sections unchanged; previous
confirmer: qa-engineer analyst, ELITEA-2168, 2026-08-15)

## "Make public" + multi-user icon color (ELITEA-2188, qa-engineer analyst, 2026-08-15)

- **`conversation-multi-user-icon`'s color is the actual signal, `data-has-icon`
  is presence-only.** The wrapper (`ConversationItem.jsx:419`, existing testid)
  already carries `data-has-icon="true"/"false"` (ELITEA-2167), but that boolean
  is `true` for BOTH `private_with_users` AND `public` — the GREEN-vs-default
  distinction only lives in the child `<svg>`'s `fill` attribute
  (`theme.palette.status.published` = `#2BD48D` for public vs
  `theme.palette.icon.fill.default` = `#A9B7C1` for private-with-users;
  confirmed live by making a real conversation public and reading both colors
  via direct DOM query). **No `data-*` attribute yet distinguishes them** — a
  genuine testid gap (not a defect), specced in
  `l3_public-conversation-green-icon-in-chat-list_ELITEA-2188.md` § Concrete
  Handles gap #2 as a new `data-conversation-type`/`data-public` attribute on
  the SAME element (testid=identity, state=data-* ruling).
- **The sharp negative control for "private = not green" is a WITH-PARTICIPANTS
  private conversation, not a single-owner one.** A single-owner conversation
  renders NO icon at all (`data-has-icon="false"`) — that only proves
  presence/absence, not color. Use a private conversation that already has
  `data-has-icon="true"` (2+ participants) as the negative control so the test
  actually isolates "public vs private", matching what the case's own step 3
  wording asks for.
- **"Make public" confirmation dialog (`DotMenu.jsx`'s plain `Modal.BaseModal`
  branch, lines 535–545) has ZERO testids** — confirmed live via direct DOM
  read of the open dialog: no `data-testid` anywhere inside it. Root cause:
  `BaseModal.jsx` accepts `data-testid`/`titleTestId`/`closeButtonTestId`/
  `confirmButtonTestId`/`cancelButtonTestId` props, but `DotMenu.jsx`'s
  `Modal.BaseModal` call never forwards any of them from `activeDialog.props`
  (unlike the sibling `Modal.DeleteEntityModal` branch, which DOES carry
  testids — `delete-confirm-dialog`/`delete-confirm-button`/etc.). This is a
  SHARED gap: `BucketItem.jsx`'s "Delete bucket?" confirm (artifacts feature)
  uses the exact same `alertTitle`/`confirmText`/no-`entityName` shape and has
  the identical zero-testid problem — grepped, only these two call sites exist
  (`grep -rn "alertTitle:" ../EliteaUI/src`). Fix threads new testid props
  through `DotMenu.jsx`'s `activeDialog.props` the same way `alertTitle` etc.
  already are — same caller-supplied-prop precedent as the existing
  `submenuTestId` on the "Move to" item.
- **`PUT /api/v2/elitea_core/conversation/prompt_lib/{project}/{id}`** with
  `is_private: false` is the real endpoint behind "Make public" (`onEdit()` in
  `handleMakePublic`, `ConversationItem.jsx:161-163`) — confirmed live,
  `200 OK`. **No inverse UI action exists** — once public, `menuItems` filters
  the "Make public" item out entirely and no "Make private" item is ever
  added (`ConversationItem.jsx`'s `.filter(item => item.label !== 'Make
  public')` at the end of the `menuItems` `useMemo`). A conversation made
  public during live exploration CANNOT be reverted via the UI; a bare
  `fetch()` PUT from the browser console also failed (`Failed to fetch` — the
  real app call carries a bearer token not reachable from `localStorage`).
  **Analyst/implementer consequence: always create a FRESH conversation for
  this flow, never reuse an existing one you don't want permanently public.**
  (Conversation id `420`, "Review attached documents" on project 471, is now
  permanently public from this session's exploration — dev/local test data,
  low-risk, left as-is.)

## ELITEA-2189/2190/2191 (2026-08-15) — NO second user identity exists; every "non-owner" case on this surface is `blocked`

- **Root cause (checked live, not assumed):** `.env.test` has exactly one UI
  credential (`TEST_USER_EMAIL`/`TEST_USER_PASSWORD`), and localhost's
  `auth_state` bypasses login entirely via a single static `VITE_DEV_TOKEN`
  (`../EliteaUI/.env`, wired in `root.jsx`/`upload.js`/
  `useArtifactContentFetch.hooks.js`/`SupportAssistant.jsx` — always the SAME
  fixed identity, `author_id: 659` / "Test Bot"). There is no code path to
  authenticate as a second identity on localhost, and no second credential
  anywhere in the repo's test data.
- **Confirmed empty second-owner conversation set**: `GET
  /api/v2/elitea_core/folder/prompt_lib/471?sort_by=updated_at&sort_order=desc&grouped=true`
  returns every conversation in project 471 with `author_id: 659` (this same
  account) — no other-owned conversation, public or private, is currently
  reachable. Conversation `420` (see the entry above — made public by a prior
  analyst session) now 404s (`GET .../conversation/prompt_lib/471/420` →
  `400 Bad Request`, "Conversation not found") — it was likely cleaned up by
  a later run; do not assume it still exists as a fixture.
- **"Invite Users" does NOT give you a second identity to log in as.** It adds
  named users ("Hrach Sargsyan", "Levon Dadayan", "Mariam Hakobyan", …
  ELITEA-2167 precedent) as **participants** of a conversation `${TEST_USER}`
  still authors/owns. Those names come from a user-search endpoint with no
  corresponding password/token this suite holds — don't mistake "can add as
  participant" for "can view as".
- **Any future case shaped "user B cannot see/edit/delete user A's X" on this
  surface hits the identical wall.** Don't re-derive this from scratch —
  check [Question #1563](https://github.com/EliteaAI/elitea-testing-public/issues/1563)
  first (files ELITEA-2189/2190/2191 together as one shared-root-cause
  question, precedent-matched to #1314's analogous editor/viewer RBAC-role
  gap) for current status before spending a session re-confirming the same
  blocker.
- **Owner-side baseline handles ARE confirmed** (useful once unblocked):
  `chat-copy-button`/`chat-regenerate-button` (real testids, ELITEA-2181) on
  AI responses; accessible names "Read out" and "Delete" (no testid found for
  the per-message Delete icon); user-message pencil icon has accessible name
  "Edit the message and regenerate answer" with **no confirmed testid**
  (distinct from `click_table_edit_icon`/`click_diagram_edit_icon`, which
  target AI-generated table/diagram edit affordances, not user-message
  editing — do not conflate). Conversation-level delete already has full
  testid coverage via `delete-confirm-*` (ELITEA-2114) and
  `CONVERSATION_MENU_ITEM_KEYS` includes `"delete"`.

**Resolved/added during ELITEA-2188 implementation (2026-08-15):**
- **Both testid gaps closed** on `automation/testids`
  (EliteaAI/EliteaUI@7292e18f): `chat-conversation-make-public-confirm-dialog`
  / `-confirm-button` / `-cancel-button` (threaded through `DotMenu.jsx` via
  new caller-supplied `dialogTestId`/`confirmButtonTestId`/`cancelButtonTestId`
  props, same precedent as `submenuTestId`); `data-conversation-type`
  (`"public"`/`"private_with_users"`/`"private_without_users"`) added to the
  existing `conversation-multi-user-icon` wrapper — asserted via new
  `ChatPage.wait_for_conversation_type()`.
- **Known, already-documented sidebar staleness defect
  (EliteaAI/elitea-testing-public#989, same class as
  `test_invite_users_add_cancel_close.py` Step 10) also fires on THIS case's
  own observables** — confirmed live: `data-conversation-type` stayed
  `"private_without_users"` for several seconds straight after an invited
  participant's Send (well after the server had persisted it), and stayed
  stale after making a conversation public too. The suite's established fix
  (`page.reload()` before re-reading the sidebar icon state) is required in
  BOTH places — right after conversation B's Send, and right after the
  make-public confirm — not just the one place ELITEA-2167 already
  documented it.
- **A SECOND back-to-back `+Chat` click in one test (open blank -> send ->
  open blank AGAIN for a second conversation) reliably hits the
  #1082-class stale-conversation race** — the first click after a Send often
  lands back on the just-sent conversation instead of a genuinely blank one.
  The `_open_genuinely_blank_conversation`-style settle-and-retry guard
  (already established in `test_invite_users_add_cancel_close.py`) is
  needed for ANY test creating 2+ fresh conversations in one run, not only
  the specific scenario that first surfaced it.
- **New timing race found and fixed this pass**: right after
  `click_add_users_confirm()`, the "Add users" modal's own MUI Dialog close
  transition can still be resolving when the very next action targets the
  composer's send button — `send_button.click(force=True, ...)` can fire
  during that transition and be silently lost (message typed, never sent, no
  navigation). Fix: `chat.add_users_dialog.wait_for(state="hidden", ...)`
  before touching the composer. Add this wait to any future flow that sends
  a message immediately after the Add-users confirm.
- **Known defect EliteaAI/elitea-testing-public#719** (Add-users picker's
  checkmark-icon `sx`-on-raw-svg console warning) re-confirmed on THIS case's
  own conversation-B setup too (not just ELITEA-2167/2168's flows) — filtered
  via the same `_is_known_checkicon_sx_svg_warning_719` idiom.

## Add/remove agent participant mid-conversation + conversation starters
(ELITEA-2177/2178/2465, qa-engineer analyst, 2026-08-15) — `/chat/{id}`
existing-conversation surface, NOT the Agent Hub / embedded-agent-detail
surfaces ELITEA-2369/1886 already cover.

- **`chat-conversation-starter-tile` renders on THIS surface too, already
  wired, zero new testid needed.** `/chat/{id}`'s `NewChat.jsx` mounts the
  SAME `ChatBox.jsx` → `ChatConversationStarters.jsx` tree ELITEA-1886 wired
  the testid on (for the embedded `/agents/all/{id}` chat) — confirmed live:
  adding an agent as a participant via the composer's "+ → Agents" flow on an
  EXISTING conversation renders starter tiles carrying
  `chat-conversation-starter-tile` with no additional wiring. `ChatPage`
  already has `CHAT_STARTER_TILE` / `get_chat_starter_tiles()` /
  `click_chat_starter_tile()` ready to use as-is.
- **The tooltip on a starter tile is CONDITIONAL on genuine visual
  truncation** (`EllipsisTextWithTooltip`'s `clientWidth < scrollWidth` check,
  `src/components/ConversationStarters.jsx:218-223`) — a short starter (e.g.
  the case-family's own "here is your task: Explain Exponential Backoff",
  48 chars) does NOT truncate at this environment's rendered tile width and
  correctly shows no tooltip on hover. Any case asserting the hover-tooltip
  behavior needs a starter text long enough to actually overflow (~150+
  chars confirmed to truncate reliably) — don't assume the case's own short
  example starter will exercise this path.
- **Plus-menu ("+") testids exist and are cleaner than the page object's
  current raw handles** — confirmed live via `getByTestId` resolution:
  `plus-menu-button`, `agents-menuitem` (same `-menuitem` suffix family as
  `PLUS_MENU_ITEM_SUFFIX`), `agents-search-input`, and the dynamic per-row
  `agents-menu-item-agent-{index}-{agent_id}`. `ChatPage.add_agent_participant()`
  still uses `get_by_role("button", name="plus menu")` /
  `get_by_placeholder("Search agents...")` / a raw `li[role="menuitem"]`
  text-match — pre-existing tech debt (#25/#42 class), not touched this
  dispatch since the method already works; a future refactor pass could
  tighten it to the testids above.
- **The composer's "X" / remove-participant icon has NO testid** —
  `AgentEditorPanel.jsx`'s `IconButton` (`aria-label="switch to model"`,
  tooltip "Switch to model", TWO render branches ~line 178 and ~line 294)
  is genuinely missing `data-testid`, confirmed via source. `testid needed:
  chat-switch-to-model-button` — real gap, not yet added (ELITEA-2465's own
  case step 4 needs to verify this icon's presence).
- **`reasoning_effort: "none"` passes agent-CREATE but 400s
  participant-ADD.** `POST .../applications/prompt_lib/{project}` accepts
  `llm_settings.reasoning_effort: "none"` silently (agent created, `201`,
  bad value persisted) but
  `POST .../elitea_core/participants/prompt_lib/{project}/{conv_id}` for
  that same agent 400s:
  `"Input should be 'low', 'medium' or 'high'"` (Pydantic literal-enum
  validation on the participants endpoint only). Confirmed live this
  dispatch — cost ~15 minutes of debugging until traced via the network
  response body. Fixture guidance: omit `reasoning_effort` entirely (or set
  a valid enum value) when creating a disposable agent that will be added as
  a chat PARTICIPANT (not just used standalone) — this is a stricter check
  than agent-creation's own validation, asymmetric between the two
  endpoints.
- **The Playwright MCP browser's default-active project is NOT guaranteed to
  match `${ELITEA_PROJECT_ID}` (399, `Private`) from `.env.test`.** This
  session's persistent browser profile opened on project 471 ("Elitea
  Testing Team") by default — confirmed via the sidebar's project-id textbox
  and via `GET .../applications/prompt_lib/{id}?...` calls literally
  targeting different project ids. Data seeded via `AgentAPI`/Bearer-token
  calls against project 399 was invisible in the UI's own agent search until
  the project switcher was used to select "Private" (project 399) —
  `participants`-add also 400s cross-project (targets the CONVERSATION's
  project, not the agent's). Any future analyst/fixture on this surface:
  confirm the UI session's ACTUAL active project (sidebar textbox, or force
  `page.goto`/project-switcher-select at test start) rather than assuming
  the config default is what's live in a persistent local browser profile.
- **Removing an agent participant cleanly clears starters AND restores the
  default LLM, confirmed via full reload (not just live DOM).** Deleting the
  agent via API (`AgentAPI.delete_agent()`) also cleanly drops it as a
  conversation participant server-side — post-reload, zero leftover chip,
  zero leftover starter tiles, default LLM shown again, zero console errors.
  Deleting a just-sent agent-response message item (via its own "Delete"
  button) CASCADES to also remove the paired user message — confirmed live,
  useful cleanup shortcut instead of deleting each message individually.
- **Case-text drift (CLARIFICATION, not filed as a defect):** the
  "Remove agent?" confirmation dialog reads
  `"Are you sure to remove the {agent-name} agent from chat?"` — case text
  (ELITEA-2178) says "...from **conversation**?". Live wording is correct/
  current; assert "from chat".
- **"Claude B" (the case-family's own example agent name, ELITEA-2177/2178/
  2465) does not exist in either the `Private` (399) or "Elitea Testing
  Team" (471) project** — confirmed via full agent listing in both. Use any
  starters-bearing agent (the pre-existing Catalog "StarterComposer" agent,
  4 starters configured, works for a quick manual check; a disposable
  per-test agent via `AgentAPI.create_agent_full()` is the implementer's
  correct choice for isolation).
- **CONFIRMED DEFECT (issue #1569, 2/2 deterministic): clicking the Stop
  control mid-generation wipes the ENTIRE message exchange, not just the
  streaming response.** After Send → (while streaming) → click Stop, the
  message list goes empty in the UI AND server-side — confirmed via
  `GET .../conversation/prompt_lib/{project}/{conv_id}?messages_limit=10&
  sort_order=desc` returning `"message_groups_count":0,"message_groups":[]`
  even after a full page reload. Reproduced on two independent fresh
  conversations (ELITEA-2182/2183 session). The input bar DOES restore
  correctly (waveform reappears, input re-enabled) — only the transcript
  wipe is the defect. A SUBSEQUENT send-and-respond cycle after Stop works
  perfectly cleanly (ELITEA-2183 confirmed) — the defect is isolated to
  "does the interrupted turn survive", not "is the composer left usable".
- **The Stop control (`UserInput.jsx` ~line 552-562, `onClick={onStop}`,
  `<StopIcon>`) has NO `data-testid` today** — `testid needed:
  chat-stop-generation-button`, real gap (ELITEA-2182/2183's own subject).
  It renders in the SAME footer slot the composer-send-button-toggle test
  already proves is neither Send nor waveform during streaming
  (`send_button.count()==0` AND `voice_mode_button.count()==0`) — that
  test proves the Stop control occupies the slot by elimination but never
  asserts on it directly.

## ELITEA-2184/2185/2186/2187 (2026-08-15/16) — Regenerate exclusivity + click-replace behavior; #1569 re-confirmed a 3rd time

**Resolved/added during ELITEA-2184/2185/2186/2187 implementation (combined
analyst+implementer session):**

- **Regenerate and Delete render ONLY for the last AI message — confirmed
  via direct DOM query, not just hover/a11y-tree inspection.**
  `document.querySelectorAll('[data-testid="chat-regenerate-button"]').length`
  and the same for `chat-delete-button` return exactly **1** regardless of
  how many AI messages exist in the conversation (confirmed with 2 AI
  messages live) — the element is conditionally rendered
  (`isLastMessage`-gated in `ApplicationAnswer.jsx`, same conditional
  family as the already-documented `Answer` block's
  `skill-test-last-response`/`chat-answer-content` split), not merely
  CSS-hover-hidden on every message. This makes "Regenerate is exclusive to
  the last response" a deterministic, non-hover-timing-dependent testid-
  count assertion.
- **Copy and Read-out render on EVERY AI message**, by contrast —
  `chat-copy-button` returned **2** matches for the same 2-AI-message
  conversation. Do not assume the 4 action icons share identical
  last-message-exclusivity; only Regenerate + Delete are exclusive.
- **The existing `regenerate_action_button`/`copy_action_button`/
  `read_out_button`/`delete_action_button` `LocatorDescriptor` fields
  resolve PAGE-WIDE** (`page.get_by_test_id(...)`, no scoping). Safe to use
  bare only when the conversation has a single AI message (as
  `test_streaming_response.py` does) — a 2+-AI-message conversation makes
  `chat.copy_action_button`/`chat.read_out_button` throw a Playwright
  strict-mode violation (multiple matches). Any test touching a
  multi-exchange conversation needs the message-scoped constant variants
  added this session (`REGENERATE_ACTION_BUTTON` etc., chained off a
  specific `messages_container.nth(i)`).
- **Clicking Regenerate reuses the IDENTICAL `chat-stop-generation-button`
  control/testid as a normal Send's mid-stream state** — confirmed live:
  the composer's send-slot shows the same orange Stop control (computed
  `color: rgb(242, 153, 74)`) whether the in-flight generation came from a
  fresh Send or a Regenerate click. No separate "regenerating" indicator
  exists — reuse the existing `ChatPage.stop_generation_button` field
  as-is for both flows.
- **Regenerate replaces the last message's content IN PLACE** — the
  message-item list count does NOT grow (confirmed: 4 items before, 4
  items after a full regenerate-and-complete cycle on a 2-exchange
  conversation); only the last item's body text and its internal "Thought
  for `<n>` secs" accordion reset and re-stream. The new response text is
  genuinely different from the pre-regenerate text (both real LLM
  completions, observed live — not test-authored).
- **Defect #1569 re-confirmed a THIRD time, independently** (ELITEA-2182/
  2183 confirmed it 2/2; this session confirmed it again on a fresh,
  unrelated conversation, using the CASE's own `"generate a poem"` prompt
  rather than ELITEA-2182's prompt): clicking Stop mid-stream removes the
  entire exchange (user message + partial AI reply), not just the
  streaming response — the message list reverts to its pre-send state, and
  the composer's input is silently refilled with the typed-but-unsent
  text. This blocks ELITEA-2186 ("Regenerate After Stopped Generation")
  entirely — its own precondition (a stopped response to hover over and
  regenerate) cannot be constructed while #1569 is open. Do not re-attempt
  ELITEA-2186 without first checking #1569's status — the WIP commit
  observed on this same batch trunk for ELITEA-2182/2183 (`d2c3dcc2`,
  "verification run in progress") suggests active work on the underlying
  Stop-handling code at the time of this session.
- **Update (2026-08-18): ELITEA-2182/2183 reclassified `blocked`** on the
  wave-12 trunk — both tests hit #1569's own headline Stop-button subject
  (not an isolated assertion), so no soft-assert workaround applies per
  `.agents/role-overrides.md` § Declared-improvisation protocol ceiling.
  Matches ELITEA-2186's existing `blocked` disposition above.

## ELITEA-2177/2178/2465 (2026-08-15/16) — Add/remove agent participant mid-conversation + conversation starters

**Resolved/added during ELITEA-2177/2178/2465 implementation:**
- **`chat-switch-to-model-button` testid ADDED** (both `AgentEditorPanel.jsx`
  render branches) — EliteaAI/EliteaUI@c1905706 on `automation/testids`. The
  "no testid" gap this digest flagged above is now closed;
  `ChatPage.chat_switch_to_model_button` is a real `LocatorDescriptor`.
- **`chat-conversation-starter-tile-tooltip` testid ADDED** on the starter
  tile's MUI Tooltip popper content, via a new `slotProps.tooltip` wire on
  `EllipsisTextWithTooltip` (`src/components/ConversationStarters.jsx`) —
  EliteaAI/EliteaUI@c7e7f88e. A raw `[role="tooltip"]` selector is NOT a
  sanctioned #579 exception for our own MUI usage, so this was a genuine gap
  too, not just a nice-to-have. `ChatPage.chat_starter_tile_tooltip_content`
  + `hover_chat_starter_tile()` consume it.
- **`chat-conversation-starter-tile` itself needed NO new wiring on this
  surface** — confirmed live it already renders on the mid-conversation
  add-agent flow via `ChatConversationStarters.jsx`'s call site (wired
  ELITEA-1886, EliteaAI/EliteaUI@afb48435, 2026-08-07). `chat_page.py`
  carried a STALE comment claiming that call site was "intentionally left
  unwired" (written before the ELITEA-1886 dispatch); corrected in place
  this implementation.
- **`chat.send_button.click(force=True)` right after a starter-tile click
  is a real, reproducible no-op here too** — same root cause as the
  project's `chat_send_button_force_click_race.md` memory entry
  (`disabledSend`'s dependency can still be mid-flap a moment after the
  DOM `disabled` attribute already reads false; `force=True` bypasses
  Playwright's actionability wait that would otherwise line up with the
  settle). Plain (non-force) `.click()` is required for the "click a
  starter tile, then click Send" sequence on THIS surface too — confirmed
  by reproducing the no-op live before fixing it.
- **`ChatPage.is_participants_badge_visible()` cannot prove a NEGATIVE
  transition right after a removal click** — it only waits for VISIBLE, so
  `assert not is_participants_badge_visible(...)` immediately after
  clicking "Remove" can read "still visible" a moment before the DOM
  update lands (confirmed live — a real, reproducible flake, not a
  one-off). Added `ChatPage.wait_for_participants_badge_absent(section,
  timeout)` — waits on `state="hidden"` directly — as the correct
  post-removal check; reuse it instead of the bool-returning method for
  any future "assert this badge is now gone" step.
- **The participants-popover row (`PARTICIPANT_ROW`) renders a
  "Participant Name" loading-skeleton placeholder before its real content
  settles** — a one-shot `row.wait_for(state="visible")` +
  `text_content()` read can catch that placeholder text instead of the
  real agent name (confirmed live — reproducible). Use a web-first
  `expect(row).to_contain_text(agent_name, timeout=...)` instead, which
  retries until the real content lands.

## ELITEA-2073/2074 (2026-08-20) — Build-with-AI Cancel-then-Generate in chat canvas; generated agent's Save/starters

- **`generate-agent-cancel-button` works identically inside the chat canvas
  as on the standalone `/agents/create` page** — confirmed live: Cancel on
  the prompt step removes `generate-agent-modal` from the DOM immediately,
  leaves `agent-name-input` empty, canvas title stays "Create New Agent".
  Re-opening the SAME modal right after (`generate-agent-open-button`
  clicked a second time) resets `generate-agent-prompt-input` to `""` — no
  stale text survives a Cancel+reopen cycle. Neither ELITEA-1917 (Cancel,
  but on `/agents/create`) nor ELITEA-1920 (canvas, but never exercises
  Cancel) had proven this specific combination before.
- **`Anthropic Claude 4.5 Sonnet` "generate an echo agent" draft is
  reproducible in SHAPE but not in exact CONTENT across separate
  generations** — two independent live generations this session (same
  prompt) both produced `name: "Echo Agent"` and exactly 4 conversation
  starters, but the starters' literal text differed. Any case built on a
  Build-with-AI-generated agent must capture the actually-rendered content
  at run time and assert against THAT, never a literal example string —
  see the ELITEA-2074 AFS § Test Data for the full drift writeup (the
  case's own "Echo this: Hello, world!" example is never what actually
  renders).
- **The generated Echo Agent's own instructions explicitly permit (and
  demonstrably add) an `"Echo:"` prefix** — instructions text: *"You may
  add a brief prefix like 'You said:' or 'Echo:' to make it clear you're
  echoing, but otherwise preserve their exact words."* Live replies this
  session: `"Echo: Hello, Echo Agent!"` and `"Echo: . Can you repeat this
  message?"` (sent texts: `"Hello, Echo Agent!"` /
  `"Can you repeat this message?"`). Any exact-equality assertion against
  the sent text on a Build-with-AI-generated "echo" agent will false-fail
  on this correct, per-instructions behavior — assert `sent_text in
  reply_text` (containment), not equality.
- **`agent-save-button` is genuinely DISABLED immediately after a
  Build-with-AI Create-Agent completes** — confirmed live
  (`.disabled === true`, same for `agent-discard-button`) — because the
  single `POST .../applications/prompt_lib/{project}` the Create-Agent
  click fires already persists the FULL generated config (name,
  instructions, welcome message, starters); there is nothing left dirty to
  save. Any case whose precondition is "an agent was just generated via
  Build with AI" should expect Save disabled, not clickable — clicking a
  disabled MUI button is a no-op (no toast, no network call).
  **Implementation gotcha (ELITEA-2074, confirmed via a real pytest run,
  R1 rerun):** the disabled state settles ASYNCHRONOUSLY right after the
  create POST resolves — a one-shot `Locator.is_disabled()` read caught a
  transient `False` (still enabled) once in automated execution, even
  though two independent MCP/live-browser explorations both read `True`
  immediately. Use the web-first, retrying `expect(locator).to_be_disabled(
  timeout=...)` for this check, never a bare `.is_disabled()` snapshot read.
- **Starter tiles remain fully clickable/functional after the conversation
  acquires a real server-side id** (post-first-send) — confirmed live: the
  same 4-tile set (`chat-conversation-starter-tile`) was still present and
  clickable for a SECOND starter after the first send/reply cycle
  completed, same conversation, no reload needed.
- **Console note:** the pre-existing, already-documented `disableUnderline`
  React-prop warning (`test-specs/agents/_surface.md`,
  `test-specs/skills/_surface.md`) fires on `GenerateAgentReviewForm.jsx`'s
  Name field for the AGENT flow too (not just Skill) — same baseline noise,
  not a new finding, exclude from console-error assertions on any
  Build-with-AI review-form case.

## Edit owned agent via chat canvas (ELITEA-2089, confirmed 2026-08-18)

Canvas edit flow for an **owned** agent participant. Distinct from ELITEA-2075
(read-only / public agent canvas) and ELITEA-2166 (create-new-agent canvas).

### How the edit canvas opens

1. Click `chat-participants-badge-button` (participants badge).
2. Hover over the participant row (`chat-participant-row-application_{agent_id}_{project_id}` —
   dynamic testid, hover to reveal actions).
3. Click `chat-participant-edit-view-button` (pencil icon labelled "Edit agent").
4. URL changes to `/chat?edited_participant_id={agent_id}`.
5. Edit canvas slides in on the right.

### "Editing..." chip state

- `chat-participant-settings-button` (button in the composer chip) shows the text
  `"Editing..."` when an owned agent's canvas is open, `"Viewing..."` for public agents.
- Source: `AgentEditorPanel.jsx:291` — `{canEdit ? 'Editing...' : 'Viewing...'}`.
- Assert via `expect(...).to_contain_text("Editing...")`.

### Canvas chrome testids (all on main)

| Element | testid |
|---|---|
| Close (X) | `agent-canvas-close-button` |
| Title | `agent-canvas-title` |
| Subtitle (version) | `agent-canvas-subtitle` |
| Save | `agent-save-button` |
| Discard | **MISSING — `agent-discard-button` needs adding** |

### Welcome message field

- `agent-welcome-message-input` (on main ✓) — the textarea.
- After typing, `agent-save-button` and `agent-discard-button` become enabled.
- Save fires `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` → 201.
- Success toast: `toast-message` contains `"The agent has been updated"`.

### Known secondary 404 after Save

After a successful save, a second call fires:
`PUT entity_settings/prompt_lib/{project_id}/undefined/{agent_id}` → 404

The `undefined` in the path is a missing parameter in AgentEditor.jsx (likely `folder_id`
or `entity_type_id`). Does NOT affect the main save or the test outcome. Exclude
`entity_settings` from console-error assertions in tests of this flow.

### Sync verification path

After saving and closing the canvas, navigate to `/agents/all/{agent_id}?viewMode=owner`.
The Welcome message field (`agent-welcome-message-input`) shows the saved value — change
is synchronised immediately.

## ELITEA-2201 — send message with attachments, AI response references filenames,
## chips clear after send — zero new testids, ready-for-automation (2026-08-19)

- **Genuine coverage gap vs the closest neighbour, ELITEA-2091** (Team-project +
  drag-drop + LLM-switch, `test_create_new_conversation_team_project_attachments_and_llm.py`,
  merged to `automation/base`): that test attaches + sends + verifies the message/
  filenames land in the thread, but it NEVER waits for the actual AI response
  content (only auto-naming) and NEVER checks the composer's attachment state
  post-send. ELITEA-2201's own steps 4-5 (response acknowledges files; chips
  cleared after send) are exactly the two things 2091 doesn't assert. Given how
  different the two scenarios are otherwise (Team project + LLM-switch vs a plain
  default-project send), this shipped as a NEW focused spec (`ready-for-automation`),
  not an `extend-existing` graft onto 2091's file — see AFS § Metadata.
- **Response-content assertion, live-confirmed workable.** Small, distinctly-named
  `.txt` files (short text bodies) attached + `"Please analyze these files"` (case's
  own verbatim message) reliably produce a response that quotes the filenames back
  VERBATIM, in both the model's "Thinking" trace and its final Markdown answer —
  confirmed live this session (`report_alpha.txt`/`notes_beta.txt`/`summary_gamma.txt`
  all appeared in the response text). The model explicitly reasons "the content has
  been embedded directly in the messages, so I don't need to use file reading tools"
  — no toolkit/file-read call is made, attachment content rides in the message
  payload itself. This is the "capture-the-real-response, assert-the-invariant"
  fidelity pattern, NOT a fabricated payload (`.agents/testing.md` § Fidelity policy).
- **Chips clear immediately on send** (confirmed live) — the composer's
  `chat-attachment-chip-{index}` elements unmount and the "Attach Files (N left)"
  counter resets to the full ceiling (`"10 left"`) the instant the message is sent,
  well before the AI response starts streaming. `ChatPage.wait_for_attachment_chip_count(0)`
  is the correct web-first wait (no race with the response).
- **Same `#691` fixture caution as ELITEA-2091** — do not seed via the shared
  `conversation_id` fixture when the test's first action is sending a UI message;
  create fresh via `+Chat` and capture the real conv id from the post-send URL for
  cleanup.
- Zero new testids — every handle (`sidebar-create-button`, `plus-menu-button`,
  `chat-attach-menuitem-button`, `chat-attachment-chip-{index}`, `chat-message-input`,
  `chat-message-item`, `send-button`) is pre-existing and on `main` (freshly
  re-verified this session).
- AFS: `test-specs/chat-interface/l3_send-message-with-attachments-verify-included_ELITEA-2201.md`.

## ELITEA-2209 — direct toolkit call, tool call in thinking steps — extend-existing
## onto ELITEA-2215's merged spec (2026-08-19)

- **Near-duplicate of ELITEA-2215** ("Chat – Tool Action and Output – Complete Flow
  from Direct Toolkit Call", `test_direct_toolkit_call_complete_flow.py`, merged to
  `automation/base`): same live flow (toolkit as sole participant, no agent, message
  triggers a real tool call, "Thought for X secs" → thinking-steps chip). 2215's
  merged test already proves 2209's steps 2-4 (thought accordion, auto-expanded
  thinking steps, colon-separated `"{toolkit}: {tool}"` chip format — 2209's OWN
  example `"aaa: create_file"` is already colon-separated despite its "dotted"
  description, same drift 2215 already documented). **Only 2209's step 1 — "Toolkit
  in PARTICIPANTS; no AGENTS section" — is unproven**: the covering test's Setup adds
  the toolkit but never reads the participants panel. `extend-existing` targeting the
  covering test, gap = one Setup-time assertion.
- **Participants-badge mechanism, live-confirmed.** `chat-participants-badge-{section}`
  (`ChatPage.is_participants_badge_visible(section=...)`, pre-existing, already used
  by 3 other merged specs for `"toolkits"`/`"agents"`) is the correct handle — no new
  testid needed. Confirmed live this pass: adding a toolkit as sole participant
  renders the `toolkits`-section collapsed badge in the composer's top-right control
  row; no `agents` badge renders. Screenshot:
  `.playwright-mcp/page-2026-08-19T12-53-41-660Z.png` (probe used the seeded
  `AutoTest Confluence Toolkit 1787` — see caution below).
- **Caution (test-data, not a defect):** `AutoTest Confluence Toolkit 1787` (seeded
  toolkit in project 399) is itself misconfigured — selecting it fires a `400` on
  `GET .../toolkit_validator/prompt_lib/399/2945` and its badge renders in an
  error/attention variant. Unrelated to this case's subject; don't reuse that toolkit
  for the new assertion — reuse 2215's own `artifact_toolkit` fixture instead (already
  confirmed properly configured by the covering test).
- **2209's target is currently gate-excluded** (2215's test carries a soft-asserted,
  confirmed-non-deterministic known defect, `elitea-testing-public#1127` — see
  `.agents/testing.md` § Merge gate "Unconfirmed" history and the covering AFS's
  fix-round-2 note). The new participants-panel assertion must be placed BEFORE the
  message send / BEFORE the #1127 classification block, as a plain unconditional
  assert — NOT routed through the existing `soft_failures` aggregation, since it's
  mechanically unrelated to #1127.
- AFS: `test-specs/chat-interface/lextend_direct-toolkit-call-participants-panel-verification_ELITEA-2209.md`.

## ELITEA-2210 — direct toolkit call, chip display — extend-existing (ZERO-DIFF) onto
## the same ELITEA-2215/2209 covering spec (2026-08-19)

- **Third case in this batch to land on the SAME `test_direct_toolkit_call_complete_flow.py`
  covering spec.** ELITEA-2210's objective ("tool execution results display as chips when
  toolkit called directly") is a near-verbatim restatement of ELITEA-2215's — different
  example toolkit/tool (`'aaa'`/`delete_file` vs the covering spec's `artifact_toolkit`/
  `create_file`), same mechanism. **No gap at all** (not even one assertion) — this is a
  zero-diff extend: the covering spec's current trunk state (post-2209) already satisfies
  every one of 2210's case elements unconditionally.
- **Tool-agnosticism confirmed by reading `ActionView.jsx` directly** (not by re-running
  live — the mechanism was already live-confirmed twice this batch by 2215/2209/2211):
  `buildTitle()` (tool-chip text) is a plain `"{toolkitName}: {toolName}"` template with no
  branching on tool name; `renderIcon()` branches on `toolkitType` only (never the specific
  tool) via `getToolIconByType(toolkitType, ...)`. So `delete_file` and `create_file` on the
  same `artifact`-type toolkit render through the byte-identical chip code path — a strong,
  source-grounded basis for treating "different tool name" as pure DATA, not a new STEP/branch
  worth its own test.
- **Case-text pitfall inherited, not new:** 2210's own message
  (`"use delete_file toolkit to remove from the bucket all files"`) is the EXACT string
  ELITEA-2211's AFS already live-tested and found ambiguous ("the bucket" → LLM asks which of
  588 buckets instead of calling the tool). Doesn't affect 2210's own disposition (zero-diff,
  no new message-driving code), but worth knowing if anyone manually runs this case's literal
  text later.
- AFS: `test-specs/chat-interface/lextend_direct-toolkit-call-chip-tool-agnostic-verification_ELITEA-2210.md`.

## ELITEA-2474 — direct toolkit call complete flow — already-covered, EXACT
## duplicate of ELITEA-2215 (2026-08-19)

- **Fourth case in this batch to reference the same `test_direct_toolkit_call_complete_flow.py`
  covering spec — but unlike ELITEA-2209/2210 (genuine or data-variant gaps), ELITEA-2474 has
  ZERO difference from ELITEA-2215.** Same toolkit-only-participant precondition, same literal
  trigger message (`"create a file named test.txt"`), same tool (`create_file`), same chip/response
  expectations — even the case-text phrasing "LLM model chip, toolkit chip, and tool call chip" is
  a verbatim match of ELITEA-2215's own case text (quoted identically in its AFS's CLARIFICATION
  note). This is a duplicate manual TMS case, not a data-variant or a genuine gap — classified
  `already-covered`, not `extend-existing` (contrast with ELITEA-2210, which needed a NEW test
  because it used a DIFFERENT tool, `delete_file`, requiring its own live proof per "coverage
  judgments stand on your own execution" — ELITEA-2474 introduces no such variation).
- **Step 6 ("chips horizontal in a row with icons and labels") is not a separate observable** — it's
  inherent to the SAME `chat-answer-tool-chip`/`chat-answer-model-chip` elements the covering test
  already asserts on: `ActionView.jsx`'s `styles.header` container is `display: 'flex'` (default row
  direction, line 584) and each chip (`styles.toolkitBadge`, line 592) always renders an icon
  (`iconContainer`, line 605) + label (`Typography`) — confirmed by reading the component this pass,
  no conditional/variable layout a second assertion could catch differently.
- No live re-execution performed for this dedup call (same precedent as ELITEA-2471/2472/2473 —
  Rule-6 dedup is a source+file:line comparison, not a fresh execution mandate, when the covering
  spec already live-executes the byte-identical flow).
- Known defect `elitea-testing-public#1127` (non-deterministic, ~2/5) still applies identically —
  not a new finding, doesn't affect the already-covered verdict.
- AFS: `test-specs/chat-interface/lcovered_direct-toolkit-call-complete-flow-duplicate_ELITEA-2474.md`.

## Context Management DISABLED — Context Budget widget stays at zero (ELITEA-2216)
- Confirms and extends the ELITEA-2218/2374 digest entries above for the OPPOSITE
  (disabled) global state: with Context Management OFF, the Context Budget widget
  (collapsed `0%` indicator, expanded panel, AND the "Edit context settings" modal)
  ALL show `0` for tokens/percentage/Messages/Summaries — confirmed live via a real
  message + full AI response (~90s genuine generation), no context-management-specific
  network call fires at all while disabled (the backend appears not to compute/track
  budget usage when the setting is off, not merely hide a computed value).
- **The collapsed-Participants-panel timing (panel not mounted pre-message, collapsed
  by default post-message, `expand_participants_panel()` required) is IDENTICAL whether
  Context Management is ON or OFF** — confirmed this is a general chat-composer
  mechanism, not something the disabled/enabled state changes. Don't re-derive this per
  state; it's the same `ChatPage.expand_participants_panel()` path either way.
- **Account's live Max Context Tokens is `6400`, not the oft-cited case-text `64000`**
  (confirmed via `/settings/memory` this session) — read the token ceiling dynamically
  in any assertion, never hardcode either value; it's account-config, not a product
  constant.
- **The "Edit context settings" per-conversation modal (`context-budget-edit-button` →
  `ContextStrategyModalContent`) is click-verified end-to-end for the first time this
  session** (ELITEA-2218's AFS only source-reviewed it). Its header carries its OWN
  "Context Management" toggle switch, mirroring the global setting (unchecked when
  globally OFF); its Save button stays disabled with nothing dirty. Three collapsed
  accordion sections inside ("Context Strategy & Token Management", "Summarization",
  "User Instructions") were not expanded/explored this pass.
- **`ChatPage.send_message()`'s send-button click is intercepted by a MUI overlay**
  (confirmed live, standard `mui-patterns.md` pattern) — `use_enter=True` (Enter
  keypress) is the reliable path; don't force-click the send button.
- No collapsed-indicator-specific testid confirmed (the bare `0%` shown before
  Participants-panel expansion) — `chat_page.py`'s own comment suggests this was
  already investigated and found to lack a stable handle. Assert via the EXPANDED
  panel's existing testids (`context-budget-tokens`/`-messages-count`/
  `-summaries-count`) instead, which this case's core assertion already uses.
- AFS: `test-specs/chat-interface/l3_context-management-disabled-widget-stays-zero_ELITEA-2216.md`.

## Context Management ON, Auto-Summarization OFF — no summarization at max tokens (ELITEA-2217)

**Resolved/added during ELITEA-2217 implementation:**
- Added the missing `context-modal-summarization-toggle` testid to the "Edit
  context settings" dialog's own "Enable automatic summarization" switch
  (`ContextStrategySummarization.jsx`, `EliteaAI/EliteaUI@69921d7c`, pushed to
  `automation/testids`) — the AFS's `testid needed` flag from analysis. Same
  `Mui-checked` class-attribute read pattern as its sibling
  `context-modal-management-toggle`.
- Added `ChatPage.set_max_context_tokens_in_modal()` — a sibling of
  `set_context_strategy_thresholds()` that touches ONLY Max Context Tokens +
  Save, because `context_modal_target_summary_tokens_input` is genuinely
  DISABLED (not just skippable) whenever Automatic Summarization is off, and
  `press_sequentially()` against a disabled input raises. The disabled field
  stays READABLE via `.input_value()` though — used to read the account's
  live Target Summary Tokens value from inside the already-open modal
  (sidesteps issue #1605) instead of navigating back to Settings > Memory.
- **Live message-count variance vs the AFS's own live session**: the AFS's
  analyst session crossed a 5,000-token Max Context Tokens threshold in 4
  real long-prompt exchanges (127→5,301). This implementation's own live run
  needed closer to the cap before crossing 100% utilization (used ~8 real
  exchanges before the first genuinely reached >100%; a first cap of 8
  undershot at 4,257/5,000 and had to be widened). Real LLM response-length
  variance run-to-run — don't hardcode a tight message-count cap for this
  family of tests; size it with headroom (this implementation settled on 15).
- **New finding — sidebar vs modal stats can transiently disagree (not a
  case-blocking defect, reported as a CLARIFICATION)**: `context-budget-*`
  (sidebar panel) and `context-modal-stat-*` (the "Edit context settings"
  dialog) are both rendered from the same `ContextStats`/`ContextBudgetProgress`
  components but are populated via two SEPARATE subscriptions to the
  conversation's stats — confirmed live this session that reading the
  sidebar's percentage immediately before opening the dialog, then reading
  the dialog's own percentage a moment later (no message sent in between),
  can show two different values off the same underlying conversation (e.g.
  114% vs 136%). Each panel is internally self-consistent (tokens/max/percent
  agree with each other within that one panel); it's the TWO panels that can
  briefly diverge. This implementation asserts each panel against its own
  internal state, not cross-panel equality — cross-panel equality is NOT a
  case requirement (the case's Step 7 only asks the modal to self-report 0
  Summaries + toggle OFF). Worth a future analyst/reviewer's attention if a
  case ever DOES require exact sidebar/modal parity.
- AFS: `test-specs/chat-interface/l3_auto-summarization-disabled-no-trigger-at-max-tokens_ELITEA-2217.md`.

## ELITEA-2076 — In-chat "Create New Pipeline" canvas Discard flow (2026-08-20,
## combined analyst+implementer)

Extends the "In-chat 'Create New X' canvas family" section above with the
Discard side of the flow — ELITEA-2079/2089 only ever exercised Save (2079)
or verified Discard's *enabled* state without clicking it (2089's AFS/test).

- **THREE new testids added this session** (`EliteaAI/EliteaUI@d4edc6e5`,
  `automation/testids` only — awaiting human promotion to `main`):
  `pipeline-canvas-discard-button`, `pipeline-canvas-discard-confirm-modal`,
  `pipeline-canvas-discard-confirm-button`. `BaseEditor.jsx`/`EditorHeader.jsx`
  already rendered `Button.DiscardButton` unconditionally when `!isPublic`
  (with a pre-existing `discardButtonTestId` prop path, added for
  ELITEA-2089's Agent-canvas Discard but never wired at `PipelineEditor.jsx`'s
  own `<BaseEditor>` call site). `Button.DiscardButton` (`DiscardButton.jsx`)
  itself already supports `modalDataTestId`/`confirmButtonDataTestId` props
  (proven live by `CredentialsTabBar.jsx`'s direct usage), but
  `EditorHeader.jsx`'s own call only ever forwarded `dataTestId` — never the
  modal/confirm-button testids. Fix: two new optional props,
  `discardModalTestId`/`discardConfirmButtonTestId`, threaded
  `BaseEditor.jsx` → `EditorHeader.jsx` → the existing `Button.DiscardButton`
  props, supplied ONLY at `PipelineEditor.jsx`'s call site — sibling
  Agent/MCP chat canvases (`AgentEditor.jsx`/`ToolkitEditor.jsx`) unaffected
  (optional, caller-supplied props).
- **Confirmation dialog is genuinely a confirm-before-discard step, not a
  no-op** — confirmed live: clicking the (now-enabled, once dirty) Discard
  button opens a `Warning`-titled `BaseModal` with body text `"Are you sure
  you want to discard changes?"` and its own "Discard" confirm button.
  Confirming it: (a) Formik `resetForm()`s the Name/Description fields back
  to `""`, (b) re-disables the header Discard button (form no longer dirty),
  (c) fires **zero** `POST`/`PUT` to `/applications/prompt_lib/{project}` at
  any point in the whole flow — the Discard path never touches the create
  endpoint (only pre-existing `GET .../applications/prompt_lib/399?...`
  list-refresh calls fire, from opening the `+` menu's Pipelines submenu,
  same background calls ELITEA-2079 also observes).
- **`chat-participants-badge-pipelines` absence is the correct negative
  assertion** for "no pipeline was created" (case step 10) — same
  already-documented idiom (`ChatPage.is_participants_badge_visible`) used
  elsewhere in this suite for "no X participant" cases
  (`test_slash_mention_empty_state.py`, `test_direct_toolkit_call_complete_flow.py`).
- **No product defect found** — this flow behaves exactly as the case
  describes; zero clarifications needed.
- AFS: `test-specs/chat-interface/l2_pipeline-discard-changes-clears-canvas_ELITEA-2076.md`.

## ELITEA-2077 — Create Pipeline from Conversation, Save Basic Configuration
(2026-08-20, combined analyst+implementer slot)

- **`pipeline-canvas-subtitle` testid added** — closes the LAST remaining
  gap in the four-way canvas-chrome testid family documented above
  (title/close/discard were fixed by ELITEA-2076/2079; subtitle was the one
  nobody had needed yet). `PipelineEditor.jsx`'s `<BaseEditor>` call now
  supplies `subtitleTestId="pipeline-canvas-subtitle"` (the prop already
  existed end-to-end, same shape as `titleTestId` — `AgentEditor.jsx` already
  supplies its own `agent-canvas-subtitle`). Pushed to `automation/testids`
  (`EliteaAI/EliteaUI@7b1e2c5a`). Renders `"base"` (the version name) next to
  the canvas title once a real (non-create-mode) pipeline is open.
- **Composer chip is a THREE-way split, not two** — `chat-switch-participant-button`
  (name, e.g. `"test-pipeline"`) and `chat-version-selector-trigger` (version,
  e.g. `"base"`) are the two elements ELITEA-2079's AFS already documented, but
  the case's "Editing..." status text lives on a THIRD sibling button in the
  same `ButtonGroup`: `chat-participant-settings-button` (pre-existing testid,
  added by ELITEA-2362 for its click target, never previously asserted for its
  TEXT). Confirmed via a full DOM text-node walk — `/editing/i` matches nowhere
  else on the page immediately post-save. Any case asserting the "Editing..."
  status should read THIS element, not try to find the text inside the
  name/version chips.
- **ADVANCED section is expanded by default in CREATE mode, no click needed**
  — `agent-canvas-section-advanced` (on-main), containing `pipeline-step-limit-input`
  pre-filled `"25"`, is visible immediately once the create-mode canvas opens
  (no accordion-expand interaction required, unlike `EDITOR NOTES` elsewhere
  on the standalone detail page). The case's "model chip" is the composer
  form's own Model Selector group (`model-selector-button`/`model-selector-name`),
  rendered in the same panel — assert non-empty text only, the display name is
  environment-dependent (`.agents/testing.md` § Known issues).
- **Dev-server HMR staleness — confirmed live, worth flagging for future
  sessions.** A long-idle `npm run dev` process on port 5173 stopped picking
  up file-watcher events for at least the `PipelineEditor.jsx` edit above — the
  new testid was committed, pushed, and present on disk, yet 3 consecutive
  live create-pipeline flows (across a full page navigation) kept rendering
  the OLD build (`curl http://localhost:5173/src/<file>.jsx` also served stale
  transformed source, confirming it wasn't a browser cache issue). A hard
  restart (`kill` the stale `vite`/`npm run dev` PIDs bound to :5173, relaunch)
  fixed it immediately. If a testid you just added reads absent live despite a
  full reload and no console/network error explains it, `curl` the served
  source for that file before concluding the JSX itself is wrong.
- **No product defect found** — this flow behaves exactly as the case
  describes; zero clarifications needed.
- AFS: `test-specs/chat-interface/l2_pipeline-create-save-basic-configuration_ELITEA-2077.md`.

## ELITEA-2078 — Pipeline Flow Editor "Add LLM Node, Discard Changes, Verify
## Node is Removed" (2026-08-20, combined analyst+implementer)

Extends the "In-chat 'Create New X' canvas family" section above — the
Flow-graph-dirty-state Discard flow, one layer deeper than ELITEA-2076
(which only ever dirtied the header form's Name/Description fields).

- **`PipelineEditor.jsx`'s Discard is gated on `totalDirty = isDirty ||
  isYamlDirty`, not just the Formik form.** `isYamlDirty` comes from
  `EditorPanel`'s `useIsPipelineYamlCodeDirty()` via a `setYamlDirty` prop —
  adding a node on the Flow tab flips it, which enables the SAME
  `pipeline-canvas-discard-button` header button ELITEA-2076 already added
  (no new testid needed). Confirmed live: Discard/Save both read `disabled`
  immediately after the Flow Editor tab opens on a fresh pipeline, and both
  become enabled the instant the LLM node is added.
- **`handleDiscard()` (`PipelineEditor.jsx`) reverts the FLOW GRAPH, not
  just form fields**: `dispatch(actions.resetPipeline())` +
  `dispatch(editorActions.resetPipelineEditor())`, alongside the
  Formik-field reset ELITEA-2076 already documented. Confirmed live: after
  confirming Discard, the canvas returns to exactly the pre-add state
  (`get_node_count()==1`, `get_node_ids()==["END"]`), and the header
  Discard/Save buttons re-disable.
- **Zero network calls fire between adding the node and the post-discard
  state** — confirmed live via network capture (only the create-mode
  `POST .../applications/prompt_lib/399` → `201` and its hydration `GET`s
  fire during Setup; nothing fires for add-node or discard). Same "Discard
  never touches the server" finding as ELITEA-2076, now confirmed to
  extend to Flow-graph changes.
- **Add Node menu's 11-item set matches the case's own list exactly, live-
  confirmed AND source-traced**: `AddNodeMenu.jsx`'s `getVisibleNodeTypes()`
  filters `FlowEditorConstants.PipelineNodeTypes` down to 11 by excluding
  `DeprecatedConstants.DeprecatedOrInvisibleNode` (Tool, Function, Pipeline,
  Condition, Loop, LoopFromTool — deprecated — plus End, Ghost, Default —
  invisible). Menu renders alphabetically by display label: Agent, Code,
  Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State
  modifier, Toolkit. The compliant testid-based methods
  (`get_add_node_menu_items()` / `select_add_node_menu_item(internal_type)`,
  ELITEA-2030) are preferred over the older `add_node(display_name)` — the
  latter still chains a raw `button.MuiIconButton-colorPrimary` CSS handle
  + `get_by_role("menuitem")`, kept only for its existing ELITEA-2079
  caller, not a pattern to imitate in new code.
- **No product defect found** — this flow behaves exactly as the case
  describes; zero clarifications needed.
- AFS: `test-specs/chat-interface/l2_pipeline-flow-editor-add-llm-node-discard-changes_ELITEA-2078.md`.

## Agent/Pipeline participant SECOND-ADD silent drop — re-characterised (ELITEA-2455, 2026-08-26)
- **Supersedes the "order-dependent" framing in the 2026-08-06 section below.** Re-run
  live over **16 repetitions** through the real pytest/page-object harness (fresh
  `agent_id` + `pipeline_with_llm_id` + fresh UI-created conversation each time):
  whichever of Agent/Pipeline is added **second** is silently dropped — **in BOTH
  orders**, 13/16 runs. Evidence commented on EliteaAI/elitea-testing-public#1279.
- **Measured breakdown:** no settle between adds → 0/6 (Pipeline→Agent). Condition-wait
  on the 1st participant's row visible + `chat-switch-participant-button` visible →
  0/3. Same + `networkidle` → 0/3. Fixed **1500 ms wall-clock** delay after each add →
  Pipeline→Agent 2/2, Agent→Pipeline 1/2.
- **There is NO honest settle condition.** Row-visible, `chat-switch-participant-button`
  visible and `networkidle` all resolve together at ~1.7–2.2 s — the measured gap between
  them and the failing second add was **0.00 s in 6/6 runs**. Only raw elapsed wall-clock
  time changes the outcome, i.e. client participant state settles after every DOM/network
  signal is quiet. A fixed `sleep` is the only known mitigation, is banned here
  (`.agents/conventions.md`), and is still only ~75 % reliable.
- **The silent-drop runs have a COMPLETELY CLEAN console** — no 400, no `icon_meta`
  TypeError, no toast. The `version/prompt_lib` 400 documented on #1279 fires only on the
  runs that SUCCEED. **Never use a console-error assertion as the guard for this
  behaviour** — it cannot see the failure.
- **Toolkit and MCP participants are unaffected** — back-to-back Toolkit→MCP adds in one
  open popper are reliable (ELITEA-2203's merged spec does exactly that, green). The race
  is specific to the version-carrying Agent/Pipeline participant types.
- **A brand-new, UNSENT conversation is not persisted** — URL stays `/chat` with no id, and
  a reload clears every participant (confirmed 4/4 live). Any persistence/reload check must
  come after the first Send.
- Any case needing an Agent **and** a Pipeline as simultaneous chat participants is still
  unautomatable. Cheap unblock probe (~4 min) recorded in
  `l1_chat-create-conversation-add-all-participant-types_ELITEA-2455.md` § Automation Hints —
  run it first before spending analysis time on such a case.

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

## Agent/Pipeline participant SECOND-ADD silent drop — re-confirmed a THIRD time (ELITEA-2094, 2026-08-27)

Independent re-confirmation of #1279 from a separate analyst session, one day after the
ELITEA-2455 pass. **7 fresh live reps, no fixed delays**, project 399, localhost:5173:

| Variant | Reps | Result |
|---|---|---|
| Agent → Pipeline | 4 | **0/4** — Pipeline silently dropped, PIPELINES section never renders |
| Pipeline → Agent | 2 | **0/2** — Agent silently dropped |
| **Pipeline alone (control)** | 1 | **1/1 OK** |

- The **pipeline-alone control is the new datapoint**: a pipeline participant adds fine on its
  own, so this is specifically a *second version-carrying participant* race, not broken pipeline
  participants. Run this control before blaming a diff.
- **Console clean in 7/7** (`console=[] pageerrors=[]`). A "no console errors" assertion cannot
  detect this failure mode — do not write one as its guard.
- Toolkit and MCP adds unaffected (4/4), consistent with ELITEA-2203's merged green spec.
- Unblock signal is mechanical: 6 reps of Agent→Pipeline landing with **no fixed wall-clock
  delay**. Probe shape recorded in
  `test-specs/chat-interface/l2_add-agent-pipeline-toolkit-mcp-participants-panel_ELITEA-2094.md`
  § Automation Hints (~4 min to re-check).

### A misconfigured participant has NO `chat-participant-row-*` testid (automation-critical, 2026-08-27)

`chat-participant-row-{uniqueId}` renders **only for a non-misconfigured participant**. A
participant flagged with a warning renders through the attention branch instead
(`chat-participant-warning-icon`) and carries **no row testid at all**.

Consequence, hit live this pass: `mcp_toolkit_with_tools` (a *healthy* public
`mcp.deepwiki.com` MCP) is falsely flagged "Server is disconnected!" (**#687, still reproducing
4/4 on 2026-08-27**), so an assertion written as "the MCP appears as
`chat-participant-row-toolkit_{id}_{proj}`" reads as an **outright missing participant** even
though the MCP is visibly present in the MCPS section. Any participant assertion touching MCPs
must either accept the warned shape or wait on #687.

### Project 399 DOES satisfy the "entities exist" precondition (retires a July note, 2026-08-27)

The July ELITEA-2094 note that `${ELITEA_PROJECT_ID}` = 399 ("Private") has zero pipelines and
zero MCPs, and that participant analysis must therefore move to project 471, is **retired**. It
described the pre-existing catalogue, not what the fixtures build: `agent_id`,
`pipeline_with_llm_id`, `artifact_toolkit` and `mcp_toolkit_with_tools` all create their own
entities in 399 and all resolved first try this pass. No project switch needed.

### Pipeline participant menu-item testid (verified live 2026-08-27)

`[data-testid="pipelines-menu-item-pipeline-{project_id}-{pipeline_id}"]` — same generic
`PlusChatSubmenu.jsx` template as the agents/toolkits/mcps rows, already on
`automation/testids`, resolves first try. **No `ChatPage` constant or `add_pipeline_participant_by_id()`
method exists yet** — the agent analogue (`AGENT_MENU_ITEM` + `add_agent_participant_by_id`) does.
That is the one genuine page-object gap for any four-participant-type case.
