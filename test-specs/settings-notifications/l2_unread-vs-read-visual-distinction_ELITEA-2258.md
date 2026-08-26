# Test Case: Unread notifications are visually distinct from read notifications

## Metadata
- **TMS ID**: ELITEA-2258
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2258/2264/2265, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture; localhost skips Keycloak).
- The user's personal project carries **at least two UNREAD notifications on page 1**.
  Confirmed live 2026-08-26: `total: 89`, page 1 = 50 rows, **all 50 unread**
  (every row rendered the unread colour set; the mark-toggle read `"Mark selected as
  read"` for the first row's selection). Assert this as a loud precondition — a silent
  skip would delete the case.

## Test Data
### create-and-cleanup (state, not entities)
- No entity is created. The test **mutates** one existing notification's `is_seen`
  (unread → read) and **restores** it (read → unread) in cleanup. This is the only way
  to obtain a read row: no read notification exists on page 1 today, so the read/unread
  contrast must be produced by the product itself during the test.
- The notification id is **discovered dynamically** from the list response (never
  hardcoded) — this is real, growing DEV history.

## Test Steps

1. Navigate to `${BASE_URL}/settings/notifications`
   (`NotificationCenterPage.navigate_and_get_rows()` — returns the list fetch's
   `rows[]`, each carrying `id` + `is_seen`).
   - **Verify**: page title starts with `"Settings: Notifications"`; table body visible;
     `len(rows) > 0`.

2. Discover the case's subjects from the product's own list response.
   - `unread_ids = [r["id"] for r in rows if not r["is_seen"]]`.
   - **Verify (precondition)**: `len(unread_ids) >= 2` — fail loudly naming the missing
     precondition otherwise. `subject_id = unread_ids[0]`, `control_id = unread_ids[1]`.
   - *(Case step 2 — "identify at least one unread notification". The DOM carries no
     read/unread attribute; the product-produced oracle is the list response's `is_seen`
     — same mechanism the merged ELITEA-2259 test uses.)*

3. Capture the UNREAD baseline styling of both subjects (computed colours, read off the
   rendered elements — the product computed them, the test only reads them).
   - `subject_msg_unread`, `subject_date_unread`, `control_msg_unread`,
     `control_date_unread` via `get_row_message_color(id)` / `get_row_date_color(id)`.
   - **Verify**: subject and control render the **same** unread colour set
     (`subject_msg_unread == control_msg_unread`, `subject_date_unread ==
     control_date_unread`) — two unread rows are styled alike.
   - Live 2026-08-26 (dark theme): message `rgb(255, 255, 255)`, date
     `rgb(255, 255, 255)`, link `rgb(41, 184, 245)`.

4. **Case step 4 — click the notification row.** Click the subject row's **date cell**
   (`notification-date-text` scoped to the subject row) and wait out the mutation
   window (assert on the absence of a `PUT`, see § Network Behavior).
   - **Amended during implementation (ELITEA-2258, 2026-08-26):** the original AFS named
     the *message* cell. Its `<Typography>` embeds an inline `<Link target="_blank">`, so
     a centre-click can land on the anchor and open a tab — that is the case's *other*
     branch ("or open the linked entity"), not the row click, and it makes the step
     non-deterministic. The date cell is link-free and sits in the same row, so it is an
     unambiguous row click. The assertion is unchanged.
   - **Verify (live contract, case-text drift — see § Known Defects)**: the click does
     **NOT** mark the notification read — no bulk-mark `PUT` is issued, the subject's
     message/date colours are **unchanged** from step 3, and a fresh list fetch still
     reports `is_seen == False` for `subject_id`.
   - Live 2026-08-26: clicking the row produced zero requests to
     `/notifications/notifications/prompt_lib/` and no styling change.
     `GridTableRow.jsx` has no row-level `onClick` (only checkbox `onSelect`), and
     `NotificationListItemMessage.jsx`'s `<Link>` is a plain
     `target="_blank"` anchor with no mark-seen handler.

5. Produce the read state through the product's real control (the only in-product path
   in the Notification Center): check the subject's row checkbox
   (`check_notification_checkbox(subject_id)`), assert the toolbar toggle reads
   `"Mark selected as read"` (proves the product itself considers the row unread), then
   `click_mark_toggle()`.
   - **Verify**: the bulk-mark `PUT` returns 200 and the auto-refetch's rows report
     `is_seen == True` for `subject_id` and `False` for `control_id`.

