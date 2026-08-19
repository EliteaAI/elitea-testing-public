# Test Case: Chat – Mentions with # – Verify Typing # Displays All Available Agents and Pipelines

## Metadata
- **TMS ID**: ELITEA-2206
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend;
  Private project, `projectId=399`)
- **User set**: `${TEST_USER}` — localhost: no login needed, `VITE_DEV_TOKEN` auto-auths
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w14`, 2026-08-19
- **Status**: **extend-existing**
- **surface_key**: `chat-hash-search-participants`

## Preconditions
- User is logged in to the Elitea platform.
- Agents and pipelines exist in the project (this DEV account has 60+ agents/pipelines, mixed
  current-project and Agent Hub/public-project sourced — ambient data, no seeding needed).

## Extension target — Rule-6 partial overlap

**Covering spec:** `automation/tests/ui/chat/test_chat_interface.py`, class `TestHashSearch`, methods
`test_hash_search_participants` (line 412) and `test_add_participant_via_hash_search` (line 434).
Merged to `origin/automation/base` (confirmed present this session via a fresh `git fetch origin`;
`git log origin/automation/base -1 -- automation/tests/ui/chat/test_chat_interface.py` →
`8981927cc`, contains this class).

**Behavioural-overlap argument.** The covering tests already prove the dropdown OPENS on `#`
(`test_hash_search_participants`, typing `#agent`) and that selecting a result item CLOSES it
(`test_add_participant_via_hash_search`, step 3: `assert not chat.is_hash_search_dropdown_visible()`
after clicking the first option). That satisfies ELITEA-2206's own Step 1 and half of Step 5
(a close mechanism exists), live-reconfirmed this session on both the bare `/chat` composer and an
existing conversation (`/chat/9082`) — identical "Search results" panel, 0 console errors either way.

