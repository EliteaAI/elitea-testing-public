# Test Case: Clicking a bucket retention-warning notification link navigates to the correct bucket

## Metadata
- **TMS ID**: ELITEA-2263
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **Analyst**: qa-engineer (Sage), analyst slot, cluster ELITEA-2261/2262/2263, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture).
- The notification history contains **at least one `bucket_expiration_warning`
  notification whose bucket still exists** in the user's personal project. Confirmed live
  2026-08-26: 41 retention warnings; most name autotest buckets already deleted by the very
  retention policy the notification announces, but `autotest-1816-182606` (notifications
  `111978`, `111967`) is still present. The spec discovers a live target at runtime and
  **fails loudly** if none exists. Never skip.

## Test Data
### reuse-existing (read-only)
- `${TEST_USER}`'s notification history and personal-project artifact buckets. GET-only
  flow — clicking the link mutates nothing. No cleanup beyond closing the popup tab.
- Nothing hardcoded: the notification id, the bucket name and the project id all come from
  the product's own list response / rendered `href`.

## Test Steps

1. **Case step 1** — navigate to `${BASE_URL}/settings/notifications`
   (`NotificationCenterPage.navigate_and_get_rows()`).
   - **Verify**: table body visible; page-info matches `^(\d+) - (\d+) of (\d+)$`.