6. **Case step 6 — the previously-unread notification is now shown in read state
   (styling changed).** Re-read the computed colours of both rows.
   - **Verify (the case's core observable)**:
     - `subject_msg_read != subject_msg_unread` **and**
       `subject_date_read != subject_date_unread` — the SAME row's styling changed when
       its read state changed;
     - `subject_msg_read != control_msg_unread` **and**
       `subject_date_read != control_date_unread` — a read row is visually distinct from
       an unread row rendered in the same table at the same moment;
     - `control_msg_read == control_msg_unread` **and**
       `control_date_read == control_date_unread` — the untouched unread row did not
       change (the distinction is per-row, not a table-wide theme shift).
   - Live 2026-08-26 (dark theme): read row message + date `rgb(169, 183, 193)`, link
     `rgba(41, 184, 245, 0.7)` vs unread `rgb(255, 255, 255)` / `rgb(41, 184, 245)`.
   - **Assert the DIFFERENCE, never the literal rgb strings** — the colours are theme
     tokens (`text.primary` / `text.secondary`, `text.link` / `text.linkSeen`) and a
     light-theme or palette change would break a hardcoded value while the contract
     still holds.

7. Side-channel: no unexpected console errors across the whole flow
   (`automation/utils/console_errors.py` `collect_console_errors(page)` — captures the
   failing resource URL, see `.agents/testing.md` § 400 flavor).

## Expected Results
- An unread notification and a read notification rendered in the same table have
  different computed colours on both the message text and the date cell.
- Marking a notification read changes that row's styling and leaves every other row's
  styling untouched.
- Clicking the notification row does not change its read state (live contract).

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | page title + table body visible | asserted |
| 2 Identify at least one unread notification | action completes | step 2 | `is_seen` from the list response (product-produced) | asserted *(decomposed: needs TWO unread rows — one subject, one control — so the "distinct from" half of the title is proven against a live sibling)* |
| 3 Verify unread notifications have a distinct visual style compared to read ones | condition holds | steps 3 + 6 | computed colour comparison subject(read) vs control(unread) | asserted *(the contrast row must be produced during the test: page 1 carries no read notification today)* |
| 4 Click the notification row or open the linked entity | control responds; expected next state shown | step 4 | absence of `PUT` + unchanged colours + `is_seen` still False | **clarification** — the live product does NOT mark a notification read on row click or link click; the assertion states the live contract (see § Known Defects, issue filed) |
| 5 Navigate back to Settings → Notifications | page loads | step 5 (implicit — never leaves the page) | n/a | asserted *(no navigation away happens: the state transition is in-place via the toolbar toggle; the case's round-trip assumed the row click navigated somewhere)* |
| 6 Verify the previously unread notification is now shown in read state (styling changed) | condition holds | step 6 | 3-way colour comparison (self-before, sibling-unread, sibling-unchanged) | asserted |
| Expected Final State: previously unread notification shown in read state | condition holds | step 6 | same as row 6 | asserted |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| Row click issues no bulk-mark `PUT` | The case's step 4 assumes the click transitions state; asserting the *absence* of the mutation is what pins the live contract and makes the filed clarification test-enforced. |
| The control (untouched) row's colours are unchanged | Without it, a table-wide re-theme would satisfy "the styling changed" — this makes the assertion per-row. |
| Toolbar toggle reads `"Mark selected as read"` before the transition | Independent product confirmation that the subject really is unread, in addition to the API's `is_seen`. |
| No unexpected console errors | Project-standard side-channel check. |

## Cleanup
- Re-select `subject_id` and click the toggle again (label now `"Mark selected as
  unread"`) to restore `is_seen == False`; assert the restoring `PUT` returns 200.
- Run this in a `finally`/fixture teardown so a mid-test failure still restores state —
  the account's notification history is shared with every other notification spec
  (`.agents/testing.md` § `#1082` shared-test-user class).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Notification table body | `LocatorDescriptor(testid="notification-table-body")` | **on-automation/testids ✓** (ELITEA-2257) — already a `NotificationCenterPage` field |
| Notification row (repeatable) | `LocatorDescriptor(testid="notification-row")` | **on-automation/testids ✓** (ELITEA-2257) — already a field |
| Per-row checkbox (dynamic) | class constant `NOTIFICATION_ROW_CHECKBOX = '[data-testid="notification-checkbox-{}"]'` | **on-automation/testids ✓** (ELITEA-2259) — already a `NotificationCenterPage` constant, used for both selection and row-id scoping |
| Mark read/unread toggle | `LocatorDescriptor(testid="notification-mark-toggle-button")` | **on-automation/testids ✓** (ELITEA-2259) — already a field |
| Message cell wrapper | `LocatorDescriptor(testid="notification-message-text")` | **on-automation/testids ✓** (ELITEA-2257). ⚠️ This is the wrapper `<Box>`; its computed `color` is the inherited default and does **not** change with `is_seen`. Use it as the CLICK target (step 4) and as the scope, never as the colour source. |
| **Message text `<Typography>` (colour source)** | `LocatorDescriptor(testid="notification-message-typography")` | **needs-adding** — caller-supplied, additive prop threading only, no new DOM node and no hook: `NotificationTable.jsx`'s `renderCell` passes `messageTestId="notification-message-typography"` → `NotificationListItem.jsx` forwards it to `NotificationListItemMessage.jsx` as `testId` → rendered as `data-testid` on the existing `<Typography sx={{ color: textColor }}>` (`NotificationListItemMessage.jsx:19-22`). Caller-supplied because both components are shared with the sidebar bell popover (`context='list'`), which must NOT gain a testid it doesn't use (`.agents/testing.md` § shared components / blanket-add ban). Precedent for the additive-prop shape: `buttonTestId` on `DeleteEntityButton` (EliteaAI/EliteaUI@30a15ac6). |
| **Date cell `<Typography>` (colour source)** | `LocatorDescriptor(testid="notification-date-text")` | **needs-adding** — a plain `data-testid` attribute on the `created_at` `<Typography>` rendered at `NotificationTable.jsx`'s own `renderCell` (`src/pages/NotificationCenter/NotificationTable.jsx:215-222`, the `color={row.is_seen ? 'text.primary' : 'text.secondary'}` node). Page-owned file, no shared component touched. |

**Scoping the colour sources to one row.** Both colour handles repeat once per row. Scope
them through the row that carries the subject's checkbox testid — a compound
`[data-testid=` selector as an UPPER_CASE class constant, per
`.claude/rules/page-objects.md` (no raw handles, no inline `get_by_test_id(f"…")`):

```python
ROW_MESSAGE_TYPOGRAPHY = (
    '[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
    '[data-testid="notification-message-typography"]'
)
ROW_DATE_TEXT = (
    '[data-testid="notification-row"]:has([data-testid="notification-checkbox-{}"]) '
    '[data-testid="notification-date-text"]'
)
```

*(`:has()` is CSS, and every hop of the selector is a `[data-testid=` term — it satisfies
the reviewer's mechanical grep, which requires the literal `[data-testid=` on the line.)*

## Fidelity Declaration

| What | Transit or terminal | Authority |
|---|---|---|
| `locator.evaluate("el => window.getComputedStyle(el).color")` to read the rendered colour | **Neither — it is a READ, not a substitution.** Nothing is fabricated, injected or replaced: the value is computed by the browser from the product's own styles. It is the only way to observe a computed colour. | Precedent in-repo: `automation/pages/agent_form_page.py:230` does exactly this. Declare it in the Run Report when the reviewer's `\.evaluate\(` grep hits it. |
| Marking the subject read via the toolbar toggle | Transit — it is the product's real control firing the real `PUT`; the case's own observable (the styling difference) is still produced entirely by the product. | `.agents/testing.md` § Fidelity policy — no fabricated response, no injected state. |

No `page.route`, no `route.fulfill`, no `page.evaluate` writing app state, no
monkeypatching anywhere in this case.

## Network Behavior
- `GET /api/v2/notifications/notifications/prompt_lib/399?limit=50&offset=0&sort_by=created_at&sort_order=desc` — list fetch (`NOTIFICATIONS_LIST_URL_MARKER = "sort_by=created_at"` distinguishes it from the unread-count probe).
- `PUT /api/v2/notifications/notifications/prompt_lib/{project_id}` body `{"ids": [id], "is_seen": bool}` — the bulk mark; 200 invalidates `TAG_NOTIFICATIONS` and auto-triggers the list refetch (`click_mark_toggle()` already waits for both).
- **Step 4's assertion is the ABSENCE of that `PUT`** after the row click. Implement it as
  a request listener armed before the click plus a bounded settle wait on an observable
  the product does produce (e.g. `expect(...).to_have_css("color", baseline)` still
  holding), not a bare `sleep`.

## Known Defects Found During Exploration
- **CLARIFICATION (case-text drift, NOT a product bug)** — case step 4 says *"Click the
  notification row or open the linked entity"* and step 6 expects the row to have become
  read. In the live Notification Center a row click does nothing (no `onClick` on
  `GridTableRow` beyond checkbox selection) and the message link is a plain
  `target="_blank"` anchor with no mark-seen handler; the only in-product read/unread
  transitions are the toolbar toggle (`NotificationTableToolbar.jsx`) and the sidebar
  popover's per-row hover button (`NotificationListItem.jsx`, `context === 'list'` only).
  The product is self-consistent; the case text assumes click-to-read that was never
  built for the table context. Filed as clarification **#1784** (`question` label; sibling of #1166 — same screen,
  different drift). Handled per the reverse-masking guard: the AFS asserts the
  **live** contract, not the stale case text.

## Blocked Steps
None.

## Automation Hints
- Target file: extend `automation/tests/ui/admin/` (the notification specs live there:
  `test_notification_mark_read_unread.py`, `test_notification_center_layout.py`) with a
  new spec, e.g. `test_notification_unread_read_visual_distinction.py`. This is a NEW
  spec, not an extension — ELITEA-2259's merged test asserts `is_seen` state and
  checkbox/toggle behaviour and never touches styling.
- Markers: `p2`, `admin` (matching the neighbouring notification specs), `regression`.
- Page-object work: add `get_row_message_color(id)` / `get_row_date_color(id)` to
  `NotificationCenterPage` (both wrapping the class-constant compound selectors above),
  plus the two new testids in EliteaUI via `add-data-testid` on `automation/testids`.
- Reuse `navigate_and_get_rows()`, `check_notification_checkbox()`,
  `get_mark_toggle_label()`, `click_mark_toggle()` — all already on the page object.
- The account is shared across notification specs and grows (89 rows on 2026-08-26);
  never hardcode a notification id, a total, or a colour.
