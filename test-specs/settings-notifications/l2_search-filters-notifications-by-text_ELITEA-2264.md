# Test Case: Search field filters notifications by text content

## Metadata
- **TMS ID**: ELITEA-2264
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2258/2264/2265, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture).
- The user's personal project carries notifications whose message texts are **not all
  identical**, so a token drawn from one row provably excludes at least one other row.
  Confirmed live 2026-08-26: 89 notifications, mixed `bucket_expiration_warning` /
  `chat_user_mentioned` / `index_data_changed` texts. Assert loudly, never skip.

## Test Data
### reuse-existing (read-only)
- `${TEST_USER}`'s existing notification history. Search issues GET requests only —
  nothing is mutated, no cleanup needed, and the spec is safe to run beside the other
  notification specs.
- **The search term is derived live from the product's own data** (see step 2) — never
  hardcoded. The DEV history is real and grows (67 rows on 2026-08-04 → 89 on
  2026-08-26).

## Test Steps

1. Navigate to `${BASE_URL}/settings/notifications`
   (`NotificationCenterPage.navigate_and_get_rows()` → baseline `rows[]`).
   - **Verify**: table body visible; page-info matches `^(\d+) - (\d+) of (\d+)$`;
     record `baseline_total` (the third group) and `baseline_row_count`
     (`len(rendered ids)`).
   - Live 2026-08-26: `"1 - 50 of 89"`, 50 rendered rows.

2. Choose the search term **from the product's own response** (not from the test's
   imagination): take the first baseline row's message text and walk its alphanumeric
   tokens of length ≥ 6, picking the first token for which **at least one other
   baseline row's text does not contain it** (case-insensitive).
   - **Verify (precondition)**: such a token exists — otherwise fail loudly naming the
     missing precondition (all visible notifications share every long token).
   - Record `source_id` (the row the token came from) and `excluded_id` (a baseline row
     whose text lacks the token).
   - Live example 2026-08-26: token `182606` from
     `"Bucket autotest-1816-182606 will start deleting files in 24 hours…"`.

3. **Case step 2** — type the token into the search field
   (`notifications-search-input`) and wait for the resulting filtered list GET
   (600 ms debounce, `useDebounceValue` in `NotificationCenter.jsx`) — wait on the
   RESPONSE, never on a sleep.
   - **Verify**: the input's `value` equals the token (the field accepted and displays
     the input); the fired request URL carries `search=<token>` **and**
     `sort_by=created_at`; the response is 200.

4. **Case step 3** — verify the list filtered to matching rows only.
   - **Verify**:
     - `filtered_total < baseline_total` (parsed from the page-info label) — filtering
       genuinely happened;
     - `filtered_total >= 1`;
     - every rendered row's message text contains the token, case-insensitive
       (`notification-message-text` `all_inner_texts()`);
     - `source_id` is among the rendered row ids (`get_rendered_row_ids()`);
     - `excluded_id` is **not** among them.
   - Live 2026-08-26: `"1 - 2 of 2"`, 2 rows, both reading
     `"Bucket autotest-1816-182606 will start deleting files in 24 hours…"`.

5. **Case step 4** — clear the search input (`search_input.fill("")`) and wait for the
   resulting list GET.
   - **Verify**: the fired request URL carries **no** `search=` parameter; response 200;
     input `value == ""`.
   - Live 2026-08-26: `fill("")` drives the React-controlled input correctly (verified
     with the real Playwright fill, not a synthetic event).

6. **Case step 5 / Expected Final State** — verify all notifications are shown again.
   - **Verify**: parsed total from page-info `== baseline_total`; rendered row count
     `== baseline_row_count`; `excluded_id` is back among the rendered row ids.
   - Live 2026-08-26: `"1 - 50 of 89"`, 50 rows.

7. **Axis-2 boundary** — type a SINGLE character into the search field and wait out the
   debounce window plus a bounded settle.
   - **Verify**: no `search=`-carrying request is issued and the list is still unfiltered
     (total `== baseline_total`) — `MIN_SEARCH_LENGTH = 2` in `NotificationCenter.jsx`
     means a 1-char query is deliberately ignored.
   - Live 2026-08-26: typed `"8"` → still `"1 - 50 of 89"`, 50 rows, no request.
   - Leave the field cleared at the end of this step.

8. Side-channel: no unexpected console errors across the flow
   (`automation/utils/console_errors.py` `collect_console_errors(page)`).

## Expected Results
- Typing ≥ 2 characters filters the list server-side to rows whose text contains the
  term; the pagination total drops accordingly.