2. **Case step 2** — find a "Bucket [bucket link] will start deleting files…" notification
   whose bucket is **live**.
   - Filter with the product's own search field using the template token
     `will start deleting files`. Live 2026-08-26: `"1 - 41 of 41"`.
   - For each rendered row read the link `href` and parse `bucket=<name>` (URL-decoded).
   - Determine liveness against the product's own artifacts state: the bucket row
     `artifacts-bucket-row-{name}` exists in the personal project's bucket list
     (`ArtifactsPage.bucket_exists(name)`), or equivalently the buckets API lists it. Take
     the FIRST (newest) live one.
   - **Verify (precondition)**: such a row exists — otherwise fail loudly naming exactly
     what is missing ("no bucket_expiration_warning notification points at a surviving
     bucket").
   - Record `notification_id`, `bucket_name`, `project_id`.
   - Live 2026-08-26: notification `111978`,
     `"Bucket autotest-1816-182606 will start deleting files in 24 hours according to its
     retention policy…"`, link text `autotest-1816-182606`.
   - **Verify (link contract, deterministic for ANY retention row)**: the rendered `href`
     equals `{origin}/{notification.project_id}/artifacts?bucket={urlencode(meta.bucket_name)}`,
     the link text equals `meta.bucket_name`, and the anchor carries `target="_blank"` +
     `rel="noopener noreferrer"`.

3. **Case step 3** — click the bucket link inside the notification text
   (`notification-message-link` scoped to `notification_id`'s row).
   - `target="_blank"` ⇒ a **NEW TAB**. Wrap the click in `expect_popup()` and hold it.
   - **Verify**: exactly one new page opened.

4. **Case step 4** — verify the new tab lands on the referenced artifact bucket.
   - Wait (framework wait, never a sleep) for the popup URL to settle at
     `…/artifacts?bucket={bucket_name}`.
   - **AMENDED during ELITEA-2263 implementation (2026-08-26): the `/{projectId}` prefix
     is NOT always consumed.** The project switcher drops it only when a switch is
     actually required. This notification's project (399, the personal project) is
     already the selected one, so the segment SURVIVES: the live landing URL is
     `http://localhost:5173/399/artifacts?bucket=autotest-1816-182606`, not
     `/artifacts?bucket=…`. (ELITEA-2261's mention notification lives in project 406,
     a real switch, and its segment IS consumed — hence the digest's original claim.)
   - **Verify**: popup path == `/artifacts` **or** `/{notification.project_id}/artifacts`
     — exactly those two, nothing else — and query param `bucket` == `bucket_name`.
   - **AMENDED during fix round 1 (2026-08-26): the "correct project" proof moved to
     step 5 and changed handle.** The landing path cannot carry it — when no switch is
     required the product serves the bare `/artifacts` form, which names no project at
     all — and the sidebar project selector renders a project *label*
     (live 2026-08-26: `Private`, title `"Artifacts - project_user_659"`) that the test
     cannot derive from the notification without hardcoding it (there is no project-name
     API client in `automation/api/`). The shipped assertion instead reads the artifacts
     REST calls the new tab actually issued and requires every one of them to be scoped
     to the notification's own `project_id` — the UI carries it as a query param, not a
     path segment (observed live 2026-08-26: `GET /artifacts/s3/?project_id=399&format=json`
     and `GET /artifacts/s3/{bucket}?project_id=399&format=json`) — strictly stronger
     evidence, since a
     same-named bucket in another project surfaces here as a foreign project id, and it
     is symmetric with ELITEA-2261's `conversation_responses` project-scoped-URL check.

5. **Case step 5** — verify the bucket page opens without a "not found" error, on the
   **correct** bucket.
   - **Verify**:
     - `artifacts-bucket-row-{bucket_name}` is visible — the named bucket is listed;
     - the bucket is actually OPENED, not merely listed: its tree expanded — either
       `artifacts-bucket-tree-empty-label-{bucket_name}` ("No files in this bucket") for an
       empty bucket, or the file list rendered for a non-empty one. `ArtifactsPage`'s
       existing `navigate_to_bucket()` / `_wait_for_bucket_panel()` already encode this wait
       and its known selected-project race — reuse them rather than re-deriving.
   - **Verify (side channel)**: no `4xx/5xx` on the artifacts/bucket-listing requests; no
     console errors attributable to them.
   - Live contrast captured for a deleted bucket (`autotest-1816-1787504970`, notification
     `111985`): the URL still carries `?bucket=…` but no `artifacts-bucket-row-…` and no
     tree panel for it — that is the failure shape this step must catch. **Note the URL
     alone is NOT a sufficient assertion.**
   - **Amended during stabilization (settings-w02 gate, 2026-08-26) — this step MUST wait on
     the popup's own bucket-list RESPONSE, not on an element budget.** The
     deleted-bucket failure shape above is byte-identical to the *still-loading* shape:
     `Artifacts.jsx:709-731` renders the artifacts EMPTY state ("Buckets: 0 / No buckets
     created yet") for the entire in-flight window, because the `?bucket=` deep-link
     selection (`Artifacts.jsx:487-520`) can only resolve once `allBuckets` has loaded. In
     the DEV account's project 399 (1 049 buckets, ~205 KB) the list read measured
     10.5-12.7 s from the API client and 14.8-18.0 s end-to-end in a fresh idle tab
     (row visible at 16.9 / 18.5 / 20.1 s), so the original flat 20 s element budget sat
     *below the fetch cost alone* and produced a red gate that read exactly like a missing
     bucket. The spec now registers a context-level `expect_event("response", …)` for
     `/artifacts/s3/?project_id={project_id}` **before** the click and resolves it before
     asserting the row (`BUCKET_LIST_READ_URL_RE_TEMPLATE` / `BUCKET_LIST_READ_TIMEOUT`);
     the element budget is a post-read *render* budget only. Pinned by
     `automation/tests/unit/test_notification_bucket_link_list_read_gate.py`.

## Expected Results
- The retention-warning link's `href` is built from the notification's own
  `meta.bucket_name` and `project_id`.
- Clicking it opens a new tab on the artifacts page of that project with `?bucket=<name>`.
- That bucket is listed AND opened (its file tree/empty-state renders); no not-found state.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | step 1 | covered |
| Step 1 — Navigate to Settings → Notifications | page/section loads | `navigate_and_get_rows()` | step 1 | covered |
| Step 2 — Find a "Bucket [bucket link] will start deleting files…" notification | produces expected UI state | search + live-bucket discovery | step 2 | covered (decomposed: search, parse href, liveness check) |
| Step 3 — Click the bucket link | control responds | click on `notification-message-link` | step 3 | covered |
| Step 4 — Browser navigates to the referenced artifact bucket | condition holds | popup URL `/artifacts?bucket={name}` or `/{project_id}/artifacts?bucket={name}` (amended); the notification's own project proven in step 5 by every artifacts REST call carrying `?project_id={project_id}` (amended, fix round 1) | steps 4-5 | covered (new TAB, not in-tab navigation) |
| Step 5 — Bucket page opens without a "not found" error | condition holds | bucket row visible + bucket tree opened | step 5 | covered |
| Expected final state | bucket page opens cleanly | same as step 5 | step 5 | covered |

### Axis 2 — observables asserted beyond the case
| Extra observable | Why grounded |
|---|---|
| `href` equals the meta-derived URL and link text == `meta.bucket_name` | "the CORRECT bucket" is decided by the href; deterministic for every retention row even when the bucket has since been deleted. |
| `target="_blank"` + `rel` | The new-tab behaviour is why the case's step-4 wording doesn't apply literally; pinning it stops a silent switch to in-tab navigation from hanging the popup wait. |
| Bucket **opened**, not merely listed | Landing on `/artifacts` with a `?bucket=` query the app ignored would satisfy a URL-only assertion while the case's intent ("navigates to the correct bucket") failed. |
| Every artifacts REST call scoped to the notification's own `project_id` | "the correct bucket" is project-scoped: bucket names are unique only within a project, and the bare `/artifacts` landing form names no project. |
| No console errors / no 4xx | Standard side-channel check. |

## Cleanup
None — read-only. Close the popup tab; clear the search field.

## Concrete Handles (discovered during exploration)

| Element | Primary handle | Provenance | Notes |
|---|---|---|---|
| Notification row (repeats) | `[data-testid="notification-row"]` | on-main ✓ | scope per row via checkbox id |
| Row checkbox (dynamic) | `[data-testid="notification-checkbox-{id}"]` | on-`automation/testids` only | `NOTIFICATION_ROW_CHECKBOX` |
| Row message cell | `[data-testid="notification-message-text"]` | on-main ✓ | |
| **In-message link** | `[data-testid="notification-message-link"]` | **ADDED during implementation** — on-`automation/testids` only (EliteaAI/EliteaUI@9733742f) | one add, consumed by ELITEA-2261 and ELITEA-2263 |
| Search input | `[data-testid="notifications-search-input"]` | on-`automation/testids` only | |
| Bucket row (dynamic) | `[data-testid="artifacts-bucket-row-{name}"]` | on-main ✓ | `ArtifactsPage.BUCKET_ROW` |
| Bucket empty-tree label (dynamic) | `[data-testid="artifacts-bucket-tree-empty-label-{name}"]` | on-`automation/testids` only | `ArtifactsPage.BUCKET_TREE_EMPTY_LABEL` — proof the bucket is OPENED |

### Testid work required (implementer, `add-data-testid`)
`notification-message-link` — see ELITEA-2261's AFS § Testid work for the exact prop-thread
shape (`linkTestId` caller-supplied prop, `NotificationTable.jsx` → `NotificationListItem` →
`NotificationListItemMessage`). **One add serves ELITEA-2261 and ELITEA-2263** — do not add
it twice.

## Fidelity Declaration
No substitutions. The `href` is rendered by `resolveHref()`, the navigation is a real click
on a real anchor, the bucket listing is the backend's. The step-2 liveness check is a
**transit** read of the product's own artifacts state that selects WHICH notification to
exercise; the case's own observable is still produced live.

## Network Behavior
- List GET (+ `search=`) as documented in `test-specs/settings-notifications/_surface.md`.
- Popup: the artifacts bucket-listing GETs for the notification's project —
  `GET /artifacts/s3/?project_id={id}&format=json` (the whole bucket list, and the
  gating read for step 5) followed by `GET /artifacts/s3/{bucket}?project_id={id}&format=json`
  (that bucket's contents). **The list read is SLOW and its cost scales with the project's
  bucket count** — 10-18 s in project 399 (1 049 buckets); see step 5's amendment.
- Known environmental noise: a `403` on `/api/v2/secrets/secrets/default/{project}` and a
  `500` on `/api/v2/elitea_core/project_info/prompt_lib/{id}/project-info` were observed on
  the popup and are unrelated to this flow (`.agents/testing.md` § Known issues — background
  resource noise). Use `automation/utils/console_errors.py` so any recurrence names its URL.
  **The spec's filter is scoped to those exact (status, resource) PAIRS**
  (`KNOWN_BACKGROUND_NOISE_SIGNATURES`), never the URL alone — a different status on either
  resource is a real failure and must fail the test (pinned by
  `automation/tests/unit/test_notification_link_console_noise_filter_scope.py`).

## Known Defects Found During Exploration
None. Retention warnings that point at already-deleted buckets are the retention policy
working as advertised, not a defect.

## Blocked Steps
None.

## Automation Hints
- File: `automation/tests/ui/admin/test_notification_link_navigates_to_bucket.py`.
- Markers: `p2`, `regression`, `admin` (+ `artifacts` if the suite convention allows two
  feature markers — check the neighbours).
- Page objects: `NotificationCenterPage` (link handle + popup-opening helper, shared with
  ELITEA-2261) and `ArtifactsPage` instantiated on the **popup** `Page`.
- Wrap every step in `with allure.step("Step N — …")`.
- Never hardcode the bucket name, the project id, or the row totals.
