# Test Case: New notification appears in the list (after an index run)

## Metadata
- **TMS ID**: ELITEA-2265
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2258/2264/2265, 2026-08-26
- **Status**: **blocked** — the case's own trigger (a completed index run) cannot be
  produced on this environment with the accounts/data available. See § Blocked Steps.

## Why this is blocked, not "expensive"

The case's steps 2–3 require *"a toolkit that has indexing capability"* and *"trigger an
index operation and wait for it to complete"*. Every prerequisite for that is absent, and
none of them can be supplied honestly from the test side:

| Prerequisite | Live state, 2026-08-26 | Evidence |
|---|---|---|
| A toolkit exists | **Zero toolkits** in the test user's personal project | `GET /toolkits/all` redirects straight to `/toolkits/create` ("New Toolkit — Choose the toolkit type"), the product's empty-state route |
| A toolkit with indexing can be created | An `artifact` toolkit form exists (`toolkit-type-card-artifact`) but its **vector-store credential select offers only `"None"`** | opened `toolkit-credential-select-pgvector-combobox` — single option `None` |
| A vector-store credential exists to select | **Zero credentials** in the project | `GET /credentials/all` redirects to `/credentials/create-credential`; the credential-type catalogue exposes no pgvector/vector-storage type (Storage → S3 API Credentials only) — vector storage is provisioned at `configurations/models` (`section=vectorstorage`), i.e. an admin/project-configuration act, not a test act |
| Test-side secrets to provision one | No `PGVECTOR*` / vector-store keys in `automation/config.py` or `.env.test` | `grep -i pgvector automation/config.py .env.test` → no hits |

Without a vector store there is no index; without an index there is no
`index_data_changed` notification; and the case's steps 5–6 assert precisely *that*
notification. Fabricating the notification (injecting a row, stubbing the list response)
would be a **terminal substitution** — the case's own observable read off a test-authored
payload — which `.agents/testing.md` § Fidelity policy forbids, and the case text never
asks for simulation. Per that policy this is a decision for a human, not an
implementation detail: routed as `blocked`.

## What WAS executed live (so the unblocked run starts warm)

- **Step 1** — `${BASE_URL}/settings/notifications` loads; the notification count is
  readable from the pagination label (`notifications-pagination-page-info`,
  `"1 - 50 of 89"` → total 89). Baseline capture is solved.
- **Step 4** — returning to the page is a plain `NotificationCenterPage.navigate()`.
- **Step 6** — "the new notification is in unread state" is observable two ways, both
  proven live this session on other rows: the list response's `is_seen` field, and the
  unread colour set (see ELITEA-2258's AFS, same batch).
- **Step 7** — the bell's red unread marker is `sidebar-notifications-bell-icon`
  carrying `data-has-messages="true"`; confirmed live on this page this session.
  Already exercised by the merged spec
  `automation/tests/ui/onboarding/test_sidebar_notification_badge.py`
  (ELITEA-2234) — **not** coverage of this case (that spec never creates a
  notification), but the handle and its semantics are settled.
- **Steps 2–3** — could not be executed at all (table above).

## Blocked Steps

| Case step | What is needed to unblock | Owner |
|---|---|---|
| 2 "Open a toolkit that has indexing capability" | A toolkit with indexing configured must exist in the test project (or be creatable by the test) | human / lead |
| 3 "Trigger an index operation and wait for it to complete" | A vector-store (pgvector) credential provisioned for the test project + confirmation that an index run completes deterministically within a test-usable time budget on the DEV backend | human / lead |
| 5 "a new notification appears at the top confirming the index was created" | Follows from step 3 | — |

**Decision the human owns (do not settle it downstream):**
1. **Provision the fixture** — add a vector-store credential + an indexable toolkit (and,
   if the index run is slow/nondeterministic, decide whether the wait is acceptable). The
   case then becomes automatable as written.
2. **Re-scope the case** — assert "a new notification appears in the list, unread, with
   the bell marker" using a *different real* notification trigger that the test can drive
   honestly (`chat_user_mentioned` / `chat_user_added` are cheaply triggerable live per
   `test-specs/settings-notifications/_surface.md`). This changes **what the case
   verifies** (steps 2–3 and step 5's "confirming the index was created"), so it is a
   case-text decision, not an implementer's improvisation
   (`.agents/role-overrides.md` § declared-improvisation protocol, ceiling limit 1).
3. **Keep it manual** — leave the case as a manual regression on an environment that has
   an indexable toolkit.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Notifications, note the count | page loads | executed live | page-info total | **blocked** (no spec emitted — the case cannot complete) |
| 2 Navigate to Toolkits, open a toolkit with indexing capability | page loads | — | — | **blocked** — no toolkit exists; none can be created without a vector-store credential |
| 3 Trigger an index operation and wait for completion | action completes | — | — | **blocked** — same root cause |
| 4 Navigate back to Settings → Notifications | page loads | executed live | `navigate()` | **blocked** (depends on 3) |
| 5 A new notification appears at the top confirming the index was created | condition holds | — | — | **blocked** — depends on 3; fabricating it would be a terminal substitution |
| 6 The new notification is in unread state | condition holds | mechanism proven live (see above) | `is_seen` / unread colours | **blocked** (depends on 5) |
| 7 The bell icon shows the red unread marker dot | condition holds | mechanism proven live | `sidebar-notifications-bell-icon[data-has-messages="true"]` | **blocked** (depends on 5) |
| Expected Final State: bell shows the red unread marker | condition holds | — | — | **blocked** |

### Axis 2 — observables beyond the case
None — no spec is emitted.

## Concrete Handles (confirmed live, for the unblocked run)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Pagination page-info (notification count) | `LocatorDescriptor(testid="notifications-pagination-page-info")` | **on-automation/testids ✓** — EliteaAI/EliteaUI@7f772acc (ELITEA-2256); `NotificationCenterPage.get_page_info()` |
| Notification rows / ids / `is_seen` | `navigate_and_get_rows()` + `get_rendered_row_ids()` | **on-automation/testids ✓** (ELITEA-2257/2259) |
| Sidebar bell + unread marker | `LocatorDescriptor(testid="sidebar-notifications-bell-icon")` + `data-has-messages` attribute | **on-automation/testids ✓** (ELITEA-2234) — `SidebarHeaderPage.notifications_bell_icon` |
| Toolkit type card (artifact) | `[data-testid="toolkit-type-card-artifact"]` | **on-automation/testids ✓** (pre-existing, MCP wave) — reachable, but the form cannot be completed (no vector-store credential) |

## Fidelity Declaration
No substitution proposed, and none is permitted here: the case's observable is the
notification the *backend* emits when an index run completes. Any test-authored
notification row or stubbed list response would be a terminal substitution
(`.agents/testing.md` § Fidelity policy) with no case-text authority for simulation.

## Known Defects Found During Exploration
None — the emptiness of the toolkit/credential lists is environment state, not a product
defect. The product's empty-state redirects behaved correctly.

## Automation Hints
Do not implement until § Blocked Steps is resolved. When it is, the notification-side
handles above are all in place; the new work is entirely on the toolkit/index side.
