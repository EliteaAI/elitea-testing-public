# Test Case: Chat – Mentions with # – Select Pipeline from List and Verify Pipeline is Added to Participants

## Metadata
- **TMS IDs (family)**: ELITEA-2208 (priority medium, 3 compound steps) + ELITEA-2470 (priority high, 7
  granular steps) — SAME flow, ELITEA-2470 is a more granular re-statement of ELITEA-2208 (icon/name
  detail in the PARTICIPANTS row is spelled out explicitly, and navigation/precondition are broken into
  their own steps). Differ only in assertion GRANULARITY, not in steps/actions — one family AFS,
  `family_afs=true`, same `afs_path`. Direct pipeline-flow sibling of the ELITEA-2207/2469 family
  (agent-flow), analysed earlier this same batch — same surface, same mechanics, different participant
  entity type.
- **Linked Story**: none (both cases `requirements: []`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Private project, `projectId=399` per the resolved participant `uniqueId` — this session's dynamically-
  selected pipeline was NOT Agent-Hub/"Public"-sourced, unlike the ELITEA-2207/2469 agent case; its
  `entity_meta.project_id` matched `settings.elitea_project_id` directly)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w14`, 2026-08-19
- **Status**: **extend-existing** (both cases)
- **surface_key**: `chat-hash-search-participants` (same surface as ELITEA-2206/2207/2469, all analysed
  this same session — reused their digest section for the `#` mechanics and testid provenance)

## Preconditions
- User is logged in to the Elitea platform.
- Pipelines exist in the project (ambient DEV data — 10+ pipeline-type cards already present in the `#`
  results for this account, no seeding needed; the shipped test should select whichever pipeline-type
  card the `#` dropdown returns, not hardcode a name, for resilience against account data changes — same
  approach ELITEA-2206/2207/2469 used).
- **Bare `/chat` navigation on this account intermittently hits a persistent loading-spinner overlay
  that blocks the composer's pointer events** (this session reproduced it: `chat-message-input` click
  retried >15× against a `MuiCircularProgress-svg`/`MuiBox-root` overlay, never cleared in 15s) — same
  account-data-volume artifact the ELITEA-2207/2469 AFS already documented (65+ folders). Live exploration
  worked around it by navigating to an existing conversation URL directly (`/chat/9082`); the shipped test
  sidesteps it entirely via the `conversation_id` fixture (API-seeded, no sidebar-folder-list dependency).

## Extension target — Rule-6 partial overlap

**Covering spec:** `automation/tests/ui/chat/test_chat_interface.py`, class `TestHashSearch`. Three
existing methods jointly cover PART of this family's flow, confirmed via fresh `git fetch origin` this
session (`git log origin/automation/base -1 -- automation/tests/ui/chat/test_chat_interface.py` →
`8981927cc`, contains all three):

1. `test_add_participant_via_hash_search` (line 434) — proves `#` opens the dropdown, a click on ANY
   first option (agent OR pipeline, unscoped) selects it, and the dropdown closes.
2. `test_hash_search_shows_agents_and_pipelines_from_all_sources` (ELITEA-2206, line 479) — proves
   per-card `pipeline` subtitle + icon presence, and that pipeline-type cards appear in the `#` results —
   but never selects one, never touches PARTICIPANTS or the composer, never sends a message.
3. `test_add_agent_via_hash_search_joins_participants_and_responds` (ELITEA-2207/2469, line 596) — proves
   the FULL flow (badge-absent → scoped-select → composer-chip → badge-present → popover-row → send →
   respond → remains-participant) but scoped to **agent**-type cards only; the pipeline analogue does not
   exist.

**Behavioural-overlap argument.** Together, (1)+(2) prove: the dropdown opens on `#`, pipeline-type cards
are present and individually distinguishable by their `-type` testid, and a generic selection closes the
dropdown. (3) proves the SAME participant-lifecycle mechanism (badge/composer/popover/send/respond/remain)
already works correctly for one entity type (agent) — end-to-end, live-confirmed, merged. That establishes
the mechanism is sound; it does not establish it for **pipelines** specifically, because pipelines route
through a structurally different `entity_name`/testid namespace (see Concrete Handles) that (3)'s own
implementation never exercises.

