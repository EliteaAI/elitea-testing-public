---
name: Version flows read two sources with different timings (URL-derived vs Formik)
description: Waiting on the VERSION trigger or URL after a version change proves nothing — the Information panel's id lags ~0.8s behind
type: reference
aliases: [version id stale read, confirm_new_version race, VERSION_CONVERGED_JS, copy-version-id stale, save as version race]
tags: [area/agents, type/gotcha]
created: 2026-08-27
updated: 2026-08-28
---

## The race

On agent/skill/pipeline detail pages, the two things a test reads after a version
change come from **different sources with different timings**:

| Read | Source | Timing |
|---|---|---|
| `agent-version-selector-trigger` | `ApplicationVersionSelect.jsx` — `if (isFromCreation) return version;` reads the route's version **path param synchronously** | flips **instantly**, before any data loads |
| `copy-version-id` (Information panel) | `ApplicationInformation.jsx` renders `version_details?.id` from **Formik** | written only after the async version-detail GET lands |

So the trigger text and the URL are **the same signal**, not two. Waiting on both
still returns inside the gap. Measured on ELITEA-1888 (issue #1872): the wait
returned at t+1.46s with the panel still showing the previous id; it converged
0.83s later. `POST 201` had already returned the new id — **the backend is
correct, only the read is racy.** Symptom: `assert '1676' != '1676'`.

## The fix shape

Wait on the three-way convergence predicate, not on either URL-derived signal:
trigger text === name **AND** `copy-version-id` non-empty **AND** URL last
segment === `copy-version-id`. It lives as
`AgentDetailPage.VERSION_CONVERGED_JS` (a class-level constant shared by
`confirm_new_version()` and `select_version_by_name()`). Requiring the
Formik-backed id to equal the URL segment is the ONLY signal proving the
version data actually arrived.

## Two traps found in the same method

- A `wait_for_function` comparing the previous **version** id against the URL's
  last segment is a **guaranteed no-op**: pre-save that segment is the **agent**
  id, so the inequality is already true at t=0. Check what the URL segment
  actually holds before and after the action.
- `BasePage.wait_for_network()` is `networkidle` (issue #1847) and can resolve in
  the dead gap between a POST completing and the follow-up GET being issued — it
  buys nothing here and is a race in its own right.

## Where it has been fixed

- `AgentDetailPage` — ELITEA-1888 / issue #1872 (the original).
- `PipelineDetailPage.confirm_new_version()` — ELITEA-2002 / issue #1893,
  2026-08-28. Same three removals (dead `prevId` URL wait, `wait_for_network`,
  trigger-text-only poll) + the hoisted `VERSION_CONVERGED_JS`. It also fixed
  ELITEA-2003 (`test_pipeline_delete_version.py`), which failed
  byte-identically from the same call site — one page-object wait, two red
  specs. **Method-scoped, not file-scoped** — the same file's
  `wait_for_fallback_to_base()` is still on the old pattern; see § Still open.

## Still open

- `SkillDetailPage.save_as_version()` and its specs — tracked as issue #1874.
- `PipelineDetailPage.wait_for_fallback_to_base()` — a residual site of the same
  family **inside the very file the section above lists as fixed**. Still
  trigger-text-only, then a `wait_for_network` whose timeout this class's
  override SWALLOWS, then one `get_version_id()` read — so it can return the
  DELETED version's id. NOT fixed alongside #1893 for a real reason:
  `VERSION_CONVERGED_JS` requires URL-last-segment === `copy-version-id`, and
  what the route becomes after a version DELETE (rewrite to base's id, or drop
  the version segment entirely?) has never been verified live — applying the
  predicate blind could trade the race for a hard hang. Documented in the
  method's own docstring (ELITEA-2002 fix round, 2026-08-28); needs live
  verification + a follow-up card before anyone changes its behaviour.

Related: [[matched_control_run_before_blaming_a_diff]]
