---
name: Artifacts bucket DotMenu hover-reveal retry
description: open_manage_permissions() hover reveal is racy (CSS :hover vs React state) — self-heals via move-away-rehover retry, verified 10/10 on DEV
type: feedback
---

`ArtifactsPage.open_manage_permissions()` (`automation/pages/artifacts_page.py`)
hovers a bucket row to reveal its DotMenu button
(`[data-testid="bucket-menu-{name}-menu-button"]`), which is sometimes stuck
`visibility: hidden` while `display: flex` after a Playwright synthetic
`hover()` — confirmed against `EliteaUI` `origin/main`
`src/pages/Artifacts/Components/BucketItem.jsx`: the reveal is gated by TWO
independent mechanisms (a React `onMouseEnter` state driving `display`, and a
separate CSS `:hover` rule driving `visibility`), and only the CSS one races
under Playwright. ELITEA-2494 (issue #2403).

**Fix (branch `tests/adjust-ELITEA-2494-bucket-menu-hover-retry`):** bounded
retry inside the method — hover, poll for `visible` with a short sub-timeout
(min(3000, timeout)), and on timeout `page.mouse.move(0, 0)` + re-hover, up to
3 attempts, before falling back to the original full-timeout wait (so the
failure mode/message on true failure is unchanged). No locator/testid change
needed — the handle was always correct, only the wait strategy was wrong.

**Verification note:** the full pytest case
(`test_bucket_permissions_api.py::test_read_only_permission_allows_get_blocks_write_operations`)
needs `TEST_USER_B_EMAIL`/`_PASSWORD`/`ELITEA_TEAM_PROJECT_ID` (CI constructs
these dynamically per `.github/workflows/test-ui-custom.yml`; a dev sandbox's
`.env.test` typically won't have them, so the fixture
`auth_state_user_b`/`artifact_api_user_b_team_project` SKIPs the case rather
than failing it). Substitute verification: called the fixed
`open_manage_permissions()` directly in a scratch script against DEV, 10/10
clean (zero retries fired, zero failures) on a throwaway bucket in the
private test project — it got past the DotMenu reveal every time; the next
step ("Manage permissions" menuitem) is unavailable outside a Team project,
which is the expected, documented limitation, not a defect.

**Also note:** `ArtifactAPI.delete_bucket()`'s id-fallback
(`p--{project_id}.{bucket_name}`) 404'd for a bucket created in the private
project via the API in this same investigation — had to delete it through the
UI (`open_bucket_menu` → `click_bucket_menu_delete_item` → `confirm_delete_bucket`)
instead. Didn't chase further — out of scope for this fix — but worth knowing
if a cleanup step silently fails next time.
