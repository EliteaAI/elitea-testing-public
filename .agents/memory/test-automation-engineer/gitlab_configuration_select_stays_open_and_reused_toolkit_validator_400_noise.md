---
name: GitLab Configuration select stays open after CREATE-click + reused-toolkit validateToolkit 400 noise
description: ELITEA-1976 redispatch — the fix for the Step-11 TimeoutError (never re-click the Configuration dropdown, it never closes after a CREATE-action option) and a new known-noise console filter for a reused invalid-credential toolkit's validateToolkit 400.
type: feedback
---

ELITEA-1976 (create private credential from a toolkit's Configuration
dropdown, GitLab vehicle) redispatch. Prior implementer pass reported
`blocked` at what became "Step 11" — a genuine Playwright `TimeoutError`
re-clicking `toolkit_page.open_configuration_dropdown(FIELD_KEY)` after
returning from the credential-create new tab.

**Root cause (confirmed live by the analyst's redispatch, CDP DOM inspection
on both tabs simultaneously):** `SingleSelect.jsx`'s `handleChange` sets
`skipNextCloseRef.current = true` before calling a `variant: 'action'`
option's `onActivate()` — the Configuration select's dropdown NEVER actually
closes after clicking "New private ... credentials" (a CREATE-action option),
even across a tab switch. This is a **deliberate, shared mechanism** (same
one powers in-place "Refresh" actions elsewhere), not a defect — filed as a
case-text clarification only (EliteaAI/elitea-testing-public#1047).
**Fix: never call `open_configuration_dropdown()` a second time.** After the
create-tab closes, just assert directly against the still-open menu
(`configuration_group_headers`, `saved_credential_option` — no `.click()` on
the trigger). Generalizes to ANY MUI `Select` action-variant option in this
codebase (`ToolkitSelect.jsx`, `LlmModelSelect.jsx` use the identical
pattern) — if a page-object method needs to interact with a dropdown AFTER a
CREATE/action-variant option fired, check whether the dropdown is still open
before writing a second open-call.

**Separate finding, same case:** the reused team-project GitLab toolkit
(id 118, project 471) has its OWN pre-existing invalid/placeholder linked
credential, so `EliteaUI/src/api/toolkits.js`'s `validateToolkit` RTK-Query
call (`GET .../elitea_core/toolkit_validator/prompt_lib/{project}/{id}`)
fires a `400` on EVERY load of that toolkit's detail page — regardless of
anything the test does. This is the SAME intended-behavior validation path
already confirmed correct by `test_toolkit_credential_indicators_e2e`
(Enhancement #5114's credential-status-indicator feature: "Save button
disabled when credentials are invalid"). Added a THIRD known-noise console
filter to the test (same idiom as its other two:
`_is_known_project_471_secrets_403`, `_is_known_554_warning`) —
`_is_known_reused_toolkit_invalid_credential_400`, scoped to
`elitea_core/toolkit_validator/prompt_lib/` + `400` only. **Generalizes: any
future case that reuses an existing, other-owned toolkit/credential
read-only in project 471 (or any project seeded with placeholder
credentials) will hit this same 400 on toolkit-detail-page load** — reach
for this filter (or its exact idiom) rather than re-diagnosing from scratch.
Root-caused via a one-line temporary `print(f"... location={msg.location!r}")`
in the console handler, re-run once, removed before commit — fast, cheap way
to identify an unfiltered console error's exact URL when the assertion
message alone (just the text) doesn't include it.

**Also recurring:** the AFS was (again) sitting uncommitted in the main
repo's working tree after the analyst's redispatch pass — only `_surface.md`
had a real commit; the individual case `.md` file itself was invisible to my
isolated worktree (`test -f` 404, `git log --all` finds nothing). Same
gap as the existing memory entry
`afs_file_uncommitted_in_main_repo_isolated_worktree_gap.md` — read it from
the main checkout's absolute path via `Read`, wrote it into my own worktree,
committed it as part of my branch/PR. Third occurrence now — worth the
orchestrator/analyst side fixing at the source (commit the AFS file itself,
not just `_surface.md`, in the same redispatch pass) rather than every
implementer re-discovering it.