**Gap: no existing test selects a PIPELINE from `#` and verifies the PARTICIPANTS/composer/messaging
consequences.** Four live-confirmed gaps, none touched by any covering test:

1. **Selection must be scoped to a PIPELINE-type card specifically** (not "whichever card is first" —
   `test_add_participant_via_hash_search`'s `get_hash_search_first_option()` may click an agent). Both
   cases' own title/steps say "Select Pipeline" — the shipped test must filter `get_hash_search_items()`
   by `get_hash_search_item_subtitle(item) == "pipeline"` before clicking (reusing the exact
   ELITEA-2206-added handles, same filter idiom as ELITEA-2207/2469's agent-scoping, just the other
   subtitle value).
2. **PARTICIPANTS panel gains a PIPELINES section (not AGENTS), and the composer shows the selected
   pipeline as its active participant** — `test_add_agent_via_hash_search_joins_participants_and_responds`
   only ever opens `section="agents"`; nothing exercises `section="pipelines"` end-to-end with a real
   selection. Live-confirmed this session: `chat-participants-badge-pipelines` badge (via
   `is_participants_badge_visible(section="pipelines")`) appears where it was previously ABSENT, and
   `chat-switch-participant-button` (`is_agent_participant_in_composer(pipeline_name)`) shows the selected
   pipeline's name — confirmed via screenshot, button accessible name is "Switch Pipeline" (vs "Switch
   Agent" for the agent case), same physical testid.
3. **Sending a message reaches the selected pipeline and it remains a participant after responding** —
   no covering test sends a message to a pipeline participant at all. Live-confirmed this session: sent
   "hello" to a dynamically-selected pipeline ("AutoTest_Pipeline_probe_2020" this session), received a
   real system-generated response (see Clarification below re: response content), and the PIPELINES badge
   still read "1" afterward — matches both cases' own final assertion ("pipeline responds and remains in
   PARTICIPANTS").
4. **The participant `uniqueId` namespace for a pipeline is `pipeline_{id}_{project_id}`, NOT
   `application_{id}_{project_id}`** — confirmed live this session (Playwright-generated locator:
   `chat-participant-row-pipeline_8056_399`) by reading `getChatParticipantUniqueId()` in
   `EliteaUI/src/[fsd]/features/chat/participants/lib/helpers/participants.helpers.js`: a pipeline's
   `entity_name` resolves to `ChatParticipantType.Pipelines` ('pipeline', singular) whenever
   `entity_settings.agent_type === 'pipelines'`, distinct from the agent case's `'application'` prefix.
   `get_agent_participant_row()`/`remove_agent_participant()` both hardcode the `application_` prefix —
   neither is directly reusable for a pipeline participant (see Automation Hints).

All four gaps are additive assertions/selectors layered on the SAME `#`-select-and-close mechanism the
covering tests already prove — no new interaction primitive for opening/closing the dropdown itself, only
new assertions + one new locator-construction path (the pipeline unique-id prefix) after the existing
select click. Classified `extend-existing`, not `ready-for-automation`.

## Test Steps (source cases, reproduced for traceability; only the gap steps below need new code)

### ELITEA-2208 (3 compound steps)
1. Create or open a conversation; verify no PIPELINES in PARTICIPANTS — **GAP** (never asserted by any
   covering test; use a FRESH `conversation_id`-fixture conversation, guaranteed zero participants).
2. Type '#' and click a pipeline from the dropdown → pipeline name in message field; PIPELINES section
   added to PARTICIPANTS — **already-covered (open+select+close, generic) + GAP (pipeline-type scoping +
   participants-panel/composer assertions)**. See Clarification below re: "message field" wording.
3. Type a message and send → pipeline processes and responds; remains in PARTICIPANTS — **GAP** (entirely
   new; no covering test sends a message to a pipeline participant).

### ELITEA-2470 (7 granular steps — same flow, finer-grained assertions)
1. Navigate to the Chats section and create or open a conversation — **already-covered**
   (`navigate_to_chat()` / existing conversation-creation flow, unrelated to hash-search).
2. Verify the PARTICIPANTS panel shows no PIPELINES section initially — **GAP**, same as ELITEA-2208
   Step 1.
3. Type "#" in the message input and click on a pipeline from the "SEARCH RESULTS" dropdown — **already-
   covered (open/select/close) + GAP (must scope to a pipeline-type card specifically, per gap 1 above)**.
4. Verify the pipeline name appears in the message input field with # mention — **GAP, with a
   Clarification** (see below — it's the COMPOSER's active-participant chip, not literal text in the
   input; identical drift to ELITEA-2207/2469's own case-text wording for agents).
5. Verify the PARTICIPANTS panel now shows a PIPELINES section with the selected pipeline listed with
   name and icon — **GAP**, stricter than ELITEA-2208's Step 2 (only asks for the section to exist).
   Live-confirmed this session (screenshot): the popover row for an added pipeline shows an icon, the
   name ("AutoTest_Pipeline_probe_2020"), and a version control (rendered as the literal version name
   "base" this session — see Concrete Handles for why this differs from the agent family's "ver"/"vX.Y"
   shape).
6. Type a message and send it — **GAP**, same as ELITEA-2208 Step 3's send half.
7. Verify the pipeline processes and responds and remains in the PARTICIPANTS panel — **GAP**, same as
   ELITEA-2208 Step 3's response half.

## Expected Results
- Dropdown open + select-any-option + dropdown-closes: already proven by
  `test_add_participant_via_hash_search`, live-reconfirmed this session for a pipeline card specifically.
- Pipeline-type cards present with `pipeline` subtitle + icon in `#` results: already proven by
  `test_hash_search_shows_agents_and_pipelines_from_all_sources` (ELITEA-2206).
- No-PIPELINES-initially, pipeline-scoped selection, participant-panel-gains-PIPELINES-section,
  composer-shows-active-pipeline, message-reaches-pipeline, pipeline-responds,
  pipeline-remains-a-participant: all genuinely new assertions, ALL live-confirmed this session on
  `/chat/9082` (an existing conversation used as a stand-in for exploration; the shipped test uses the
  `conversation_id` fixture for a guaranteed-fresh, guaranteed-zero-pipelines starting state — see
  Automation Hints). No defect found on any of them — the live product does exactly what both cases' own
  intent describes, once the two Clarifications below are accounted for.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipelines exist in project | — | ambient DEV data | 10+ pipeline-type cards present in `#` results | already-covered |
| New conversation → no PIPELINES in PARTICIPANTS | PIPELINES section absent | **GAP** | `not is_participants_badge_visible(section="pipelines")` on a fresh `conversation_id` conversation | **extend — gap assertion** |
| Type '#' → dropdown appears | dropdown appears | covering `test_add_participant_via_hash_search` | `wait_for_hash_search_dropdown()` | already-covered |
| Click a PIPELINE (not any card) from dropdown | pipeline selected, dropdown closes | select/close: covering test; pipeline-type scoping: **GAP** | `get_hash_search_items()` filtered by `get_hash_search_item_subtitle()=="pipeline"`, then `.click()`; `not is_hash_search_dropdown_visible()` | **extend — gap assertion** |
| Pipeline name appears "in message field" with # mention | mention visible | **GAP + Clarification** | `is_agent_participant_in_composer(pipeline_name)` on `chat-switch-participant-button` (accessible name "Switch Pipeline"; NOT literal text in `chat-message-input` — see Clarification) | **extend — gap assertion, case-text drift noted** |
| PIPELINES section added to PARTICIPANTS | PIPELINES section + row visible | **GAP** | `is_participants_badge_visible(section="pipelines")` → True; `open_participants_popover(section="pipelines")` shows a row | **extend — gap assertion** |
| (ELITEA-2470 only) row shows name, version, icon | all 3 sub-elements present | **GAP** | scoped read inside the popover's participant row (name text, version-name text, `chat-participant-icon` element) | **extend — gap assertion, ELITEA-2470 only** |
| Type a message and send | message sent to the pipeline | **GAP** | `send_message("hello")` — sent-to-the-pipeline is established by construction (the pipeline is this conversation's only participant after Step 2's selection, per the `conversation_id` fixture's guaranteed-zero-participants start) and confirmed generically by the next row's message-count growth; no testid exists on the AI/pipeline response header to assert a literal "to \<Pipeline Name\>" attribution string (fix-round correction — see Axis 2, Clarification 3) | **extend — gap assertion** |
| Pipeline processes and responds | response rendered (real or a genuine execution-error card — see Clarification) | **GAP** | `wait_for_ai_response(initial_count)` — Copy button + non-transient content | **extend — gap assertion** |
| Pipeline remains in PARTICIPANTS after response | PIPELINES badge still shows the pipeline | **GAP** | `is_participants_badge_visible(section="pipelines")` still True post-response | **extend — gap assertion** |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- **Clarification 1, not a defect (reverse-masking guard)**: both cases say the pipeline name/mention
  appears "in the message input field" (ELITEA-2208 Step 2, ELITEA-2470 Steps 3-4). Live-confirmed this
  session (screenshot): after clicking a pipeline from the `#` dropdown, the message **input stays
  completely empty** (placeholder "Type your message..." unchanged) — the selected pipeline instead
  renders as a dedicated chip in the composer's control row (`chat-switch-participant-button`, accessible
  name "Switch Pipeline", labelled "AutoTest_Pipeline_probe_2020" this session). Byte-identical pattern to
  the ELITEA-2207/2469 AFS's own Clarification for agents — participant selection always produces a
  composer-level active-participant control, never literal inserted text in the message body. The case
  text's "message field" wording is the stale half; assert against the real composer chip, do not file as
  a defect.
- **Clarification 2, not a defect (reverse-masking guard, pipeline-specific)**: sending a message to a
  dynamically-selected ambient pipeline may produce a genuine **execution-error response** rather than a
  substantive answer, if that particular pipeline happens to have no configured nodes. Live-confirmed this
  session: the pipeline selected ("AutoTest_Pipeline_probe_2020", an ambient DEV-data probe pipeline)
  responded with "Pipeline has no nodes to execute. Please add at least one node to the pipeline before
  running it." — rendered as a normal, non-transient message list item, attributed to the pipeline
  ("AutoTest_Pipeline_probe_2020 to Message"), complete with a working Copy-to-clipboard button. This is a
  REAL response produced by the real system (the pipeline genuinely attempted execution and genuinely
  failed on its own empty-node precondition) — not a substitution, and not a product defect: an
  intentionally-empty probe pipeline correctly reporting it has nothing to run is correct behavior. Both
  cases' own expected result only asks that "the pipeline processes and responds" and "remains in
  PARTICIPANTS" — neither demands a specific response CONTENT. The shipped test must therefore assert
  generically (message count grows, response is attributed to the pipeline, PIPELINES badge persists)
  exactly as `test_add_agent_via_hash_search_joins_participants_and_responds` already does for agents —
  never assert on specific response text, since which ambient pipeline gets dynamically selected (and
  whether it happens to have nodes) is account-data-dependent and out of this test's control.
- **Source-confirmed mechanism (not re-derived from the case text alone)**: the participants popover's
  per-row version control for a PIPELINE shows the pipeline's own **version NAME** as a literal string
  (e.g. "base" this session) — NOT the "ver"/"vX.Y" auto-generated shape the agent family's own AFS
  documented. Confirmed both in the popover row (`AutoTest_Pipeline_probe_2020` + `base`, concatenated
  with no separator, same text-concatenation pattern as the agent row) and in the composer's own
  "version selector menu" button (text = "base" directly). This makes sense structurally: agent versions
  are numbered/auto-labelled, pipeline versions are user-named (e.g. "base", "prod", "v2-experimental") —
  the implementer must NOT reuse ELITEA-2207/2469's `re.match(r"v(er\b|\d)", ...)` regex for the pipeline
  row; assert only that a non-empty version-text remainder exists after the pipeline's name, not that it
  matches a "v..." shape.
- **Clarification 3, not a defect (fix-round correction, PR #1600 review)**: the "Type a message and send"
  Coverage Map row originally claimed the shipped test would assert "header shows 'to \<Pipeline Name\>'
  attribution" — copy-pasted verbatim from the sibling ELITEA-2207/2469 AFS's own row for the same shape
  (which itself never got implemented in that AFS's covering test either — confirmed by reading
  `test_add_agent_via_hash_search_joins_participants_and_responds`, PR #1599, already merged). Checked
  `EliteaUI/src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx` directly (fresh `git fetch origin`,
  both `main` and `automation/testids`): the response header's participant-name Typography and its "\<name\>
  to Message" text (visible in Axis 2, Clarification 2's screenshot) carry **no testid** — only
  `chat-message-item` (the whole-item container), `chat-answer-content`, and the four hover-action buttons
  do. Per this project's testid-only locator policy, there is no compliant way to assert that string today.
  Neither case's own text asks for it (ELITEA-2208 Step 3 / ELITEA-2470 Step 7 both say only "pipeline
  processes and responds; remains in PARTICIPANTS") — and because the `conversation_id` fixture guarantees
  the pipeline is the conversation's ONLY participant, the message-count-grew-by-2 + PIPELINES-badge-persists
  assertions the shipped test already makes are sufficient to establish it was that pipeline that responded.
  Corrected the Coverage Map row and Automation Hints wording to match what is actually (and honestly)
  asserted, rather than filing a `testid needed` request for a string neither case asks to see — a genuinely
  new testid on a shared response-header component is out of scope for this fix and would need its own
  case-driven justification if ever required.
- **Account-data hazard, precondition-relevant**: bare `/chat` navigation on this account hit a persistent
  loading-spinner overlay blocking the composer for >15s (65+ sidebar folders, same artifact the
  ELITEA-2207/2469 AFS already flagged) — worked around via an existing-conversation URL for live
  exploration; the shipped test's `conversation_id` fixture sidesteps this by construction (no sidebar-
  folder-list dependency).
- Console/network side-channel checked throughout this session's live exploration — 0 console errors
  before, during, or after the participant-add + send-message + remove-participant sequence.

## Cleanup
This session's exploration on `/chat/9082` (the same shared conversation reused for read-only/mutating
exploration by the ELITEA-2206 and ELITEA-2207/2469 analyses earlier this same session) DID mutate state —
a real pipeline participant was added and a real "hello" message + pipeline response (execution-error
card) were sent. Restored immediately after confirming the response: opened the PIPELINES popover, hovered
the `chat-participant-row-pipeline_8056_399` row, clicked "Remove pipeline", confirmed "Remove" in the
"Remove pipeline?" dialog — the `chat-participants-badge-pipelines` badge is confirmed gone from the DOM
afterward (matches `wait_for_participants_badge_absent()`'s documented "disappears from DOM at count 0"
contract, same mechanism already relied on by the agent family). The sent "hello" message + the pipeline's
error-response remain in `/chat/9082`'s history (message history is not retroactively deleted by removing
a participant — same as every other participant-removal precedent in this digest) — cosmetic only, does
not affect any other case's exploration of this conversation.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git grep`
on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (fetched fresh this
session) unless noted "pre-existing, page-object confirmed" (already relied on by multiple merged tests,
so provenance was established in earlier sessions this digest already records).

| Element | Testid / handle | Provenance | Notes |
|---|---|---|---|
| Message input | `chat-message-input` | on-`main` ✓ | Reused as-is — `ChatPage.message_input`. |
| Hash-search results container | `chat-hash-search-results-list` | on-`automation/testids` only (ELITEA-2206) | Reused verbatim, no changes needed for pipelines. |
| Per-card item | `chat-hash-search-item-{project_id}_{id}` (dynamic) | on-`automation/testids` only (ELITEA-2206) | `ChatPage.HASH_SEARCH_ITEM` + `get_hash_search_items()`/`get_hash_search_item()`, reused as-is. Live-confirmed this session: clicking a pipeline card selected it identically to the agent flow. |
| Per-card subtitle (`agent`/`pipeline`) | `{testId}-type` (dynamic) | on-`automation/testids` only (ELITEA-2206) | `ChatPage.HASH_SEARCH_ITEM_TYPE` + `get_hash_search_item_subtitle()` — THIS family filters by `== "pipeline"` (mirror of the agent family's `== "agent"` filter, same mechanism, no new testid). |
| Composer active-participant chip | `chat-switch-participant-button` | on-`automation/testids` ✓ (pre-existing, ELITEA-1736 rework, already relied on by merged tests) | `ChatPage.switch_participant_button` + `is_agent_participant_in_composer(pipeline_name)` — reused as-is, works for pipelines identically to agents (same physical element, its accessible name is "Switch Pipeline" when a pipeline is active vs "Switch Agent" for an agent — the testid is what the page object locates, so no branching needed). Live-confirmed this session: button text contains "AutoTest_Pipeline_probe_2020" after selection. |
| PIPELINES participants badge (collapsed) | `chat-participants-badge-pipelines` (`PARTICIPANTS_BADGE.format("pipelines")`) | on-`main` ✓ (pre-existing, ELITEA-1793 rework — `section: 'pipelines'` confirmed via `git grep` in `CollapsedPerticapantsList.jsx`) | `is_participants_badge_visible(section="pipelines")` / `wait_for_participants_badge_absent(section="pipelines")` — reused as-is for BOTH the "absent initially" and "present after select" and "still present after response" assertions. Accessible name observed this session: "Pipelines in this conversation". |
| PIPELINES badge clickable trigger | `chat-participants-badge-button` | on-`main` ✓ | `open_participants_popover(section="pipelines")` — reused as-is. |
| Participants popper container | `chat-participants-popper` | on-`main` ✓ | Reused as-is. |
| Per-participant row (expanded/popover) — PIPELINE | `chat-participant-row-{uniqueId}` where `uniqueId = pipeline_{pipeline_id}_{project_id}` (dynamic) | on-`main` ✓ (pre-existing, ELITEA-1793) — **prefix differs from the agent family's `application_` prefix, confirmed via `EliteaUI/src/[fsd]/features/chat/participants/lib/helpers/participants.helpers.js`'s `getChatParticipantUniqueId()`: a participant's `entity_name` resolves to `'pipeline'` (singular) whenever `entity_settings.agent_type === 'pipelines'`, distinct from the agent's `'application'`** | `ChatPage.PARTICIPANT_ROW` template is entity-agnostic (just formats `{uniqueId}`) — reusable as-is once the caller builds the correct `pipeline_{id}_{project_id}` string instead of `application_{id}_{project_id}`. Live-confirmed this session as `chat-participant-row-pipeline_8056_399` (Playwright-generated locator from a real hover interaction) for the selected pipeline. Row text includes the pipeline name + its version's literal name (e.g. "base" — see Axis 2 note); icon is the row's leading element via `chat-participant-icon` (see below), identical structural position to the agent row. |
| Participant icon (unconditional) | `chat-participant-icon` | on-`automation/testids` ✓ (pre-existing, ELITEA-2469, added on `EntityIcon.jsx`'s container `Box`) | `ChatPage.PARTICIPANT_ICON` + `get_participant_icon()` — reused as-is; renders unconditionally regardless of image-vs-fallback icon, same shared `EntityIcon`/`ParticipantItem.jsx` component backs both agent AND pipeline rows. |
| Remove-participant hover button | `chat-participant-remove-button` | on-`main` ✓ (pre-existing, ELITEA-1793) | Live-confirmed this session: accessible name is "Remove pipeline" when hovering a pipeline row (vs "Remove agent" for an agent row) — same physical testid, page-object-visible text differs per entity type automatically (component-driven, not a locator concern). Used only for this AFS's own Cleanup, not part of either case's asked-for assertions. |
| Remove-confirm dialog button | `delete-confirm-button` | on-`main` ✓ (pre-existing) | Confirms the "Remove pipeline?" dialog (text differs from the agent family's "Remove agent?", same physical control) — used only for Cleanup, not case-asked. |

**Provenance grep (this session, fresh `git fetch origin` first) — only handles this family newly relies
on that the agent family's own grep didn't already cover; everything else is pre-existing/already-relied-
upon per this digest's prior entries:**
```
chat-participants-badge-pipelines       main:YES (pre-existing, ELITEA-1793 — section: 'pipelines' in CollapsedPerticapantsList.jsx)
chat-hash-search-item-{}_{}-type        testids:YES (EliteaAI/EliteaUI@58d30f08, ELITEA-2206) main:no  [same testid as the agent family, reused]
chat-participant-icon                   testids:YES (EliteaAI/EliteaUI@dd44ce90, ELITEA-2469) main:no  [same testid as the agent family, reused]
```
No genuinely new testid is needed for this family — every handle either already exists on `main`, or was
already added by the ELITEA-2206/ELITEA-2207/2469 units earlier in this same batch/session. The only new
work is a **page-object generalization** (not a testid): `get_agent_participant_row()` /
`remove_agent_participant()` both hardcode the `application_` unique-id prefix and cannot resolve a
pipeline's row as-is — see Automation Hints for the additive fix the implementer needs to make (mirrors
the `agent_project_id` optional-parameter pattern the ELITEA-2207/2469 implementation already added to
the same methods for a different reason).

## Network Behavior
- Selecting a participant via `#` is client-side state (no network call at selection time) — same
  "no network call at keystroke/click time" pattern this digest already documents for the sibling
  attachment-chip, hash-search-open, and agent-select surfaces.
- Sending "hello" fires the normal chat-send request/WebSocket flow already covered by every other
  message-send test in this suite — no new network assertion needed; `wait_for_ai_response()` already
  waits past it via its own `wait_for_network()` call. This holds whether the pipeline returns a
  substantive answer or an execution-error card (Axis 2, Clarification 2) — both are real completed
  responses from the product's perspective, not a hung/pending state.

## Known Defects Found During Exploration
None. Live product behavior matches both cases' own intent on every gap assertion — the "message field"
wording and the response-content assumption are case-text clarifications (see Axis 2), not defects.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Implement as a NEW test method in `TestHashSearch` (`test_chat_interface.py`), directly beside
  `test_add_agent_via_hash_search_joins_participants_and_responds` — do not modify any existing method in
  this class (additive-only).
- **Use the `conversation_id` fixture** (fresh, API-seeded, zero participants) rather than an existing
  conversation — this is what makes the "no PIPELINES initially" assertion (both cases' own Step 1/2)
  trivially true and deterministic, and avoids the account-data-volume spinner hazard this session hit on
  bare `/chat` navigation (see Preconditions).
- **Family parameterization**: one test method (or `@pytest.mark.parametrize`) covering both TMS ids via
  two `@allure.issue` decorators, same pattern as ELITEA-2207/2469's family AFS. ELITEA-2470's extra
  name+version+icon row assertion (Coverage Map row 7) is the only per-case delta — implement it as an
  additional assertion block tagged for ELITEA-2470 specifically if using one shared method, or as a
  second thin test reusing the same setup if parametrizing.
- **Pipeline selection must filter by type**: do NOT reuse `get_hash_search_first_option()` as-is (it may
  resolve an agent). Iterate `get_hash_search_items()`, resolve each item's
  `get_hash_search_item_subtitle()`, and click the first one where it equals `"pipeline"` (lowercase —
  same drift this digest already documents for the agent family's "Pipeline"/"pipeline" case).
- **Page-object generalization needed (additive, mirrors the ELITEA-2207/2469 `agent_project_id`
  precedent)**: `get_agent_participant_row(popper, agent_id, ..., agent_project_id=None)` and
  `remove_agent_participant(agent_id, ...)` both build `unique_id = f"application_{agent_id}_{project_id}"`
  — hardcoded to the agent entity-name prefix. Neither resolves a pipeline participant's row
  (`pipeline_{id}_{project_id}`, see Concrete Handles). The implementer needs an additive fix — e.g. an
  optional `entity_type: str = "application"` parameter threaded into the `unique_id` construction on both
  methods (default unchanged, so every existing agent caller keeps identical behavior — Hard Rule 3's
  escape clause), OR two new thin sibling methods (`get_pipeline_participant_row()` /
  `remove_pipeline_participant()`) that share the row-resolution/hover/click mechanics via a common
  private helper. Either shape is acceptable; pick whichever keeps the existing agent callers byte-
  identical. Re-run the existing agent callers after the change to confirm no regression (same discipline
  the ELITEA-2207/2469 implementation already followed for its own additive change to these methods).
- **Version-text assertion must NOT reuse the agent family's regex.** `test_add_agent_via_hash_search_joins_participants_and_responds`
  asserts `re.match(r"v(er\b|\d)", version_text.lower())` on the popover row's post-name remainder — this
  assumes agent versions always render as "ver"/"vX.Y". Pipeline versions render their own NAME as a
  literal string (e.g. "base" this session) with no "v" prefix guarantee. Assert only that a non-empty
  version-text remainder exists after the pipeline's name (`len(version_text.strip()) > 0`), not that it
  matches any particular shape.
- Query string: bare `#` is sufficient (matches all participants; this session's first-page results
  already included multiple pipeline-type cards). A narrower query prefix is not required (unlike
  ELITEA-2206's fallback-to-`#pipe` path, which existed only because THAT test needed a pipeline result on
  a page that might not show one on page 1 — this family selects from whatever page-1 results already
  contain, same as the agent family's own approach).
- Wait strategy: reuse `wait_for_hash_search_dropdown()` for open; after clicking a pipeline card, wait on
  `is_participants_badge_visible(section="pipelines")` (condition wait, not a fixed sleep) before asserting
  the popover contents — the badge's appearance is the correct signal that the participant-add mutation
  has landed client-side.
- For the send+response step: capture `initial_count = get_message_count()` before `send_message("hello")`,
  then `wait_for_ai_response(initial_count)` — standard pattern already used by every other message-send
  test in this file. **Do not assert on the response's specific text** (Axis 2, Clarification 2) — assert
  only that the message count grew by 2 (sent + response) and that the PIPELINES badge still shows the
  pipeline afterward, exactly as the agent family's own Step 6 does. **Do NOT add a separate "response
  attributed to \<Pipeline Name\>" assertion** (Axis 2, Clarification 3, fix-round correction): the
  response header's participant-name text carries no testid in `ApplicationAnswer.jsx` (checked live,
  neither `main` nor `automation/testids`), neither case asks for it, and the `conversation_id` fixture's
  single-participant guarantee makes message-count growth + badge persistence sufficient on its own.
- Cleanup: whichever removal method the implementer builds (see the page-object generalization bullet
  above), call it in a `finally`/fixture-teardown style if the test seeds via UI-selection rather than an
  API precondition — optional, not a correctness requirement, since the `conversation_id` fixture deletes
  the entire conversation (participant and all) on teardown regardless. Same non-mandatory note as the
  agent family's own AFS.