**Gap: three assertions ELITEA-2206's own steps ask for that neither covering test makes**, all
live-confirmed this session (Playwright MCP, existing conversation `/chat/9082` "Analyze these
files" — the same scope the covering tests use via their `conversation_id` fixture):

1. **Steps 2-3 — per-item subtitle + icon, split by type.** Neither covering test inspects a single
   result card's contents; `test_add_participant_via_hash_search` only grabs "the first option" via
   `get_hash_search_first_option()`'s best-effort DOM heuristic and clicks it — it never asserts what
   the card actually shows. Live-confirmed via accessibility snapshot on `/chat/9082` typing bare
   `#`: every card renders a name + a type label directly under it, and an icon (either a custom
   `img "elitea"` for participants with an uploaded icon, or a two-letter initials avatar for those
   without — always present, never absent) — e.g. `"AA" / agent`, `"Agent testing skills" / agent`
   (img icon), `"AutoTest_Pipeline_probe_2020" / pipeline` (initials fallback,
   `[data-testid]`-less today). **Case-text wording clarification, not a defect**: the case says
   "'Agent' subtitle" / "'Pipeline' subtitle" (capitalized); the live DOM text is lowercase
   `agent`/`pipeline` (`NewParticipantCard.jsx`'s `typeText` — `participant.agent_type === 'pipeline'
   ? 'pipeline' : 'agent'`). Assert the real lowercase value (reverse-masking guard) — a
   case-insensitive/exact-lowercase match, not the capitalized wording. Icon TYPE differentiation
   (agent-shaped vs pipeline-shaped icon) is source-confirmed to exist at the `EntityTypeIcon`
   component level (`EliteaUI/src/components/EntityIcon.jsx`, switch on `type`) but this card's
   actual render path falls back to a plain initials avatar or the participant's own custom
   `icon_meta` image for MOST items in this account's data (not the generic type SVG) — scope the
   gap assertion to "an icon/avatar element is present for every card" (structural), not "the icon
   differs by type", consistent with the ELITEA-2199 precedent in this feature's digest (icon
   type-genericity was investigated and found not to hold for the sibling attachment-chip surface;
   asserting an unconfirmed type-specific icon here would risk the same false claim).
2. **Step 4 — mixed sources (current project + Agent Hub).** Neither covering test asserts anything
   about WHERE results come from. Live-confirmed: typing bare `#` on `/chat/9082` returns a mix of
   items carrying a `"Public"` chip (Agent Hub / public-project sourced — e.g. "Business Analyst",
   "Code Review Assistant") and items with NO such chip (current-project-only — e.g. "autotest GH
   Issue Bot 601356", "AutoTest_Pipeline_probe_2020"). Both are present in the same result set on the
   same query, proving "all sources represented" as the case's Step 4 asks. `SearchResultList.jsx`
   confirms this at the query level: `useParticipants({ projectFilter: 'all', ... })` — `'all'` is
   the literal source-scope value, not project-only.
3. **Step 5 — press elsewhere (click-away) closes the dropdown, WITHOUT selecting anything.** The
   covering `test_add_participant_via_hash_search` only proves closure via SELECTING an option
   (`first_option.click()`); it never proves the `ClickAwayListener` close path the case's own Step 5
   describes ("Press elsewhere to close dropdown" — no selection made). Live-confirmed this session:
   typed `#` on `/chat/9082`, then clicked the sidebar "Chats" nav button (definitely outside the
   dropdown) — `page.get_by_text("Search results")` transitioned to hidden, confirming the
   `ClickAwayListener onClose` path fires independently of selection.

All three gaps are additive assertions on the SAME `#`-typed dropdown the covering tests already
open — no new interaction primitive, no near-rewrite. Classified `extend-existing`, not
`ready-for-automation`.

## Test Steps (source case, reproduced for traceability; only the gap steps need new code)
1. Open a conversation and type '#' in the message input — 'SEARCH RESULTS' dropdown appears.
   **already-covered** (covering `test_hash_search_participants`/`test_add_participant_via_hash_search`
   both prove the dropdown opens; live-reconfirmed this session the visible container heading text is
   `"Search results"`, not literally all-caps — CSS likely uppercases it visually, DOM text is
   sentence-case; assert against the real DOM text).
2. Verify agents shown with 'Agent' subtitle and agent icons — Agent items visible. **GAP** — add a
   per-card subtitle-text (`agent`, lowercase) + icon-presence assertion, scoped to cards whose
   subtitle is `agent`.
3. Verify pipelines shown with 'Pipeline' subtitle and pipeline icons — Pipeline items visible.
   **GAP** — same shape as Step 2, scoped to cards whose subtitle is `pipeline`. Requires the result
   set to contain at least one pipeline (ambient data on this account already does —
   `AutoTest_Pipeline_probe_2020`, `debug_router_manual`, several `test-pipeline` entries confirmed
   live; if the implementer's account/query lacks one, search a query term that surfaces one, e.g.
   `#pipe`).
4. Verify list includes agents from current project and Agent Hub — All sources represented. **GAP**
   — add an assertion that the result set contains at least one `"Public"`-labeled card (Agent
   Hub/public project) AND at least one card without that label (current project).
5. Press elsewhere to close dropdown — Dropdown closes. **GAP (click-away half only)** — add a
   click-away-without-selecting assertion; the select-and-close half is already covered.

## Expected Results
- Step 1 already proven by both covering tests, re-confirmed live this session on both the bare
  `/chat` composer and an existing conversation.
- Steps 2, 3, 4, and the click-away half of Step 5 are genuinely new assertions, all live-confirmed
  this session; the live product matches the case's own intent on every one (case-text capitalization
  wording aside, per the clarification above) — no defect found.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agents/pipelines exist in project | — | ambient DEV data | 60+ agents/pipelines present, mixed sources | already-covered |
| 1. Type '#' → 'SEARCH RESULTS' dropdown appears | dropdown appears | covering `test_hash_search_participants`/`test_add_participant_via_hash_search` | `wait_for_hash_search_dropdown()` | already-covered |
| 2. Agents shown with 'Agent' subtitle + icon | agent items visible | **GAP** — new assertion needed | per-card subtitle text == `"agent"` + icon element present, scoped to `chat-hash-search-item-*` cards | **extend — gap assertion** |
| 3. Pipelines shown with 'Pipeline' subtitle + icon | pipeline items visible | **GAP** — new assertion needed | per-card subtitle text == `"pipeline"` + icon element present | **extend — gap assertion** |
| 4. List includes current-project AND Agent Hub sources | all sources represented | **GAP** — new assertion needed | ≥1 card WITH `"Public"` label AND ≥1 card WITHOUT it, same result set | **extend — gap assertion** |
| 5. Press elsewhere → dropdown closes | dropdown closes | select-close half: covering `test_add_participant_via_hash_search`; click-away half: **GAP** | click outside the dropdown container (no selection) → `is_hash_search_dropdown_visible()` false | **partially already-covered / extend — click-away gap** |
| Expected Final State / Pass-Fail: "'#' shows all available agents and pipelines from all sources" | — | Step 1 + 4 new gap assertions | as above | already-covered + extend |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Case-text capitalization drift ("Agent"/"Pipeline" subtitle vs live lowercase `agent`/`pipeline`) —
  *added: reverse-masking guard, live product is correct/self-consistent, case wording is the stale
  half; assert the real value, do not file as a defect.*
- Source-mix mechanism (`SearchResultList.jsx`'s `useParticipants({ projectFilter: 'all', ... })`) —
  *added: source-confirmed to explain WHY both current-project and Agent-Hub items appear in one
  result set, not assumed from the case's own wording alone.*
- Console/network side-channel checked throughout this session's live exploration (both the bare
  `/chat` composer and `/chat/9082`) — 0 console errors either time.

## Cleanup
No mutation performed — every step this session was read-only (typed `#`, observed the dropdown,
clicked a nav button to close it; never selected/added a participant). `/chat/9082` left in its
pre-existing state.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via
`git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone
(fetched fresh this session).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Message input (type `#` into this) | `chat-message-input` | on-`main` ✓ | Reused as-is — `ChatPage.message_input`, existing field. |
| Hash-search results container | `chat-hash-search-results-list` (**new**) | **needs-adding** | The `#`-search feature is wired via `SearchResultList.jsx` → shared `NewParticipantList.jsx` — the SAME shared component `SlashSuggestionList.jsx` already threads `containerTestId="slash-mention-list"` / `getItemTestId={...}` through, per this project's "shared components never hardcode feature-scoped testids" rule (`.agents/testing.md` § Locator policy). `SearchResultList.jsx` currently does NOT accept or forward those two props at all — add them (mirror `SlashSuggestionList.jsx`'s own wiring exactly) and pass the literal strings at the `ChatBox.jsx` call site (`~line 2697`, the `<SearchResultList ... />` JSX for the `enableMentions && query` branch — this is the call site both covering tests exercise via `conversation_id`/existing-conversation navigation; do NOT also touch the `NewConversationView.jsx` call site, which no test in this family exercises — canon ruling #511, "referenced = called on the test's actual code path"). |
| Per-card item (agent or pipeline) | `chat-hash-search-item-{project_id}_{id}` (**new**, dynamic) | **needs-adding** | Same wiring as above, `getItemTestId={participant => \`chat-hash-search-item-${participant.project_id}_${participant.id}\`}` — exact naming mirror of `SLASH_MENTION_ITEM`'s existing `slash-mention-item-{}_{}"` pattern (`ChatPage.py`). Add as a class-level UPPER_CASE template constant, e.g. `HASH_SEARCH_ITEM = '[data-testid="chat-hash-search-item-{}_{}"]'`, per `.agents/testing.md` § Locator policy's dynamic-testid shape — never an inline f-string in a method body. |
| Card subtitle text (`agent`/`pipeline`) | none needed | n/a | Read via `.locator(self.HASH_SEARCH_ITEM.format(project_id, id)).locator("p, span").last.text_content()` scoped INSIDE the already-testid'd item card (`NewParticipantCard.jsx`'s `bodyContainer` renders name then type as the two Typography children in fixed order) — a scoped read off a real testid parent, not a free-floating handle. Same idiom as the existing `chat-attachment-chip-{i}` → structural-child-read precedent in this digest's ELITEA-2196 section. |
| Card icon (img or initials avatar) | none needed | n/a | Structural presence check scoped inside the item card (`item.locator("img, svg, .MuiAvatar-root").count() > 0` or equivalent) — same "no new testid needed for a structurally-verifiable child" precedent as the file-type icon in ELITEA-2196's section. Do NOT assert icon TYPE differs between agent/pipeline cards — not confirmed to hold on this card's actual fallback-avatar render path (see Extension-target discussion above). |
| "Public" source chip | none needed | n/a | `NewParticipantCard.jsx` renders a `Typography` with literal text `"Public"` when `participant.project_id == PUBLIC_PROJECT_ID` — read via `.locator(self.HASH_SEARCH_ITEM.format(...)).get_by_text("Public")` scoped inside the item card, same structural-read idiom as above. No dedicated testid needed for a single-purpose, always-same-text label scoped under an already-testid'd parent. |
| Existing covering-test raw handles (`wait_for_hash_search_dropdown()`, `get_hash_search_first_option()`, `is_hash_search_dropdown_visible()`) | none — pre-existing tech debt | on-`main` ✓ (raw, not testid) | Reused as-is for the "dropdown open/close" mechanics this extension does NOT re-implement — **do not** silently upgrade these to the new testid mid-extension; the covering tests' own methods stay untouched (Hard Rule: additive-only extension). A future dedicated pass may migrate them once the new container/item testids exist. |

**Provenance grep (this session, fresh `git fetch origin` first):**
```
chat-message-input                      main:YES
chat-hash-search-results-list           main:no   testids:no   (needs-adding this unit)
chat-hash-search-item-{}_{}             main:no   testids:no   (needs-adding this unit)
```

## Network Behavior
- Typing `#` and reading the result list is pure client-side rendering triggered by a debounced
  `useParticipants` query — the same "no network call at keystroke time" pattern already documented
  for the sibling attachment-chip surface in this digest; the actual participant-list fetch is a
  background GET that both covering tests already wait past implicitly via `wait_for_hash_search_dropdown()`.
  No new network assertion needed for any of the three gap steps (all are pure DOM/text reads on the
  already-rendered dropdown).

## Known Defects Found During Exploration
None. Live product behavior matches the case's own intent on all three gap assertions (per-type
subtitle+icon presence, mixed-source result set, click-away close) — case-text capitalization is a
wording clarification, not a defect (see Extension-target discussion above).

