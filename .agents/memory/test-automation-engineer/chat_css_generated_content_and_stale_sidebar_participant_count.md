---
name: Chat CSS-generated badge counts and stale sidebar participant metadata
description: Two distinct read-strategy traps found while finishing ELITEA-2167 (invite-users add/cancel/close) — a badge count rendered as CSS ::after content (invisible to any DOM-text read) and a sidebar list item's participant-derived fields that don't live-update after Invite Users + first Send.
type: feedback
---

## 1. Collapsed-participants badge count is CSS generated content, not DOM text

`CollapsedPerticapantsList.jsx`'s `collapsedTriggerButton(count, ...)` style sets the
visible number via `'&::after': { content: `"${count}"` }` on the trigger `IconButton`
(`chat-participants-badge-button` testid) — for BOTH the entity sections (agents/
pipelines/toolkits/mcp) and the dedicated `UsersParticipantDropdown` (users section).
The button's real DOM subtree contains only an SVG icon; `text_content()` returns `''`
and any `.filter(has_text=...)` / `get_by_text(...)` on it will NEVER match, silently
timing out watching a value that was never in the DOM.

**Fix:** read `window.getComputedStyle(el, '::after').content` via `.evaluate()` (one-shot,
strip surrounding quotes) or `page.wait_for_function()` (condition-based wait) — this is
the one sanctioned case where reading past the DOM into computed style is required, not
a `page.evaluate()`-to-bypass-a-check violation (Hard Rule 2's "Using page.evaluate() to
bypass a CSS/DOM check the AC requires" — this is the OPPOSITE: using it because the AC's
own observable IS CSS-rendered, not present as DOM text at all).

`ChatPage.get_participants_badge_count()` / `wait_for_participants_badge_count()` (added
this case) implement both forms — reuse before adding a third variant.

## 2. Popover section heading text is real title-case DOM text; the visible uppercase is CSS-only

`UsersParticipantDropdown`'s heading `<Typography sx={styles.title}>Users</Typography>`
(same for the entity-section variant, heading = `{entityType}`) uses
`textTransform: 'uppercase'` in its `sx` — a pure CSS rendering effect. The actual DOM
`textContent` is title-case (`"Users"`, `"Agents"`, etc.), NOT `"USERS"`/`"AGENTS"`. An
AFS/case-text description of what a human SAW on screen ("shows a USERS heading") is a
visual description, not a DOM-text spec — assert the real DOM string, not what the
CSS transform makes it look like. This is exactly the reverse-masking-guard "case text
is a hypothesis, live product is ground truth" pattern, just at the CSS-vs-DOM level
rather than product-behavior level.

## 3. Post-Send `page.url` read races the SPA router's URL commit

Right after the participants-persist network response resolves (the last "queued
users flushed" call), `page.url` can still read the pre-navigation bare `/chat` for a
beat — the router commits `/chat/{id}` only after a couple more calls in the sequence
(`.../select_conversation/...` per this app's own Network Behavior). Extracting the new
conversation id from `page.url` synchronously right after `expect_response()` resolves
is a race. Fix: `page.wait_for_url(re.compile(r"/chat/\d+"), timeout=...)` BEFORE reading
`page.url` — applies to any "first Send creates + navigates" flow, not just this case
(also fixed in the negative-control single-owner-conversation helper in the same file).

## 4. Multi-user icon wrapper: hidden-when-false is a real state, not "not yet visible"

`ConversationItem.jsx`'s `conversation-multi-user-icon` wrapper carries
`data-has-icon={conversationType === 'private_with_users' || conversationType === 'public'}`
and is ALWAYS in the DOM — but is CSS-hidden (zero-content) when `data-has-icon="false"`.
A `.wait_for(state="visible")` on it times out FOREVER for the negative-control case
(confirmed via the Playwright call log itself: `24 × locator resolved to hidden <div
data-has-icon="false" ...>` — it never becomes "visible" because there's genuinely
nothing to show). Switching naively to `state="attached"` fixes the negative case but
BREAKS the positive one: the attribute settles asynchronously right after a conversation
is freshly created/populated, so reading immediately on DOM attachment can catch a
transient pre-update "false". The correct fix for a boolean DOM ATTRIBUTE whose value
settles asynchronously in EITHER direction is `expect(locator).to_have_attribute(name,
"true"/"false", timeout=...)` — Playwright's own auto-retrying assertion, already the
established idiom elsewhere in this repo (`artifacts_page.py`, `mcp_form_page.py`,
`pipeline_detail_page.py`) but not yet used in `chat_page.py` before this case (had to add
`from playwright.sync_api import Page, expect`). `ChatPage.wait_for_conversation_multi_user_icon(id,
expected_has_icon, timeout)` is the new method — prefer it over hand-rolling a
`wait_for(state=...)` + manual attribute read for any future boolean-attribute check.

## 5. Sidebar conversation-list items cache participant-derived fields; they don't live-update

`ConversationItem.jsx`'s `getConversationType()` derives from the `conversation` prop's
own `users_count`/`is_private` fields — sourced from whatever fetch populated the
sidebar's conversation-list cache. Adding participants via Invite Users + the first Send
does NOT push a live update into that cached list entry (confirmed: `data-has-icon`
stayed `"false"` for 10s+ after Send, well after the participants badge/popover already
correctly showed the new count) — a full list refetch (`page.reload()` +
`wait_for_page_load()` + `wait_for_conversations_to_load()`) is required to see the
accurate value. Same STALENESS CLASS as the already-documented
`chat_created_conversation_stuck_active_after_navigate_away.md` (#692) — different field,
same "sidebar list item doesn't live-track a state change" shape, same established fix
already used in `test_open_conversation_today_section.py` Step 2. Any future
assertion reading a conversation-list-item's DERIVED (not directly-fetched) field right
after a mutating action should default to reload-before-read, not assume live sync.

## Process note: recognize this class of bug fast

All five of the above are READ-STRATEGY bugs (wrong wait state / wrong text source /
race / stale cache), not product defects — each cost one debug cycle because the FIRST
symptom (a `Locator.wait_for` timeout or a plain `AssertionError`) looks identical to a
real product bug until you check: (a) is the value CSS-generated vs DOM text — `evaluate`
+ `getComputedStyle`; (b) is the assertion's literal string a human's visual description
vs the actual DOM text; (c) does the URL/attribute change lag other confirmed signals —
add an explicit wait for THAT signal, don't assume adjacency; (d) is the "visible" wait
appropriate when the negative case is legitimately hidden-by-design — check the call
log's "resolved to hidden" detail, it tells you outright; (e) is the field being read
DERIVED/cached on a list item vs directly fetched — sidebar list items in this app are
known to cache participant-derived state.
