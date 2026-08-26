# Agent-hub surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent Hub / Catalog
surface (`/elitea-catalog`). Not a substitute for execution — verify a handle
as you use it. One writer at a time; last confirmed by: qa-engineer (analyst
slot), ELITEA-2364, 2026-08-10.

## Conversation-starter tiles — TWO real testid gaps (ELITEA-2369)
- **Modal's starter list items** (`AgentConversationStarterItem.jsx`, inside
  `catalog-agent-modal-chat-starters-section`) carry ZERO testid — confirmed
  via source, only `onClick`/hover wiring. Feature-scoped (agent-hub only),
  not shared — a hardcoded static testid on the item root is fine. Not yet
  added as of this dispatch.
- **Chat-area starter tiles** (`ChatConversationStarters.jsx` → the SHARED
  `EllipsisTextWithTooltip` in `src/components/ConversationStarters.jsx`,
  also used by `NewConversationView.jsx`'s pre-chat composer) carry ZERO
  testid — confirmed via source AND live (had to fall back to a raw
  `.MuiBox-root.css-vjd7yg` CSS-class locator during this exploration, NOT
  an acceptable shipped locator). Being shared, the fix is a caller-supplied
  `testId` prop, not a hardcode inside `ConversationStarters.jsx` — wire only
  `ChatConversationStarters.jsx`'s call site for now (canon #511: only the
  code path a test actually executes); `NewConversationView.jsx`'s own
  call site is a DIFFERENT case's job.
  **[CORRECTION, ELITEA-2369 implementer fix round 2 — the bullet above names
  the WRONG call site, do not follow it]** This original bullet has it
  backwards. ELITEA-2369's own live flow (Catalog → modal → "Start Chat" →
  brand-new conversation, before any message is sent) renders its starter
  tiles via `src/pages/NewChat/NewConversationView.jsx` — which imports
  `EllipsisTextWithTooltip` directly and does NOT go through
  `ChatConversationStarters.jsx` at all. `ChatConversationStarters.jsx` is a
  DIFFERENT call site, consumed only by
  `src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx`'s embedded/
  agent-participant chat surface — a not-yet-analysed flow ELITEA-2369 never
  reaches. Per canon #511 ("touches" = the code path THIS test actually
  executes), the shipped `testId="chat-conversation-starter-tile"` prop is
  wired at `NewConversationView.jsx`'s call site ONLY — confirmed via a fresh
  `git fetch origin` + `git grep "chat-conversation-starter-tile"
  origin/automation/testids -- src/`, exactly one hit
  (`NewConversationView.jsx:1020`); `ChatConversationStarters.jsx`'s call site
  remains unwired, same as this bullet intended, just for the opposite of the
  reason it states. (Full history: the AFS's own "wrong component identified"
  amendment + the fix-round-1 "leftover orphan wiring" amendment in
  `l3_agent-hub-start-conversation-with-starters_ELITEA-2369.md` § Known
  Defects — a first implementer pass wired BOTH call sites simultaneously by
  mistake, review caught the orphan, fix round 1 reverted it down to the one
  correct site.) Any future case that DOES analyse the `ChatBox.jsx` embedded
  surface will need its own testid wiring at `ChatConversationStarters.jsx`'s
  call site — that work is still undone, this correction only fixes which
  site is ALREADY wired.
- **Clicking a starter tile POPULATES the composer, does not auto-send**
  (`onSendConversationStarter` → `chatInput.current.setValue(starter)`) —
  confirmed live: input field receives the full starter text, send button
  transitions from absent to enabled, nothing is sent until the user clicks
  Send. Matches case text for both ELITEA-2369 (modal-starters agent) and any
  future sibling exercising the same click.
- **Starter tiles do NOT disappear immediately after a populate-click** — they
  only vanish once `isTheUserChattingNow` flips true (i.e. once an actual
  send + AI-streaming response starts), and REAPPEAR once streaming finishes
  (confirmed live: visible before send, hidden during the ~38s "thinking"
  window, visible again after the reply completed). Not a defect — no case
  text requires either hidden or visible at the populate-click step, but
  future analysts on this surface: don't assert either transient state as if
  it were guaranteed, assert only what your own case's text requires.
