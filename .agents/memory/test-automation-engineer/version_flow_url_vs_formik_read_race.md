---
name: Version flows read two sources with different timings (URL-derived vs Formik)
description: Waiting on the VERSION trigger or URL after a version change proves nothing — the Information panel's id lags ~0.8s behind
type: reference
aliases: [version id stale read, confirm_new_version race, VERSION_CONVERGED_JS, copy-version-id stale, save as version race]
tags: [area/agents, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
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

## Still open

The same defect lives in `PipelineDetailPage.confirm_new_version()` and
`SkillDetailPage.save_as_version()` and their specs — tracked as issue #1874.

Related: [[matched_control_run_before_blaming_a_diff]]
