# Test Case: Viewer and Monitor roles cannot access Secrets section — ALREADY COVERED

## Metadata
- **TMS ID**: ELITEA-2246
- **Priority**: l3 (case frontmatter `priority: medium`)
- **Status**: **already-covered** (Rule-6 behavioural-equivalence dedup)
- **Covering spec**: `automation/tests/ui/admin/test_viewer_role_cannot_access_secrets.py`
  — `TestViewerRoleCannotAccessSecrets::test_viewer_role_is_not_offered_the_secrets_section`
  (**merged to `automation/base`**, commit `53f916c5b`, PR
  EliteaAI/elitea-testing-public#1912)
- **Covering TMS case**: **ELITEA-2348** — `execution_type: automated`,
  `status: ready`,
  `automation_test_id: tests.ui.admin.test_viewer_role_cannot_access_secrets.TestViewerRoleCannotAccessSecrets.test_viewer_role_is_not_offered_the_secrets_section`
- **Covering AFS**: `test-specs/settings-secrets/l3_viewer-role-cannot-access-secrets_ELITEA-2348.md`
- **Environment re-verified**: local (`http://localhost:5173`, `automation/testids`,
  DEV backend), 2026-08-30
- **Analyst**: qa-engineer (Sage), batch `settings-w12`, 2026-08-30
- **surface_key**: `settings-drawer-role-access`

---

## ELITEA-2246 and ELITEA-2348 are the SAME case, filed twice in the TMS

Both files exist in `EliteaAI/onetest-ai-tm-Elitea`:

- `tests/automated-full-regression-ui/settings/ELITEA-2246_viewer-and-monitor-roles-cannot-access-secrets-section.md`
- `tests/automated-full-regression-ui/settings/secrets/ELITEA-2348_viewer-and-monitor-roles-cannot-access-secrets-section.md`

Identical `title`, `priority`, `type`, `tags`, **Objective** and **Expected Final
State**. The only textual difference is step granularity — 2246 splits "navigate to
Settings" and "click Secrets" into two rows where 2348 has one:

| ELITEA-2246 | ELITEA-2348 |
|---|---|
| 2. Navigate to Settings · 3. Click "Secrets" | 2. Navigate to Settings → Secrets |
| 4. Verify the section is either not visible in the sidebar OR shows an "Access Denied" / permission error when accessed | 3. Verify the section is either not visible in the sidebar OR shows an "Access Denied" error |
| 5-7. Log in as Monitor, repeat, verify Monitor is blocked | 4-6. Log in as Monitor, repeat, verify Monitor is blocked |

Same subject, same actor, same expected observable, same OR-branch structure. There
is no assertion ELITEA-2246 asks for that ELITEA-2348's merged spec does not already
make.

## Behavioural-equivalence argument

The case's operative expectation (step 4 / Expected Final State) is an **OR**: the
Secrets section is *either* absent from the sidebar *or* shows an access denial. The
merged spec satisfies the **sidebar-absence branch**, three times over, on a real
product-computed viewer vantage:

- `test_viewer_role_cannot_access_secrets.py:141-151` — **control**: on project 399
  (where the user holds `configuration.secrets.*`) the drawer **does** offer
  `settings-nav-item-secrets`, so the later absence is meaningful rather than vacuous.
- `:153-172` — **the case's own assertion**: after switching to project 471, where the
  user's only role is `viewer`, `expect(drawer.nav_item("secrets")).to_have_count(0)`
  plus an id-list assertion.
- `:174-186` — the same absence **after a full page load**, so it is not merely a
  stale in-session permission cache.
- `:188-194` — returning to the control project restores the entry, proving the
  difference is role-driven and reversible.
- `_assert_drawer_healthy()` (`:110-124`) guards every absence read against a
  failed drawer render.

Re-verified live for this case, 2026-08-30, on the same build:
`nav_item_ids_in_order()` on project **471** = `[project-general, ai-providers,
project-context, users, analytics, usage, profile, preferences, ai-personality,
memory, tokens, notifications]` — **`secrets` absent**; on project **399** the same
list **contains `secrets`**. Role/permission ground truth the same day:
`viewer` on 471 with **0** `*secret*` permissions vs `editor`+`viewer` on 399 with
**6**. The covered behaviour still holds.

## The Monitor half is un-executable in BOTH cases — and already tracked

`GET /api/v2/admin/roles/default/{pid}` returns `['admin','editor','viewer']` for
every project checked (399, 400, 471, 406, 25) — **Elitea has no Monitor role**
(re-verified 2026-08-30). Steps 5-7 name a subject the product does not have, so
there is no observable to assert. Already filed as clarification
**EliteaAI/elitea-testing-public#1909** (OPEN) for ELITEA-2348; a new occurrence for
ELITEA-2246/2247 was commented on that issue rather than re-filed
(`.agents/profile.md` § Bug filing — "a real duplicate found BEFORE filing ⇒ do not
file").

## Why the deep-linked route is (still) not asserted

Re-confirmed live 2026-08-30: deep-linking `/settings/secrets` on the viewer project
471 renders the ordinary "No secrets" empty state while the backend returns
**403** on `GET /api/v2/secrets/secrets/default/471` — no access-denied UI at all.
That is the OPEN bug **EliteaAI/elitea-testing-public#1773**, and the route also
fires **#1203** (`Maximum update depth exceeded`, observed again this session).
Asserting that branch would make the spec a duplicate red for #1773 rather than
coverage of this case — the covering AFS's reasoning is unchanged and still correct.

## What the orchestrator should do

- **No implementation work.** No new spec, no extension.
- Link ELITEA-2246 → ELITEA-2348 in the TMS as a duplicate, and back-write
  ELITEA-2246 with the covering case's `automation_test_id`
  (`tests.ui.admin.test_viewer_role_cannot_access_secrets.TestViewerRoleCannotAccessSecrets.test_viewer_role_is_not_offered_the_secrets_section`)
  if the project's back-write policy allows a shared ref — one test may back a
  several cases (`.agents/test-automation.yaml` § `backwrite_on_done`).
- Worth flagging upstream: the duplicate exists because the same case body was
  authored into two folders (`settings/` and `settings/secrets/`). Intake dedups by
  case **id**, which cannot catch a re-authored twin.
