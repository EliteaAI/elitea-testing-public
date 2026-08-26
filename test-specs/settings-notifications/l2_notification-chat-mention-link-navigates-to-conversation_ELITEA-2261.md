# Test Case: Clicking a chat-mention notification link navigates to the correct conversation

## Metadata
- **TMS ID**: ELITEA-2261
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2261/2262/2263, 2026-08-26
- **Status**: ready-for-automation
- **Case-text clarification filed**: EliteaAI/elitea-testing-public#1786 (step 6 — see § Known Defects)

## Preconditions
- User is logged in (`auth_state` fixture; localhost bypasses Keycloak via `VITE_DEV_TOKEN`).
- The user's notification history contains **at least one `chat_user_mentioned`
  notification whose conversation still exists**. Confirmed live 2026-08-26: 12 mention
  notifications; conversations `5883` ("Hello") and `4165` ("HI Chat") resolve, `7839` and
  `4205` are gone. This is real DEV history, not fixture data — the spec discovers a live
  target at runtime (step 2) and **fails loudly** if none exists. Never skip.

## Test Data
### reuse-existing (read-only)
- `${TEST_USER}`'s existing notification history. The whole flow is GET-only: clicking the
  link neither mutates the notification nor the conversation. No cleanup.
- **Nothing is hardcoded** — the notification id, the conversation id and the message id all
  come from the product's own list response / rendered `href`.

## Test Steps

1. **Case step 1** — navigate to `${BASE_URL}/settings/notifications`
   (`NotificationCenterPage.navigate_and_get_rows()`).
   - **Verify**: table body visible; page title starts with `Settings: Notifications`;
     page-info matches `^(\d+) - (\d+) of (\d+)$`.

2. **Case step 2** — find a chat-mention notification with a **live** target.
   - Filter the list with the product's own search field (`search_notifications(...)`) using
     the mention template token `mentioned you in` — a server-side filter, 600 ms debounce,
     ≥ 2 chars (`MIN_SEARCH_LENGTH`). Live 2026-08-26: `"1 - 12 of 12"`.
   - For each rendered row, read the row's link `href` and parse `conversation=<id>` from it.
     Determine liveness through the **product's own conversation read**
     (`GET /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}` —
     200 = live, 400 = gone) using the suite's cookie-auth API client, and take the FIRST
     (newest) row that is live.
   - **Verify (precondition)**: such a row exists — otherwise fail loudly naming exactly what
     is missing ("no chat_user_mentioned notification points at a surviving conversation").
   - Record `notification_id`, `conversation_id`, `message_id`, `link_text`.
   - Live 2026-08-26: notification `109487`, text `"Levon Dadayan mentioned you in Hello"`,
     link text `"Hello"`, `conversation=5883`, `message_id=53fa2b40-…`.
   - **Verify (link contract, deterministic for ANY mention row)**: the rendered `href`
     equals
     `{origin}/{notification.project_id}/chat?conversation={meta.conversation_id}&message_id={meta.message_id}`
     — i.e. every component is the notification's OWN metadata, and the link carries
     `target="_blank"` + `rel="noopener noreferrer"`.

