---
name: Agent import recreates skills quirks
description: Agent .agent.md import flow (toolbar Import button, Import parameters preview dialog, Import Complete success dialog), the application_skills API response shape, and the shrinking-locator bug in a "click all matching X" loop (from ELITEA-1795)
type: feedback
---

## Agent import flow (ELITEA-1795)

- Agents list toolbar "Import" button (`/agents/all`) has **no data-testid**
  — resolve via `page.get_by_role("button", name="Import")`. Clicking opens
  a native OS file chooser directly (no intermediate menu).
- Selecting a `.md` file opens an "Import parameters" dialog
  (`getByRole('dialog')`, heading "Import parameters") with TWO collapsed
  preview sections, each behind its own "Show details" toggle:
  - "Main entity" (the Agent: name/type, then Description/Instructions/
    Welcome message/Chat starters/Other behind the toggle)
  - "Skills" (each embedded Skill: name/type, then Description/
    Instructions/Version behind its own toggle)
  Both previews are populated **client-side from the uploaded file's
  content** before any import API call fires (confirmed: a planted marker
  string in the Skill's instructions shows up in the preview).
- The dialog's own "Import" (confirm) button shares the exact same
  accessible name ("Import") as the page-toolbar trigger button — must
  scope to the dialog: `dialog.get_by_role("button", name="Import")`.
- Confirming does NOT navigate directly to the new Agent — it opens a
  second "Import Complete" success dialog (heading "Import Complete")
  listing `"{n} agents:"` / `"{n} skills:"` with the created entity names,
  and a "Got it" button. Clicking "Got it" is what auto-navigates to the
  new Agent's detail page (`/agents/all/{new-id}?...`).
- A pre-existing cosmetic React warning (`Warning: validateDOMNesting(...):
  <p> cannot appear as a descendant of <p>`) fires during the Import
  Complete dialog's own internal markup (`IWModalSucceedContent.jsx`) —
  not asserted against, not a defect, unrelated to import correctness.

## application_skills API response (concrete, network-level assertion surface)

`GET /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}`
returns `{"skills": [{"name", "description", "skill_id", "version_id",
"version_name", "version_missing", "icon_meta"}], "max_skills": n}`. This
call fires as part of the new Agent detail page's own load sequence (can be
captured with `page.expect_response(...)` wrapped around the "Got it" click
that triggers the navigation) — gives a non-UI-dependent assertion for
"the imported Skill's ID is new/unique" that sidesteps the first-paint
timing race below.

**Known non-defect UI-timing quirk:** the imported Agent detail page's
Skills counter can show "0/5 skills added." on first paint, before the
secondary `application_skills` fetch resolves (lags main page paint by
~1-2s). The existing `AgentDetailPage.wait_for_skills_counter(expected_prefix,
timeout)` helper (already used for the identical attach-time cache-
invalidation race) is the right tool — poll the counter, don't assert on
first paint, don't add a raw sleep.

## Shrinking-locator bug — general pattern for "click all matching X"

`AgentsListPage.expand_import_preview_details()`'s first draft:

```python
show_details_buttons = dialog.get_by_role("button", name="Show details")
count = show_details_buttons.count()          # BAD: snapshot count up front
for i in range(count):
    show_details_buttons.nth(i).click()       # clicking button 0 flips ITS
                                               # OWN accessible name to "Hide
                                               # details", shrinking the live
                                               # match set — nth(1) then waits
                                               # for an index that no longer
                                               # exists -> 10s timeout
```

Root-caused via manual `playwright-cli` exploration of the live dialog
(confirmed exactly 2 "Show details" toggles — Main entity + Skills — each
independently flipping its own accessible name on click, not shared
state).

**Fix — the general pattern**: whenever clicking a matched element changes
*its own* matched property (text/name/state), don't snapshot count once and
index by `nth()`. Re-query and always take `.first`:

```python
show_details_buttons = dialog.get_by_role("button", name="Show details")
while show_details_buttons.count() > 0:
    show_details_buttons.first.click()
```

This generalizes beyond this one dialog — any "click every X" loop where X
is a toggle whose own click flips it out of the matching set needs this
shape, not a fixed-count `nth()` loop.