- Clearing the field restores the full, unfiltered list.
- A 1-character query does not filter.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications | page loads | step 1 | table body visible + page-info parsed | asserted |
| 2 Type a partial text matching at least one notification | field accepts and displays the input | steps 2–3 | input `value` + `search=` request param | asserted *(decomposed: term derivation from live data added as step 2 — see Axis 2)* |
| 3 Verify the list filters to only matching rows | condition holds | step 4 | total drop + per-row text containment + source present / excluded absent | asserted |
| 4 Clear the Search input | action completes | step 5 | request without `search=` + empty input value | asserted |
| 5 Verify all notifications are shown again | condition holds | step 6 | total back to baseline + excluded row back | asserted |
| Expected Final State: all notifications shown again | condition holds | step 6 | same as row 5 | asserted |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why it is grounded |
|---|---|
| The term is derived from the product's own response, with a proven excluded row | Without an excluded row, "the list filtered" is unfalsifiable — a search that matched everything would pass. This is what turns the case into a real filter assertion. |
| The request carries `search=<token>` / carries none after clear | Proves the filtering is the product's server-side query, not a client-side coincidence. |
| 1-character query does not filter (`MIN_SEARCH_LENGTH = 2`) | A deliberate product boundary sitting one keystroke away from the case's own step 2; cheap to assert in the same flow and it pins a rule a refactor could silently drop. |
| No unexpected console errors | Project-standard side-channel check. |

## Cleanup
- None required (read-only). Leave the search field empty (step 7 already does).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Search input | `LocatorDescriptor(testid="notifications-search-input")` | **on-automation/testids ✓** — EliteaAI/EliteaUI@7f772acc (ELITEA-2255), `SimpleSearchBar`'s existing `data-testid` prop threaded onto its `InputBase` `inputProps`. NOT yet on `main`. Already a `NotificationCenterPage.search_input` field. |
| Table body | `LocatorDescriptor(testid="notification-table-body")` | **on-automation/testids ✓** (ELITEA-2257) — existing field |
| Notification row (repeatable) | `LocatorDescriptor(testid="notification-row")` | **on-automation/testids ✓** (ELITEA-2257) — existing field |
| Message cell text | `LocatorDescriptor(testid="notification-message-text")` | **on-automation/testids ✓** (ELITEA-2257) — existing field; `all_inner_texts()` gives every rendered row's text |
| Pagination page-info label | `LocatorDescriptor(testid="notifications-pagination-page-info")` | **on-automation/testids ✓** — EliteaAI/EliteaUI@7f772acc (ELITEA-2256), existing `page_info_label` field + `get_page_info()` |
| Rendered row ids | `NotificationCenterPage.get_rendered_row_ids()` (scoped constant `ROW_CHECKBOXES_IN_BODY`) | **on-automation/testids ✓** (ELITEA-2256) — existing helper, reads ids off `notification-checkbox-{id}` |

**No new testid is needed for this case** — every handle already exists on
`automation/testids`.

## Fidelity Declaration
No substitution of any kind: no `page.route`, no `route.fulfill`, no `page.evaluate`
writing state, no monkeypatching, no stubbed client. Every asserted value (row texts,
totals, request URLs) is produced by the product. The search term itself is read out of
the product's own list response.

## Network Behavior
- `GET …/notifications/notifications/prompt_lib/{project_id}?limit=50&offset=0&sort_by=created_at&sort_order=desc` — unfiltered list.
- `GET …&search=<token>` — filtered list (same endpoint, extra param). Only issued when
  the debounced value is ≥ 2 characters (`MIN_SEARCH_LENGTH`); debounce is 600 ms.
- The separate unread-count probe (`only_new=true&only_total=true`) shares the URL prefix
  — `NotificationCenterPage._is_notifications_list_response()` already discriminates it
  via `sort_by=created_at`; reuse that predicate, and add a `search=`-aware variant for
  step 3/5 rather than matching the bare prefix.

## Known Defects Found During Exploration
None. The case text matches the live product for this flow.

## Blocked Steps
None.

## Automation Hints
- New spec under `automation/tests/ui/admin/` (where the notification specs live), e.g.
  `test_notification_search_filter.py`. Not an extension — no merged spec touches the
  search field's behaviour (ELITEA-2255's layout spec only asserts the input is visible).
- Markers: `p2`, `admin`, `regression`.
- Page-object work: add `search_notifications(token)` and `clear_search()` to
  `NotificationCenterPage`, each wrapping `expect_response` on the filtered list GET, and
  a `get_page_total()` helper parsing `get_page_info()`'s `"{start} - {end} of {total}"`.
- The debounce is 600 ms; ALWAYS wait on the response, never on a fixed sleep. For the
  1-char boundary (step 7), arm a request listener and assert nothing matching
  `search=` fired within a bounded settle window.