3. **Case step 3** — click the link inside the notification text
   (`notification-message-link`, scoped to `notification_id`'s row).
   - The anchor is `target="_blank"` ⇒ it opens a **NEW TAB**. Wrap the click in
     `page.context().expect_page()` / `page.expect_popup()` and hold the popup.
   - **Verify**: exactly one new page was opened.

4. **Case step 4** — verify the new tab lands on the referenced conversation.
   - Wait for the SPA's project switch to finish: the popup's path becomes `/chat/<digits>`
     (framework wait on `page.wait_for_url` / a `expect(...).to_have_url` regex — never a sleep).
     The `/{projectId}` prefix is consumed by the project switcher and the query string is
     rewritten by the app.
   - **Verify**: popup path == `/chat/{conversation_id}` **or**
     `/{notification.project_id}/chat/{conversation_id}` — AMENDED during ELITEA-2261
     implementation (2026-08-26): the switcher consumes the `/{projectId}` segment only
     when a switch is actually required. Project 406 ≠ the selected 399 here, so it IS
     consumed; ELITEA-2263's notification lives in the already-selected project 399 and
     its segment SURVIVES (`/399/artifacts?bucket=…`). Both shapes name the same page of
     the same project; the spec accepts exactly those two and nothing else.
   - Live 2026-08-26: `http://localhost:5173/chat/5883?name=Hello`, title
     `"Chat: Hello - Bugs & Features"` (project 406 — the notification's own project, not the
     user's personal one).

5. **Case step 5** — verify the chat opens without a "not found" error.
   - **Verify** (both, they are the observed discriminators):
     - `alert-dialog-content` has count 0 in the popup — the "Conversation not found"
       `AlertDialog` is absent;
     - `chat-message-list` is visible and `chat-message-item` count ≥ 1 — the conversation's
       real messages rendered.
   - **Verify (side channel)**: no `4xx/5xx` response on
     `/api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}` and no
     console errors attributable to it.
   - Live contrast captured for the dead conversation `7839`: `alert-dialog-content` PRESENT
     ("The conversation you are looking for does not exist in your project or you don't have
     access to it."), `chat-message-list` absent, `400` on the conversation GET. That is the
     failure shape this step must catch.

6. **Case step 6 — REWRITTEN, case-text drift (clarification #1786).** The case says
   "navigate back — verify the notification is now in read state". The product does **not**
   mark a notification read when its link is clicked, and because the link opens a new tab
   there is no back-navigation at all.
   - Close the popup, return to the notifications tab, reload, re-apply the search.
   - **Verify (the live contract)**: the row's `notification-message-typography` computed
     colour is **unchanged** from the pre-click reading — clicking a link is not a read
     transition. Read the colour via
     `locator.evaluate("el => window.getComputedStyle(el).color")`
     (`NotificationCenterPage.get_row_message_color`).
   - Live 2026-08-26: `rgb(255, 255, 255)` before and after (unread both times).
   - Assert the **difference/sameness**, never the literal rgb token.

## Expected Results
- The in-message link's `href` is built entirely from the notification's own `meta`
  (`conversation_id`, `message_id`) and `project_id`.
- Clicking it opens a new tab on `/chat/{conversation_id}` in the notification's project
  (the `/{project_id}` segment survives when that project is already selected — see step 4).
- The conversation renders its message list; no "Conversation not found" dialog.
- The notification's read state is unchanged by the click.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | step 1 | covered |
| Step 1 — Navigate to Settings → Notifications | page/section loads | `navigate_and_get_rows()` | step 1 | covered |
| Step 2 — Find a "[User] mentioned you in [Chat link]" notification | produces expected UI state | search + live-target discovery | step 2 | covered (decomposed: search, parse href, liveness probe) |
| Step 3 — Click the Chat link in the notification text | control responds | click on `notification-message-link` | step 3 | covered |
| Step 4 — Browser navigates to the referenced chat conversation | condition holds | popup URL == `/chat/{conversation_id}` or `/{project_id}/chat/{conversation_id}` (amended) | step 4 | covered (new TAB, not in-tab navigation) |
| Step 5 — Chat opens without a "not found" error | condition holds | `alert-dialog-content` count 0 + `chat-message-list` visible | step 5 | covered |
| Step 6 — Navigate back, notification now in read state | page loads / state read | read state re-read after return | step 6 | **clarification** — product does not mark read on link click; asserted as unchanged. #1786 |
| Expected final state | notification read | — | — | **clarification** (same as step 6) |

### Axis 2 — observables asserted beyond the case
| Extra observable | Why grounded |
|---|---|
| `href` equals the meta-derived URL exactly | The case says "the CORRECT conversation" — the href is where correctness is decided, and it is deterministic for any mention row even when the target has since been deleted. |
| `target="_blank"` + `rel="noopener noreferrer"` | The new-tab behaviour is the reason the case's step-4/6 wording does not apply; pinning it prevents a silent switch to in-tab navigation that would make the spec's popup wait hang. |
| No 4xx on the conversation GET | The "not found" dialog is downstream of a `400`; asserting the API too distinguishes a UI regression from a data-gone precondition. |
| No console errors on the popup | Standard side-channel check (`.agents/testing.md`). |

## Cleanup
None — the whole flow is read-only. Close the popup tab; clear the search field.

## Concrete Handles (discovered during exploration)

| Element | Primary handle | Provenance | Notes |
|---|---|---|---|
| Notification row (repeats) | `[data-testid="notification-row"]` | on-main ✓ | scope per row via the checkbox id, existing `NotificationCenterPage` idiom |
| Row checkbox (dynamic, row key) | `[data-testid="notification-checkbox-{id}"]` | on-`automation/testids` only | `NOTIFICATION_ROW_CHECKBOX` |
| Row message cell | `[data-testid="notification-message-text"]` | on-main ✓ | |
| Row message typography (colour) | `[data-testid="notification-message-typography"]` | on-`automation/testids` only (EliteaAI/EliteaUI@e0d98f4a) | `ROW_MESSAGE_TYPOGRAPHY` |
| **In-message link** | `[data-testid="notification-message-link"]` | **ADDED during implementation** — on-`automation/testids` only (EliteaAI/EliteaUI@9733742f) | see § Testid work below |
| Search input | `[data-testid="notifications-search-input"]` | on-`automation/testids` only | |
| Page-info label | `[data-testid="notifications-pagination-page-info"]` | on-`automation/testids` only | |
| "Conversation not found" dialog | `[data-testid="alert-dialog-content"]` | on-main ✓ | shared AlertDialog; used as an **absence** assertion (canon #511 extension: absence assertions are references) |
| Chat message list | `[data-testid="chat-message-list"]` | on-main ✓ | positive proof the conversation rendered |
| Chat message item (repeats) | `[data-testid="chat-message-item"]` | on-main ✓ | count ≥ 1 |

### Testid work required (implementer, `add-data-testid`)
`notification-message-link` — the in-message `<Link>` in
`src/[fsd]/entities/notifications/ui/NotificationListItemMessage.jsx` has **no testid**
(verified: not on `main`, not on `automation/testids`). The component is SHARED with the
sidebar bell popover, so follow the precedent already in place for `messageTestId`
(EliteaAI/EliteaUI@e0d98f4a): a **caller-supplied additive prop**, threaded
`NotificationTable.jsx` `renderCell` (`linkTestId="notification-message-link"`) →
`NotificationListItem` (forward as `linkTestId`) → `NotificationListItemMessage`
(`data-testid={linkTestId}` on the existing `<Link>`). Prop plumbing only — **no new DOM
node, no hook, no markup removal** (zero-functional-impact rule).
A static value is correct: the handle is disambiguated by row scoping, exactly like
`ROW_MESSAGE_TYPOGRAPHY`:
```python
ROW_MESSAGE_LINK = (
    '[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
    '[data-testid="notification-message-link"]'
)
```
Live check 2026-08-26: every notification row on this account renders **exactly one**
`<a target="_blank">`, so the scoped selector is unambiguous. `parseMessage()` can in
principle emit several link segments — if a future case needs that, index the suffix then,
not now.

## Fidelity Declaration
No substitutions. Every observable is produced by the system: the `href` is rendered by
`resolveHref()`, the navigation is a real click on a real anchor, the messages are the
backend's, the colour is `getComputedStyle` **read** off the product's own rendering
(a read, not an injection — precedent `agent_form_page.py:230`; declare it when the
reviewer's `\.evaluate\(` grep hits).
The step-2 liveness probe is a **transit** read of the product's own conversation endpoint —
it selects WHICH notification to exercise (a precondition), and the case's own observable
(what clicking does) is still produced live by the system.

## Network Behavior
- List: `GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?limit=&offset=&sort_by=created_at&sort_order=desc`
  (+ `search=` when filtering) — 200.
- Popup: `GET /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}?messages_limit=10&sort_order=desc`
  — **200 = conversation opens**, **400 = "Conversation not found" dialog**.
- Known environmental noise on the popup: `403` on `/api/v2/secrets/secrets/default/{project}`
  and `500` on `/elitea_core/project_info/prompt_lib/{id}/project-info` were both observed
  once each and are unrelated to this flow (`.agents/testing.md` § Known issues — the
  background-resource noise class). Scope the console-error assertion accordingly and use
  `automation/utils/console_errors.py` so the URL is captured.
  **AMENDED fix round 1 (2026-08-26):** "scope accordingly" means the exact
  (status, resource) PAIR, not the URL alone (`KNOWN_BACKGROUND_NOISE_SIGNATURES`) — a
  `500` on the secrets probe or a `404` on project-info is a real failure and must fail
  the test. Pinned by
  `automation/tests/unit/test_notification_link_console_noise_filter_scope.py`.

## Known Defects Found During Exploration
- **None (no product defect).** Two of the twelve mention notifications (conversations `7839`,
  `4205`) point at conversations that no longer exist and correctly show
  "Conversation not found" — stale real history, not a defect.
- **Case-text drift → clarification EliteaAI/elitea-testing-public#1786** (sibling of #1784):
  step 6's "notification is now in read state" does not happen; the link has no mark-seen
  handler and opens a new tab so there is no back-navigation.

## Blocked Steps
None.

## Automation Hints
- File: `automation/tests/ui/admin/test_notification_link_navigates_to_conversation.py`
  (the notification specs live under `tests/ui/admin/`, not `tests/ui/settings/`).
- Markers: `p2`, `regression`, `admin` (match the neighbouring notification specs).
- Page objects: extend `automation/pages/notification_center_page.py` (link handle +
  `click_message_link_expecting_popup(notification_id)`), reuse `ChatPage` for the popup's
  message-list assertions — instantiate it on the popup `Page`.
- Wrap every step in `with allure.step("Step N — …")`.
- The popup needs its own `Page` object; do NOT reuse the notifications page's `page`.
- Do not hardcode `personal_project_id`, conversation ids, or totals — the DEV history grows
  (67 rows 2026-08-04 → 89 rows 2026-08-26).