- **"API Testing Buddy" (id 34)** is a confirmed live example of an agent
  WITH conversation starters + a configured welcome message (4 starters,
  matches the case-family's own "e.g." example verbatim) — pairs with the
  existing "Business Analyst"/"User Story Creator" no-starters examples
  already in this digest, for any future sibling needing either precondition.

## Catalog → chat continuation (Start Chat → send → reply) — all handles pre-existing (ELITEA-2368)
- Clicking "Start Chat" in the modal redirects to `/chat`, then to
  `/chat/{conversation_id}?name=...` once the first message auto-names the
  conversation. `ChatPage` already covers the ENTIRE chat-side continuation —
  confirmed live, zero new testids needed: `new_conversation_greeting`
  (`chat-new-conversation-greeting`, "Hello, {user}! What can I do for you
  today?"), `switch_participant_button` (`chat-switch-participant-button`,
  the composer's agent-name chip) + `chat_version_selector_trigger`
  (`chat-version-selector-trigger`, the version chip — **two SEPARATE
  adjacent elements, not one combined "AgentName vX.X" chip** — a dedicated
  sibling case, [ELITEA-2362/#870](https://github.com/EliteaAI/elitea-testing-public/issues/870),
  exists specifically to explore this and is not yet analysed; future
  analyst there: this is your target, don't re-discover the split),
  `expand_participants_panel_via_toggle()` + `get_participant_row_by_name()`
  (expanded Participants panel shows an "Agents" heading + the participant
  row), `message_input`/`send_button`/`is_send_button_enabled()`,
  `answer_thought_accordion` ("Thought for N secs"), `wait_for_ai_response()`,
  `is_conversation_in_group(conv_id, "today")` (sidebar grouping),
  `wait_for_context_budget_panel()` + `wait_for_context_budget_messages_count()`
  (Context Budget — **absent entirely pre-send**, appears only once ≥1
  message sent, confirmed live: went from no indicator at all to "2%" /
  "239 / 10 000 tokens" / Messages: "2" / Summaries: "0" after one
  exchange). Cleanup precedent (ELITEA-2075): parse `conv_id` from
  `page.url` (`r"/chat/(\d+)"`), delete via
  `ConversationAPI.delete_conversation(conv_id)` in a `finally` block.

## Category filter-rail behavior: single-select vs. multi-select (ELITEA-2352 / ELITEA-2353)
- **Single-select behavior (ELITEA-2352)**: clicking one category chip filters to that category only — all other category sections disappear. Clicking a different chip replaces the filter (prior chip deselects).
- **Multi-select accumulation behavior (ELITEA-2353, confirmed live 2026-08-10)**: clicking category chips accumulates filters — clicking "Business Analyst" filters to that category, then clicking "Elitea" while Business Analyst remains selected shows **both** categories' sections simultaneously. Both chips show `data-selected="true"` at the same time. This is automatic in `AgentsTab.jsx`'s `selectedTagNames` state machine (toggle logic: `includes(tag) ? remove(tag) : add(tag)`), not a defect or special behavior. A third click on either selected chip removes it from the set (toggle off).
- **Verified chip state handling**: `data-selected="true"/"false"` attribute correctly flips on each click, persists across subsequent clicks on OTHER chips, and does not leak focus-state (unlike DOM `[active]` marker which Playwright incorrectly surfaces) — safe to assert on.
- **Section header positioning**: after multi-select filters, sections appear in the order of their categories in the filter-rail (left to right), not alphabetical or discovery order. Business Analyst appears before Elitea in the filtered output because Business Analyst appears before Elitea in the category-rail chip list.

## "Business Analyst" (id 31) ALSO satisfies the "no starters/no welcome message" precondition (ELITEA-2368)
- Not just "User Story Creator" (id 172, used by ELITEA-2356/2365's
  explorations) — "Business Analyst" (id 31, 8 likes, the literal "e.g."
  example named in the ELITEA-2350..2370+ case family's own text for THIS
  specific sub-case) confirmed live to also show "No predefined chat
  starters" / "No welcome message set" in its preview modal. Any
  case needing a no-starters agent example that must ALSO match its own
  case text's literal "e.g." name can check that agent directly rather than
  assuming a substitution note is required — confirmed generic across at
  least these two agents.

## "My Liked" section reload icon — SAME drift as #1212, confirmed on this category too (ELITEA-2365)
- ELITEA-2365's case text claims a reload/refresh (↻) icon renders next to
  the "My Liked" section header. **Confirmed absent**, same as #1212's
  "Business Analyst" instance — `AgentCategorySection.jsx` is the SAME shared
  component for every category (including "My Liked"), and its
  `headerContainer` renders only a `Typography`, zero icon elements,
  regardless of which category is being rendered. **Do not re-file** — this
  is the identical component/root-cause #1212 already tracks; cite it.
- **Cross-tab My-Liked sync works, via a full page reload** (the only actual
  refresh mechanism on this surface — no manual UI trigger exists anywhere,
  confirmed both here and by #1212). Confirmed live, two tabs sharing one
  `BrowserContext` (`page.context.new_page()`): liking an agent in Tab B
  (`POST .../social/like/... => 201`) is NOT reflected in Tab A's already-
  rendered "My Liked" section until Tab A does its own fresh fetch — a full
  `page.goto()`/`reload_and_wait()` triggers that fetch and the agent then
  appears with the matching count.
- **The "My Liked" filter-rail chip's selected state does NOT survive a full
  page reload** — it is client-only UI state, no URL param. Confirmed live:
  after `page.goto('/elitea-catalog')`, the chip reset to unselected and the
  unfiltered default view rendered; `click_category_filter_chip("My Liked")`
  had to be called again post-reload before re-reading the section. Any test
  that reloads mid-flow while relying on a category filter must re-select it.

## ⚠️ PROVENANCE CORRECTION (2026-08-06, ELITEA-2363) — prior "on-main ✓" claims for this surface's core testids are WRONG as of today

A fresh `git fetch origin` + `git grep` against `origin/main` (this session) shows
**`catalog-page-heading`, `catalog-search-input`, and `catalog-agent-card-{id}` do
NOT exist on `origin/main`** — `EliteaCatalog.jsx` on `main` has no `data-testid` on
the heading or the search `TextField` at all, and a `git grep` for
`catalog-agent-card-` against `origin/main -- src/` returns zero hits. All three
ARE present on `origin/automation/testids`. This directly contradicts the
ELITEA-2354 AFS's Concrete Handles table, which lists all three as
"on-main ✓ (pre-existing, ELITEA-2075)". Whether that claim was wrong when made or
`main` was reset/force-pushed since is out of scope to root-cause here — **any
future analyst/lead/closure-record on this surface: re-verify with a fresh fetch
before citing ANY of this surface's testids as "on-main"; do not propagate the
ELITEA-2354 file's claim forward.** This digest's own per-testid provenance notes
below (marked "pre-existing, ELITEA-2075/2075") should likewise be treated as
NEEDING RE-VERIFICATION against a fresh fetch, not trusted as-is.

## Catalog search bar (`catalog-search-input`) — real-time, debounced, no clear button (ELITEA-2363)
- Typing alone filters the list — confirmed live AND via source
  (`EliteaCatalog.jsx`'s `TextField.onChange` is the ONLY wiring; no
  `onKeyDown`/Enter handler, no adjacent submit/search-icon button in the JSX).
  Debounce is 300ms (`AgentsTab.jsx`'s `useDebounceValue(query, 300)`) — exactly
  ONE `GET .../public_applications/prompt_lib/?query=<term>&...` fires per typing
  burst, regardless of how many characters were typed, ~300ms after the last
  keystroke. `AgentHubPage.search(query)` already encodes this wait correctly
  (`press_sequentially` + `expect_response`) — reuse it, don't reinvent.
- Match is **case-insensitive substring**, server-side (query sent lowercase
  matched titles with capitalized "Story").
- **No clear/X button exists** — confirmed absent via source (`EliteaCatalog.jsx`'s
  `TextField` has no `InputProps` endAdornment at all, plain MUI `TextField`).
  "Clear the search field" (case text, this family) means select-all + Backspace,
  NOT `fill("")` (per `.claude/rules/mui-patterns.md`, `fill()` skips the React
  `onChange`, so the debounced `query` state — and the rendered list — would never
  update). Clearing re-fires the identical 3-request pattern seen on initial page
  mount (bulk `query=`, Trending, My Liked) — confirmed live, restores the exact
  original card/category set.
- Category sections with zero matches are removed from the DOM entirely (not
  hidden/greyed) when filtered — confirmed live (5 of 7 categories vanished when
  filtering on "story", all 7 returned on clear).
- No testid needed for search/filter/clear — `catalog-search-input` +
  `AGENT_CARD_PREFIX` already cover everything this behavior needs. One NEW page-
  object method is needed though: `clear_search()` (select-all+Backspace,
  network-response-aware) — didn't exist before this dispatch.

## "No results" empty state — NO testids, confirmed live (ELITEA-2367)
- **"No agents found" / "Try adjusting your search terms" messages** (`Category.NoResultsMessage.jsx`, renders via `AgentsTab.jsx`'s `noResultsTitle`/`noResultsDescription` props when `results === []`). **Both messages are SPAN elements with MuiTypography classes only; neither carries a testid** — confirmed via live DOM inspection 2026-08-10 (ELITEA-2367 exploration).
- Elements: `<span class="MuiTypography-root MuiTypography-headingMedium ...">No agents found</span>` + `<span class="MuiTypography-root MuiTypography-bodyMedium ...">Try adjusting your search terms</span>`, both children of `<div class="MuiBox-root css-cxi1bf">`.
- **Layout consistency confirmed:** when search matches zero agents, the empty-state messages render in place of the agent-card grid, while the page heading, search input, tabs, and category filter rail all remain visible and functional (not hidden/disabled/collapsed).
- **Workaround for automation:** use `page.get_by_text("No agents found")` / `page.get_by_text("Try adjusting your search terms")` as fallback locators. **Future enhancement:** add `data-testid="catalog-no-results-title"` and `catalog-no-results-description` to the component (one-line addition to each SPAN) so tests can use stable testid selectors.
- No console errors during empty-state render; no 4xx/5xx network responses when search matches zero agents.

## Agent detail modal (`AgentModal.jsx`) — mostly untested, only 3 of ~10 fields have testids
- Opened by clicking any Catalog agent card; content-ready signal is the
  underlying `GET /api/v2/elitea_core/public_application/prompt_lib/{id}`
  (singular) request resolving — reuse `AgentHubPage.open_agent_by_name()`,
  which already waits on this exact response.
- **Pre-existing testids (on-main, ELITEA-2075):** `catalog-agent-modal-agent-name`,
  `catalog-agent-modal-show-instructions-link`, `catalog-agent-modal-start-chat-button`.
  Also pre-existing (unrelated dispatch): `agent-hub-modal-menu-button` (the
  overflow "..." menu — Export/Fork/Share; "Share" performs the copy-link action).
- **Zero testids (confirmed via source + live), needed for ELITEA-2356:**
  agent icon (`EntityIcon` at `AgentModal.jsx:222-227` — the component
  already accepts a `data-testid` prop, just needs it passed), owner name
  (`AgentModal.jsx:190-195` Typography), the like button (`AgentHubLike` at
  `AgentModal.jsx:198-201` threads NO `testId` at all, unlike the card-list
  like button which does — same `Like.jsx` component, `data-liked` auto-derives
  once a `testId` is threaded), close "x" button (`AgentModal.jsx:208-216`,
  `aria-label="close"` only), description (`AgentModal.jsx:236-241`), and both
  content sections' containers (`AgentConversationStarters.jsx` /
  `AgentWelcomeMessage.jsx`). Full recommended names + line numbers:
  `l3_agent-hub-open-agent-detail-modal_ELITEA-2356.md` § Concrete Handles.
- **Case-text drift (recurring, already tracked, cite don't re-file):** case
  families calling this modal say "CONVERSATION STARTERS" / "Start
  conversation" — live product reads **"CHAT STARTERS"** / **"Start Chat"**
  (`AgentConversationStarters.jsx` / `AgentModal.jsx:267`). Filed as
  [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042),
  which explicitly names ELITEA-2356 (and ELITEA-2357/2358/2359/2360/2361/2362/
  2368/2369) as affected siblings — **every future case that opens this
  modal will hit the same drift; cite #1042, don't re-file.**
- **New this dispatch:** "copy link icon" case-text also drifts — there is no
  standalone copy-link icon; it's the `agent-hub-modal-menu-button` overflow
  menu's "Share" item. Filed as
  [EliteaAI/elitea-testing-public#1218](https://github.com/EliteaAI/elitea-testing-public/issues/1218)
  (also names ELITEA-2359/#867 as an affected sibling — the case that
  actually exercises the copy-link action).
- Welcome Message section header is "Welcome Message" (title case, NOT
  all-caps) while the adjacent Chat Starters header IS all-caps — a real,
  confirmed live inconsistency in the product's own copy, not itself worth a
  separate ticket (noted here so a future analyst doesn't re-litigate it).
- Agent descriptions are free-text, author-authored data (not app-generated
  copy) — a typo in one agent's description (confirmed live: "User Story
  Creator" reads "Thuis agent is responsible...") is live product DATA, not a
  UI defect. Assert description non-empty/visible, never the literal string.

## Like/unlike an agent card — testids IMPLEMENTED, shared `Like.jsx` component
- Heart icon + count on every agent card is the shared `src/components/Like.jsx`
  (also used by the data-table widget and `Card.jsx` for pipelines) via
  `AgentHubLike.jsx` → `AgentCard.jsx`. **Testids now implemented** (confirmed
  live ELITEA-2355 exploration, 2026-08-10): `catalog-agent-like-button-{application.id}`
  testid is present on the button element; the attribute is a caller-supplied
  `testId` prop threaded from `AgentCard.jsx` into the shared `Like.jsx`
  component (same discipline as `CategoryRail.jsx`'s chip prop). Status on `main`:
  requires fresh `git fetch origin` + `git grep` to verify (ELITEA-2354 made a
  false claim about presence on main; re-verify before citing).
- "Liked" state **now has an accessible signal**: `data-liked="true"/"false"`
  attribute on the like button (same precedent as ELITEA-2352's chip
  `data-selected`, implemented alongside the testid). Confirmed live: attribute
  flips correctly on click, persists across page reload, and the heart icon
  renders as filled (`HeartActiveIcon`) when `data-liked="true"`, unfilled
  (`HeartIcon`) when `data-liked="false"`. Full detail (including unlike flow):
  `l3_agent-hub-unlike-agent-from-list-view_ELITEA-2355.md` (ELITEA-2355 AFS, this dispatch).
- Endpoints: `POST /api/v2/social/like/prompt_lib/{project_id}/application/{id}`
  → `201` (like); `DELETE` same path → `204` (unlike). Update is optimistic
  client-side (no re-fetch awaited).
- **Known defect (filed, MINOR, non-blocking)**: every like AND unlike click
  fires a Redux "non-serializable value" `console.error`
  (`agentHub/updateApplicationInCategories` action payload carries a raw
  function). Root cause: `useAgentHubData.hooks.js:330` dispatches a closure;
  `slices/agentHub.js:42-49`'s reducer invokes it. Dev-console-only noise, the
  like/unlike flow itself is correct. Filed as
  [EliteaAI/elitea-testing-public#1215](https://github.com/EliteaAI/elitea-testing-public/issues/1215).
  **Future analysts on like/unlike-adjacent cases (ELITEA-2355, 2364, 2365):
  expect the same console error and cite #1215 rather than re-discovering it.**
- **Like counts are mutable shared product data, not a stable fixture** — a
  case's named "e.g." example agent (e.g. "AI Platform Design Advisor") will
  NOT reliably show a specific like count session-to-session; automation must
  dynamically discover a card matching the needed starting state (e.g. "any
  card with 0 likes") rather than hardcoding the example name.
- **Default post-refresh view only renders the top-6 "Trending" cards** (sorted
  by likes desc) — a freshly-liked LOW-count agent is not guaranteed to appear
  there after a reload. Use the Catalog search box (`catalog-search-input`) to
  re-locate a specific agent by name after a refresh, rather than assuming it's
  still in the default unfiltered view.
- **Any case that likes an agent MUST unlike it again as cleanup** — like state
  is shared, cross-session product data that sibling cases in this family (My
  Liked filter, reload-button, unlike) depend on as a clean baseline.

## Category filter-rail chip "selected" state — NO accessible signal existed pre-ELITEA-2352
- Before this dispatch, the filter-rail `Chip` (`CategoryRail.jsx`) had **zero**
  accessible/stable way to detect "selected" state: no `aria-selected`, no
  `aria-pressed`, no `data-*` state attribute — only a computed CSS
  background-color style difference (`styles.selectedChip` vs `styles.chip`).
- **Trap: Playwright's own accessibility-snapshot `[active]` marker on the chip
  is PURE DOM-FOCUS, not the app's selection state** — confirmed live by
  clicking a second chip (focus + `[active]` moved to it, even though the
  first-clicked category remained the actually-filtered one) and by clicking
  an unrelated element like the search input (`[active]` disappeared from the
  still-selected chip). Never assert on `[active]`/focus for this component.
- Fixed this dispatch: added `data-selected="true"/"false"` directly on the
  chip (`EliteaAI/EliteaUI@9b93f67c`, on `automation/testids`, not yet on
  `main`), driven by the same `selectedCategories.includes(category)`
  expression already used for styling. Confirmed live: flips on click,
  persists correctly across focus changes (unlike the `[active]` false
  signal). Combined locator: `[data-testid="catalog-agent-category-filter-chip-{slug}"][data-selected="true"]`.

## Category filtering is actually multi-select at the app-state level (not explored further)
- `handleTagSelect` in `AgentsTab.jsx` toggles `selectedTagNames` as an array
  (add/remove), and `useGroupedCategories`'s own `selectedCategories` follows
  suit — clicking a SECOND chip after a first ADDS its section to the content
  list rather than replacing it (confirmed live: after Business Analyst then
  DevOps, both sections rendered simultaneously). ELITEA-2352 only exercises
  the single-click case, so this wasn't pursued further — relevant to a future
  "filter by multiple categories" sibling case (see below).

## "Reload category items" icon — DOES NOT EXIST (case-text drift, 2nd instance in this family)
- ELITEA-2352's case text (and title) claims a "reload category items" icon
  renders next to the filtered category's section header. **Confirmed absent**
  both visually and via source: `AgentCategorySection.jsx`'s `headerContainer`
  renders only a `Typography` title, and a full-file grep for reload/refresh
  icon components (`RestartAlt`/`SyncIcon`/`ReplayIcon`/`Autorenew`/
  `RefreshIcon`/`CachedIcon`) under `src/[fsd]/features/agent-hub` and
  `src/[fsd]/shared/ui/category` returns 0 hits. The page's only refresh is a
  fully automatic, throttled background refresh (`useCatalogAutoRefresh`) —
  no manual UI trigger anywhere. Filed as
  [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212).
  **Future analysts in this family: expect the same claim to recur** across
  sibling cases (like #1208's "Agent HUB" header text did) — cite #1212 rather
  than re-discovering it.

## Page identity / naming (case-text drift, recurring across the ELITEA-2350..2370+ family)
- The TMS "Agent Hub" family (ELITEA-2350 through at least ELITEA-2370, ~20
  sibling cases filed as GitHub issues #858-#878) all use case text calling
  the surface "Agent HUB". The LIVE product calls it "Catalog" everywhere:
  sidebar nav item text, `<title>` (`"ELITEA Catalog - {project}"` — includes
  the active project name, useful as a free project-context assertion), and
  the page heading `data-testid="catalog-page-heading"` = **"Welcome to
  ELITEA Catalog!"**. `AgentHub`/`/agents-hub` is only a legacy redirect
  source in `routes.js`, never a rendered label. Filed as
  [EliteaAI/elitea-testing-public#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208)
  (ELITEA-2350); the SAME drift was independently noted (but not filed) in
  the ELITEA-2075 AFS. **Every sibling case in this family will hit the same
  drift** — future analysts: cite #1208 rather than re-discovering/re-filing.
- Route: `/elitea-catalog`. Two tabs at the top (`role=tab`, MUI `BaseTabs`):
  "Agents" (default/selected) and "Skills" — these are the ONLY actual `tab`
  role elements on the page (the case family's "category filter tabs"
  wording refers to a DIFFERENT thing — see below).

## Category filter rail vs. category content-list headings — two different UI elements, same word "category"
- **Content-list headings** (inside the scrollable left column, one per
  rendered category section, e.g. "Trending" above a grid of cards):
  `catalog-category-heading-{slug}` — pre-existing testid,
  `AgentCategorySection.jsx`, already wired into `AgentHubPage.CATEGORY_HEADING`
  / `is_category_section_visible()`. Slug function (confirmed via source):
  `String(category).toLowerCase().replace(/[^a-z0-9]+/g, '-')` — e.g.
  "Business Analyst" → `business-analyst`, "Knowledge & Documentation" →
  `knowledge-documentation` (space + `&` collapse to one hyphen).
- **Filter-rail chips** (right-hand column, `CategoryRail.jsx`, shared between
  `AgentsTab`/`SkillsTab` via `CatalogBody.jsx`): clickable MUI `Chip`s split
  into "Featured" (Trending, My Liked — static constants
  `AgentHubConstants.TRENDING_CATEGORY`/`MY_LIKED_CATEGORY`) and "Categories"
  (Business Analyst, DevOps, Development, Elitea, Epam, Knowledge &
  Documentation, Project Management, Quality Assurance, Other — dynamic, from
  the backend tag list). **Confirmed live, 2026-08-05: this exact 11-item
  list matches the ELITEA-2350 case text verbatim** — no drift here, unlike
  the header text. **ZERO `data-testid`/`testId` anywhere in
  `CategoryRail.jsx`** (confirmed via full-file read +
  `git grep -c "data-testid\|testId"` = 0 on both `origin/main` and
  `origin/automation/testids`) — this is a real, not-yet-added testid gap.
  Because the component is shared across two features (agent-hub, skill-hub),
  it needs a caller-supplied `testId`/`<part>TestId` prop per
  `.agents/testing.md`'s shared-component rule, NOT a hardcoded testid inside
  `CategoryRail.jsx` itself. Recommended shape (not yet implemented as of
  this digest entry): a `chipTestIdPrefix` prop threaded
  `AgentsTab`/`SkillsTab` → `CatalogBody` → `CategoryRail`, each call site
  supplying its own feature-scoped prefix (e.g. agent-hub's own call site:
  `"catalog-agent-category-filter-chip"` → renders
  `catalog-agent-category-filter-chip-{slug}` per chip, same slugify fn as
  the content-list headings for consistency).

## Agent cards
- `catalog-agent-card-{application.id}` — pre-existing dynamic testid,
  `AgentCard.jsx`, already wired into `AgentHubPage.AGENT_CARD_PREFIX` /
  `get_agent_card()`. Default view (no search/filter): 6 cards render under
  "Trending" plus a "Show more" expander (confirmed live, this environment).

## Project context
- Sidebar `project-selector-trigger-combobox` (pre-existing testid, dup'd
  across `admin_users_page.py`/`analytics_page.py`/`chat_page.py`) reads
  "Project: Private" by default for `${TEST_USER}` on localhost — no explicit
  switch needed for "Private project" cases in this family. `ChatPage`
  already exposes `get_selected_project_text()` / `switch_project()` — reuse
  by composition rather than adding a 4th duplicate `LocatorDescriptor`.
  The page `<title>` (`"ELITEA Catalog - {project name}"`) is a free,
  zero-interaction second confirmation of the active project context.

## "My Liked" filter behavior — confirms like/unlike in filtered view removes agents (ELITEA-2364)
- Clicking the "My Liked" filter chip (`catalog-agent-category-filter-chip-my-liked`) activates `data-selected="true"` and isolates the "My Liked" section as the sole rendered category.
- Agents in the "My Liked" view show `data-liked="true"` on their like buttons.
- **Unliking an agent while in the "My Liked" view removes it from the list immediately** (optimistic client-side update, `DELETE .../social/like/... => 204`). The agent's card and like button are no longer present in the DOM after the unlike click — not hidden/greyed, fully removed. Confirmed live, session 2026-08-10: agent ID 16 appeared in My Liked after a like (count 7→8, `data-liked=true`), then disappeared from the My Liked view after an unlike click (card query returned null).
- **The "My Liked" chip selection is client-only state and does NOT survive a full page reload** — same as documented above for the multi-select filter behavior. After `page.goto()` or `reload()`, the chip resets to unselected and the unfiltered default view renders; any test that reloads while relying on the "My Liked" filter must re-select it post-reload (confirmed live during ELITEA-2365's cross-tab exploration).
- Like counts in "My Liked" view correctly reflect the global like count — no stale/cached values observed.

## Known defects (already tracked elsewhere, not re-filed)
- #1043 — Catalog agent-preview modal's "Start Chat" button has no
  `disabled={isFetching}` guard; race condition. Only relevant to cases that
  open an agent's preview modal / start a chat (not this page-load-only
  family member).
- #1016 — Catalog category "Show more" permanently locks to collapse after
  first click. Only relevant to cases that interact with "Show more".

## Clicking a starter tile INSIDE the modal — direct navigate + pre-populate, no "Start Chat" needed (ELITEA-2093)
- **Resolved/added during ELITEA-2093 implementation:** `AgentModal.jsx`'s
  `onSelectStarter` handler (bound to each `AgentConversationStarterItem`'s
  `onClick`, confirmed via source) fires `onStartConversation(starter)()`
  (dispatches `setSelectedAgentInfo({agent, starter})`, then
  `navigate({pathname: Chat, search: 'create=1'})`) AND `onClose()`
  synchronously off a SINGLE click on a starter item — materially different
  from the `catalog-agent-modal-start-chat-button` flow (ELITEA-2368/2369):
  no separate "Start Chat" click, no #1043-style race window to guard with
  `page.wait_for_timeout(1000)`. Confirmed live: clicking a starter item
  closed the modal and navigated to `/chat` with the composer already
  pre-populated, off one click, for "Assistant for ELITEA Documentation"
  (application id 16, category "Elitea", 3 configured starters: "Help me
  configure Jira toolkit?", "Tell me about Elitea", "Can I use Azure dev
  ops repo through Elitea").
- **Why this click is naturally safe from the #1043 class of race**: unlike
  the "Start Chat" button (always rendered, clickable before `agentDetails`
  commits), the starter items themselves only render once
  `agentDetails?.version_details?.conversation_starters` has data — so any
  caller that already waited for a starter item to be visible (to read/count
  them, per this case's own earlier step) is by construction past the same
  async gap #1043 has to work around separately. New page-object method
  `AgentHubPage.click_modal_starter_item(match_text)` added this dispatch
  (filters `MODAL_STARTER_ITEM` by `has_text`, same idiom as
  `ChatPage.click_chat_starter_tile()`) — zero new testid, reuses the
  pre-existing `catalog-agent-modal-starter-item`.
- **Conversation is NOT created by the starter click** — only by the
  subsequent Send. The click only performs a client-side navigation with
  `?create=1`; `POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}`
  fires on Send, same as the ELITEA-2368/2369 siblings' "Start Chat" flow.
- **Auto-naming resolved near-instantly, no observable "Naming" placeholder
  window** in this live run (message "Tell me about Elitea" → sidebar title
  "Tell about Elitea", a word dropped, not a defect — case text only
  requires "resolves to an auto-generated title"). `ChatPage.wait_for_naming_label_to_resolve()`
  is no-op-safe for this (its `naming_label.count() > 0` guard skips the wait
  entirely when the placeholder never rendered) — always call it before
  reading the sidebar title regardless of whether the placeholder was
  observed, per the existing `test_conversation_management.py` Step-6
  precedent (assert title is non-empty and doesn't contain "Naming", never
  assert the placeholder WAS visible first).

## Sibling family (not yet analysed as of this entry)
ELITEA-2351 ("Team project" variant of this exact case — differs from
ELITEA-2350 only in which project is active, a DATA difference per the
family-vs-separate test) plus ~18 more behavioral cases (filter by
category/multiple categories, like/unlike, open/close modal, search,
start-conversation flows, etc. — GitHub issues #859-#878). A future batch
covering the whole family should re-check whether ELITEA-2350/2351 belong in
one parameterized family AFS (project name as the only variable) rather than
two near-identical specs — this dispatch analysed ELITEA-2350 alone, not as
a cluster, so no family-AFS merge was performed here.
