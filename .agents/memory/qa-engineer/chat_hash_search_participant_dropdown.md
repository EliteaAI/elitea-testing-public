---
name: Chat hash-search participant dropdown (#)
description: Existing TestHashSearch spec carries OLD TMS-id links (ELITEA-0498/0501), not ELITEA-2206 — found only by grepping by behaviour.
type: reference
---

## Surface
`#` typed in the chat composer opens a `SearchResultList.jsx` → shared
`NewParticipantList.jsx` panel listing **agents and pipelines** (current project
+ Agent Hub/public project, mixed in one result set — `useParticipants({
projectFilter: 'all', ... })`). Distinct from the `/`-slash-mention family
(toolkit/MCP participants) and the `~`-skill-mention family — three separate
mention triggers, three separate components, do not conflate.

## The TMS-id-mismatch trap
A merged, green spec already existed for this exact feature —
`automation/tests/ui/chat/test_chat_interface.py::TestHashSearch`
(`test_hash_search_participants` / `test_add_participant_via_hash_search`) — but
its `@allure.issue` links point at `ELITEA-0498`/`ELITEA-0501`, an OLDER TMS-id
lineage, not `ELITEA-2206` (the case that re-describes the same feature under a
new id). Grepping `test-specs/`/the suite BY TMS ID would silently miss this and
risk a duplicate `ready-for-automation` spec. Only found via `grep -rli
"hash.*search\|mention.*search"` (behaviour, not id) per `test-case-analysis`
§ 2b. **General lesson, already covered by this project's broader "search by
behaviour, not case id" doctrine — this is a concrete recurrence worth knowing
if you touch this specific surface, not a new principle.**

## Live-confirmed facts (2026-08-19, ELITEA-2206)
- Container heading DOM text: `"Search results"` (component `title` prop),
  sentence-case — any all-caps look is CSS `text-transform`, not the DOM text.
  Confirmed identical on both the bare `/chat` new-conversation composer
  (`NewConversationView.jsx`'s own `SearchResultList` call) and an existing
  conversation (`ChatBox.jsx`'s call, `/chat/9082`) — same component, same
  behavior, both call sites.
- Per-card subtitle text is **lowercase** `agent`/`pipeline`
  (`NewParticipantCard.jsx`'s `typeText`) — TMS case text says capitalized
  "Agent"/"Pipeline"; this is case-text drift (assert the real lowercase
  value), not a defect.
- Every card has an icon: either the participant's own custom `img "elitea"`
  (uploaded `icon_meta`) or a two-letter initials avatar fallback — never
  absent. Icon TYPE (agent-shaped vs pipeline-shaped SVG) is source-confirmed
  to exist at the `EntityTypeIcon` component level
  (`EliteaUI/src/components/EntityIcon.jsx`) but this card's actual fallback
  render path does NOT reliably reach that generic type-SVG for most items in
  live data (custom icon or initials avatar wins first) — don't assert
  icon-differs-by-type here without re-verifying; scope to "an icon element is
  present," same precedent as the ELITEA-2199 icon-genericity finding on the
  sibling attachment-chip surface.
- `"Public"` chip = Agent Hub/public-project source; its absence = current
  project. Both present in ONE bare-`#` result set (not two separate queries) —
  proves "all sources represented" directly.
- Click-away (`ClickAwayListener`) closes the dropdown independent of
  selection — confirmed by clicking the sidebar "Chats" nav button while the
  dropdown was open, without clicking any result card.
- **Gotcha**: on a genuinely blank/new-conversation composer, the open
  dropdown's own subtree can intercept pointer events over the
  greeting/welcome-text area ("subtree intercepts pointer events" — Playwright
  actionability error) if you try to click-away onto that specific region. Use
  a target clearly outside the dropdown's bounding box (sidebar nav, message
  list of an existing conversation) instead.

## Testid gap (as of this pass)
`SearchResultList.jsx` does NOT forward `containerTestId`/`getItemTestId` to
`NewParticipantList.jsx` at all (unlike `SlashSuggestionList.jsx`, which
already wires `slash-mention-list`/`slash-mention-item-{}_{}` through the
SAME shared component). Zero testids exist on this surface today — both
`chat-hash-search-results-list` (container) and
`chat-hash-search-item-{project_id}_{id}` (dynamic item) are `needs-adding`,
scoped to the `ChatBox.jsx` call site only (the existing-conversation flow the
merged tests + this extension exercise — leave `NewConversationView.jsx`'s own
call site untouched per canon #511).
