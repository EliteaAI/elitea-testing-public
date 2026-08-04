---
name: API pipeline/agent seed project mismatch
description: Standalone PipelineAPI/AgentAPI scripts default to ELITEA_PROJECT_ID (.env.test), which can differ from the browser session's ACTIVE project — creates a pipeline the UI then 400s/403s on
type: feedback
---

## The gotcha

`.env.test`'s `ELITEA_PROJECT_ID` (e.g. `399`, "Private") is a **default**,
not a guarantee it matches whatever project a given localhost browser
session actually has active. A localhost session can default to a
DIFFERENT project (observed: "Elitea Testing Team", id `471`) depending on
whatever was last selected in that browser profile/localStorage.

If you create a pipeline/agent via a **standalone token-auth API script**
(`PipelineAPI(browser_cookies=[])`, relying on `settings.elitea_api_token`)
using the default project id, then navigate to it in a browser session
that's on a *different* active project:

- Bare `/pipelines/{id}` (no `?viewMode=owner`) redirects to `/pipelines/all`
  silently (looks like a 404, but is actually a project-context miss).
- `/pipelines/all/{id}?viewMode=owner` surfaces the real symptom: a console
  `400 Bad Request` on `GET .../application/prompt_lib/{wrong_project}/{id}`
  — the browser is asking for the pipeline under ITS active project, not
  the one it was created in.
- If you then try to create directly against the browser's mismatched
  project (e.g. by also passing `project_id=` explicitly to match), you may
  get a `403 access_denied` / `models.applications.applications.create` —
  the dev-token user may not have create rights on every listed project.

## Fix / avoidance

- **Fixtures using `browser_cookies`-based auth** (the normal
  `pipeline_id`/`pipeline_api` test fixtures in
  `automation/fixtures/api_fixtures.py`/`data_fixtures.py`) don't hit this —
  they inherit whatever project the browser context is actually on. This
  gotcha is specific to standalone scripts run OUTSIDE a real browser
  session (exactly the kind of ad-hoc script an analyst writes to seed
  precondition data quickly).
- If you must create via a standalone API script for manual exploration:
  first read the sidebar's active project id in the browser
  (`Project:` combobox → its textbox value), and pass that explicitly as
  `project_id=` to the API client — don't trust the `.env.test` default.
- Or just create everything through the UI (`/pipelines/create?viewMode=owner`)
  — the project selector combobox
  (`[data-testid="project-selector-trigger-combobox"]`) lets you switch to
  "Private" (`[data-testid="select-option-399"]`) explicitly before filling
  the form, guaranteeing the created entity lands in the project you expect.

Hit during ELITEA-2033 (Router node) analysis, 2026-08-04 — cost ~10 minutes
to diagnose from a silent redirect + a misleading 403.