**Separate finding, NOT part of this case's scope (flagged for the lead, not filed as a defect
against THIS case):** both covering tests (`test_hash_search_participants`,
`test_add_participant_via_hash_search`) wrap their own core dropdown-appears wait in
`try/except PlaywrightTimeoutError: pytest.skip(...)` — a genuine timeout on the feature's own core
behavior currently reports SKIPPED, not FAILED. This is pre-existing merged code, not introduced or
touched by this extension, and out of scope to fix here (Hard Rule: additive-only extension) — noted
for a future dedicated hardening pass.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Implement as a NEW test method in `TestHashSearch` (`test_chat_interface.py`) — do not modify
  `test_hash_search_participants` or `test_add_participant_via_hash_search`'s existing bodies, only
  ADD a new method that types bare `#` (not `#agent`/`#query` — the case's own Step 1 wording is a
  bare `#`) on an existing conversation (reuse the `conversation_id` fixture, same as both covering
  tests) and asserts the three gaps.
- **Testid work is a precondition, not optional** — `chat-hash-search-results-list` /
  `chat-hash-search-item-{}_{}` don't exist yet on either `main` or `automation/testids`. Wire via
  `add-data-testid`: (1) add `containerTestId`/`getItemTestId` props to `SearchResultList.jsx`,
  forwarding them into its `<NewParticipantList ... />` call (mirror `RecommendationList.jsx`'s or
  `SlashSuggestionList.jsx`'s existing wiring exactly); (2) pass the literal testid strings at
  `ChatBox.jsx`'s `<SearchResultList ... />` call site only (`~line 2697`). Commit + push
  `automation/testids` per the standard flow.
- Query string: use a bare `#` (matches ALL participants, both agent and pipeline, both sources) —
  do NOT scope to `#agent` (that would only surface agent-type results and defeat the pipeline/source
  gap assertions). Use `chat.message_input.press_sequentially("#", delay=50)` — `fill()` will NOT
  trigger the keydown-based hash-search feature (same MUI/React-onChange gotcha the covering test's
  own docstring already documents: *"The hash search feature detects '#' via keydown events"*).
- For Step 3 (pipeline card), if the default bare-`#` result page (first N by relevance/pagination)
  happens not to surface a pipeline card, iterate the rendered cards' subtitle text to find one, or
  fall back to a query prefix known to surface pipelines (`#pipe` — confirmed live this session to
  return `AutoTest_Pipeline_probe_2020` among others) for that specific sub-assertion only; keep the
  Step 4 (mixed-sources) and Step 5 (click-away) assertions on the original bare-`#` query.
- Click-away target for Step 5: click any element clearly outside the dropdown's bounding box (this
  session used the sidebar "Chats" nav button) — avoid clicking the greeting/welcome text area on a
  brand-new blank composer, which this session found the still-open dropdown itself intercepts
  (`subtree intercepts pointer events`) since it visually overlaps that region; an existing
  conversation's message-list area is a safe click-away target and avoids the overlap entirely.
- Wait strategy: reuse the covering tests' own `wait_for_hash_search_dropdown()`/
  `is_hash_search_dropdown_visible()` for open/close mechanics; add a condition-based wait (element
  count changes on the new item testid, or `page.wait_for_timeout` is NOT acceptable per
  `.agents/testing.md`) rather than a fixed sleep for "results settled" if pagination/loading
  skeletons are still resolving when the new assertions run.
