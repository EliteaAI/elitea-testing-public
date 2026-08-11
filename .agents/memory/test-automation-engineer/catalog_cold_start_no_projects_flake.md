---
name: Catalog cold-start "No projects" / "No agents found" flake
description: A fresh browser context navigating straight to /elitea-catalog can render before project bootstrap completes — "No projects" sidebar + empty catalog, self-resolves on retry. Not a click_start_chat/#1043 issue.
type: feedback
---

Observed twice this dispatch (ELITEA-2360 root-cause debug, 2026-08-11) on
otherwise-unmodified code (once on the pristine base, once after my own
change — ruling out my change as the cause): a fresh pytest `context`
fixture (empty storage state on localhost, per `session_fixtures.py`)
navigating straight to `/elitea-catalog` via `AgentHubPage.navigate()` can
render the Catalog heading fully ready (`page_heading` visible — the page
object's own ready-signal) while the sidebar still reads "Project: No
projects" (or later, "Private" with zero agents) and the catalog body shows
"No agents found — Try adjusting your search terms". This fails
`agent_hub.get_agent_card(name).first.is_visible()` (or any assertion
depending on catalog content) even though nothing is actually wrong —
retrying the identical test immediately afterward passes cleanly.

Root cause not fully isolated — plausibly the app's project-bootstrap
sequence (default-project selection via `VITE_DEV_TOKEN` auto-login) hasn't
resolved by the time `page_heading` renders, since that heading is static
markup independent of the project-fetch. `wait_for_page_load()` only waits
on `page_heading`, not on any project/agent-list signal.

Separately (same dispatch, different solo rerun), also saw a genuine
DEV-backend hiccup: `dev.elitea.ai` socket.io polling requests failing with
CORS + a burst of `503 Service Unavailable` — a transient backend
availability blip, not a frontend race. Distinguish by the network requests: project-selector text ("No projects" vs a real project name) points at the
bootstrap-race version; CORS/503 console errors point at backend instability.

**Neither of these is related to known defect #1043 / `click_start_chat()`**
— don't misattribute a "No projects"/CORS-503 failure to the Start Chat
race; check the screenshot/console first. If this recurs often enough to be
worth a structural fix, the candidate is strengthening
`AgentHubPage.wait_for_page_load()` to also wait for a real agent card OR
the sidebar project name to resolve — not yet done (out of scope for a
click_start_chat debug task; flag to the lead if it keeps blocking cases).
